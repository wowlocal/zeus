"""``/command@ourbot args`` from Telegram's group command menu reaches the gateway as ``/command args``.

Driven through the adapter's real command entry point (``_handle_command``).
"""

import asyncio
import re
from types import SimpleNamespace

import pytest

from tests.gateway.test_telegram_group_gating import _group_message, _make_adapter


def _telegram_entities(text):
    return [SimpleNamespace(
        type="bot_command" if m.group().startswith("/") else "mention",
        offset=len(text[:m.start()].encode("utf-16-le")) // 2,
        length=len(m.group().encode("utf-16-le")) // 2,
    ) for m in re.finditer(r"/[A-Za-z0-9_]+(?:@[A-Za-z0-9_]{1,32})?|@[A-Za-z0-9_]{1,32}", text)]


def _dispatch(text, *, adapter=None, entities=None):
    adapter = adapter or _make_adapter(require_mention=True)
    seen = []

    async def _capture(event):
        seen.append(event)

    adapter.handle_message = _capture
    adapter._enqueue_text_event = seen.append
    msg = _group_message(text, entities=_telegram_entities(text) if entities is None else entities)
    handler = adapter._handle_command if text.startswith("/") else adapter._handle_text_message
    asyncio.run(handler(SimpleNamespace(update_id=7, message=msg, effective_message=msg), SimpleNamespace()))
    return seen


def _dispatched_command(text):
    seen = _dispatch(text)
    assert len(seen) == 1, "the addressed command was not dispatched"
    return seen[0]


@pytest.mark.parametrize("text, command, args", [
    ("/reasoning@zeus_bot medium", "reasoning", "medium"),
    ("/reasoning@zeus_bot: high --global", "reasoning", "high --global"),
    ("/memory@zeus_bot approve abc123", "memory", "approve abc123"),
    ("/new@zeus_bot", "new", ""),
    ("@zeus_bot /model@zeus_bot gpt-5", "model", "gpt-5"),
    ("@zeus_bot, /model gpt-5", "model", "gpt-5"),
    ("/btw did @zeus_bot already answer Alice?", "btw", "did @zeus_bot already answer Alice?"),
    ("/btw@zeus_bot did @zeus_bot already answer?", "btw", "did @zeus_bot already answer?"),
    ("/btw 👋 did @zeus_bot already answer?", "btw", "👋 did @zeus_bot already answer?"),
    ("/model @zeus_bot gpt-5", "model", "gpt-5"),
    ("/model gpt-5 @zeus_bot", "model", "gpt-5"),
    ("/model gpt-5 @zeus_bot @zeus_bot", "model", "gpt-5"),
    ("/reasoning high @zeus_bot --global", "reasoning", "high --global"),
    ("/reasoning high @zeus_bot @zeus_bot --global", "reasoning", "high --global"),
    ("/btw did @zeus_bot — our helper — already answer?", "btw", "did @zeus_bot — our helper — already answer?"),
    ("/x a @zeus_bot --level 3", "x", "a --level 3"),
    ("/x a @zeus_bot -v", "x", "a -v"),
    ("/x a @zeus_bot —global", "x", "a —global"),
    ("/x a @zeus_bot –global", "x", "a –global"),
    ("/reload-mcp@zeus_bot x", "reload-mcp", "x"),
])
def test_command_menu_form_keeps_its_arguments(text, command, args):
    event = _dispatched_command(text)
    assert event.get_command() == command
    assert event.text == f"/{command} {args}".rstrip()
    assert event.get_command_args() == args.replace("—", "--").replace("–", "-")


def test_prose_mention_cleanup_is_unchanged():
    adapter = _make_adapter(require_mention=True)
    assert adapter._clean_bot_trigger_text("@zeus_bot, summarize this") == "summarize this"
    assert adapter._clean_bot_trigger_text("thanks @zeus_bot") == "thanks"


@pytest.mark.parametrize("text, expected", [
    ("@zeus_bot /new@zeus_bot/log.txt", "/new/log.txt"),
    ("/new@zeus_bot/log.txt", "/new /log.txt"),
    ("@zeus_bot /new@alice/log.txt is missing", "/new@alice/log.txt is missing"),
    ("/file.txt is missing", "/file.txt is missing"),
    ("/file-name.txt mentions @zeus_bot here", "/file-name.txt mentions here"),
    ("@zeus_bot , @ops_bot are you both listening?", "@zeus_bot , @ops_bot are you both listening?"),
    ("@zeus_bot", "@zeus_bot"),
    ("@zeus_bot, summarize this", "summarize this"),
    ("thanks @zeus_bot", "thanks"),
    ("/new", "/new"),
    ("@zeus_bot /new", "/new"),
    ("@file: /model@zeus_bot gpt-5", "@file: /model@zeus_bot gpt-5"),
    ("/set-home @zeus_bot", "/set-home"),
    ("/codex-runtime", "/codex-runtime"),
    ("/reload-mcp x", "/reload-mcp x"),
    ("@alice /model@OtherBot failed; @zeus_bot can you explain?",
     "@alice /model@OtherBot failed; @zeus_bot can you explain?"),
    ("/model@zeus_bot gpt-5 @OtherBot", "/model@zeus_bot gpt-5 @OtherBot"),
    ("@zeus_bot /btw ask @alice", "@zeus_bot /btw ask @alice"),
])
def test_other_inputs_keep_parent_behavior(text, expected):
    entities = _telegram_entities(text)
    if text.endswith("/new"):
        next(e for e in entities if e.type == "bot_command").type = "code"
    events = _dispatch(text, adapter=_make_adapter(require_mention=False), entities=entities)
    assert [e.text for e in events] == [expected]


def test_full_length_bot_username_keeps_parent_behavior():
    username = "a" * 32
    events = _dispatch(f"/model@{username} gpt-5", adapter=_make_adapter(bot_username=username))
    assert [e.text for e in events] == ["/model gpt-5"]


def test_path_without_entities_keeps_parent_behavior():
    text = "@zeus_bot /new@alice/log.txt is missing"
    assert [e.text for e in _dispatch(text, entities=[])] == ["/new@alice/log.txt is missing"]
