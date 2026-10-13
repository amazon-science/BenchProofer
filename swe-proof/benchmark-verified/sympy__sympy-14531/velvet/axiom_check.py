#!/usr/bin/env python3
"""G-AX soundness check for sympy__sympy-14531 (plan §4, SPEC_GUIDE §0.7).

The only modeled callee is the A-reference `renderSub` (Solution.lean), the
opaque per-sub-object rendering STEP of the active serializer, standing for
`self._print(sub)` on the printer serializing the composite — the UNCHANGED
settings-and-state-aware sub-dispatch. The spec models one step as

    renderSub : Bool -> List Char -> SubObj -> (List Char x List Char)

i.e. as a FUNCTION from (configuration, incoming declaration registry,
sub-object) to the PAIR (text the sub-object renders to, registry the serializer
carries afterwards). This script runs the REAL callee in the instance image (at
base_commit, UNPATCHED) and asserts exactly the properties that modeling makes
the spec rely on, plus the two OBSERVABILITY facts that make the spec's two
`ensures` clauses non-vacuous.

TWO REALIZABLE SLICES (why the legs are validated on different printers). The
registry the caller emits ahead of the composite lives on `PythonPrinter`
(`self.symbols` / `self.functions`, appended to by `_print_Symbol` /
`_print_Function`), and `PythonPrinter._default_settings` is `{'order': None}` —
it REJECTS `sympy_integers` with `TypeError: Unknown setting`. `StrPrinter`
accepts `sympy_integers` but carries no declaration registry at all. So the
model's product domain (cfg x reg) is not realizable in one printer object: the
`cfg` leg is realizable only on the StrPrinter slice (registry always empty) and
the `reg` leg only on the PythonPrinter slice (configuration at its default).
Both slices are validated separately below, and the non-realizability itself is
asserted rather than assumed (mapping.md §3.1). Modeling them as one step with
both parameters is a SOUND over-approximation: `renderSub` asserts nothing
whatsoever about either component (no `axiom`, no `ensures`), so every
real-callee behaviour on either slice is an instance of it.

  (1) STEP DETERMINISM — one step is a FUNCTION of (cfg, reg, sub): two
      independently primed printers carrying the SAME registry render the same
      sub-object to the same text AND leave the same registry. Checked on both
      slices. (An opaque Lean function is deterministic; if the real step were
      not a function of these three, the model would be unsound. Note this is
      NOT the same as calling `_print` twice on one printer — the first call
      mutates the registry — which is why every probe primes fresh printers.)

  (2) HISTORY COLLAPSE — the step's result depends on the registry's VALUE, not
      on the sequence of steps that produced it: a printer primed by replaying a
      different step sequence that lands on the same registry gives the same
      pair. This is what licenses `List Char` (a value) as the modeled state.

  (3) THE MODELED CARRIER LOSES NOTHING — the declaration TEXT the caller emits
      is an INJECTIVE function of the real registry state (symbols, functions)
      over the fuzz corpus, so collapsing that pair of lists into the single
      `List Char` registry of the model is faithful.

  (4) REGISTRY EFFECT IS OBSERVABLE — there exist (reg, sub) with
      `(renderSub cfg reg sub).2 != reg`, and the effect REACHES THE CALLER'S
      OUTPUT: `python(expr)` emits the registry ahead of the expression. This is
      what makes the second `ensures` of each method (`reg = ...Reg ...`)
      non-vacuous.

  (5) STEP ORDER IS OBSERVABLE — for two distinct sub-objects, stepping b then a
      leaves a DIFFERENT registry (and a different emitted declaration text)
      than stepping a then b. This is the crux fact behind the second `ensures`,
      and it is what the F2P test `test_python_relational` grades:
      `python(Eq(x, y)) == "x = Symbol('x')\\ny = Symbol('y')\\ne = Eq(x, y)"`
      pins the two declarations in ARGUMENT order.

  (6) IDEMPOTENCE IS REAL BUT NOT ASSUMED — the real registry DEDUPLICATES
      (`if symbol not in self.symbols`), so stepping the same sub-object twice
      leaves the same registry as stepping it once. Recorded here because it is
      the measured reason a duplicated-step rival's real counterpart still
      resolves (verdict.md, atk_4_dup_render resolved=True). The model does NOT
      assume it — an opaque step is a function of its incoming registry and
      nothing more — so the model is WEAKER than the real callee here, which is
      the sound direction.

  (7) THROWAWAY-SERIALIZER FACTS — a fresh serializer's registry starts EMPTY,
      and steps taken on it leave another serializer's registry untouched. This
      is the mechanism of the measured `xtra_fresh_printer` break: the returned
      text is right and the declarations never reach the output.

  (8) COMPOSITIONALITY OF THE FOLD — for both modeled arms, the (text, registry)
      produced by taking the steps IN SEQUENCE on ONE printer equals the CHAINED
      COMPOSITION of single steps observed on independently primed printers.
      This is the exact shape of `taggedPair` / `taggedPairReg` / `limitTriple` /
      `limitTripleReg`: each segment is the text produced FROM the registry the
      previous steps left, and the out-registry is the left-to-right fold. It
      replaces this file's previous check (3), which compared a string to itself
      and could not fail.

  (9) CONFIGURATION IS OBSERVABLE — StrPrinter slice, with the F2P witnesses:
      `_print(Rational(2,3))` is `S(2)/3` under `sympy_integers=True` and `2/3`
      by default (likewise 7/2, 1/2). This is what makes the modeled `cfg`
      distinction non-vacuous and `Solution_prepatch.lean` genuinely fail, and
      it is what the F2P test `test_Rational` grades
      (`sstr(Eq(x, Rational(2, 3)), sympy_integers=True) == "Eq(x, S(2)/3)"`,
      `sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) ==
      "Limit(x, x, S(7)/2)"`).

 (10) THE MATERIALIZATION RULE IS SOUND (mapping.md §2.2) — an application of
      `renderSub` whose result is never written back to `reg` refines to one
      `self._print` on a PROBE primed to the active printer's settings and
      registry. Asserted: the probe returns EXACTLY the text the live call would
      return from the same state, it lands in exactly the state a live step
      would, and it leaves the LIVE printer's `(symbols, functions)` untouched —
      on the PythonPrinter slice over the fuzz corpus, and on the StrPrinter
      slice for the configuration leg. This is what makes an uncommitted
      observation refinable to real, effect-free code, and it is the check that
      keeps the second `ensures` an assertion about the steps the composite
      COMMITS rather than an unfalsifiable claim about call multiplicity
      (refinement.md §F).

Imports only `sympy` (stdlib). Exit 0 iff every observation is sound.
NOTE: this runs at base_commit (PRE-patch), which is correct for an A-reference:
`self._print` and the caller's registry emission are the UNCHANGED parts of the
system. The patch changes only WHICH serializer the two composite arms route
their sub-objects through — the active one, whose configuration and registry are
both in play, instead of a throwaway one — and never the step itself. No
post-patch behaviour is asserted here (that is conformance_check.py / G-CONF).
"""
import keyword
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sympy import (Symbol, Rational, Integer, Function, Eq, Limit,  # noqa: E402
                   sin, cos, exp)
from sympy.printing.str import StrPrinter                           # noqa: E402
from sympy.printing.python import PythonPrinter, python             # noqa: E402

SEED = 14531
N_STEP = 20_000     # step-determinism probes, per slice
N_COMP = 5_000      # compositionality probes, per modeled arm

NAMES = ['x', 'y', 'z', 'alpha', 'theta', 'phi', 'a', 'b', 'n', 'w']
FUNCS = ['f', 'g', 'h']


def sub_atoms(rng):
    """A sub-object a composite arm might route through one step."""
    k = rng.randrange(7)
    if k == 0:
        return Symbol(rng.choice(NAMES))
    if k == 1:
        return Rational(rng.randint(1, 999), rng.randint(1, 999))
    if k == 2:
        return Integer(rng.randint(-100, 100))
    if k == 3:
        return Symbol(rng.choice(NAMES)) ** Rational(rng.randint(1, 9),
                                                     rng.randint(1, 9))
    if k == 4:
        return Function(rng.choice(FUNCS))(Symbol(rng.choice(NAMES)))
    if k == 5:
        return rng.choice([sin, cos, exp])(Symbol(rng.choice(NAMES)))
    return Symbol(rng.choice(NAMES)) + Rational(rng.randint(1, 9), 4)


def primed(regs, regf):
    """A PythonPrinter whose declaration registry IS (regs, regf).

    This is the model's `reg` parameter, materialized: the caller's serializer
    at the moment it reaches the composite.
    """
    p = PythonPrinter()
    p.symbols = list(regs)
    p.functions = list(regf)
    return p


def reg_of(p):
    """The real registry state of a PythonPrinter, as a value."""
    return (tuple(p.symbols), tuple(p.functions))


def decl_text(p):
    """The declaration preamble `python()` emits ahead of the expression.

    This is the modeled `List Char` registry. `python()` escapes names that are
    Python keywords; the fuzz corpus contains none (asserted), so the plain form
    below is exactly what the caller emits.
    """
    return "".join(["%s = Symbol('%s')\n" % (s, s) for s in p.symbols] +
                   ["%s = Function('%s')\n" % (f, f) for f in p.functions])


def step(regs, regf, sub):
    """ONE real step: `renderSub <default cfg> (regs, regf) sub`.

    Returns the PAIR the model returns: (text, registry afterwards). Both halves
    come from the SAME call, which is the model's `.1` / `.2` of one `renderSub`.
    """
    p = primed(regs, regf)
    text = p._print(sub)
    return text, reg_of(p)


def main():
    rng = random.Random(SEED)
    fails = 0

    def bad(msg):
        nonlocal fails
        fails += 1
        print(msg, file=sys.stderr)

    # ---- (0) the two realizable slices are what the docstring says ----------
    if any(kw in NAMES + FUNCS for kw in map(str, keyword.kwlist)):
        bad("FUZZ CORPUS uses a Python keyword; decl_text() would diverge from "
            "python()'s escaping")
    try:
        PythonPrinter({'sympy_integers': True})
        bad("SLICE CLAIM WRONG: PythonPrinter accepted sympy_integers, so the "
            "cfg and reg legs would be jointly realizable and mapping.md §3.1 "
            "understates what could be validated")
    except TypeError:
        pass
    if hasattr(StrPrinter(), 'symbols'):
        bad("SLICE CLAIM WRONG: StrPrinter carries a declaration registry")
    if reg_of(PythonPrinter()) != ((), ()):
        bad("a fresh PythonPrinter does not start with an EMPTY registry")

    p_def = StrPrinter()                              # cfg = false
    p_int = StrPrinter({'sympy_integers': True})      # cfg = true

    # ---- (1) step determinism, both slices ---------------------------------
    for _ in range(N_STEP):
        sub = sub_atoms(rng)
        # StrPrinter slice: text is a function of (cfg, sub); fresh printers.
        for cfg, settings in ((False, {}), (True, {'sympy_integers': True})):
            t1 = StrPrinter(dict(settings))._print(sub)
            t2 = StrPrinter(dict(settings))._print(sub)
            if t1 != t2:
                bad(f"NONDETERMINISM (StrPrinter slice, cfg={cfg}): {sub!r} "
                    f"{t1!r} vs {t2!r}")
        # PythonPrinter slice: the PAIR is a function of (reg, sub).
        regs = tuple(rng.sample(NAMES, rng.randrange(len(NAMES) + 1)))
        regf = tuple(rng.sample(FUNCS, rng.randrange(len(FUNCS) + 1)))
        r1 = step(regs, regf, sub)
        r2 = step(regs, regf, sub)
        if r1 != r2:
            bad(f"NONDETERMINISM (PythonPrinter slice): sub={sub!r} "
                f"reg=({regs},{regf}) {r1!r} vs {r2!r}")

    # ---- (2) history collapse: the state is the VALUE, not the path ---------
    for _ in range(N_STEP // 4):
        subs = [Symbol(n) for n in rng.sample(NAMES, rng.randrange(1, 5))]
        sub = sub_atoms(rng)
        # reach a registry by REPLAYING steps ...
        p_replay = PythonPrinter()
        for s in subs:
            p_replay._print(s)
        reached = reg_of(p_replay)
        # ... and by ASSIGNING the same value directly.
        via_replay_text = p_replay._print(sub)
        via_replay_reg = reg_of(p_replay)
        direct = step(reached[0], reached[1], sub)
        if (via_replay_text, via_replay_reg) != direct:
            bad(f"HISTORY LEAK: step after replay {reached!r} differs from step "
                f"from the same registry assigned directly: "
                f"{(via_replay_text, via_replay_reg)!r} vs {direct!r}")

    # ---- (3) the modeled carrier is injective on the real state ------------
    seen = {}
    for _ in range(N_STEP // 4):
        regs = tuple(rng.sample(NAMES, rng.randrange(len(NAMES) + 1)))
        regf = tuple(rng.sample(FUNCS, rng.randrange(len(FUNCS) + 1)))
        txt = decl_text(primed(regs, regf))
        prev = seen.setdefault(txt, (regs, regf))
        if prev != (regs, regf):
            bad(f"CARRIER COLLISION: distinct registry states {prev!r} and "
                f"{(regs, regf)!r} emit the same declaration text {txt!r}, so "
                f"the modeled List Char registry would lose information")

    # ---- (4) the registry effect is observable, and reaches the output -----
    x, y = Symbol('x'), Symbol('y')
    t, after = step((), (), x)
    if after == ((), ()):
        bad("REGISTRY EFFECT NOT OBSERVABLE: stepping a symbol left the registry "
            "unchanged — the second `ensures` of each method would be vacuous")
    if after != (('x',), ()):
        bad(f"unexpected registry after one symbol step: {after!r}")
    if t != 'x':
        bad(f"unexpected text for a symbol step: {t!r}")
    # the caller emits the registry ahead of the expression:
    if python(x**2) != "x = Symbol('x')\ne = x**2":
        bad(f"CALLER DOES NOT EMIT THE REGISTRY: python(x**2) = {python(x**2)!r}")

    # ---- (5) step ORDER is observable -------------------------------------
    _, ord_xy = None, None
    p_xy = PythonPrinter(); p_xy._print(x); p_xy._print(y)
    p_yx = PythonPrinter(); p_yx._print(y); p_yx._print(x)
    if reg_of(p_xy) == reg_of(p_yx):
        bad("STEP ORDER NOT OBSERVABLE: stepping x,y and y,x left the same "
            "registry — the ordered fold the second `ensures` pins would be "
            "unfalsifiable")
    if decl_text(p_xy) != "x = Symbol('x')\ny = Symbol('y')\n":
        bad(f"declaration text is not append-ordered: {decl_text(p_xy)!r}")
    if decl_text(p_yx) != "y = Symbol('y')\nx = Symbol('x')\n":
        bad(f"declaration text is not append-ordered: {decl_text(p_yx)!r}")
    # and the ORDER reaches the caller's output, which is what F2P grades:
    got = python(Eq(y, x))
    if not got.startswith("y = Symbol('y')\nx = Symbol('x')\n"):
        # pre-patch the charmap arm registers NOTHING, so `python(Eq(...))` has
        # no preamble at all; the order fact is then carried by the arm that
        # does dispatch through `self._print` (Ge/Le/Gt/Lt), which is unchanged.
        from sympy import Ge
        got2 = python(Ge(y, x))
        if not got2.startswith("y = Symbol('y')\nx = Symbol('x')\n"):
            bad(f"ORDER DOES NOT REACH THE OUTPUT: python(Ge(y, x)) = {got2!r}")

    # ---- (6) idempotence is real (recorded), and NOT assumed by the model --
    p_once = PythonPrinter(); p_once._print(x)
    p_twice = PythonPrinter(); p_twice._print(x); p_twice._print(x)
    if reg_of(p_once) != reg_of(p_twice):
        bad("RECORDED FACT WRONG: the real registry does not deduplicate, so "
            "verdict.md's explanation of atk_4_dup_render resolving is wrong")

    # ---- (7) throwaway-serializer facts -----------------------------------
    p_live = primed(('w',), ())
    p_throw = PythonPrinter()
    p_throw._print(x); p_throw._print(y)
    if reg_of(p_live) != (('w',), ()):
        bad("a step on a throwaway serializer mutated the live serializer's "
            "registry")
    if reg_of(p_throw) != (('x', 'y'), ()):
        bad(f"throwaway serializer registry unexpected: {reg_of(p_throw)!r}")

    # ---- (8) compositionality of the fold, both modeled arms ---------------
    # The real thing: take the steps in sequence on ONE primed printer, exactly
    # as the patched arm does. The model: chain independently observed single
    # steps. These must agree on BOTH the assembled text and the out-registry.
    for _ in range(N_COMP):
        regs = tuple(rng.sample(NAMES, rng.randrange(len(NAMES) + 1)))
        regf = tuple(rng.sample(FUNCS, rng.randrange(len(FUNCS) + 1)))
        a, b, c = sub_atoms(rng), sub_atoms(rng), sub_atoms(rng)

        # ---- binary arm: '%s(%s, %s)' % (tag, self._print(a), self._print(b))
        p = primed(regs, regf)
        real_txt = '%s(%s, %s)' % ('Eq', p._print(a), p._print(b))
        real_reg = reg_of(p)
        ta, r_a = step(regs, regf, a)               # renderSub cfg reg a
        tb, r_b = step(r_a[0], r_a[1], b)           # renderSub cfg (reg after a) b
        model_txt = 'Eq' + '(' + ta + ', ' + tb + ')'      # taggedPair
        model_reg = r_b                                     # taggedPairReg
        if real_txt != model_txt:
            bad(f"ASSEMBLY INFIDELITY (binary): real {real_txt!r} != model "
                f"{model_txt!r} at reg=({regs},{regf}) a={a!r} b={b!r}")
        if real_reg != model_reg:
            bad(f"FOLD INFIDELITY (binary): real {real_reg!r} != model "
                f"{model_reg!r} at reg=({regs},{regf}) a={a!r} b={b!r}")

        # ---- ternary arm: "Limit(%s, %s, %s)" % tuple(map(self._print, ...))
        p = primed(regs, regf)
        real_txt = "Limit(%s, %s, %s)" % tuple(map(p._print, (a, b, c)))
        real_reg = reg_of(p)
        te, r_e = step(regs, regf, a)
        tz, r_z = step(r_e[0], r_e[1], b)
        tz0, r_z0 = step(r_z[0], r_z[1], c)
        model_txt = 'Limit(' + te + ', ' + tz + ', ' + tz0 + ')'   # limitTriple
        model_reg = r_z0                                      # limitTripleReg
        if real_txt != model_txt:
            bad(f"ASSEMBLY INFIDELITY (ternary): real {real_txt!r} != model "
                f"{model_txt!r} at reg=({regs},{regf})")
        if real_reg != model_reg:
            bad(f"FOLD INFIDELITY (ternary): real {real_reg!r} != model "
                f"{model_reg!r} at reg=({regs},{regf})")
        # `map` over a tuple is forced left to right, which is WHY the fold is
        # in argument order; assert the direction rather than assuming it.
        p2 = primed(regs, regf)
        seq = [p2._print(s) for s in (a, b, c)]
        if seq != [te, tz, tz0] or reg_of(p2) != r_z0:
            bad("TERNARY STEP ORDER: tuple(map(self._print, (e, z, z0))) is not "
                "the left-to-right fold")

    # ---- (9) configuration is observable (StrPrinter slice, F2P witnesses) --
    observed = False
    for w, aware_want, blind_want in ((Rational(2, 3), 'S(2)/3', '2/3'),
                                      (Rational(7, 2), 'S(7)/2', '7/2'),
                                      (Rational(1, 2), 'S(1)/2', '1/2')):
        aware = p_int._print(w)        # renderSub true
        blind = p_def._print(w)        # renderSub false
        if aware != aware_want:
            bad(f"witness {aware_want} wrong: {aware!r}")
        if blind != blind_want:
            bad(f"witness {blind_want} wrong: {blind!r}")
        if str(w) != blind:
            bad(f"DEFAULT-PRINTER MISMATCH str() vs _print(): {w!r}")
        if aware != blind:
            observed = True
    if not observed:
        bad("CONFIG NOT OBSERVABLE: no witness diverged between settings — the "
            "modeled cfg distinction would be vacuous")

    # ---- (10) the MATERIALIZATION RULE of mapping.md §2.2 ------------------
    # An application `renderSub cfg reg s` whose `.2` is never written back is an
    # OBSERVATION, and it refines to `self._print(s)` on a PROBE primed to the
    # active printer's settings and a COPY of its registry. Two obligations make
    # that refinement sound, and both are asserted here against the real callee:
    #   (a) the probe returns EXACTLY the text the live call would return from the
    #       same state, so the observation's `.1` is faithful;
    #   (b) the probe leaves the LIVE printer's registry untouched, so the absent
    #       write-back is faithful (the model's `reg` really does not advance).
    # Without (a) an uncommitted observation would be unrefinable; without (b) it
    # would refine to something with an effect the model does not have.
    def probe_of(live):
        """A serializer carrying `live`'s configuration and registry VALUE."""
        pr = live.__class__.__new__(live.__class__)
        pr.__dict__.update(live.__dict__)
        pr._settings = dict(live._settings)
        for attr in ('symbols', 'functions'):
            if hasattr(live, attr):
                setattr(pr, attr, list(getattr(live, attr)))
        return pr

    for _ in range(N_STEP // 4):
        regs = tuple(rng.sample(NAMES, rng.randrange(len(NAMES) + 1)))
        regf = tuple(rng.sample(FUNCS, rng.randrange(len(FUNCS) + 1)))
        sub = sub_atoms(rng)
        live = primed(regs, regf)
        pr = probe_of(live)
        t_probe = pr._print(sub)
        t_live, r_live = step(regs, regf, sub)          # what a live call gives
        if t_probe != t_live:
            bad(f"PROBE TEXT INFIDELITY: a primed probe rendered {sub!r} as "
                f"{t_probe!r} where the live call gives {t_live!r} at "
                f"reg=({regs},{regf}) — mapping.md §2.2 rule (2) would be unsound")
        if reg_of(live) != (regs, regf):
            bad(f"PROBE LEAKED AN EFFECT: the live printer's registry moved from "
                f"{(regs, regf)!r} to {reg_of(live)!r} while only the probe "
                f"stepped — an uncommitted observation would not be effect-free")
        if reg_of(pr) != r_live:
            bad(f"PROBE STATE INFIDELITY: probe left {reg_of(pr)!r}, a live step "
                f"leaves {r_live!r} — the probe is not the same step")
        # the CONTRAST that makes rule (1) different from rule (2): the same step
        # taken live DOES advance the printer the caller reads.
        if r_live != (regs, regf) and reg_of(live) == r_live:
            bad("live/probe distinction collapsed")
    # the cfg leg of the rule, on the StrPrinter slice (§2.1): a probe must carry
    # the active CONFIGURATION, not a default one.
    for settings in ({}, {'sympy_integers': True}):
        live = StrPrinter(dict(settings))
        for _ in range(200):
            sub = sub_atoms(rng)
            if probe_of(live)._print(sub) != StrPrinter(dict(settings))._print(sub):
                bad(f"PROBE DROPPED THE CONFIGURATION at settings={settings!r}, "
                    f"sub={sub!r}")

    if fails:
        print(f"G-AX FAIL: {fails} unsound observation(s) (seed {SEED}).",
              file=sys.stderr)
        return 1
    print(f"G-AX PASS: renderSub == one real `self._print` step on both "
          f"realizable slices (seed {SEED}). Deterministic as a function of "
          f"(cfg, reg, sub) and history-collapsing over {N_STEP} fuzzed steps "
          f"per slice; the modeled List Char registry is injective on the real "
          f"(symbols, functions) state; the registry effect and the STEP ORDER "
          f"are both observable and both reach the caller's output; the real "
          f"registry deduplicates (recorded, NOT assumed by the model); a "
          f"throwaway serializer starts empty and leaves the live registry "
          f"untouched; taggedPair/taggedPairReg and limitTriple/limitTripleReg "
          f"are exactly the real arms' sequenced steps over {N_COMP} fuzzed "
          f"(registry, sub-object) tuples per arm; configuration observable "
          f"(S(2)/3 vs 2/3, S(7)/2 vs 7/2); and the mapping.md §2.2 "
          f"materialization rule holds — a probe primed to the active printer's "
          f"settings and registry returns the live step's text exactly and leaves "
          f"the live registry untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
