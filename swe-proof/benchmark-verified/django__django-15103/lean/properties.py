"""properties.py — G-PBT falsification battery for django__django-15103 (lean).

PORT of the nagini sibling's spec-lane battery to the lean carrier. NOT a Lean
file; a record of adversarial cases the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_scriptTag``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over four inputs, two of them opaque):

  scriptTag
      (jsonBody : String → String) (escapeId : String → String)
      (value optId : String) : String
      result =
        if optId ≠ "" then
          "<script id=\\"" ++ escapeId optId ++ "\\" type=\\"application/json\\">"
            ++ jsonBody value ++ "</script>"
        else
          "<script type=\\"application/json\\">" ++ jsonBody value ++ "</script>"

  The two step functions (encode the value into its safe body; escape an
  identifier for attribute use) are left universally quantified, so the pinned
  behavior is exactly "the presence of an identifier selects whether an ``id``
  attribute is emitted, and the encoded body is framed by the corresponding
  script tag." ``optId`` is a single ``String``: ``optId = ""`` is the FALSY
  case (mapping.md: an absent OR empty identifier), ``optId ≠ ""`` the truthy
  case. This is the carrier's collapse of nagini's two-way ``element_id is None``
  / ``len == 0`` presence predicate onto a single string emptiness test.

  The one top-level clause folds several inseparable sub-decisions, each pinned
  to a distinct binder:

    * WHICH FRAME is emitted — the id-bearing opening tag vs the id-free one —
      keyed on ``optId ≠ ""``. Pinned by ``optId``.
    * WHAT identifier text the id-bearing frame carries — ``escapeId optId``,
      not the raw identifier. Pinned by ``escapeId`` and ``optId``.
    * WHAT body the frame wraps — ``jsonBody value``, the encoded body, not the
      raw value. Pinned by ``jsonBody`` and ``value``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY: both modeled inputs are held at fractional
    (read-only) permission and a rival that overwrites one is rejected for
    insufficient permission (its two ``frame-mut-*`` rivals). Lean is
    referentially transparent — the inputs are plain immutable ``String`` /
    function values, there is no half-permission to violate and no aliasing to
    exploit — so this class has NO expressible instance here. No substitute is
    fabricated for it. (nagini: ``frame-mut-payload``, ``frame-mut-element_id``
    OMITTED — vacuous on this carrier.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_scriptTag``
    is a total Lean ``def``; a non-returning implementation cannot be written at
    all, so the nagini ``vac-nonterm`` rival (an infinite append loop that
    satisfies the value postcondition only vacuously, rejected by nagini's
    ``MustTerminate`` obligation) has no counterpart here. (nagini:
    ``vac-nonterm`` OMITTED — vacuous on this carrier; NOT a known spec hole,
    unlike the velvet ``partial`` case in the corpus-wide termination-semantics finding.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built from the inputs — two constant literal frames, the
    opaque steps applied to their own arguments (``escapeId optId``,
    ``jsonBody value``), and the emptiness split on ``optId`` — fully unfolded.
    There is no ``opaque``/``axiom`` callee CONTRACT to echo (the two steps are
    free parameters with no asserted property), so no answer-key exists. The
    honest analogue is the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN (the pre-patch behavior) — APPLIES, load-bearing. The pre-fix
    code always emitted the id-bearing frame. ``weak-absent-emits-id`` reproduces
    exactly that on the falsy sub-domain and is refuted precisely there — the
    F2P (no-id) slice. (nagini: ``weak-absent-emits-id`` PORTED.)

  * BRANCH-SELECTION INVERSION — APPLIES. ``weak-swap-branches`` inverts the
    presence guard, so the truthy input gets the id-free frame and the falsy
    input gets the id-bearing one. Refuted on the truthy slice (Q-present) with
    a distinct concrete input. (nagini: ``weak-swap-branches`` PORTED.)

  * BODY-COMBINATION — APPLIES (a lean-carrier attack with no nagini line item,
    added to cover the ``jsonBody value`` sub-term of the clause, which is a free
    opaque application here but was a grounded literal fold in nagini). A rival
    that frames the RAW value instead of the encoded body verifies against a spec
    that left the body sub-term unpinned. Refuted by instantiating ``jsonBody``
    at a constant distinct from the identity, at the falsy sub-domain.

  * EMPTY-vs-ABSENT BOUNDARY — COLLAPSED. nagini distinguishes ``element_id is
    None`` from ``len == 0`` and carries a ``weak-present-on-empty`` rival that
    misclassifies the empty token as present. On this carrier both are the single
    value ``optId = ""``, so ``weak-present-on-empty`` has NO distinct
    counterpart: a rival that treats ``""`` as present is byte-identical in
    output to ``weak-absent-emits-id`` (both emit ``escapeId "" ...`` on the
    falsy input). (nagini: ``weak-present-on-empty`` OMITTED — collapses into
    ``weak-absent-emits-id`` under the single-string presence test.)

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
carries a Lean snippet stating the spec predicate directly at a concrete input,
with the two OPAQUE step parameters instantiated at concrete closures (``id`` or
a constant) so the whole predicate is ``decide``-able. Each was checked to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). No hypothesis-conditioning is needed: instantiating the
free function parameters makes the carrier fully compute, so every witness binder
is jointly satisfiable by construction.

BINDER COVERAGE across the reject witnesses (so the battery exercises the spec's
dependence on each input rather than probing one point):
  * ``optId`` — refuted at ``""`` (falsy; absent-emits-id, raw-body) AND at
    ``"a"`` (truthy; swap-branches).
  * ``escapeId`` — instantiated at ``id`` (absent-emits-id, raw-body) AND at a
    constant ``fun _ => "Z"`` (swap-branches), so it is not pinned to one closure.
  * ``jsonBody`` — instantiated at ``id`` (absent-emits-id, swap) AND at the
    non-trivial ``fun s => s ++ "!"`` (raw-body), the witness that pins the body
    sub-term.
  * ``value`` — supplied as the argument to ``jsonBody`` in every witness, and
    varied off the shared ``"V"`` to ``"X"`` in the raw-body witness, where
    ``jsonBody`` genuinely depends on it (``jsonBody "X" = "X!" ≠ "X"``); that
    rival demonstrates the framed body must be ``jsonBody value``, not ``value``,
    so the value binder is load-bearing there.
``pts`` = 3 distinct input points (``id id "V" ""``, ``id (fun _ => "Z") "V"
"a"``, ``(fun s => s ++ "!") id "X" ""``).

AXIOM lane: EMPTY. meta.json declares no consumed axiom and no deep-model
reference (the two step functions are free parameters, not axiomatized callees),
so there is no axiom-soundness / axiom-containment obligation for this gate to
re-discharge (that lane is G-AX's job in any case). The nagini
``AXIOM_TESTS`` (its A-reference deep model of the real ``json_script`` validated
in Docker) are DROPPED per the porting contract. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-15103"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_scriptTag\n"
    "    (jsonBody : String → String)\n"
    "    (escapeId : String → String)\n"
    "    (value optId : String) : String := Id.run do\n"
    "  -- Encode the value into its safe JSON body once; this step is independent of\n"
    "  -- any identifier.\n"
    "  let jsonStr := jsonBody value\n"
    "  -- Select the script-tag frame: with an `id` attribute when an identifier is\n"
    "  -- supplied, otherwise without one.\n"
    "  let mut result := \"\"\n"
    "  if optId ≠ \"\" then\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ jsonStr ++ \"</script>\"\n"
    "  else\n"
    "    result := \"<script type=\\\"application/json\\\">\" ++ jsonStr ++ \"</script>\"\n"
    "  return result\n"
)

_PROOF_BODY = (
    "  intro jsonBody escapeId value optId\n"
    "  unfold problem_spec_scriptTag implementation_scriptTag\n"
    "  by_cases h : optId ≠ \"\" <;> simp only [h, if_false, Id.run] <;> rfl\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with ONLY the gold impl body replaced (frozen
    proof body carried over — for a reject case it will not close against the
    reshaped impl, which is exactly the intended 'did not verify')."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / control impl bodies (each is a full impl region; only the impl — and
# for the reorder control, also the proof body — changes, so the spec and the
# theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): structurally DIFFERENT but behaviourally
# identical — tests the FALSY predicate FIRST with an explicit guard, returns the
# id-free frame, then the id-bearing frame in the fall-through (where the truthy
# entry condition holds by negation of the falsy guard). Only the textual order
# of the two independent guarded branches changes; the body-encode step and both
# literal frames are verbatim. Must VERIFY (else SPEC-TOO-STRONG).
_POS_REORDER = (
    "def implementation_scriptTag\n"
    "    (jsonBody : String → String)\n"
    "    (escapeId : String → String)\n"
    "    (value optId : String) : String := Id.run do\n"
    "  let jsonStr := jsonBody value\n"
    "  let mut result := \"\"\n"
    "  if optId = \"\" then\n"
    "    result := \"<script type=\\\"application/json\\\">\" ++ jsonStr ++ \"</script>\"\n"
    "  else\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ jsonStr ++ \"</script>\"\n"
    "  return result\n"
)
# The frozen tactic splits on `optId ≠ ""`; the reorder splits the other way, so
# the tactic body is re-proved (statement byte-identical, no new lemma/axiom).
_POS_REORDER_PROOF = (
    "  intro jsonBody escapeId value optId\n"
    "  unfold problem_spec_scriptTag implementation_scriptTag\n"
    "  by_cases h : optId = \"\" <;> simp [h, Id.run, pure] <;> rfl\n"
)

# ADMISSIBILITY: keep the gold impl VERBATIM and discharge the spec predicate at
# the F2P ground input (no identifier supplied, `optId = ""`) inside the proof
# region, alongside the frozen obligation. Confirms the modeled behavior is
# satisfiable at exactly the input the F2P exercises (else the analogue of
# PRECOND-TOO-STRONG). The theorem STATEMENT is byte-identical; the ground
# instance is a `have` in the existing tactic body; nothing new is assumed.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_scriptTag id id \"{}\" \"\"\n"
    "      (implementation_scriptTag id id \"{}\" \"\") := by\n"
    "    unfold problem_spec_scriptTag implementation_scriptTag\n"
    "    decide\n"
    + _PROOF_BODY
)

# PARTIAL-DOMAIN (= the pre-patch behavior): the falsy branch ALSO emits the
# id-bearing frame (with an empty escaped id). Correct on the truthy slice, wrong
# on the falsy (F2P no-id) slice.
_WEAK_ABSENT_EMITS_ID = (
    "def implementation_scriptTag\n"
    "    (jsonBody : String → String)\n"
    "    (escapeId : String → String)\n"
    "    (value optId : String) : String := Id.run do\n"
    "  let jsonStr := jsonBody value\n"
    "  let mut result := \"\"\n"
    "  if optId ≠ \"\" then\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ jsonStr ++ \"</script>\"\n"
    "  else\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ jsonStr ++ \"</script>\"\n"
    "  return result\n"
)

# BRANCH-SELECTION INVERSION: flip the presence guard. Truthy id gets the id-free
# frame; falsy id gets the id-bearing frame. Both branches wrong.
_WEAK_SWAP = (
    "def implementation_scriptTag\n"
    "    (jsonBody : String → String)\n"
    "    (escapeId : String → String)\n"
    "    (value optId : String) : String := Id.run do\n"
    "  let jsonStr := jsonBody value\n"
    "  let mut result := \"\"\n"
    "  if optId = \"\" then\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ jsonStr ++ \"</script>\"\n"
    "  else\n"
    "    result := \"<script type=\\\"application/json\\\">\" ++ jsonStr ++ \"</script>\"\n"
    "  return result\n"
)

# BODY-COMBINATION: select the frame correctly, but wrap the RAW value instead of
# the encoded body `jsonBody value`. Attacks the body sub-term of the clause.
_WEAK_RAW_BODY = (
    "def implementation_scriptTag\n"
    "    (jsonBody : String → String)\n"
    "    (escapeId : String → String)\n"
    "    (value optId : String) : String := Id.run do\n"
    "  let mut result := \"\"\n"
    "  if optId ≠ \"\" then\n"
    "    result := \"<script id=\\\"\" ++ escapeId optId ++ \"\\\" type=\\\"application/json\\\">\"\n"
    "      ++ value ++ \"</script>\"\n"
    "  else\n"
    "    result := \"<script type=\\\"application/json\\\">\" ++ value ++ \"</script>\"\n"
    "  return result\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation, the spec is SPEC-TOO-STRONG. The theorem STATEMENT is
    # byte-identical; the tactic body is re-proved for the new branch order.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_REORDER), _PROOF_BODY, _POS_REORDER_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl: tests the falsy predicate "
            "first (`if optId = \"\" then` → the id-free frame), then the id-bearing "
            "frame in the fall-through (where `optId ≠ \"\"` holds by negation of "
            "the falsy guard). Only the textual order of the two independent guarded "
            "branches changes — the body-encode step `jsonBody value` and both "
            "literal frames are verbatim, no dropped step. It must satisfy the frozen "
            "`result = if optId ≠ \"\" then …`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Proof: `by_cases` on `optId = \"\"`, `simp [Id.run, "
            "pure]` reduces the `do` block, `rfl` closes each branch — no new "
            "declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # at the F2P-shaped input rather than only in the abstract. The frozen theorem
    # carries NO precondition hypothesis (the behavior is total, `∀` unguarded),
    # so nagini's precondition-admission probe has no binder to attack; the honest
    # analogue is to discharge the spec predicate at the F2P ground input (no
    # identifier, `optId = ""`) inside the proof region, alongside the frozen
    # obligation.
    # =====================================================================
    {
        "id": "admiss-no-id-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (no identifier "
            "supplied, `optId = \"\"`, so the id-free frame is required) by `decide`, "
            "then the frozen obligation is closed verbatim. Verifies (else the spec "
            "is unsatisfiable at the normal no-id input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P (so a verifying rival would be
    # a true verify-does-not-imply-resolve break, not an artifact), and (b) a
    # refutation witness pinning the violation at one concrete input, with the two
    # opaque step parameters instantiated so the predicate computes.
    # =====================================================================
    {
        "id": "weak-absent-emits-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT_EMITS_ID),
        "refinement": (
            "this IS the pre-patch behavior: the no-identifier case still emits the "
            "id-bearing frame (with an empty escaped id). Its faithful real patch is "
            "the UNCHANGED repo, which on the F2P no-id call renders the id-bearing "
            "tag rather than the id-free one the F2P tests assert. Does NOT resolve — "
            "exactly the change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECT from the falsy branch of the clause: for `optId = \"\"` the spec "
            "demands `\"<script type=\\\"application/json\\\">\" ++ jsonBody value ++ "
            "\"</script>\"`, but the rival returns the id-bearing frame "
            "`\"<script id=\\\"\" ++ escapeId \"\" ++ …`, which carries the ` id=\"…\"` "
            "segment. PARTIAL-DOMAIN: correct on the truthy slice, wrong on the falsy "
            "slice. If it VERIFIES => SPEC-TOO-WEAK (the id-omission is not enforced)."
        ),
        "witness": (
            "-- Refuted on the falsy (no-identifier) slice: with both step functions\n"
            "-- the identity, the spec requires the id-FREE frame, but the rival emits\n"
            "-- the id-bearing (empty-id) frame.\n"
            "example : ¬ problem_spec_scriptTag id id \"V\" \"\"\n"
            "    (implementation_scriptTag id id \"V\" \"\") := by\n"
            "  unfold problem_spec_scriptTag implementation_scriptTag\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "refinement": (
            "inverting the presence guard (`if optId = \"\"` selecting the id-bearing "
            "frame) is the exact opposite of the gold `if element_id:`. Every "
            "identifier-present call (e.g. the P2P test that supplies an id) would "
            "render the id-FREE frame and every no-id F2P call would render the "
            "id-bearing frame — both wrong. Fails every F2P and P2P. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from BOTH branches of the clause. (a) On the truthy slice "
            "`optId ≠ \"\"` the spec demands the id-bearing frame `\"<script id=\\\"\" "
            "++ escapeId optId ++ …`, but the inverted guard routes it to the id-free "
            "fall-through returning `\"<script type=\\\"application/json\\\">\" ++ …`. "
            "(b) On the falsy slice it emits the id-bearing frame the spec forbids. A "
            "full value-level inversion. If it VERIFIES => SPEC-TOO-WEAK (the branch "
            "selection is unpinned)."
        ),
        "witness": (
            "-- Refuted on the truthy slice (identifier \"a\"), with escapeId a\n"
            "-- constant distinct from identity: the spec requires the id-bearing\n"
            "-- frame, but the inverted guard returns the id-free frame.\n"
            "example : ¬ problem_spec_scriptTag id (fun _ => \"Z\") \"V\" \"a\"\n"
            "    (implementation_scriptTag id (fun _ => \"Z\") \"V\" \"a\") := by\n"
            "  unfold problem_spec_scriptTag implementation_scriptTag\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-raw-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RAW_BODY),
        "refinement": (
            "framing the RAW value rather than the encoded body corresponds to a "
            "patch that drops the JSON-encode + entity-translation step of the body. "
            "Its faithful real patch renders the un-encoded value inside the tag, so "
            "the F2P no-id assertion (encoded body `{\"key\": \"value\"}`) and the P2P "
            "body-encoding assertions fail. Does NOT resolve. (This attacks the body "
            "sub-term of the clause, which is a free opaque application on this "
            "carrier — nagini pinned it as a grounded literal fold, so it has no "
            "nagini line item; the sub-term is load-bearing and must be defended.)"
        ),
        "rationale": (
            "REJECT from the body sub-term of the clause: the spec pins the wrapped "
            "body to `jsonBody value`, but the rival wraps `value` directly. With "
            "`jsonBody` instantiated at `fun s => s ++ \"!\"` (a genuine function of "
            "its argument, so `jsonBody \"X\" = \"X!\" ≠ \"X\"`), the spec demands the "
            "frame carry the encoded body \"X!\" while the rival carries the raw "
            "\"X\". If it VERIFIES => SPEC-TOO-WEAK (the body-combination is unpinned; "
            "an impl may frame anything as the body). The witness exercises the "
            "`value` binder's dependence — the discriminator is `jsonBody value ≠ "
            "value`, false only because the modeled body step is non-trivial on "
            "`value`."
        ),
        "witness": (
            "-- Refuted with jsonBody a genuine function of its argument\n"
            "-- (`fun s => s ++ \"!\"`, so `jsonBody \"X\" = \"X!\"`): the spec requires\n"
            "-- the framed body be the ENCODED body `jsonBody value` (\"X!\"), but the\n"
            "-- rival frames the raw value (\"X\").\n"
            "example : ¬ problem_spec_scriptTag (fun s => s ++ \"!\") id \"X\" \"\"\n"
            "    (implementation_scriptTag (fun s => s ++ \"!\") id \"X\" \"\") := by\n"
            "  unfold problem_spec_scriptTag implementation_scriptTag\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the two step functions are
# universally-quantified parameters with no asserted property, so there is no
# in-model axiom obligation for the PBT axiom lane to re-discharge. The nagini
# AXIOM_TESTS (the A-reference deep model validated against the real callee in
# Docker) are dropped per the porting contract (that lane is G-AX's job).
AXIOM_TESTS = []
