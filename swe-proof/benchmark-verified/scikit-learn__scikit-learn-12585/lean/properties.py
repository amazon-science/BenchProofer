"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-12585 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one function ``reproduce(est, permit_fallback)`` over a FLAT record
``Candidate(is_aggregate, has_introspect, is_class_object)`` whose success value
is a FRESH object, contracted with fractional-permission (read-only) inputs and
a ``MustTerminate`` measure. This Lean bundle models the SINGLE purely-functional
core as a total recursive ``def`` over a RICHER carrier: a ``PyVal`` tree
(``group kind elems`` | ``node isBlueprint exposesConfig tag config``) duplicated
under a ``safe`` flag, returning an ``Except``-carried outcome. The obligation is
``result = <structural reproduction> safe v``.

Two carrier facts reshape which nagini cases survive:

  * On this carrier a SUCCESSFUL reproduction is structurally the input value
    (a leaf is returned unchanged; a rebuild carries every field through). There
    is no observable "fresh vs. same object" distinction — Lean is referentially
    transparent, values have no identity. So the whole nagini family that turned
    on identity-of-result (the "genuine instance must be a DISTINCT object"
    clause, and its guarded twin) is VACUOUS here: the modeled spec asserts no
    identity, so a "returns the same value" rival is not a violation and CANNOT
    be refuted. Those cases are dropped with reasons in ``assessment``.
  * What IS attackable is the ROUTING and the SHAPE: whether a value is sent to
    the no-configuration path or the rebuild path, whether the safe flag turns a
    no-configuration value into a failure or an unchanged return, and — new to
    this carrier, since nagini's flat record had no collection shape — the
    element-wise failure-propagation, kind and order of a collection.

DEFENDED SURFACE (one modeled behavior). ``result`` is pinned equal to a single
grounded structural computation over the inputs, with these independent
top-level behaviors selected by the input:

  * (the fix) the no-configuration decision depends on whether the configuration
    interface is actually USABLE — a value that merely ADVERTISES the interface
    but is a blueprint is routed to the no-configuration path, exactly like a
    value that exposes nothing;
  * on the no-configuration path, ``safe`` decides between an unchanged return
    and a reported failure;
  * a collection is duplicated element-wise, preserving kind and order, and
    fails as a whole if any element fails.

The BEHAVIOURAL DISCRIMINATOR (the fix): the no-configuration routing condition
is (does-not-expose OR is-blueprint), not (does-not-expose) alone. Pre-fix, a
blueprint that advertises the interface fell through to the rebuild path, which
queries an interface that is not usable on a blueprint and fails — precisely the
F2P scenario (a class-valued parameter cloned during the recursive descent). The
first reject rival below IS that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite. The nagini frame-mutation rival has no expressible instance here;
    no substitute is fabricated. (nagini case ``frame-mutate-input``.)
  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE, and the reason was measured
    rather than assumed. The original port note claimed a diverging impl "cannot
    be written at all". That is not quite true: marking the impl ``partial``
    does let a non-terminating one be written, and the audit built one. What
    happens is that ``partial`` makes the impl OPAQUE to the kernel, so
    ``fun_induction`` has no functional-induction principle to offer
    (``No functional induction theorem for `implementation_duplicate` ``) and
    the FROZEN obligation cannot close — the case is rejected, which is the
    expected outcome for a wrong impl. But it is rejected for an unfoldable-impl
    reason rather than a spec reason, and its witness cannot be landed either:
    the refutation needs ``implementation_duplicate`` to reduce at a concrete
    input, and ``unfold`` on a ``partial`` def fails
    (``Tactic `unfold` failed to unfold``). So the case cannot be given a
    discriminating witness on this carrier and is NOT shipped. Recorded here
    because "we could not land it" is the honest reason, not "it is
    unwritable".
    SECOND-AUDIT RE-DERIVATION, with the disposition checked against the
    semantics this bundle actually sets. The frozen solution carries NO
    ``set_option loom.semantics.termination`` line (nor does any lean bundle in
    the corpus), so the carrier's default governs: a plain ``def`` must satisfy
    the termination checker, and the frozen impl discharges an explicit
    ``termination_by sizeOf v`` / ``decreasing_by``. A diverging rival is
    therefore genuinely REJECTED here rather than verifying vacuously — the
    "total" disposition — so the case would be SHIPPABLE if a discriminating
    witness could be landed. Both halves were re-measured. The rival is writable
    (``partial def`` with a self-call on the same input; passes variant scope)
    and does fail the obligation: ``No functional induction theorem for
    `implementation_duplicate` `` (module exit 1). But the witness genuinely
    cannot be landed, and this time BOTH tactic routes were tried rather than
    one: the ``unfold`` route reproduces the port's error verbatim (``Tactic
    `unfold` failed to unfold `implementation_duplicate` ``, exit 1), and the
    ``eq_def`` route that the collection and rebuild witnesses use fails
    differently and just as fatally — ``Unknown constant
    `implementation_duplicate.eq_def` `` (exit 1), since ``partial`` generates no
    equation lemma either. A ``witness_reference`` cannot rescue it: that
    mechanism replaces the GOLD side of the pair, whereas the half that fails
    here is the RIVAL side (the witness must first HOLD of the rival, and no
    tactic makes an opaque ``partial`` constant reduce at a concrete input). So
    this is a KNOWN HOLE in what the battery can certify — not a vacuous class,
    and not a tooling bug — and the port's disposition stands with the reason now
    measured on both routes. Distinct from the velvet ``partial``-semantics hole
    (``the corpus-wide termination-semantics finding``), which is a VERIFYING diverging impl on a
    different backend; this backend's lean bundles are explicitly out of that
    finding's scope and nothing here re-reports it.
  * RESULT-IDENTITY — VACUOUS. See PORT NOTE: the spec asserts no object
    identity, so nagini's ``nonleaf-identity-leak`` and
    ``instance-identity-leak-guarded`` collapse (a "returns the same value" rival
    satisfies the spec). Dropped.
    SECOND-AUDIT RE-DERIVATION, by machine check at nagini's own refutation
    point rather than by argument. Built and elaborated (exit 0) the equation
    ``reproduce false (.node false true 9 [(1, .node false false 0 [])])
    = .ok (.node false true 9 [(1, .node false false 0 [])])`` — i.e. at exactly
    the value nagini's C3 called a "genuine instance" (realized,
    configuration-exposing, with a non-empty configuration), the result the spec
    DEMANDS is structurally the input itself. So a "hand back the same value"
    rival does not violate the spec there; it satisfies it, and no witness can
    refute what the spec requires. The vacuity call is correct and now
    demonstrated at the point that matters. (A stronger general lemma —
    ``∀ v, reproduce false v = .ok v`` — was also attempted and NOT closed: the
    collection arm needs a ``mapM``-of-``Except.ok`` inversion the frozen helper
    lemmas do not provide. That is a proof-engineering shortfall on the auditor's
    side and is recorded as such; it is not evidence against the vacuity, which
    the concrete point above already establishes.)
  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (no opaque callee, no
    axiom). There is no answer key to echo. In its place the battery carries
    honest cheapest-implementation POSITIVE CONTROLS.
  * ROUTING / VALUE / SHAPE — APPLIES. The reject rivals below attack the
    usable-interface routing decision (the fix), the safe-flag failure/return
    decision, the no-configuration unchanged-return decision, and the collection
    failure-propagation and kind preservation.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was checked to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.
The carrier is fully transparent (no opaque callee), so every witness input is a
concrete literal and reduces by evaluation: node witnesses unfold and
``simp [reproduce, configUnusable]``; collection witnesses additionally reduce
the element traversal (``mapM``/``attach``) on both sides via the ``eq_def``
equation lemmas. No witness binds a hypothesis, so none can be inconsistent.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point. ``safe`` takes both settings
(``false`` for the fix / no-op / kind / identity rivals, ``true`` for the
refusal / failure-propagation / unsafe-descent rivals). ``v`` ranges over
``node`` (blueprint-exposing-config; plain leaf; and realized
configuration-exposing, both with an empty and with a non-empty configuration)
and ``group`` (kind 3 with a failing child, kind 7 with a succeeding child).
Within ``node`` all four ``(isBlueprint, exposesConfig)`` combinations that
mapping.md lists as realizable are now reached. Within ``group`` the ``kind``
binder is moved off the value a kind-dropping rival would hardcode, and in the
rebuild rivals the class identity is likewise moved off the hardcoded value. The
eight reject witnesses probe eight distinct inputs; no two share a refutation
point.

SECOND-AUDIT CORRECTION to this claim. The paragraph above previously asserted
all four flag combinations were reached and credited the two rebuild-path rivals
with closing that gap. That was FALSE, and it was the one prose claim in this
file the gate cannot check. The seven shipped witness inputs were
``(isBlueprint, exposesConfig)`` = (T,T) twice, (F,F) three times, (F,T) twice —
the fourth realizable combination, **(T,F)** (a value that IS a blueprint and
exposes no configuration interface at all), was never a witness
input. It is not merely a missing point: it is the only combination where the
routing guard's two disjuncts are BOTH true, so it is exactly the point that
distinguishes the specified disjunction from an EXCLUSIVE one. A rival routing on
``(!exposesConfig) != isBlueprint`` (xor) therefore agreed with the frozen impl at
every one of the seven old witness inputs, and the battery could not refute it.
That rival now ships as ``route-on-exclusive-or``, which is refuted at (T,F).

AUDIT PROVENANCE. This battery was independently audited after its port. Every
positive and every reject case was rebuilt from scratch by the auditor: each
reject witness was built twice (against its rival, which must succeed, and
against the frozen solution, which must fail), and all five original gold-side
failures were confirmed to be semantic refutations (``unsolved goals ⊢ False``
— the claim reduced and gold satisfies the spec at that input) rather than
missing identifiers, type errors, or stuck reductions. Five NEW wrong impls were
tried against the frozen spec as a SPEC-TOO-WEAK probe (element order reversed;
the no-configuration return dropping the value's configuration; the safe flag
not propagated into the collection recursion; the configuration recursion
inheriting ``safe``; the rebuild dropping the class identity) and every one was
rejected, so no spec hole was found. The last two were then ADDED to the battery
as the rebuild-path rivals, since they closed a real coverage gap. Two correct
reshapes were tried as a SPEC-TOO-STRONG probe; the commuted-routing-guard one
verified and is now shipped as ``pos-guard-disjunction-commuted``. Two false
``refinement`` claims (both asserting that a collection-cloning test would
break, when this instance's test set contains no such test) were corrected in
place.

SECOND AUDIT (independent, after the first). Re-derived rather than re-read.
Statement integrity: the ``theorem correct_duplicate`` statement was extracted
from all 11 case modules and compared byte-for-byte against the frozen file —
all 11 identical. All seven then-shipped reject witnesses were rebuilt on both
sides (rival exit 0, gold exit 1, ``unsolved goals ⊢ False`` in every case), and
each was additionally put through a FORGERY test: the ``¬`` was dropped so the
witness claims gold is WRONG-free at that input, and the flipped file was built
on both sides. Every flip inverted cleanly (gold exit 0, rival exit 1), so each
gold-side exit code demonstrably tracks the claim rather than a fixed syntactic
failure — none of the seven is hollow. The ``admiss-class-valued-param`` ground
``have`` was forged the same way (negated): the module then FAILS with
``unsolved goals ⊢ False``, so the ``have`` is genuinely discharged by evaluation
and is load-bearing, not vacuous.
Seven MORE wrong impls were tried as a SPEC-TOO-WEAK probe, aimed at what the
existing rivals left alone: the configuration KEY dropped on the rebuild; the
rebuild handing back an emptied configuration; routing on ``isBlueprint`` alone
(the opposite disjunct from the pre-fix rival); the no-configuration return
dropping the value's blueprint flag; the safe refusal firing only on a non-empty
configuration (a SUB-DOMAIN near-miss); the rebuild swapping the two observable
flags; and the collection arm not recursing at all. All seven were rejected with
witnesses that discriminate (rival exit 0 / gold exit 1), so no spec hole. An
EIGHTH — the routing guard as an EXCLUSIVE or — was also rejected, but only at an
input no shipped witness used, which is the coverage defect described above; it
is now shipped as ``route-on-exclusive-or``. Two more correct reshapes were tried
as a SPEC-TOO-STRONG probe (the guard by De Morgan, ``!(exposesConfig &&
!isBlueprint)``; the safe decision as a ``match safe with`` instead of an ``if``)
and BOTH verified (exit 0), so the routing and safe-flag clauses are not pinned
to one spelling. No spec hole in either direction.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` leaf and consumes no
``axiom`` (every routing decision is modeled structurally over the value's own
flags). The nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-12585"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positives that
# re-prove, spans the impl edit + the matching proof-body edit) so same_spec
# stays byte-identical. The impl arms are byte-identical to the spec arms, so
# every anchor is pinned on impl-only text (the inline guard, or a multi-line
# block that includes the `implementation_duplicate` recursive call).

# The inline no-configuration guard of the impl (spec uses the `configUnusable`
# helper at this point, so this bare-disjunction line is impl-only and unique).
_I_GUARD = "      if (!exposesConfig) || isBlueprint then"

# The whole no-configuration arm (guard + safe decision + else head) of the impl.
_I_NOCONFIG = (
    "      if (!exposesConfig) || isBlueprint then\n"
    "        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)\n"
    "      else"
)

# The collection arm of the impl (its recursive `implementation_duplicate` call
# makes the block impl-only and unique against the identically-worded spec arm).
_I_GROUP = (
    "      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with\n"
    "      | .error _ => .error ()\n"
    "      | .ok es' => .ok (.group kind es')"
)

# The rebuild arm of the impl: the configuration traversal plus the
# reconstruction. Its recursive `implementation_duplicate` call makes the block
# impl-only and unique against the identically-worded spec arm. This is the arm
# reached ONLY by a realized configuration-exposing node — the rebuild path.
_I_CONFIG = (
    "          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with\n"
    "          | .error _ => .error ()\n"
    "          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')"
)

# The frozen proof preamble (proof region) — anchor for the admissibility have.
_P_PREAMBLE = (
    "  intro safe v\n"
    "  simp only [problem_spec_duplicate]"
)

# The frozen case6/case7 proof bodies (proof region) — the two rebuild-path
# cases, reproven for the commuted-guard positive.
_P_CASE67 = (
    "  · -- case6: node, realized config, mapM = error\n"
    "    rename_i hguard hib a hmap ih\n"
    "    conv_rhs => rw [reproduce]\n"
    "    simp only [configUnusable]\n"
    "    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]\n"
    "  · -- case7: node, realized config, mapM = ok\n"
    "    rename_i hguard hib cfg' hmap ih\n"
    "    conv_rhs => rw [reproduce]\n"
    "    simp only [configUnusable]\n"
    "    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]"
)

# The frozen case3/case4 proof bodies (proof region) — reproven for the
# safe-flipped positive.
_P_CASE34 = (
    "  · -- case3: node, configUnusable, safe = true\n"
    "    rename_i hguard\n"
    "    conv_rhs => rw [reproduce]\n"
    "    simp only [configUnusable, hguard, if_true]\n"
    "  · -- case4: node, configUnusable, safe = false\n"
    "    rename_i hguard hsafe\n"
    "    conv_rhs => rw [reproduce]\n"
    "    simp only [configUnusable, hguard, if_true]\n"
    "    rw [if_neg hsafe]"
)


# Witness tactic blocks shared across cases. The carrier is transparent, so the
# spec predicate reduces to an Except equality by evaluation.
_W_NODE = (
    "  unfold problem_spec_duplicate implementation_duplicate\n"
    "  simp [reproduce, configUnusable]\n"
)
# Collection witnesses reduce the element traversal on BOTH sides (the rival's
# `implementation_duplicate` mapM and the spec's `reproduce` mapM).
_W_GROUP = (
    "  unfold problem_spec_duplicate\n"
    "  rw [implementation_duplicate.eq_def, reproduce.eq_def]\n"
    "  simp [List.attach, List.attachWith, List.mapM, List.mapM.loop, "
    "configUnusable, reproduce, implementation_duplicate]\n"
)
# Rebuild-path witnesses traverse the KEYED configuration, whose element step is
# an `Except.map` over a pair rather than a bare recursive call, so the monadic
# plumbing (`bind`/`pure`/`Except.map`) has to be unfolded too — without it the
# goal stalls on an unreduced `pure []` / `<$>` and the refutation does not
# close (measured: exit 1 with the traversal still symbolic on BOTH sides, which
# is a tactic gap and not a refutation).
_W_CONFIG = (
    "  unfold problem_spec_duplicate\n"
    "  rw [implementation_duplicate.eq_def, reproduce.eq_def]\n"
    "  simp [List.attach, List.attachWith, List.mapM, List.mapM.loop, bind, "
    "Except.bind,\n"
    "    pure, Except.pure, Functor.map, Except.map, configUnusable, reproduce,\n"
    "    implementation_duplicate]\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; nothing is assumed (no new
    # axiom / lemma / sorry). Ports nagini case `pos-control-reordered` (a
    # structurally-different correct impl) onto the single modeled function.
    # =====================================================================
    {
        "id": "pos-safe-branch-flipped",
        "kind": "soundness",
        "expect": "verify",
        # On the no-configuration path, express the safe decision as `if !safe`
        # with the branches swapped. Same result on every input; the two
        # affected proof cases are re-closed by `simp_all` (the branch condition
        # is negated, nothing else changes). A genuine live-path reshape.
        "module": _swap(
            _swap(
                _BASE, _I_NOCONFIG,
                "      if (!exposesConfig) || isBlueprint then\n"
                "        if !safe then .ok (.node isBlueprint exposesConfig tag cfg) else .error ()\n"
                "      else",
            ),
            _P_CASE34,
            "  · -- case3 (reshaped: !safe branch taken, so safe = false)\n"
            "    rename_i hguard hns\n"
            "    conv_rhs => rw [reproduce]\n"
            "    simp only [configUnusable, hguard, if_true]\n"
            "    simp_all\n"
            "  · -- case4 (reshaped: else branch, so safe = true)\n"
            "    rename_i hguard hns\n"
            "    conv_rhs => rw [reproduce]\n"
            "    simp only [configUnusable, hguard, if_true]\n"
            "    simp_all",
        ),
        "rationale": "the safe-flag decision on the no-configuration path is "
                     "reshaped from `if safe then error else ok` to `if !safe "
                     "then ok else error` — a live path both branches reach. The "
                     "result is identical on every input, so `result = <structural "
                     "reproduction> safe v` still holds. Must verify, else the "
                     "no-configuration safe clause is SPEC-TOO-STRONG. Proof: the "
                     "two affected `fun_induction` cases are re-closed by "
                     "`simp_all` (only the branch condition is negated). Ports "
                     "nagini's structural-reshape positive.",
    },
    {
        "id": "pos-blueprint-branch-reshaped",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the (provably unreachable) realized-blueprint inner branch to
        # return the value unchanged instead of a failure. That branch is reached
        # only when the configuration interface is usable AND the value is a
        # blueprint, which is contradictory, so the change is observationally a
        # no-op and the frozen proof (whose matching case closes by
        # contradiction) is retained verbatim.
        #
        # AUDIT NOTE (kept, with its weakness stated). This positive edits a
        # PROVABLY DEAD branch, so it constrains the spec only very weakly: an
        # unreachable branch cannot change any observable, so "it still verifies"
        # is close to guaranteed and is not evidence that a live clause is
        # satisfiable. It is retained because it is the only case that pins the
        # branch as dead (if the spec ever admitted a realized blueprint, this
        # case would start to fail, which is real information), but the
        # SPEC-TOO-STRONG question is carried by the two live-path positives:
        # `pos-safe-branch-flipped` and `pos-guard-disjunction-commuted`.
        "rationale": "the realized-blueprint inner branch (reached only when the "
                     "configuration interface is usable AND the value is a "
                     "blueprint — a contradictory guard) is reshaped to return the "
                     "value unchanged rather than a failure. Since the branch is "
                     "unreachable the observable result is identical on every "
                     "input, so `result = <structural reproduction> safe v` still "
                     "holds. Must verify. Proof: the frozen tactic body is retained "
                     "(its matching case closes by contradiction regardless of the "
                     "branch value). WEAK BY CONSTRUCTION (a dead-branch edit "
                     "cannot change an observable); it pins the branch as dead, "
                     "and the live-path soundness question is carried by "
                     "`pos-safe-branch-flipped` and "
                     "`pos-guard-disjunction-commuted`.",
        "module": _swap(
            _BASE,
            "      else\n"
            "        if isBlueprint then .error ()\n"
            "        else",
            "      else\n"
            "        if isBlueprint then .ok (.node isBlueprint exposesConfig tag cfg)\n"
            "        else",
        ),
    },
    {
        "id": "pos-guard-disjunction-commuted",
        "kind": "soundness",
        "expect": "verify",
        # THE canonical correct-reshape probe for this bundle: commute the two
        # disjuncts of the ROUTING GUARD itself — the exact clause the fix
        # introduces, and the clause every reject rival attacks. `isBlueprint ||
        # (!exposesConfig)` selects the same branch on all four flag
        # combinations as `(!exposesConfig) || isBlueprint`, so this is a
        # faithful correct impl whose syntactic form differs at precisely the
        # discriminating point. If the frozen spec rejected it, the routing
        # clause would be pinned to one spelling of a commutative disjunction
        # rather than to the behavior — SPEC-TOO-STRONG on the fix's own clause.
        #
        # This is the reshape/wrong distinction the witness requirement exists to
        # make: `prepatch-blueprint-misroute` DROPS a disjunct (wrong, refuted at
        # a concrete input) while this one REORDERS the same two disjuncts
        # (correct, and must verify). A spec that could not tell those apart
        # would be attesting to syntax.
        "module": _swap(
            _swap(
                _swap(_BASE, _I_GUARD,
                      "      if isBlueprint || (!exposesConfig) then"),
                _P_CASE34,
                "  · -- case3 (guard commuted: re-orient hguard, then frozen script)\n"
                "    rename_i hguard\n"
                "    rw [Bool.or_comm] at hguard\n"
                "    conv_rhs => rw [reproduce]\n"
                "    simp only [configUnusable, hguard, if_true]\n"
                "  · -- case4 (guard commuted)\n"
                "    rename_i hguard hsafe\n"
                "    rw [Bool.or_comm] at hguard\n"
                "    conv_rhs => rw [reproduce]\n"
                "    simp only [configUnusable, hguard, if_true]\n"
                "    rw [if_neg hsafe]",
            ),
            _P_CASE67,
            "  · -- case6 (guard commuted)\n"
            "    rename_i hguard hib a hmap ih\n"
            "    rw [Bool.or_comm] at hguard\n"
            "    conv_rhs => rw [reproduce]\n"
            "    simp only [configUnusable]\n"
            "    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]\n"
            "  · -- case7 (guard commuted)\n"
            "    rename_i hguard hib cfg' hmap ih\n"
            "    rw [Bool.or_comm] at hguard\n"
            "    conv_rhs => rw [reproduce]\n"
            "    simp only [configUnusable]\n"
            "    rw [if_neg hguard, if_neg hib, ← attach_mapM_fun_eq_config _ ih, hmap]",
        ),
        "rationale": "the ROUTING GUARD's two disjuncts are commuted: "
                     "`isBlueprint || (!exposesConfig)` instead of "
                     "`(!exposesConfig) || isBlueprint`. `||` is commutative on "
                     "`Bool`, so the same branch is selected at all four flag "
                     "combinations and the result is identical on every input — a "
                     "faithful correct impl reshaped at exactly the clause the fix "
                     "introduces and every rival attacks. Must verify, else the "
                     "usable-interface routing clause is SPEC-TOO-STRONG (pinned "
                     "to one spelling of a commutative disjunction rather than to "
                     "the behavior). Proof: each of the four affected "
                     "`fun_induction` cases re-orients its guard hypothesis with "
                     "`Bool.or_comm` and then runs the frozen script verbatim. "
                     "This is the correct-reshape twin of "
                     "`prepatch-blueprint-misroute`, which DROPS a disjunct "
                     "instead of reordering it.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini precondition
    # -admission probe has no binder to attack here; the honest analogue is to
    # discharge the spec predicate by evaluation at the exact F2P scenario — a
    # class-valued (blueprint) parameter that advertises the configuration
    # interface, cloned unsafely (the recursion's flag) — alongside the frozen
    # obligation. Ports nagini case `admiss-class-object-input`.
    # =====================================================================
    {
        "id": "admiss-class-valued-param",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped input (a blueprint exposing
        # the configuration interface, duplicated unsafely) by evaluation as a
        # `have`, then run the frozen proof verbatim. Nothing is assumed: no new
        # declaration, statement byte-identical.
        "module": _swap(
            _BASE, _P_PREAMBLE,
            "  intro safe v\n"
            "  have _ground : problem_spec_duplicate false (.node true true 0 [])\n"
            "      (implementation_duplicate false (.node true true 0 [])) := by\n"
            "    unfold problem_spec_duplicate implementation_duplicate\n"
            "    simp [reproduce, configUnusable]\n"
            "  simp only [problem_spec_duplicate]",
        ),
        "rationale": "the obligation is discharged at the F2P-shaped input — a "
                     "blueprint value that advertises the configuration interface "
                     "(the routing the fix corrects), duplicated with the "
                     "recursion's unsafe flag — by evaluation, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior is unsatisfiable at exactly the input the F2P "
                     "exercises — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body. Ports nagini's class-object "
                     "admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input,
    # checked to hold of the rival and fail on the frozen solution.
    # =====================================================================

    # ---- the fix itself: usable-interface routing (nagini `prepatch-class-misroute`) ----
    {
        "id": "prepatch-blueprint-misroute",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: the no-configuration routing condition tests only
        # whether the value exposes the interface, dropping the is-blueprint
        # disjunct. A blueprint that advertises the interface then falls through
        # to the rebuild path (and, being a blueprint, fails there).
        "module": _swap(_BASE, _I_GUARD, "      if (!exposesConfig) then"),
        "refinement": "this IS the pre-fix behavior: routing on advertisement "
                      "alone. A class-valued parameter (a blueprint that advertises "
                      "the configuration interface) is sent to the rebuild path, "
                      "which queries the interface — not usable on a blueprint — and "
                      "raises. That is the exact F2P failure (the class-valued "
                      "parameter cloned during the recursive descent); the F2P test "
                      "asserts the clone succeeds and returns the class unchanged, "
                      "so the faithful real patch would NOT resolve.",
        "rationale": "REJECT from the usable-interface routing clause (the fix): "
                     "for a blueprint exposing the interface under the unsafe flag "
                     "the spec routes to the no-configuration path and returns the "
                     "value unchanged (`.ok`), while the rival falls to the rebuild "
                     "path and fails (`.error`), so the outcome constructor itself "
                     "differs. Binder spread: safe=false, a node with "
                     "isBlueprint=true, exposesConfig=true.",
        "witness": (
            "-- Refuted at the F2P input: a blueprint advertising the interface,\n"
            "-- duplicated unsafely. Fully concrete (transparent carrier), reduces\n"
            "-- by evaluation; the outcomes are `.ok`/`.error` distinct.\n"
            "example : ¬ problem_spec_duplicate false (.node true true 0 [])\n"
            "    (implementation_duplicate false (.node true true 0 [])) := by\n"
            + _W_NODE
        ),
    },

    # ---- the routing guard is an INCLUSIVE disjunction, not an exclusive one ----
    #
    # ADDED BY THE SECOND AUDIT, closing a measured coverage defect rather than a
    # hypothetical one. Every other rival in this battery is refuted at an input
    # where the two disjuncts of the routing guard disagree, so all of them are
    # blind to how the guard behaves when BOTH are true. The four realizable flag
    # combinations reach that point only at (isBlueprint=true,
    # exposesConfig=false) — a value that IS a blueprint and also exposes no
    # configuration interface at all — and no shipped witness used
    # it. Measured consequence: this xor rival agreed with the frozen impl at all
    # seven of the previously-shipped witness inputs, so the battery as it stood
    # could not refute it, while the docstring claimed all four combinations were
    # covered. The claim was corrected and this case landed.
    {
        "id": "route-on-exclusive-or",
        "kind": "uniqueness",
        "expect": "reject",
        # Route on an EXCLUSIVE or: a value takes the no-configuration path iff
        # exactly one of "exposes nothing" / "is a blueprint" holds. Agrees with
        # the spec on three of the four flag combinations and diverges on the
        # fourth, where both disjuncts hold and the exclusive form falls through
        # to the rebuild path instead.
        "module": _swap(_BASE, _I_GUARD,
                        "      if ((!exposesConfig) != isBlueprint) then"),
        "refinement": "a faithful real patch reading the routing condition as "
                      "an exclusive choice — treating a value as configurable "
                      "again precisely when it BOTH exposes no configuration "
                      "interface AND is a blueprint — would send a "
                      "non-configurable class down the rebuild path and query a "
                      "configuration interface that value does not even "
                      "advertise. The narrow F2P scenario is a blueprint that "
                      "DOES advertise the interface, so this rival happens to "
                      "route that one input correctly and the F2P would still "
                      "pass; the would-not-resolve claim is therefore NOT made "
                      "for this rival. What it violates is the documented "
                      "contract, which specifies the no-configuration path for "
                      "every value that exposes no usable configuration "
                      "interface — a condition satisfied by a value that fails "
                      "BOTH ways at once, not just by one that fails exactly "
                      "one way. Kept as a spec-strength (uniqueness) rival on "
                      "that basis: it pins the guard as an INCLUSIVE "
                      "disjunction, which is the shape the spec genuinely "
                      "asserts and which no other rival in this battery "
                      "distinguishes.",
        "rationale": "REJECT from the usable-interface routing clause, at the "
                     "one point that separates an inclusive disjunction from an "
                     "exclusive one: for a value that is a blueprint AND exposes "
                     "no configuration interface, under the unsafe flag, the "
                     "spec routes to the no-configuration path and returns the "
                     "value unchanged (`.ok`), while the rival's exclusive guard "
                     "is false there, so it falls to the rebuild path and fails "
                     "(`.error`). Binder spread: safe=false, and the FOURTH "
                     "realizable (isBlueprint, exposesConfig) combination "
                     "(true, false) — the only combination where both disjuncts "
                     "hold, and the one no other witness in this battery "
                     "reaches.",
        "witness": (
            "-- Refuted where BOTH disjuncts of the routing guard hold: a value\n"
            "-- that is a blueprint AND exposes no configuration interface,\n"
            "-- duplicated unsafely. The spec returns it unchanged; an exclusive\n"
            "-- guard sends it to the rebuild path, which fails.\n"
            "example : ¬ problem_spec_duplicate false (.node true false 0 [])\n"
            "    (implementation_duplicate false (.node true false 0 [])) := by\n"
            + _W_NODE
        ),
    },

    # ---- drop the safe refusal (nagini `no-refuse-on-forbidden-leaf`) ----
    {
        "id": "no-refuse-config-unusable",
        "kind": "uniqueness",
        "expect": "reject",
        # Never report a failure on the no-configuration path: return the value
        # unchanged regardless of the safe flag. On a configuration-unusable value
        # under the safe flag the spec MUST report a failure; this returns it.
        "module": _swap(
            _BASE, _I_NOCONFIG,
            "      if (!exposesConfig) || isBlueprint then\n"
            "        .ok (.node isBlueprint exposesConfig tag cfg)\n"
            "      else",
        ),
        "refinement": "removing the safe-mode refusal makes duplication return a "
                      "non-configurable value unchanged under the safe flag instead "
                      "of reporting the failure the caller demanded. The faithful "
                      "real patch would silently accept a value it must reject under "
                      "safe mode, breaking the P2P safe-mode contract (a "
                      "non-configurable value under safe mode must be reported, not "
                      "returned). It would NOT resolve.",
        "rationale": "REJECT from the no-configuration safe-flag clause: for a "
                     "configuration-unusable value (exposes nothing) under the safe "
                     "flag the spec yields `.error` and the rival yields `.ok`, so "
                     "`result` differs. Binder spread: safe=true (the only rival at "
                     "this setting on a node), a plain leaf "
                     "(isBlueprint=false, exposesConfig=false).",
        "witness": (
            "example : ¬ problem_spec_duplicate true (.node false false 0 [])\n"
            "    (implementation_duplicate true (.node false false 0 [])) := by\n"
            + _W_NODE
        ),
    },

    # ---- the no-configuration unchanged-return decision (carrier-specific) ----
    {
        "id": "noconfig-returns-error",
        "kind": "uniqueness",
        "expect": "reject",
        # On the no-configuration path, report a failure even in the unsafe
        # regime, where the value must be returned unchanged.
        "module": _swap(
            _BASE, _I_NOCONFIG,
            "      if (!exposesConfig) || isBlueprint then\n"
            "        if safe then .error () else .error ()\n"
            "      else",
        ),
        "refinement": "reporting a failure for a non-configurable value even in "
                      "the unsafe regime would make the recursive (unsafe) descent "
                      "fail on any leaf or class-valued parameter, so cloning any "
                      "container of such parameters would fail. The unsafe regime "
                      "exists precisely to return those values unchanged, so the "
                      "faithful real patch would NOT resolve (it breaks the "
                      "recursion the F2P scenario depends on).",
        "rationale": "REJECT from the no-configuration unsafe-return clause: for a "
                     "configuration-unusable value under the unsafe flag the spec "
                     "returns it unchanged (`.ok`) and the rival reports a failure "
                     "(`.error`), so the outcome constructor differs. Binder "
                     "spread: safe=false, a plain leaf. Distinct input from the "
                     "refusal rival (which holds safe=true), so each probes its own "
                     "point of the safe binder.",
        "witness": (
            "example : ¬ problem_spec_duplicate false (.node false false 0 [])\n"
            "    (implementation_duplicate false (.node false false 0 [])) := by\n"
            + _W_NODE
        ),
    },

    # ---- collection failure-propagation (carrier-specific; nagini's flat record had no collection) ----
    {
        "id": "group-error-not-propagated",
        "kind": "uniqueness",
        "expect": "reject",
        # When an element of a collection fails, do NOT propagate the failure:
        # return a successful (empty) collection instead.
        "module": _swap(
            _BASE, _I_GROUP,
            "      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with\n"
            "      | .error _ => .ok (.group kind [])\n"
            "      | .ok es' => .ok (.group kind es')",
        ),
        # AUDIT CORRECTION. The previous refinement claimed "the tests that a
        # collection of non-duplicable elements is reported (not silently
        # truncated) would break". That claim was FALSE for this instance: no
        # F2P or P2P test in this instance's test set passes a collection to the
        # modeled function at all (every call site hands it a single value), so
        # no named test constrains this branch. The honest refinement is a
        # documented-contract argument, not a test-breakage argument, and it is
        # stated as such below.
        "refinement": "NOT witnessed by a named test in this instance's test set "
                      "— no F2P or P2P case here passes a collection to the "
                      "modeled function, so this rival's faithful real patch "
                      "would not be caught by THIS instance's tests and the "
                      "would-not-resolve claim is NOT made. What it does violate "
                      "is the documented contract of the modeled behavior: the "
                      "collection branch is specified to duplicate every element "
                      "and to fail as a whole when an element cannot be "
                      "duplicated, so swallowing an element failure and handing "
                      "back a truncated collection silently loses elements the "
                      "caller asked for. Kept as a spec-strength (uniqueness) "
                      "rival on that basis: it pins a clause the spec really "
                      "asserts, which is what the reject lane certifies. The "
                      "resolve-linked rivals are the three `node` cases above, "
                      "whose refinements do name real tests.",
        "rationale": "REJECT from the collection failure-propagation clause: a "
                     "collection with a failing element under the safe flag must "
                     "fail as a whole (`.error`); the rival returns `.ok` of an "
                     "empty collection, so the outcome constructor differs. Binder "
                     "spread: safe=true, v a `group` (kind 3) whose single element "
                     "is a configuration-unusable value that fails under safe mode "
                     "— moves v off `node` onto the collection shape.",
        "witness": (
            "example : ¬ problem_spec_duplicate true (.group 3 [.node false false 0 []])\n"
            "    (implementation_duplicate true (.group 3 [.node false false 0 []])) := by\n"
            + _W_GROUP
        ),
    },

    # ---- collection kind preservation (carrier-specific) ----
    {
        "id": "group-kind-not-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        # Rebuild a duplicated collection with a hardcoded kind instead of the
        # input's kind.
        "module": _swap(
            _BASE, _I_GROUP,
            "      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with\n"
            "      | .error _ => .error ()\n"
            "      | .ok es' => .ok (.group 0 es')",
        ),
        # AUDIT CORRECTION. The previous refinement claimed "the tests that a
        # cloned collection has the same type as its source would break". That
        # claim was FALSE for this instance: no test here clones a collection, so
        # no such test exists to break. Restated as a contract argument.
        "refinement": "NOT witnessed by a named test in this instance's test set "
                      "— no F2P or P2P case here clones a collection, so the "
                      "would-not-resolve claim is NOT made for this rival. What it "
                      "violates is the documented contract: the collection variety "
                      "is specified to be preserved across duplication, so "
                      "rebuilding every collection as one fixed variety changes "
                      "the container type of the duplicate and a caller that "
                      "duplicates a collection gets back a different kind of "
                      "collection than it supplied. Kept as a spec-strength "
                      "(uniqueness) rival on that basis — it pins the "
                      "kind-preservation clause the spec genuinely asserts.",
        "rationale": "REJECT from the collection kind-preservation clause: the "
                     "spec rebuilds the collection with the input `kind`, the rival "
                     "hardcodes kind 0, so for a non-zero kind `result` differs. "
                     "Binder spread: safe=false, v a `group` with kind 7 (moved off "
                     "the value the rival hardcodes) and a succeeding element, so "
                     "the divergence is in the kind field alone.",
        "witness": (
            "example : ¬ problem_spec_duplicate false (.group 7 [.node true true 0 []])\n"
            "    (implementation_duplicate false (.group 7 [.node true true 0 []])) := by\n"
            + _W_GROUP
        ),
    },

    # =====================================================================
    # REBUILD-PATH rivals (added by the adversarial audit).
    #
    # GAP THESE CLOSE. Every rival above attacks either the no-configuration
    # path or the collection arm. None of them puts a REALIZED
    # configuration-exposing node (`isBlueprint=false, exposesConfig=true`) at
    # the top of the input, so the third arm of the modeled behavior — read the
    # configuration, duplicate each entry, rebuild — was entirely unprobed, and
    # so was the flag combination that corresponds to the most ordinary value in
    # the domain. Concretely unpinned before these two: whether the rebuild
    # carries the value's class identity through, and whether the configuration
    # recursion is performed with the UNSAFE flag (the clause that makes the
    # whole fix reachable — the recursive descent is where a configuration entry
    # that is itself a blueprint gets duplicated). A spec that left either
    # unpinned would admit a wrong impl, so both are checked rather than assumed.
    # =====================================================================

    # ---- the rebuild must carry the value's class identity through ----
    {
        "id": "rebuild-drops-tag",
        "kind": "uniqueness",
        "expect": "reject",
        # Rebuild a realized configuration-exposing node under a hardcoded class
        # identity instead of the input's own.
        "module": _swap(
            _BASE, _I_CONFIG,
            "          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with\n"
            "          | .error _ => .error ()\n"
            "          | .ok cfg' => .ok (.node isBlueprint exposesConfig 0 cfg')",
        ),
        "refinement": "a faithful real patch that reconstructed every "
                      "configurable value under one fixed class identity, rather "
                      "than the source value's own, would hand back a duplicate "
                      "that is not of the source's type at all. Every P2P case "
                      "that duplicates a configurable value and then compares the "
                      "duplicate's configuration against the source's would break "
                      "(the reconstruction would be built from the wrong class), "
                      "so it would NOT resolve.",
        "rationale": "REJECT from the rebuild clause: the spec rebuilds the value "
                     "under its own class identity `tag`, the rival hardcodes 0, so "
                     "for a value whose identity is non-zero `result` differs in "
                     "that field. Binder spread: FIRST case to place a realized "
                     "configuration-exposing node (isBlueprint=false, "
                     "exposesConfig=true) at the top of the input — the rebuild "
                     "path, and the fourth flag combination, both otherwise "
                     "unprobed; safe=false, class identity 9 (moved off the value "
                     "the rival hardcodes) with an empty configuration, so the "
                     "divergence is in the identity field alone.",
        "witness": (
            "-- The rebuild path at a realized configuration-exposing node: the\n"
            "-- duplicate must carry class identity 9, the rival emits 0.\n"
            "example : ¬ problem_spec_duplicate false (.node false true 9 [])\n"
            "    (implementation_duplicate false (.node false true 9 [])) := by\n"
            + _W_CONFIG
        ),
    },

    # ---- the configuration recursion must be UNSAFE ----
    {
        "id": "config-recursion-inherits-safe",
        "kind": "uniqueness",
        "expect": "reject",
        # Duplicate each configuration entry with the CALLER's safe flag instead
        # of unconditionally unsafely. Under the safe flag a configuration entry
        # that has no usable configuration interface then fails, so the whole
        # rebuild fails where the spec succeeds.
        "module": _swap(
            _BASE, _I_CONFIG,
            "          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate safe kv.2).map (fun v => (kv.1, v))) with\n"
            "          | .error _ => .error ()\n"
            "          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')",
        ),
        "refinement": "this is the clause that makes the fix REACHABLE, so its "
                      "loss is the more damaging near-miss of the two. The "
                      "configuration entries of a value are specified to be "
                      "duplicated in the unsafe regime — that is precisely why an "
                      "entry with no usable configuration interface is returned "
                      "unchanged rather than reported. A faithful real patch that "
                      "propagated the caller's flag into the descent instead would "
                      "make duplication of any ordinary configurable value fail as "
                      "soon as one of its configuration entries is a plain "
                      "non-configurable value — which is the common case, and "
                      "exactly what the F2P scenario duplicates. It would NOT "
                      "resolve, and it would break the P2P cases that duplicate a "
                      "configurable value carrying plain configuration entries.",
        "rationale": "REJECT from the unsafe-descent clause of the rebuild: for a "
                     "realized configuration-exposing node whose single "
                     "configuration entry has no usable configuration interface, "
                     "duplicated under the SAFE flag, the spec duplicates that "
                     "entry unsafely and succeeds (`.ok`) while the rival "
                     "propagates the safe flag, so the entry is reported as a "
                     "failure and the whole rebuild fails (`.error`) — the outcome "
                     "constructor itself differs. Binder spread: safe=true on the "
                     "rebuild path (no other case reaches the rebuild arm at all, "
                     "and none combines safe=true with a non-empty configuration).",
        "witness": (
            "-- A realized configuration-exposing node whose one configuration\n"
            "-- entry has no usable interface, duplicated under the SAFE flag:\n"
            "-- the spec descends UNSAFELY and succeeds; inheriting `safe` fails.\n"
            "example : ¬ problem_spec_duplicate true (.node false true 9 [(1, .node false false 0 [])])\n"
            "    (implementation_duplicate true (.node false true 9 [(1, .node false false 0 [])])) := by\n"
            + _W_CONFIG
        ),
    },
]

# No AXIOM lane here: the bundle declares no `opaque` leaf and consumes no
# `axiom` (every routing decision is modeled structurally over the value's own
# flags). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
