#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-11510 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`assembleInsertedLines`) transliterated to Python over the real
              repo types (`list[str]`, `str`), via the mapping.md bijection
              (`List (List Char)` ↔ `list[str]`, `splitLines` ↔ the full
              CPython `str.splitlines` model over every line-boundary char,
              `List.intercalate ['\\n']` ↔ `"\\n".join`, `dropLast.dropLast`
              ↔ `[:-2]`, `drop (len-2)` ↔ `[-2:]`). The transform parameter
              is supplied as a real Python callback.
  * ORACLE  — patch.diff's behaviour: the exact body of the gold patch's new
              `_insert_input` closure (`sphinx/directives/other.py`,
              `Include.run`), with the effectful event-emit replaced by directly
              calling the same callback (the emit round-trip `arg=[text];
              emit(...); text=arg[0]` is observationally `text = cb(text)`).

There is NO A-tagged callee in this bundle (the consumer transform is a
universally-quantified parameter, not an axiom), so the shadow is pure R/I and
G-CONF covers the whole impl region. They must agree on every input. Exit 0 iff
zero disagreements.

stdlib-only; the fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
Inputs and transforms range over the FULL line-boundary alphabet (\\n, \\r,
\\r\\n, \\v, \\f, \\x1c, \\x1d, \\x1e, \\x85, \\u2028, \\u2029) so the
splitLines leg is exercised on every CPython boundary (mapping.md §3.1).
"""
import random
import sys

SEED = 11510
N_FUZZ = 100_000

LINE_BREAKS = "\n\x0b\x0c\r\x1c\x1d\x1e\x85  "


# --- the R/I shadow: Solution.lean splitLines/intercalate/slices ------------

def split_lines(s):
    """splitLines (full model of CPython str.splitlines): split at every
    line-boundary char (CR-LF a single boundary); a terminating boundary
    yields no trailing empty field ("" -> [])."""
    out = []
    i, n = 0, len(s)
    while i < n:
        j = i
        while j < n and s[j] not in LINE_BREAKS:
            j += 1
        out.append(s[i:j])
        if j < n:
            if s[j] == "\r" and j + 1 < n and s[j + 1] == "\n":
                j += 2
            else:
                j += 1
        i = j
    return out


def shadow_assemble(transform, lines):
    """assembleInsertedLines (transform) (lines), transliterated.
    out = splitLines (transform (intercalate '\\n' lines[:-2])) ++ lines[-2:]"""
    content = lines[:-2]
    text = transform("\n".join(content))
    return split_lines(text) + lines[-2:]


# --- the oracle: the gold patch's _insert_input body ------------------------

def oracle_assemble(transform, lines):
    """patch.diff behaviour: the exact line-assembly of the gold closure.
    The event-emit round-trip is observationally `text = transform(text)`."""
    include_lines = list(lines)
    text = "\n".join(include_lines[:-2])
    arg = [text]
    arg[0] = transform(arg[0])          # == self.env.app.events.emit("source-read", docname, arg)
    text = arg[0]
    include_lines = text.splitlines() + include_lines[-2:]
    return include_lines


# --- transform callbacks (a fuzzed family of consumer handlers) -------------

def make_transforms(rng):
    fns = [
        ("identity", lambda t: t),
        ("constant_empty", lambda t: ""),
        ("upper", lambda t: t.upper()),
        ("prefix", lambda t: "PRE:" + t),
        ("suffix", lambda t: t + ":POST"),
        # the issue's own substitutions (F2P scenarios)
        ("replace_me", lambda t: t.replace("&REPLACE_ME;", "REPLACED")),
        ("magical", lambda t: t.replace("#magical", "amazing")),
        ("strip_hash", lambda t: t.replace("#", "")),
        ("double", lambda t: t + t),
        # boundary-injecting handlers: the transform may emit ANY character,
        # so splitlines must be modeled on the full boundary alphabet
        # (the G-PANEL-2 counterexample was exactly nl_to_cr)
        ("nl_to_cr", lambda t: t.replace("\n", "\r")),
        ("nl_to_crlf", lambda t: t.replace("\n", "\r\n")),
        ("suffix_cr", lambda t: t + "\r"),
        ("suffix_crlf", lambda t: t + "\r\n"),
        ("inject_vt_ff", lambda t: t.replace("a", "a\x0b").replace("b", "b\x0c")),
        ("inject_seps", lambda t: t.replace("x", "x\x1c").replace("=", "=\x1d")
                                   .replace("z", "z\x1e")),
        ("inject_nel", lambda t: t.replace("e", "e\x85")),
        ("inject_ls_ps", lambda t: t.replace("o", "o ").replace("i", "i ")),
        ("cr_only_prefix", lambda t: "\r" + t),
    ]
    return fns


# --- input fuzzing (full line-boundary alphabet) -----------------------------

def fuzz_line_lists(n, rng):
    # boundary cases first
    yield ["m1", "m2"]                       # no content, only markers
    yield ["only one line", "m1", "m2"]
    yield ["", "", "m1", "m2"]
    yield ["Baz", "===", "", ".. include:: foo.rst", "", "Baz was here.", "m1", "m2"]
    yield ["The #magical foo.", "", "m1", "m2"]
    yield ["a", "b", "c", "m1", "m2"]
    yield []                                 # degenerate: no lines at all
    yield ["m1"]                             # fewer than two lines
    yield ["x&REPLACE_ME;y", "z", "m1", "m2"]
    # content lines carrying stray non-LF boundary chars (splitlines re-splits
    # them post-transform; shadow and oracle must agree)
    yield ["a\rb", "c\x0bd", "m1", "m2"]
    yield ["a\r", "\x85e", "m1", "m2"]
    yield ["a b", " ", "m1", "m2"]
    tokens = ["a", "Baz", "===", "", ".. include:: foo.rst", "The #magical foo.",
              "&REPLACE_ME;", "Baz was here.", "m1", "m2", "x", "  indented",
              "line with spaces", "#magical",
              "a\rb", "c\x0bd", "e\x0cf", "g\x1ch", "i\x1dj", "k\x1el",
              "m\x85n", "o p", "q r", "s\r\nt", "\r", "\x85"]
    for _ in range(n):
        k = rng.randint(0, 8)
        yield [rng.choice(tokens) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    transforms = make_transforms(rng)
    disagreements = []
    count = 0
    for lines in fuzz_line_lists(N_FUZZ, rng):
        for _name, cb in transforms:
            count += 1
            shadow = shadow_assemble(cb, lines)
            oracle = oracle_assemble(cb, lines)
            if shadow != oracle:
                disagreements.append((_name, lines, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for nm, lines, sh, orc in disagreements:
            print("  transform=%s lines=%r shadow=%r oracle=%r"
                  % (nm, lines, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleInsertedLines agrees with patch.diff "
          "behaviour on %d checks (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
