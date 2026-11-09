"""Accessibility: axe-core scans every state of the page a visitor reaches, against WCAG 2.2 A and AA and axe's
best practices, in both themes and on a phone. Plus the keyboard paths axe can't judge.

axe-core is the pinned copy inside the axe-playwright-python package (its version in the file's header), run straight
in the page. The scans use reduced motion, which the page honours: mid-animation a fading bubble's colours read as a
contrast failure that no visitor sees.
"""
from pathlib import Path

import axe_playwright_python
import pytest
from playwright.sync_api import expect

from test_chat import PHONE, choose_and_consent, make_offer

AXE_SOURCE = (Path(axe_playwright_python.__file__).parent / "axe.min.js").read_text(encoding="utf-8")
STANDARDS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]
STILL = {"reduced_motion": "reduce"}


def assert_accessible(page, state):
    """No axe violation on the page as it is now."""
    page.evaluate(AXE_SOURCE)
    result = page.evaluate("standards => axe.run(document, {runOnly: {type: 'tag', values: standards}})", STANDARDS)
    found = [f"{v['id']} ({v['impact']}): {v['help']}\n    " + "\n    ".join(
                 f"{', '.join(n['target'])}: {n['failureSummary'].splitlines()[-1].strip()}" for n in v["nodes"][:5])
             for v in result["violations"]]
    assert not found, f"{state}: {len(found)} accessibility violation(s)\n  " + "\n  ".join(found)


@pytest.mark.browser_context_args(**STILL)
def test_the_whole_sales_path_is_accessible(chat, model):
    assert_accessible(chat.page, "welcome")
    make_offer(chat, model)
    assert_accessible(chat.page, "offer with price cards")
    choose_and_consent(chat, model)
    assert_accessible(chat.page, "after consent, with the PM record")
    chat.page.get_by_role("button", name="Nová konverzácia").click()
    expect(chat.page.get_by_role("dialog")).to_be_visible()
    assert_accessible(chat.page, "reset dialog")


@pytest.mark.browser_context_args(color_scheme="dark", **STILL)
def test_the_dark_theme_is_accessible(chat, model):
    make_offer(chat, model)
    model.replies("Výborne, Samsung AR35 WIFI. Napíšte mi prosím meno a telefónne číslo.")
    chat.send("Beriem ten Samsung.")
    expect(chat.consent).to_be_visible()  # the consent buttons, the page's other filled buttons
    assert_accessible(chat.page, "dark theme")


@pytest.mark.browser_context_args(**STILL)
def test_the_debugging_view_is_accessible(chat, model):
    chat.page.get_by_text("Ladenie", exact=True).click()
    make_offer(chat, model)  # tool chips and the bot's notes
    assert_accessible(chat.page, "debugging view")


@pytest.mark.browser_context_args(**PHONE, **STILL)
def test_the_phone_layout_is_accessible(chat, model):
    assert_accessible(chat.page, "phone, chat")
    chat.page.get_by_role("tab", name="Zápis pre PM").click()
    assert_accessible(chat.page, "phone, PM record tab")


# ---------- the keyboard ----------

def test_a_conversation_works_from_the_keyboard(chat, model):
    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    page = chat.page
    page.keyboard.press("Tab")
    for _ in range(30):  # Tab through the page until the message box has the focus
        if page.evaluate("document.activeElement.id") == "input":
            break
        page.keyboard.press("Tab")
    expect(chat.input).to_be_focused()
    page.keyboard.type("Dobrý deň")
    page.keyboard.press("Enter")
    chat.wait_for_reply()
    expect(chat.bot_bubbles).to_have_count(1)
    expect(chat.input).to_be_focused()  # back in the message box for the next one


@pytest.mark.browser_context_args(**PHONE)
def test_the_phone_tabs_follow_the_arrow_keys(chat):
    tabs = chat.page.get_by_role("tablist", name="Zobrazenie")
    tabs.get_by_role("tab", name="Rozhovor").focus()
    chat.page.keyboard.press("ArrowRight")
    expect(tabs.get_by_role("tab", name="Zápis pre PM")).to_be_focused()
    expect(tabs.get_by_role("tab", name="Zápis pre PM")).to_have_attribute("aria-selected", "true")
    expect(chat.brief).to_be_visible()
    chat.page.keyboard.press("ArrowLeft")
    expect(tabs.get_by_role("tab", name="Rozhovor")).to_have_attribute("aria-selected", "true")
