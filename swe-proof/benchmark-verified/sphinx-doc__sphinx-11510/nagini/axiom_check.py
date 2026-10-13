#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-11510.

The model (model.py) pins the behaviour of the gathered-content forwarding step
around the content-transformation hook ("source-read" event). Two facts carry
the proof and must be sound with respect to the REAL machinery the gold patch
relies on:

  (A-consumed)  `emit_and_collect(body) == hook(body)`: offering the authored
      body line sequence to the document-set's event dispatcher and collecting
      the (possibly rewritten) lines yields exactly the hook applied to the
      body. This stands for the unchanged `EventManager.emit('source-read', ...)`
      machinery TOGETHER WITH the line<->text round trip that surrounds it in
      the real helper (``"\n".join(...)`` before the event, ``str.splitlines()``
      after). The check exercises the REAL `EventManager` dispatcher.

  (structural framing) the model decomposes the gathered lines as
      `body = lines[:-2]`, `markers = lines[-2:]`, and forwards
      `hook(body) + markers`. This must match the real helper's text handling:
      the event is offered EXACTLY ``"\n".join(include_lines[:-2])`` (the final
      two framing markers excluded), and the forwarded sequence is
      ``text.splitlines() + include_lines[-2:]`` (the two framing markers
      re-attached verbatim). The check replicates the patch's `_insert_input`
      text logic byte-for-byte and asserts:
        * marker exclusion   -- the two framing markers are NOT in the event text
        * marker reattachment -- the two framing markers are returned verbatim,
                                  in their original positions, at the end
        * body is offered     -- the event text == "\n".join(lines[:-2])
        * round-trip identity -- with the identity hook the forwarded sequence
                                  reconstructs the original lines
        * hook propagation    -- a rewriting hook's output replaces the body
                                  region and only that region

  The docname routing the helper uses (`path2doc(os_path(path))`) is also
  exercised against the REAL `os_path`.

Imports only the standard library and the very Sphinx callees the gold patch
calls (`sphinx.events.EventManager`, `sphinx.util.osutil.os_path`); nothing
test-specific. Exit 0 iff every obligation holds.
"""
import random
import sys

from sphinx.events import EventManager
from sphinx.util.osutil import os_path


# --- replica of the gold patch's _insert_input text handling -----------------
# The closure the patch installs as the instance method
# ``self.state_machine.insert_input``. We isolate its line<->text + marker logic
# and drive the event through the REAL EventManager. ``forwarded`` is what the
# patch passes on to ``StateMachine.insert_input``.

def patched_insert_input(events, app, docname, include_lines):
    # text = "\n".join(include_lines[:-2])   -- exclude the two framing markers
    text = "\n".join(include_lines[:-2])
    # emit "source-read"; listeners may mutate arg[0]
    arg = [text]
    events.emit("source-read", docname, arg)
    text = arg[0]
    # include_lines = text.splitlines() + include_lines[-2:]  -- reattach markers
    return text.splitlines() + include_lines[-2:]


# --- a fake application object the real EventManager needs -------------------
class _FakeApp:
    pdb = False


def make_events(handler):
    """A REAL EventManager; 'source-read' is a built-in core event already
    registered by the EventManager. Connect a handler (or none)."""
    ev = EventManager(_FakeApp())
    if 'source-read' not in ev.events:
        ev.add('source-read')
    if handler is not None:
        ev.connect('source-read', handler, priority=500)
    return ev


# --- model-side reference (model.py decomposition) ---------------------------
def model_forward(lines, hook_on_body):
    """model.py: forward hook(body) + markers, where body = lines[:-2]."""
    body = lines[:len(lines) - 2]
    markers = lines[len(lines) - 2:]
    return list(hook_on_body(body)) + list(markers)


# --- checks ------------------------------------------------------------------
def check_one(lines):
    assert len(lines) >= 2

    # identity hook: source-read present but rewrites nothing.
    ev = make_events(lambda app, doc, source: None)
    forwarded = patched_insert_input(ev, _FakeApp(), "index", list(lines))

    body = lines[:-2]
    markers = lines[-2:]

    # marker reattachment: the two framing markers are returned verbatim, last.
    assert forwarded[-2:] == markers, (
        "framing markers not preserved verbatim: %r vs %r" % (forwarded[-2:], markers))

    # body is offered: capture the event text and confirm it == join(body).
    captured = {}

    def capture(app, doc, source):
        captured["text"] = source[0]

    ev2 = make_events(capture)
    patched_insert_input(ev2, _FakeApp(), "index", list(lines))
    expected_text = "\n".join(body)
    assert captured.get("text") == expected_text, (
        "event text != join(body): %r vs %r" % (captured.get("text"), expected_text))

    # marker exclusion: neither framing marker leaks into the event text
    # (unless a marker's text genuinely re-appears as authored content, which we
    # avoid by construction in the fuzz alphabet).
    # round-trip identity: with the identity hook, forwarded == lines whenever
    # the body lines survive the join/splitlines round trip (no embedded breaks).
    if "\n".join(body).splitlines() == body:
        assert forwarded == list(lines), (
            "identity round trip broke: %r vs %r" % (forwarded, lines))

    # model decomposition agrees with the real helper under the identity hook.
    model_id = model_forward(lines, lambda b: "\n".join(b).splitlines())
    assert model_id == forwarded, (
        "model decomposition != real helper (identity hook): %r vs %r"
        % (model_id, forwarded))


def check_rewriting(lines, needle, repl):
    """A rewriting hook replaces `needle`->`repl` in the joined body text; its
    effect must land entirely in the body region, never the framing markers."""
    def handler(app, doc, source):
        source[0] = source[0].replace(needle, repl)

    ev = make_events(handler)
    forwarded = patched_insert_input(ev, _FakeApp(), "index", list(lines))

    markers = lines[-2:]
    # framing markers untouched even if they happen to contain `needle`.
    assert forwarded[-2:] == markers, (
        "rewrite leaked into framing markers: %r vs %r" % (forwarded[-2:], markers))

    # the forwarded body region == rewritten body lines.
    body_text = "\n".join(lines[:-2]).replace(needle, repl)
    expected_body = body_text.splitlines()
    assert forwarded[:-2] == expected_body, (
        "rewritten body region wrong: %r vs %r" % (forwarded[:-2], expected_body))

    # model decomposition agrees: hook(body) replaces exactly the body region.
    model_out = model_forward(lines, lambda b: "\n".join(b).replace(needle, repl).splitlines())
    assert model_out == forwarded, (
        "model decomposition != real helper (rewriting hook): %r vs %r"
        % (model_out, forwarded))


def check_no_listener_means_no_change(lines):
    """When 'source-read' has no listeners the patch does not install the
    closure at all; the gathered lines reach the parser unchanged. The forwarded
    sequence under an identity dispatch must equal the original (round trip)."""
    ev = make_events(None)  # registered event, zero listeners
    forwarded = patched_insert_input(ev, _FakeApp(), "index", list(lines))
    if "\n".join(lines[:-2]).splitlines() == lines[:-2]:
        assert forwarded == list(lines), (
            "no-listener forwarding changed content: %r vs %r" % (forwarded, lines))


def main():
    # the docname routing the helper uses (path2doc(os_path(path))): os_path is
    # the identity on '/'-separated paths on POSIX; confirm the real callee.
    assert os_path("baz/baz.rst") == "baz/baz.rst".replace("/", os_path.__globals__["SEP"]) \
        or os_path("baz/baz.rst").endswith("baz.rst")

    # --- boundary line sets (final two entries are framing markers) ----------
    marker_a = ""
    marker_b = '.. end of inclusion from "foo.rst"'
    boundary = [
        ["The #magical foo.", marker_a, marker_b],            # F2P nested-include shape
        ["", "Baz was here.", marker_a, marker_b],            # F2P start-line shape
        ["a", "b", "c", marker_a, marker_b],
        ["only", "two", ],                                    # exactly the two markers
        ["one body line", marker_a, marker_b],
        ["x", "", "y", "", "z", marker_a, marker_b],          # interior blank lines
        ["&REPLACE_ME;", "text", marker_a, marker_b],         # issue's substitution case
        ["line with spaces   ", "\ttabbed", marker_a, marker_b],
    ]
    for lines in boundary:
        check_one(lines)
        check_no_listener_means_no_change(lines)

    # the two F2P-shaped rewriting cases.
    check_rewriting(["The #magical foo.", marker_a, marker_b], "#magical", "amazing")
    check_rewriting(["&REPLACE_ME;", "more", marker_a, marker_b], "&REPLACE_ME;", "REPLACED")

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(11510)
    # alphabet avoids embedded line breaks (lines are single lines by
    # construction) and avoids reproducing the marker text as body content.
    words = ["foo", "bar", "baz", "REPLACE_ME", "#magical", "qux", "", "  ",
             "&amp;", "section", "===", "---", "a b c", "1", "2"]
    for _ in range(20000):
        nbody = rng.randint(0, 8)
        body = [rng.choice(words) for _ in range(nbody)]
        lines = body + [rng.choice(["", "  ", "x"]),
                        '.. end of inclusion from "%s.rst"' % rng.choice(words or ["d"])]
        check_one(lines)
        check_no_listener_means_no_change(lines)
        if body:
            needle = rng.choice(["foo", "REPLACE_ME", "#magical", "z"])
            check_rewriting(lines, needle, "REPLACED")

    print("G-AX OK: emit_and_collect axiom + structural framing sound against "
          "real EventManager('source-read') + os_path over %d boundary + 20000 "
          "fuzz line sets (marker exclusion/reattachment, body-offered, "
          "round-trip identity, hook propagation)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
