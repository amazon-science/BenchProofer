# properties.py — PBT falsification battery for django__django-13925.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the single `# impl-start` .. `# impl-end` body of check_default_pk and leave
# the frozen spec (PkField ctor, pure region advisory_warranted /
# reuses_ancestor_declared_key, pre/post-conditions, signature) byte-identical.
# same_spec is therefore guaranteed for every case.
#
# DEFENDED SURFACE (read from model.py / refinement.md / mapping.md / instance.json):
#   check_default_pk(pk: PkField, setting_overridden, appconfig_overridden) -> int
#   pins, in its post-conditions:
#     (V) Result() == 0 or Result() == 1                          -- count is a bit
#     (W) (Result() == 1) == advisory_warranted(pk.auto,
#             pk.reuses_ancestor_key_a, pk.reuses_ancestor_key_b,
#             setting_overridden, appconfig_overridden)           -- the LOAD-BEARING clause
#     (F) Acc(pk.auto,1/2) & Acc(pk.reuses_ancestor_key_a,1/2) &
#         Acc(pk.reuses_ancestor_key_b,1/2) held on entry AND exit, plus
#         pk.auto==Old(pk.auto) & the two reuse flags ==Old(...)  -- read-only frame
#   where (grounded, fully-unfolded @Pure helper):
#     advisory_warranted(a,ra,rb,s,c) ==
#        a and not (ra and rb) and not s and not c
#     reuses_ancestor_declared_key(a,ra,rb) == ra and rb
#
#   (T) Requires(MustTerminate(6)) on check_default_pk, and
#       Requires(MustTerminate(1)) on PkField.__init__       -- TOTAL correctness
#
#   (T) is what makes the postconditions claims about ALL runs rather than only
#   the ones that reach the return. Without it a rival that never returns
#   satisfies every Ensures vacuously and VERIFIES; 'weak-self-call-diverges'
#   below is exactly such a rival (it verified before (T) landed) and is kept in
#   the reject lane as the witness. The two levels are ordered 6 > 1 because
#   Nagini's call rule is caller_level > callee_level, so the constructor must sit
#   strictly beneath its caller; at level 1 for the caller the same rule fails
#   against list/__init__-style callees with "Obligation leak check failed".
#   There are no loops in this model, so no MustTerminate invariant is needed.
#
#   (W) is the discriminating fix: the added conjunct not (ra and rb) suppresses
#   the W042 advisory exactly for the auto-created key that re-uses a concrete
#   ancestor's already-declared key. The pre-patch guard lacked it (warned at
#   (auto,ra,rb)=(True,True,True)) -- that is model_prepatch.py and the bug the
#   F2P test_auto_created_inherited_pk / test_explicit_inherited_pk demand fixed.
#
# READ-ONLY INPUT: pk is held with Acc(pk.<field>, 1/2) on the three booleans.
#   => the FRAME-MUTATION class APPLIES and is MANDATORY. weak-frame-mutate below
#   tries to satisfy (W) vacuously by WRITING to pk; it must be rejected for
#   INSUFFICIENT PERMISSION (half permission is read-only; a write needs full).
#
# ORACLE GROUNDING: advisory_warranted is @Pure but GROUNDED -- it is a closed
#   boolean function of the function's own arguments (pk's three flags + the two
#   override params), fully unfolded in the pure region. There is NO opaque
#   answer-key to echo: any value an impl returns is checked against the real
#   boolean computed from the inputs. So there is no "wrong echo that verifies"
#   (the UNGROUNDED-ORACLE class does NOT apply). The honest stand-in is a
#   cheapest-correct positive control that returns 1 iff advisory_warranted holds
#   (pos-cheapest-grounded), spelled with the inlined predicate.
#
# AXIOMS: meta.json axioms == [] and the axioms region is empty (every op is a
#   boolean field read / connective). There is one A-reference deep model
#   (advisory_warranted == real branch condition under the field bijection),
#   exhaustively validated over the full 2**5 truth table by axiom_check.py /
#   G-AX. That is a deep-model equality fully enumerated on a finite domain, not a
#   @ContractOnly callee contract; there is no real callee to fuzz in-container
#   beyond that finite enumeration. AXIOM_TESTS is therefore [] (justified in
#   'assessment'); the containment is trivially total (5 booleans, 32 cases, all
#   covered, boundary == fuzz).
from pathlib import Path

INSTANCE = "django__django-13925"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The single whole-impl anchor of check_default_pk (lines 100-107 of model.py).
# Terminated by the trailing `# impl-end` so the swap stays strictly inside the
# one impl region and never touches the frozen spec above it.
_IMPL = """    if (
        pk.auto and
        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and
        not setting_overridden and
        not appconfig_overridden
    ):
        return 1
    return 0
    # impl-end"""


def _impl(new_body: str) -> str:
    """Replace ONLY check_default_pk's impl body, keeping the `# impl-end`
    marker so the region boundary is untouched (same_spec guaranteed)."""
    return _swap(_BASE, _IMPL, new_body + "\n    # impl-end")


SPEC_TESTS = [

    # ----------------------------------------------------------------- soundness
    # POSITIVE CONTROL (structural reorder). A correct but structurally-different
    # impl: invert the guard and return 0 first via an early-out per-conjunct
    # short-circuit, then return 1 in the fall-through. Same truth function, no
    # framing lemma needed (the post facts are a single boolean equivalence over
    # immutable args, not a fold over a sequence), so it MUST verify. If it cannot
    # => SPEC-TOO-STRONG.
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not pk.auto:\n"
            "        return 0\n"
            "    if pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b:\n"
            "        return 0\n"
            "    if setting_overridden:\n"
            "        return 0\n"
            "    if appconfig_overridden:\n"
            "        return 0\n"
            "    return 1"
        ),
        "rationale": "a correct but reordered impl (per-conjunct early-out 0, "
                     "fall-through 1) computes the same advisory_warranted bit; "
                     "the post is a direct boolean equivalence over immutable "
                     "args (no fold/induction lemma) so it must verify "
                     "(else SPEC-TOO-STRONG). Source: postcondition (W).",
    },

    # CHEAPEST HONEST positive control (grounded-oracle stand-in). Since the
    # oracle is grounded in the args, the cheapest correct impl computes the
    # inlined predicate directly and returns 1/0 from it. This is exactly the work
    # the gold does -- there is no wrong echo to build (see header). Must verify.
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    warranted = (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    )  # type: bool\n"
            "    if warranted:\n"
            "        return 1\n"
            "    return 0"
        ),
        "rationale": "cheapest correct impl: binds the grounded predicate to a "
                     "typed local and returns 1 iff it holds. Grounded oracle => "
                     "no wrong echo; this is the honest positive control. "
                     "Source: postcondition (W).",
    },

    # ----------------------------------------------------------------- admissibility
    # A caller that constructs F2P/P2P-shaped PkField records and asserts the
    # graph's own oracle on each. If the Requires (half-permission on three
    # constructed booleans, plus MustTerminate) cannot be met for a normal input
    # => PRECOND-TOO-STRONG. The caller lives strictly in the impl region of
    # check_default_pk, so the spec is untouched.
    #
    # NOTE ON SHAPE: this probe deliberately does NOT self-call check_default_pk.
    # The precondition carries Requires(MustTerminate(6)), and Nagini's measure
    # rule for a call is caller_level > callee_level (Measure$check demands
    # Measure$value > value). A self-call is level 6 calling level 6, so 6 > 6 is
    # false for EVERY choice of level -- an unguarded self-call is unprovable by
    # construction, not by a level that was picked too low. It is also genuinely
    # non-terminating: the probe recursed unconditionally with no base case
    # (confirmed by executing the body as plain Python -> RecursionError). The
    # diverging original is retained, in the reject lane, as
    # 'weak-self-call-diverges' below. Admissibility is therefore probed the
    # honest way: construct the records (exercising PkField.__init__ at
    # level 1 < 6, which is what proves the constructor is callable from here)
    # and assert the grounded oracle plus the read-only permissions the
    # precondition demands.
    {
        "id": "admiss-construct-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        res = 1\n"
            "    else:\n"
            "        res = 0\n"
            "    # admissibility probe: F2P/P2P-shaped PkField records are\n"
            "    # constructible here (PkField.__init__ sits at MustTerminate(1),\n"
            "    # strictly below this method's level 6, so the obligation leaves\n"
            "    # room beneath it) and each satisfies the Acc(...,1/2) Requires.\n"
            "    plain = PkField(True, False, False)   # auto-created plain pk -> warns (P2P test_auto_created_pk)\n"
            "    Assert(Acc(plain.auto, 1 / 2) and Acc(plain.reuses_ancestor_key_a, 1 / 2)\n"
            "           and Acc(plain.reuses_ancestor_key_b, 1 / 2))\n"
            "    Assert(advisory_warranted(plain.auto, plain.reuses_ancestor_key_a,\n"
            "                              plain.reuses_ancestor_key_b, False, False))\n"
            "    inherited = PkField(True, True, True)  # auto-created parent-link key -> suppressed (F2P)\n"
            "    Assert(not advisory_warranted(inherited.auto, inherited.reuses_ancestor_key_a,\n"
            "                                  inherited.reuses_ancestor_key_b, False, False))\n"
            "    explicit = PkField(False, False, False)  # explicit pk -> no advisory (P2P test_explicit_pk)\n"
            "    Assert(not advisory_warranted(explicit.auto, explicit.reuses_ancestor_key_a,\n"
            "                                  explicit.reuses_ancestor_key_b, False, False))\n"
            "    return res"
        ),
        "rationale": "the precondition must admit normal F2P/P2P-shaped inputs: a "
                     "freshly-constructed PkField carries full permission (so the "
                     "Acc(...,1/2) Requires is establishable) and the constructor "
                     "is reachable under MustTerminate(6) because __init__ sits at "
                     "level 1; the grounded oracle then holds with the F2P/P2P "
                     "polarity on each record. Else PRECOND-TOO-STRONG. "
                     "Source: pre-conditions + (W).",
    },

    # ----------------------------------------------------------------- uniqueness
    # ATTACK 1 (FRAME-MUTATION, MANDATORY -- pk is read-only at Acc(...,1/2)).
    # A rival that tries to satisfy the postcondition by WRITING to the read-only
    # input pk (overwriting pk.reuses_ancestor_key_b to neutralise the ancestor-
    # reuse case before reading it). It keeps the gold guard verbatim so the
    # rejection is attributable to the WRITE, not to a wrong value. Must be
    # rejected for INSUFFICIENT PERMISSION (half permission cannot be written).
    {
        "id": "weak-frame-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    pk.reuses_ancestor_key_b = False\n"
            "    if (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "the real check only READS cls._meta.pk.* (auto_created, "
                      "isinstance(pk, OneToOneField), remote_field.parent_link); a "
                      "faithful real patch that mutated the model's pk field "
                      "descriptor mid-check would corrupt shared class metadata "
                      "(cls._meta.pk is shared state) and is not what the gold "
                      "patch does -- so it does not faithfully refine the gold and "
                      "would not resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: pk.reuses_ancestor_key_b "
                      "is held with Acc(...,1/2) (read-only); writing it needs full "
                      "permission => insufficient permission. Source: pre-conditions "
                      "Acc(pk.reuses_ancestor_key_b, 1/2).",
    },

    # ATTACK 2 (partial-domain, THE bug-delta = model_prepatch). Drop the
    # ancestor-reuse suppression conjunct: warn whenever auto and no overrides.
    # Correct on every plain auto-created key (ra and rb not both True), WRONG on
    # the auto-created parent-link inherited key (ra and rb both True). This is the
    # exact pre-patch guard.
    {
        "id": "weak-drop-reuse-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "this is the PRE-PATCH guard (drops `not (isinstance(pk, "
                      "OneToOneField) and pk.remote_field.parent_link)`). On the "
                      "auto-created inherited parent-link key (auto,ra,rb)="
                      "(True,True,True) it returns 1 (emits W042) where the gold "
                      "returns 0. The F2P test_auto_created_inherited_pk / "
                      "test_explicit_inherited_pk assert NO W042 on that model => "
                      "the faithful real patch FAILS the F2P; it does NOT resolve.",
        "rationale": "violates (W): at (auto,ra,rb,s,c)=(True,True,True,False,False) "
                      "advisory_warranted is False (not (ra and rb) is False) yet "
                      "Result()==1. Source: postcondition (W), the added conjunct.",
    },

    # ATTACK 3 (partial-domain, over-suppress on flag A alone). Suppress on
    # reuses_ancestor_key_a alone (drop the conjunction with B). Correct whenever
    # A==B (incl. both-True and both-False), WRONG on the (A=True, B=False) sub-
    # domain: a one-to-one pk that is NOT a parent link should still warn but this
    # suppresses it.
    {
        "id": "weak-suppress-on-A-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not pk.reuses_ancestor_key_a and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "this suppresses the advisory on a one-to-one pk that is NOT "
                      "a parent link (isinstance(pk, OneToOneField) True but "
                      "remote_field.parent_link False) -- a real auto-created "
                      "OneToOneField pk that is not the inherited link. The gold "
                      "guard requires BOTH conjuncts; suppressing on the isinstance "
                      "alone wrongly drops W042 for such a model, so the faithful "
                      "real patch silences a warning the spec demands (and would "
                      "diverge from gold on that configuration) -- it does NOT "
                      "resolve.",
        "rationale": "violates (W): at (auto,ra,rb,s,c)=(True,True,False,False,False) "
                      "advisory_warranted is True (not (True and False) == True) yet "
                      "Result()==0. Source: postcondition (W), the conjunction in "
                      "reuses_ancestor_declared_key.",
    },

    # ATTACK 4 (partial-domain, ignore one override). Drop the appconfig_overridden
    # check. Correct whenever the app-config override is not set, WRONG when only
    # the app-config override is configured (it should suppress but this still
    # warns). Hits the P2P test_app_default_auto_field.
    {
        "id": "weak-ignore-appconfig-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden\n"
            "    ):\n"
            "        return 1\n"
            "    return 0"
        ),
        "refinement": "this drops `not cls._meta.app_config."
                      "_is_default_auto_field_overridden`. When the owning app sets "
                      "default_auto_field (appconfig_overridden True) the advisory "
                      "must be suppressed; this still emits W042. The P2P "
                      "test_app_default_auto_field asserts NO warning when the app "
                      "config overrides the default => the faithful real patch warns "
                      "spuriously and FAILS that P2P; it does NOT resolve.",
        "rationale": "violates (W): at (auto,ra,rb,s,c)=(True,False,False,False,True) "
                      "advisory_warranted is False (not c is False) yet Result()==1. "
                      "Source: postcondition (W), the appconfig_overridden conjunct.",
    },

    # ATTACK 6 (NON-TERMINATION, retained from the former accept-lane
    # 'admiss-self-call'). This body is byte-for-byte the probe that used to sit
    # in the admissibility lane with expect="verify". It DIVERGES: it self-calls
    # check_default_pk unconditionally, on every path, with no base case -- the
    # three probe calls are reached whatever the arguments, so each invocation
    # spawns another. Executing the body as plain Python raises RecursionError.
    #
    # Under the OLD specification, which demanded nothing of termination, this
    # rival VERIFIED (measured: "Verification successful"): the postconditions
    # were claimed only of runs reaching the return, and this run never reaches
    # it, so every Ensures held vacuously. That is precisely the partial-vs-total
    # hole Requires(MustTerminate(6)) exists to close, and this case is the
    # witness for it: with the obligation, Nagini rejects it with "Obligation
    # leak check failed. Callee check_default_pk might not take all unsatisfied
    # obligations from the caller."
    #
    # No level assignment can rescue it. Nagini's measure rule for a call is
    # caller_level > callee_level (Measure$check requires Measure$value > value),
    # so a self-call compares 6 > 6 -- false for every n. It is not a measure
    # that went unfound; a variant that never returns IS a wrong implementation,
    # and asserting the spec REJECTS it is a stronger claim than asserting the
    # spec accepted it.
    {
        "id": "weak-self-call-diverges",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        res = 1\n"
            "    else:\n"
            "        res = 0\n"
            "    plain = PkField(True, False, False)\n"
            "    Assert(check_default_pk(plain, False, False) == 1)\n"
            "    inherited = PkField(True, True, True)\n"
            "    Assert(check_default_pk(inherited, False, False) == 0)\n"
            "    explicit = PkField(False, False, False)\n"
            "    Assert(check_default_pk(explicit, False, False) == 0)\n"
            "    return res"
        ),
        "refinement": "the real check is a straight-line read of cls._meta.pk.* "
                      "and two config flags; it calls nothing recursively. A "
                      "faithful real patch shaped like this would re-enter "
                      "_check_default_pk on every model check without a base case "
                      "and hang the whole `manage.py check` run -- the F2P/P2P "
                      "tests would never return a warnings list to assert on, so "
                      "it does NOT resolve.",
        "rationale": "rejected by the OBLIGATION system: the method carries "
                      "Requires(MustTerminate(6)) and an unguarded self-call must "
                      "satisfy caller_level > callee_level, i.e. 6 > 6, which is "
                      "false for every level => 'Callee check_default_pk might not "
                      "take all unsatisfied obligations from the caller'. This "
                      "rival VERIFIED before the obligation landed, so it is the "
                      "direct witness that the spec now proves TOTAL rather than "
                      "partial correctness. Source: pre-conditions "
                      "Requires(MustTerminate(6)).",
    },

    # ATTACK 5 (supporting near-miss: count out of range). Return the W042 count as
    # 2 instead of 1 on the warranted path. Cheap supporting case; hits clause (V).
    # Still carries a real refinement (a duplicated-warning list would change the
    # observable count the F2P/P2P assert on).
    {
        "id": "weak-count-out-of-range",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if (\n"
            "        pk.auto and\n"
            "        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and\n"
            "        not setting_overridden and\n"
            "        not appconfig_overridden\n"
            "    ):\n"
            "        return 2\n"
            "    return 0"
        ),
        "refinement": "this returns count 2 (a list with two W042 warnings) on the "
                      "warranted path. The F2P/P2P tests assert the warnings list "
                      "equals exactly [Warning(... id='models.W042')] (a single "
                      "advisory) => a duplicated warning fails the assertEqual; the "
                      "faithful real patch (returning two copies) does NOT resolve.",
        "rationale": "violates (V) Result()==0 or Result()==1 (and (W) which forces "
                      "Result()==1 on the warranted path, not 2). Source: "
                      "post-conditions (V)+(W).",
    },
]


# No @ContractOnly axioms (meta.json axioms == []; axioms region empty). The one
# A-reference deep model (advisory_warranted == real branch condition under the
# field bijection) is a total boolean function of five booleans, fully enumerated
# over the 2**5 truth table by axiom_check.py / G-AX (boundary == fuzz; the input
# domain is finite and completely covered, so containment is trivially total).
# There is no opaque real callee to fuzz in-container beyond that enumeration.
AXIOM_TESTS = []
