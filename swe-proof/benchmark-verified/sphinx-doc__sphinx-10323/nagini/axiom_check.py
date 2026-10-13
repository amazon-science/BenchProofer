#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10323.

The per-line left-margin trim is modelled DEEPLY in model.py (the pure function
`trim_block`, the per-line `PSeq.drop(n)`), NOT behind a consumed @ContractOnly
axiom.  G-AX therefore validates that deep model against the REAL trim callee
and validates the end-to-end refinement against the REAL assembly pipeline:

    sphinx.directives.code.dedent_lines(lines, dedent, location)
    sphinx.directives.code.LiteralIncludeReader.read()

Abstraction (mapping.md / refinement.md): a "line" in model.py is its CONTENT,
a `PSeq[int]` of code points WITHOUT the trailing newline; the newline is an
implicit line separator.  Rendering a model line `c` back to repo reality is
`c + "\\n"`.  Under that abstraction the per-line component of `trim_block`,
`c.drop(n)`, renders to exactly what the real `dedent_lines` produces for the
repo line `c + "\\n"` — the real callee's `line[dedent:]` plus its
empty-line/newline special case is absorbed by the separator.

Two checks:

  (A-reference) deep model `trim_block` (per line) == real `dedent_lines`, per
      line, over boundary + 200000 fuzz lines (incl. the empty-line /
      newline-special-case edge and over-long trim widths).

  (refinement / end-to-end) the REAL post-fix `LiteralIncludeReader.read()`
      with `dedent` set — and with `prepend`/`append` either set or absent —
      produces a block in which each author-supplied line is emitted VERBATIM
      (its indentation preserved) while the included lines are trimmed
      UNCONDITIONALLY, i.e. it equals model.py's `assemble` semantics
      `emit(lead) + trim_block(included) + emit(trail)`, over the issue scenario,
      the dedent-only scenarios (no author line at all) and randomized fuzz
      covering all four author-line presence combinations.  This is the property
      the gold reordering establishes.  The `emit` component is model.py's
      author-line PRESENCE rule (an empty option contributes no line), validated
      here against the real guarded author filters rather than assumed.

Imports the REAL sphinx under test (the module the gold patch edits); nothing is
stubbed except the file read (we feed the reader literal lines).  Exit 0 iff
every observation matches the deep model and the refinement holds.
"""
import os
import random
import sys
import tempfile

from sphinx.directives.code import dedent_lines, LiteralIncludeReader


# --- model.py deep-model reference (kept in lock-step with the pure region) --
# A model "line" is its content (no trailing newline); rendering is c + "\n".

def trim_line(content, n):
    """The per-line component of model.py `trim_block`: content[n:]
    (PSeq.drop(n))."""
    return content[n:]


def trim_block(contents, n):
    """model.py `trim_block`: per-line trim over a block of content lines."""
    return [trim_line(c, n) for c in contents]


def emit(line):
    """model.py `emit`: the contribution of ONE author line — the line itself
    when it has content, and NO line at all when it is empty."""
    return [] if len(line) == 0 else [line]


def assemble(included, lead, trail, n):
    """model.py `assemble`: each supplied author line verbatim, included lines
    trimmed unconditionally — as a list of content lines."""
    return emit(lead) + trim_block(included, n) + emit(trail)


def render(content_lines):
    """Render a block of model content lines back to repo text."""
    return "".join(c + "\n" for c in content_lines)


# --- real-callee harness ------------------------------------------------------

class _Config:
    source_encoding = "utf-8"


def make_reader(options):
    """A REAL LiteralIncludeReader with the given options (no file touched until
    read() is called)."""
    return LiteralIncludeReader("/dev/null", dict(options), _Config())


def check_trim_reference(content, n):
    """Assert deep model trim_line(content, n) renders to the REAL dedent_lines
    output for the repo line `content + '\\n'`."""
    real_line = dedent_lines([content + "\n"], n)[0]      # real callee
    model_line = trim_line(content, n) + "\n"             # deep model, rendered
    assert real_line == model_line, (
        "trim_line deep model unsound on content=%r n=%d: dedent_lines gave %r, "
        "deep model renders %r" % (content, n, real_line, model_line))


def check_pipeline_refinement(included, lead, trail, n):
    """Assert the REAL post-fix read() pipeline (dedent+prepend+append) equals
    the model `assemble` semantics: leading/trailing verbatim, included trimmed.

    We drive the real filters in the gold (post-fix) order directly, then also
    cross-check via the full read() with a temp file."""
    repo_included = [c + "\n" for c in included]

    # (1) Drive the REAL filter methods in the gold/post-fix order.
    reader = make_reader({"dedent": n, "prepend": lead, "append": trail})
    lines = list(repo_included)
    lines = reader.dedent_filter(lines)
    lines = reader.prepend_filter(lines)
    lines = reader.append_filter(lines)
    observed = "".join(lines)

    expected = render(assemble(included, lead, trail, n))
    assert observed == expected, (
        "pipeline refinement broken (filter methods): included=%r lead=%r "
        "trail=%r n=%d -> real %r, model %r"
        % (included, lead, trail, n, observed, expected))

    # A SUPPLIED author line must be present VERBATIM (the whole point); an
    # ABSENT one must contribute no line at all (the presence rule), which the
    # length check below pins together with the equality above.
    if lead:
        assert lines[0] == lead + "\n", (
            "leading line not verbatim: %r != %r" % (lines[0], lead + "\n"))
    if trail:
        assert lines[-1] == trail + "\n", (
            "trailing line not verbatim: %r != %r" % (lines[-1], trail + "\n"))
    assert len(lines) == len(emit(lead)) + len(included) + len(emit(trail)), (
        "author-line presence rule broken: included=%r lead=%r trail=%r n=%d -> "
        "%d line(s), model expects %d"
        % (included, lead, trail, n, len(lines),
           len(emit(lead)) + len(included) + len(emit(trail))))
    # The included text is trimmed WHETHER OR NOT an author line is supplied.
    offset = len(emit(lead))
    for k in range(len(included)):
        assert lines[offset + k] == trim_line(included[k], n) + "\n", (
            "included line %d not trimmed (lead=%r trail=%r n=%d): %r != %r"
            % (k, lead, trail, n, lines[offset + k],
               trim_line(included[k], n) + "\n"))

    # (2) Cross-check via the full real read() over a temp include file.
    fd, path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("".join(repo_included))
        reader2 = LiteralIncludeReader(
            path, {"dedent": n, "prepend": lead, "append": trail}, _Config())
        content, _ = reader2.read()
        assert content == expected, (
            "pipeline refinement broken (read()): included=%r lead=%r trail=%r "
            "n=%d -> real %r, model %r"
            % (included, lead, trail, n, content, expected))
    finally:
        os.unlink(path)


def main():
    # === (A-reference) deep model trim_block (per line) == real dedent_lines ==
    boundary = [
        ("", 0), ("", 2), ("", 5),
        ("def baz():", 0), ("def baz():", 1), ("def baz():", 4),
        ("    def baz():", 2), ("        pass", 2), ("        pass", 4),
        ("  ", 2), ("  ", 4), ("  x", 4), ("class Foo:", 2),
        ("# comment", 2), ("\t<plugin>", 1), ("      <plugin>", 6),
        ("a", 1), ("a", 2), ("ab", 3), ("abc", 100),
    ]
    for content, n in boundary:
        check_trim_reference(content, n)

    rng = random.Random(10323)
    alphabet = list(" \tabxyz#<>:_/")
    for _ in range(200000):
        L = rng.randint(0, 10)
        content = "".join(rng.choice(alphabet) for _ in range(L))
        n = rng.randint(0, 12)
        check_trim_reference(content, n)

    # === (refinement) real read() pipeline == model assemble =================
    # The model domain (model.py Requires) is just n >= 0: nothing is required of
    # the author lines, so an ABSENT one (the empty, falsy option that the real
    # prepend/append filters skip) is in-domain and is covered below. The trim is
    # driven by the dedent option alone, so it must reach the included text in
    # every one of those states.
    #
    # The issue scenario: lines 9-11 of the fixture, dedent 2, prepend class
    # header, append a trailing comment.
    check_pipeline_refinement(
        ["    def baz():", "        pass", ""], "class Foo:", "# comment", 2)
    # The original bug report scenario: an XML snippet with a prepended,
    # already-indented opening tag that must NOT be dedented.
    check_pipeline_refinement(
        ["        <groupId>x</groupId>", "      </plugin>"],
        "      <plugin>", "# end", 1)

    bnd_pipe = [
        (["    a", "      b", ""], "HEAD", "TAIL", 2),
        (["x", "y"], "  indented head", "  indented tail", 4),
        (["        deep", "    less"], "lead", "trail", 8),
        ([""], "p", "a", 1),
        (["only"], "L", "T", 3),
        ([], "L", "T", 2),
        # No author line at all: the dedent-only scenarios. The trim must still
        # reach every included line and no line may be invented in the absent
        # author lines' place.
        (["    def baz():", "        pass", ""], "", "", 2),
        (["    def baz():", "        pass", ""], "", "", 4),
        (["    def baz():", "        pass", ""], "", "", 6),
        (["    def quux(self):", "        pass"], "", "", 4),
        ([""], "", "", 1),
        ([], "", "", 2),
        (["  "], "", "", 4),
        # Exactly one author line supplied.
        (["    a", "      b"], "HEAD", "", 2),
        (["    a", "      b"], "", "TAIL", 2),
        ([], "HEAD", "", 1),
        ([], "", "TAIL", 1),
        # Zero-width trim (the identity), with and without author lines.
        (["    a", "      b"], "HEAD", "TAIL", 0),
        (["    a", "      b"], "", "", 0),
        ([], "", "", 0),
    ]
    for inc, lead, trail, n in bnd_pipe:
        check_pipeline_refinement(inc, lead, trail, n)

    alpha2 = list(" \tabxyz<>/")
    for _ in range(3000):
        ni = rng.randint(0, 5)
        included = []
        for _ in range(ni):
            L = rng.randint(0, 8)
            included.append("".join(rng.choice(alpha2) for _ in range(L)))
        # in-domain: n >= 0 and nothing required of the author lines, so each is
        # absent (the empty, falsy option) a quarter of the time — all four
        # presence combinations — and the identity width is drawn too.
        if rng.randint(0, 3) == 0:
            lead = ""
        else:
            lead = "".join(rng.choice(alpha2) for _ in range(rng.randint(1, 6)))
        if rng.randint(0, 3) == 0:
            trail = ""
        else:
            trail = "".join(rng.choice(alpha2) for _ in range(rng.randint(1, 6)))
        n = rng.randint(0, 8)
        check_pipeline_refinement(included, lead, trail, n)

    print("G-AX OK: deep model trim_block (per line) == real dedent_lines on %d "
          "boundary + 200000 fuzz lines; real read() pipeline "
          "(dedent+prepend+append) == model assemble (leading/trailing verbatim, "
          "included trimmed) on the issue scenario + %d boundary + 3000 fuzz blocks"
          % (len(boundary), len(bnd_pipe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
