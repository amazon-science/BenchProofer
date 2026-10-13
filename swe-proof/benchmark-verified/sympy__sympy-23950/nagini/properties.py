# properties.py — PBT falsification battery for sympy__sympy-23950.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-for-byte (only the impl region is swapped, enforced
# by markers.same_spec) and are checked by the Nagini verifier on the host. Axiom
# cases run the REAL sympy `Contains` callee in the instance Docker image.
#
# ---- The defended surface (read adversarially) -----------------------------
# solution_region(self: MembershipAssertion) -> Region models the gold change
#   Contains.as_set():  raise NotImplementedError()  ->  return self.args[1]
# Frozen contract:
#   Requires(Acc(self.element, 1/2))      # READ-ONLY inputs (directive 5):
#   Requires(Acc(self.region,  1/2))      #   half permission => may read, NOT write
#   Requires(MustTerminate(2))            # TOTAL correctness: the view MUST
#                                         #   terminate; a diverging body (self-
#                                         #   recursion / infinite loop) satisfies
#                                         #   the value postconditions only
#                                         #   vacuously and is rejected by the
#                                         #   obligation system.
#   Ensures (Acc(self.element, 1/2))
#   Ensures (Acc(self.region,  1/2))
#   Ensures (Result() is self.region)     # LOAD-BEARING: returns NORMALLY and the
#                                         #   returned object IS the region component
#                                         #   (the set operand args[1]) BY IDENTITY.
# Impl region (the only editable text):   return self.region
#
# The two F2P-observable wrong behaviours the spec must reject (problem
# statement + test_as_set):
#   (a) returning the ELEMENT (args[0]) instead of the set — `Contains(x,Reals)`
#       used to return itself / the wrong operand; the discriminator is
#       `Result() is self.region`, and self.element is a DISTINCT object not
#       provably identical to self.region, so an element-return cannot verify.
#   (b) DEFERRING (raise NotImplementedError) — the pre-patch body; the no-Exsures
#       spec forbids any raise, so a raising body cannot establish the normal
#       Result()-pin (= G-DIFF, model_prepatch.py).
#
# ungrounded-oracle echo: N/A here — the postcondition oracle `Result() is
#   self.region` is GROUNDED in the input (a direct identity selection of a
#   stored field, fully unfolded; no @Pure answer-key / opaque marker to echo).
#   There is no "wrong echo" to build; instead the soundness lane carries an
#   honest cheapest-correct positive control (see assessment).

from pathlib import Path

INSTANCE = "sympy__sympy-23950"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The unique impl-region text (verified unique below). We swap ONLY the body
# line, keeping the `# impl-end` marker as the right anchor so the edit is
# guaranteed to land inside # impl-start / # impl-end (same_spec preserved).
_IMPL = "    return self.region\n    # impl-end"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(body):
    """Build a full model.py whose impl region body is `body` (a string of
    one-or-more statements, each already indented 4 spaces), keeping # impl-end."""
    return _swap(_BASE, _IMPL, body + "\n    # impl-end")


SPEC_TESTS = [
    # ---- 5. POSITIVE CONTROL (soundness) --------------------------------------
    # Structurally different but CORRECT: bind the region component into a typed
    # local first, then return the local. Object identity is preserved
    # (r is self.region), so Result() is self.region still holds. If a faithful
    # correct impl in a different shape cannot verify => SPEC-TOO-STRONG.
    # (Region is in scope; the typed local uses the exact `# type: Region` form,
    #  attached to an assignment target — avoids the bare-return type-comment bug.)
    {
        "id": "pos-control-typed-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    r = self.region  # type: Region\n"
            "    return r"
        ),
        "rationale": "a structurally-different CORRECT impl (region bound to a "
                     "typed local, then returned — identity preserved) MUST "
                     "verify; if not, the postcondition is SPEC-TOO-STRONG.",
    },

    # ---- 6. ADMISSIBILITY -----------------------------------------------------
    # The precondition must ADMIT a normal F2P-shaped input: with only
    # Acc(self.region,1/2) / Acc(self.element,1/2) we must still be able to READ
    # both components and observe their identities. Reading both fields and
    # asserting the returned-region identity (the fact the postcondition needs)
    # exercises that the Requires is establishable for a normal assertion. If
    # this cannot verify, the precondition is PRECOND-TOO-STRONG.
    {
        "id": "admiss-read-both-fields",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    e = self.element  # type: Region\n"
            "    r = self.region   # type: Region\n"
            "    Assert(r is self.region)\n"
            "    return r"
        ),
        "rationale": "a normal in-domain assertion lets us READ both half-perm "
                     "components and pin the region identity; if the Requires "
                     "cannot be established for this F2P-shaped input it is "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- 1. FRAME-MUTATION (MANDATORY — read-only inputs) ---------------------
    # The inputs are held at Acc(...,1/2) (read-only). A rival tries to satisfy
    # the postcondition VACUOUSLY by OVERWRITING the region field with the
    # element, then returning it (Result() is self.region trivially after the
    # write). With only half permission this WRITE is illegal => must REJECT for
    # INSUFFICIENT PERMISSION. A byte-fuzzer never tries to mutate the input.
    {
        "id": "frame-mut-overwrite-region",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    self.region = self.element\n"
            "    return self.region"
        ),
        "refinement": "its faithful real patch would be `self.args[1] = "
                      "self.args[0]; return self.args[1]` — mutating the stored "
                      "set operand to the element. That makes as_set() return "
                      "the element (a non-Set boolean operand), so "
                      "test_as_set's `Contains(x,FiniteSet(y)).as_set() == "
                      "FiniteSet(y)` FAILS (it would equal x). It does NOT "
                      "resolve the F2P.",
        "rationale": "rejection comes from the PERMISSION system: writing "
                     "self.region needs full permission, but the Requires "
                     "grants only Acc(self.region,1/2) (read-only) — "
                     "insufficient permission, not the postcondition.",
    },

    # Frame-mutation variant: overwrite the ELEMENT field (also read-only). Even
    # though the return value is still self.region, writing the half-permission
    # element field is illegal => must REJECT for insufficient permission.
    {
        "id": "frame-mut-overwrite-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    self.element = self.region\n"
            "    return self.region"
        ),
        "refinement": "its faithful real patch would write to args[0] (the "
                      "element operand) before returning args[1]. sympy `Basic` "
                      "args are an immutable tuple; the real method neither can "
                      "nor does mutate operands — a patch that did would change "
                      "the assertion's element and is not the gold behaviour, so "
                      "it does not faithfully resolve the F2P.",
        "rationale": "rejection comes from the PERMISSION system: writing "
                     "self.element needs full permission but only "
                     "Acc(self.element,1/2) is held — insufficient permission.",
    },

    # ---- 3. PARTIAL-DOMAIN / wrong-component ----------------------------------
    # The single most natural wrong impl: return the ELEMENT operand instead of
    # the region. self.element and self.region are DISTINCT references the
    # verifier cannot prove identical, so Result() is self.region FAILS => must
    # REJECT. This is exactly behaviour (a) above — the bug in the issue.
    {
        "id": "wrong-component-return-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant("    return self.element"),
        "refinement": "its faithful real patch is `return self.args[0]` — "
                      "returning the asserted element x, not the set. "
                      "test_as_set asserts `Contains(x,FiniteSet(y)).as_set() == "
                      "FiniteSet(y)`, but args[0] is x (a Symbol), so it equals "
                      "x != FiniteSet(y): the F2P FAILS. (axiom_check.py confirms "
                      "args[0] is x is a DISTINCT object from args[1].)",
        "rationale": "rejection comes from the postcondition clause "
                     "`Result() is self.region`: self.element is a distinct, "
                     "not-provably-identical object reference.",
    },

    # ---- 4. CONTROL-FLOW-EFFECT (deferral / raise) ----------------------------
    # The pre-patch deferral: decline to produce the view by raising. The spec
    # has NO Exsures, so any raise is a verification failure (Nagini: 'method
    # raises no exceptions') and the normal-return Result()-pin is unreachable.
    # This is behaviour (b) above and exactly what model_prepatch.py reproduces
    # (G-DIFF). ViewNotProduced is defined in the frozen module (outside impl),
    # so referencing it keeps same_spec.
    {
        "id": "defer-raise-viewnotproduced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant("    raise ViewNotProduced()"),
        "refinement": "its faithful real patch keeps `raise "
                      "NotImplementedError()` (the pre-patch body the gold "
                      "change REMOVES). test_as_set then raises instead of "
                      "returning FiniteSet(y) — the F2P FAILS (this is the very "
                      "pre-patch state, and the old test even asserted the "
                      "raise). Does not resolve.",
        "rationale": "rejection comes from the no-Exsures spec + the normal "
                     "return obligation: an uncaught raise cannot establish "
                     "Result() is self.region (Nagini 'method raises no "
                     "exceptions').",
    },

    # Control-flow variant: NEVER return (infinite-defer surrogate). A body that
    # falls off the end without returning a Region cannot satisfy
    # Result() is self.region => reject. Supporting near-miss for the
    # return-vs-defer discrimination (the spec demands a NORMAL return of the
    # region).
    {
        "id": "no-return-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    e = self.element  # type: Region\n"
            "    Assert(e is self.element)"
        ),
        "refinement": "a faithful patch with no `return` (or `return None`) "
                      "leaves as_set() returning None, so "
                      "`Contains(x,FiniteSet(y)).as_set() == FiniteSet(y)` is "
                      "`None == FiniteSet(y)` => False: the F2P FAILS.",
        "rationale": "rejection comes from the normal-return Result()-pin: a "
                     "body that produces no Region result cannot establish "
                     "Result() is self.region.",
    },

    # ---- 2. VACUOUS NON-TERMINATION (uniqueness) ------------------------------
    # Self-recursion: `return solution_region(self)` — the exact G-PANEL-1 /
    # G-EQ attack (atk3_self_recursion). Every value postcondition is
    # "established" by the recursive call's own postcondition, but no execution
    # ever returns: the value spec alone is satisfied only vacuously. Under
    # Requires(MustTerminate(2)) a same-measure self-call cannot discharge the
    # caller's termination obligation, so Nagini's obligation system MUST
    # reject it ("Obligation leak check failed").
    {
        "id": "nonterm-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant("    return solution_region(self)"),
        "refinement": "its faithful real patch is `return self.as_set()` — "
                      "infinite recursion. test_as_set then hits "
                      "RecursionError instead of returning FiniteSet(y): the "
                      "F2P FAILS. (This is the recorded G-EQ counterexample "
                      "atk3_self_recursion.py.)",
        "rationale": "rejection comes from the termination obligation: "
                     "MustTerminate(2) gives the callee the same measure as "
                     "the caller, so the self-call leaks the obligation "
                     "(Nagini 'Obligation leak check failed'); the value "
                     "postconditions alone would be satisfied vacuously.",
    },

    # Non-termination variant: spin forever in a loop before the return. The
    # loop carries no MustTerminate invariant (and has no decreasing measure),
    # so it cannot take the caller's obligation => must REJECT ("Loop might
    # not take all unsatisfied obligations from the context").
    {
        "id": "nonterm-infinite-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    i = 0\n"
            "    while 0 <= i:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= i)\n"
            "        # invariants-end\n"
            "        i = i + 1\n"
            "    return self.region"
        ),
        "refinement": "its faithful real patch spins (`while True: pass`) "
                      "before returning — as_set() never returns, so "
                      "test_as_set hangs and the F2P FAILS.",
        "rationale": "rejection comes from the termination obligation: the "
                     "non-decreasing loop takes no MustTerminate invariant, "
                     "leaking the caller's MustTerminate(2) obligation.",
    },
]

# ----------------------------------------------------------------------------
# AXIOM lane. There is NO @ContractOnly axiom (axioms: []). The bundle's single
# trust point is the A-reference DEEP MODEL: `return self.region` <-> the real
# `Contains.as_set() is self.args[1]`, and the field bijection
# (self.region <-> args[1], self.element <-> args[0], distinct). PBT_PLAN §2.4 /
# §4: A-reference deep models are checked the same way as axioms — the deep
# model must equal the real callee on every caller-reachable input. We embed
# axiom_check.py's logic (read on the HOST at load time; the container mounts
# ONLY the probe script) and run the REAL sympy Contains in Docker on the gold
# tree. Files opened with encoding="utf-8" (ASCII-locale container).
# ----------------------------------------------------------------------------

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness: run the deep-model's real callee (Contains.as_set, post-gold)
# and assert it matches the deep model's encoded property on every operand pair
# in the F2P + adversarial-fuzz domain: as_set() IS args[1] AND == the input set,
# args[0] IS the element, and the two operands are DISTINCT. We reuse
# axiom_check.py verbatim (it already fuzzes boundaries / nested / Union / the
# three F2P sets and exits 0 iff the deep model holds), then add an explicit
# assertion that it observed the post-gold round trip on the F2P operands.
_PROBE_SOUNDNESS = (
    _AXIOM_CHECK_SRC
    + "\n\n"
    + "# ---- PBT axiom-soundness wrapper -------------------------------------\n"
      "import sys as _sys\n"
      "if __name__ == '__main__':\n"
      "    rc = main()\n"
      "    # main() already asserts the deep-model property on every operand\n"
      "    # pair; an explicit post-gold round-trip witness on the F2P operands\n"
      "    # so the probe is meaningless if as_set is NOT the gold body.\n"
      "    from sympy import Symbol, FiniteSet, S\n"
      "    from sympy.sets.contains import Contains\n"
      "    _x = Symbol('x'); _y = Symbol('y')\n"
      "    for _e, _s in [(_x, FiniteSet(_y)), (_x, S.Integers), (_x, S.Reals)]:\n"
      "        _c = Contains(_e, _s, evaluate=False)\n"
      "        _v = _c.as_set()\n"
      "        assert _v is _c.args[1], 'deep model unsound: as_set() is not args[1]'\n"
      "        assert _v == _s, 'deep model unsound: as_set() != the set operand'\n"
      "        assert _c.args[0] is _e, 'bijection unsound: args[0] is not x'\n"
      "        assert _c.args[0] is not _c.args[1], 'operands coincide'\n"
      "    print('PBT axiom-soundness OK: as_set() is args[1] == s on the 3 F2P operands')\n"
      "    _sys.exit(rc)\n"
)

# axiom-containment: every caller-reachable input the MODEL can abstract is a
# real Contains(x, s) whose stored operands are the two components the model
# carries (element <-> args[0], region <-> args[1]) and are distinct objects.
# The model NEVER reaches a Contains whose .args is not a 2-tuple of distinct
# stored operands (the constructor always stores exactly the two operands in
# order). We assert: across the F2P + adversarial operand space, every
# Contains(x,s) the model could abstract HAS a 2-element args with args[1] the
# stored set returned by identity — i.e. no reachable input falls OUTSIDE the
# deep model's assumed domain. A reachable Contains with args[1] not the stored
# set (or args not length-2) would be AXIOM-TOO-WEAK-FOR-CALLER.
_PROBE_CONTAINMENT = (
    "import sys\n"
    "from sympy import Symbol, FiniteSet, Interval, S\n"
    "from sympy.sets.contains import Contains\n"
    "\n"
    "x = Symbol('x'); y = Symbol('y'); z = Symbol('z')\n"
    "i = Symbol('i', integer=True)\n"
    "# The operand space the model can abstract (F2P + adversarial fuzz). The\n"
    "# model's Requires only assumes a MembershipAssertion with two object\n"
    "# components; every real Contains built from a (element, set) pair is such.\n"
    "cases = [\n"
    "    (x, FiniteSet(y)), (i, S.Integers), (x, S.Reals), (x, S.Integers),\n"
    "    (x, S.Naturals), (x, S.Rationals), (x, FiniteSet(y, z)),\n"
    "    (x, FiniteSet(1, 2, 3)), (x, Interval(0, 1)),\n"
    "    (x, Interval(-S.Infinity, S.Infinity)),\n"
    "    (x, FiniteSet(FiniteSet(y), z)), (x, FiniteSet(y) | FiniteSet(z)),\n"
    "]\n"
    "n = 0\n"
    "for elem, region in cases:\n"
    "    c = Contains(elem, region, evaluate=False)\n"
    "    # Containment: the model abstracts EXACTLY two stored components; the\n"
    "    # real Contains must expose exactly args[0] (element) and args[1]\n"
    "    # (the stored set), with args[1] the object as_set returns by identity.\n"
    "    assert len(c.args) == 2, (\n"
    "        'reachable input OUTSIDE model domain: Contains(%r,%r).args has %d '\n"
    "        'operands, model assumes exactly 2' % (elem, region, len(c.args)))\n"
    "    assert c.args[0] is elem, (\n"
    "        'reachable input OUTSIDE model domain: args[0] is not the element')\n"
    "    assert c.args[1] == region, (\n"
    "        'reachable input OUTSIDE model domain: args[1] is not the set operand')\n"
    "    assert c.args[0] is not c.args[1], (\n"
    "        'reachable input OUTSIDE model domain: the two components coincide')\n"
    "    n += 1\n"
    "print('PBT axiom-containment OK: every one of %d caller-reachable '\n"
    "      'Contains(x,s) inputs lies in the deep-model domain (2 distinct '\n"
    "      'stored operands; region=args[1])' % n)\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-as-set-is-args1",
        "axiom": "as_set-deep-model",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the deep model describes POST-GOLD as_set behaviour
        "probe": _PROBE_SOUNDNESS,
        "rationale": "the A-reference deep model `return self.region` claims the "
                     "real Contains.as_set() returns the STORED set operand "
                     "args[1] BY IDENTITY (== the input set), with args[0] the "
                     "distinct element. If the real callee disagrees on any F2P "
                     "or fuzz operand, the deep model is AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-contains-operand-domain",
        "axiom": "as_set-deep-model",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "every Contains(x,s) the model can abstract exposes exactly "
                     "two distinct stored operands with region=args[1]; a "
                     "reachable input whose args is not a 2-tuple of distinct "
                     "operands (or whose args[1] is not the set) would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER. None exists in the F2P+fuzz "
                     "operand space.",
    },
]
