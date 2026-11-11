"""Phones: the on-screen keyboard, small screens, and the motion a reload must not replay.

A headless browser has no on-screen keyboard, so the keyboard is played the way iOS Safari plays it: the visual viewport
(the part of the page the visitor sees) shrinks and pans down to the message box, while the page itself keeps its size.
The page must follow it (fitViewport in index.html). Chrome on Android resizes the layout too
(interactive-widget=resizes-content), which the same code handles as an ordinary resize.
"""
import pytest
from playwright.sync_api import expect

from conftest import ChatPage
from test_chat import PHONE, make_offer

# Replaces window.visualViewport before the page runs; window.__keyboard(height, top) opens or closes the keyboard.
FAKE_KEYBOARD = """
(() => {
  const real = window.visualViewport;
  const fake = new EventTarget();
  const state = { height: null, top: 0 };
  for (const key of ["width", "offsetLeft", "pageLeft", "scale"]) Object.defineProperty(fake, key, { get: () => real[key] });
  Object.defineProperty(fake, "height", { get: () => state.height ?? real.height });
  Object.defineProperty(fake, "offsetTop", { get: () => state.top });
  Object.defineProperty(fake, "pageTop", { get: () => state.top });
  Object.defineProperty(window, "visualViewport", { configurable: true, get: () => fake });
  window.__keyboard = (height, top) => { state.height = height; state.top = top; fake.dispatchEvent(new Event("resize")); };
})();
"""
LONG_REPLY = ("Rád vám pomôžem. Aby som vedel odporučiť vhodný výkon, potrebujem vedieť, do akej miestnosti klimatizáciu "
              "hľadáte a koľko má približne m². Napíšte mi aj, čo je pre vás najdôležitejšie: tichý chod, filtrácia "
              "vzduchu, ovládanie cez Wi-Fi alebo čo najnižšia cena.")


def box(locator):
    b = locator.bounding_box()
    return round(b["y"]), round(b["y"] + b["height"])


@pytest.mark.browser_context_args(**PHONE)
def test_the_keyboard_never_hides_the_header_or_the_message_box(page, guard_page, model):
    page.add_init_script(FAKE_KEYBOARD)
    chat = ChatPage(guard_page(page)).open()
    for question in ("Dobrý deň", "Chcem klimatizáciu", "Do bytu"):  # enough conversation to scroll
        model.replies(LONG_REPLY)
        chat.send(question)
    tabs = page.get_by_role("tablist", name="Zobrazenie")
    expect(tabs).to_be_visible()

    chat.input.focus()
    page.evaluate("window.__keyboard(500, 300)")  # 415 px of keyboard; the browser panned 300 px down to the box
    expect(page.locator("html.kb-open")).to_have_count(1)
    assert box(page.locator("body")) == (300, 800), "the app fills exactly the part of the screen the visitor sees"
    header_top, _ = box(page.get_by_role("banner"))
    _, input_bottom = box(chat.input)
    assert header_top >= 300 and input_bottom <= 800
    messages_top, messages_bottom = box(page.locator("#messages"))
    _, reply_bottom = box(chat.bot_bubbles.last)
    assert messages_top < reply_bottom <= messages_bottom, "the latest reply stays in view"
    expect(tabs).to_be_hidden()  # the tabs make way while the keyboard is up…
    expect(page.get_by_role("complementary", name="Upozornenie k ukážke")).to_be_visible()  # …the demo notice doesn't

    page.evaluate("window.__keyboard(915, 0)")  # the keyboard closes
    expect(tabs).to_be_visible()
    assert box(page.locator("body")) == (0, 915)


@pytest.mark.browser_context_args(**PHONE)
def test_small_phones_never_scroll_sideways(chat, model):
    make_offer(chat, model)  # the widest things on the page: two price cards and a long reply
    for width, height in ((320, 568), (360, 640), (375, 667), (412, 915)):
        chat.page.set_viewport_size({"width": width, "height": height})
        overflow = chat.page.evaluate("""() => {
            const wider = (el) => el.scrollWidth > el.clientWidth + 1;
            const out = [...document.querySelectorAll('.app-header, .demo-strip, .view-tabs, #messages, .quote-card, .composer')]
              .filter((el) => wider(el) || el.getBoundingClientRect().right > innerWidth + 1).map((el) => el.className || el.id);
            if (document.documentElement.scrollWidth > innerWidth + 1) out.push('the page');
            return out;
        }""")
        assert not overflow, f"{width}×{height}: wider than the screen: {overflow}"
        expect(chat.send_button).to_be_in_viewport()
        expect(chat.price_cards.last.get_by_role("button", name="Toto chcem")).to_be_attached()


@pytest.mark.browser_context_args(**{**PHONE, "viewport": {"width": 390, "height": 560}})
def test_a_short_phone_opens_the_welcome_card_at_its_top(chat):
    # The first deploy of fitViewport kept "the latest message" in view on load, and on a short screen that
    # was the bottom of the welcome card, its heading scrolled away.
    expect(chat.welcome).to_be_in_viewport()
    assert chat.page.evaluate("document.getElementById('messages').scrollTop") == 0


def test_a_reload_does_not_replay_the_entrances(chat, model):
    entrances = "() => document.getAnimations().filter((a) => document.getElementById('message-list').contains(a.effect && a.effect.target)).length"
    model.replies("Do akej miestnosti hľadáte klimatizáciu a koľko má m²?")
    chat.send("Dobrý deň")
    assert chat.page.evaluate(entrances) > 0, "a new message comes in with an animation"

    chat.page.reload()
    expect(chat.bot_bubbles).to_have_count(1)
    assert chat.page.evaluate(entrances) == 0, "the rebuilt conversation is simply there"
