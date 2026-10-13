#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14531 (nagini).

Refutes (never proves) the refinement leg: does the MODEL in model.py actually
agree with the REAL patched repository code it claims to model? The gate applies
patch.diff to /testbed before this script runs, so every oracle below is the
PATCHED function.

TWO OBSERVABLES, TWO STOCK RECEIVERS, ONE PATCHED METHOD
--------------------------------------------------------
model.py's renderer carries two pieces of state: the wrap CONFIGURATION and the
name REGISTRY. In the repo those two pieces live on two different stock printer
classes that INHERIT THE SAME method objects:

  * the configuration lives on `StrPrinter` (`_settings['sympy_integers']`, read
    by `StrPrinter._print_Rational`, sympy/printing/str.py:574-580);
  * the registry lives on `PythonPrinter` (`self.symbols`, sympy/printing/
    python.py:21, appended by `PythonPrinter._print_Symbol`, python.py:38-42,
    and drained into the `x = Symbol('x')` preamble by `python()`, python.py:
    56-69). `PythonPrinter(ReprPrinter, StrPrinter)` (python.py:15) does NOT
    accept `sympy_integers` at all: its `_default_settings` come from
    `ReprPrinter` (repr.py:20-22), so `PythonPrinter({'sympy_integers': True})`
    raises TypeError. That is asserted below, not assumed.

Both classes dispatch the compound through the SAME function object — this
script asserts `PythonPrinter._print_Relational is StrPrinter._print_Relational`
and `PythonPrinter._print_Limit is StrPrinter._print_Limit` — so the two
readings are two consequences of ONE patched line, not two functions. The model
conjoins them, exactly as the instance's own FAIL_TO_PASS pair does: one test
reads the patched line through `sstr` (configuration) and the other through
`python()` (registry).

Accordingly each observable is read on the receiver that HAS it: text on a
`StrPrinter`, registry on a `PythonPrinter`. Nothing is read on a receiver that
lacks the state in question, and no printer class is subclassed, monkeypatched
or otherwise invented here.

SHADOW — the `# impl-start` / `# impl-end` regions of model.py, copied VERBATIM
with only the contract calls deleted (`Requires`, `Ensures`, `Invariant`,
`Assert`, `Acc`, `list_pred`, `ToSeq`, `MustTerminate`, and the
`# invariants-start`/`-end` markers). No restructuring, no renaming, no
"simplification": `render_equation`, `render_directed_limit`, `render_name`,
`render_operand` and `materialize` below are the model's own statements in the
model's own order, including `materialize`'s element-at-a-time copy loop. The
`@Pure` helpers the model uses in its specifications (`lit_*`, `is_name`,
`registered`, `render_rational`, `eq_text`, `eq_registry`, `limit_text`,
`limit_registry`) are copied over too, contracts stripped, and cross-checked
against the same oracles (they are the model's A-reference deep models,
mapping.md §3.2 / §3.3) — that is extra refutation power, not a substitute for
the impl diff. `PSeq` is realized by the immutable tuple shim below (the shape
reused across this corpus's nagini G-CONF scripts): `take`/`drop`/`+`/`len`/
`[]`/`==`/`in`.

The two `@ContractOnly` callees have no body to copy, so the shadow calls the
REAL thing they axiomatize rather than assuming the axiom:
  * `digits(n)`  -> the CPython built-in `str(int)` (mapping.md §3.1: the exact
    spelling `_print_Rational` uses for `expr.p` / `expr.q` at
    sympy/printing/str.py:574-580). Called for real; its non-emptiness Ensures
    is asserted on every call, so a violated axiom fails this gate too.
  * `coprime(p, q)` -> the canonicalisation invariant of the REAL
    `Rational(p, q)` (mapping.md §3.1): the pair is accepted only when
    `math.gcd(p, q) == 1` AND the real constructor keeps it, i.e.
    `Rational(p, q).p == p and .q == q` (no collapse to a different fraction or
    to an `Integer`). Domain filter only — never used to route around a
    disagreement.

ORACLES — the REAL patched repo functions named in mapping.md §1, CALLED, not
transliterated (they need nothing that cannot be built in-container: a `Symbol`,
a `Rational`, a `StrPrinter` and a `PythonPrinter`):

  TEXT (configuration-carrying receiver)
  * `render_equation(wrap, nl, rp, rq, reg)` text
        <- `StrPrinter._print_Relational` charmap arm, sympy/printing/str.py:622
           (patched body lines 636-637), on
           `Eq(Symbol(chr(nl)), Rational(rp, rq))` with `sympy_integers=wrap`.
  * `render_directed_limit(wrap, ne, nz, z0p, z0q, reg)` text
        <- `StrPrinter._print_Limit`, `str(dir) == "+"` arm,
           sympy/printing/str.py:216 (patched body line 219), on
           `Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(z0p, z0q))`.
  * `render_operand(wrap, p, q, reg)` text
        <- the recursive dispatch `Printer._print` (sympy/printing/printer.py:238)
           landing on `StrPrinter._print_Rational` (str.py:574), evaluated on the
           SAME printer instance (hence the same `_settings`) — which is exactly
           what the gold patch substituted for the pre-patch bare `%s`.
  * `render_name(c, reg)` text
        <- the same dispatch landing on `StrPrinter._print_Symbol` (str.py), on
           `Symbol(chr(c))`, at BOTH wrap settings (the name's text is
           configuration-independent, and this script checks that rather than
           assuming it).

  REGISTRY (registry-carrying receiver)
  * `render_equation` / `render_directed_limit` / `render_name` /
    `render_operand` registry effect
        <- `PythonPrinter.symbols` before vs after the SAME patched method runs
           on a `PythonPrinter` whose `symbols` list is pre-seeded with the
           model's `reg` argument. Read twice: once through the instance
           dispatch `pp._print(expr)` (the path `python()` drives) and once by
           applying the patched method object directly to that receiver
           (`StrPrinter._print_Relational(pp, rel)`), so neither a dispatch-level
           nor a method-level mask can hide a divergence.

Each text oracle is likewise taken TWICE and both readings must agree with the
shadow: once through the public dispatch entry point (`sstr(expr,
sympy_integers=wrap)`, the surface the F2P test drives) and once by calling the
patched method object directly on a `StrPrinter` carrying the setting. For
`render_operand` the direct reading is additionally taken at a pre-bumped
`_print_level` (the nested frame a container's `self._print(sub)` really runs
at) and all levels must agree — `_print_Rational` is level-insensitive, and this
script asserts that rather than assuming it.

END-TO-END: whenever the pre-seed is empty, the registry reading is also taken
through the public `python()` entry point (python.py:47-69) and its
`<name> = Symbol('<name>')` preamble must list exactly the model's registry, in
the model's order. That is the surface `test_python_relational` reads.

TYPE BRIDGE (mapping.md §2, inverted). Model side: `wrap: bool`; a name operand
as a single code point `c` with `is_name(c)` (97..122); an operand as the coprime
pair `(p, q)` with `p >= 0, q >= 2`; text as `List[int]` / `PSeq[int]` of code
points; the registry as a `List[int]` / `PSeq[int]` of code points. Repo side:
`self._settings['sympy_integers'] = wrap`, `Symbol(chr(c))`, `Rational(p, q)`,
a `str`, and `printer.symbols` (a list of name `str`s). Inversion:
`c -> Symbol(chr(c))`, `(p, q) -> Rational(p, q)` (checked non-collapsing),
`List[int] -> "".join(chr(c) for c in out)` and
`registry List[int] -> [chr(c) for c in reg]`; the comparisons are on the
concrete `str` / list-of-`str`, so a wrong code point, a wrong registry order or
a missing registration is a disagreement.

INPUT DOMAIN — every input satisfies the model's `Requires`
(`is_name(...)` for each name slot, `p >= 0 and q >= 2 and coprime(p, q)`, plus
a `reg` pre-seed drawn from name code points). Note `gcd(0, q) = q`, so `p = 0`
is outside the modeled domain for `q >= 2` (`Rational(0, q)` is `Integer(0)`, a
different carrier — mapping.md §2) and is therefore never generated; the
generator filters on the REAL `Rational`, it does not widen or narrow the spec.
Boundary set first: the exact F2P shapes (`Eq(x, 2/3)` and `Limit(x, x, 7/2)`),
the smallest fraction, single- vs multi-digit numerators and denominators (so
`materialize`'s copy loop runs 1 and many iterations), EVERY name key a..z,
EQUAL and DISTINCT limit name pairs (the duplicate-free registry behaves
differently on the two), and registry pre-seeds that are empty, disjoint from the
input names, already containing them, and containing only one of two — so both
arms of `registered`'s `if c in r:` are taken by construction, and both values of
`wrap` are used throughout. Then seeded fuzz over the same domain to reach the
count. Each input is checked through all four modeled functions.

INPUTS: 100000 + boundary. Pinned seed: 14531 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on any disagreement the input and both outputs
are printed and the exit status is 1. stdlib + the repo's own sympy only.
"""
import json
import random
import sys
from math import gcd
from typing import List  # noqa: F401 — the copied impl region's `# type:` comments

from sympy import Symbol, Rational, Eq, Limit, sstr
from sympy.printing.str import StrPrinter
from sympy.printing.python import PythonPrinter, python

SEED = 14531
N_FUZZ = 100_000


# --------------------------------------------------------------------------
# PSeq shim: Nagini's immutable pure sequence, the operations the model uses.
# --------------------------------------------------------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *elems):
        self._t = tuple(elems)

    @classmethod
    def _of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def take(self, n):
        return PSeq._of(self._t[:n])

    def drop(self, n):
        return PSeq._of(self._t[n:])

    def __add__(self, other):
        return PSeq._of(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __contains__(self, x):
        return x in self._t

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._of(lst)


# --------------------------------------------------------------------------
# @ContractOnly callees: call the REAL thing they axiomatize (mapping.md §3.1).
# --------------------------------------------------------------------------

def digits(n):
    """`digits` axiom: the REAL CPython `str(int)` spelling used inside
    `_print_Rational` for `expr.p` / `expr.q`. The axiom's Ensures
    (`len(Result()) >= 1`) is asserted on every call, so an unsound axiom fails
    this gate rather than being assumed."""
    assert n >= 0, "digits precondition violated: n=%r" % (n,)
    out = PSeq._of(ord(c) for c in str(n))
    assert len(out) >= 1, "digits(%d) Ensures len>=1 violated" % n
    return out


def coprime(p, q):
    """`coprime` axiom: the canonicalisation invariant of the REAL `Rational`
    (mapping.md §3.1) — `gcd(p, q) == 1`, and the real constructor must keep the
    pair as written (no reduction, no collapse to Integer)."""
    if gcd(p, q) != 1:
        return False
    r = Rational(p, q)
    return r.p == p and r.q == q


# --------------------------------------------------------------------------
# model.py `# pure-start`/`# pure-end` region, contracts stripped.
# --------------------------------------------------------------------------

def lit_S_open():
    # 'S('
    return PSeq(83, 40)


def lit_close_slash():
    # ')/'
    return PSeq(41, 47)


def lit_slash():
    # '/'
    return PSeq(47)


def render_rational(wrap, p, q):
    if wrap:
        return lit_S_open() + digits(p) + lit_close_slash() + digits(q)
    return digits(p) + lit_slash() + digits(q)


def is_name(c):
    return 97 <= c and c <= 122


def lit_name(c):
    return PSeq(c)


def registered(r, c):
    if c in r:
        return r
    return r + PSeq(c)


def lit_eq_open():
    # 'Eq('
    return PSeq(69, 113, 40)


def lit_comma_space():
    # ', '
    return PSeq(44, 32)


def lit_rparen():
    # ')'
    return PSeq(41)


def lit_limit_open():
    # 'Limit('
    return PSeq(76, 105, 109, 105, 116, 40)


def eq_text(wrap, nl, rp, rq):
    return (lit_eq_open() + lit_name(nl) + lit_comma_space()
            + render_rational(wrap, rp, rq) + lit_rparen())


def eq_registry(r, nl):
    return registered(r, nl)


def limit_text(wrap, ne, nz, z0p, z0q):
    return (lit_limit_open() + lit_name(ne) + lit_comma_space()
            + lit_name(nz) + lit_comma_space()
            + render_rational(wrap, z0p, z0q) + lit_rparen())


def limit_registry(r, ne, nz):
    return registered(registered(r, ne), nz)


# --------------------------------------------------------------------------
# SHADOW: the `# impl-start`/`# impl-end` regions of model.py, VERBATIM with
# only the contract calls and invariant markers deleted.
# --------------------------------------------------------------------------

def render_equation(wrap, nl, rp, rq, reg):
    out = []  # type: List[int]
    out = out + [69, 113, 40]                          # 'Eq('
    out = out + render_name(nl, reg)                   # lhs: THIS renderer's name
    out = out + [44, 32]                               # ', '
    out = out + render_operand(wrap, rp, rq, reg)      # SAME-config render of rhs
    out = out + [41]                                   # ')'
    return out


def render_directed_limit(wrap, ne, nz, z0p, z0q, reg):
    out = []  # type: List[int]
    out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('
    out = out + render_name(ne, reg)                   # e: THIS renderer's name
    out = out + [44, 32]                               # ', '
    out = out + render_name(nz, reg)                   # z: THIS renderer's name
    out = out + [44, 32]                               # ', '
    out = out + render_operand(wrap, z0p, z0q, reg)    # SAME-config render of z0
    out = out + [41]                                   # ')'
    return out


def render_name(c, reg):
    if not (c in reg):
        reg.append(c)
    return [c]


def render_operand(wrap, p, q, reg):
    if wrap:
        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
    return materialize(digits(p)) + [47] + materialize(digits(q))


def materialize(s):
    out = []  # type: List[int]
    i = 0
    while i < len(s):
        out = out + [s[i]]
        i = i + 1
    return out


# --------------------------------------------------------------------------
# Receiver facts the mapping relies on: asserted, not assumed.
# --------------------------------------------------------------------------

def check_receiver_facts():
    """The configuration-carrying and registry-carrying receivers dispatch the
    modeled compounds through the SAME patched method objects, and the
    registry-carrying one genuinely has no wrap setting."""
    problems = []
    if PythonPrinter._print_Relational is not StrPrinter._print_Relational:
        problems.append("PythonPrinter._print_Relational is not the StrPrinter one")
    if PythonPrinter._print_Limit is not StrPrinter._print_Limit:
        problems.append("PythonPrinter._print_Limit is not the StrPrinter one")
    if "sympy_integers" in PythonPrinter._default_settings:
        problems.append("PythonPrinter unexpectedly carries sympy_integers")
    try:
        PythonPrinter({"sympy_integers": True})
        problems.append("PythonPrinter accepted sympy_integers")
    except TypeError:
        pass
    if not hasattr(PythonPrinter({}), "symbols"):
        problems.append("PythonPrinter has no symbols registry")
    if hasattr(StrPrinter({}), "symbols"):
        problems.append("StrPrinter unexpectedly carries a symbols registry")
    return problems


# --------------------------------------------------------------------------
# Type bridge (mapping.md §2, inverted).
# --------------------------------------------------------------------------

def to_str(code_points):
    """model carrier (List[int] / PSeq[int] code points) -> repo carrier (str)."""
    if isinstance(code_points, PSeq):
        code_points = [code_points[k] for k in range(len(code_points))]
    return "".join(chr(c) for c in code_points)


def to_names(reg):
    """model carrier (registry as code points) -> repo carrier (list of names)."""
    if isinstance(reg, PSeq):
        reg = [reg[k] for k in range(len(reg))]
    return [chr(c) for c in reg]


def to_symbol(c):
    """model carrier (a name code point) -> repo value (the real name operand)."""
    return Symbol(chr(c))


def to_rational(p, q):
    """model carrier (the coprime pair) -> repo value (the real operand)."""
    return Rational(p, q)


def printer_for(wrap):
    """model carrier (`wrap: bool`) -> repo state (`StrPrinter._settings`)."""
    return StrPrinter({"sympy_integers": wrap})


def registry_printer(pre):
    """model carrier (`reg` as code points) -> repo state (`PythonPrinter.symbols`)."""
    pp = PythonPrinter({})
    pp.symbols = to_names(pre)
    return pp


# --------------------------------------------------------------------------
# ORACLE readings of the REAL patched functions.
# --------------------------------------------------------------------------

def oracle_equation_text(wrap, nl, rp, rq):
    """`StrPrinter._print_Relational` charmap arm (str.py:622, patched body
    636-637), read through the public dispatch entry point and again by direct
    method call on a configuration-carrying receiver."""
    rel = Eq(to_symbol(nl), to_rational(rp, rq))
    # Must remain a genuine Relational: a numeric/numeric Eq auto-evaluates to a
    # Boolean and has no template at all (mapping.md §3.3).
    assert rel.func is Eq, "Eq(%s, %d/%d) auto-evaluated to %r" % (chr(nl), rp, rq, rel)
    via_dispatch = sstr(rel, sympy_integers=wrap)
    via_method = printer_for(wrap)._print_Relational(rel)
    return via_dispatch, via_method


def oracle_equation_registry(nl, rp, rq, pre):
    """The registry effect of the SAME patched method on the registry-carrying
    receiver: `PythonPrinter.symbols` after the compound is printed, read once
    through the instance dispatch and once by applying the patched method object
    directly to that receiver."""
    rel = Eq(to_symbol(nl), to_rational(rp, rq))
    pp = registry_printer(pre)
    pp._print(rel)
    via_dispatch = list(pp.symbols)
    pp2 = registry_printer(pre)
    StrPrinter._print_Relational(pp2, rel)
    via_method = list(pp2.symbols)
    return via_dispatch, via_method


def oracle_limit_text(wrap, ne, nz, z0p, z0q):
    """`StrPrinter._print_Limit` `str(dir) == "+"` arm (str.py:216, patched body
    219), read through the public dispatch entry point and again by direct
    method call."""
    lim = Limit(to_symbol(ne), to_symbol(nz), to_rational(z0p, z0q))
    assert str(lim.args[3]) == "+", "Limit dir != '+' for %r" % (lim,)
    via_dispatch = sstr(lim, sympy_integers=wrap)
    via_method = printer_for(wrap)._print_Limit(lim)
    return via_dispatch, via_method


def oracle_limit_registry(ne, nz, z0p, z0q, pre):
    """Registry effect of the patched `_print_Limit` on the registry-carrying
    receiver, both readings."""
    lim = Limit(to_symbol(ne), to_symbol(nz), to_rational(z0p, z0q))
    pp = registry_printer(pre)
    pp._print(lim)
    via_dispatch = list(pp.symbols)
    pp2 = registry_printer(pre)
    StrPrinter._print_Limit(pp2, lim)
    via_method = list(pp2.symbols)
    return via_dispatch, via_method


def oracle_name_text(wrap, c):
    """`StrPrinter._print_Symbol` through the dispatch and by direct call. Taken
    at the given `wrap` — the name's text must not depend on it."""
    sym = to_symbol(c)
    via_dispatch = sstr(sym, sympy_integers=wrap)
    via_method = printer_for(wrap)._print_Symbol(sym)
    return via_dispatch, via_method


def oracle_name_registry(c, pre):
    """`PythonPrinter._print_Symbol` (python.py:38-42): the registry after the
    registry-carrying receiver renders one name, both readings."""
    sym = to_symbol(c)
    pp = registry_printer(pre)
    pp._print(sym)
    via_dispatch = list(pp.symbols)
    pp2 = registry_printer(pre)
    PythonPrinter._print_Symbol(pp2, sym)
    via_method = list(pp2.symbols)
    return via_dispatch, via_method


def oracle_operand_text(wrap, p, q):
    """The recursive dispatch `Printer._print` (printer.py:238) on the SAME
    printer instance, landing on `StrPrinter._print_Rational` (str.py:574).
    Read at the top level, at the nested `_print_level` a container's
    `self._print(sub)` really runs at, and through the public entry point."""
    r = to_rational(p, q)
    top = printer_for(wrap)
    via_nested = top._print(r)
    deep = printer_for(wrap)
    deep._print_level = 1  # the container's own frame; the sub renders at >= 2
    via_deep = deep._print(r)
    via_dispatch = sstr(r, sympy_integers=wrap)
    return via_dispatch, via_nested, via_deep


def oracle_operand_registry(p, q, pre):
    """A fractional operand is not a name: the registry-carrying receiver's
    registry is untouched by printing it, both readings."""
    r = to_rational(p, q)
    pp = registry_printer(pre)
    pp._print(r)
    via_dispatch = list(pp.symbols)
    pp2 = registry_printer(pre)
    StrPrinter._print_Rational(pp2, r)
    via_method = list(pp2.symbols)
    return via_dispatch, via_method


def oracle_preamble_names(expr):
    """The registry as the public `python()` entry point exposes it
    (python.py:47-69): the `<name> = Symbol('<name>')` preamble, in registry
    order. Only meaningful from an EMPTY pre-seed, which is how `python()`
    starts."""
    out = []
    for line in python(expr).splitlines():
        if " = Symbol('" in line:
            out.append(line.split(" = Symbol('")[1].rstrip("')"))
        else:
            break
    return out


# --------------------------------------------------------------------------
# One input, all four modeled functions, shadow vs oracle.
# --------------------------------------------------------------------------

def check_one(wrap, nl, ne, nz, p, q, pre, failures):
    # Requires of the four modeled functions.
    assert is_name(nl) and is_name(ne) and is_name(nz), \
        "generator escaped is_name: %r" % ((nl, ne, nz),)
    assert p >= 0 and q >= 2 and coprime(p, q), \
        "generator escaped the model's Requires: wrap=%r p=%r q=%r" % (wrap, p, q)
    assert all(is_name(c) for c in pre), "bad pre-seed %r" % (pre,)

    def report(fn, shadow, readings):
        failures.append(
            "DISAGREE %s: input wrap=%r names=(%s,%s,%s) p=%d q=%d "
            "pre=%r (operand %s)\n  shadow = %r\n  oracle = %s"
            % (fn, wrap, chr(nl), chr(ne), chr(nz), p, q, to_names(pre),
               to_rational(p, q), shadow,
               "  ".join(repr(x) for x in readings)))

    # --- shadow, each call from a FRESH copy of the pre-seeded registry -------
    reg_eq = list(pre)
    eq_out = render_equation(wrap, nl, p, q, reg_eq)
    reg_lim = list(pre)
    lim_out = render_directed_limit(wrap, ne, nz, p, q, reg_lim)
    reg_nm = list(pre)
    nm_out = render_name(nl, reg_nm)
    reg_op = list(pre)
    op_out = render_operand(wrap, p, q, reg_op)

    # --- oracle readings -----------------------------------------------------
    eq_text_readings = oracle_equation_text(wrap, nl, p, q)
    eq_reg_readings = oracle_equation_registry(nl, p, q, pre)
    lim_text_readings = oracle_limit_text(wrap, ne, nz, p, q)
    lim_reg_readings = oracle_limit_registry(ne, nz, p, q, pre)
    nm_text_readings = oracle_name_text(wrap, nl)
    nm_reg_readings = oracle_name_registry(nl, pre)
    op_text_readings = oracle_operand_text(wrap, p, q)
    op_reg_readings = oracle_operand_registry(p, q, pre)

    if not pre:
        # The public surface `test_python_relational` reads.
        eq_reg_readings = eq_reg_readings + (
            oracle_preamble_names(Eq(to_symbol(nl), to_rational(p, q))),)
        lim_reg_readings = lim_reg_readings + (
            oracle_preamble_names(
                Limit(to_symbol(ne), to_symbol(nz), to_rational(p, q))),)
        nm_reg_readings = nm_reg_readings + (
            oracle_preamble_names(to_symbol(nl)),)

    comparisons = 0
    for fn, shadow, readings in (
            # the impl region (the shadow proper) — TEXT
            ("render_operand/text", to_str(op_out), op_text_readings),
            ("render_name/text", to_str(nm_out), nm_text_readings),
            ("render_equation/text", to_str(eq_out), eq_text_readings),
            ("render_directed_limit/text", to_str(lim_out), lim_text_readings),
            # the impl region (the shadow proper) — REGISTRY
            ("render_operand/registry", to_names(reg_op), op_reg_readings),
            ("render_name/registry", to_names(reg_nm), nm_reg_readings),
            ("render_equation/registry", to_names(reg_eq), eq_reg_readings),
            ("render_directed_limit/registry",
             to_names(reg_lim), lim_reg_readings),
            # the model's @Pure deep models (mapping.md §3.2/§3.3) must describe
            # the same real text/registry the impl region produces; `materialize`
            # is the identity on character content, so all of these agree or
            # something in the model is unfaithful.
            ("pure/render_rational", to_str(render_rational(wrap, p, q)),
             op_text_readings),
            ("pure/lit_name", to_str(lit_name(nl)), nm_text_readings),
            ("pure/eq_text", to_str(eq_text(wrap, nl, p, q)), eq_text_readings),
            ("pure/limit_text", to_str(limit_text(wrap, ne, nz, p, q)),
             lim_text_readings),
            ("pure/registered", to_names(registered(ToSeq(pre), nl)),
             nm_reg_readings),
            ("pure/eq_registry", to_names(eq_registry(ToSeq(pre), nl)),
             eq_reg_readings),
            ("pure/limit_registry",
             to_names(limit_registry(ToSeq(pre), ne, nz)), lim_reg_readings)):
        comparisons += len(readings)
        if any(shadow != o for o in readings) or \
                any(readings[0] != o for o in readings):
            report(fn, shadow, readings)

    return comparisons


def boundary_operands():
    """Boundary fractions first: the exact F2P shapes, the smallest fraction, and
    single- vs multi-digit numerator/denominator so `materialize`'s copy loop
    runs both one and many iterations. All are coprime with q >= 2."""
    return [
        (2, 3),            # F2P test_Rational, the Eq case
        (7, 2),            # F2P test_Rational, the Limit case
        (1, 2),            # smallest proper fraction
        (1, 3),
        (3, 4),
        (5, 6),
        (1, 7),
        (9, 2),            # single digit / single digit, both extremes
        (10, 3),           # two digits / one digit
        (1, 10),           # one digit / two digits
        (123, 7),
        (7, 123),
        (999999937, 2),    # long numerator (9 digits) -> long copy loop
        (1, 10 ** 10),     # long denominator (11 digits)
        (10 ** 10 + 1, 10 ** 10 + 3),
    ]


X, Y, Q, Z = ord("x"), ord("y"), ord("q"), ord("z")
ALPHA = list(range(97, 123))


def boundary_inputs():
    """(wrap, nl, ne, nz, p, q, pre) tuples. Covers the F2P shapes, every name
    key, equal and distinct limit name pairs, and pre-seeds hitting both arms of
    `registered`'s `if c in r:` for each slot."""
    out = []
    seeds = [(), (Y,), (Q, Y), (X,), (Z, X), (X, Y), (Y, X)]
    for wrap in (False, True):
        # the two F2P shapes, against every pre-seed
        for pre in seeds:
            out.append((wrap, X, X, X, 2, 3, pre))
            out.append((wrap, X, X, X, 7, 2, pre))
            out.append((wrap, X, X, Y, 7, 2, pre))
            out.append((wrap, X, Y, X, 7, 2, pre))
        # every name key, empty and occupied pre-seeds
        for c in ALPHA:
            out.append((wrap, c, c, c, 2, 3, ()))
            out.append((wrap, c, c, c, 2, 3, (c,)))
            out.append((wrap, c, c, X, 7, 2, (Y,)))
            out.append((wrap, c, X, c, 7, 2, (Y,)))
        # every fraction boundary, at the F2P names
        for (p, q) in boundary_operands():
            out.append((wrap, X, X, X, p, q, ()))
            out.append((wrap, Y, X, Z, p, q, (Q,)))
    return out


# ==========================================================================
# GENERALISED SWEEP — the WIDENED domain of the current model.py: all three
# operand kinds at every slot, and BOTH template forms of `_print_Limit`.
#
# The narrow sweep above ranges over name and fraction slots of the `plus`
# template form only, so it cannot see the direction slot or the third operand
# kind. This section closes that: it shadows the CURRENT `limit_text` /
# `limit_registry` / `eq_text` / `eq_registry` against the real patched methods
# on real `Limit` / `Eq` objects whose direction takes BOTH values.
#
# `opaque_text` / `opaque_registry` are UNINTERPRETED in the model, so here they
# are REALISED by the real callee (as `digits` and `coprime` are): for a handle
# bound to a real operand, `opaque_text(a, wrap)` is that operand's own rendering
# AT A SLOT and `opaque_registry(r, a)` is the real registry after the receiver
# renders it from `r`. Each is built as one function of its declared arguments,
# so a sweep that passes also refutes the "the same handle is forced to two
# different values at two different slots" unsatisfiability shape.
# ==========================================================================

# handle -> real operand. Every operand here is outside BOTH modelled leaf
# carriers (not a proper coprime fraction, not a one-char lowercase name), i.e.
# genuinely of the model's third kind.
def _g_operands():
    from sympy import (oo, zoo, nan, pi, E, I, Integer, Float, sin,
                       S as _S)
    ops = [oo, -oo, zoo, nan, pi, E, I, Integer(0), Integer(-5), Float(2.5),
           sin(Symbol('x')), _S.EulerGamma, Symbol('-'), Symbol('+-'),
           Symbol('+')]
    return {1000 + i: o for i, o in enumerate(ops)}


G_OPERAND = _g_operands()
G_HANDLE = {str(o): a for a, o in G_OPERAND.items()}


def g_slot_text(expr, wrap, level=1):
    """The text THIS renderer produces for `expr` AT A SLOT, i.e. in the nested
    frame a container's `self._print(sub)` really runs in. `Printer._print`
    bumps `_print_level` and `StrPrinter._print_Float` reads it
    (`full_prec == 'auto'` strips zeros only above the top frame), so the slot
    reading is not the top-level `sstr` reading for a `Float`."""
    p = printer_for(wrap)
    p._print_level = level
    return p._print(expr)


_G_TEXT_CACHE = {}


def g_opaque_text(a, wrap, failures=None):
    key = (a, wrap)
    if key not in _G_TEXT_CACHE:
        at2 = g_slot_text(G_OPERAND[a], wrap, 1)
        at3 = g_slot_text(G_OPERAND[a], wrap, 2)
        if at2 != at3 and failures is not None:
            failures.append("opaque_text level-sensitive for %r at wrap=%s: "
                            "%r vs %r" % (G_OPERAND[a], wrap, at2, at3))
        _G_TEXT_CACHE[key] = at2
    return _G_TEXT_CACHE[key]


def g_opaque_registry(names, a):
    pp = PythonPrinter({})
    pp.symbols = list(names)
    pp._print(G_OPERAND[a])
    return list(pp.symbols)


# --- the current `# pure-start`..`# pure-end` region, over names (str) --------
def g_atom_text(k, u, v, wrap, failures):
    if k == 1:
        return to_str(lit_name(u))
    if k == 0:
        return to_str(render_rational(wrap, u, v))
    return g_opaque_text(u, wrap, failures)


def g_atom_registry(names, k, u, v):
    if k == 1:
        return to_names(registered(ToSeq([ord(c) for c in names]), u))
    if k == 0:
        return list(names)
    return g_opaque_registry(names, u)


def g_eq_text(wrap, tl, tr, failures):
    return ("Eq(" + g_atom_text(tl[0], tl[1], tl[2], wrap, failures) + ", "
            + g_atom_text(tr[0], tr[1], tr[2], wrap, failures) + ")")


def g_eq_registry(names, tl, tr):
    return g_atom_registry(g_atom_registry(names, *tl), *tr)


def g_limit_text(wrap, plus, te, tz, t0, ud, failures):
    head = ("Limit(" + g_atom_text(te[0], te[1], te[2], wrap, failures) + ", "
            + g_atom_text(tz[0], tz[1], tz[2], wrap, failures) + ", "
            + g_atom_text(t0[0], t0[1], t0[2], wrap, failures))
    if plus:
        return head + ")"
    return head + ", dir='" + g_opaque_text(ud, wrap, failures) + "')"


def g_limit_registry(names, plus, te, tz, t0, ud):
    r = g_atom_registry(g_atom_registry(g_atom_registry(names, *te), *tz), *t0)
    if plus:
        return r
    return g_opaque_registry(r, ud)


# --- the bridge in: a real operand -> the model triple ----------------------
def g_triple(expr):
    """`(k, u, v)` for a real operand, or `None` when it is outside the carrier."""
    if isinstance(expr, Symbol):
        n = expr.name
        if len(n) == 1 and 97 <= ord(n) <= 122:
            return (1, ord(n), 0)
    if isinstance(expr, Rational) and not expr.is_Integer:
        p, q = expr.p, expr.q
        if p >= 0 and q >= 2 and coprime(p, q):
            return (0, p, q)
    for a, o in G_OPERAND.items():
        if type(o) is type(expr) and o == expr:
            return (2, a, 0)
    return None


def g_in_carrier(names):
    """The registry carrier holds ONE code point per entry, so a multi-character
    name (`Symbol('ab')`, the `'+-'` direction) has no preimage — mapping.md §2."""
    return all(len(n) == 1 for n in names)


def g_oracle_text(expr, wrap):
    """The real patched method, read through the public dispatch AND by direct
    application in the frame `doprint` gives it (`_print_level == 1`)."""
    via_dispatch = sstr(expr, sympy_integers=wrap)
    p = printer_for(wrap)
    p._print_level = 1
    if isinstance(expr, Limit):
        via_method = StrPrinter._print_Limit(p, expr)
    else:
        via_method = StrPrinter._print_Relational(p, expr)
    return via_dispatch, via_method


def g_oracle_registry(expr, names):
    pp = PythonPrinter({})
    pp.symbols = list(names)
    pp._print(expr)
    via_dispatch = list(pp.symbols)
    pp2 = PythonPrinter({})
    pp2.symbols = list(names)
    pp2._print_level = 1
    if isinstance(expr, Limit):
        StrPrinter._print_Limit(pp2, expr)
    else:
        StrPrinter._print_Relational(pp2, expr)
    return via_dispatch, list(pp2.symbols)


G_SEEDS = [[], ['q'], ['x'], ['-'], ['a', '-', 'b'], ['x', 'y', 'z']]


def generalised_sweep(failures):
    """Returns (inputs, comparisons, plus_arm, else_arm)."""
    from sympy import oo, zoo, nan, pi, E, I, Integer, Float, sin, S as _S
    x = Symbol('x')
    bodies = [Symbol('x'), Symbol('y'), Rational(2, 3), oo, sin(x), pi]
    variables = [Symbol('x'), Symbol('z'), Rational(7, 2), Integer(0)]
    points = [Rational(7, 2), Rational(2, 3), Symbol('y'), oo, -oo, zoo, nan,
              pi, E, I, Integer(0), Integer(-5), Float(2.5), _S.EulerGamma]
    dirs = [None, '+', '-', '+-']
    inputs = comparisons = 0
    arms = {True: 0, False: 0}

    for pt in points:
        for d in dirs:
            for body in bodies:
                for var in variables:
                    try:
                        lim = (Limit(body, var, pt) if d is None
                               else Limit(body, var, pt, dir=d))
                    except Exception:
                        continue
                    te = g_triple(lim.args[0])
                    tz = g_triple(lim.args[1])
                    t0 = g_triple(lim.args[2])
                    td = g_triple(lim.args[3])
                    if None in (te, tz, t0, td) or td[0] != 2:
                        continue
                    plus = (str(lim.args[3]) == "+")
                    arms[plus] += 1
                    inputs += 1
                    for wrap in (False, True):
                        got = g_limit_text(wrap, plus, te, tz, t0, td[1], failures)
                        rd, rm = g_oracle_text(lim, wrap)
                        comparisons += 2
                        if not (got == rd == rm):
                            failures.append(
                                "GEN limit/text %r wrap=%s: shadow=%r dispatch=%r "
                                "method=%r" % (str(lim), wrap, got, rd, rm))
                            return inputs, comparisons, arms[True], arms[False]
                    for seed in G_SEEDS:
                        rd, rm = g_oracle_registry(lim, seed)
                        if not (g_in_carrier(rd) and g_in_carrier(seed)):
                            continue
                        got = g_limit_registry(list(seed), plus, te, tz, t0, td[1])
                        comparisons += 2
                        if not (got == rd == rm):
                            failures.append(
                                "GEN limit/registry %r seed=%r: shadow=%r "
                                "dispatch=%r method=%r"
                                % (str(lim), seed, got, rd, rm))
                            return inputs, comparisons, arms[True], arms[False]

    lefts = [Symbol('y'), Symbol('x'), Rational(2, 3), oo, pi]
    rights = [Rational(2, 3), Rational(7, 2), Symbol('x'), oo, -oo, zoo, nan,
              pi, I, Integer(0), Float(2.5), Symbol('-')]
    for lhs in lefts:
        for rhs in rights:
            try:
                rel = Eq(lhs, rhs, evaluate=False)
            except Exception:
                continue
            if rel.func is not Eq or not hasattr(rel, "rel_op"):
                continue
            tl, tr = g_triple(rel.lhs), g_triple(rel.rhs)
            if None in (tl, tr):
                continue
            inputs += 1
            for wrap in (False, True):
                got = g_eq_text(wrap, tl, tr, failures)
                rd, rm = g_oracle_text(rel, wrap)
                comparisons += 2
                if not (got == rd == rm):
                    failures.append("GEN eq/text %r wrap=%s: shadow=%r "
                                    "dispatch=%r method=%r"
                                    % (str(rel), wrap, got, rd, rm))
                    return inputs, comparisons, arms[True], arms[False]
            for seed in G_SEEDS:
                rd, rm = g_oracle_registry(rel, seed)
                if not (g_in_carrier(rd) and g_in_carrier(seed)):
                    continue
                got = g_eq_registry(list(seed), tl, tr)
                comparisons += 2
                if not (got == rd == rm):
                    failures.append("GEN eq/registry %r seed=%r: shadow=%r "
                                    "dispatch=%r method=%r"
                                    % (str(rel), seed, got, rd, rm))
                    return inputs, comparisons, arms[True], arms[False]
    return inputs, comparisons, arms[True], arms[False]


def main():
    rng = random.Random(SEED)
    failures = []
    inputs = 0
    comparisons = 0

    problems = check_receiver_facts()
    if problems:
        for pr in problems:
            print("RECEIVER-FACT FAIL: " + pr)
        print("G-CONF FAIL: %d receiver fact(s) the mapping relies on do not "
              "hold." % len(problems))
        print(json.dumps({"checked": 0, "comparisons": 0,
                          "disagreements": len(problems), "seed": SEED}))
        return 1

    for (wrap, nl, ne, nz, p, q, pre) in boundary_inputs():
        assert coprime(p, q) and q >= 2, "bad boundary %d/%d" % (p, q)
        comparisons += check_one(wrap, nl, ne, nz, p, q, list(pre), failures)
        inputs += 1
        if failures:
            break

    n_boundary = inputs
    while not failures and inputs < n_boundary + N_FUZZ:
        # Fuzz the same domain: p >= 1 (p == 0 is not coprime with q >= 2),
        # q >= 2, filtered on the REAL Rational's canonicalisation invariant;
        # name keys uniform over a..z; a pre-seed of 0..3 distinct name keys.
        p = rng.randint(1, 10 ** rng.randint(1, 12))
        q = rng.randint(2, 10 ** rng.randint(1, 12))
        if not coprime(p, q):
            continue
        wrap = bool(rng.getrandbits(1))
        nl = rng.choice(ALPHA)
        ne = rng.choice(ALPHA)
        nz = rng.choice(ALPHA)
        pre = rng.sample(ALPHA, rng.randint(0, 3))
        comparisons += check_one(wrap, nl, ne, nz, p, q, pre, failures)
        inputs += 1

    # The sweep above ranges over the name and fraction slots of the `plus`
    # template form only. The generalised sweep adds the third operand kind at
    # every slot and BOTH template forms, so `plus == False` and the direction
    # slot are mechanised too rather than left to the prose.
    g_inputs = g_comparisons = g_plus = g_else = 0
    if not failures:
        g_inputs, g_comparisons, g_plus, g_else = generalised_sweep(failures)
        comparisons += g_comparisons
        if g_else == 0 or g_plus == 0:
            failures.append("generalised sweep covered only one template form: "
                            "plus=%d else=%d" % (g_plus, g_else))

    if failures:
        for f in failures[:10]:
            print(f)
        print("G-CONF FAIL: %d disagreement(s) after %d inputs (seed %d)."
              % (len(failures), inputs, SEED))
        print(json.dumps({"checked": inputs, "comparisons": comparisons,
                          "disagreements": len(failures), "seed": SEED}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py "
          "(render_equation / render_directed_limit / render_name / "
          "render_operand / materialize), in BOTH observables (rendered text "
          "and name-registry growth), == the real patched "
          "StrPrinter._print_Relational (charmap arm) / _print_Limit "
          "(dir=='+' arm) / _print_Symbol / Printer._print -> _print_Rational, "
          "text read on a configuration-carrying StrPrinter and registry read "
          "on a registry-carrying PythonPrinter sharing the SAME patched method "
          "objects, on %d Requires-satisfying inputs (%d boundary + %d fuzz, "
          "both wrap settings, %d comparisons, seed %d); 0 disagreements."
          % (inputs, n_boundary, inputs - n_boundary, comparisons, SEED))
    print("G-CONF OK (generalised): the CURRENT limit_text / limit_registry / "
          "eq_text / eq_registry semantics -- all three operand kinds at every "
          "slot, with opaque_text / opaque_registry realised by the real callee "
          "-- == the real patched _print_Limit / _print_Relational on %d "
          "Requires-satisfying real compounds (%d on the dir=='+' template "
          "form, %d on the \", dir='...'\" form, both wrap settings, 6 registry "
          "pre-seeds, %d comparisons); 0 disagreements."
          % (g_inputs, g_plus, g_else, g_comparisons))
    print(json.dumps({"checked": inputs, "comparisons": comparisons,
                      "disagreements": 0, "seed": SEED,
                      "generalised_inputs": g_inputs,
                      "generalised_comparisons": g_comparisons,
                      "generalised_plus_arm": g_plus,
                      "generalised_else_arm": g_else,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "real patched sympy/printing/str.py "
                                "(_print_Relational, _print_Limit, "
                                "_print_Symbol, _print_Rational via "
                                "Printer._print) + sympy/printing/python.py "
                                "(PythonPrinter.symbols, python())"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
