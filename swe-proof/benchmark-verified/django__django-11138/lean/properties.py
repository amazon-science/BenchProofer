"""properties.py — G-PBT falsification battery for django__django-11138 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_tzConvertSql`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled decision):

  tzConvertSql (useTz : Bool) (connTz tzname fieldName : String) : String
    Builds the SQL expression presenting a stored datetime column in a target
    time zone, for a backend that keeps datetimes as naive local values. The
    postcondition pins the result BY FULL VALUE over the WHOLE guard partition,
    with two independent top-level clauses:
      * (useTz = true ∧ connTz ≠ tzname) →
            result = convertTzFragment fieldName connTz tzname
        — the conversion branch: the column expression wrapped in a conversion
          FROM the source (connection) zone TO the target zone;
      * ¬ (useTz = true ∧ connTz ≠ tzname) →
            result = fieldName
        — every other guard combination (tz processing off, OR source zone ==
          target zone) returns the column expression UNCHANGED.
    ``convertTzFragment fieldName srcTz dstTz`` is a fully grounded helper (a
    transparent string concatenation of its three arguments), NOT an opaque
    answer-key: the two zone arguments are pinned to ``connTz`` (source) and
    ``tzname`` (target) in that ORDER, so echoing it without sourcing the
    conversion from the connection zone is impossible. The
    ungrounded-oracle-echo class does not apply. The load-bearing content is
    exactly the two-bug fix the issue reports: (A) the conversion source must be
    the connection zone ``connTz``, not a hard-wired ``'UTC'``; and (B) the
    conversion is SKIPPED when ``connTz = tzname``.

CARRIER NARROWING vs NAGINI.

  The nagini sibling modeled the SAME two-bug behaviour on an ARITHMETIC
  carrier: ``local_walltime(stored, conn_off, target_off, has_target, use_tz)``
  returning an ``int`` minute offset, with the conversion expressed as
  ``stored - conn_off + target_off``. This lean bundle models the SAME logical
  change at the mysql representative site as the ``str → str`` SQL-fragment
  BUILDER (``_convert_field_to_tz``): the observable is the SQL expression, and
  the two bugs surface as (A) which zone name is emitted as the conversion
  SOURCE and (B) whether the wrapping fragment is emitted at all when the zones
  coincide. The adversarial INTENT of every nagini uniqueness rival ports; the
  arithmetic MECHANICS (offset subtraction, sign of the shift) are re-expressed
  as string-fragment mishandling, because on this carrier the ``int`` offset has
  no counterpart — there is no ``conn_off``/``target_off`` value, only the two
  zone NAMES and whether/how they are threaded into the fragment.

  Nagini rival → lean re-expression:
    * weak-prepatch (drop ``- conn_off``; source hard-wired to UTC) →
      weak-utc-source: emit ``'UTC'`` as the conversion source instead of
      ``connTz`` (bug A in ISOLATION — it keeps the equal-zone skip, so it is a
      NEAR-MISS of the frozen impl, not the pre-patch skeleton; the case that
      reproduces the pre-patch impl byte-for-byte is weak-utc-source-skip).
    * weak-drop-conn (subtler UTC-source variant that keeps the branch shape) →
      folded into weak-utc-source and weak-utc-source-skip: on this carrier
      "omit the connection relabel" IS "emit UTC as the source"; the two nagini
      variants differ only in an equal-zone arithmetic restore that has no
      string counterpart, so a single UTC-source rival plus its equal-zone-skip
      variant covers both. Kept as two cases because they attack DIFFERENT
      clauses (see below).
    * weak-sign (convert in the wrong direction, target_off - conn_off flipped)
      → weak-swap-zones: emit the conversion with source/target zone names
      SWAPPED — the wrong-direction conversion, refutable on distinct zones.
    * weak-partial-equalzone (correct on distinct zones, off-by-one exactly on
      the equal-zone sub-domain) → weak-no-skip: still emit the conversion
      fragment when ``connTz = tzname`` instead of returning the column
      unchanged — the partial-domain attack on the equal-zone identity, bug B.
    * weak-partial-notarget / weak-zero (identity / un-restored relabel on a
      precond-admitted sub-domain) → weak-identity: never emit a conversion.
      (There is no ``has_target`` binder on this carrier — the target zone is
      always a plain ``tzname`` string, never absent — so the two nagini
      no-target cases collapse to the single "never convert" identity rival,
      refuted on the distinct-zone sub-domain.)
    * weak-ignore-usetz: a lean-native binder-coverage rival with no distinct
      nagini source — narrow the guard to drop the ``useTz`` term, so the
      ``useTz`` binder is exercised at ``false`` by a rival built to abuse it.

  There are NO nagini FRAME-MUTATION rivals to port. (An earlier revision of
  this docstring claimed "the two nagini FRAME-MUTATION rivals are vacuous on
  this carrier"; that was a fabricated omission — the nagini manifest contains
  no such case. Its SPEC_TESTS is exactly the nine cases enumerated above, and
  its own header records frame-mutation as N/A at the SOURCE: every nagini input
  is an immutable ``int``/``bool`` scalar, so there is no ``Acc(...,1/2)``
  half-permission carrier there either. Nothing was dropped in this lane; the
  count of ported-vs-omitted cases below is the whole story.)

  There is no DIVERGENCE / non-termination lane in the nagini sibling to port
  (its inputs are all scalars). On lean the lane is empty for a MECHANICAL
  reason, verified rather than assumed: ``implementation_tzConvertSql`` is a
  total Lean ``def``, and making it ``partial`` so it can self-loop does not
  buy a vacuous verify — the frozen tactic body fails with ``Tactic `unfold`
  failed to unfold `implementation_tzConvertSql``` (a ``partial`` def has no
  equation lemmas to unfold), so such a rival is REJECTED, not admitted. Lean
  has no ``partial``-semantics escape hatch of the kind recorded for another
  backend in ``the corpus-wide termination-semantics finding``; that finding is explicitly scoped
  to velvet and does not apply here.

  The nagini axiom lane is empty (AXIOM_TESTS == []) and is out of G-PBT scope
  regardless (that lane belongs to G-AX). No axiom case is ported.

POSITIVES. The nagini positives port directly: pos-cheapest (the honest oracle
echo) has no counterpart because the helper here is a plain fragment builder,
not a separate grounded oracle def — the cheapest honest impl IS the branch
that emits ``convertTzFragment``, which pos-reorder and pos-functional both do
in structurally different shapes. pos-reorder ports the nagini "compute the
result the other way and it still verifies" positive (init to the converted
fragment, override to the plain column on the else-guard); pos-functional ports
the nagini branch-reorder / De-Morgan-guard positive as a pure ``if _ ∧ _``
functional impl. admiss-f2p-ground ports the nagini admiss-self probe:
discharge the obligation at a ground F2P-shaped input (tz on, distinct
Bangkok→Nairobi zones — the reported distinct-zone case) inside the existing
tactic body, then close the frozen obligation verbatim.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at one concrete, ``decide``-able input; each was checked to ELABORATE
against its rival (the rival provably contradicts the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). ``decide`` computes on ``String`` here, so every witness uses
concrete literal zone/column names — no opaque term, no conditioning hypothesis
needed. The witnesses spread over EVERY input binder of the predicate:
``useTz`` moves between ``true`` (utc-source, utc-source-skip, swap-zones,
no-skip, identity, drop-column, quote-shape) and ``false`` (ignore-usetz);
``connTz``/``tzname`` take an EQUAL pair (utc-source-skip, no-skip) as well as
several DISTINCT pairs, so the equal-vs-distinct guard binder is exercised at
both settings; and ``fieldName`` is not merely varied across witnesses but
ABUSED by a rival (drop-column substitutes a literal for it), which is what
makes its variation load-bearing rather than two spellings of the same point.

WHERE THE RIVALS AIM. The guard is attacked from every side (source zone wrong,
skip dropped, zones swapped, flag ignored, conversion never emitted), and the
fragment's own three ARGUMENTS are attacked independently: the wrapped operand
(drop-column) and the assembled byte string with all arguments correct
(quote-shape). The latter two were added by the adversarial audit of this
battery; before them every rival threaded ``fieldName`` into a correctly-shaped
``convertTzFragment`` call, so the clause's by-value pinning of the emitted text
was never probed — the battery would equally have passed against a spec that
only required "wraps the column, sourced from connTz".
"""
from pathlib import Path

INSTANCE = "django__django-11138"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---- region anchor: the FULL body of the `impl` region (unique in
# Solution.lean). Every impl replacement below lands entirely inside the impl
# region, so `same_spec` holds and the theorem STATEMENT is untouched. ----
_IMPL_OLD = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz && connTz != tzname then\n"
    "    field := convertTzFragment field connTz tzname\n"
    "  return field"
)

# ---- region anchor: the FULL body of the `proof` region (unique in
# Solution.lean). The positive re-proofs and the admissibility probe swap this
# whole block; the `theorem correct_tzConvertSql : …` STATEMENT above it is
# never touched. ----
_PROOF_OLD = (
    "  intro useTz connTz tzname fieldName\n"
    "  unfold problem_spec_tzConvertSql implementation_tzConvertSql\n"
    "  simp only [Id.run, bind, pure]\n"
    "  constructor\n"
    "  · rintro ⟨hu, hn⟩\n"
    "    have h : (useTz && connTz != tzname) = true := by\n"
    "      simp [hu, bne_iff_ne, hn]\n"
    "    simp [h]\n"
    "  · intro hcon\n"
    "    by_cases h : (useTz && connTz != tzname) = true\n"
    "    · rw [Bool.and_eq_true, bne_iff_ne] at h\n"
    "      exact absurd h hcon\n"
    "    · simp [h]"
)

assert _BASE.count(_IMPL_OLD) == 1, "impl-tzConvertSql drifted"
assert _BASE.count(_PROOF_OLD) == 1, "proof-tzConvertSql drifted"


# ---------------------------------------------------------------------------
# Reshaped impls / proofs for the positive controls.
# ---------------------------------------------------------------------------

# pos-reorder: initialise the accumulator to the CONVERTED fragment and override
# it with the plain column expression on the else-of-the-frozen-guard, rather
# than initialising to the column and wrapping. Same value for every guard
# combination. The frozen proof shape closes it verbatim (the guard `h` /
# `by_cases h` reasoning is identical), so only the impl changes.
_IMPL_REORDER = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := convertTzFragment fieldName connTz tzname\n"
    "  if !(useTz && connTz != tzname) then\n"
    "    field := fieldName\n"
    "  return field"
)

# pos-functional: a pure `if _ = true ∧ _ ≠ _ then … else …` functional impl (no
# `Id.run do` / `let mut`), guard written in the spec's own `∧`/`≠` shape. Needs
# its own (shorter) proof because the frozen `Id.run`-reducing script no longer
# matches; the reproof stays inside the proof region and keeps the theorem
# statement byte-identical.
_IMPL_FUNCTIONAL = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String :=\n"
    "  if useTz = true ∧ connTz ≠ tzname then\n"
    "    convertTzFragment fieldName connTz tzname\n"
    "  else\n"
    "    fieldName"
)
_PROOF_FUNCTIONAL = (
    "  intro useTz connTz tzname fieldName\n"
    "  unfold problem_spec_tzConvertSql implementation_tzConvertSql\n"
    "  constructor\n"
    "  · rintro h\n"
    "    simp [h]\n"
    "  · intro hcon\n"
    "    simp [hcon]"
)

# admiss-f2p-ground: discharge the obligation at a ground F2P-shaped input (tz
# on, distinct Bangkok→Nairobi zones — the reported distinct-zone case) by
# `decide`, then close the frozen obligation verbatim. The impl region is
# unchanged; the ground instance is a `have` prepended inside the existing
# tactic body, so the theorem STATEMENT is byte-identical and nothing new is
# declared.
_PROOF_ADMISS = (
    "  have _ground : problem_spec_tzConvertSql true \"Asia/Bangkok\" \"Africa/Nairobi\" \"col\"\n"
    "      (implementation_tzConvertSql true \"Asia/Bangkok\" \"Africa/Nairobi\" \"col\") := by\n"
    "    unfold problem_spec_tzConvertSql implementation_tzConvertSql\n"
    "    decide\n"
    + _PROOF_OLD
)


# ---------------------------------------------------------------------------
# Wrong impls for the uniqueness rivals.
# ---------------------------------------------------------------------------

# weak-utc-source: emit 'UTC' as the conversion SOURCE instead of the connection
# zone — bug A in ISOLATION. Keeps the equal-zone skip, so it is a NEAR-MISS
# that is CORRECT on the whole ¬(useTz ∧ connTz≠tzname) sub-domain and wrong only
# where the conversion is actually emitted. (The pre-patch skeleton is the
# STRICTLY weaker weak-utc-source-skip, which drops the skip as well.)
_RIVAL_UTC_SOURCE = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz && connTz != tzname then\n"
    "    field := convertTzFragment field \"UTC\" tzname\n"
    "  return field"
)

# weak-utc-source-skip: the FULL pre-patch bug — UTC source AND no equal-zone
# skip (convert whenever tz processing is on). Attacks both clauses at once.
_RIVAL_UTC_NOSKIP = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz then\n"
    "    field := convertTzFragment field \"UTC\" tzname\n"
    "  return field"
)

# weak-swap-zones: convert in the WRONG direction — source/target zone names
# swapped (target as source, connection as target).
_RIVAL_SWAP = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz && connTz != tzname then\n"
    "    field := convertTzFragment field tzname connTz\n"
    "  return field"
)

# weak-no-skip: source zone is correct (connTz), but the equal-zone skip is
# dropped — still emit the conversion when connTz = tzname (bug B).
_RIVAL_NO_SKIP = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz then\n"
    "    field := convertTzFragment field connTz tzname\n"
    "  return field"
)

# weak-ignore-usetz: drop the useTz term from the guard — convert whenever the
# zones differ, even with tz processing off.
_RIVAL_IGNORE_USETZ = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if connTz != tzname then\n"
    "    field := convertTzFragment field connTz tzname\n"
    "  return field"
)

# weak-identity: never emit a conversion; return the column expression unchanged.
_RIVAL_IDENTITY = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  return field"
)

# weak-drop-column: guard and BOTH zone arguments are correct; the WRAPPED
# operand is a fixed literal instead of the incoming column expression, so the
# emitted fragment converts the wrong thing. Added by audit: every other rival
# threads `fieldName` into the fragment correctly, so the `fieldName` binder was
# exercised only as an inert literal that no rival was built to abuse. This
# attacks the fragment's FIRST argument — the one the two-bug story leaves
# unguarded — and so probes the clause's value-pinning rather than its guard.
_RIVAL_DROP_COLUMN = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz && connTz != tzname then\n"
    "    field := convertTzFragment \"value\" connTz tzname\n"
    "  return field"
)

# weak-quote-shape: guard, operand and both zone names are all correct and in the
# right ORDER; only the fragment's literal punctuation differs (double quotes
# around the zone names instead of single quotes). Added by audit: the emitted
# SQL text is the whole observable on this carrier, so a rival that gets every
# argument right and still emits a different string is the sharpest test that the
# spec pins the fragment BY VALUE and not merely "wraps the column, sourced from
# connTz". Its faithful real patch emits SQL the database does not accept.
_RIVAL_QUOTE_SHAPE = (
    "def implementation_tzConvertSql\n"
    "    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do\n"
    "  let mut field := fieldName\n"
    "  if useTz && connTz != tzname then\n"
    "    field := \"CONVERT_TZ(\" ++ field ++ \", \\\"\" ++ connTz\n"
    "      ++ \"\\\", \\\"\" ++ tzname ++ \"\\\")\"\n"
    "  return field"
)


def _witness(useTz, connTz, tzname, fieldName):
    """A refutation snippet stating ¬spec at a concrete input, discharged by
    `decide` (String computes). Elaborates against a rival that violates the
    spec there; FAILS against the frozen solution (which satisfies it)."""
    return (
        f"example : ¬ problem_spec_tzConvertSql {useTz} {connTz} {tzname} {fieldName}\n"
        f"    (implementation_tzConvertSql {useTz} {connTz} {tzname} {fieldName}) := by\n"
        "  unfold problem_spec_tzConvertSql implementation_tzConvertSql\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _IMPL_REORDER),
        "rationale": "A correct reshape of the sole obligation: the accumulator "
                     "is initialised to `convertTzFragment fieldName connTz "
                     "tzname` and overridden with the plain `fieldName` exactly "
                     "when `!(useTz && connTz != tzname)`, so on every guard "
                     "combination it returns the same value as the frozen impl "
                     "(conversion iff `useTz=true ∧ connTz≠tzname`). If it "
                     "cannot verify, the postcondition is SPEC-TOO-STRONG. The "
                     "frozen proof body closes it verbatim — the guard case "
                     "split reduces identically on the reshaped `Id.run do`.",
    },
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_OLD, _IMPL_FUNCTIONAL),
            _PROOF_OLD,
            _PROOF_FUNCTIONAL,
        ),
        "rationale": "A structurally different CORRECT impl: a pure "
                     "`if useTz = true ∧ connTz ≠ tzname then convertTzFragment "
                     "… else fieldName` (no `Id.run do`/`let mut`), the guard "
                     "written directly in the spec's `∧`/`≠` shape. Returns the "
                     "conversion fragment on exactly the conversion sub-domain "
                     "and the column otherwise, matching the frozen impl "
                     "pointwise. Because the imperative-reducing frozen script "
                     "no longer matches, the proof is reshaped INSIDE the proof "
                     "region (the theorem statement is byte-identical): the "
                     "guard is the first clause's own hypothesis, so both "
                     "clauses close by `simp [h]` / `simp [hcon]`. Must verify "
                     "(else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_OLD, _PROOF_ADMISS),
        "rationale": "The frozen theorem is unconditional (no precondition "
                     "binder); the honest admissibility probe discharges the "
                     "spec at a ground F2P-shaped input — the conversion branch "
                     "(tz on, distinct connection→target zones Bangkok→Nairobi, "
                     "the reported distinct-zone case) — by `decide`, then "
                     "closes the frozen obligation verbatim. Verifies (else the "
                     "spec is unsatisfiable at a normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: the ground "
                     "instance is a `have` inside the existing tactic body, the "
                     "impl region and the theorem statement are unchanged.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input,
    # checked to elaborate against the rival and fail on the frozen solution.
    # =====================================================================
    {
        "id": "weak-utc-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_UTC_SOURCE),
        "refinement": "Bug A in ISOLATION: the conversion source is "
                      "hard-wired to a fixed UTC literal rather than the "
                      "connection's configured zone. Its faithful real patch "
                      "sources the conversion from the wrong zone, so on a "
                      "connection whose configured zone is not UTC the emitted "
                      "SQL converts from the wrong origin and the date-lookup "
                      "F2P reads the wrong date — exactly the failure the issue "
                      "reports. It does NOT resolve.",
        "rationale": "REJECT from the conversion-branch clause "
                     "`(useTz=true ∧ connTz≠tzname) → result = convertTzFragment "
                     "fieldName connTz tzname`: the rival emits the fixed UTC "
                     "literal as the source instead of `connTz`, so the fragment "
                     "differs whenever the connection zone is not that literal. "
                     "Refuted at (true, Asia/Bangkok, Africa/Nairobi, col) — a "
                     "distinct-zone input with a non-UTC source.",
        "witness": _witness("true", '"Asia/Bangkok"', '"Africa/Nairobi"', '"col"'),
    },
    {
        "id": "weak-utc-source-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_UTC_NOSKIP),
        "refinement": "The FULL pre-patch skeleton: UTC-sourced conversion AND "
                      "no equal-zone skip (wrap whenever tz processing is on). "
                      "Its faithful real patch is the unpatched code the issue "
                      "reports — both the wrong-source date error AND the "
                      "spurious conversion when the zones coincide (which needs "
                      "a populated tz table the issue notes is absent). It does "
                      "NOT resolve. Refuted on the EQUAL-zone sub-domain, which "
                      "distinguishes it from weak-utc-source (that near-miss is "
                      "correct on equal zones because it keeps the skip).",
        "rationale": "REJECT from the unchanged-branch clause "
                     "`¬(useTz=true ∧ connTz≠tzname) → result = fieldName`: on "
                     "the sub-domain useTz=true, connTz=tzname the rival still "
                     "emits a conversion fragment instead of the bare column. "
                     "Refuted at (true, Africa/Nairobi, Africa/Nairobi, dt) — "
                     "an equal-zone input (weak-no-skip pins that same "
                     "connTz=tzname setting; what is UNIQUE to this case is "
                     "that the SOURCE bug is present too, so it is refutable on "
                     "BOTH sub-domains and is the strictly weaker rival).",
        "witness": _witness("true", '"Africa/Nairobi"', '"Africa/Nairobi"', '"dt"'),
    },
    {
        "id": "weak-swap-zones",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_SWAP),
        "refinement": "Converts in the WRONG direction: source and target zone "
                      "names are swapped (target treated as origin, connection "
                      "as destination). A faithful real patch that reversed the "
                      "conversion arguments produces the inverse offset — it "
                      "does not yield the connection→app-zone value the date "
                      "lookup expects, so it does NOT resolve.",
        "rationale": "REJECT from the conversion-branch clause "
                     "`(useTz=true ∧ connTz≠tzname) → result = convertTzFragment "
                     "fieldName connTz tzname`: the rival emits "
                     "`convertTzFragment fieldName tzname connTz` (arguments "
                     "swapped), which differs from the pinned fragment whenever "
                     "the two zones differ. Refuted at (true, P, Q, colx) — a "
                     "distinct-zone input.",
        "witness": _witness("true", '"P"', '"Q"', '"colx"'),
    },
    {
        "id": "weak-no-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_NO_SKIP),
        "refinement": "Bug B in isolation: the conversion source is CORRECT "
                      "(the connection zone), but the equal-zone skip is "
                      "dropped, so a conversion fragment is emitted even when "
                      "the connection zone already equals the target. A faithful "
                      "real patch that fixed the source but not the skip still "
                      "wraps the column in CONVERT_TZ when the zones coincide, "
                      "which needs the populated tz table the issue notes is "
                      "absent — it does NOT resolve the equal-zone case the "
                      "issue explicitly demands works.",
        "rationale": "REJECT from the unchanged-branch clause "
                     "`¬(useTz=true ∧ connTz≠tzname) → result = fieldName`: on "
                     "the sub-domain useTz=true, connTz=tzname the rival emits "
                     "`convertTzFragment fieldName connTz tzname` instead of the "
                     "bare column. Refuted at (true, Europe/Paris, Europe/Paris, "
                     "ts) — an equal-zone input.",
        "witness": _witness("true", '"Europe/Paris"', '"Europe/Paris"', '"ts"'),
    },
    {
        "id": "weak-ignore-usetz",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_IGNORE_USETZ),
        "refinement": "Drops the tz-processing flag from the guard: emits a "
                      "conversion whenever the zones differ, even with tz "
                      "processing off. A faithful real patch that ignored the "
                      "flag would wrap columns in CONVERT_TZ in the "
                      "non-tz-aware legacy configuration, where the value must "
                      "be presented in the zone it is already recorded in — "
                      "corrupting the legacy read path, so it does NOT resolve.",
        "rationale": "REJECT from the unchanged-branch clause "
                     "`¬(useTz=true ∧ connTz≠tzname) → result = fieldName`: on "
                     "the sub-domain useTz=false, connTz≠tzname the rival emits "
                     "a conversion fragment instead of the bare column. Refuted "
                     "at (false, A, B, field0) — the only witness with "
                     "useTz=false, so the useTz binder is exercised at a value "
                     "no other rival probes.",
        "witness": _witness("false", '"A"', '"B"', '"field0"'),
    },
    {
        "id": "weak-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_IDENTITY),
        "refinement": "Pure identity: never emits a conversion, returning the "
                      "column expression unchanged on every input. The faithful "
                      "real patch is the code with the whole conversion removed "
                      "— the stored connection-zone value is never re-expressed "
                      "in the target zone, so a date lookup in a distinct active "
                      "zone reads the wrong date and the F2P fails to resolve.",
        "rationale": "REJECT from the conversion-branch clause "
                     "`(useTz=true ∧ connTz≠tzname) → result = convertTzFragment "
                     "fieldName connTz tzname`: the rival returns the bare "
                     "column on the conversion sub-domain, differing from the "
                     "required fragment whenever the zones differ. Refuted at "
                     "(true, S, T, colr) — a distinct-zone input.",
        "witness": _witness("true", '"S"', '"T"', '"colr"'),
    },
    {
        "id": "weak-drop-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_DROP_COLUMN),
        "refinement": "The guard and both zone names are correct; the operand "
                      "being converted is a fixed literal rather than the "
                      "incoming column expression. A faithful real patch that "
                      "did this emits a conversion of a constant instead of the "
                      "column, so the date lookup compares against a value that "
                      "has nothing to do with the row — every such read is "
                      "wrong, and it does NOT resolve.",
        "rationale": "REJECT from the conversion-branch clause "
                     "`(useTz=true ∧ connTz≠tzname) → result = convertTzFragment "
                     "fieldName connTz tzname`: the rival wraps a fixed literal "
                     "rather than `fieldName`, so the fragment differs whenever "
                     "the column expression is not that literal. This is the "
                     "only rival that abuses the `fieldName` binder — the other "
                     "rivals all thread it correctly and vary only the guard or "
                     "the zone arguments. Refuted at (true, Europe/Paris, UTC, "
                     "mycol).",
        "witness": _witness("true", '"Europe/Paris"', '"UTC"', '"mycol"'),
    },
    {
        "id": "weak-quote-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _RIVAL_QUOTE_SHAPE),
        "refinement": "Every ARGUMENT is right — the guard, the wrapped column, "
                      "and both zone names in the correct source→target order — "
                      "and only the emitted fragment's quoting differs. A "
                      "faithful real patch quoting the zone names this way emits "
                      "SQL the database rejects rather than the intended "
                      "conversion, so the date lookup errors instead of reading "
                      "the converted value: it does NOT resolve.",
        "rationale": "REJECT from the conversion-branch clause "
                     "`(useTz=true ∧ connTz≠tzname) → result = convertTzFragment "
                     "fieldName connTz tzname`: the clause pins the result to "
                     "that fragment BY VALUE, so an impl that assembles a "
                     "different byte string from the same correctly-ordered "
                     "parts violates it. This is the sharpest probe that the "
                     "spec pins the emitted text and not merely the weaker "
                     "'wraps the column, sourced from connTz' shape — no other "
                     "rival gets every argument right and still fails. Refuted "
                     "at (true, Europe/Paris, UTC, mycol).",
        "witness": _witness("true", '"Europe/Paris"', '"UTC"', '"mycol"'),
    },
]

# The nagini axiom lane is empty (AXIOM_TESTS == []); nothing to port, and the
# axiom lane is G-AX's job regardless.
AXIOM_TESTS = []
