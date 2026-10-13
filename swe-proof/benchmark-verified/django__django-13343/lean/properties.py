# properties.py — G-PBT falsification battery for django__django-13343 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only
# the impl region — and, where a positive reproves, the proof body — is edited),
# checked by variant_scope + the real Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to
# the postcondition and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# ---------------------------------------------------------------------------
# Defended surface (read from Solution.lean / mapping.md)
# ---------------------------------------------------------------------------
# Two obligations, forming a producer -> consumer chain over the same carrier.
#
#   problem_spec_initStorage (defaultStorage : StorageInst) (arg : StorageArg)
#                            (result : FieldState)
#     A three-way case on the argument shape, each arm pinning BOTH components of
#     the resulting state (so no component is left unconstrained — the analogue of
#     the frame obligation on a referentially transparent carrier):
#       (a1) .useDefault  => result.storage = defaultStorage ∧ callable slot none
#       (a2) .inst s      => result.storage = s              ∧ callable slot none
#       (a3) .callable c  => result.storage = c.result       ∧ callable slot some c
#     Note (a3) pins the retained value to c ITSELF (identity `Callable.id`), not
#     merely to something callable-shaped, and pins the resolved instance to the
#     value the argument PRODUCES (`c.result`), not to the argument's own identity.
#
#   problem_spec_deconstructStorage (defaultStorage : StorageInst)
#                                   (state : FieldState)
#                                   (result : Option DeconstructStorage)
#     A guard plus a two-arm choice:
#       (b1) state.storage = defaultStorage        => result = none  (omission)
#       (b2) otherwise, retained slot = some c     => result = some (.callable c)
#       (b3) otherwise, retained slot = none       => result = some (.inst storage)
#
# The oracles are GROUNDED: every clause relates the result to the actual input
# components (`arg`'s payload, `state.storage`, `state.storageCallable`), never to
# an opaque answer-key. There is no `opaque` callee and no axiom anywhere in this
# bundle, so the whole carrier is transparent and `decide` computes both predicates
# at any literal input — no witness needs to condition on the carrier, and none of
# them binds anything (so none can be `witness-inconsistent`).
#
# CARRIER NOTE. The nagini sibling modeled the same two behaviors as a MUTATING
# procedure over a heap object (`configure` writing `field.{store,has_producer,
# producer_id}` under full permission) plus a read-only query (`describe_store`
# holding those fields at 1/2 permission). This backend models them as two total
# functions over immutable values: `StorageArg` (the three argument shapes),
# `FieldState` (the resolved instance + the optional retained value) and
# `Option DeconstructStorage` (key-absent / retained-value / resolved-instance).
# Every nagini POSTCONDITION clause therefore has a direct counterpart here:
#   nagini (c1)/(c2)/(c2')  ->  the callable-slot half of (a1)/(a2)/(a3)
#   nagini (c3)             ->  the storage half of (a1)/(a2)/(a3)
#   nagini (d1)             ->  (b1)
#   nagini (d2)             ->  (b2)
#   nagini (d3)             ->  (b3)
# and each is refutable at a concrete literal input.
#
# ---------------------------------------------------------------------------
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload)
# ---------------------------------------------------------------------------
#   * FRAME-MUTATION (nagini's two mandatory cases, `frame-mutate-store` and
#     `frame-mutate-producer-id`, which wrote to a field held at Acc(...,1/2) and
#     were rejected by the PERMISSION SYSTEM before any postcondition was read).
#     Lean is referentially transparent — no heap, no aliasing, no fractional
#     permission — so "write to a read-only input" is not expressible and the whole
#     class is VACUOUS here. What survives of the argument is the dead-state half:
#     the nagini spec had to add clause (c2') to stop a wrong impl scribbling on a
#     slot it should have left alone, and that clause's counterpart here is the
#     "callable slot = none" half of (a1)/(a2). BOTH halves are attacked, by
#     `weak-instance-arm-retains-spurious-callable` (the (a2) half) and
#     `weak-default-arm-retains-spurious-callable` (the (a1) half).
#   * DIVERGENCE / NON-TERMINATION. Genuinely vacuous on lean: both
#     `implementation_*` are total Lean `def`s (one `Id.run do`, one pattern
#     match), so a non-terminating implementation cannot be written at all. This is
#     NOT the velvet situation described in the corpus-wide termination-semantics finding, where a
#     `partial`-semantics bundle ADMITS a diverging rival and the class is a known
#     spec hole; here the carrier forecloses it. The nagini sibling carries no
#     divergence case either.
#   * ADMISSIBILITY. It is true that both lean obligations are closed universal
#     statements over their full input type with NO precondition hypothesis, so
#     there is no `Requires` clause that could literally be over-strong. That is
#     NOT on its own a reason to drop the lane: on a TOTAL carrier the analogue of
#     PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which a positive that discharges it at that concrete input
#     — by evaluation, as a `have`, before closing the frozen obligation verbatim —
#     tests directly. So the lane IS ported, as
#     `admiss-composed-f2p-roundtrip` below, over the COMPOSED chain (resolve then
#     serialize) at a callable argument whose produced instance differs from the
#     project default. (The nagini `evaluated != given` precondition correspondingly
#     has no counterpart: this carrier admits a self-producing argument, and the
#     battery deliberately probes one — see `weak-callable-arm-retains-nothing`.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. There is
#     no consumed axiom to test anyway (both behaviors are modeled deeply).
from pathlib import Path

INSTANCE = "django__django-13343"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Impl/proof-region anchors. Each lies ENTIRELY inside an impl-start/impl-end
# (or proof-start/proof-end) span and is unique in the file, so every variant
# provably edits only the intended region and the manifest breaks loudly if the
# frozen solution ever changes.
# ===========================================================================

# --- initStorage: one anchor per arm of the three-way case on the argument.
_A_DEFAULT_ARM = "  | .useDefault => pure ()\n"
_A_INST_ARM = "  | .inst s => storage := s\n"
_A_RETAIN = "      storageCallable := some c\n"
_A_RESOLVE = "      storage := c.result\n"

# The whole initStorage definition (signature + body), for the positive that
# reshapes it into a pure functional match.
_A_DEF = """def implementation_initStorage (defaultStorage : StorageInst) (arg : StorageArg) :
    FieldState := Id.run do
  -- self.storage = storage or default_storage
  let mut storage : StorageInst := defaultStorage
  let mut storageCallable : Option Callable := none
  match arg with
  | .useDefault => pure ()
  | .inst s => storage := s
  | .callable c =>
      -- callable branch: retain the original callable, then evaluate it
      storageCallable := some c
      storage := c.result
  return { storage := storage, storageCallable := storageCallable }"""

# --- deconstructStorage: the two-arm choice, and the whole body.
_B_EMIT = """    result := some (match state.storageCallable with
                    | some c => .callable c
                    | none   => .inst state.storage)
"""
_B_BODY = """  let mut result : Option DeconstructStorage := none
  if state.storage ≠ defaultStorage then
    -- getattr(self, retained-callable, resolved-instance)
    result := some (match state.storageCallable with
                    | some c => .callable c
                    | none   => .inst state.storage)
  return result"""

# --- the frozen proof body of correct_deconstructStorage (tactic lines only).
_B_PROOF = """  intro defaultStorage state
  unfold problem_spec_deconstructStorage implementation_deconstructStorage
  by_cases h : state.storage = defaultStorage
  · rw [if_pos h]
    simp only [Id.run, ne_eq, h, not_true, if_false]
    rfl
  · rw [if_neg h]
    simp only [Id.run, ne_eq, h, not_false_iff, if_true]
    rfl"""

for _a in (_A_DEFAULT_ARM, _A_INST_ARM, _A_RETAIN, _A_RESOLVE, _A_DEF,
           _B_EMIT, _B_BODY, _B_PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted or not unique: {_a[:60]!r}")


# ===========================================================================
# Witness builders. Both spec predicates are total and transparent, so a
# refutation is just `¬ problem_spec_X <literal inputs> (implementation_X <same>)`
# closed by `decide` after unfolding. It ELABORATES against a rival that diverges
# from the frozen verdict at that input and FAILS on gold, which satisfies both
# predicates at every input. No hypothesis is bound, so there is nothing that
# could be jointly unsatisfiable.
# ===========================================================================

def _w_init(default_storage, arg, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_initStorage {default_storage} {arg}\n"
        f"    (implementation_initStorage {default_storage} {arg}) := by\n"
        f"  unfold problem_spec_initStorage implementation_initStorage\n"
        f"  decide")


def _w_deconstruct(default_storage, state, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_deconstructStorage {default_storage} {state}\n"
        f"    (implementation_deconstructStorage {default_storage} {state}) := by\n"
        f"  unfold problem_spec_deconstructStorage implementation_deconstructStorage\n"
        f"  decide")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# (P1) deconstructStorage, restructured: an early return on the omission guard
# with the POSITIVE test (`= defaultStorage`) instead of the negated one, and the
# two-arm choice lifted out of the `some (...)` scrutinee into two returning
# match arms. Behaviourally identical on every input; only the branch FORM
# changes — a shape a faithful realization could equally take. The frozen tactic
# script is tuned to the accumulator shape (`rw [if_pos h]` then `rfl` through the
# `Id.run` join point) and no longer closes, so the proof body is HONESTLY
# re-closed: the `theorem correct_deconstructStorage` STATEMENT is byte-identical
# and no axiom / lemma / sorry / native_decide is introduced.
_POS_DECONSTRUCT_RESHAPED = _swap(
    _swap(
        _BASE, _B_BODY,
        """  if state.storage = defaultStorage then
    return none
  match state.storageCallable with
  | some c => return some (.callable c)
  | none   => return some (.inst state.storage)"""),
    _B_PROOF,
    """  intro defaultStorage state
  unfold problem_spec_deconstructStorage implementation_deconstructStorage
  by_cases h : state.storage = defaultStorage
  · simp only [Id.run, h, if_pos, if_true]
    rfl
  · rw [if_neg h]
    simp only [Id.run, h, if_false]
    cases state.storageCallable <;> rfl""")

# (P2) initStorage, restructured: the accumulate-then-return shape replaced by a
# direct pure match building each arm's state in one shot (no mutable locals, no
# `Id.run do`, arms in the same order). Behaviourally identical; this is the
# functional counterpart of nagini's `pos-control-configure-reshaped`, which set
# every field exactly once inside its own branch. The frozen `cases arg <;> exact
# ⟨rfl, rfl⟩` proof still closes verbatim, so nothing is reproved here.
_POS_INIT_DIRECT_MATCH = _swap(
    _BASE, _A_DEF,
    """def implementation_initStorage (defaultStorage : StorageInst) (arg : StorageArg) :
    FieldState :=
  match arg with
  | .useDefault => { storage := defaultStorage, storageCallable := none }
  | .inst s     => { storage := s,              storageCallable := none }
  | .callable c => { storage := c.result,       storageCallable := some c }""")

# (P3) ADMISSIBILITY. The total-carrier analogue of PRECOND-TOO-STRONG: not "is
# some precondition too strong" (there is no precondition to be strong) but "is
# the obligation SATISFIABLE at exactly an F2P-shaped input". The `have`s below
# discharge the serialization obligation, and pin the composed round-trip, at the
# input the F2P is about — a field configured with a callable argument whose
# produced instance is not the project default — BY EVALUATION, before the frozen
# obligation is closed verbatim afterwards. Nothing is assumed: no new
# declaration, no axiom/sorry, the `theorem correct_deconstructStorage` statement
# is byte-identical, and the frozen tactic body still follows the inserted `have`s.
# If either `have` failed, the modeled behavior would be unsatisfiable at a normal
# input and the whole obligation would be vacuous there.
# Load-bearing, not a tautology (measured by this audit): changing the pinned
# round-trip value from `some (.callable {id := 3, result := 7})` to
# `some (.inst 7)` makes the case FAIL to build (exit 1), so the `have` really
# does compute the retained callable's survival rather than restating something
# any value would satisfy.
_ADMISS_COMPOSED = _swap(
    _BASE, _B_PROOF,
    """  -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped input --
  -- a field configured with a callable argument whose produced instance differs
  -- from the project default. Discharged by evaluation over the COMPOSED chain
  -- (resolve, then serialize) before the frozen obligation is closed verbatim.
  have _ground : problem_spec_deconstructStorage 0
      (implementation_initStorage 0 (.callable { id := 3, result := 7 }))
      (implementation_deconstructStorage 0
        (implementation_initStorage 0 (.callable { id := 3, result := 7 }))) := by
    unfold problem_spec_deconstructStorage implementation_deconstructStorage
      implementation_initStorage
    decide
  -- and the composed round-trip really does carry the ORIGINAL callable through:
  have _roundtrip : implementation_deconstructStorage 0
      (implementation_initStorage 0 (.callable { id := 3, result := 7 }))
      = some (.callable { id := 3, result := 7 }) := by
    unfold implementation_deconstructStorage implementation_initStorage
    decide
""" + _B_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the
# frozen spec exactly, edits only the impl region, and leaves the frozen proof
# body in place (that proof will not close for the reshaped impl, which is why the
# rejection alone proves nothing and each case ships a witness instead).
# ===========================================================================

# --- behavior B: serialization ------------------------------------------------

# (B/1) The literal pre-image of the serialization behavior: the resolved instance
# is echoed unconditionally, so a retained value never survives.
_WEAK_IGNORE_RETAINED = _swap(_BASE, _B_EMIT,
                              "    result := some (.inst state.storage)\n")

# (B/2) NEAR-MISS on the same clause: the retained value is honoured only when the
# instance it produces DIFFERS from the resolved instance. Agrees with gold
# wherever they differ; wrong exactly where they coincide — which, since the
# resolution step sets the resolved instance TO the produced one, is every state
# the producer can actually build.
_WEAK_RETAIN_ONLY_IF_DISTINCT = _swap(
    _BASE, _B_EMIT,
    "    result := some (match state.storageCallable with\n"
    "                    | some c =>\n"
    "                        if c.result = state.storage then .inst state.storage"
    " else .callable c\n"
    "                    | none   => .inst state.storage)\n")

# (B/3) Wrong on the no-retained-value sub-domain: emits the project default in
# place of the resolved instance.
_WEAK_NO_RETAINED_EMITS_DEFAULT = _swap(
    _BASE, _B_EMIT,
    "    result := some (match state.storageCallable with\n"
    "                    | some c => .callable c\n"
    "                    | none   => .inst defaultStorage)\n")

# (B/4) The omission guard is dropped: a value is always emitted, even when the
# resolved instance IS the project default.
_WEAK_NO_OMISSION = _swap(
    _BASE, _B_BODY,
    "  let mut result : Option DeconstructStorage := none\n"
    "  result := some (match state.storageCallable with\n"
    "                  | some c => .callable c\n"
    "                  | none   => .inst state.storage)\n"
    "  return result")

# --- behavior A: construction-time resolution ---------------------------------

# (A/1) The literal pre-image of the resolution behavior: the callable arm
# evaluates the argument to the runtime instance but retains NOTHING.
_WEAK_RETAIN_NOTHING = _swap(_BASE, _A_RETAIN, "")

# (A/2) NEAR-MISS on the same clause: something IS retained, but its identity is
# the evaluated instance rather than the argument's own. Indistinguishable from
# gold whenever the argument's identity coincides with what it produces; wrong
# whenever they differ.
_WEAK_RETAIN_EVALUATED_IDENTITY = _swap(
    _BASE, _A_RETAIN,
    "      storageCallable := some { c with id := c.result }\n")

# (A/3) The callable arm resolves to the argument's OWN identity instead of the
# instance it produces — the evaluation step is skipped.
_WEAK_RESOLVE_TO_ARGUMENT = _swap(_BASE, _A_RESOLVE, "      storage := c.id\n")

# (A/4) Dead-state corruption on the direct-instance arm: a spurious retained
# value is recorded even though no callable was supplied. This is the counterpart
# of nagini's atk_7 / clause (c2') case.
_WEAK_INST_ARM_RETAINS = _swap(
    _BASE, _A_INST_ARM,
    "  | .inst s =>\n"
    "      storage := s\n"
    "      storageCallable := some { id := s + 1, result := s }\n")

# (A/5) The direct-instance arm ignores the supplied instance and keeps the
# project default.
_WEAK_INST_ARM_IGNORED = _swap(_BASE, _A_INST_ARM, "  | .inst _ => pure ()\n")

# (A/6) The absent-argument arm resolves to something that is not the project
# default.
_WEAK_DEFAULT_ARM_OFF = _swap(
    _BASE, _A_DEFAULT_ARM,
    "  | .useDefault => storage := defaultStorage + 1\n")

# (A/7) Dead-state corruption on the ABSENT-argument arm: the resolved instance is
# right, but a spurious retained value is recorded even though no argument at all
# was supplied. The (a1) "retains no callable" half is a distinct conjunct from the
# (a2) one attacked by A/4 — an impl can get one right and the other wrong — so it
# needs its own rival. Added by audit: the shipped battery attacked the resolution
# half of (a1) (A/6) and the retention half of (a2) (A/4), but nothing moved the
# retention half of (a1).
_WEAK_DEFAULT_ARM_RETAINS = _swap(
    _BASE, _A_DEFAULT_ARM,
    "  | .useDefault =>\n"
    "      storageCallable := some { id := defaultStorage + 1,"
    " result := defaultStorage }\n")


SPEC_TESTS = [

    # -------------------------------------------------------------------
    # POSITIVE CONTROLS
    # -------------------------------------------------------------------
    {
        "id": "pos-deconstruct-reshaped-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DECONSTRUCT_RESHAPED,
        "rationale": (
            "structurally different but CORRECT: the omission guard is tested "
            "POSITIVELY with an early return, and the two-arm choice becomes two "
            "returning match arms instead of a scrutinee inside `some (...)`. The "
            "verdict is identical on every (defaultStorage, state) pair — only the "
            "branch form changes. The frozen tactic script is tuned to the "
            "accumulator shape and no longer closes, so the proof body is honestly "
            "re-closed with the same by_cases/simp/rfl vocabulary; the `theorem "
            "correct_deconstructStorage` statement is byte-identical and no axiom, "
            "lemma, sorry or native_decide is introduced. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition would be over-fit to one branch "
            "order rather than pinning behavior). Ports nagini's "
            "pos-control-describe-reordered."
        ),
    },
    {
        "id": "pos-init-direct-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INIT_DIRECT_MATCH,
        "rationale": (
            "structurally different but CORRECT: the accumulate-into-locals shape "
            "is replaced by a direct pure match that builds each arm's state in one "
            "shot — every component assigned exactly once inside its own arm, arms "
            "in the same order. Behaviourally identical on every (defaultStorage, "
            "arg) pair, and the frozen `cases arg <;> exact ⟨rfl, rfl⟩` closes it "
            "verbatim, so nothing is reproved and no obligation is weakened. If it "
            "FAILS => SPEC-TOO-STRONG. Ports nagini's "
            "pos-control-configure-reshaped."
        ),
    },

    # -------------------------------------------------------------------
    # ADMISSIBILITY
    # -------------------------------------------------------------------
    {
        "id": "admiss-composed-f2p-roundtrip",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_COMPOSED,
        "rationale": (
            "the obligation is discharged AT a concrete F2P-shaped input, by "
            "evaluation, as a `have`, before the frozen obligation is closed "
            "verbatim: a field configured with a callable argument (identity 3, "
            "producing instance 7) against project default 0 — the shape the F2P "
            "test is about, and the shape where the produced instance is neither "
            "the argument's own identity nor the default. A second `have` pins the "
            "COMPOSED round-trip (resolve then serialize) to some (.callable "
            "{id := 3, result := 7}), i.e. the original callable survives the "
            "chain. Verifies (else the modeled behavior would be UNSATISFIABLE at "
            "exactly a normal F2P input — the total-carrier analogue of "
            "PRECOND-TOO-STRONG, and the direction neither the soundness nor the "
            "uniqueness lane can see). Nothing is assumed: no new declaration, no "
            "axiom/sorry/native_decide, statement byte-identical, and the ground "
            "instances are `have`s inside the existing tactic body. Ports nagini's "
            "admiss-configure-producer-input, whose Requires this carrier has no "
            "counterpart for — the satisfiability question is what survives."
        ),
    },

    # -------------------------------------------------------------------
    # UNIQUENESS — behavior B (serialization)
    # -------------------------------------------------------------------
    {
        "id": "weak-serialize-ignores-retained-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_IGNORE_RETAINED,
        "refinement": (
            "This is the exact pre-change serialization behavior: the resolved "
            "runtime instance is recorded unconditionally. Its faithful real patch "
            "is the unpatched repo. The F2P test test_deconstruction "
            "(file_storage.tests.FieldCallableFileStorageTests) asserts, with "
            "assertIs, that the value recorded under the storage key IS the original "
            "callable object; the resolved instance is a DIFFERENT object, so the "
            "assertion fails and the instance does NOT resolve. A rival that "
            "verified here would be the textbook verify-does-not-imply-resolve "
            "break — the spec would be blind to the very behavior it exists to pin."
        ),
        "rationale": (
            "REJECTED by clause (b2): with the retained slot = some c and a "
            "non-default resolved instance, the result must be some (.callable c), "
            "but this rival yields some (.inst state.storage). Attacks the "
            "retained-value arm over the `state` binder (its storageCallable "
            "component). If it VERIFIES => SPEC-TOO-WEAK. Ports nagini's "
            "uniqueness-producer-returns-evaluated-store."
        ),
        # (0, {storage := 7, retained := some {id := 3, result := 7}}): gold emits
        # .callable {3,7}; the rival emits .inst 7.
        "witness": _w_deconstruct(
            "0", "{ storage := 7, storageCallable := some { id := 3, result := 7 } }",
            "a retained value is present: gold emits it, the rival emits the "
            "resolved instance instead"),
    },
    {
        "id": "weak-serialize-retains-only-when-distinct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_RETAIN_ONLY_IF_DISTINCT,
        "refinement": (
            "NEAR-MISS: the retained value is honoured only when the instance it "
            "produces differs from the resolved instance, so this rival agrees with "
            "the frozen spec across that whole sub-domain. It is nevertheless wrong "
            "on every state the producer can actually build, because the resolution "
            "step sets the resolved instance TO the produced one — so the two always "
            "coincide there. Its faithful real patch records the original callable "
            "only when re-invoking it would yield a different backend, which for the "
            "F2P input (a callable whose product IS the field's live backend) means "
            "recording the instance. F2P test_deconstruction's assertIs against the "
            "original callable then fails: does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (b2) on the sub-domain c.result = state.storage — "
            "precisely the composed-reachable one. Attacks the retained-value arm "
            "again, and this case is NOT redundant with the cheaper rival above, but "
            "the reason is the reverse of a sub-domain the other witness misses: both "
            "witnesses in fact sit at coincident points (7/7 there, 5/5 here), so the "
            "cheaper rival's witness DOES also refute this rival (measured: exit 0). "
            "What makes this a genuinely distinct partial-domain rival is the other "
            "direction — at a NON-coincident point (storage 7, c.result 9) this rival "
            "AGREES with the frozen spec, so a refutation there fails against it "
            "(measured: exit 1) while still refuting the cheaper rival (exit 0). If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (0, {storage := 5, retained := some {id := 2, result := 5}}): the produced
        # instance equals the resolved one, so the rival drops to .inst 5 where gold
        # emits .callable {2,5}.
        "witness": _w_deconstruct(
            "0", "{ storage := 5, storageCallable := some { id := 2, result := 5 } }",
            "a self-producing retained value: gold still emits it, the rival "
            "collapses to the resolved instance"),
    },
    {
        "id": "weak-serialize-no-retained-emits-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_NO_RETAINED_EMITS_DEFAULT,
        "refinement": (
            "PARTIAL-DOMAIN: correct on the omission guard and on every state with a "
            "retained value (so it agrees with gold on the F2P input itself), but on "
            "the no-retained-value sub-domain it records the project default in place "
            "of the configured instance. Its faithful real patch makes the fallback "
            "of the retained-value lookup the project default rather than the "
            "field's own resolved backend, so serializing a field configured with a "
            "concrete backend records the project default instead — a migration "
            "would then silently rebuild the field against the wrong backend. That "
            "break is on the sub-domain this instance's F2P does not probe (it is "
            "the repo's field-deconstruction round-trip that asserts the recorded "
            "kwarg equals the supplied backend), so this rival is included for "
            "clause coverage: if clause (b3) were hollow, a rival free to put "
            "ANYTHING in the fallback arm would verify. Ports nagini's "
            "partial-domain-nonproducer-returns-producer-id."
        ),
        "rationale": (
            "REJECTED by clause (b3): with the retained slot = none and a non-default "
            "resolved instance, the result must be some (.inst state.storage), but "
            "this rival yields some (.inst defaultStorage). Attacks the fallback arm, "
            "varying the `state` binder's storageCallable component to none while "
            "keeping storage non-default. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (0, {storage := 5, retained := none}): gold emits .inst 5, rival .inst 0.
        "witness": _w_deconstruct(
            "0", "{ storage := 5, storageCallable := none }",
            "no retained value: gold emits the resolved instance, the rival emits "
            "the project default"),
    },
    {
        "id": "weak-serialize-drops-omission-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_NO_OMISSION,
        "refinement": (
            "The omission guard is dropped, so a value is recorded even when the "
            "resolved instance IS the project default. Its faithful real patch always "
            "emits the storage entry, so serializing a field that was given no "
            "storage argument at all records an explicit project-default backend "
            "where the construction arguments should carry no storage entry — the "
            "round-trip is no longer the identity on the default case, and a "
            "migration acquires a spurious inlined backend. Like the rival above the "
            "observable break is outside this instance's F2P input (which is a "
            "non-default callable-backed field); it is included because clause (b1) "
            "is an independent top-level arm of the postcondition and would "
            "otherwise be attacked by nothing at all."
        ),
        "rationale": (
            "REJECTED by clause (b1): when state.storage = defaultStorage the result "
            "must be none, but this rival always returns `some ...`. This is the only "
            "case attacking the omission arm, and it is the one that moves the "
            "`defaultStorage` binder off 0 while making it EQUAL the state's resolved "
            "instance — the sub-domain every other reject witness keeps out of. If it "
            "VERIFIES => SPEC-TOO-WEAK. Ports the (d1) half of nagini's "
            "describe_store surface."
        ),
        # (4, {storage := 4, retained := none}): resolved instance IS the default, so
        # gold omits (none) while the rival emits some (.inst 4).
        "witness": _w_deconstruct(
            "4", "{ storage := 4, storageCallable := none }",
            "the resolved instance is the project default: gold omits the entry, "
            "the rival emits one"),
    },

    # -------------------------------------------------------------------
    # UNIQUENESS — behavior A (construction-time resolution)
    # -------------------------------------------------------------------
    {
        "id": "weak-callable-arm-retains-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_RETAIN_NOTHING,
        "refinement": (
            "This is the exact pre-change resolution behavior: the callable argument "
            "is evaluated to the runtime instance and nothing is retained. Its "
            "faithful real patch is the unpatched repo. With no retained value the "
            "serialization step's lookup falls through to the resolved instance, so "
            "F2P test_deconstruction's assertIs against the original callable fails: "
            "does NOT resolve. This is one of the two independently-observable hunks "
            "the fix comprises (Solution_prepatch_1), so a rival that verified here "
            "would mean the spec cannot see half the fix."
        ),
        "rationale": (
            "REJECTED by clause (a3): a .callable c argument must leave the retained "
            "slot = some c, but this rival leaves it none. Attacks the retention half "
            "of the callable arm over the `arg` binder. Its witness sits at a "
            "SELF-PRODUCING argument (identity = produced instance), which is the "
            "point the near-miss rival below AGREES with the spec at — so this "
            "witness is not a discriminator for that rival and each of the two cases "
            "carries its own input point rather than one covering both. (Measured, "
            "not assumed: this witness built against the near-miss rival exits 1, "
            "while the near-miss rival's own witness at c.id ≠ c.result exits 0 "
            "against THIS rival — the two sub-domains overlap in one direction only.) "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (0, .callable {id := 5, result := 5}): gold retains some {5,5}, rival none.
        "witness": _w_init(
            "0", "(.callable { id := 5, result := 5 })",
            "a self-producing callable argument: gold retains it, the rival retains "
            "nothing"),
    },
    {
        "id": "weak-callable-arm-retains-evaluated-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_RETAIN_EVALUATED_IDENTITY,
        "refinement": (
            "NEAR-MISS on the retention clause: something IS retained and its "
            "produced instance is right, but its IDENTITY is the evaluated instance "
            "rather than the argument's own — so it is indistinguishable from gold "
            "wherever the two coincide, and the previous rival's witness point is "
            "exactly such a place (measured: that witness's build against THIS rival "
            "exits 1, so it does not discriminate here and this case needs the "
            "distinct input point below). Its faithful real patch retains the result of invoking the "
            "argument instead of the argument itself, so the serialization step "
            "records an object that is not the original callable and F2P "
            "test_deconstruction's assertIs fails: does NOT resolve. Ports nagini's "
            "uniqueness-configure-records-evaluated-as-producer."
        ),
        "rationale": (
            "REJECTED by clause (a3), which pins the retained value to c ITSELF "
            "(Callable.id is part of the DecidableEq identity), not merely to "
            "something whose product is right. Attacks the same clause as the rival "
            "above but on the disjoint sub-domain c.id ≠ c.result, and moves the "
            "`arg` binder to a distinct callable payload. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would pin only the produced instance and let "
            "the retained identity be anything, which is precisely the observable "
            "the F2P asserts with assertIs)."
        ),
        # (0, .callable {id := 3, result := 7}): gold retains some {3,7}; the rival
        # retains some {7,7}.
        "witness": _w_init(
            "0", "(.callable { id := 3, result := 7 })",
            "argument identity differs from what it produces: gold retains the "
            "argument, the rival retains its product"),
    },
    {
        "id": "weak-callable-arm-resolves-to-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_RESOLVE_TO_ARGUMENT,
        "refinement": (
            "The callable arm skips evaluation and resolves the field's runtime "
            "backend to the argument's own identity. Its faithful real patch leaves "
            "the field's backend as the callable object itself instead of the "
            "instance it produces. That breaks listed PASS_TO_PASS tests directly: "
            "test_callable_function_storage_file_field asserts the field's backend "
            "equals the instance the callable returns (and reads .location off it), "
            "and test_callable_storage_file_field_in_model asserts the same for a "
            "model field. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (a3)'s resolution half: result.storage must equal "
            "c.result, but this rival yields c.id. Attacks the resolution half of the "
            "callable arm — the clause NO other rival touches. Its witness is the "
            "only CALLABLE-arm point whose `defaultStorage` is off 0 (it is 2; the "
            "other two callable witnesses sit at 0), so the battery demonstrates that "
            "the callable arm's verdict does not depend on the default. It is not the "
            "only initStorage witness off 0 overall — weak-instance-arm-ignores-"
            "argument uses 1 and weak-default-arm-resolves-off-default uses 3. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (2, .callable {id := 6, result := 11}): gold resolves to 11, rival to 6.
        "witness": _w_init(
            "2", "(.callable { id := 6, result := 11 })",
            "gold resolves to what the argument produces, the rival to the "
            "argument's own identity"),
    },
    {
        "id": "weak-instance-arm-retains-spurious-callable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_INST_ARM_RETAINS,
        "refinement": (
            "Dead-state corruption: a retained value is recorded even though the "
            "argument was a direct instance and nothing callable was supplied. Its "
            "faithful real patch populates the retained slot unconditionally, and "
            "because the serialization step prefers that slot over the resolved "
            "instance, EVERY field configured with a concrete backend then serializes "
            "to the spurious record instead of to its own backend — the composed "
            "round-trip stops being the identity on the direct-instance arm. This is "
            "the counterpart of the nagini case added after an audit exhibited "
            "exactly this counterexample (clause c2'), and it is why the frozen spec "
            "pins BOTH components of the resulting state on every arm rather than "
            "leaving the retained slot free: an unconstrained component is the "
            "referentially-transparent analogue of the full-permission hole."
        ),
        "rationale": (
            "REJECTED by clause (a2): a .inst s argument must leave the retained slot "
            "= none, but this rival sets it to some {id := s+1, result := s}. Attacks "
            "the no-retention half of the direct-instance arm, moving the `arg` binder "
            "onto the .inst constructor. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would let a wrong impl put anything in a slot it must leave empty)."
        ),
        # (0, .inst 5): gold retains none, rival retains some {6,5}.
        "witness": _w_init(
            "0", "(.inst 5)",
            "a direct-instance argument: gold retains nothing, the rival records a "
            "spurious retained value"),
    },
    {
        "id": "weak-instance-arm-ignores-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_INST_ARM_IGNORED,
        "refinement": (
            "The direct-instance arm discards the supplied instance and keeps the "
            "project default. Its faithful real patch ignores a concretely-supplied "
            "backend, so every field configured with one reads and writes through the "
            "project default instead. Listed PASS_TO_PASS tests break immediately: "
            "the model's fields are configured with a concrete temporary backend and "
            "tests such as test_files, test_filefield_read/write and "
            "test_extended_length_storage assert the saved names and contents resolve "
            "through THAT backend. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (a2)'s resolution half: result.storage must equal s, "
            "but this rival yields defaultStorage. Attacks the resolution half of the "
            "direct-instance arm, and its witness moves `defaultStorage` to 1 with a "
            "distinct instance payload, so the .inst arm is probed at two different "
            "(defaultStorage, arg) points across the battery. If it VERIFIES => "
            "SPEC-TOO-WEAK. Ports the (c3)/else-branch half of nagini's "
            "uniqueness-configure-flag-always-true."
        ),
        # (1, .inst 8): gold resolves to 8, rival to 1.
        "witness": _w_init(
            "1", "(.inst 8)",
            "gold resolves to the supplied instance, the rival keeps the project "
            "default"),
    },
    {
        "id": "weak-default-arm-resolves-off-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DEFAULT_ARM_OFF,
        "refinement": (
            "The absent-argument arm resolves to something other than the project "
            "default. Its faithful real patch makes a field constructed with no "
            "storage argument fall back to a backend that is not the project default. "
            "The listed PASS_TO_PASS test "
            "test_file_field_storage_none_uses_default_storage asserts exactly that a "
            "field built with no storage argument has the project default as its "
            "backend, so it fails: does NOT resolve. Also observable downstream — the "
            "serialization step's omission guard compares against the project "
            "default, so such a field would additionally start emitting a storage "
            "entry that should be absent."
        ),
        "rationale": (
            "REJECTED by clause (a1): a .useDefault argument must resolve to "
            "defaultStorage, but this rival yields defaultStorage + 1. This is the "
            "only case attacking (a1)'s RESOLUTION half — the retention half of the "
            "same arm is attacked separately by "
            "weak-default-arm-retains-spurious-callable — and between them they are "
            "what move the `arg` binder onto the absent-argument constructor, without "
            "which a rival mishandling an absent argument would go uncaught. Its "
            "witness is also the only one placing `defaultStorage` at 3. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (3, .useDefault): gold resolves to 3, rival to 4.
        "witness": _w_init(
            "3", ".useDefault",
            "an absent argument: gold resolves to the project default, the rival "
            "does not"),
    },
    {
        "id": "weak-default-arm-retains-spurious-callable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DEFAULT_ARM_RETAINS,
        "refinement": (
            "Dead-state corruption on the absent-argument arm: the field resolves to "
            "the project default correctly, but a retained value is recorded even "
            "though no storage argument was supplied at all. Its faithful real patch "
            "populates the retained slot on the fall-back-to-default path too. Because "
            "the serialization step prefers that slot over the resolved instance, the "
            "damage is only masked here by the omission guard — a field left on the "
            "project default still omits the entry — so the observable break needs a "
            "field whose retained slot is spurious AND whose resolved instance is "
            "non-default, which the composed chain reaches once the default itself "
            "differs from the resolved value. Included for clause coverage rather "
            "than for an F2P break: it is the (a1) counterpart of the dead-state case "
            "the nagini sibling's clause (c2') exists for."
        ),
        "rationale": (
            "REJECTED by clause (a1)'s retention half: a .useDefault argument must "
            "leave the retained slot = none, but this rival sets it to some {...}. "
            "This half of (a1) is a SEPARATE conjunct from the (a2) half attacked by "
            "weak-instance-arm-retains-spurious-callable — an impl can satisfy either "
            "one while violating the other — and before this case the battery moved "
            "the `arg` binder onto .useDefault only for the RESOLUTION half (A/6), so "
            "an impl scribbling on the slot for an absent argument was uncaught. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (0, .useDefault): gold retains none, this rival retains some {1,0}.
        "witness": _w_init(
            "0", ".useDefault",
            "an absent argument: gold retains nothing, the rival records a spurious "
            "retained value anyway"),
    },
]


# The axiom lane belongs to G-AX and this gate ignores it. There is nothing to put
# here regardless: both modeled behaviors are spelled out with concrete operations
# over a fully transparent carrier, so the bundle declares no `opaque` callee and
# consumes no axiom.
AXIOM_TESTS = []
