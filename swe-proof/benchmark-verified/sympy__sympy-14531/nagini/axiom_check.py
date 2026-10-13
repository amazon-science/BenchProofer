#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14531.

Executes the REAL callees the model abstracts and asserts every observation
matches the contracts encoded in model.py. Crucially, every A-reference deep
model is validated against the ACTUAL DISPATCH ENTRY POINT the gold patch routes
through — the public `sstr(...)` / `python(...)` (which call `self._print(op)`
for the sub-expressions) — never a hand-picked leaf method, so the
integer/dispatch double-mask trap cannot hide a disagreement.

model.py's renderer carries TWO pieces of state and the model pins BOTH: the
wrap CONFIGURATION (which decides how a fractional operand is written) and the
name REGISTRY (which records the simple names the renderer has rendered). In the
repo those live on two stock printer classes that inherit the SAME method
objects — `StrPrinter` has `_settings['sympy_integers']`, `PythonPrinter` has
`self.symbols` — so each observable is validated on the receiver that has it,
and `check_receiver_split()` asserts that the two receivers really do share the
one method object (otherwise the two readings would be of two functions).

  (A-consumed) `digits` == `str(int)` for a non-negative integer. The only
      property the proof consumes is that it is deterministic and NON-EMPTY
      (`len(digits(n)) >= 1`). Checked over 0, single/multi-digit, large.

  (A-reference leaf) `render_rational(wrap, p, q)` == the REAL rendering of the
      fractional operand p/q under settings={'sympy_integers': wrap}, over the
      MODELED DOMAIN (proper fraction in lowest terms: q>=2, gcd(p,q)==1):
          wrap      -> 'S(p)/q'
          not wrap  -> 'p/q'
      Validated via `sstr(Rational(p, q), sympy_integers=wrap)`. The domain is
      restricted to coprime non-integer pairs because `Rational(p,q)` reduces a
      non-coprime pair to a different fraction, and `Rational(n,1)` IS an
      `Integer` that dispatches through `_print_Integer` (yielding `'S(n)'`
      under the wrap setting) — neither is the carrier this leaf models.

  (A-reference leaf) `lit_name(c)` == the REAL rendering of `Symbol(chr(c))`,
      the same under EITHER wrap setting. This is checked, not assumed: it is
      precisely BECAUSE the name's text is configuration-independent that the
      text observable alone cannot witness who rendered the name slot, which is
      why the registry observable exists.

  (A-reference leaf) `registered(r, c)` == the REAL `PythonPrinter.symbols`
      after that receiver renders `Symbol(chr(c))` starting from `r`: appended
      unless already present, so one entry per DISTINCT name in first-render
      order (sympy/printing/python.py:38-42).

  (A-reference compound) `eq_text` / `limit_text` == the REAL
      `sstr(Eq(Symbol(n), p/q), sympy_integers=wrap)` /
      `sstr(Limit(Symbol(e), Symbol(z), p/q), sympy_integers=wrap)`. A
      relation/limit between NAMES and a fractional operand is used because
      `Eq` of two numeric constants auto-evaluates to a Boolean (no template).
      This asserts the fractional operand is rendered with the SAME `wrap` the
      compound is rendered with — i.e. the setting PROPAGATES into the
      sub-expression. With wrap=True the real output MUST contain the wrapped
      'S(p)/q' form; an operand rendered by an ambient default renderer would
      produce 'p/q' and fail. Asserted at the full-string level (no double
      mask). Mirrors the F2P test `test_Rational`.

  (A-reference compound) `eq_registry` / `limit_registry` == the REAL
      `PythonPrinter.symbols` after that receiver renders the compound: each
      NAME operand entered, left to right, duplicate-free; the fractional
      operand entering nothing. This is the observable that a name slot emitted
      as a bare constant token CANNOT satisfy — its text is identical, its
      registry effect is not. Read both through the instance dispatch and
      through the public `python()` preamble, which is the surface the F2P test
      `test_python_relational` reads.

Imports only the standard library and the repo's own api (`sympy.sstr`,
`sympy.Eq`, `sympy.Limit`, `sympy.Rational`, `sympy.Symbol`,
`sympy.printing.python.python` / `PythonPrinter`, `sympy.printing.str
.StrPrinter`) — the same surface the gold patch and the F2P tests exercise.
Exit 0 iff every obligation holds.
"""
import random
import sys
from math import gcd

from sympy import Symbol, Rational, Eq, Limit, sstr
from sympy.printing.python import PythonPrinter, python
from sympy.printing.str import StrPrinter


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_digits(n):
    """Reference for the A-consumed axiom `digits`: str(n) as code points."""
    assert n >= 0
    return [ord(c) for c in str(n)]


def model_render_rational(wrap, p, q):
    """Reference for model.py deep model `render_rational(wrap, p, q)` over the
    modeled domain (q>=2, coprime)."""
    assert p >= 0 and q >= 2 and gcd(p, q) == 1
    dp = str(p)
    dq = str(q)
    if wrap:
        return "S(" + dp + ")/" + dq
    return dp + "/" + dq


def model_is_name(c):
    """Reference for model.py `is_name(c)`: a single lowercase letter."""
    return 97 <= c <= 122


def model_lit_name(c):
    """Reference for model.py deep model `lit_name(c)`: the name's own text."""
    assert model_is_name(c)
    return chr(c)


def model_registered(reg, c):
    """Reference for model.py deep model `registered(r, c)`."""
    assert model_is_name(c)
    if c in reg:
        return list(reg)
    return list(reg) + [c]


def model_eq_text(wrap, nl, rp, rq):
    """Reference for model.py deep model `eq_text` (a name on the lhs)."""
    return ("Eq(" + model_lit_name(nl) + ", "
            + model_render_rational(wrap, rp, rq) + ")")


def model_eq_registry(reg, nl):
    """Reference for model.py deep model `eq_registry`: the ONE name operand."""
    return model_registered(reg, nl)


def model_limit_text(wrap, ne, nz, z0p, z0q):
    """Reference for model.py deep model `limit_text` (the `dir == '+'` form,
    which is what Limit(e, z, c) produces for a real point c)."""
    return ("Limit(" + model_lit_name(ne) + ", " + model_lit_name(nz) + ", "
            + model_render_rational(wrap, z0p, z0q) + ")")


def model_limit_registry(reg, ne, nz):
    """Reference for model.py deep model `limit_registry`: BOTH name operands,
    left to right."""
    return model_registered(model_registered(reg, ne), nz)


# --- carrier bridges ---------------------------------------------------------

def names_of(reg):
    """model registry (code points) -> repo registry (list of name strings)."""
    return [chr(c) for c in reg]


def registry_printer(reg):
    """A registry-carrying receiver seeded with the model's `reg`."""
    pp = PythonPrinter({})
    pp.symbols = names_of(reg)
    return pp


def preamble_names(expr):
    """The registry as the public `python()` entry point exposes it
    (sympy/printing/python.py:47-69): the `<name> = Symbol('<name>')` preamble,
    in registry order. Only meaningful from an empty start, which is how
    `python()` begins."""
    out = []
    for line in python(expr).splitlines():
        if " = Symbol('" in line:
            out.append(line.split(" = Symbol('")[1].rstrip("')"))
        else:
            break
    return out


# --- the checks --------------------------------------------------------------

def check_receiver_split():
    """The mapping reads the text observable on the configuration-carrying
    receiver and the registry observable on the registry-carrying one. That is
    only a reading of ONE function if the two receivers share the method
    object — asserted here rather than assumed."""
    assert PythonPrinter._print_Relational is StrPrinter._print_Relational, \
        "the two receivers do not share _print_Relational"
    assert PythonPrinter._print_Limit is StrPrinter._print_Limit, \
        "the two receivers do not share _print_Limit"
    assert "sympy_integers" not in PythonPrinter._default_settings, \
        "the registry-carrying receiver unexpectedly carries the wrap setting"
    try:
        PythonPrinter({"sympy_integers": True})
        raise AssertionError(
            "the registry-carrying receiver accepted the wrap setting")
    except TypeError:
        pass
    assert hasattr(PythonPrinter({}), "symbols"), \
        "the registry-carrying receiver has no registry"
    assert not hasattr(StrPrinter({}), "symbols"), \
        "the configuration-carrying receiver unexpectedly has a registry"


def check_digits_axiom(n):
    """A-consumed: str(n) is non-empty (the only property the proof uses)."""
    d = model_digits(n)
    assert len(d) >= 1, "digits(%d) empty" % n


def check_render_rational(wrap, p, q):
    """A-reference leaf: render_rational(wrap, p, q) == real render of the
    fraction p/q under sympy_integers=wrap, validated via the public dispatch
    entry point `sstr(Rational(p,q), sympy_integers=wrap)`."""
    assert q >= 2 and gcd(p, q) == 1, "out of modeled domain: %d/%d" % (p, q)
    expected = model_render_rational(wrap, p, q)
    r = Rational(p, q)
    # Guard against the carrier collapsing: a coprime q>=2 pair stays a proper
    # fraction (never an Integer), so the leaf domain is non-degenerate.
    assert r.q == q and r.p == p, (
        "domain collapse: Rational(%d,%d) reduced to %d/%d" % (p, q, r.p, r.q))
    observed = sstr(r, sympy_integers=wrap)
    assert observed == expected, (
        "render_rational deep model mismatch wrap=%r p=%d q=%d: "
        "model %r vs real %r" % (wrap, p, q, expected, observed))


def check_lit_name(wrap, c):
    """A-reference leaf: a name's text is its own single character, the same
    under either configuration."""
    assert model_is_name(c)
    observed = sstr(Symbol(chr(c)), sympy_integers=wrap)
    assert observed == model_lit_name(c), (
        "lit_name deep model mismatch wrap=%r c=%r: model %r vs real %r"
        % (wrap, chr(c), model_lit_name(c), observed))


def check_registered(reg, c):
    """A-reference leaf: `registered(r, c)` == the real registry after the
    registry-carrying receiver renders the name (python.py:38-42). Read through
    the instance dispatch and, from an empty start, through `python()`'s
    preamble."""
    assert model_is_name(c) and all(model_is_name(k) for k in reg)
    expected = names_of(model_registered(reg, c))
    pp = registry_printer(reg)
    pp._print(Symbol(chr(c)))
    assert list(pp.symbols) == expected, (
        "registered deep model mismatch reg=%r c=%r: model %r vs real %r"
        % (names_of(reg), chr(c), expected, list(pp.symbols)))
    if not reg:
        obs = preamble_names(Symbol(chr(c)))
        assert obs == expected, (
            "registered vs python() preamble mismatch c=%r: model %r vs real %r"
            % (chr(c), expected, obs))


def check_eq_text(wrap, nl, rp, rq):
    """A-reference compound: the FULL real rendering of
    Eq(Symbol(n), p/q) under sympy_integers=wrap equals the template with the
    fractional operand rendered under the SAME wrap. Asserted at the full-string
    level so a setting-dropping operand render is caught (it would leave 'p/q'
    where the model demands 'S(p)/q')."""
    assert rq >= 2 and gcd(rp, rq) == 1 and model_is_name(nl)
    expected = model_eq_text(wrap, nl, rp, rq)
    rel = Eq(Symbol(chr(nl)), Rational(rp, rq))
    # The relation must NOT auto-evaluate to a Boolean (it would have no
    # template); a symbol operand keeps it a genuine Relational.
    assert rel.func is Eq, (
        "Eq(%s, %d/%d) auto-evaluated to %r — not a Relational"
        % (chr(nl), rp, rq, rel))
    observed = sstr(rel, sympy_integers=wrap)
    assert observed == expected, (
        "eq_text deep model mismatch wrap=%r (%s, %d/%d): model %r vs real %r"
        % (wrap, chr(nl), rp, rq, expected, observed))


def check_eq_registry(reg, nl, rp, rq):
    """A-reference compound, THE ONE A CONSTANT NAME TOKEN CANNOT PASS: the real
    registry after the registry-carrying receiver renders Eq(Symbol(n), p/q).
    The name operand is entered (duplicate-free); the fractional operand enters
    nothing. Read through the instance dispatch and, from an empty start,
    through the public `python()` preamble the F2P test reads."""
    assert rq >= 2 and gcd(rp, rq) == 1 and model_is_name(nl)
    assert all(model_is_name(k) for k in reg)
    expected = names_of(model_eq_registry(reg, nl))
    rel = Eq(Symbol(chr(nl)), Rational(rp, rq))
    assert rel.func is Eq
    pp = registry_printer(reg)
    pp._print(rel)
    assert list(pp.symbols) == expected, (
        "eq_registry deep model mismatch reg=%r (%s, %d/%d): model %r vs real %r"
        % (names_of(reg), chr(nl), rp, rq, expected, list(pp.symbols)))
    if not reg:
        obs = preamble_names(rel)
        assert obs == expected, (
            "eq_registry vs python() preamble mismatch (%s, %d/%d): "
            "model %r vs real %r" % (chr(nl), rp, rq, expected, obs))


def check_limit_text(wrap, ne, nz, z0p, z0q):
    """A-reference compound: the FULL real rendering of
    Limit(e, z, p/q) under sympy_integers=wrap equals the template with the
    limit point rendered under the SAME wrap. Mirrors the F2P
    `Limit(x, x, Rational(7, 2))` case."""
    assert z0q >= 2 and gcd(z0p, z0q) == 1
    assert model_is_name(ne) and model_is_name(nz)
    lim = Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(z0p, z0q))
    # Real-point limit takes the dir == '+' branch the model encodes.
    assert str(lim.args[3]) == "+", "Limit dir != '+' for %r" % (lim,)
    expected = model_limit_text(wrap, ne, nz, z0p, z0q)
    observed = sstr(lim, sympy_integers=wrap)
    assert observed == expected, (
        "limit_text deep model mismatch wrap=%r (%s, %s, %d/%d): "
        "model %r vs real %r"
        % (wrap, chr(ne), chr(nz), z0p, z0q, expected, observed))


def check_limit_registry(reg, ne, nz, z0p, z0q):
    """A-reference compound: the real registry after the registry-carrying
    receiver renders Limit(e, z, p/q) — BOTH name operands entered, left to
    right, duplicate-free. With distinct names this separates the two slots, so
    neither can be a constant token."""
    assert z0q >= 2 and gcd(z0p, z0q) == 1
    assert model_is_name(ne) and model_is_name(nz)
    assert all(model_is_name(k) for k in reg)
    lim = Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(z0p, z0q))
    assert str(lim.args[3]) == "+", "Limit dir != '+' for %r" % (lim,)
    expected = names_of(model_limit_registry(reg, ne, nz))
    pp = registry_printer(reg)
    pp._print(lim)
    assert list(pp.symbols) == expected, (
        "limit_registry deep model mismatch reg=%r (%s, %s, %d/%d): "
        "model %r vs real %r"
        % (names_of(reg), chr(ne), chr(nz), z0p, z0q, expected,
           list(pp.symbols)))
    if not reg:
        obs = preamble_names(lim)
        assert obs == expected, (
            "limit_registry vs python() preamble mismatch (%s, %s, %d/%d): "
            "model %r vs real %r"
            % (chr(ne), chr(nz), z0p, z0q, expected, obs))


def check_operand_registers_nothing(reg, p, q):
    """A-reference leaf: a fractional operand is not a name — rendering it
    leaves the registry-carrying receiver's registry untouched. This is what
    makes the compounds' registry clauses attributable to the NAME slots."""
    assert q >= 2 and gcd(p, q) == 1 and all(model_is_name(k) for k in reg)
    expected = names_of(reg)
    pp = registry_printer(reg)
    pp._print(Rational(p, q))
    assert list(pp.symbols) == expected, (
        "render_operand registry clause violated reg=%r %d/%d: real %r"
        % (expected, p, q, list(pp.symbols)))


def check_f2p_exact():
    """The exact F2P assertions from test_Rational / test_python_relational.
    Each named F2P sub-case is asserted explicitly; none is skipped."""
    x = Symbol("x")
    y = Symbol("y")
    # test_Rational (the two new lines):
    assert sstr(Eq(x, Rational(2, 3)), sympy_integers=True) == "Eq(x, S(2)/3)", \
        "F2P test_Rational Eq case failed"
    assert sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) == \
        "Limit(x, x, S(7)/2)", "F2P test_Rational Limit case failed"
    # The pre-existing correct case (sanity, must still hold):
    assert sstr(x + Rational(1, 2), sympy_integers=True) == "x + S(1)/2", \
        "settings already worked on Add (control) -- unexpectedly broken"
    # test_python_relational (the changed Eq line): the symbol declarations are
    # emitted because the operands are traversed via self._print, i.e. because
    # the renderer that owns the relation is the one that renders the name.
    assert python(Eq(x, y)) == \
        "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)", \
        "F2P test_python_relational Eq case failed"
    # The same registry surface on the Limit template (not an F2P line; an
    # additional real reading of the same patched delegation).
    assert python(Limit(x, y, Rational(7, 2))) == \
        "x = Symbol('x')\ny = Symbol('y')\ne = Limit(x, y, Rational(7, 2))", \
        "registry surface on the Limit template failed"


ALPHA = list(range(97, 123))
X, Y, Q, Z = ord("x"), ord("y"), ord("q"), ord("z")
SEEDS = [[], [Y], [Q, Y], [X], [Z, X], [X, Y], [Y, X]]


def main():
    # --- the receiver facts the mapping relies on ----------------------------
    check_receiver_split()

    # --- A-consumed: digits non-empty ---------------------------------------
    for n in [0, 1, 2, 3, 7, 9, 10, 39, 99, 100, 1000, 10 ** 10, 123456789]:
        check_digits_axiom(n)

    # --- A-reference leaves: names -------------------------------------------
    for wrap in (False, True):
        for c in ALPHA:
            check_lit_name(wrap, c)
    for c in ALPHA:
        for reg in SEEDS:
            check_registered(reg, c)

    # --- A-reference leaf: render_rational over a coprime (wrap, p, q) grid ---
    rng = random.Random(14531)
    # boundary: the F2P fractions + small coprime proper fractions.
    # (numerator 0 is excluded: Rational(0, q) collapses to Integer 0, which is
    #  not a proper fraction in lowest terms — out of the modeled leaf domain.)
    leaf_boundary = [(2, 3), (1, 2), (7, 2), (5, 6), (10, 3), (1, 10 ** 10),
                     (1, 7), (123, 7), (3, 4), (1, 3)]
    for wrap in (False, True):
        for (p, q) in leaf_boundary:
            assert gcd(p, q) == 1 and q >= 2, "bad boundary %d/%d" % (p, q)
            check_render_rational(wrap, p, q)
        # fuzz the leaf over coprime non-integer pairs (numerator >= 1 so the
        # fraction never collapses to Integer 0)
        n = 0
        while n < 2000:
            p = rng.randint(1, 5000)
            q = rng.randint(2, 5000)
            if gcd(p, q) != 1:
                continue
            check_render_rational(wrap, p, q)
            n += 1
    for (p, q) in leaf_boundary:
        for reg in SEEDS:
            check_operand_registers_nothing(reg, p, q)

    # --- A-reference compounds: text propagation and registry growth ---------
    for wrap in (False, True):
        for (rp, rq) in [(2, 3), (1, 2), (7, 2), (5, 6), (1, 7), (3, 4)]:
            for nl in (X, Y, Q, Z):
                check_eq_text(wrap, nl, rp, rq)
        for (z0p, z0q) in [(7, 2), (1, 2), (2, 3), (10, 3), (1, 3), (5, 6)]:
            for (ne, nz) in ((X, X), (X, Y), (Y, X), (Q, Z)):
                check_limit_text(wrap, ne, nz, z0p, z0q)
        # every name key at the F2P fractions
        for c in ALPHA:
            check_eq_text(wrap, c, 2, 3)
            check_limit_text(wrap, c, c, 7, 2)
            check_limit_text(wrap, c, X, 7, 2)
            check_limit_text(wrap, X, c, 7, 2)
        # fuzz the compound sites (numerator >= 1: a proper fraction operand)
        n = 0
        while n < 1500:
            rp, rq = rng.randint(1, 999), rng.randint(2, 999)
            if gcd(rp, rq) != 1:
                continue
            check_eq_text(wrap, rng.choice(ALPHA), rp, rq)
            z0p, z0q = rng.randint(1, 999), rng.randint(2, 999)
            while gcd(z0p, z0q) != 1:
                z0p, z0q = rng.randint(1, 999), rng.randint(2, 999)
            check_limit_text(wrap, rng.choice(ALPHA), rng.choice(ALPHA),
                             z0p, z0q)
            n += 1

    # The registry observable is wrap-INDEPENDENT (registration does not consult
    # `_settings`), so it is checked once per (registry, names, fraction).
    for reg in SEEDS:
        for (rp, rq) in [(2, 3), (7, 2), (1, 2)]:
            for nl in (X, Y, Q, Z):
                check_eq_registry(reg, nl, rp, rq)
            for (ne, nz) in ((X, X), (X, Y), (Y, X), (Q, Z), (Y, Y)):
                check_limit_registry(reg, ne, nz, rp, rq)
    for c in ALPHA:
        check_eq_registry([], c, 2, 3)
        check_eq_registry([c], c, 2, 3)
        check_limit_registry([], c, c, 7, 2)
        check_limit_registry([], c, X, 7, 2)
        check_limit_registry([X], c, X, 7, 2)
        check_limit_registry([Y], X, c, 7, 2)
    n = 0
    while n < 1500:
        rp, rq = rng.randint(1, 999), rng.randint(2, 999)
        if gcd(rp, rq) != 1:
            continue
        reg = rng.sample(ALPHA, rng.randint(0, 3))
        check_eq_registry(reg, rng.choice(ALPHA), rp, rq)
        check_limit_registry(reg, rng.choice(ALPHA), rng.choice(ALPHA), rp, rq)
        check_operand_registers_nothing(reg, rp, rq)
        n += 1

    # --- the exact F2P assertions -------------------------------------------
    check_f2p_exact()

    print("G-AX OK: the two receivers share the patched method objects "
          "(_print_Relational / _print_Limit) and the wrap/registry state is "
          "split between them exactly as mapping.md §2 declares; digits "
          "(A-consumed non-empty) sound; render_rational deep model == real "
          "sstr(Rational(p,q), sympy_integers=wrap) over the coprime "
          "non-integer boundary grid + 4000 fuzz fractions (both settings); "
          "lit_name == the real Symbol text under BOTH settings for all 26 name "
          "keys; registered == the real PythonPrinter.symbols growth over 26 "
          "keys x 7 pre-seeds; a fractional operand registers nothing; "
          "eq_text/limit_text deep model == real sstr(Eq(n, p/q) / "
          "Limit(e, z, p/q), sympy_integers=wrap) over boundary + ~6000 "
          "compound fuzz inputs -- the setting PROPAGATES into the fractional "
          "sub-expression; eq_registry/limit_registry deep model == the real "
          "registry growth (instance dispatch AND the public python() "
          "preamble) over boundary + 1500 fuzz inputs -- the NAME operands are "
          "entered by the renderer that owns the compound; exact F2P "
          "assertions (test_Rational + test_python_relational) hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
