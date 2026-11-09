"""Fixtures for the browser tests: the real web app with a scripted model.

The browser is real (Playwright's Chromium), and so are web/web.py, bot.py and the page. Only the
Anthropic client is replaced by the scripted FakeClient of tests/test_guards.py, so every run gives the
same replies, costs nothing and needs no key or network. What the model would say is the evals' job
(eval/); these tests check everything between the model and the customer's screen.

Run:  .venv/bin/python -m pytest            (pyproject.toml points pytest at tests/e2e)
      .venv/bin/python -m pytest --headed --slowmo 300   (watch it)
A failed test keeps its trace and screenshot in test-results/: `playwright show-trace <trace.zip>`.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

TESTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TESTS_DIR))

# Before bot is imported (load_dotenv never overrides): no real key, the public demo's settings.
os.environ["ANTHROPIC_API_KEY"] = "test-no-network"
os.environ["KLIMABOT_DEMO"] = "1"
os.environ.pop("KLIMABOT_REPO_URL", None)

# test_guards points bot's output (logs, leads, PM records) at a temp dir, blanks the PM e-mail and
# loads web/web.py; its fake model and helpers are shared with the unit tests.
import test_guards as tg  # noqa: E402

bot, web, cost_report = tg.bot, tg.web, tg.cost_report


class _NoModel:
    """The client between tests: a call nobody scripted fails instead of reaching the API."""

    @property
    def messages(self):
        return self

    def create(self, **_kw):
        raise AssertionError("the model was called but the test scripted no response")


bot.client = _NoModel()

# Everything here answers in milliseconds (no model, no network): a check that waits 10 s has failed,
# and the 30 s default only makes a broken run slow.
expect.set_options(timeout=10_000)


# ---------- the app ----------

@pytest.fixture(scope="session")
def base_url():
    """The real Flask app in a thread on a free port (pytest-playwright resolves page.goto("/") against it)."""
    server = make_server("127.0.0.1", 0, web.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, name="klimabot-e2e", daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(5)


class _ErrorLog(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.records = []

    def emit(self, record):
        self.records.append(self.format(record))


@pytest.fixture(autouse=True)
def fresh_server():
    """Every test starts on a server nobody has visited today: no sessions, no rate-limit hits, no spend.
    An exception in a request (web.py logs it and shows the visitor a generic error) fails the test."""
    for table in (web._visitors, web._hits, web._in_flight, web._reserved["per_ip"]):
        table.clear()
    web._reserved["total"] = 0.0
    web._ledger.clear()
    web._ledger.update(web._fresh_ledger())
    bot._BREAKER.update(until=0, reason=None)
    tg.THINKING_PREFIXES.clear()
    errors = _ErrorLog()
    web.log.addHandler(errors)
    yield
    web.log.removeHandler(errors)
    bot.client = _NoModel()
    assert not errors.records, "the server failed a request:\n" + "\n".join(errors.records)


# ---------- the model ----------

class Model:
    """The scripted model: model.replies("text") or model.script(resp(...), ...) before each message."""

    def __init__(self):
        self.client = None

    def script(self, *responses):
        self.assert_used()
        self.client = bot.client = tg.FakeClient(responses)
        return self.client

    def replies(self, *texts):
        """One plain reply per model call (a regeneration needs its own)."""
        return self.script(*(tg.resp(tg.text(t)) for t in texts))

    def assert_used(self):
        if self.client is not None:
            assert self.client.responses == [], f"scripted responses never used: {self.client.responses}"


@pytest.fixture
def model():
    m = Model()
    yield m
    m.assert_used()


# ---------- the page ----------

@pytest.fixture
def guard_page(base_url):
    """Fails the test on a JavaScript error, a console error or a request to another site
    (the page must load everything from this server, as its Content-Security-Policy promises)."""
    host = urlsplit(base_url).netloc

    def attach(page):
        problems = []
        page.on("pageerror", lambda exc: problems.append(f"page error: {exc}"))
        page.on("console", lambda msg: msg.type == "error" and problems.append(f"console error: {msg.text}"))

        def only_this_server(route):
            url = urlsplit(route.request.url)
            if url.scheme in ("data", "blob") or url.netloc == host:
                return route.continue_()
            problems.append(f"request to another site: {route.request.url}")
            return route.abort()

        page.route("**/*", only_this_server)
        return problems

    attached = []
    yield lambda page: attached.append(attach(page)) or page
    for problems in attached:
        assert not problems, "\n".join(problems)


class ChatPage:
    """The chat as the customer sees it. Locators go by role and accessible name where the page has one,
    so a test reads like the steps a customer takes and survives a CSS refactor; the chat bubbles have no
    role, so they are found by class."""

    def __init__(self, page):
        self.page = page
        self.input = page.get_by_label("Vaša správa")
        self.send_button = page.get_by_role("button", name="Odoslať správu")
        self.log = page.get_by_role("log", name="Správy")
        self.bot_bubbles = self.log.locator(".row.bot .bubble.md")
        self.user_bubbles = self.log.locator(".row.user .bubble")
        self.price_cards = self.log.get_by_role("region", name="Cenová ponuka")
        self.consent = self.log.get_by_role("group", name="Rýchla odpoveď")
        self.errors = self.log.get_by_role("alert")
        self.brief = page.get_by_role("complementary", name="Zápis pre projektového manažéra")
        self.welcome = page.get_by_role("heading", name="Dobrý deň, som Klimabot")

    def open(self, path="/"):
        self.page.goto(path)
        # The demo notice is shown once /api/config has answered.
        expect(self.page.get_by_role("complementary", name="Upozornenie k ukážke")).to_contain_text("Ukážka")
        return self

    def send(self, text):
        self.input.fill(text)
        self.input.press("Enter")
        self.wait_for_reply()

    def wait_for_reply(self):
        # The typing row goes in the same synchronous step that frees the composer (sendMessage's finally).
        expect(self.log.locator(".row.typing")).to_have_count(0)


@pytest.fixture
def chat(page, guard_page):
    """The chat page, opened and ready (session created, demo settings loaded)."""
    return ChatPage(guard_page(page)).open()


@pytest.fixture
def server():
    """What the server holds for the one visitor of the test."""
    class Server:
        @staticmethod
        def visitor():
            (v,) = web._visitors.values()
            return v

        def session(self):
            return self.visitor().session

        def log_text(self):
            path = self.session().log_path
            return path.read_text(encoding="utf-8") if path.exists() else ""
    return Server()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Slovak, as the page's visitors are (numbers are formatted with the browser's locale)."""
    return {**browser_context_args, "locale": "sk-SK", "timezone_id": "Europe/Bratislava"}
