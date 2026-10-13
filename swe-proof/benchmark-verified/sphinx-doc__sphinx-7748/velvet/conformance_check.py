#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7748 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List LineInfo` ↔ one docstring's `List[str]`; `Sig` ↔ the
              `(args, retann)` pair; `out : List Sig` ↔ `result` + `_signatures`;
              the `format_signature` newline join ↔ the render). Each `LineInfo`
              is derived from the REAL unchanged callees via the mapping.md §3
              bridge (`py_ext_sig_re`, `str.endswith/rstrip`); that derivation is
              the A-reference, checked by G-AX, not re-litigated here. There are
              no consumed axioms, so the A leg is empty.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `DocstringSignatureMixin._find_signature` + `format_signature`
              applied at base_commit (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the patched SWE-Bench instance image), stdlib + the real repo
regex/function only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import types

from sphinx.ext.autodoc import py_ext_sig_re, DocstringSignatureMixin

SEED = 7748
N_FUZZ = 100_000


# --- mapping.md §3 bridge: one docstring line -> LineInfo (real callees) ------
def line_info(s, valid_names):
    blank = not s
    if s.endswith('\\'):
        cont = True
        stripped = s.rstrip('\\').rstrip()
    else:
        cont = False
        stripped = s
    m = py_ext_sig_re.match(stripped)
    is_sig = bool(m) and (m.group(3) in valid_names)
    sig = (m.group(4), m.group(5)) if m else (None, None)
    return {"blank": blank, "isSig": is_sig, "cont": cont, "sig": sig}


# --- SHADOW: collectSigs control flow + render, transliterated from Lean ------
def shadow_collect(infos):
    """The deep model `collectSigs` (front-recursive fold), transliterated."""
    out = []
    for li in infos:
        if li["blank"]:
            break
        if li["isSig"]:
            out.append(li["sig"])
            if not li["cont"]:
                break
    return out


def shadow_render(doclines, valid_names):
    """Full R/I shadow: derive LineInfo per line, run collectSigs, then render
    the way the patched _find_signature/format_signature expose it:
      result = out[0]; _signatures = ['(args) -> retann' for the rest]."""
    infos = [line_info(s, valid_names) for s in doclines]
    out = shadow_collect(infos)
    if not out:
        return None, []
    result = out[0]
    extra = ["(%s) -> %s" % (a, r) for (a, r) in out[1:]]
    return result, extra


# --- ORACLE: the patched _find_signature, bound to a minimal fake `self` ------
def make_fake(docstrings, objpath):
    settings = types.SimpleNamespace(tab_width=8)
    document = types.SimpleNamespace(settings=settings)
    state = types.SimpleNamespace(document=document)
    directive = types.SimpleNamespace(state=state)
    fake = types.SimpleNamespace(
        objpath=objpath,
        directive=directive,
        _new_docstrings=None,
        _signatures=None,
    )
    fake.get_doc = lambda *a, **k: docstrings
    return fake


def oracle_render(doclines, objpath):
    fake = make_fake([list(doclines)], objpath)
    result = DocstringSignatureMixin._find_signature(fake)
    return result, list(fake._signatures or [])


# --- fuzz corpus -------------------------------------------------------------
def fuzz_inputs(n, rng):
    base = ["E", "F"]
    pool = [
        "", "  ", "plain descriptive text", "second paragraph line",
        "E(foo, bar)", "E(foo: int, bar: int, baz: int) -> None",
        "E(a) \\", "E(foo: int) -> None \\", "E()", "E", "E -> None",
        "F(x, y)", "F(p) \\", "D(foo, bar, baz)", "module.E(z) -> str",
        "E(a, *args, **kw) -> 'T'", "    E(indented)",
    ]
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        [],
        [""],
        ["E(foo, bar)"],
        ["E(foo: int) -> None \\", "E(foo: str) -> None"],
        ["E(a) \\", "E(b) \\", "E(c)"],
        ["E(a) \\", "E(b) \\", "E(c) \\"],
        ["E(a) \\", "", "E(b)"],
        ["preamble", "E(foo, bar)"],
        ["F(x)", "E(y)"],
        ["", "E(z)"],
        ["D(foo, bar, baz)"],
    ]
    for ds in boundary:
        yield ds
    for _ in range(n):
        k = rng.randint(0, 8)
        yield [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    valid_names = ["E"]            # the function-case objpath[-1]; G-AX covers class case
    objpath = ["E"]
    disagreements = []
    count = 0
    for doclines in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_render(doclines, valid_names)
        oracle = oracle_render(doclines, objpath)
        if shadow != oracle:
            disagreements.append((doclines, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ds, sh, orc in disagreements:
            print("  doclines=%r shadow=%r oracle=%r" % (ds, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of collectSignatures agrees with patch.diff "
          "behaviour on %d docstrings (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
