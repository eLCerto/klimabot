"""Stand-in for `anthropic.Anthropic().messages.create` that runs the model through
the local Claude Code CLI (`claude -p`), i.e. on the Claude subscription login
instead of an API key.

The CLI can't take custom tool definitions, so tools are described in the prompt
and the model calls them with <tool_call name="...">{json}</tool_call> blocks.
The adapter turns those into tool_use content blocks with stop_reason "tool_use",
so bot.py's loop, validator, quote() and guards run exactly as in production.

Differences from the API (documented in the eval report):
- prompted tool calling instead of native tool use;
- tool schemas live in the system prompt, the customer state and regen notes
  in the user message (the system prompt stays identical across calls so the
  CLI can cache it);
- the CLI adds ~800 tokens of its own context (environment, date);
- no max_tokens limit.

Pass the production model ID (bot.MODEL): the CLI's "haiku" alias moves on with new releases. Haiku 5.5 thinks
here although production turns thinking off (see __init__), so CLI figures don't carry over to production.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx

TOOL_PROTOCOL = """
=== NÁSTROJE ===
Môžeš volať nástroje opísané nižšie (JSON schémy). Nástroj zavoláš blokom presne v tomto tvare:
<tool_call name="NÁZOV_NÁSTROJA">{"argument": "hodnota"}</tool_call>
- JSON musí byť platný a zodpovedať input_schema nástroja. V jednej správe môžeš zavolať viac nástrojov.
- Text mimo blokov tool_call vidí zákazník. Pred volaniami napíš najviac krátku vetu (alebo nič) a správu ukonči hneď za posledným blokom tool_call.
- Výsledky dostaneš v ďalšej výzve v blokoch <tool_result>. Nikdy ich nepíš sám a nevymýšľaj si ich.
- Správa bez bloku tool_call je tvoja konečná odpoveď zákazníkovi v tomto kole.
- Ignoruj informácie o prostredí, dátume či e-maile, ktoré pridáva runtime — nie sú súčasťou rozhovoru.
<tools>
{tools}
</tools>
"""

_TOOL_CALL_RE = re.compile(r'<tool_call\s+name="([^"]+)"\s*>(.*?)</tool_call>', re.DOTALL)
_CUT_RE = re.compile(r"<(?:tool_result|customer|/?tool_results|/?server_context)\b")


def find_claude_cli():
    """CLAUDE_CLI env var, `claude` on PATH, or the newest VS Code extension binary."""
    if os.getenv("CLAUDE_CLI"):
        return os.environ["CLAUDE_CLI"]
    if shutil.which("claude"):
        return shutil.which("claude")
    pattern = str(Path.home() / ".vscode" / "extensions" / "anthropic.claude-code-*" / "resources" / "native-binary" / "claude*")
    found = sorted(glob.glob(pattern), key=lambda p: [int(x) for x in re.findall(r"\d+", Path(p).parts[-4])])
    if not found:
        raise SystemExit("claude CLI not found — set CLAUDE_CLI to its path.")
    return found[-1]


def _field(block, name, default=None):
    return block.get(name, default) if isinstance(block, dict) else getattr(block, name, default)


def _system_text(system):
    if isinstance(system, str):
        return [system]
    return [b["text"] for b in system]


def render_transcript(messages):
    names = {}
    out = []
    for msg in messages:
        content = msg["content"]
        if msg["role"] == "user":
            if isinstance(content, str):
                out.append(f"<customer>\n{content}\n</customer>")
                continue
            results, texts = [], []
            for block in content:
                btype = _field(block, "type")
                if btype == "text":  # the customer's message, or bot.py's per-call <server_context> block
                    text = _field(block, "text")
                    texts.append(text if text.startswith("<server_context>") else f"<customer>\n{text}\n</customer>")
                if btype != "tool_result":
                    continue
                tid = _field(block, "tool_use_id")
                err = "true" if _field(block, "is_error") else "false"
                results.append(f'<tool_result id="{tid}" name="{names.get(tid, "?")}" is_error="{err}">\n'
                               f'{_field(block, "content")}\n</tool_result>')
            if results:
                out.append("<tool_results>\n" + "\n".join(results) + "\n</tool_results>")
            out.extend(texts)
        else:
            if isinstance(content, str):
                out.append(f"<assistant>\n{content}\n</assistant>")
                continue
            parts = []
            for block in content:
                btype = _field(block, "type")
                if btype == "text" and _field(block, "text"):
                    parts.append(_field(block, "text"))
                elif btype == "tool_use":
                    names[_field(block, "id")] = _field(block, "name")
                    parts.append(f'<tool_call name="{_field(block, "name")}">'
                                 f'{json.dumps(_field(block, "input"), ensure_ascii=False)}</tool_call>')
            out.append("<assistant>\n" + "\n".join(parts) + "\n</assistant>")
    return "\n\n".join(out)


def parse_reply(text):
    """Split the model's raw output into (customer text, [(tool name, input dict)])."""
    text = text.strip()
    text = re.sub(r"^<assistant>\s*|\s*</assistant>$", "", text)
    cut = _CUT_RE.search(text)
    if cut:  # the model started inventing the next prompt — drop it
        text = text[:cut.start()].rstrip()
    calls = []
    for m in _TOOL_CALL_RE.finditer(text):
        raw = m.group(2).strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        # raw_decode tolerates text the model wrote after the JSON object.
        value, _ = json.JSONDecoder().raw_decode(raw)  # JSONDecodeError → caller retries
        calls.append((m.group(1).strip(), value))
    first = _TOOL_CALL_RE.search(text)
    reply = text[:first.start()].rstrip() if first else text
    return reply, calls


class ClaudeCLIClient:
    def __init__(self, model="haiku", timeout=300, retries=3, log_dir=None, effort=None):
        self.exe = find_claude_cli()
        self.model = model
        self.effort = effort
        self.timeout = timeout
        self.retries = retries
        self.cwd = Path(tempfile.gettempdir()) / "klimabot_cli_cwd"  # outside the repo: no CLAUDE.md
        self.cwd.mkdir(exist_ok=True)
        self.log_dir = Path(log_dir) if log_dir else None
        self.messages = self  # so `client.messages.create(...)` works
        env = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
        # Production runs without extended thinking. Haiku 5.5 thinks anyway: this, --thinking disabled and the
        # other CLI switches don't stop its adaptive thinking (checked 2026-10-30; modelUsage.thinkingTokens > 0).
        env["MAX_THINKING_TOKENS"] = "0"
        self.env = env

    def _run(self, system_prompt, prompt):
        # The system prompt goes in a file: as an argument, persona + checklist + tool schemas
        # would pass Windows' 32 767-character command-line limit.
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", dir=self.cwd, delete=False) as f:
            f.write(system_prompt)
        cmd = [self.exe, "-p", "--model", self.model, "--output-format", "json",
               "--system-prompt-file", f.name, "--tools", "", "--strict-mcp-config",
               "--disable-slash-commands", "--setting-sources", "local", "--no-session-persistence"]
        if self.effort:
            cmd += ["--effort", self.effort]
        last_error = None
        try:
            for attempt in range(self.retries):
                try:
                    proc = subprocess.run(cmd, input=prompt, capture_output=True, encoding="utf-8",
                                          errors="replace", cwd=self.cwd, env=self.env, timeout=self.timeout)
                    data = json.loads(proc.stdout)
                    if data.get("is_error"):
                        message = data.get("result") or "CLI error"
                        if "limit" in message.lower():  # subscription limit: retrying won't help
                            raise anthropic.APIError(f"claude CLI failed: {message}",
                                                     httpx.Request("POST", "http://claude-cli.local"), body=None)
                        raise RuntimeError(message)
                    return data
                except (subprocess.TimeoutExpired, json.JSONDecodeError, RuntimeError) as e:
                    last_error = e
                    time.sleep(5 * (attempt + 1))
        finally:
            os.unlink(f.name)
        raise anthropic.APIError(f"claude CLI failed: {last_error}",
                                 httpx.Request("POST", "http://claude-cli.local"), body=None)

    def create(self, model=None, max_tokens=None, system="", messages=(), tools=None, tool_choice=None, **_):
        blocks = _system_text(system)
        if tools:
            # Stable part (persona + critical rules + tools) in the system prompt; the
            # per-turn blocks (customer state, regen note) go into the user message.
            tools_json = json.dumps(tools, ensure_ascii=False, separators=(",", ":"))
            system_prompt = "\n\n".join(blocks[:2]) + "\n" + TOOL_PROTOCOL.replace("{tools}", tools_json)
            dynamic = "\n\n".join(blocks[2:])
            # tool_choice none: the turn's budget allows only a final answer (bot.py drops any tool call).
            # tool_choice any: the policy's offer turns and the regenerations that must call a tool — the API
            # enforces it, so the prompt has to as well, or CLI runs measure a bot without it.
            choice = (tool_choice or {}).get("type")
            task = ("Napíš konečnú odpoveď asistenta zákazníkovi, bez blokov tool_call." if choice == "none" else
                    "Napíš ďalšiu správu asistenta: musí obsahovať aspoň jeden blok tool_call (nástroj si vyber)."
                    if choice == "any" else "Napíš ďalšiu správu asistenta (text a/alebo bloky tool_call).")
            prompt = ((f"=== DODATOČNÉ SYSTÉMOVÉ INFORMÁCIE ===\n{dynamic}\n\n" if dynamic else "")
                      + "=== ROZHOVOR ===\n" + render_transcript(messages)
                      + f"\n\n=== ÚLOHA ===\n{task}")
        else:
            system_prompt = "\n\n".join(blocks)
            last = messages[-1]["content"]
            prompt = last if len(messages) == 1 and isinstance(last, str) else render_transcript(messages)

        data = self._run(system_prompt, prompt)
        raw = data.get("result") or ""
        try:
            reply, calls = parse_reply(raw) if tools else (raw.strip(), [])
        except json.JSONDecodeError as e:
            data = self._run(system_prompt, prompt + f"\n\n(Predošlý pokus mal neplatný JSON v tool_call: {e}. Napíš správu znova.)")
            raw = data.get("result") or ""
            try:
                reply, calls = parse_reply(raw)
            except json.JSONDecodeError as e2:  # surface as an API error: bot.py rolls the turn back
                raise anthropic.APIError(f"invalid tool_call JSON twice: {e2}",
                                         httpx.Request("POST", "http://claude-cli.local"), body=None)
        if self.log_dir:
            with (self.log_dir / "cli_calls.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "raw": raw, "tool_calls": [c[0] for c in calls],
                                    "usage": data.get("usage"), "cost_usd": data.get("total_cost_usd"),
                                    "model_usage": data.get("modelUsage")},
                                   ensure_ascii=False) + "\n")

        content = []
        if reply:
            content.append(SimpleNamespace(type="text", text=reply))
        for name, inp in calls:
            content.append(SimpleNamespace(type="tool_use", name=name, input=inp,
                                           id=f"toolu_{uuid.uuid4().hex[:20]}"))
        u = data.get("usage") or {}
        usage = SimpleNamespace(input_tokens=u.get("input_tokens", 0), output_tokens=u.get("output_tokens", 0),
                                cache_creation_input_tokens=u.get("cache_creation_input_tokens", 0),
                                cache_read_input_tokens=u.get("cache_read_input_tokens", 0))
        return SimpleNamespace(content=content, stop_reason="tool_use" if calls else "end_turn", usage=usage)
