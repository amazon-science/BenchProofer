"""properties.py — PBT falsification battery for django__django-11603.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Each SPEC_TEST is a FULL model.py variant built
by region-surgery (editing ONLY text inside an # impl-start / # impl-end block),
so the frozen spec is never touched and `same_spec(base, variant)` holds for
every case. Spec cases are checked by Nagini verify on the host; expect="verify"
passes iff (same_spec AND verifies), expect="reject" passes iff (same_spec AND
does NOT verify).

DEFENDED SURFACE (what this spec actually pins):
  Three functions over plain booleans (NO heap, NO Acc(...,1/2) read-only
  inputs -> frame-mutation is N/A; see 'assessment').

  construct_dedup(allow_dedup, dedup) -> bool   (deep model of the unchanged
    Aggregate.__init__ dedup prologue):
      Ensures(dedup is False or allow_dedup is True)   # normal-return reachable
                                                       #   only when honourable
      Ensures(Result() == dedup)                       # read-back fidelity
      Exsures(CapabilityError, dedup is True and allow_dedup is False)
                                                       # refuse EXACTLY the
                                                       #   disallowed case
  build_mean(dedup) / build_total(dedup) -> bool:
      Ensures(Result() == dedup)   with NO Exsures  ==> must return normally for
      EVERY dedup (incl. True) and record it.  This is the LOAD-BEARING clause:
      it is the *absence* of an Exsures, combined with Result()==dedup, that
      forces the family to honour a deduplicate request — exactly the gold
      change (Avg/Sum gain allow_distinct=True).  The two prepatch witnesses
      (model_prepatch*.py) revert to construct_dedup(False, dedup) and FAIL on
      "method raises no exceptions" when dedup=True.

  No @ContractOnly axioms, no A-reference deep models (meta.axioms == [],
  deep_model_references == []) ==> AXIOM_TESTS = [].

  The oracle Result()==dedup is GROUNDED in the input dedup (not an opaque
  answer-key), so there is no "wrong echo" to build: the ungrounded-oracle class
  is N/A and is replaced by an honest cheapest-impl positive control.
"""
from pathlib import Path

INSTANCE = "django__django-11603"
FLOAT_ENCODING = None  # meta.json float_encoding is null; behaviour is pure boolean

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each is a UNIQUE block; the replacement keeps every
#      spec line verbatim and changes ONLY the executable body) ---------------

# construct_dedup impl block (unique: only function with a raise in its impl)
_CD_IMPL = (
    "    # impl-start\n"
    "    if dedup and not allow_dedup:\n"
    "        raise CapabilityError()\n"
    "    stored = dedup\n"
    "    return stored\n"
    "    # impl-end"
)

# build_mean: anchor on the unique discriminating post-condition comment through
# the impl-end so the swap is unique even though the body text is shared with
# build_total. The spec lines (# The arithmetic-mean ... # deduplicate. /
# Ensures / # post-conditions-end) are reproduced VERBATIM in the replacement.
_MEAN_BLOCK = (
    "    # The arithmetic-mean family MUST honour a deduplicate request: construction\n"
    "    # always succeeds (no Exsures clause => never raises) and records the\n"
    "    # request exactly, for EVERY value of `dedup` including a request to\n"
    "    # deduplicate.\n"
    "    Ensures(Result() == dedup)\n"
    "    # post-conditions-end\n"
    "    # impl-start\n"
    "    return construct_dedup(True, dedup)\n"
    "    # impl-end"
)
_MEAN_SPEC_PREFIX = (
    "    # The arithmetic-mean family MUST honour a deduplicate request: construction\n"
    "    # always succeeds (no Exsures clause => never raises) and records the\n"
    "    # request exactly, for EVERY value of `dedup` including a request to\n"
    "    # deduplicate.\n"
    "    Ensures(Result() == dedup)\n"
    "    # post-conditions-end\n"
)

_TOTAL_BLOCK = (
    "    # The running-total family MUST honour a deduplicate request: construction\n"
    "    # always succeeds (no Exsures clause => never raises) and records the\n"
    "    # request exactly, for EVERY value of `dedup` including a request to\n"
    "    # deduplicate.\n"
    "    Ensures(Result() == dedup)\n"
    "    # post-conditions-end\n"
    "    # impl-start\n"
    "    return construct_dedup(True, dedup)\n"
    "    # impl-end"
)
_TOTAL_SPEC_PREFIX = (
    "    # The running-total family MUST honour a deduplicate request: construction\n"
    "    # always succeeds (no Exsures clause => never raises) and records the\n"
    "    # request exactly, for EVERY value of `dedup` including a request to\n"
    "    # deduplicate.\n"
    "    Ensures(Result() == dedup)\n"
    "    # post-conditions-end\n"
)


def _mean_impl(new_body):
    return _MEAN_SPEC_PREFIX + "    # impl-start\n" + new_body + "\n    # impl-end"


def _total_impl(new_body):
    return _TOTAL_SPEC_PREFIX + "    # impl-start\n" + new_body + "\n    # impl-end"


# ===========================================================================
# SPEC TESTS
# ===========================================================================
SPEC_TESTS = [

    # -------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness): structurally-different CORRECT impls
    # must verify, else SPEC-TOO-STRONG.
    # -------------------------------------------------------------------
    {
        "id": "pos-construct-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _CD_IMPL,
            "    # impl-start\n"
            "    # Branch-reorder: handle the honourable case first, raise after.\n"
            "    # Same behaviour, different control-flow shape.\n"
            "    if (not dedup) or allow_dedup:\n"
            "        stored = dedup\n"
            "        return stored\n"
            "    raise CapabilityError()\n"
            "    # impl-end",
        ),
        "rationale": "construct_dedup with the accept-branch first and the raise last "
                     "is behaviourally identical (records dedup on the honourable case, "
                     "raises iff dedup and not allow_dedup). It must verify against all "
                     "three contract clauses; if it cannot, the postcondition over-"
                     "constrains a correct impl (SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-mean-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # Local-variable reshape: name the capability, then delegate.\n"
                "    cap = True\n"
                "    return construct_dedup(cap, dedup)"
            ),
        ),
        "rationale": "build_mean delegating with the capability bound to a local True is "
                     "the same honest impl shaped differently; it returns normally for "
                     "every dedup and records it, so Ensures(Result()==dedup) holds. Must "
                     "verify (else SPEC-TOO-STRONG).",
    },

    # -------------------------------------------------------------------
    # ADMISSIBILITY: the precondition must accept normal F2P-shaped inputs.
    # build_mean(True) is exactly what the F2P test exercises
    # (Avg('rating', distinct=True)); construct_dedup(True, True) is its
    # in-domain delegate. A self-call that asserts the recorded value
    # confirms the precondition is satisfiable for the discriminating input.
    # -------------------------------------------------------------------
    {
        "id": "admiss-mean-distinct",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # Admissibility witness: the precondition (none beyond bool) admits\n"
                "    # the discriminating F2P input dedup=True; the honest delegate then\n"
                "    # constructs and records it. Assert the recorded read-back.\n"
                "    res = construct_dedup(True, dedup)\n"
                "    Assert(res == dedup)\n"
                "    return res"
            ),
        ),
        "rationale": "Avg('rating', distinct=True) is the literal F2P shape (dedup=True). "
                     "The caller establishes construct_dedup's Requires for that input and "
                     "the Assert on the recorded value passes. If this cannot verify, the "
                     "precondition rejects a legitimate input (PRECOND-TOO-STRONG).",
    },

    # -------------------------------------------------------------------
    # UNIQUENESS / partial-domain — construct_dedup record fidelity.
    # The read-back oracle Result()==dedup must pin the EXACT recorded value.
    # -------------------------------------------------------------------
    {
        "id": "weak-construct-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CD_IMPL,
            "    # impl-start\n"
            "    # WRONG: keep the refuse guard but always record False, dropping the\n"
            "    # honourable dedup=True request silently.\n"
            "    if dedup and not allow_dedup:\n"
            "        raise CapabilityError()\n"
            "    stored = False\n"
            "    return stored\n"
            "    # impl-end",
        ),
        "refinement": "Recording False instead of `distinct` is self.distinct=False in the "
                      "real Aggregate.__init__: Avg('rating', distinct=True) would build but "
                      "carry distinct=False, so the SQL would NOT add DISTINCT and the "
                      "aggregate would average ALL rows -> the F2P expects 4.125 (distinct) "
                      "but gets the all-rows mean. Faithful patch FAILS test_distinct_on_"
                      "aggregate.",
        "rationale": "Rejected by Ensures(Result()==dedup): for dedup=True the impl returns "
                     "False != True. If it verified, the read-back postcondition would be "
                     "SPEC-TOO-WEAK (admits dropping the request).",
    },
    {
        "id": "weak-construct-negate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CD_IMPL,
            "    # impl-start\n"
            "    # WRONG: record the NEGATION of the request (off-by-flip).\n"
            "    if dedup and not allow_dedup:\n"
            "        raise CapabilityError()\n"
            "    stored = not dedup\n"
            "    return stored\n"
            "    # impl-end",
        ),
        "refinement": "self.distinct = not distinct flips the dedup state: a distinct=True "
                      "request records False (no DISTINCT in SQL -> all-rows aggregate, wrong "
                      "4.125->wrong value) and a distinct=False request records True. The F2P "
                      "would compute the wrong aggregate; faithful patch FAILS.",
        "rationale": "Rejected by Ensures(Result()==dedup): for dedup=False returns True, "
                     "for dedup=True returns False. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # UNIQUENESS / accept-too-much — construct_dedup must REFUSE the
    # disallowed case. A rival that never raises violates the
    # normal-return-reachability clause.
    # -------------------------------------------------------------------
    {
        "id": "weak-construct-never-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CD_IMPL,
            "    # impl-start\n"
            "    # WRONG: drop the capability guard entirely — always accept and record.\n"
            "    stored = dedup\n"
            "    return stored\n"
            "    # impl-end",
        ),
        "refinement": "Dropping `if distinct and not self.allow_distinct: raise TypeError` "
                      "is the bug the codebase had BEFORE distinct-capability gating existed: "
                      "a disabled family (Max/Min/StdDev/Variance) would silently accept "
                      "distinct=True. The test_count regression / the P2P suite that asserts "
                      "disabled aggregates raise TypeError on distinct would FAIL. Faithful "
                      "patch does not resolve the family-gating behaviour.",
        "rationale": "Rejected by Ensures(dedup is False or allow_dedup is True): on the "
                     "normal-return path with dedup=True, allow_dedup=False both disjuncts "
                     "are False. The contract only permits a normal return when honourable; "
                     "SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # CONTROL-FLOW-EFFECT — construct_dedup must raise on EXACTLY the
    # disallowed case (the Exsures domain). A rival that raises on an
    # honourable input (a spurious refusal) is a raise/return difference the
    # value abstraction would miss; the Exsures pins the raise domain.
    # -------------------------------------------------------------------
    {
        "id": "weak-construct-over-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _CD_IMPL,
            "    # impl-start\n"
            "    # WRONG: refuse whenever dedup is requested, ignoring the capability.\n"
            "    if dedup:\n"
            "        raise CapabilityError()\n"
            "    stored = dedup\n"
            "    return stored\n"
            "    # impl-end",
        ),
        "refinement": "Raising on every distinct=True request (even for permitted families) "
                      "is `if distinct: raise TypeError` — Avg('rating', distinct=True) would "
                      "raise instead of building, so test_distinct_on_aggregate raises and "
                      "FAILS for Avg/Sum/Count. Faithful patch does not resolve the F2P.",
        "rationale": "Rejected by Exsures(CapabilityError, dedup is True and allow_dedup is "
                     "False): the impl raises for dedup=True, allow_dedup=True, but the "
                     "Exsures only sanctions a raise when allow_dedup is False. Nagini "
                     "rejects an exception outside its declared Exsures domain. This is a "
                     "control-flow (raise vs return) difference the bare value abstraction "
                     "could not see; the Exsures domain catches it. SPEC-TOO-WEAK if "
                     "verified.",
    },

    # -------------------------------------------------------------------
    # PARTIAL-DOMAIN on build_mean / build_total — a rival correct on
    # dedup=False but diverging on dedup=True (the input the F2P actually
    # passes). These are the reasoned analogues of the prepatch witnesses.
    # -------------------------------------------------------------------
    {
        "id": "weak-mean-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # WRONG (pre-patch Avg): route through the DISABLED capability.\n"
                "    return construct_dedup(False, dedup)"
            ),
        ),
        "refinement": "This is exactly model_prepatch.py: Avg without allow_distinct=True "
                      "inherits Aggregate.allow_distinct=False, so Avg('rating', "
                      "distinct=True) raises TypeError('Avg does not allow distinct.'). "
                      "test_distinct_on_aggregate FAILS on the Avg subTest. Faithful patch "
                      "(omitting the Avg line) does NOT resolve the F2P.",
        "rationale": "Rejected: build_mean has no Exsures, but construct_dedup(False, True) "
                     "raises CapabilityError -> 'method raises no exceptions' at the call "
                     "site. The absence of Exsures + Ensures(Result()==dedup) forces normal "
                     "return for dedup=True. SPEC-TOO-WEAK if verified.",
    },
    {
        "id": "weak-total-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _TOTAL_BLOCK,
            _total_impl(
                "    # WRONG (pre-patch Sum): route through the DISABLED capability.\n"
                "    return construct_dedup(False, dedup)"
            ),
        ),
        "refinement": "This is exactly model_prepatch_2.py: Sum without allow_distinct=True "
                      "inherits Aggregate.allow_distinct=False, so Sum('rating', "
                      "distinct=True) raises TypeError. test_distinct_on_aggregate FAILS on "
                      "the Sum subTest. Faithful patch (omitting the Sum line) does NOT "
                      "resolve the F2P.",
        "rationale": "Rejected: build_total has no Exsures; construct_dedup(False, True) "
                     "raises -> 'method raises no exceptions'. SPEC-TOO-WEAK if verified.",
    },
    {
        "id": "weak-mean-honour-only-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # WRONG partial-domain: correct on dedup=False (delegate with the\n"
                "    # capability enabled), but on dedup=True re-raise the refusal — so it\n"
                "    # honours the request only when there is nothing to honour.\n"
                "    if dedup:\n"
                "        raise CapabilityError()\n"
                "    return construct_dedup(True, dedup)"
            ),
        ),
        "refinement": "Honouring distinct only when distinct is False is the pre-patch Avg "
                      "behaviour wearing a disguise: Avg('rating', distinct=True) still "
                      "raises TypeError, so test_distinct_on_aggregate FAILS for Avg. The "
                      "subdomain it gets right (distinct=False) is never exercised by the "
                      "F2P. Faithful patch does NOT resolve the F2P.",
        "rationale": "Rejected: build_mean declares no Exsures yet the impl raises for "
                     "dedup=True -> 'method raises no exceptions'. The load-bearing "
                     "absence-of-Exsures pins the dedup=True subdomain that the F2P needs. "
                     "SPEC-TOO-WEAK if verified.",
    },
    # -------------------------------------------------------------------
    # VACUITY / non-termination — the constructor must actually COMPLETE.
    # Nagini is a partial-correctness verifier: without a termination
    # obligation a diverging body satisfies every Ensures vacuously. The
    # MustTerminate(2) precondition on build_mean/build_total (and the
    # measure-1 obligation on the construct_dedup prologue) pins totality.
    # -------------------------------------------------------------------
    {
        "id": "weak-mean-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # WRONG (vacuous): spin forever before the correct tail. Every\n"
                "    # Ensures holds vacuously (no normal exit is ever reached), yet the\n"
                "    # constructor never delivers the object to its caller.\n"
                "    b = True\n"
                "    while b:\n"
                "        Invariant(True)\n"
                "        b = True\n"
                "    return construct_dedup(True, dedup)"
            ),
        ),
        "refinement": "A real Avg.__init__ that hangs (e.g. an accidental infinite loop "
                      "before delegating to Aggregate.__init__) never constructs the "
                      "aggregate: Avg('rating', distinct=True) blocks forever, so "
                      "test_distinct_on_aggregate (and every P2P touching Avg) times out — "
                      "the faithful patch does NOT resolve. (This is the audit's P1 witness "
                      "class: an Invariant(True) loop that VERIFIED under the pre-fix "
                      "contract, since Nagini requires no termination proof by default.)",
        "rationale": "Rejected by the MustTerminate(2) termination obligation in "
                     "build_mean's preconditions: the loop takes no termination measure, so "
                     "Nagini reports an obligation leak ('Loop might not take all "
                     "unsatisfied obligations from the context'). Without MustTerminate "
                     "this rival verified — the pre-fix G-PANEL-1 hole.",
    },
    {
        "id": "weak-mean-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _MEAN_BLOCK,
            _mean_impl(
                "    # WRONG: construct (never raises) but record the WRONG value — always\n"
                "    # False, dropping the deduplicate request the family must honour.\n"
                "    construct_dedup(True, dedup)\n"
                "    return False"
            ),
        ),
        "refinement": "Building Avg but recording self.distinct=False discards the request: "
                      "no DISTINCT reaches the SQL, so Avg('rating', distinct=True) averages "
                      "all six rows instead of the four distinct ratings -> not 4.125. "
                      "test_distinct_on_aggregate FAILS. Faithful patch does NOT resolve.",
        "rationale": "Rejected by build_mean's Ensures(Result()==dedup): for dedup=True it "
                     "returns False. This is the build-level analogue of the construct "
                     "record-fidelity attack; SPEC-TOO-WEAK if verified.",
    },
]

# ===========================================================================
# AXIOM TESTS — none.
# meta.json: axioms == [], deep_model_references == []. The changed datum
# (Avg/Sum allow_distinct=True) is modelled DEEPLY (construct_dedup spells out
# the real Aggregate.__init__ guard); nothing is axiomatized, so there is no
# axiom-soundness or axiom-containment obligation. (G-AX evidence — that the
# deep model equals the real Django decisions over all 7 families x
# {False,True} — lives in axiom_check.py and is out of PBT scope here.)
# ===========================================================================
AXIOM_TESTS = []
