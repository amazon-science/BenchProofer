#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16766 (nagini).

SHADOW: the impl region of model.py's `print_indexed`, copied VERBATIM below
with the contract calls (Invariant/Assert; Requires/Ensures live outside the
impl region) stripped. The @Pure helpers the impl consults (`empty_seq`,
`sep`) copy over as plain functions, as does the spec-side `join_sep` for
completeness; `PSeq`/`ToSeq` become immutable-tuple shims (a small tuple
subclass carrying `.take`/`.drop`, which `empty_seq`'s empty-sequence literal
and the front-recursive join use). There are no @ContractOnly callees and no
axioms in this bundle.

ORACLE: the REAL patched repo function per mapping.md — the element-access
renderer method of the Python-source printer class in the printing module
(the gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed). Called directly on real element-access expressions.

Type bridge (mapping.md section 2): the repo carriers are `str` values; the
model carriers are `List[int]` / `PSeq[int]` of Unicode code points, mapped
via `ord`/`chr` per character. The model's inputs `name` and
`index_renderings` are the outputs of the UNCHANGED callees (the carrier's
`str()` rendering and the per-index dispatcher rendering), so each test case
is realized by building a real expression, deriving those two carriers from
it with the real unchanged callees, feeding their code points to the shadow,
and comparing the shadow's output code points against the real renderer's
output on the same expression.

Input domain: exactly the model's Requires — any carrier name and any
non-empty list of index renderings, as reachable through real expressions
(an element-access expression always carries at least one index; the
constructor enforces this, matching the precondition). The mix
over-represents interesting regimes: single index, many indices, carrier
names containing brackets / comma-space / braces / percent / unicode, index
renderings that themselves contain the separator or brackets, and numeric /
symbolic / compound index expressions.

>= 1e5 Requires-satisfying inputs: hand-picked boundary cases + randomized
fuzz to a total of 100000+. Pinned fuzz seed: 167660.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List

SEED = 167660
N_TOTAL = 100_000


# --- shims for the sequence carrier -----------------------------------------

class _Seq(tuple):
    """Immutable code-point sequence with the tiny slice API the pure
    helpers use. `+` on tuples already matches PSeq concatenation."""
    def take(self, n):
        return _Seq(self[:n])

    def drop(self, n):
        return _Seq(self[n:])


def PSeq(*items):
    """Immutable sequence literal."""
    return _Seq(items)


def ToSeq(lst):
    """Immutable snapshot of a list's contents."""
    return _Seq(lst)


# --- @Pure helpers from model.py, contracts stripped -------------------------

def empty_seq():
    """The empty code-point sequence."""
    return PSeq(0).take(0)


def sep():
    """The index separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


def join_sep(s):
    """Separator-joined concatenation of index renderings: between every two
    adjacent indices a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def print_indexed(name, index_renderings):
    nm = ToSeq(name)                  # type: _Seq
    idx = ToSeq(index_renderings)     # type: _Seq
    n = len(index_renderings)
    joined = empty_seq()              # type: _Seq
    i = n
    while i > 0:
        e = idx[i - 1]
        if i == n:
            joined = e
        else:
            joined = e + sep() + joined
        i = i - 1
    return nm + PSeq(91) + joined + PSeq(93)


# --- differential driver ------------------------------------------------------

def check_case(printer, expr):
    """Run shadow and oracle on one element-access expression; return an
    error string on disagreement, else None."""
    base = expr.args[0]
    index = expr.args[1:]
    # Input carriers, derived by the real UNCHANGED callees (mapping.md):
    # the carrier's str() rendering and the per-index dispatcher rendering.
    name_str = str(base)
    renders = [printer._print(ind) for ind in index]
    name_cp = [ord(ch) for ch in name_str]
    idx_cp = [_Seq(ord(ch) for ch in r) for r in renders]
    shadow = print_indexed(name_cp, idx_cp)
    try:
        real = printer._print_Indexed(expr)
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: name=%r indices=%r"
                "\n  shadow: %r\n  real raised %s: %s"
                % (name_str, renders, _dec(shadow),
                   type(exc).__name__, exc))
    if tuple(shadow) != tuple(ord(ch) for ch in real):
        return ("DISAGREEMENT\n  input: name=%r indices=%r"
                "\n  shadow: %r\n  real:   %r"
                % (name_str, renders, _dec(shadow), real))
    return None


def _dec(cps):
    return "".join(chr(c) for c in cps)


def main():
    # REAL patched repo class (mapping.md section 1) — importable
    # from /testbed once the gate has applied the patch.
    from sympy.printing.pycode import PythonCodePrinter
    from sympy import Symbol, Integer, Rational, IndexedBase
    from sympy.tensor.indexed import Indexed

    printer = PythonCodePrinter()
    rng = random.Random(SEED)

    # Adversarial carrier names: brackets, the separator itself, format-ish
    # braces and percent signs, whitespace, unicode, long names.
    base_names = [
        "p", "A", "x0", "arr_2", "M", "longname_with_many_chars_0123456789",
        "a b", "a, b", "n[k]", "q]", "[r", "{f}", "{}", "%s", "%%", "{0}",
        "α", "βγ", "bézier", "_", "__x__", "name.attr",
        "s'; t", 'd"q', "tab\tname", "comma,name",
    ]
    # Index atoms: numbers, symbols (some with adversarial printed forms),
    # and compound expressions.
    i, j, k = Symbol("i"), Symbol("j"), Symbol("k")
    weird_syms = [Symbol(nm) for nm in
                  ["i", "j", "k", "idx", "n_1", "a, b", "u]v", "[w",
                   "{m}", "%d", "δ", "lambda", "x y"]]
    atoms = ([Integer(v) for v in (-3, -1, 0, 1, 2, 7, 10 ** 12)]
             + [Rational(1, 2), Rational(-5, 3)]
             + weird_syms
             + [i + 1, 2 * j, -k, i ** 2, i + j * k])

    bases = {nm: IndexedBase(nm) for nm in base_names}

    checked = 0

    # --- boundary inputs ------------------------------------------------------
    boundary = []
    for nm in base_names:
        boundary.append(Indexed(bases[nm], Integer(0)))          # single index
    p = bases["p"]
    boundary.append(Indexed(p, Integer(0), Integer(1)))          # two indices
    boundary.append(Indexed(p, i, j, k))                         # symbolic
    boundary.append(Indexed(p, *[Integer(t) for t in range(8)]))  # many
    boundary.append(Indexed(p, Symbol("a, b")))     # separator inside a render
    boundary.append(Indexed(p, Symbol("u]v"), Symbol("[w")))     # brackets
    boundary.append(Indexed(bases["a, b"], Symbol("a, b"), Integer(-1)))
    boundary.append(Indexed(bases["{f}"], Rational(1, 2)))
    boundary.append(Indexed(bases["%s"], i + 1, 2 * j))
    boundary.append(Indexed(bases["α"], Symbol("δ")))
    for expr in boundary:
        err = check_case(printer, expr)
        if err:
            print(err)
            return 1
        checked += 1

    # --- randomized fuzz to >= N_TOTAL ------------------------------------------
    ascii_printable = [chr(c) for c in range(33, 127)]
    n_fuzz = N_TOTAL - checked
    for t in range(n_fuzz):
        if t % 7 == 0:
            # fresh random carrier name (printable ASCII, occasionally unicode)
            ln = rng.randint(1, 12)
            if rng.random() < 0.1:
                nm = "".join(chr(rng.randint(0x100, 0x2FF))
                             for _ in range(ln))
            else:
                nm = "".join(rng.choice(ascii_printable) for _ in range(ln))
            base = bases.setdefault(nm, IndexedBase(nm))
        else:
            base = bases[rng.choice(base_names)]
        nidx = rng.randint(1, 6)
        idxs = [rng.choice(atoms) for _ in range(nidx)]
        expr = Indexed(base, *idxs)
        err = check_case(printer, expr)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched element-access renderer on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
