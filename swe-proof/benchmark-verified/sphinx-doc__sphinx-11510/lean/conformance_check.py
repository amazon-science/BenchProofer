#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-11510.

The bundle models ONE behaviour: the `_insert_input` interception that the patch
installs on the include directive's state machine (mapping.md). Its observable
effect is a PURE function of the inputs the real closure reads:

    hasListeners, srcRead (net listener effect on the body text),
    path (only as an opaque docname tag), include_lines

Standing up docutils + a real Sphinx app to drive the directive is heavy and
unnecessary: the modeled value is this pure line-manipulation + event-emission
decision. So the ORACLE below is a faithful in-process replica of the POST-PATCH
`_insert_input` (joining `include_lines[:-2]`, emitting the source-read event,
re-splitting + re-attaching `include_lines[-2:]`, gated on a listener being
present), and the SHADOW is the op-for-op transliteration of
`implementation_includedSource` (Solution.lean impl region), per refinement.md.

Faithfulness of the model boundaries:
  * `joinLines`   == "\\n".join
  * `splitLines`  == str.splitlines() in full: all universal line boundaries
                     (\\n, \\r, \\r\\n, \\v, \\f, \\x1c, \\x1d, \\x1e, \\x85,
                     \\u2028, \\u2029), CRLF as ONE boundary, no spurious
                     trailing empty line — the ORACLE leg calls the REAL
                     str.splitlines(); the SHADOW leg transliterates the Lean
                     splitLinesGo, so this equivalence is itself fuzzed here
  * marker split  == include_lines[:-2] / include_lines[-2:]  ==  take/drop(n-2)
                     with Python/Lean agreeing at n<2 (both saturate to 0/all)
  * pathToDocname == an opaque path->docname tag; modeled here by a fixed
                     deterministic stand-in (its concrete value is irrelevant —
                     the spec only pins emitted == (pathToDocname path, body), and
                     both legs apply the SAME tag function, so disagreement can
                     only come from body/markers/lines, never the tag).

This genuinely tests the soundness-critical behaviour: when a listener is present
the body (minus markers) is offered to the hook and the rewritten text — re-split
with the markers re-attached — is what is parsed; when absent, the lines pass
through untouched and nothing is emitted. Matches the F2P expectations
(`test_include_source_read_event`, `test_include_source_read_event_nested_includes`).

stdlib-only. Pinned seed: 11510 (also in mapping.md).
"""
import random
import sys

SEED = 11510
N = 120_000


# --- Lean splitLines transliteration (SHADOW leg) -------------------------------
# isLineBoundary: the universal line boundaries (LF, CR, VT, FF, FS, GS, RS, NEL,
# LINE SEPARATOR, PARAGRAPH SEPARATOR); CRLF handled as one boundary by the
# splitter itself. Mirrors Solution.lean isLineBoundary byte-for-byte.
_BOUNDARIES = set("\n\r\x0b\x0c\x1c\x1d\x1e\x85  ")


def is_line_boundary(c):
    return c in _BOUNDARIES


def split_lines_go(chars, acc):
    # Mirrors Solution.lean splitLinesGo (recursion flattened to a loop).
    out = []
    i = 0
    n = len(chars)
    while True:
        if i >= n:
            out.append("".join(acc))
            return out
        if chars[i] == "\r" and i + 1 < n and chars[i + 1] == "\n":
            rest_empty = (i + 2 >= n)
            if rest_empty:
                out.append("".join(acc))
                return out
            out.append("".join(acc))
            acc = []
            i += 2
            continue
        c = chars[i]
        if is_line_boundary(c):
            rest_empty = (i + 1 >= n)
            if rest_empty:
                out.append("".join(acc))
                return out
            out.append("".join(acc))
            acc = []
            i += 1
            continue
        acc.append(c)
        i += 1


def split_lines(s):
    # Lean splitLines: empty text -> no lines; else splitLinesGo over the chars.
    if s == "":
        return []
    return split_lines_go(list(s), [])


def join_lines(xs):
    return "\n".join(xs)


# pathToDocname stand-in: any deterministic function works (see module docstring).
def path_to_docname(path):
    return "doc::" + path


# --- ORACLE: faithful in-process replica of the POST-PATCH _insert_input -------
# Mirrors the patch: gated on a listener, join [:-2], emit (docname, text),
# splitlines() + [-2:].
def oracle(hasListeners, src_read, path, lines):
    if hasListeners:
        # Real Python slice semantics: include_lines[:-2] / include_lines[-2:].
        body = join_lines(lines[:-2])
        markers = lines[-2:]
        docname = path_to_docname(path)
        modified = src_read(body)
        # REAL str.splitlines(): the actual op the patch performs (all universal
        # line boundaries, CRLF as one, no trailing empty line).
        out_lines = modified.splitlines() + markers
        return (("some", docname, body), out_lines)
    else:
        return (("none",), lines[:])


# --- SHADOW of implementation_includedSource (the R leg) -----------------------
# Mirrors Solution.lean impl region exactly, using Lean take/drop(n-2) semantics.
def take(xs, k):
    k = max(0, k)
    return xs[:k]


def drop(xs, k):
    k = max(0, k)
    return xs[k:]


def shadow(hasListeners, src_read, path, lines):
    if hasListeners:
        n = len(lines)
        body = join_lines(take(lines, n - 2))
        markers = drop(lines, n - 2)
        docname = path_to_docname(path)
        modified = src_read(body)
        new_lines = split_lines(modified) + markers
        return (("some", docname, body), new_lines)
    else:
        return (("none",), lines[:])


# --- srcRead family ------------------------------------------------------------
def _ident(s):
    return s


def _replace_magical(s):
    return s.replace("#magical", "amazing")


def _upper(s):
    return s.upper()


def _prefix(s):
    return "X:" + s


def _suffix(s):
    return s + "\n;Z"


def _const_empty(s):
    return ""


def _dup_nl(s):
    return s + "\n"


def _to_crlf(s):
    return s.replace("\n", "\r\n")


def _to_cr(s):
    return s.replace("\n", "\r")


def _exotic_boundaries(s):
    # Inject every universal line boundary str.splitlines() knows about.
    return "\v" + s + "\f tail\x1cA\x1dB\x1eC\x85D E "


def _trailing_crlf(s):
    return s + "\r\n"


def _trailing_cr(s):
    return s + "\r"


SRC_READS = [_ident, _replace_magical, _upper, _prefix, _suffix, _const_empty,
             _dup_nl, _to_crlf, _to_cr, _exotic_boundaries, _trailing_crlf,
             _trailing_cr]


def disagree(hasListeners, src_read, path, lines):
    got = oracle(hasListeners, src_read, path, lines)
    want = shadow(hasListeners, src_read, path, lines)
    if got != want:
        return (hasListeners, src_read.__name__, path, lines, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P nested-include body: 2 content lines + 2 markers, #magical->amazing
    cases.append((True, _replace_magical, "baz/baz", ["The #magical foo.", "", "<m1>", "<m2>"]))
    # F2P source-read recording (identity on arg[0]); markers preserved
    cases.append((True, _ident, "index", ["", "Baz was here.", "<src>", "<line>"]))
    # no listener: pass-through, nothing emitted
    cases.append((False, _replace_magical, "index", ["The #magical foo.", "", "<m1>", "<m2>"]))
    # fewer than two lines (Nat-subtraction boundary)
    cases.append((True, _ident, "p", []))
    cases.append((True, _ident, "p", ["only"]))
    cases.append((True, _replace_magical, "p", ["#magical"]))
    cases.append((True, _ident, "p", ["a", "b"]))  # body empty, both are markers
    # body becomes empty after marker removal
    cases.append((True, _const_empty, "p", ["x", "y", "z"]))
    # transform adds a trailing newline (splitlines must not add empty tail)
    cases.append((True, _dup_nl, "p", ["a", "b", "<m1>", "<m2>"]))
    # empty strings as content
    cases.append((True, _ident, "p", ["", "", "<m1>", "<m2>"]))
    # the G-PANEL-2 counterexample: listener output containing a bare \r
    cases.append((True, _to_cr, "p", ["a", "b", "<m1>", "<m2>"]))
    # CRLF rewrites, trailing CR / CRLF, and the full exotic-boundary zoo
    cases.append((True, _to_crlf, "p", ["a", "b", "<m1>", "<m2>"]))
    cases.append((True, _trailing_cr, "p", ["a", "b", "<m1>", "<m2>"]))
    cases.append((True, _trailing_crlf, "p", ["a", "b", "<m1>", "<m2>"]))
    cases.append((True, _exotic_boundaries, "p", ["a", "b", "<m1>", "<m2>"]))
    # lone boundary characters as the whole rewritten body
    cases.append((True, lambda s: "\r", "p", ["a", "<m1>", "<m2>"]))
    cases.append((True, lambda s: "\r\n", "p", ["a", "<m1>", "<m2>"]))
    cases.append((True, lambda s: "\r\n\r\n", "p", ["a", "<m1>", "<m2>"]))
    cases.append((True, lambda s: "x\r", "p", ["a", "<m1>", "<m2>"]))
    cases.append((True, lambda s: "\rx", "p", ["a", "<m1>", "<m2>"]))
    cases.append((True, lambda s: "  ", "p", ["a", "<m1>", "<m2>"]))
    return cases


def _rand_lines(rng):
    n = rng.choice([0, 1, 2, 3, 3, 4, 4, 5, 6, 8])
    toks = ["The #magical foo.", "", "Baz was here.", "abc", "#magical", "x y z",
            "<marker1>", "<marker2>", "line", "  ", "\t"]
    return [rng.choice(toks) for _ in range(n)]


def _fuzz_splitlines(rng, rounds):
    """Direct differential: Lean splitLines transliteration vs REAL
    str.splitlines() over boundary-rich random strings (plus the empty-string
    special case: Lean splitLines '' = [] = ''.splitlines())."""
    alphabet = list("ab z#.") + ["\n", "\r", "\r\n", "\v", "\f",
                                 "\x1c", "\x1d", "\x1e", "\x85",
                                 " ", " "]
    for _ in range(rounds):
        n = rng.randrange(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if split_lines(s) != s.splitlines():
            print(f"DISAGREE splitlines: lean={split_lines(s)!r} "
                  f"py={s.splitlines()!r} inp={s!r}")
            return False
    return True


def main() -> int:
    checked = 0
    rng0 = random.Random(SEED ^ 0x5EED)
    if not _fuzz_splitlines(rng0, 60_000):
        print("status=fail")
        return 1
    checked += 60_000
    for (hl, sr, path, lines) in _enumerate_edge():
        d = disagree(hl, sr, path, lines)
        if d:
            print(f"DISAGREE edge: oracle={d[4]} shadow={d[5]} inp=(hl={d[0]}, sr={d[1]}, path={d[2]}, lines={d[3]})")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        hl = rng.random() < 0.5
        sr = rng.choice(SRC_READS)
        path = rng.choice(["index", "baz/baz", "foo", "a/b/c", ""])
        lines = _rand_lines(rng)
        d = disagree(hl, sr, path, lines)
        if d:
            print(f"DISAGREE fuzz: oracle={d[4]} shadow={d[5]} inp=(hl={d[0]}, sr={d[1]}, path={d[2]}, lines={d[3]})")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
