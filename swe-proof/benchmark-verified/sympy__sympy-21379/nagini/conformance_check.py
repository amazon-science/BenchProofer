#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21379 (nagini).

Refutes (never proves) the refinement leg: does model.py's MODEL actually agree
with the REAL patched repo code it claims to model?  Both sides are executed on
the same operand pairs and their observable outputs are compared structurally.

SHADOW — the `# impl-start` / `# impl-end` region of `model.py`, copied VERBATIM
(`shadow_reduce_extract_common_factor` below).  On nagini the model IS Python,
so nothing is transliterated: the body is byte-for-byte model.py's impl region
(comments included) with ONLY the contract calls removed — the two `Assert(...)`
lines.  The signature's `Requires(...)` lines are likewise dropped.  Nothing is
renamed, reordered or "simplified"; the double factor call (`common_factor_
compute` then the `G = common_factor(code)` rebind that mapping.md §1 explains)
is preserved exactly, so the shadow re-invokes the real `gcd` twice just as the
model does.  The model's `pure` region is EMPTY (model.py lines 118-121: "no
derived pure spec helpers"), so there is no `@Pure` spec helper to copy.

The model's four `@ContractOnly` callees have no body to copy, so — as the
contract requires — each one CALLS THE REAL REPO FUNCTION it axiomatizes
(mapping.md §1/§4), and the axiom is therefore exercised rather than assumed:

  * `common_factor_compute(code)`  -> the REAL `gcd(p, q)` call as MADE at
    `sympy/core/mod.py:169` @ base_commit (the raising facet).  A real
    `PolynomialError` (`sympy/polys/polyerrors.py`) is re-signalled as the
    model's user-defined `FactorUnavailable` (mapping.md §2, row 4).
  * `common_factor(code)`          -> the REAL `gcd(p, q)`, value facet (same
    call, second invocation, exactly as the impl region makes it).
  * `divide_out(value, factor)`    -> the REAL
    `sympy.core.exprtools.gcd_terms(value/factor, clear=False, fraction=False)`
    as called at `sympy/core/mod.py:171-172`.
  * `build_result(factor, p, q)`   -> the tail construction `G*cls(p, q, …)`
    (mapping.md §4.3), performed by CALLING the real `Mod`.  Both the argument
    triple AND the constructed value are compared: the triple is the faithful
    concrete reading of an OPAQUE 3-argument constructor (two applications are
    equal exactly when all three arguments are), and the built value additionally
    catches a divergence that the arguments alone would hide.

ORACLE — the REAL patched block, CALLED, not reimplemented.  Two independent
readings of it, and they must agree with each other as well as with the shadow:

  (A) `oracle_block(p, q)` execs the patched block's OWN SOURCE TEXT, lifted at
      runtime out of the loaded `Mod.eval` with `inspect.getsource` (the lines
      between the "extract gcd" comment and `pwas, qwas = p, q`, i.e.
      `sympy/core/mod.py:168-176` post-patch).  The callee namespace is built by
      exec'ing `Mod.eval`'s OWN local `from sympy… import` lines, so `gcd`,
      `gcd_terms`, `S` and `PolynomialError` are the very objects the real
      function binds.  Nothing here is retyped from patch.diff by hand: if the
      loaded source is not the patched source, `_assert_patched()` aborts before
      any verdict is printed, so a green run cannot come from unpatched code.
  (B) `insitu_trace(p, q)` drives the REAL `Mod(p, q)` and captures the real
      frame's `(G, p, q)` locals at the `pwas, qwas` line with `sys.settrace`,
      AND records whether the patched recovery line (`G = S.One`) was executed —
      the patched function itself, running in situ, no source surgery at all.
      `Mod.eval` returns early for many pairs and then never reaches the block;
      such pairs yield no observation and are reported separately.  Every pair
      that DOES reach it must match (A) exactly, and the recovery arm must be
      taken exactly on the refusal shape (code 2).  (B) is the guard that (A)'s
      source-lift is a faithful driver of the real function rather than a
      convenient paraphrase of it.  It costs ~13 ms/input against ~25 µs for (A),
      hence (A) carries all 1e5 inputs and (B) samples the boundary catalogue.

TYPE BRIDGE (mapping.md §2, inverted).  The model works over an integer
operand-shape `code` (0/1/2) plus two opaque integer value carriers `p`, `q`;
the real block wants a SymPy `Expr` pair.  Inverted:

  `p`, `q` (opaque int carriers)  <->  the real `Expr` operands themselves (the
      model never inspects an operand's value — it only copies it, hands it to
      `divide_out`, or passes it to `build_result` — so the real `Expr` serves
      directly as the opaque carrier, and structural `Expr` equality is the
      carrier equality).
  `code`                          <->  the real `gcd(p, q)` outcome per
      mapping.md §3: raises `PolynomialError` -> 2; returns `G != 1` -> 0;
      returns `G == 1` -> 1.
  factor `1` (int)                <->  `S.One` (and any `G == 1`, incl. the
      `Float(1.0)` a Float operand pair yields).
  `FactorUnavailable`             <->  `PolynomialError`.

Generation runs CONCRETE -> ABSTRACT: a real operand pair is drawn first and its
`code` is then READ OFF the real `gcd`'s behaviour, so every generated input
satisfies `Requires(0 <= code and code <= 2)` by construction and no input is
ever manufactured to fit a branch.  `code` is derived by a probe call that is
SEPARATE from the shadow's own call, so a pair on which `gcd` is not
reproducible (this issue's own symptom is cache-order dependent) shows up as a
path/code disagreement instead of being silently absorbed.  A pair on which
`gcd` raises something OTHER than `PolynomialError` has no `code` under §3, is
outside the modeled domain, and is counted and reported rather than scored.

INPUTS.  The modeled abstract input space of the branch facet is FINITE and
tiny — `code in {0, 1, 2}` — so it is covered EXHAUSTIVELY.  ANTI-VACUITY: the
run FAILS unless every code and every impl branch carries >= 1% of the checked
inputs, AND both F2P dividend shapes are observed taking the patched recovery arm
inside the real `Mod.eval` — a generator that dodged the branch the gold patch
changed must not be able to report green.
The operand carriers are unbounded, so the same three-code space is then fuzzed
with >= 1e5 concrete `Expr` instantiations: (1) a boundary catalogue — the exact
F2P/issue shape `Piecewise((x, y > x), (y, True))/z`, bare and Float-divided
Piecewise, Piecewise-vs-Piecewise, singleton/identity/zero operands, oo/nan/zoo,
Float, Rational, irrational, imaginary and transcendental factors, negated
operands, and `test_Mod`'s own `(12*x + 18*y) % (3*x)` pair; (2) the in-situ
trace cross-check (B) over that catalogue; (3) the issue's end-to-end
`exp(sinh(Piecewise((x, y > x), (y, True))/z)).subs({1: 1.0})`, which must now
complete; (4) seeded grammar fuzz deliberately biased onto all three codes to
fill the count.

Pinned seed: 21379 (recorded in mapping.md under `## G-CONF`).

Comparison is STRICT: `sympy.srepr` structural identity on the whole
`(factor, p, q, built)` tuple, not mathematical `==`, so a shadow that returned
`S.One` where the real block produced `Float(1.0)` would be refuted rather than
excused.  A shadow raise is itself a disagreement (the spec has no `Exsures`).

MUTATION CONTROLS (run before this script was installed; each was caught): a
shadow that skips the `if G != 1` transform; a shadow that lets the refusal
escape (the PRE-patch behaviour, i.e. the bug); a shadow that returns a
non-identity factor on the refusal path; and an unpatched /testbed (refused with
`G-CONF ERROR`, exit 2 — it did not pass).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1.  stdlib + the sympy under test only (no
hypothesis needed — the generator is a pinned `random.Random`).
"""
import inspect
import json
import random
import sys
import textwrap

SEED = 21379
N_FUZZ = 100_000
MAX_REPORT = 5


# ---------------------------------------------------------------------------
# the model's carrier declarations (model.py lines 51-55, minus docstring text)
# ---------------------------------------------------------------------------
class FactorUnavailable(Exception):
    """The model's refusal signal; stands in for the repo's PolynomialError
    (mapping.md §2, row 4)."""


# ---------------------------------------------------------------------------
# the real repo callees + the patched block, lifted from the loaded module
# ---------------------------------------------------------------------------
import sympy                                                       # noqa: E402
from sympy import (Float, Integer, Piecewise, Rational, S, Mod,     # noqa: E402
                   nan, oo, zoo, sqrt, sin, sinh, exp, srepr,
                   symbols, sympify, I)
from sympy.core import mod as _modmod                               # noqa: E402
from sympy.core.exprtools import gcd_terms as _real_gcd_terms       # noqa: E402
from sympy.polys.polytools import gcd as _real_gcd                  # noqa: E402
from sympy.polys.polyerrors import PolynomialError                  # noqa: E402

_MOD_FILE = _modmod.__file__
_EVAL_SRC_LINES, _EVAL_FIRST_LINE = inspect.getsourcelines(_modmod.Mod.eval)
_EVAL_SRC = "".join(_EVAL_SRC_LINES)


def _assert_patched():
    """Refuse to report any verdict unless the LOADED module really is the
    patched one (the gate applies patch.diff to /testbed before this runs).
    A green G-CONF must not be obtainable from unpatched code."""
    missing = [needle for needle in
               ("except PolynomialError",
                "from sympy.polys.polyerrors import PolynomialError",
                "gcd_terms(i/G, clear=False, fraction=False)")
               if needle not in _EVAL_SRC]
    if missing:
        print("G-CONF ERROR: loaded sympy/core/mod.py is not the patched "
              "source; missing %r (file=%s)" % (missing, _MOD_FILE))
        print(json.dumps({"status": "error", "instance": "sympy__sympy-21379",
                          "reason": "oracle module not patched",
                          "missing": missing}))
        sys.exit(2)


def _lift_patched_block():
    """The patched block's OWN source text, plus the namespace `Mod.eval` binds
    for it.  Returns (code_object, callee_namespace, block_text, abs_lineno of
    the `pwas, qwas` anchor, abs_lineno of the patched `G = S.One` recovery)."""
    start = end = recovery = None
    for off, line in enumerate(_EVAL_SRC_LINES):
        if start is None and "extract gcd" in line:
            start = off
        elif start is not None and "pwas, qwas" in line:
            end = off
            break
        elif start is not None and line.strip() == "G = S.One":
            recovery = off
    if start is None or end is None or recovery is None:
        print("G-CONF ERROR: could not locate the extract-gcd block in the "
              "loaded Mod.eval source")
        print(json.dumps({"status": "error", "instance": "sympy__sympy-21379",
                          "reason": "block delimiters not found in oracle"}))
        sys.exit(2)
    block = textwrap.dedent("".join(_EVAL_SRC_LINES[start + 1:end]))
    # Mod.eval's own local imports, so the oracle's callees are the very objects
    # the real function binds (not a hand-picked set of look-alikes).
    imports = "".join(textwrap.dedent(l) for l in _EVAL_SRC_LINES
                      if l.strip().startswith("from sympy"))
    ns = {}
    exec(compile(imports, "<Mod.eval imports>", "exec"), ns)
    for needed in ("gcd", "gcd_terms", "S", "PolynomialError"):
        if needed not in ns:
            print("G-CONF ERROR: Mod.eval's local imports did not provide %r"
                  % needed)
            sys.exit(2)
    return (compile(block, "<Mod.eval extract-gcd block>", "exec"), ns, block,
            _EVAL_FIRST_LINE + end, _EVAL_FIRST_LINE + recovery)


_ORACLE_CODE, _ORACLE_NS = None, None
ORACLE_BLOCK_TEXT, _ANCHOR_LINE, _RECOVERY_LINE = "", 0, 0


def oracle_block(p, q):
    """ORACLE (A): the patched block's own source text, exec'd on (p, q).
    Returns the `(G, p, q, built)` the block hands to `Mod.eval`'s tail."""
    ns = dict(_ORACLE_NS)
    ns["p"] = p
    ns["q"] = q
    exec(_ORACLE_CODE, ns)
    return _built(ns["G"], ns["p"], ns["q"])


def insitu_trace(p, q):
    """ORACLE (B): drive the REAL `Mod(p, q)` and capture the real frame's
    `(G, p, q)` at the `pwas, qwas` line, plus whether the patched recovery line
    (`G = S.One`) was executed.  Returns `(quad, took_recovery)`, or None when
    `Mod.eval` returned before reaching the block (or was not entered).

    This is the real patched function running IN SITU — no source surgery — and
    it is what licenses ORACLE-A's source-lift as a faithful driver."""
    captured = []
    recovery = []

    def _local(frame, event, arg):
        if event == "line":
            if frame.f_lineno == _RECOVERY_LINE:
                recovery.append(True)
            elif frame.f_lineno == _ANCHOR_LINE and not captured:
                loc = frame.f_locals
                captured.append(_built(loc.get("G"), loc.get("p"), loc.get("q")))
        return _local

    def _global(frame, event, arg):
        if (frame.f_code.co_filename == _MOD_FILE
                and frame.f_code.co_name == "eval"):
            return _local
        return None

    old = sys.gettrace()
    sys.settrace(_global)
    try:
        Mod(p, q)
    except Exception:
        pass
    finally:
        sys.settrace(old)
    if not captured:
        return None
    return (captured[0], bool(recovery))


# ---------------------------------------------------------------------------
# the @ContractOnly bridges: each one CALLS the real repo callee (mapping.md §1)
# ---------------------------------------------------------------------------
class _Operands:
    """The concrete operand pair the abstract `code` stands for.  The verbatim
    impl region passes only `code` to the factor callees (the model's carrier),
    so the pair the real `gcd` is applied to is carried here — this IS the
    §2 type bridge, nothing more."""
    p = None
    q = None
    took_transform = False
    took_refusal = False
    build_factor_trivial = None

    @classmethod
    def bind(cls, p, q):
        cls.p, cls.q = p, q
        cls.took_transform = False
        cls.took_refusal = False
        cls.build_factor_trivial = None


def common_factor_compute(code):
    """`@ContractOnly` (raising facet) -> the REAL `gcd(p, q)` call as made at
    sympy/core/mod.py:169.  PolynomialError -> the model's FactorUnavailable."""
    try:
        return _real_gcd(_Operands.p, _Operands.q)
    except PolynomialError:
        _Operands.took_refusal = True
        raise FactorUnavailable()


def common_factor(code):
    """`@ContractOnly` (value facet) -> the REAL `gcd(p, q)`, same call site."""
    return _real_gcd(_Operands.p, _Operands.q)


def divide_out(value, factor):
    """`@ContractOnly` -> the REAL `gcd_terms(value/factor, clear=False,
    fraction=False)` as called at sympy/core/mod.py:171-172."""
    _Operands.took_transform = True
    return _real_gcd_terms(value / factor, clear=False, fraction=False)


def build_result(factor, p, q):
    """`@ContractOnly` -> the value the block feeds into `Mod.eval`'s tail: the
    `G*cls(p, q, …)` construction (mapping.md §4.3), built by CALLING the real
    `Mod`.  Returns both the argument triple (an OPAQUE 3-argument constructor is
    faithfully realized by its arguments: two applications are equal exactly when
    all three arguments are) and the real constructed value, so the comparison
    covers the built value too and not only the arguments.
    `1` (the model's identity factor) bridges to `S.One` (mapping.md §2)."""
    _Operands.build_factor_trivial = bool(factor == 1)
    return _built(sympify(factor), p, q)


def _built(factor, p, q):
    """The tail construction as the real `Mod.eval` performs it."""
    try:
        value = factor * Mod(p, q, evaluate=False)
    except Exception as e:            # a construction the real tail also cannot do
        value = "construction raised %s" % type(e).__name__
    return (factor, p, q, value)


# ---------------------------------------------------------------------------
# SHADOW — model.py's impl region, VERBATIM (only the Assert contract calls and
# the signature's Requires removed).  Do not restructure.
# ---------------------------------------------------------------------------
def shadow_reduce_extract_common_factor(code, p, q):
    # impl-start
    # pr, qr are the operands as they enter the result: unchanged unless the
    # factor is not the identity, in which case each is passed through the
    # transform helper. The parameters p, q are read-only and keep their original
    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
    # ...) refer to the operands as given (directive 5: read-only inputs are not
    # mutated).
    pr = p
    qr = q
    try:
        # The single factor-producing call. Its raising facet
        # (common_factor_compute) raises for the unanswerable input (code 2); for
        # an answerable input it returns the factor, whose value is the helper's
        # own pure-facet output common_factor(code). On normal completion this
        # establishes code in {0, 1}, so the value facet is well-defined and the
        # factor G is exactly common_factor(code).
        G = common_factor_compute(code)
        G = common_factor(code)
        if G != 1:
            # factor is not the identity: pass each operand through the transform
            # helper, then build the value from the transformed operands. Because
            # G is common_factor(code) and divide_out is opaque, the transformed
            # operands are exactly the postcondition's witnesses (clause 3a) — an
            # implementation that skips this step cannot discharge them.
            pr = divide_out(p, G)
            qr = divide_out(q, G)
        # On normal completion the operands were transformed exactly when
        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
        return build_result(G, pr, qr)
    except FactorUnavailable:
        # the unanswerable input: keep the identity factor; the operands enter
        # the value unchanged. The raise occurs only for code 2
        # (common_factor_compute's Exsures guard), so this handler runs only
        # there; pr, qr are still their original p, q (never reassigned).
        return build_result(1, pr, qr)
    # impl-end


# ---------------------------------------------------------------------------
# type bridge: concrete pair -> abstract code (mapping.md §2/§3, inverted)
# ---------------------------------------------------------------------------
def abstract_code(p, q):
    """Read the model's operand-shape `code` off the REAL `gcd`'s behaviour
    (mapping.md §3).  Returns None when the pair is OUTSIDE the modeled domain
    (`gcd` raises something other than PolynomialError), which is reported, not
    scored."""
    try:
        G = _real_gcd(p, q)
    except PolynomialError:
        return 2
    except Exception:
        return None
    return 1 if G == 1 else 0


def strict_triple(t):
    """STRICT structural key for a `(factor, p, q, built)` tuple: srepr, not `==`,
    so `S.One` vs `Float(1.0)` is a disagreement and not excused."""
    return tuple(v if isinstance(v, str) else srepr(sympify(v)) for v in t)


def _f2p_shapes():
    """The two dividend shapes from the issue / F2P, as srepr keys: the exact
    reported operand and its `z ** -1.0` variant.  Both must be observed taking
    the patched recovery arm inside the real `Mod.eval`."""
    x, y, z = symbols('x y z', real=True)
    pw = Piecewise((x, y > x), (y, True))
    return {srepr(pw / z), srepr(pw * z ** -1.0)}


F2P_SHAPES = _f2p_shapes()


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def boundary_pairs():
    """Boundary catalogue: the F2P/issue shape, every code, degenerate and
    exotic operands.  (mapping.md §3 example pairs included verbatim.)"""
    x, y, z = symbols('x y z', real=True)
    a, b = symbols('a b')
    pw = Piecewise((x, y > x), (y, True))
    out = [
        # --- code 2: the refusal (the issue's own shape) ---
        (pw / z, S.One),                       # the exact F2P/issue operand
        (pw * z ** -1.0, S.One),               # Float-power divided variant
        (pw, S.One),
        (pw, x),
        (pw, pw),
        (pw / z, S(2)),
        (pw / z, pw),
        (Piecewise((x, x > 2), (2, True)), x),  # mapping.md §3 example
        (Piecewise((x, y > x), (y, True)) / z, x * y),
        (sympify(1) + pw, x),
        # --- code 0: non-trivial factor (the transform branch) ---
        (2 * x, 2 * y),                        # mapping.md §3 example
        (S(6), S(9)),                          # mapping.md §3 example
        (x ** 2 - 1, x ** 2 - 3 * x + 2),      # mapping.md §3 example
        (12 * x + 18 * y, 3 * x),              # test_Mod's own F2P assertion
        (6 * x, 4 * x),
        (12 * x * y, 8 * x),
        (x + 1, x + 1),
        (S(15), S(10)),
        (S.Zero, S.Zero),
        (S.Zero, x),
        (x, S.Zero),
        (-x, -2 * x),
        (I * x, x),
        (sqrt(2) * x, sqrt(2) * y),
        (x * sin(y), sin(y)),
        (exp(x), exp(x)),
        (Rational(1, 2) * x, Rational(1, 2) * y),
        # --- code 1: trivial factor (no transform) ---
        (x, y),                                # mapping.md §3 example
        (S(7), S(13)),                         # mapping.md §3 example
        (x * y, S.One),
        (S.One, S.One),
        (oo, x),
        (nan, x),
        (zoo, x),
        (Float(0.6) * x, Float(0.3) * y),      # Float-1 gcd (bridge: 1.0 == 1)
        (Rational(1, 3) * x, Rational(2, 3) * y),
        (a, b),
        (sinh(pw / z), x),                     # Piecewise under a function
        (-x, -y),
    ]
    return out


def fuzz_pairs(rng):
    """Seeded grammar fuzz, biased so all three codes stay heavily covered.
    Unbounded: the driver consumes it until the checked count is reached, so an
    out-of-domain draw shrinks nothing but its own slot."""
    x, y, z = symbols('x y z', real=True)
    a, b = symbols('a b')
    gens = [x, y, z, a, b, S.One, x * y, x ** 2, sin(x), exp(y), sqrt(2)]
    coeffs = [S(k) for k in range(1, 13)] + [Rational(1, 2), Rational(2, 3),
                                             Float(0.5), S(-3)]
    cond_syms = [x, y, a, b]
    branch_vals = [x, y, a, b, S(2), S(3), x * y, S.Zero]
    denoms = [z, x, S(2), S.One, x * z, z ** -1.0]
    while True:
        r = rng.random()
        if r < 0.34:
            # code-2 leg: a Piecewise-bearing operand (the patched branch)
            c1 = rng.choice(branch_vals)
            c2 = rng.choice(branch_vals)
            if c1 == c2:
                c2 = c2 + 1
            cs = rng.choice(cond_syms)
            pw = Piecewise((c1, cs > rng.choice([0, 1, 2])), (c2, True))
            den = rng.choice(denoms)
            other = rng.choice([S.One, S(2), x, x * y, pw])
            yield (pw / den if rng.random() < 0.7 else pw, other)
        elif r < 0.67:
            # code-0 leg: a deliberately shared factor
            shared = rng.choice(coeffs) * rng.choice(gens)
            yield (shared * rng.choice(gens), shared * rng.choice(gens))
        else:
            # mixed: mostly code 1, sometimes code 0
            yield (rng.choice(coeffs) * rng.choice(gens),
                   rng.choice(coeffs) * rng.choice(gens))


def f2p_end_to_end():
    """The issue's own reproducer must now complete (the behaviour under
    specification, end to end through the real Mod.eval)."""
    from sympy.core.cache import clear_cache
    problems = []
    x, y, z = symbols('x y z', real=True)
    for fn in (sinh,):
        clear_cache()
        expr = exp(fn(Piecewise((x, y > x), (y, True)) / z))
        try:
            expr.subs({1: 1.0})
        except Exception as e:                                  # pragma: no cover
            problems.append("%s: %s: %s" % (fn.__name__, type(e).__name__, e))
    pw = Piecewise((x, y > x), (y, True))
    try:
        got = Mod(pw / z, S.One)
        if not isinstance(got, Mod):
            problems.append("Mod(pw/z, 1) collapsed to %r" % (got,))
    except Exception as e:                                      # pragma: no cover
        problems.append("Mod(pw/z,1): %s: %s" % (type(e).__name__, e))
    return problems


# ---------------------------------------------------------------------------
def main():
    global _ORACLE_CODE, _ORACLE_NS, ORACLE_BLOCK_TEXT
    global _ANCHOR_LINE, _RECOVERY_LINE
    _assert_patched()
    (_ORACLE_CODE, _ORACLE_NS, ORACLE_BLOCK_TEXT, _ANCHOR_LINE,
     _RECOVERY_LINE) = _lift_patched_block()

    rng = random.Random(SEED)
    disagreements = []
    checked = 0
    out_of_domain = 0
    codes_seen = {0: 0, 1: 0, 2: 0}
    branches = {"transform": 0, "refusal": 0, "no_transform": 0}
    insitu_checked = 0
    insitu_unreached = 0
    insitu_recovered = []

    boundary = boundary_pairs()

    def observe(p, q, trace_insitu):
        nonlocal checked, out_of_domain, insitu_checked, insitu_unreached
        code = abstract_code(p, q)
        if code is None:
            out_of_domain += 1
            return
        codes_seen[code] += 1
        _Operands.bind(p, q)
        try:
            shadow = shadow_reduce_extract_common_factor(code, p, q)
        except Exception as e:
            disagreements.append((code, p, q,
                                  "shadow raised %s: %s" % (type(e).__name__, e),
                                  "(oracle not run)"))
            return
        if _Operands.took_refusal:
            branches["refusal"] += 1
        elif _Operands.took_transform:
            branches["transform"] += 1
        else:
            branches["no_transform"] += 1
        # the abstraction's own claim (mapping.md §3): code 2 <-> the refusal
        if (code == 2) != _Operands.took_refusal:
            disagreements.append((code, p, q,
                                  "shadow path refusal=%s" % _Operands.took_refusal,
                                  "code table says code=%d" % code))
            return
        try:
            oracle = oracle_block(p, q)
        except Exception as e:
            disagreements.append((code, p, q, repr(shadow),
                                  "oracle raised %s: %s" % (type(e).__name__, e)))
            return
        checked += 1
        if strict_triple(shadow) != strict_triple(oracle):
            disagreements.append((code, p, q, repr(shadow), repr(oracle)))
            return
        if trace_insitu:
            traced = insitu_trace(p, q)
            if traced is None:
                insitu_unreached += 1
            else:
                insitu_quad, took_recovery = traced
                insitu_checked += 1
                if strict_triple(insitu_quad) != strict_triple(oracle):
                    disagreements.append(
                        (code, p, q, "in-situ %r" % (insitu_quad,),
                         "lifted-block oracle %r" % (oracle,)))
                    return
                # the patched recovery arm must be the arm the refusal takes,
                # observed inside the REAL function, not merely in the lift
                if took_recovery != (code == 2):
                    disagreements.append(
                        (code, p, q,
                         "real Mod.eval recovery arm taken=%s" % took_recovery,
                         "code table says code=%d (recovery iff code==2)" % code))
                    return
                if took_recovery:
                    insitu_recovered.append((p, q))

    for p, q in boundary:
        observe(p, q, trace_insitu=True)
        if len(disagreements) >= MAX_REPORT:
            break

    if len(disagreements) < MAX_REPORT:
        # consume the seeded stream until N_FUZZ in-domain comparisons are done
        # (an out-of-domain draw must not silently shrink the count below 1e5)
        for p, q in fuzz_pairs(rng):
            observe(p, q, trace_insitu=False)
            if len(disagreements) >= MAX_REPORT or checked >= N_FUZZ:
                break

    problems = f2p_end_to_end()

    if disagreements or problems:
        print("G-CONF FAIL: %d disagreement(s) over %d checked inputs"
              % (len(disagreements), checked))
        for code, p, q, sh, orc in disagreements:
            print("  code=%d p=%r q=%r\n      shadow=%s\n      oracle=%s"
                  % (code, p, q, sh, orc))
        for msg in problems:
            print("  F2P end-to-end regression: %s" % msg)
        print(json.dumps({
            "status": "fail", "instance": "sympy__sympy-21379",
            "backend": "nagini", "checked": checked,
            "disagreements": len(disagreements),
            "f2p_problems": problems, "seed": SEED}))
        return 1

    # ANTI-VACUITY. A generator that dodged the branch the gold patch changed
    # must not be able to report green, so every shape code and every impl
    # branch must carry a real share (>= 1%) of the checked inputs, and the F2P
    # shapes must be seen taking the patched recovery arm inside the REAL
    # Mod.eval — not merely inside the source-lift.
    floor = max(1, checked // 100)
    thin = ["branch:%s=%d" % (k, v) for k, v in branches.items() if v < floor]
    thin += ["code:%d=%d" % (c, v) for c, v in codes_seen.items() if v < floor]
    f2p_recovered = len(F2P_SHAPES & {srepr(p) for p, _q in insitu_recovered})
    if thin or checked < N_FUZZ or insitu_checked == 0 or f2p_recovered < 2:
        print("G-CONF FAIL: coverage insufficient — thin=%r checked=%d "
              "insitu=%d f2p_recovered_in_situ=%d/2 (floor=%d)"
              % (thin, checked, insitu_checked, f2p_recovered, floor))
        print(json.dumps({
            "status": "fail", "instance": "sympy__sympy-21379",
            "backend": "nagini", "reason": "coverage", "thin": thin,
            "checked": checked, "insitu_checked": insitu_checked,
            "f2p_recovered_in_situ": f2p_recovered, "seed": SEED}))
        return 1

    print("G-CONF OK: nagini impl-region shadow (verbatim, @ContractOnly callees "
          "bound to the real gcd/gcd_terms) agrees with the patched "
          "Mod.eval extract-gcd block on %d operand pairs "
          "(codes 0/1/2 = %d/%d/%d; branches transform/no-transform/refusal = "
          "%d/%d/%d; %d in-situ traced; %d out-of-domain skipped; seed=%d), "
          "0 disagreements."
          % (checked, codes_seen[0], codes_seen[1], codes_seen[2],
             branches["transform"], branches["no_transform"],
             branches["refusal"], insitu_checked, out_of_domain, SEED))
    print(json.dumps({
        "status": "pass", "instance": "sympy__sympy-21379", "backend": "nagini",
        "oracle": "sympy/core/mod.py Mod.eval 'extract gcd' block (patched), "
                  "source-lifted (all inputs) + in-situ traced (sample)",
        "shadow": "model.py impl-start/impl-end region, verbatim minus contracts",
        "checked": checked, "boundary": len(boundary),
        "codes": {str(k): v for k, v in codes_seen.items()},
        "branches": branches, "insitu_checked": insitu_checked,
        "insitu_unreached": insitu_unreached,
        "f2p_shapes_recovered_in_situ": "%d/2" % f2p_recovered,
        "out_of_domain": out_of_domain, "disagreements": 0, "seed": SEED}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
