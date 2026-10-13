"""properties.py — G-PBT falsification battery for django__django-16315 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct conflictColumns`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the DISCRIMINATION SUBJECT — normally the frozen solution, but where the
frozen impl cannot DECIDE anything (this bundle: see WITNESS MECHANICS) the
subject is the case's declared ``witness_reference``, a loop-free impl of the
same frozen spec that the gate independently checks shares the spec AND
VERIFIES).

DEFENDED SURFACE (one contracted method):

  conflictColumns (fields : List Field) return (out : List (List Char))
    ensures out = dbColumns fields                      -- the WHOLE pin (C1)

Each element of ``fields`` is a persisted field abstracted to its two observable
string attributes: the model-side attribute name (``attr``) and the database
column (``column``). When a field is declared with an explicit database column
the two differ; otherwise the column equals the attribute. The method produces
the ordered list of tokens that identify each field in a generated
conflict-resolution clause; each token MUST be the field's DATABASE COLUMN, in
order. The pure region pins the whole outcome as a total function of the
method's own input:

  dbColumns []        = []
  dbColumns (f :: fs) = [f.column] ++ dbColumns fs

so C1 (``out = dbColumns fields``) is the sole impl-constraining clause and it is
GROUNDED: ``dbColumns`` is a transparent front-recursive fold over the method's
own argument (the ``axioms`` region is empty; there is NO opaque answer-key
oracle), so pinning ``out = dbColumns fields`` cannot be satisfied by a wrong
echo — it forces the per-field ``column`` projection, in order, for the whole
list. C1 pins THREE independent things about the output, each attacked by some
rival below:

  * (V) VALUE — each element is the field's ``column``, NOT its ``attr``. This is
        the behaviour the change under test turns on: the storage COLUMN vs the
        in-memory attribute NAME. The discriminator bites exactly when a field
        carries an explicit db column so ``column != attr``.
  * (O) ORDER — the tokens appear in the SAME order as ``fields``.
  * (L) LENGTH — one token per field (``|out| = |fields|``).

The sole input binder ``fields`` is free (no ``require`` clause) and the
post-image must hold for EVERY value; the reject witnesses vary it across the
per-field ``attr``/``column`` split (fields where the two agree and where they
differ), list order, and list length.

The F2P declares fields with mixed-case explicit db columns (an attribute under
a lower-case name, its column in mixed case), so ``column != attr`` on those
fields; a rival that emits the ATTRIBUTE verifies-but-does-not-resolve only if
the spec is too weak — that is the central attack here.

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case accounting
in the footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO mandatory
    frame-mutation rivals: each keeps a correct value but WRITES back through a
    read-only registry input held at a fractional heap permission
    (``Acc(list_pred(field_columns),1/2)`` / ``1/4``) and is rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``fields`` is an immutable value, this bundle declares no ``mut`` binder, and
    there is no heap, aliasing, or permission system to subvert. There is no
    read-only input to overwrite, so the class is vacuous. No substitute probe is
    fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    records for its grounded ``column_for`` walk. The post-image C1 is
    ``dbColumns fields``, a transparent fold over the method's own argument; there
    is no opaque answer key to echo. The honest cheapest CORRECT impl (``return
    dbColumns fields``) is carried as a POSITIVE control instead — it doubles as
    proof the spec is not echo-vulnerable, since any impl emitting the ATTRIBUTE
    (or a scrambled/short list) fails ``out = dbColumns fields``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. A rival can
    emit the ATTRIBUTE for every field (the pre-change dataflow), or only for the
    FIRST field (a genuine partial-domain break, correct on every field whose
    attribute already equals its column), or scramble the token ORDER, or DROP a
    field so the token count is short.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS ON THIS BUNDLE. C1's carrier is fully TRANSPARENT (``dbColumns``
and ``Field`` are concrete ``def``/``structure``; the ``axioms`` region is
empty), so the postcondition is decidable at concrete inputs — but the tester
path is unnecessary here, and each rival is written LOOP-FREE (a ``fields.map`` /
``match`` on the head), so its extracted program ``conflictColumnsExec`` — the
``NonDetT``-run of the impl — REDUCES fully under ``decide`` at a concrete input.
Each witness states, at one concrete input,

    (match conflictColumnsExec <input> with | DivM.res r => r | _ => [])
        ≠ dbColumns <input>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator sees (measured: exit 0 on each rival).

THE FROZEN IMPL CANNOT BE THE DISCRIMINATION SUBJECT, so each reject case names a
``witness_reference`` instead. Gold's body is the backward ``while`` fold under
``loom.semantics.choice "demonic"``; its ``conflictColumnsExec`` elaborates
through machinery the kernel cannot unfold, so ``decide`` never reaches a verdict
against gold — the build fails with

    `decide` failed ... its `Decidable` instance instDecidableNot did not reduce
    to `isTrue` or `isFalse` ... reduction got stuck at ... `.hasDecEq`

That is a STUCK REDUCTION, not a refutation: the kernel never evaluated the
claim, so gold's exit code carries no information and would attest to a
discrimination never performed. The gate screens exactly this
(``gates/pbt.py`` ``_STUCK_REDUCTION`` -> ``witness-undecided``), and three
independent witness shapes were measured stuck or unprovable on gold here:
the ``…Exec`` match refuted by ``decide`` (stuck ``.hasDecEq``), the full tester
(``derive_tester_for`` -> ``conflictColumnsTester [f] = false``, also stuck), and
a hypothesis-conditioned form over ``conflictColumnsExec … = DivM.res r``
(unsolved goals on BOTH sides, so not a discriminator either). The property is
gold's LOOP, not the carrier: C1's carrier is fully transparent.

So each reject case declares ``witness_reference = _POS_DIRECT``, the loop-free
``return (dbColumns fields)`` impl also shipped as ``pos-control-direct``. The
gate checks that reference shares the frozen spec and VERIFIES before using it
(``_reference_ok``), and an impl the verifier ACCEPTS cannot violate its own
spec — so a witness that fails there fails for a semantic reason. Measured, the
subject-side failure is a genuine refutation, not a stuck term:

    `decide` proved that the proposition ... ≠ dbColumns [...] is false

i.e. the reference's output EQUALS the post-image at that input while the rival's
does not — the discrimination the gate requires, actually performed. No witness
binds a hypothesis (every input is a concrete ``Field`` literal that decides C1),
so no consistency probe is needed. No banned token (sorry/admit/native_decide/
axiom/opaque). Every build was re-run with ``scripts/lean_verify.sh``: rival exit
0, reference exit 1 by refutation (`decide` proved it false), and gold exit 1 by
stuck reduction — which is why gold is not the subject.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares no consumed
``axiom`` and no deep-model reference (mapping.md §3: ``Field.column`` is a plain
projection carried by the structure, checked by G-CONF, not axiomatized); the
nagini sibling's single axiom-soundness probe over the real Django callee is
G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16315"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let mut acc : List (List Char) := []\n"
    "    let mut i := fields.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
    "      invariant acc = dbColumns (fields.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let f := fields[i - 1]!\n"
    "      acc := [f.column] ++ acc\n"
    "      i := i - 1\n"
    "    return acc\n"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct conflictColumns by\n"
    "  loom_solve\n"
    "  rw [dbColumns_drop_step fields i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for loop-free correct reshapes,
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble + builder. C1's carrier is transparent, so a witness
# ---- extracts the executable program and refutes C1 directly on the
# ---- transparent `dbColumns`. Each rival is loop-free so its `…Exec` reduces
# ---- under `decide`; gold's `while`-loop `…Exec` stays stuck. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT = "extract_program_for conflictColumns\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match conflictColumnsExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ dbColumns ({inp}) := by\n"
        "  decide\n"
    )


# Concrete `Field` literals used by the witnesses. `_FA`/`_FB` carry an explicit
# db column so `column != attr` (the override sub-domain, where the value bug
# bites); `_FG` has `column = attr` (no override, where an attr-echoing rival is
# CORRECT — used to make the partial-domain rival's separating point precise).
_FA = "{ attr := ['a'], column := ['A'] }"
_FB = "{ attr := ['b'], column := ['B'] }"
_FG = "{ attr := ['g'], column := ['g'] }"


# ---- THE DISCRIMINATION SUBJECT for every reject case. Gold's `while` loop
# ---- makes `decide` STUCK (see WITNESS MECHANICS), so gold's exit code
# ---- discriminates nothing and the frozen impl cannot serve as the second
# ---- subject. This loop-free impl of the SAME frozen spec can: it reduces, and
# ---- the gate independently checks it shares the spec and VERIFIES before
# ---- refuting any witness against it. It is byte-identical to the module of the
# ---- `pos-control-direct` positive, which is separately required to verify — so
# ---- the reference's fitness is asserted twice and checked twice.
_POS_DIRECT = _impl_reproved(
    "    return (dbColumns fields)\n",
    "prove_correct conflictColumns by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole token sequence DIRECTLY via the transparent
        # fold, no per-field loop. C1 is literally `out = dbColumns fields`, so
        # this is the cheapest HONEST correct impl — and, since `dbColumns fields`
        # is GROUNDED in the argument (not an opaque answer key), it doubles as
        # proof the spec is not echo-vulnerable (any impl emitting the ATTRIBUTE,
        # or a scrambled/short list, fails `out = dbColumns fields`). The loop is
        # gone, so the frozen proof's backward-fold step is unneeded and the
        # residual goal closes under `loom_solve` alone.
        # Also serves as the reject lane's `witness_reference` (_POS_DIRECT):
        # the SAME source object, so the impl the gate checks verifies here is
        # byte-identically the impl every witness is refuted against.
        "module": _POS_DIRECT,
        "rationale": (
            "the post-image `dbColumns fields` is GROUNDED in the input (a total "
            "front-recursive fold, no opaque answer key), so `return dbColumns "
            "fields` is the honest cheapest CORRECT impl; C1 is literally `out = "
            "dbColumns fields`, so it MUST verify, else C1 is SPEC-TOO-STRONG. "
            "Ports the nagini pos-cc-local-reshape / echo-attempt-honest spirit: "
            "the cheapest impl satisfying the grounded pin, showing the spec is "
            "not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-local-column",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-field DATABASE
        # COLUMN to a typed local `c` before prepending it. Same value flow
        # (`c = f.column`), different control shape; the frozen proof still closes
        # unchanged (the loop invariant and step lemma are untouched).
        "module": _impl(
            "    let mut acc : List (List Char) := []\n"
            "    let mut i := fields.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
            "      invariant acc = dbColumns (fields.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let f := fields[i - 1]!\n"
            "      let c := f.column\n"
            "      acc := [c] ++ acc\n"
            "      i := i - 1\n"
            "    return acc\n"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the per-field "
            "database column to a typed local before prepending it) must verify; "
            "the value flow is unchanged (`c = f.column`) so C1 still discharges "
            "and the frozen loop proof closes as-is. Ports the nagini "
            "pos-lookup-local-reshape: if it fails => SPEC-TOO-STRONG (over-fit to "
            "the inline-prepend code form)."
        ),
    },
    {
        "id": "pos-control-map-reproved",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E). The two shipped positives were both close to
        # the frozen text: one keeps gold's loop verbatim plus a `let`, the other
        # echoes the post-image term `dbColumns fields` literally — so neither
        # forces the SPEC to accept an independently-computed answer, and a spec
        # over-fit to the term `dbColumns fields` would still have passed both.
        # This impl computes the tokens by a genuinely DIFFERENT total function
        # (`List.map` of the `column` projection: no loop, no invariant, and not
        # the post-image term) and must be RE-PROVEN from scratch by induction on
        # `fields` — the frozen backward-fold step lemma is useless to it. So it
        # is the first positive whose verification is evidence about C1 rather
        # than about syntactic proximity to gold.
        "module": _impl_reproved(
            "    return (fields.map (fun f => f.column))\n",
            "prove_correct conflictColumns by\n"
            "  loom_solve\n"
            "  induction fields with\n"
            "  | nil => simp [dbColumns]\n"
            "  | cons f fs ih => simp [dbColumns, ih]"),
        "rationale": (
            "a CORRECT impl computing the token list by a different total "
            "function (`fields.map (·.column)`) — not gold's loop and not the "
            "post-image term `dbColumns fields` — must verify. `List.map` is "
            "extensionally equal to the front-recursive `dbColumns` fold but not "
            "definitionally so on this carrier: the frozen proof does NOT close "
            "it (measured: the backward-fold step lemma does not apply) and the "
            "obligation is re-discharged by induction on `fields`. If it failed "
            "=> SPEC-TOO-STRONG (C1 over-fit to gold's fold shape rather than to "
            "the token sequence it denotes)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-lookup-precond-establishable.
    # That case established that the sub-call's read-only precondition (well-
    # formed registry + name present) is derivable from the caller's own
    # Requires. This method carries NO `require` clause (the pre-conditions region
    # is empty) and models no separate sub-call, so the classic "the precondition
    # admits a normal input" probe is vacuous. Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is jointly
    # SATISFIABLE by a gold-shaped computation. The frozen impl discharging the
    # ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the token builder is total over "
            "every field list; the gold impl discharging the ensures is the "
            "admissibility witness that the post-image `out = dbColumns fields` is "
            "satisfiable. Near-trivial precisely because the precondition is "
            "empty. Re-aimed from the nagini admiss-lookup-precond-establishable, "
            "whose read-only-precondition half has no counterpart on this "
            "referentially-transparent, precondition-free carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = dbColumns
    # fields`); the input binder `fields` is varied across the per-field
    # attr/column split, list order, and list length.
    # =====================================================================
    {
        "id": "rival-emit-attr",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE (V): emit each field's ATTRIBUTE instead of its database COLUMN.
        # This is the pre-change dataflow — the token identifying a field is its
        # in-memory attribute name, not its storage column.
        "module": _impl("    return (fields.map (fun f => f.attr))\n"),
        "refinement": (
            "emitting `f.attr` per field is the PRE-CHANGE behaviour: the "
            "conflict-resolution clause is built from the in-memory attribute "
            "names, not the storage columns. Its faithful real patch is the "
            "unpatched repo, whose generated clause names the attribute (e.g. a "
            "lower-case attribute) rather than the mixed-case column, so the F2P "
            "test_update_conflicts_unique_fields_update_fields_db_column stays "
            "FAILING — a verify here would be verify-but-not-resolve. This is the "
            "exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (`out = dbColumns fields`) on the VALUE (V): "
            "`dbColumns` pins each token to the field's `column`, so a rival "
            "emitting `attr` diverges from the post-image on every field whose "
            "attribute differs from its column. Refuted at a single field with "
            "`column != attr`. If it verified => SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness(f"[{_FA}]"),
        # Gold cannot DECIDE this witness (its `while` loop leaves `decide`
        # stuck, not refuted), so the discrimination subject is the loop-free
        # verifying impl of the same frozen spec. See WITNESS MECHANICS.
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "rival-emit-attr-first",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (V): emit the correct COLUMN for every field EXCEPT the
        # first, whose ATTRIBUTE is emitted. Correct on every field list whose
        # first field already has `column = attr`, and on every non-first field;
        # the divergence is confined to lists whose head carries an override.
        "module": _impl(
            "    match fields with\n"
            "    | [] => return []\n"
            "    | f :: rest => return ([f.attr] ++ rest.map (fun g => g.column))\n"),
        "refinement": (
            "emits the database column correctly for every field EXCEPT the first, "
            "for which it emits the attribute. A faithful real patch of this shape "
            "(special-casing the first conflict target) would still name the "
            "attribute for any field list whose FIRST field carries a db-column "
            "override, and the F2P keys on such a first field, so the produced "
            "clause names the attribute there and the test would NOT resolve. A "
            "genuine partial-domain break — correct on every non-first field and "
            "on any first field without an override. Ports the nagini "
            "rej-lookup-returns-arg-name as a distinct wrong-identifier surface "
            "confined to a sub-domain."
        ),
        "rationale": (
            "REJECT from C1 (`out = dbColumns fields`) on the VALUE (V): C1 pins "
            "the WHOLE sequence including index 0, so a rival that mis-emits only "
            "the leading field still diverges from `dbColumns fields` on lists "
            "whose head has `column != attr`. Refuted at input `[FA, FG]` — a "
            "DISTINCT point from rival-emit-attr (a leading override field "
            "followed by a NON-override field `FG` where `column = attr`, so the "
            "tail is emitted correctly and only the head diverges), varying the "
            "`fields` binder across the attr==column / attr!=column split. If it "
            "verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness(f"[{_FA}, {_FG}]"),
        # Gold cannot DECIDE this witness (its `while` loop leaves `decide`
        # stuck, not refuted), so the discrimination subject is the loop-free
        # verifying impl of the same frozen spec. See WITNESS MECHANICS.
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER (O): emit the correct per-field COLUMNS but in REVERSED order — so
        # each position gets a neighbouring field's column. On a two-field list
        # this is exactly the off-by-one / wrong-field resolution (position 0 gets
        # field 1's column).
        "module": _impl("    return ((fields.map (fun f => f.column)).reverse)\n"),
        "refinement": (
            "emitting the columns in reversed order is a wrong-field resolution: "
            "each conflict-target position names a neighbouring field's column "
            "(on the F2P's two-field registry, the first target would name the "
            "second field's column and vice versa). A real patch producing tokens "
            "in the wrong order hands the wrong db column per position, so the F2P "
            "assertion on the produced clause fails and it would NOT resolve. "
            "Ports the nagini rej-lookup-off-by-one-column (a neighbouring slot's "
            "column) as an order/position violation."
        ),
        "rationale": (
            "REJECT from C1 (`out = dbColumns fields`) on the ORDER (O): "
            "`dbColumns` pins the tokens in the SAME order as `fields`, so a rival "
            "that reverses them diverges whenever two fields have distinct "
            "columns. Refuted at input `[FA, FB]` — two fields with distinct "
            "columns, a distinct point from the value rivals, so reversing "
            "genuinely reorders. If it verified => SPEC-TOO-WEAK (order "
            "unconstrained)."
        ),
        "witness": _witness(f"[{_FA}, {_FB}]"),
        # Gold cannot DECIDE this witness (its `while` loop leaves `decide`
        # stuck, not refuted), so the discrimination subject is the loop-free
        # verifying impl of the same frozen spec. See WITNESS MECHANICS.
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "rival-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # LENGTH (L): drop the FIRST field's token, so the output is length
        # len-1 / order-shifted. Correct on the empty list; wrong length and
        # wrong element-0 on any non-empty input.
        "module": _impl("    return ((fields.map (fun f => f.column)).tail)\n"),
        "refinement": (
            "dropping the first field's token omits a conflict target from the "
            "generated clause (e.g. omits the first unique field). A real patch "
            "that skipped the first field would not key the upsert on it, so the "
            "F2P's expected rows/columns differ from what is produced and it would "
            "NOT resolve. Ports the nagini rej-cc-skip-first."
        ),
        "rationale": (
            "REJECT from C1 (`out = dbColumns fields`) on the LENGTH (L): "
            "`dbColumns` yields one token per field, so a rival that drops the "
            "first token is length len-1 (and element-shifted) for any non-empty "
            "input, diverging from the post-image. Refuted at input `[FG, FB]` — "
            "a leading NON-override field `FG` (so this is a pure length/omission "
            "break, NOT a value-echo: even the correct column of the dropped field "
            "would still be missing), a distinct point that abuses the LENGTH "
            "clause rather than the value or order clauses. If it verified => "
            "SPEC-TOO-WEAK (length/omission unconstrained)."
        ),
        "witness": _witness(f"[{_FG}, {_FB}]"),
        # Gold cannot DECIDE this witness (its `while` loop leaves `decide`
        # stuck, not refuted), so the discrimination subject is the loop-free
        # verifying impl of the same frozen spec. See WITNESS MECHANICS.
        "witness_reference": _POS_DIRECT,
    },
    {
        "id": "rival-spurious-token-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). BOUNDARY (L at zero). Every other rival in
        # this battery is refuted at a NON-EMPTY list, and all four agree with
        # gold at `[]` (checked: `emit-attr`, `emit-attr-first`, `reverse` and
        # `drop-first` all return `[]` there). So the empty list — the one input
        # where the whole output is forced to be empty rather than merely
        # correct-per-element — was left entirely unattacked, and a spec that
        # constrained C1 only on non-empty lists would have passed the shipped
        # battery unchanged. This rival is CORRECT on every non-empty input and
        # wrong only at `[]`, where it emits one spurious empty token.
        "module": _impl_reproved(
            "    match fields with\n"
            "    | [] => return [[]]\n"
            "    | f :: fs => return (dbColumns (f :: fs))\n",
            "prove_correct conflictColumns by\n  loom_solve"),
        "refinement": (
            "emitting one spurious token for an EMPTY field list adds a "
            "conflict target that no field asked for: the generated clause would "
            "carry an empty column reference. A real patch of this shape (a "
            "builder that seeds its token list with one element before the "
            "per-field walk) produces a malformed clause whenever the caller "
            "supplies no fields for that argument position, which the suite "
            "exercises through the argument position that is legitimately empty "
            "while the other is populated — so it would NOT resolve. Attacks the "
            "boundary the four ported rivals all agree with gold on."
        ),
        "rationale": (
            "REJECT from C1 (`out = dbColumns fields`) at the BOUNDARY of the "
            "LENGTH clause (L): `dbColumns [] = []` by the first defining "
            "equation, so the output at the empty list is forced EMPTY, and a "
            "rival emitting a single token there diverges. Refuted at input `[]` "
            "— a FIFTH distinct point, and the only one at which every other "
            "rival in this battery agrees with gold (all four return `[]` there), "
            "so nothing else in the battery could have caught a spec that "
            "constrained C1 on non-empty lists only. Correct on every non-empty "
            "input, so the rejection is attributable to the boundary alone. If it "
            "verified => SPEC-TOO-WEAK (the zero-length case unconstrained)."
        ),
        "witness": _witness("([] : List Field)"),
        # Gold cannot DECIDE this witness (its `while` loop leaves `decide`
        # stuck, not refuted), so the discrimination subject is the loop-free
        # verifying impl of the same frozen spec. See WITNESS MECHANICS.
        "witness_reference": _POS_DIRECT,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                     -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-lookup-local-reshape        -> pos-control-local-column      PORTED
#   pos-cc-local-reshape            -> pos-control-direct            RE-EXPRESSED
#   rej-lookup-returns-name         -> rival-emit-attr               PORTED
#   rej-lookup-returns-arg-name     -> rival-emit-attr-first         RE-EXPRESSED
#   rej-lookup-off-by-one-column    -> rival-reverse-order           RE-EXPRESSED
#   rej-cc-skip-first               -> rival-drop-first              PORTED
#   rej-frame-mutate-field-columns  -> (none)                        VACUOUS
#   rej-frame-mutate-lookup-columns -> (none)                        VACUOUS
#   admiss-lookup-precond-...       -> admiss-gold-total             RE-AIMED
#   AXIOM_TESTS (1)                 -> (none)                         DROPPED (G-AX lane)
#   (no nagini source)              -> pos-control-map-reproved       ADDED BY AUDIT
#   (no nagini source)              -> rival-spurious-token-on-empty  ADDED BY AUDIT
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness.
#
# ADDED BY AUDIT (neither ports a nagini case; both close a gap the ported set
#   left open, each measured with scripts/lean_verify.sh):
#   * pos-control-map-reproved (attack E, SPEC-TOO-STRONG probe). The two ported
#     positives both sit syntactically NEXT TO gold: `pos-control-local-column`
#     keeps gold's loop verbatim and adds a `let`, and `pos-control-direct`
#     returns the post-image term `dbColumns fields` itself. Neither forces the
#     spec to accept an INDEPENDENTLY computed answer, so a C1 over-fit to the
#     term `dbColumns fields` or to gold's fold shape would have passed the
#     shipped battery. `fields.map (·.column)` is extensionally equal but not
#     definitionally so, the frozen proof does NOT close it, and the obligation is
#     re-discharged by induction on `fields` — so this is the first positive whose
#     success is evidence about C1 rather than about proximity to gold. Verifies
#     (exit 0).
#   * rival-spurious-token-on-empty (attack D, SPEC-TOO-WEAK probe). All four
#     ported rivals AGREE with gold at the empty list (checked value-by-value:
#     each returns `[]` there), so the zero-length boundary — where C1 forces the
#     entire output empty rather than merely correct per element — was unattacked,
#     and a spec constraining C1 on non-empty lists only would have passed the
#     shipped battery unchanged. This rival is correct on every non-empty input
#     and wrong only at `[]`. Rejected (exit 1, unsolved goals) with a witness at
#     `([] : List Field)` (rival exit 0, reference exit 1 by refutation).
#   Ten further tuned WRONG impls were built during the same audit and every one
#   was REJECTED, so no spec hole was found: attr-only-on-override fields (the
#   sharpest form of the defect, identity elsewhere), reverse-only-when-long,
#   swap-last-two, append-empty-token, duplicate-last-token, attr-on-last-field,
#   shorter-of-column-or-attr, dedupe-tokens, wrong-at-empty, and a `:|`
#   nondeterministic echo of the post-image (which does not even elaborate).
#   Three further CORRECT reshapes verify (`fields.map`, `List.map Field.column`,
#   `foldr`), so no SPEC-TOO-STRONG hole either. A forward-appending `while` loop
#   was NOT landed — its take-step obligation is a different lemma than the frozen
#   drop-step and the audit did not close the proof; that is an unclosed PROOF, not
#   evidence about the spec, and it is recorded as uncertain rather than as a hole.
#
# CARRIER NARROWING. The nagini sibling models TWO functions — `lookup`
#   (name -> column) and `conflict_columns` (the per-field walk that calls
#   lookup). This bundle models only the purely functional core: a SINGLE method
#   `conflictColumns (fields : List Field)` that takes the ALREADY-RESOLVED field
#   list as a free input (mapping.md §1: name->Field resolution via `get_field`
#   is UNCHANGED and upstream of the modeled boundary, so it is not modeled). So
#   there is no separate `lookup` surface here: the two nagini `lookup`-returns-
#   the-name rivals (rej-lookup-returns-name, rej-lookup-returns-arg-name) both
#   collapse to "emit the ATTRIBUTE, not the COLUMN" — carried as rival-emit-attr
#   (whole domain) and rival-emit-attr-first (partial domain, distinct separating
#   point), so both nagini rivals are represented rather than merged away.
# RE-EXPRESSED (pos-cc-local-reshape -> pos-control-direct): the nagini positive
#   aliased the resolved column to a local around the forward append; on this
#   carrier C1 already IS `out = dbColumns fields`, so the honest cheapest correct
#   impl is `return dbColumns fields` — same argument (the grounded pin is
#   satisfiable only by the real per-field column work; no wrong echo verifies)
#   expressed as a loop-free correct impl.
# RE-EXPRESSED (rej-lookup-off-by-one-column -> rival-reverse-order): the nagini
#   off-by-one returns a NEIGHBOURING slot's column (field_columns[j+1]). On the
#   whole-list carrier the faithful analogue is a position/order violation; on a
#   two-field list `reverse` IS exactly the off-by-one (position 0 gets field 1's
#   column). Attacks the ORDER clause (O) of C1.
# RE-AIMED (admiss-lookup-precond-... -> admiss-gold-total): the nagini case
#   established the sub-call's read-only precondition is establishable from the
#   caller's Requires. This method has NO `require` and models no sub-call, so
#   that probe is degenerate (every input is in-domain); re-aimed at the residual
#   total-domain risk (post-image joint satisfiability), witnessed by the frozen
#   impl discharging the ensures.
# VACUOUS (rej-frame-mutate-field-columns, rej-frame-mutate-lookup-columns): both
#   nagini frame-mutation rivals keep a correct value but WRITE back through a
#   read-only registry input held at fractional permission (1/2, 1/4) and must be
#   rejected for INSUFFICIENT PERMISSION. Velvet is referentially transparent:
#   `fields` is an immutable value, no `mut` binder, no heap, no aliasing, no
#   permission system. There is no read-only input to overwrite. No substitute
#   fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the nagini file's single axiom-soundness/containment
#   probe over the real Django callee is G-AX's job. This bundle declares no
#   consumed axiom and no deep-model reference (mapping.md §3: `Field.column` is a
#   plain projection carried by the structure, R not A, checked by G-CONF); the
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause is C1
#   (`out = dbColumns fields`), pinning THREE independent things, each attacked:
#     * VALUE (V, each token is the field's `column` not `attr`):
#         rival-emit-attr (whole domain), rival-emit-attr-first (partial domain).
#     * ORDER (O, tokens in `fields` order): rival-reverse-order.
#     * LENGTH (L, one token per field): rival-drop-first, and at the zero
#         boundary rival-spurious-token-on-empty.
#   The sole input binder `fields` is varied across FIVE distinct points (pts=5):
#     [FA]            — one override field (column != attr);
#     [FA, FG]        — override head + non-override tail (column == attr);
#     [FA, FB]        — two override fields with distinct columns;
#     [FG, FB]        — non-override head + override tail;
#     []              — the empty list (the zero-length boundary).
#   Each point is MEANINGFUL, not a respelling: for every rival, the declared
#   point was checked to be one where the rival's output actually DIFFERS from
#   `dbColumns` (verified value-by-value for all five rivals across all five
#   points). In particular `[]` is the only point at which all four ported rivals
#   agree with gold, which is why it needed its own rival rather than another
#   witness.
#   Both the `attr` and `column` projections of `Field` are exercised (fields
#   where the two agree AND where they differ), list order is exercised (reverse),
#   and list length is exercised both above zero (drop-first) and at zero
#   (spurious-token-on-empty). No binder value is held fixed by every witness.
#   All three positives and the admissibility case defend C1; only
#   pos-control-map-reproved does so from a shape the frozen proof cannot close.
#
# WITNESS MECHANICS: C1's carrier is transparent (`dbColumns`/`Field` concrete,
#   `axioms` region empty). Every witness extracts the executable program and
#   refutes C1 directly against `dbColumns`: each rival is loop-free so its
#   `…Exec` reduces under `decide`.
#   GOLD IS NOT THE DISCRIMINATION SUBJECT. Gold's backward-`while` `…Exec` leaves
#   `decide` STUCK (`instDecidableNot did not reduce to isTrue or isFalse`,
#   `.hasDecEq`) — a non-verdict, so its exit code discriminates nothing and the
#   gate would record `witness-undecided`. Three witness shapes were measured
#   against gold and none decides: the `…Exec` match under `decide` (stuck), the
#   full `derive_tester_for` tester (stuck), and a hypothesis-conditioned form
#   over `…Exec = DivM.res r` (unsolved goals on BOTH sides, so not a
#   discriminator). So each reject case declares `witness_reference =
#   _POS_DIRECT` — the loop-free `return (dbColumns fields)` impl of the SAME
#   frozen spec, which the gate checks shares the spec and VERIFIES before
#   refuting any witness against it. Measured with scripts/lean_verify.sh, all
#   four cases: rival exit 0; reference exit 1 by REFUTATION (`decide` proved the
#   proposition `… ≠ dbColumns [...]` is false — i.e. the reference agrees with
#   the post-image where the rival does not); gold exit 1 by stuck reduction.
#   No witness binds a hypothesis, so no consistency probe is needed.
#   NOTE the `_POS_DIRECT` reference is the same source object as
#   `pos-control-direct`'s module, so the impl the gate proves verifies is
#   byte-identically the impl the witnesses are refuted against.
AXIOM_TESTS = []
