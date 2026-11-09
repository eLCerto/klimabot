"""The web chat end to end: a real browser, the real app, a scripted model (see conftest.py).

Each test is one thing a visitor does, checked on the screen and, where the business depends on it,
on the server too (the lead on disk, the GDPR audit of the log).
"""
import re

import pytest
from playwright.sync_api import expect

import test_guards as tg
bot, cost_report = tg.bot, tg.cost_report

SAMSUNG = ["AR40H09C1AMNEU", "AR40H09C1AMXEU"]   # the two sets code picks for a 14 m² bedroom
TOSHIBA = ["RAS-10B2AVG-E2", "RAS-B10B2KVG-E2"]
SAMSUNG_PRICE, TOSHIBA_PRICE = tg.priced(SAMSUNG), tg.priced(TOSHIBA)  # from quote(), never typed by hand
OFFER = (f"**Samsung AR35 WIFI** (2,6 kW): **{SAMSUNG_PRICE}** s DPH.\n\n"
         f"**Toshiba SEIYA Classic 2** (2,5 kW): **{TOSHIBA_PRICE}** s DPH.\n\nVyhovuje vám niektorá z nich?")
CONSENT_QUESTION = bot.CONSENT_QUESTIONS["sales"]["sk"]
PHONE = {"viewport": {"width": 412, "height": 915}, "device_scale_factor": 2.625, "is_mobile": True, "has_touch": True}


def make_offer(chat, model):
    """The first suggestion on the welcome card: code prices two sets, the model writes the offer."""
    model.replies(OFFER)
    chat.page.get_by_role("button", name=re.compile("Spálňa 14 m²")).click()
    chat.wait_for_reply()
    expect(chat.price_cards).to_have_count(2)


def choose_and_consent(chat, model):
    """Click the Samsung card, leave a name and phone, agree with the consent button."""
    model.replies("Výborne, Samsung AR35 WIFI. Napíšte mi prosím meno a telefónne číslo.")
    chat.price_cards.first.get_by_role("button", name="Toto chcem").click()
    chat.wait_for_reply()
    expect(chat.user_bubbles.last).to_contain_text("Chcem túto ponuku: 1× Samsung AR35 WIFI")
    expect(chat.bot_bubbles.last).to_contain_text(CONSENT_QUESTION)  # added by code, not by the model
    expect(chat.consent).to_be_visible()

    model.replies("Ďakujem, pán Testovací.")
    chat.send("Ján Testovací, 0900 123 456")
    expect(chat.bot_bubbles.last).to_contain_text(CONSENT_QUESTION)  # contacts are no consent: asked again

    model.replies("Ďakujem, projektový manažér sa vám ozve.")
    chat.consent.get_by_role("button", name="Áno, súhlasím").click()
    chat.wait_for_reply()
    expect(chat.consent).to_have_count(0)


# ---------- the sale ----------

def test_a_suggestion_gets_an_offer_with_price_cards(chat, model):
    expect(chat.welcome).to_be_visible()
    make_offer(chat, model)

    expect(chat.welcome).to_be_hidden()
    expect(chat.user_bubbles).to_have_text(["Dobrý deň, hľadám klimatizáciu do spálne, má 14 m². Koľko by stála?"])
    expect(chat.bot_bubbles.last).to_contain_text(SAMSUNG_PRICE)
    samsung, toshiba = chat.price_cards.first, chat.price_cards.last
    expect(samsung).to_contain_text("Samsung AR35 WIFI")
    expect(samsung.locator(".grand")).to_contain_text(SAMSUNG_PRICE)
    expect(toshiba.locator(".grand")).to_contain_text(TOSHIBA_PRICE)
    expect(samsung).to_contain_text("Montáž: cenu určí projektový manažér")  # never an installation price


def test_the_customer_view_hides_the_debugging(chat, model):
    make_offer(chat, model)
    tool_chips = chat.log.locator(".tool-chip")
    notes = chat.page.get_by_role("complementary", name="Poznámky bota o zákazníkovi")
    expect(tool_chips.first).to_be_hidden()  # the demo opens in the customer's view
    expect(notes).to_be_hidden()

    switch = chat.page.get_by_role("switch", name="Ladenie")
    chat.page.get_by_text("Ladenie", exact=True).click()  # the label, as a person clicks it
    expect(switch).to_be_checked()
    expect(tool_chips.filter(has_text="quote")).to_have_count(2)  # code priced both picks (Move.prerun)
    expect(notes).to_be_visible()

    chat.page.reload()  # the visitor's choice is remembered
    expect(switch).to_be_checked()


def test_choosing_an_offer_and_agreeing_writes_the_pm_record(chat, model, server):
    expect(chat.brief).to_contain_text("Zatiaľ prázdny")
    make_offer(chat, model)
    choose_and_consent(chat, model)

    expect(chat.brief).to_contain_text("Pripravený")
    expect(chat.brief).to_contain_text("Ján Testovací")
    expect(chat.brief).to_contain_text("GDPR súhlas: áno")
    # The business side: the lead is on disk and the log passes the independent GDPR audit.
    assert server.session().handoff_path
    assert cost_report.summarize(server.session().log_path)["gdpr_status"] == "ok"

    with chat.page.expect_download() as download:
        chat.brief.get_by_role("button", name="Stiahnuť .md").click()
    record = download.value.path().read_text(encoding="utf-8")
    assert "Ján Testovací" in record and "AR40H09C1AMNEU" in record


def test_refusing_consent_stores_nothing(chat, model, server):
    make_offer(chat, model)
    model.replies("Výborne, Samsung AR35 WIFI. Napíšte mi prosím meno a telefónne číslo.")
    chat.send("Beriem ten Samsung.")
    expect(chat.consent).to_be_visible()

    model.replies("Rozumiem, vaše údaje neukladám.")
    chat.consent.get_by_role("button", name="Nie, nesúhlasím").click()
    chat.wait_for_reply()

    expect(chat.bot_bubbles.last).to_contain_text(bot.COMPANY_EMAIL)  # code adds the company contact
    expect(chat.consent).to_have_count(0)
    expect(chat.brief).to_contain_text("Zatiaľ prázdny")
    assert server.session().consent_refused and not server.session().handoff_path


# ---------- the page ----------

def test_markup_in_a_reply_cannot_run_script(chat, model):
    # Replies and the PM record carry visitor-typed text: the page renders them through DOMPurify.
    hostile = ('Do akej miestnosti hľadáte klimatizáciu? <img src="data:," onerror="window.__xss = 1">'
               '<script>window.__xss = 2</script><a href="javascript:window.__xss = 3">odkaz</a>')
    # The server lets HTML through (only the spelling check minds it: the tag names aren't Slovak, one
    # regeneration), so the browser's sanitizing is the last line of defence.
    model.replies(hostile, hostile)
    chat.send('<b onmouseover="window.__xss = 4">Dobrý deň</b>')

    reply = chat.bot_bubbles.last
    expect(reply).to_contain_text("Do akej miestnosti")
    expect(chat.user_bubbles.last).to_have_text('<b onmouseover="window.__xss = 4">Dobrý deň</b>')  # shown as typed
    reply.get_by_text("odkaz").click()
    assert chat.page.evaluate("window.__xss") is None
    assert reply.locator("script, [onerror], [onmouseover], a[href^='javascript']").count() == 0


def test_a_reload_resumes_the_conversation(chat, model, server):
    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.send("Dobrý deň")

    chat.page.reload()
    expect(chat.user_bubbles).to_have_text(["Dobrý deň"])
    expect(chat.bot_bubbles).to_have_count(1)
    expect(chat.welcome).to_be_hidden()

    model.replies("Čo je pre vás najdôležitejšie — tichý chod, filtrácia alebo Wi-Fi?")
    chat.send("Spálňa, 14 m2.")
    assert server.visitor().turns == 2, "the reloaded tab kept its session"


def test_a_new_conversation_is_confirmed_first(chat, model, server):
    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.send("Dobrý deň")
    dialog = chat.page.get_by_role("dialog", name="Začať novú konverzáciu?")

    chat.page.get_by_role("button", name="Nová konverzácia").click()
    dialog.get_by_role("button", name="Zrušiť").click()
    expect(dialog).to_be_hidden()
    expect(chat.user_bubbles).to_have_count(1)

    chat.page.get_by_role("button", name="Nová konverzácia").click()
    dialog.get_by_role("button", name="Začať novú").click()
    expect(chat.welcome).to_be_visible()
    expect(chat.user_bubbles).to_have_count(0)
    expect(chat.log).to_contain_text("Začali ste novú konverzáciu.")
    assert server.session().conversation == []


def test_an_api_error_gets_a_polite_message_and_the_chat_goes_on(chat, model):
    model.script(tg.api_error(tg.anthropic.BadRequestError, 400,
                              {"type": "error", "error": {"type": "invalid_request_error", "message": "boom"}}))
    chat.send("Dobrý deň")
    expect(chat.errors).to_contain_text("odpoveď sa teraz nepodarilo pripraviť")
    expect(chat.errors).not_to_contain_text("boom")  # never the raw API error

    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.send("Dobrý deň")
    expect(chat.bot_bubbles.last).to_contain_text("Do akej miestnosti")


def test_the_composer(chat, model):
    expect(chat.send_button).to_be_disabled()  # nothing to send
    chat.input.fill("Spálňa")
    chat.input.press("Shift+Enter")  # a new line, not a message
    expect(chat.user_bubbles).to_have_count(0)
    expect(chat.send_button).to_be_enabled()

    chat.input.fill("x" * 700)  # the counter shows up near the 800-character limit
    expect(chat.page.get_by_text("700 / 800")).to_be_visible()

    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.input.fill("Dobrý deň")
    chat.send_button.click()
    chat.wait_for_reply()
    expect(chat.input).to_have_value("")
    expect(chat.bot_bubbles).to_have_count(1)


def test_rating_a_reply_reaches_the_log(chat, model, server):
    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.send("Dobrý deň")
    useful = chat.log.get_by_role("button", name="Užitočná odpoveď", exact=True)

    useful.click()
    expect(useful).to_have_attribute("aria-pressed", "true")
    expect(chat.page.get_by_text("Ďakujeme za hodnotenie.")).to_be_visible()
    assert '"reply_feedback"' in server.log_text()  # the toast shows after the server answered


# ---------- phones ----------

@pytest.mark.browser_context_args(**PHONE)
def test_on_a_phone_the_pm_record_is_a_tab_with_a_notice(chat, model):
    tabs = chat.page.get_by_role("tablist", name="Zobrazenie")
    expect(tabs).to_be_visible()
    expect(chat.brief).to_be_hidden()  # one panel at a time

    tabs.get_by_role("tab", name="Zápis pre PM").click()
    expect(chat.brief).to_be_visible()
    expect(chat.brief).to_contain_text("Zápis vznikne po súhlase")
    tabs.get_by_role("tab", name="Rozhovor").click()

    make_offer(chat, model)
    choose_and_consent(chat, model)
    toast = chat.page.get_by_text("Zápis pre projektového manažéra je pripravený.")
    expect(toast).to_be_visible()
    chat.page.get_by_role("button", name="Zobraziť").click()
    expect(chat.brief).to_be_visible()
    expect(chat.brief).to_contain_text("Ján Testovací")
    expect(tabs.get_by_role("tab", name="Zápis pre PM")).to_have_attribute("aria-selected", "true")
