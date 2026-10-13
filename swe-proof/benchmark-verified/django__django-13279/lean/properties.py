"""properties.py — G-PBT falsification battery for django__django-13279 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function, a dispatch on a configured
serialization-format identifier):

  encode (algo : String) (session : List (String × String)) : String
      result = (if algo = "sha1" then legacyEncode session else modernEncode session)

  The two interchangeable serialization schemes are modeled as OPAQUE carriers
  (``legacyEncode`` / ``modernEncode``): the behavior under test is *which*
  scheme is selected for a given identifier and session, not the internal byte
  layout of either scheme. The postcondition is two independent implications:

    (Q-legacy)  algo = "sha1"  → result = legacyEncode session
    (Q-modern)  algo ≠ "sha1"  → result = modernEncode session

  Input binders of the spec predicate: ``algo`` (the format identifier) and
  ``session`` (the data to serialize). ``algo`` takes both the ``"sha1"`` value
  and a non-``"sha1"`` value across the reject witnesses, so each implication is
  probed in its own regime.

  ``session`` needs a sharper statement than "two distinct records appear". A
  rival can only be SENSITIVE to ``session`` if it applies the selected scheme to
  a record other than the one it was handed; the corrupt/wrong-scheme rivals all
  pass ``session`` through untouched, so spelling their witnesses at two
  different literal records varies the point of evaluation without varying
  anything the spec's verdict depends on. The binder is therefore attacked
  directly by ``weak-legacy-empty-record`` below, which serializes the EMPTY
  record in the legacy regime: it is correct at ``session = []`` and wrong at
  every non-empty record, so it is the one rival whose rejection genuinely turns
  on WHICH record the scheme is applied to. (This is the nagini
  ``weak-legacy-empty`` PARTIAL-DOMAIN rival, which an earlier draft dropped;
  it is expressible here by the same conditioning technique the wrong-scheme
  rival uses.)

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini bundle held the serialized
    payload at a fractional (read-only) permission and its MANDATORY frame probe
    wrote back into it (a no-op store) to be rejected for insufficient
    permission. Lean is referentially transparent: the input carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. The nagini ``frame-mut-write`` rival has NO expressible
    instance here and no substitute is fabricated for it. See 'assessment'.

  * PARTIAL-DOMAIN / VALUE — APPLIES. The nagini value rivals turn on
    DISTINGUISHING the two schemes' concrete byte outputs. It is TRUE that
    ``legacyEncode s ≠ modernEncode s`` is not a theorem on this opaque carrier
    (the two may be extensionally equal for all the closed spec knows), so a
    witness cannot COMPUTE that inequality. It does NOT follow that a
    wrong-scheme rival is inexpressible: the witness CONDITIONS on the
    disagreement instead (a hypothesis ``hne : modernEncode s ≠ legacyEncode s``
    at the F2P input), and the gate's consistency probe confirms the hypothesis
    is satisfiable precisely BECAUSE the terms are opaque (no tactic derives
    ``False`` from two unequal opaque terms). The literal pre-patch bug — emit
    the modern scheme in the legacy regime — is therefore carried as
    ``weak-wrong-scheme-legacy`` (an earlier draft wrongly dropped it as
    "no discriminating witness"). It is the ONLY rival attacking the DISPATCH
    SELECTION; without it the battery pins each arm's byte-exactness but never
    that the correct scheme is selected — the very defect the fix removes. The
    nagini PARTIAL-DOMAIN rival proper (a legacy-regime result that carries the
    EMPTY record instead of the given one — correct on ``{}``, wrong on every
    other record) is carried as ``weak-legacy-empty-record`` by the SAME
    conditioning technique: the witness assumes only
    ``legacyEncode [] ≠ legacyEncode <F2P record>``, which the consistency probe
    confirms is satisfiable. In
    ADDITION, each arm's output-exactness is pinned by a rival that corrupts the
    already-correctly-selected scheme's output (appends a byte), refuted by
    string length — two such rivals, one per clause, so each implication and
    each binder value is attacked.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition equates ``result`` to a
    term built only from the inputs and the two opaque schemes applied to
    ``session``; there is no separate answer-key oracle an implementation could
    echo without applying the selected scheme to the actual session. The honest
    analogues are the POSITIVE CONTROLS (``pos-*``) that must verify.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input. Because the schemes are opaque, the witness cannot ``decide`` a
value equality; it instead derives a STRING-LENGTH contradiction from the
appended byte (``|scheme s ++ "0"| = |scheme s|``), which holds of the corrupting
rival and FAILS on the frozen solution (whose selected arm returns the scheme's
output verbatim). Each was checked to hold of its rival and to fail on gold.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (the keyed_digest / modern_
serialize / F2P-route soundness probes over the deep model) belong to G-AX,
which the G-PBT spec lane ignores. This carrier declares only two opaque
signatures and consumes NO ``axiom … _prop`` (the proof closes by case analysis
on the identifier), so there is no axiom-soundness / axiom-containment
obligation for this gate in any case.
"""
from pathlib import Path

INSTANCE = "django__django-13279"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of the impl region, or the FULL tactic
# body of the proof region, or the frozen obligation's opening two tactic lines,
# so every replacement lands entirely inside the region it means to edit and
# same_spec is preserved by construction. Uniqueness is asserted at import.
# ---------------------------------------------------------------------------

_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    return legacyEncode session\n"
    "  return modernEncode session"
)

_PROOF = (
    "  intro algo session\n"
    "  unfold problem_spec_encode implementation_encode\n"
    "  by_cases h : algo = \"sha1\"\n"
    "  · subst h\n"
    "    refine ⟨fun _ => rfl, fun hne => ?_⟩\n"
    "    exact absurd rfl hne\n"
    "  · have hb : (algo == \"sha1\") = false := by\n"
    "      simpa using h\n"
    "    refine ⟨fun habs => absurd habs h, fun _ => ?_⟩\n"
    "    simp only [Id.run, hb]\n"
    "    rfl"
)

_PROOF_INTRO = (
    "  intro algo session\n"
    "  unfold problem_spec_encode implementation_encode"
)

assert _BASE.count(_IMPL) == 1, "impl region anchor drifted from Solution.lean"
assert _BASE.count(_PROOF) == 1, "proof region anchor drifted from Solution.lean"
assert _BASE.count(_PROOF_INTRO) == 1, "proof-intro anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot satisfy the frozen obligation
# the spec is SPEC-TOO-STRONG. Each keeps the `theorem correct_encode` statement
# byte-identical; none introduces a helper lemma, an axiom, or an assumption
# token.
# ---------------------------------------------------------------------------

# pos-negated-guard: reorder the two exits behind a negated guard — handle the
# non-legacy regime first, fall through to the legacy scheme. Same
# scheme-selection on every input. The frozen script is tuned to the frozen
# guard shape, so the obligation is RE-PROVED with a mirror case split (core
# lemmas only, no new declaration).
_POS_NEG_IMPL = (
    "  if algo != \"sha1\" then\n"
    "    return modernEncode session\n"
    "  return legacyEncode session"
)
_POS_NEG_PROOF = (
    "  intro algo session\n"
    "  unfold problem_spec_encode implementation_encode\n"
    "  by_cases h : algo = \"sha1\"\n"
    "  · subst h\n"
    "    refine ⟨fun _ => ?_, fun hne => absurd rfl hne⟩\n"
    "    simp only [Id.run, bne_self_eq_false]\n"
    "    rfl\n"
    "  · have hb : (algo != \"sha1\") = true := by\n"
    "      simpa [bne] using h\n"
    "    refine ⟨fun habs => absurd habs h, fun _ => ?_⟩\n"
    "    simp only [Id.run, hb]\n"
    "    rfl"
)
POS_NEG = _swap(_swap(_BASE, _IMPL, _POS_NEG_IMPL), _PROOF, _POS_NEG_PROOF)

# pos-let-binding: bind the selected scheme's output to a local before returning
# it in the legacy arm. Same value flow, so the frozen proof body still closes
# (the local zeta-reduces).
_POS_LET_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    let r := legacyEncode session\n"
    "    return r\n"
    "  return modernEncode session"
)
POS_LET = _swap(_BASE, _IMPL, _POS_LET_IMPL)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — a positive control that the obligation is SATISFIABLE at a
# normal, F2P-shaped input rather than only in the abstract. The frozen theorem
# carries no precondition hypothesis (the modeled behavior is total), so the
# nagini precondition-admission probe has no binder to attack; the honest
# analogue discharges the spec predicate at the ground legacy-regime input the
# F2P exercises (the identifier `"sha1"` with the F2P record), inside the proof
# region, alongside the frozen obligation. If that ground instance could not be
# discharged the modeled behavior would be unsatisfiable at exactly the input
# the F2P exercises (the analogue of PRECOND-TOO-STRONG).
# ---------------------------------------------------------------------------
_ADMISS_BLOCK = (
    "  have _ground : problem_spec_encode \"sha1\" [(\"a test key\", \"a test value\")]\n"
    "      (implementation_encode \"sha1\" [(\"a test key\", \"a test value\")]) := by\n"
    "    refine ⟨fun _ => rfl, fun hne => absurd rfl hne⟩\n"
    + _PROOF_INTRO
)
ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_BLOCK)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, so a verifying rival would be a true
# verify-does-not-imply-resolve break rather than an artifact, and (b) a
# refutation witness pinning the violation at one concrete input, checked to hold
# of the rival and to fail on the frozen solution. Each ships the FROZEN proof
# body verbatim (a `sorry` would violate the variant scope), so its rejection is
# the frozen script failing to close against the reshaped impl — which is exactly
# why the witness, not the rejection, attributes the failure to the spec.
# ---------------------------------------------------------------------------

# weak-legacy-corrupt: in the legacy regime, emit the legacy scheme's output with
# an extra byte appended. Attacks (Q-legacy) at algo = "sha1": the result must be
# EXACTLY legacyEncode session, and this is one byte longer.
_WEAK_LEGACY_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    return legacyEncode session ++ \"0\"\n"
    "  return modernEncode session"
)
RIVAL_LEGACY = _swap(_BASE, _IMPL, _WEAK_LEGACY_IMPL)

# weak-modern-corrupt: in the non-legacy regime, emit the modern scheme's output
# with an extra byte appended. Attacks (Q-modern) at algo ≠ "sha1": the result
# must be EXACTLY modernEncode session, and this is one byte longer. Probes the
# OTHER clause and the OTHER binder value (a non-"sha1" identifier, a distinct
# session) so both implications and both binders move.
_WEAK_MODERN_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    return legacyEncode session\n"
    "  return modernEncode session ++ \"0\""
)
RIVAL_MODERN = _swap(_BASE, _IMPL, _WEAK_MODERN_IMPL)

# weak-wrong-scheme-legacy: the LITERAL pre-patch bug — emit the MODERN scheme in
# BOTH regimes, so the legacy regime (algo = "sha1") produces `modernEncode
# session` where (Q-legacy) demands `legacyEncode session`. This is exactly the
# defect the fix removes (the pre-patch impl ignores the identifier and always
# runs the standard scheme) and is the ONLY rival that attacks the DISPATCH
# SELECTION itself rather than the byte-exactness of an already-correctly-selected
# arm. The two corrupt rivals above cannot see a wrong-scheme selection: each
# assumes the right scheme is chosen and only appends to it. Because the schemes
# are opaque, `legacyEncode s ≠ modernEncode s` is not a theorem, so the witness
# cannot COMPUTE the contradiction — it CONDITIONS on it: at the F2P input the two
# schemes disagree (hypothesis `hne`), and the spec then forces the legacy arm to
# equal `legacyEncode`, contradicting the rival's `modernEncode`. The gate's
# consistency probe confirms `hne` is satisfiable (no tactic derives `False` from
# two opaque terms being unequal), so the counterexample input genuinely exists.
_WEAK_WRONG_SCHEME_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    return modernEncode session\n"
    "  return modernEncode session"
)
RIVAL_WRONG_SCHEME = _swap(_BASE, _IMPL, _WEAK_WRONG_SCHEME_IMPL)

# weak-legacy-empty-record: PARTIAL-DOMAIN on the `session` binder. Select the
# RIGHT scheme in the legacy regime, but apply it to the EMPTY record instead of
# the one supplied. (Q-legacy) demands `result = legacyEncode session` for the
# ACTUAL session, so this is correct at exactly `session = []` and wrong at every
# other record — the sub-domain shape the other three rivals cannot express: each
# of them applies the scheme to `session` verbatim and so is wrong uniformly in
# the binder, meaning their rejections never depend on WHICH record is passed.
# This is the only rival whose refutation needs a specific non-empty record.
_WEAK_LEGACY_EMPTY_IMPL = (
    "  if algo == \"sha1\" then\n"
    "    return legacyEncode []\n"
    "  return modernEncode session"
)
RIVAL_LEGACY_EMPTY = _swap(_BASE, _IMPL, _WEAK_LEGACY_EMPTY_IMPL)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
# The schemes are opaque, so a value equality is undecidable; each witness
# derives a STRING-LENGTH contradiction from the appended byte instead.

_WIT_LEGACY = (
    "example : ¬ problem_spec_encode \"sha1\" [(\"a test key\", \"a test value\")]\n"
    "    (implementation_encode \"sha1\" [(\"a test key\", \"a test value\")]) := by\n"
    "  intro h\n"
    "  have h1 := h.1 rfl\n"
    "  have hg : (\"sha1\" == \"sha1\") = true := by decide\n"
    "  simp only [implementation_encode, Id.run, hg, if_true, bind, pure] at h1\n"
    "  have hlen := congrArg String.length h1\n"
    "  rw [String.length_append] at hlen\n"
    "  have h0 : (\"0\").length = 1 := by decide\n"
    "  omega\n"
)

_WIT_MODERN = (
    "example : ¬ problem_spec_encode \"sha256\" [(\"k\", \"v\")]\n"
    "    (implementation_encode \"sha256\" [(\"k\", \"v\")]) := by\n"
    "  intro h\n"
    "  have h1 := h.2 (by decide)\n"
    "  have hg : (\"sha256\" == \"sha1\") = false := by decide\n"
    "  simp only [implementation_encode, Id.run, hg, Bool.false_eq_true, if_false,\n"
    "    bind, pure] at h1\n"
    "  have hlen := congrArg String.length h1\n"
    "  rw [String.length_append] at hlen\n"
    "  have h0 : (\"0\").length = 1 := by decide\n"
    "  omega\n"
)


# weak-wrong-scheme-legacy witness: at algo = "sha1" the spec's legacy clause
# forces result = legacyEncode session; the rival returns modernEncode session.
# Conditioned on the two schemes disagreeing at the F2P input (`hne`) — an opaque
# fact that HOLDS (the two real schemes differ there) and that the frozen solution
# does NOT contradict, so the witness fails on gold (gold's legacy arm returns
# legacyEncode, so `h1 : legacyEncode = legacyEncode`, and `hne _` is a type
# mismatch — the discriminator, not an unfolding gap). Checked: elaborates vs the
# rival (exit 0), fails on gold (exit 1, semantic), probe cannot derive False
# (exit 1, so `hne` is satisfiable).
_WIT_WRONG_SCHEME = (
    "example\n"
    "    (hne : modernEncode [(\"a test key\", \"a test value\")]\n"
    "        ≠ legacyEncode [(\"a test key\", \"a test value\")]) :\n"
    "    ¬ problem_spec_encode \"sha1\" [(\"a test key\", \"a test value\")]\n"
    "    (implementation_encode \"sha1\" [(\"a test key\", \"a test value\")]) := by\n"
    "  intro h\n"
    "  have h1 := h.1 rfl\n"
    "  have hg : (\"sha1\" == \"sha1\") = true := by decide\n"
    "  simp only [implementation_encode, Id.run, hg, if_true, bind, pure] at h1\n"
    "  exact hne h1\n"
)


# weak-legacy-empty-record witness: at algo = "sha1" with the F2P record, the
# spec's legacy clause forces result = legacyEncode <that record>, while the rival
# returns legacyEncode [] — the scheme applied to the WRONG record. Conditioned
# only on the scheme distinguishing the empty record from the F2P record (`hne`),
# which is what makes the sub-domain claim precise: the rival IS correct at
# session = [], so the refutation must name a record where it is not. Checked:
# elaborates vs the rival (exit 0), fails on gold (exit 1), and the type-revealing
# forgery prints `has type True` on gold vs the concrete equation
# `legacyEncode [] = legacyEncode [...]` on the rival, so gold's exit code tracks
# the claim. Probe cannot derive False (exit 1), so `hne` is satisfiable.
_WIT_LEGACY_EMPTY = (
    "example\n"
    "    (hne : legacyEncode ([] : List (String × String))\n"
    "        ≠ legacyEncode [(\"a test key\", \"a test value\")]) :\n"
    "    ¬ problem_spec_encode \"sha1\" [(\"a test key\", \"a test value\")]\n"
    "    (implementation_encode \"sha1\" [(\"a test key\", \"a test value\")]) := by\n"
    "  intro h\n"
    "  have h1 := h.1 rfl\n"
    "  have hg : (\"sha1\" == \"sha1\") = true := by decide\n"
    "  simp only [implementation_encode, Id.run, hg, if_true, bind, pure] at h1\n"
    "  exact hne h1\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_NEG,
        "rationale": "structurally-different CORRECT impl: the two regimes are "
        "reordered behind a negated guard (handle the non-legacy scheme first, "
        "fall through to the legacy scheme). The scheme selected for every "
        "(algo, session) is unchanged, so both implications of the postcondition "
        "still hold; must verify (else SPEC-TOO-STRONG — a faithful correct impl "
        "rejected). Re-proved because the frozen script is tuned to the frozen "
        "guard shape: a mirror case split on `algo = \"sha1\"` closes it using "
        "core lemmas (`bne_self_eq_false`), no new declaration.",
    },
    {
        "id": "pos-let-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LET,
        "rationale": "binding the selected scheme's output to a local before "
        "returning it in the legacy arm keeps the exact value returned on every "
        "branch, so the postcondition is unchanged; a correct reshape must verify "
        "(else SPEC-TOO-STRONG). Proof: the frozen tactic body is retained (the "
        "local zeta-reduces before the case split).",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-legacy-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged at the ground legacy-regime "
        "input the F2P exercises (the identifier `\"sha1\"` with the F2P record) "
        "as a `have` inside the existing tactic body, then the frozen obligation "
        "is closed verbatim. Verifies (else the modeled behavior is unsatisfiable "
        "at the normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
        "assumed: no new declaration, the `correct_encode` statement is "
        "byte-identical, and the ground instance is a `have` prepended to the "
        "frozen tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "weak-legacy-corrupt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_LEGACY,
        "refinement": "a faithful real patch whose legacy-regime serialization "
        "did not reproduce the legacy interchange format EXACTLY (e.g. emitted "
        "the selected scheme's bytes with any extra content) would produce a "
        "string the unchanged legacy reader does not round-trip back to the "
        "record; the F2P test asserts the legacy reader recovers the exact "
        "`{'a test key': 'a test value'}` from the legacy-regime output, so it "
        "would NOT resolve.",
        "rationale": "REJECT from (Q-legacy): at algo = \"sha1\" the result must "
        "be EXACTLY `legacyEncode session`, but this rival returns "
        "`legacyEncode session ++ \"0\"`, which is strictly longer. The schemes "
        "are opaque so the witness derives a string-length contradiction rather "
        "than a value inequality. Attacks the legacy implication at the `\"sha1\"` "
        "identifier and the F2P record.",
        "witness": _WIT_LEGACY,
    },
    {
        "id": "weak-modern-corrupt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_MODERN,
        "refinement": "a faithful real patch whose non-legacy-regime "
        "serialization did not reproduce the current interchange format EXACTLY "
        "would produce a string the current reader does not round-trip; the "
        "pre-existing round-trip tests (exercised outside the legacy regime) "
        "assert the current reader recovers the exact record from the "
        "non-legacy-regime output, so it would NOT resolve. This attacks the "
        "OTHER clause and the OTHER identifier value, so the battery does not "
        "leave the non-legacy regime unpinned.",
        "rationale": "REJECT from (Q-modern): at algo ≠ \"sha1\" the result must "
        "be EXACTLY `modernEncode session`, but this rival returns "
        "`modernEncode session ++ \"0\"`, which is strictly longer. Witness at a "
        "non-\"sha1\" identifier (`\"sha256\"`) and a distinct session, so both "
        "spec binders (`algo`, `session`) take a second value across the reject "
        "witnesses. Opaque schemes → string-length contradiction.",
        "witness": _WIT_MODERN,
    },
    {
        "id": "weak-wrong-scheme-legacy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_WRONG_SCHEME,
        "refinement": "this is the literal pre-patch behavior: `encode` ignores "
        "the configured identifier and always runs the standard scheme. Under the "
        "legacy-regime identifier `\"sha1\"` it emits the standard-scheme string, "
        "which the unchanged legacy reader does NOT round-trip back to the record "
        "(the standard scheme's output is not a legacy-format string). The F2P "
        "asserts that in the legacy regime the produced string round-trips through "
        "the legacy reader to the exact `{'a test key': 'a test value'}` record, so "
        "this impl would NOT resolve — it is exactly the failing behavior the fix "
        "removes.",
        "rationale": "REJECT from (Q-legacy): at algo = \"sha1\" the result must be "
        "EXACTLY `legacyEncode session`, but this rival returns `modernEncode "
        "session` — the WRONG scheme selected, not a corrupted-but-correct scheme. "
        "This is the only rival that attacks the dispatch SELECTION; the two "
        "corrupt rivals assume the right scheme is chosen and merely lengthen it. "
        "The schemes are opaque so `legacyEncode s ≠ modernEncode s` is not a "
        "theorem; the witness therefore conditions on the two schemes disagreeing "
        "at the F2P input (`hne`, which the consistency probe confirms is "
        "satisfiable) and derives the contradiction from the spec's legacy clause. "
        "Fails on gold because gold's legacy arm returns `legacyEncode` verbatim.",
        "witness": _WIT_WRONG_SCHEME,
    },
    {
        "id": "weak-legacy-empty-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_LEGACY_EMPTY,
        "refinement": "a faithful real patch whose legacy-regime serialization "
        "ran the compatibility scheme over an EMPTY record rather than the record "
        "it was given would emit a well-formed legacy-format string that the "
        "unchanged legacy reader round-trips to the EMPTY record, not to the one "
        "supplied. The F2P asserts the legacy reader recovers the exact "
        "`{'a test key': 'a test value'}` record from the legacy-regime output, so "
        "this impl would NOT resolve — it round-trips to `{}` instead. Note it "
        "WOULD pass a round-trip check exercised only on an empty record, which is "
        "exactly why the sub-domain case is needed.",
        "rationale": "REJECT from (Q-legacy), and the only rival that attacks the "
        "`session` binder: at algo = \"sha1\" the result must be EXACTLY "
        "`legacyEncode session` for the session GIVEN, but this rival returns "
        "`legacyEncode []`. It is therefore CORRECT at `session = []` and wrong at "
        "every non-empty record — a genuine partial-domain near-miss, unlike the "
        "other three rivals, each of which is wrong uniformly in `session` (they "
        "pass it through and corrupt or misselect the scheme, so their witnesses "
        "would refute at any record). The schemes are opaque, so the witness "
        "conditions on the compatibility scheme distinguishing the empty record "
        "from the F2P record (`hne`); the consistency probe confirms that is "
        "satisfiable. Fails on gold because gold's legacy arm applies the scheme "
        "to the actual `session`, so the equation reduces to `True` there.",
        "witness": _WIT_LEGACY_EMPTY,
    },
]
