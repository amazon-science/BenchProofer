"""properties.py — G-PBT falsification battery for django__django-14500 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over an ordered identifier sequence):

  unapplyMigration (mig : Migration) : List MigrationId
      result = mig.replaces ++ [(mig.appLabel, mig.name)]

The behavior rolls back a migration that stands in for a set of earlier
migrations. The observable is the ORDERED SEQUENCE of identifiers recorded as
no-longer-applied: each identifier the migration stands in for, in listed
order, THEN the migration's own identifier — the latter recorded
UNCONDITIONALLY, not only when it stands in for nothing. The load-bearing
clause is that single sequence equality, grounded entirely in the two pieces of
the input (``mig.replaces`` and the pair ``(mig.appLabel, mig.name)``); there is
no opaque oracle to echo.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the input is a pure ``Migration`` value with no heap permission, there is no
    read-only half-permission to overwrite and no aliasing to exploit. The
    nagini bundle already justified this class N/A (its only heap object was the
    freshly-built result); here it is not even expressible. No substitute is
    fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is an equality against a
    term built ONLY from the inputs; the bundle declares no ``opaque``/``axiom``
    (axioms region empty), so there is no answer key an implementation could
    echo without doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify.

  * AXIOM lane — DROPPED. The nagini sibling's AXIOM_TESTS (A-reference
    soundness + containment for the deep model) belong to G-AX, which this gate
    ignores. meta.json records axioms == [] and deep_model_references == [].

  * MISSING-OWN-KEY / OVER-RECORDING / PARTIAL-DOMAIN — APPLY to the single
    sequence-equality clause. The four uniqueness rivals below re-express the
    nagini rivals against this carrier: the pre-patch else-only recording, the
    own key omitted entirely, the own key appended only on a short sub-domain,
    and an over-recording variant appending a spurious identifier.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form (an
``if``-guarded ``for`` loop followed by an unconditional append, bridged to a
``forIn`` helper by an ``rfl``) — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet proving
the rival CONTRADICTS the spec at one concrete input. Each is stated directly
against the spec predicate at ``decide``-able literals, and each was checked to
hold of its rival AND to FAIL on the frozen solution (so it discriminates
rather than asserting a tautology).

BINDER COVERAGE. The spec has a single input binder, ``mig``, whose two relevant
components are the stand-in list ``mig.replaces`` and the own identifier
``(mig.appLabel, mig.name)``. The reject witnesses spread over that binder
rather than fixing it at one convenient point: ``replaces`` is probed EMPTY
(own-omitted, where the own key is the ONLY thing that should be recorded),
length ONE (else-only / spurious, where the pre-patch bug and the
over-recording both surface), and length TWO (partial-domain, the F2P witness
shape where the short-sub-domain rival first diverges), and the own identifier
takes a different value in each. So no rival mishandling only one of those
components would slip past unprobed.
"""
from pathlib import Path

INSTANCE = "django__django-14500"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl def body (entirely inside the impl region) and the FULL tactic
# body of the sole obligation (entirely inside the proof region), so every
# replacement lands within the region it means to edit and same_spec holds.
_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  if mig.replaces ≠ [] then\n"
    "    for r in mig.replaces do\n"
    "      recorded := recorded ++ [r]\n"
    "  recorded := recorded ++ [(mig.appLabel, mig.name)]\n"
    "  return recorded"
)

_PROOF = (
    "  intro mig\n"
    "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
    "  simp only [Id.run]\n"
    "  by_cases h : mig.replaces ≠ []\n"
    "  · rw [if_pos h]\n"
    "    -- bridge the desugared `do` body to the clean `forIn` form of the helper\n"
    "    have h2 : (do\n"
    "        let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r_1 ++ [r]))\n"
    "        pure PUnit.unit\n"
    "        pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))\n"
    "      = Id.run (forIn mig.replaces ([] : List MigrationId)\n"
    "          (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl\n"
    "    rw [h2, unapplyMigration_forIn]; simp\n"
    "  · rw [if_neg h]\n"
    "    push_neg at h\n"
    "    rw [h]; rfl"
)


# ---- soundness positive: guard-free reshape (impl + reproof) ----------------
# Drop the `if mig.replaces ≠ []` guard: the loop over an empty list is a no-op,
# so the guarded and unguarded builds compute the same sequence on every input.
# The frozen proof's `by_cases`/`if_pos`/`if_neg` no longer applies (there is no
# `if`), so the obligation is re-proved for the new shape — statement identical.
_POS_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  for r in mig.replaces do\n"
    "    recorded := recorded ++ [r]\n"
    "  recorded := recorded ++ [(mig.appLabel, mig.name)]\n"
    "  return recorded"
)
_POS_PROOF = (
    "  intro mig\n"
    "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
    "  simp only [Id.run]\n"
    "  have h2 : (do\n"
    "      let r ← forIn mig.replaces ([] : List MigrationId) fun r r_1 => do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield (r_1 ++ [r]))\n"
    "      pure (r ++ [(mig.appLabel, mig.name)]) : Id (List MigrationId))\n"
    "    = Id.run (forIn mig.replaces ([] : List MigrationId)\n"
    "        (fun r acc => (ForInStep.yield (acc ++ [r])))) ++ [(mig.appLabel, mig.name)] := rfl\n"
    "  rw [h2, unapplyMigration_forIn]; simp"
)

# ---- admissibility positive: ground instance + frozen proof -----------------
# Prepend, inside the SAME tactic body, a `have` discharging the obligation at a
# concrete F2P-shaped input (a replacement migration standing in for two others)
# by evaluation, then close the frozen obligation verbatim. If that ground
# instance could not be discharged the modeled behavior would be unsatisfiable
# at exactly the input the F2P exercises. No new declaration, statement
# byte-identical, ground instance is a `have`.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_unapplyMigration\n"
    "      { appLabel := \"migrations\", name := \"0001_squashed_0002\",\n"
    "        replaces := [(\"migrations\", \"0001_initial\"), (\"migrations\", \"0002_second\")] }\n"
    "      (implementation_unapplyMigration\n"
    "        { appLabel := \"migrations\", name := \"0001_squashed_0002\",\n"
    "          replaces := [(\"migrations\", \"0001_initial\"), (\"migrations\", \"0002_second\")] }) := by\n"
    "    unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
    "    decide\n"
) + _PROOF


# ---- uniqueness rivals (impl-only reshape; frozen proof retained) -----------
# else-only (pre-patch): the own identifier is recorded ONLY in the
# no-stand-in branch. For a replacement migration (non-empty replaces) it is
# never recorded.
_ELSE_ONLY_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  if mig.replaces ≠ [] then\n"
    "    for r in mig.replaces do\n"
    "      recorded := recorded ++ [r]\n"
    "  else\n"
    "    recorded := recorded ++ [(mig.appLabel, mig.name)]\n"
    "  return recorded"
)
# own-omitted: the own identifier is NEVER recorded; only the stand-ins are.
_OWN_OMITTED_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  if mig.replaces ≠ [] then\n"
    "    for r in mig.replaces do\n"
    "      recorded := recorded ++ [r]\n"
    "  return recorded"
)
# partial-domain: the own identifier is appended only when there is at most one
# stand-in; for two or more (the F2P shape) it is dropped.
_PARTIAL_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  if mig.replaces ≠ [] then\n"
    "    for r in mig.replaces do\n"
    "      recorded := recorded ++ [r]\n"
    "  if mig.replaces.length ≤ 1 then\n"
    "    recorded := recorded ++ [(mig.appLabel, mig.name)]\n"
    "  return recorded"
)
# over-recording: appends a spurious identifier not derivable from the input
# after the correct own identifier.
_SPURIOUS_IMPL = (
    "def implementation_unapplyMigration (mig : Migration) : List MigrationId := Id.run do\n"
    "  let mut recorded : List MigrationId := []\n"
    "  if mig.replaces ≠ [] then\n"
    "    for r in mig.replaces do\n"
    "      recorded := recorded ++ [r]\n"
    "  recorded := recorded ++ [(mig.appLabel, mig.name)]\n"
    "  recorded := recorded ++ [(\"extra\", \"spurious\")]\n"
    "  return recorded"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the `theorem correct_unapplyMigration` statement byte-identical and
    # re-proves it for the new shape; introduces no helper lemma, axiom, or
    # assumption token (the `forIn` helper is the FROZEN one, unchanged).
    # =====================================================================
    {
        "id": "pos-control-guard-free",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _POS_IMPL), _PROOF, _POS_PROOF),
        "rationale": (
            "dropping the emptiness guard is a behaviour-preserving reshape: the "
            "loop over an empty stand-in list is a no-op, so the unguarded build "
            "records exactly `mig.replaces ++ [(mig.appLabel, mig.name)]` on every "
            "input, satisfying the sole clause. Must verify, else the sequence-"
            "equality postcondition is SPEC-TOO-STRONG. Re-proved because the "
            "frozen `by_cases`/`if_pos`/`if_neg` no longer applies (no `if`); the "
            "new proof reuses the FROZEN `forIn` helper — no new declaration."),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe has no binder to attack here; the honest
    # analogue discharges the spec predicate at a ground replacement-migration
    # input by evaluation inside the proof region, alongside the frozen
    # obligation.
    # =====================================================================
    {
        "id": "admiss-ground-replacement",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at a ground replacement-migration input "
            "(standing in for two earlier migrations, the F2P shape) by `decide`, "
            "then the frozen obligation is closed verbatim. Verifies (else the "
            "spec is unsatisfiable at the normal input, the analogue of PRECOND-"
            "TOO-STRONG). Nothing is assumed: no new declaration, statement "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete input, checked to hold of the rival and to FAIL on gold.
    # =====================================================================
    {
        "id": "weak-else-only-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behavior: own identifier recorded only in the
        # no-stand-in branch. For non-empty replaces it is never recorded.
        "module": _swap(_BASE, _IMPL, _ELSE_ONLY_IMPL),
        "refinement": (
            "This is the pre-patch shape verbatim: the own identifier is recorded "
            "only when the migration stands in for nothing. Its faithful real "
            "patch leaves the own-identifier recording inside the else, so a "
            "rolled-back REPLACEMENT migration (the F2P witness stands in for two "
            "earlier migrations) never records its own identifier and the F2P "
            "assertion that it is no longer applied FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from `result = mig.replaces ++ [(mig.appLabel, mig.name)]`: on "
            "a non-empty stand-in list the rival returns `mig.replaces` with the "
            "trailing own identifier absent. Witness probes replaces of length "
            "ONE — the smallest non-empty case where the else-branch is skipped."),
        "witness": (
            "example : ¬ problem_spec_unapplyMigration\n"
            "    { appLabel := \"s\", name := \"sq\", replaces := [(\"m\", \"0002\")] }\n"
            "    (implementation_unapplyMigration\n"
            "      { appLabel := \"s\", name := \"sq\", replaces := [(\"m\", \"0002\")] }) := by\n"
            "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-own-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        # Own identifier never recorded; only the stand-ins are appended.
        "module": _swap(_BASE, _IMPL, _OWN_OMITTED_IMPL),
        "refinement": (
            "The own identifier is NEVER recorded (only the stand-ins are). Its "
            "faithful real patch drops the own-identifier recording entirely, so "
            "the migration is never marked no-longer-applied for ANY input — the "
            "F2P assertion fails, and even a plain (no-stand-in) migration is left "
            "applied. Does NOT resolve."),
        "rationale": (
            "REJECT from the sequence equality: the rival returns exactly "
            "`mig.replaces` on every input, so the trailing own identifier is "
            "absent. Witness probes the EMPTY stand-in list, where the own "
            "identifier is the ONLY thing that should be recorded (`[]` vs the "
            "required `[(mig.appLabel, mig.name)]`) — a distinct binder point from "
            "the other rivals, which all use a non-empty list."),
        "witness": (
            "example : ¬ problem_spec_unapplyMigration\n"
            "    { appLabel := \"a\", name := \"0001\", replaces := [] }\n"
            "    (implementation_unapplyMigration\n"
            "      { appLabel := \"a\", name := \"0001\", replaces := [] }) := by\n"
            "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-partial-domain-len2",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct for at most one stand-in; drops the own identifier for two+.
        "module": _swap(_BASE, _IMPL, _PARTIAL_IMPL),
        "refinement": (
            "Correct on the short sub-domain (at most one stand-in) but drops the "
            "own-identifier append for two or more. The F2P witness stands in for "
            "TWO earlier migrations, so its faithful real patch (own identifier "
            "recorded only when there is at most one stand-in) never records the "
            "replacement's own identifier, it stays applied, and the F2P assertion "
            "FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from the sequence equality on the length>=2 sub-domain: the "
            "rival returns `mig.replaces` (no trailing own identifier). Witness "
            "probes replaces of length TWO — exactly the F2P shape, and the "
            "boundary where this near-miss first diverges from gold (it AGREES "
            "with gold at length 0 and 1)."),
        "witness": (
            "example : ¬ problem_spec_unapplyMigration\n"
            "    { appLabel := \"s\", name := \"sq\", replaces := [(\"m\", \"0001\"), (\"m\", \"0002\")] }\n"
            "    (implementation_unapplyMigration\n"
            "      { appLabel := \"s\", name := \"sq\", replaces := [(\"m\", \"0001\"), (\"m\", \"0002\")] }) := by\n"
            "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-spurious-extra",
        "kind": "uniqueness",
        "expect": "reject",
        # Appends a spurious identifier not derivable from the input after the
        # correct own identifier (over-recording).
        "module": _swap(_BASE, _IMPL, _SPURIOUS_IMPL),
        "refinement": (
            "Over-recording: records an extra identifier not derivable from the "
            "input after the correct own identifier. Its faithful real patch marks "
            "an unrelated migration no-longer-applied that was not part of this "
            "roll-back, corrupting the applied set beyond what the roll-back should "
            "touch and breaking the applied-set bookkeeping the P2P state tests "
            "rely on. Does NOT resolve."),
        "rationale": (
            "REJECT from the exact sequence equality: the pinned sequence is the "
            "stand-ins followed by the SINGLE own identifier; the extra trailing "
            "element makes the result longer than "
            "`mig.replaces ++ [(mig.appLabel, mig.name)]`. Witness probes a "
            "length-ONE stand-in list with an own identifier distinct from the "
            "else-only rival's, so this rival's divergent point is its own."),
        "witness": (
            "example : ¬ problem_spec_unapplyMigration\n"
            "    { appLabel := \"z\", name := \"1\", replaces := [(\"m\", \"0002\")] }\n"
            "    (implementation_unapplyMigration\n"
            "      { appLabel := \"z\", name := \"1\", replaces := [(\"m\", \"0002\")] }) := by\n"
            "  unfold problem_spec_unapplyMigration implementation_unapplyMigration\n"
            "  decide\n"
        ),
    },
]
