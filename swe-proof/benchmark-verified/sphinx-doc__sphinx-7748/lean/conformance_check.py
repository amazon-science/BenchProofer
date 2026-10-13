#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-7748.

The bundle models the signature-reading behavior of `DocstringSignatureMixin`
(`sphinx/ext/autodoc/__init__.py`): `_find_signature` together with the
`format_signature` join. The observable is the ORDERED LIST of signatures
collected from the leading text of a documentation comment.

This script differential-tests two independent constructions of that observable:

  * `shadow`  — a transliteration of the Lean `implementation_collectSignatures`
    (the R/I impl): a `result`/`signatures` accumulator pair driven by an inner
    line loop with the break/continue control flow of the Lean `for` loops.

  * `oracle`  — a faithful replica of the POST-PATCH Python control flow of
    `_find_signature` (the nested `for i, doclines` / `for j, line` loops,
    `multiline` continuation handling, `result` vs `self._signatures`) followed
    by the `format_signature` join `[sig] + self._signatures`.

The UNCHANGED matcher `py_ext_sig_re.match` is modeled by `matchSig` (an
A-reference). The Lean impl and the patched Python invoke it IDENTICALLY, so we
stub it with the SAME deterministic function on both legs (`match_sig`), which
makes it cancel and isolates the behavior the patch changes: multi-line scan,
backslash continuation, and collect-all-in-order.

We compare the two legs on the modeled observable only: the ordered list of
(args, retann) pairs. (The Python `"(%s) -> %s"` rendering and the `"\n".join`
are value-level formatting of these same pairs; testing the pair list tests the
collection behavior the patch changes.)

stdlib-only; deterministic built-in fuzzer. Pinned seed: 7748 (also in mapping.md).
"""
import random
import sys

SEED = 7748
N = 120_000


# --- the UNCHANGED callee (A-reference), stubbed IDENTICALLY on both legs -----
# Models py_ext_sig_re.match(line).groups() -> (exmod, path, base, args, retann)
# restricted to the (base, args, retann) the modeled behavior keys on. The fuzzer
# emits lines of the shape "NAME(ARGS)[ -> RET]" plus junk; this recogniser
# accepts exactly the well-formed ones, deterministically. Returns None or a
# (base, args, retann) triple. Both legs call THIS.
def match_sig(line):
    # An empty line is never a match here (callers gate on emptiness first, but
    # be safe).
    if line == "":
        return None
    # NAME must be a run of word chars; then optional "(...)" then optional
    # " -> RET". Anything else -> no match. This is a faithful stand-in for the
    # extended-signature regex over the fuzzer's alphabet.
    i = 0
    n = len(line)
    j = 0
    while j < n and (line[j].isalnum() or line[j] == "_"):
        j += 1
    if j == 0:
        return None
    base = line[:j]
    rest = line[j:]
    if rest == "":
        # bare name, no args / no parens -> still a match (args group empty)
        return (base, "", "")
    if not rest.startswith("("):
        return None
    # find the matching close paren (no nesting in the fuzzer alphabet)
    close = rest.find(")")
    if close == -1:
        return None
    args = rest[1:close]
    tail = rest[close + 1:]
    if tail == "":
        return (base, args, "")
    if tail.startswith(" -> "):
        return (base, args, tail[4:])
    return None


# --- helpers shared by the modeling (R/I) -------------------------------------
def strip_continuation(s):
    # drop trailing backslashes, then trailing whitespace (Lean stripContinuation
    # / Python line.rstrip('\\').rstrip())
    return s.rstrip("\\").rstrip()


# --- shadow: transliteration of implementation_collectSignatures --------------
def shadow(docstrings, valid_names):
    result = None
    signatures = []
    for doclines in docstrings:
        for line0 in doclines:
            if line0 == "":
                break
            multiline = line0.endswith("\\")
            line = strip_continuation(line0) if multiline else line0
            m = match_sig(line)
            if m is None:
                continue
            base, args, retann = m
            if base in valid_names:
                if result is None:
                    result = (args, retann)
                else:
                    signatures.append((args, retann))
                if multiline:
                    continue
                else:
                    break
            else:
                continue
        if result is not None:
            break
    if result is None:
        return []
    return [result] + signatures


# --- oracle: faithful replica of the POST-PATCH _find_signature + join --------
def oracle(docstrings, valid_names):
    _signatures = []
    result = None
    for i, doclines in enumerate(docstrings):
        for j, line in enumerate(doclines):
            if not line:
                break
            if line.endswith("\\"):
                multiline = True
                line = line.rstrip("\\").rstrip()
            else:
                multiline = False
            match = match_sig(line)
            if not match:
                continue
            base, args, retann = match
            if base not in valid_names:
                continue
            if result is None:
                result = (args, retann)
            else:
                _signatures.append((args, retann))
            if multiline:
                continue
            else:
                break
        if result:
            break
    # format_signature: [sig] + self._signatures (as the modeled pair list)
    if result is None:
        return []
    return [result] + _signatures


# --- fuzzer -------------------------------------------------------------------
_NAMES = ["E", "D", "Foo", "__init__", "Bar", "baz", "object"]
_ARGS = ["", "foo, bar, baz", "foo: int, bar: int", "x", "a, b, c", "self"]
_RET = ["", "None", "int", "Foo"]


def _rand_sig_line(rng, name=None, with_cont=False):
    nm = name if name is not None else rng.choice(_NAMES)
    a = rng.choice(_ARGS)
    r = rng.choice(_RET)
    base = "%s(%s)" % (nm, a)
    if r:
        base += " -> %s" % r
    if with_cont:
        # optionally pad with spaces before the continuation backslash
        base += " " * rng.randint(0, 3) + "\\"
    return base


def _rand_line(rng, valid_names):
    roll = rng.random()
    if roll < 0.10:
        return ""                                   # empty terminator
    if roll < 0.25:
        # junk / non-matching line
        return rng.choice(["lorem ipsum dolor", ": not a sig", "(oops)", "-> x",
                            "a b c d", "###"])
    name = rng.choice(valid_names + _NAMES)
    cont = rng.random() < 0.45
    return _rand_sig_line(rng, name=name, with_cont=cont)


def _rand_doc(rng, valid_names):
    k = rng.randint(0, 5)
    return [_rand_line(rng, valid_names) for _ in range(k)]


def _rand_input(rng):
    vn = rng.sample(_NAMES, rng.randint(1, 3))
    nblocks = rng.randint(0, 3)
    docs = [_rand_doc(rng, vn) for _ in range(nblocks)]
    return docs, vn


# --- hand-picked edge cases ---------------------------------------------------
def _edge_cases():
    cases = []
    # single non-continuation signature (PASS_TO_PASS: D(foo, bar, baz))
    cases.append(([["D(foo, bar, baz)"]], ["D", "__init__"]))
    # two-signature backslash continuation run (FAIL_TO_PASS: class E)
    cases.append(([["E(foo: int, bar: int, baz: int) -> None \\",
                    "E(foo: str, bar: str, baz: str) -> None"]],
                  ["E", "__init__"]))
    # continuation run terminated by a non-continuation 3rd line
    cases.append(([["E(a) -> None \\", "E(b) -> None \\", "E(c) -> None",
                    "E(d) -> None"]], ["E"]))
    # name mismatch skipped, then a matching one
    cases.append(([["Other(z)", "E(foo) -> None"]], ["E"]))
    # empty line terminates the run before a later (ignored) signature
    cases.append(([["E(foo) -> None", "", "E(bar) -> None"]], ["E"]))
    # first block empty-run, second block wins
    cases.append(([["nonsense", "more nonsense"], ["E(foo) -> None"]], ["E"]))
    # no match anywhere -> empty
    cases.append(([["nope", "nada"], ["zip"]], ["E"]))
    # empty docstrings list
    cases.append(([], ["E"]))
    # block with empty first line
    cases.append(([["", "E(foo)"]], ["E"]))
    # bare-name match (no parens)
    cases.append(([["E"]], ["E"]))
    # exotic Python whitespace exposed under the continuation backslash
    # (str.rstrip() strips these; a whitespace class narrower than
    # str.isspace() would leave them and mis-classify the line):
    # form feed (the G-PANEL-2 counterexample), NBSP, ideographic space,
    # vertical tab, NEL — alone and mixed with plain spaces
    for ws in ["\x0c", "\xa0", "　", "\x0b", "\x85", " \x0c ", "\xa0  "]:
        cases.append(([["E(a)%s\\" % ws, "E(b)"]], ["E"]))
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = 0
    shown = 0

    for inp in _edge_cases():
        docs, vn = inp
        a = shadow(docs, vn)
        b = oracle(docs, vn)
        if a != b:
            disagreements += 1
            if shown < 10:
                print("EDGE DISAGREE: docs=%r valid=%r shadow=%r oracle=%r"
                      % (docs, vn, a, b))
                shown += 1

    for _ in range(N):
        docs, vn = _rand_input(rng)
        a = shadow(docs, vn)
        b = oracle(docs, vn)
        if a != b:
            disagreements += 1
            if shown < 10:
                print("FUZZ DISAGREE: docs=%r valid=%r shadow=%r oracle=%r"
                      % (docs, vn, a, b))
                shown += 1

    total = N + len(_edge_cases())
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements (seed=%d)"
              % (disagreements, total, SEED))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements (seed=%d)" % (total, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
