#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14531 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. The
comparison is over BOTH observables the spec pins, because the operation under
spec changes both:

  * SHADOW  — Solution.lean's `pure` region, transliterated to Python over the
              real repo carrier. Each per-sub-object step is the A-reference
              `renderSub cfg reg sub`, left as the REAL `self._print` (the
              unchanged callee, out of scope for the R/I diff) OBSERVED AS A
              SINGLE STEP on a printer primed to the incoming registry, so the
              shadow really is the model's chained fold rather than a second
              spelling of the oracle's own loop:
                taggedPair     = tag + "(" + t_a + ", " + t_b + ")"
                taggedPairReg  = the registry after a's step then b's step
                limitTriple    = "Limit(" + t_e + ", " + t_z + ", " + t_z0 + ")"
                limitTripleReg = the registry after e's, z's and z0's steps
              where t_a is observed from the incoming registry, t_b from the
              registry a's step left, and so on. The two discriminating
              refinements (the fix) are that the step is taken by the SAME
              serializer as the composite — so its `cfg` settings reach the
              sub-objects AND its declaration registry is the one that advances —
              rather than by a throwaway default-settings `str(sub)`.
  * ORACLE  — `patch.diff`'s behaviour: the patched `StrPrinter._print_Relational`
              (charmap arm) and `StrPrinter._print_Limit` (dir == "+" arm), run
              in-process on the same expressions, the same printer settings, and
              the same primed registry. This is the actual Python the gold patch
              ships (the patch is applied to /testbed before this script runs).

TWO REALIZABLE SLICES. The declaration registry lives on `PythonPrinter`, which
REJECTS `sympy_integers`; `StrPrinter` accepts `sympy_integers` and carries no
registry (mapping.md §3.1, asserted in axiom_check.py). So each slice is
compared for what it can realize:

  A. TEXT slice — `StrPrinter` under BOTH settings (cfg=false and cfg=true):
     compare the assembled string. This is the leg `test_Rational` grades.
  B. EFFECT slice — `PythonPrinter` primed to a non-trivial incoming registry:
     compare the assembled string AND the registry the arm leaves behind. This
     is the leg `test_python_relational` grades, and it is what the second
     `ensures` of each method was added for.
  C. CALLER slice — end-to-end through `python(expr)` on a subset: the whole
     emitted program (declaration preamble in fold order, then `e = <expr>`)
     must equal what the shadow predicts. This closes the loop from the modeled
     registry to the observable the failing test actually reads.
  D. PROBE slice — the MATERIALIZATION RULE of mapping.md §2.2, which is the one
     part of the refinement map that is about an OPERATION rather than a value:
     an application of `renderSub` whose result is never written back to `reg`
     refines to one `self._print` on a PROBE primed to the active printer's
     settings and registry, discarded afterwards. An arm that takes such an extra
     observation (in both the dead shape and the branch-consumed `ite_self`
     shape — verdict.md's atk_1_extra_step_b and atk_1d_extra_branch) is compared
     against the GOLD arm on the assembled text, the registry, the declaration
     preamble, AND end-to-end through `python(expr)` with those arms actually
     installed on `StrPrinter`. Byte-identical everywhere is the claim, i.e. the
     shape the two `ensures` cannot exclude is one whose materialization is
     behaviourally gold (refinement.md §F).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

stdlib + sympy only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. Runs in-process; no DB, no network.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sympy import (Symbol, Rational, Integer, Function, Eq, Ne, Limit)  # noqa: E402
from sympy.printing.str import StrPrinter                               # noqa: E402
from sympy.printing.python import PythonPrinter, python                 # noqa: E402

SEED = 14531
N_FUZZ = 100_000
E2E_EVERY = 250          # caller-slice (slice C) sampling stride

NAMES = ['x', 'y', 'z', 'a', 'b', 'w']
FUNCS = ['f', 'g']


# --- the per-sub-object step (A-reference: the REAL self._print) -------------
def str_step(cfg, sub):
    """`renderSub cfg reg sub` on the TEXT slice: one step of a StrPrinter whose
    configuration is `cfg`. The registry is vacuous on this slice."""
    p = StrPrinter({'sympy_integers': True} if cfg else {})
    return p._print(sub)


def py_step(reg, sub):
    """`renderSub cfg reg sub` on the EFFECT slice: ONE step of a PythonPrinter
    primed to the incoming registry `reg`. Returns the model's PAIR — (text,
    registry afterwards) — both halves from the same call."""
    p = PythonPrinter()
    p.symbols, p.functions = list(reg[0]), list(reg[1])
    text = p._print(sub)
    return text, (tuple(p.symbols), tuple(p.functions))


def decl_text(reg):
    """The declaration preamble `python()` emits for registry `reg`: the modeled
    `List Char` registry. No fuzz name is a Python keyword, so no escaping."""
    return "".join(["%s = Symbol('%s')\n" % (s, s) for s in reg[0]] +
                   ["%s = Function('%s')\n" % (f, f) for f in reg[1]])


# --- SHADOW: Solution.lean's `pure` region, transliterated -------------------
def shadow_tagged_pair_text(cfg, tag, a, b):
    """taggedPair on the TEXT slice."""
    return '%s(%s, %s)' % (tag, str_step(cfg, a), str_step(cfg, b))


def shadow_limit_triple_text(cfg, e, z, z0):
    """limitTriple on the TEXT slice."""
    return "Limit(%s, %s, %s)" % (str_step(cfg, e), str_step(cfg, z),
                                  str_step(cfg, z0))


def shadow_tagged_pair(reg, tag, a, b):
    """(taggedPair, taggedPairReg) on the EFFECT slice: b's text is observed
    FROM the registry a's step left, and the out-registry is the fold."""
    t_a, r_a = py_step(reg, a)
    t_b, r_b = py_step(r_a, b)
    return '%s(%s, %s)' % (tag, t_a, t_b), r_b


def shadow_limit_triple(reg, e, z, z0):
    """(limitTriple, limitTripleReg) on the EFFECT slice."""
    t_e, r_e = py_step(reg, e)
    t_z, r_z = py_step(r_e, z)
    t_z0, r_z0 = py_step(r_z, z0)
    return "Limit(%s, %s, %s)" % (t_e, t_z, t_z0), r_z0


# --- ORACLE: patch.diff's behaviour, the real patched arms ------------------
_CHARMAP = {"==": "Eq", "!=": "Ne"}


def oracle_text(printer, expr, kind):
    """The patched arm, exercised directly on `printer`."""
    return (printer._print_Relational(expr) if kind == "rel"
            else printer._print_Limit(expr))


def oracle_effect(reg, expr, kind):
    """The patched arm on a PythonPrinter primed to `reg`: (text, registry)."""
    p = PythonPrinter()
    p.symbols, p.functions = list(reg[0]), list(reg[1])
    text = oracle_text(p, expr, kind)
    return text, (tuple(p.symbols), tuple(p.functions))


# --- slice D: the mapping.md §2.2 MATERIALIZATION RULE, end to end ----------
def probe_of(live):
    """A serializer carrying `live`'s configuration and a COPY of its registry.

    This is how mapping.md §2.2 rule (2) materializes an application
    `renderSub cfg reg sub` whose `.2` is never written back: the step is taken,
    the state it leaves is discarded. axiom_check.py check 10 asserts against the
    real callee that this returns the live step's text exactly and leaves the
    live registry untouched.
    """
    pr = live.__class__.__new__(live.__class__)
    pr.__dict__.update(live.__dict__)
    pr._settings = dict(live._settings)
    for attr in ('symbols', 'functions'):
        if hasattr(live, attr):
            setattr(pr, attr, list(getattr(live, attr)))
    return pr


def probe_relational(self, expr):
    """The gold charmap arm PLUS one extra UNCOMMITTED observation of the second
    sub-object, materialized per §2.2 rule (2). This is the refinement of the
    impl `let pre := renderSub cfg reg b; <gold two steps>` — the shape recorded
    in verdict.md as atk_1_extra_step_b, which refinement.md §F proves is the
    same program as gold."""
    charmap = {"==": "Eq", "!=": "Ne", ">": "Gt", "<": "Lt", ">=": "Ge",
               "<=": "Le"}
    if expr.rel_op in charmap:
        _pre = probe_of(self)._print(expr.rhs)        # observation, discarded
        return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
                               self._print(expr.rhs))
    return _GOLD_RELATIONAL(self, expr)


def probe_relational_branch(self, expr):
    """As above, but the observation's TEXT is genuinely consumed — as a branch
    condition over two identical assemblies (verdict.md atk_1d_extra_branch, the
    `ite_self` shape). Materializes to the same behaviour, which is the point."""
    charmap = {"==": "Eq", "!=": "Ne", ">": "Gt", "<": "Lt", ">=": "Ge",
               "<=": "Le"}
    if expr.rel_op in charmap:
        _pre = probe_of(self)._print(expr.rhs)
        if _pre == '':
            return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
                                   self._print(expr.rhs))
        else:
            return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
                                   self._print(expr.rhs))
    return _GOLD_RELATIONAL(self, expr)


_GOLD_RELATIONAL = StrPrinter._print_Relational


def probe_arm_effect(reg, expr, kind, tag, branch=False):
    """The materialized probe arm on a PythonPrinter primed to `reg`: the extra
    observation on a probe, then the arm's own steps live, in order."""
    p = PythonPrinter()
    p.symbols, p.functions = list(reg[0]), list(reg[1])
    if kind == "rel":
        pre = probe_of(p)._print(expr.rhs)
        if branch and pre == '':
            text = '%s(%s, %s)' % (tag, p._print(expr.lhs), p._print(expr.rhs))
        else:
            text = '%s(%s, %s)' % (tag, p._print(expr.lhs), p._print(expr.rhs))
    else:
        e, z, z0, _d = expr.args
        pre = probe_of(p)._print(z0)
        text = "Limit(%s, %s, %s)" % tuple(map(p._print, (e, z, z0)))
    return text, (tuple(p.symbols), tuple(p.functions))


def atoms(rng):
    """Sub-objects whose surface form depends on `sympy_integers`
    (rationals/integers) or not (symbols), plus registry-visible ones."""
    k = rng.randrange(8)
    if k in (0, 1):
        return Symbol(rng.choice(NAMES))
    if k == 2:
        return Rational(rng.randint(1, 99), rng.randint(1, 99))
    if k == 3:
        return Integer(rng.randint(-50, 50))
    if k == 4:
        return rng.choice([Rational(1, 2), Rational(2, 3), Rational(7, 2)])
    if k == 5:
        return Function(rng.choice(FUNCS))(Symbol(rng.choice(NAMES)))
    if k == 6:
        return Symbol(rng.choice(NAMES)) ** Rational(rng.randint(1, 9), 4)
    return Symbol(rng.choice(NAMES)) + Rational(rng.randint(1, 9), 4)


def fuzz_cases(n, rng):
    x = Symbol('x')
    # boundary cases first (plan §4.1 step 4): the two F2P witnesses, then the
    # registry-shaped ones (both sub-objects registry-visible, in both orders,
    # and the duplicate case the real registry collapses).
    yield ("rel", Eq(x, Rational(1, 2), evaluate=False))
    yield ("rel", Ne(x, Rational(2, 3), evaluate=False))
    yield ("rel", Eq(x, Rational(2, 3), evaluate=False))
    yield ("rel", Eq(Symbol('a'), Symbol('b'), evaluate=False))
    yield ("rel", Eq(Symbol('b'), Symbol('a'), evaluate=False))
    yield ("rel", Eq(x, x, evaluate=False))
    yield ("rel", Eq(Function('f')(x), Symbol('y'), evaluate=False))
    yield ("lim", Limit(x, x, Rational(7, 2)))
    yield ("lim", Limit(x, x, Rational(1, 2)))
    yield ("lim", Limit(Symbol('e'), x, Integer(0)))
    yield ("lim", Limit(Symbol('y'), Symbol('y'), Symbol('a')))
    for _ in range(n):
        if rng.random() < 0.5:
            yield ("rel", rng.choice([Eq, Ne])(atoms(rng), atoms(rng),
                                               evaluate=False))
        else:
            yield ("lim", Limit(atoms(rng), Symbol(rng.choice(NAMES)),
                                atoms(rng)))


def main():
    rng = random.Random(SEED)
    text_printers = [(False, StrPrinter()),
                     (True, StrPrinter({'sympy_integers': True}))]
    fails = 0
    checked = 0
    e2e = 0
    probes = 0

    def disagree(msg):
        nonlocal fails
        fails += 1
        if fails <= 10:
            print(msg, file=sys.stderr)

    for i, (kind, expr) in enumerate(fuzz_cases(N_FUZZ, rng)):
        if kind == "rel":
            if expr.rel_op not in _CHARMAP:
                continue          # only the charmap arm is modeled (mapping.md §1)
            tag = _CHARMAP[expr.rel_op]
            subs = (expr.lhs, expr.rhs)
        else:
            e, z, z0, _dir = expr.args
            if str(_dir) != "+":
                continue          # only the dir == "+" arm is modeled
            subs = (e, z, z0)

        # ---- slice A: TEXT, both configurations -------------------------
        for cfg, printer in text_printers:
            shadow = (shadow_tagged_pair_text(cfg, tag, *subs) if kind == "rel"
                      else shadow_limit_triple_text(cfg, *subs))
            oracle = oracle_text(printer, expr, kind)
            checked += 1
            if shadow != oracle:
                disagree(f"DISAGREE-TEXT [{kind}] cfg={cfg} expr={expr!r} "
                         f"shadow={shadow!r} oracle={oracle!r}")

        # ---- slice B: TEXT + REGISTRY, primed incoming registry ----------
        reg = (tuple(rng.sample(NAMES, rng.randrange(len(NAMES) + 1))),
               tuple(rng.sample(FUNCS, rng.randrange(len(FUNCS) + 1))))
        s_txt, s_reg = (shadow_tagged_pair(reg, tag, *subs) if kind == "rel"
                        else shadow_limit_triple(reg, *subs))
        o_txt, o_reg = oracle_effect(reg, expr, kind)
        checked += 1
        if s_txt != o_txt:
            disagree(f"DISAGREE-TEXT/eff [{kind}] reg={reg!r} expr={expr!r} "
                     f"shadow={s_txt!r} oracle={o_txt!r}")
        if s_reg != o_reg:
            disagree(f"DISAGREE-REGISTRY [{kind}] reg={reg!r} expr={expr!r} "
                     f"shadow={s_reg!r} oracle={o_reg!r}")
        if decl_text(s_reg) != decl_text(o_reg):
            disagree(f"DISAGREE-DECLTEXT [{kind}] reg={reg!r} expr={expr!r}")

        # ---- slice D: the §2.2 materialization rule for an UNCOMMITTED
        # ---- observation. The arm takes ONE EXTRA step on a primed PROBE and
        # ---- then the steps it commits, live. Per the rule this must be
        # ---- behaviourally the GOLD arm: same text, same registry, same
        # ---- declaration preamble. (refinement.md §F — the executable half of
        # ---- the claim that a discarded step is invisible in the behaviour and
        # ---- not merely invisible in the two `ensures`.)
        for branch in (False, True) if kind == "rel" else (False,):
            d_txt, d_reg = probe_arm_effect(reg, expr, kind, tag if kind == "rel"
                                            else None, branch=branch)
            checked += 1
            if d_txt != o_txt:
                disagree(f"DISAGREE-PROBE-TEXT [{kind}] branch={branch} "
                         f"reg={reg!r} expr={expr!r} probe-arm={d_txt!r} "
                         f"oracle={o_txt!r}")
            if d_reg != o_reg or decl_text(d_reg) != decl_text(o_reg):
                disagree(f"DISAGREE-PROBE-REGISTRY [{kind}] branch={branch} "
                         f"reg={reg!r} expr={expr!r} probe-arm={d_reg!r} "
                         f"oracle={o_reg!r}")

        # ---- slice C: end to end through the caller ----------------------
        if i % E2E_EVERY == 0:
            s_txt0, s_reg0 = (shadow_tagged_pair(((), ()), tag, *subs)
                              if kind == "rel"
                              else shadow_limit_triple(((), ()), *subs))
            want = decl_text(s_reg0) + 'e = ' + s_txt0
            got = python(expr)
            e2e += 1
            checked += 1
            if want != got:
                disagree(f"DISAGREE-CALLER [{kind}] expr={expr!r} "
                         f"shadow={want!r} python()={got!r}")
            # slice D, end to end: install the materialized probe arms and read
            # the WHOLE emitted program the F2P test grades. Byte-identical to
            # gold's or the materialization rule is unsound.
            if kind == "rel":
                for fn, label in ((probe_relational, "probe"),
                                  (probe_relational_branch, "probe-branch")):
                    StrPrinter._print_Relational = fn
                    try:
                        got_d = python(expr)
                    finally:
                        StrPrinter._print_Relational = _GOLD_RELATIONAL
                    probes += 1
                    checked += 1
                    if got_d != got:
                        disagree(f"DISAGREE-PROBE-CALLER [{label}] expr={expr!r} "
                                 f"gold={got!r} materialized={got_d!r}")

    if fails:
        print(f"G-CONF FAIL: {fails} disagreement(s) over {checked} "
              f"comparisons (seed {SEED}).", file=sys.stderr)
        return 1
    print(f"G-CONF PASS: {checked} comparisons, 0 disagreements (seed {SEED}). "
          f"_print_Relational (charmap arm) + _print_Limit (dir==+ arm) on both "
          f"realizable slices: sub-objects rendered under the printer's OWN "
          f"settings (text slice, both configurations) and by the printer whose "
          f"OWN declaration registry advances, left to right (effect slice, "
          f"primed registries; text, registry and emitted declaration preamble "
          f"all compared), plus {e2e} end-to-end python() programs. Slice D "
          f"(mapping.md 2.2): the materialization of an UNCOMMITTED observation "
          f"-- one extra step on a primed probe, discarded, in both the dead and "
          f"the branch-consumed shape -- agrees with the gold arm on text, "
          f"registry and preamble everywhere, and on {probes} end-to-end python() "
          f"programs emitted with those arms installed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
