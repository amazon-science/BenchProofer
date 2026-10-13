"""properties.py — G-PBT falsification battery for django__django-14434 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct buildUniqueStatement`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  buildUniqueStatement (dbTable : String) (columns : List String)
      return (out : Stmt)
    ensures ∀ t col, out.referencesColumn t col
                       = ((dbTable == t) && columns.contains col)   (C1)
    ensures ∀ t, out.referencesTable t = (dbTable == t)             (C2)
    ensures out.renderedColumns = columns                           (C3)

The operation builds a deferred statement for a named unique constraint over a
column list, restricted to the two reference-bearing parts of the result. Three
independent top-level ``ensures`` clauses pin the behavior the issue + tests
demand:
  C1 — COLUMN REFERENCE: for every queried table/column the built statement
       reports that it references that column iff the query names the
       constraint's own table AND the column is one of the listed columns. This
       is the LOAD-BEARING clause: the reported defect is that this query is
       always false, because the carrier threaded into the column-reference part
       is an opaque object that wraps the table name (compared by identity) in
       place of the bare name (compared by value).
  C2 — TABLE REFERENCE: the statement references exactly the constraint's own
       table.
  C3 — RENDERED PAYLOAD: the column part stores the given column sequence
       verbatim, in order and with multiplicity — the payload the emitted DDL
       text carries.
Two input binders, ``dbTable : String`` and ``columns : List String``, ground
every clause; the ``axioms`` region declares nothing and every predicate
(``referencesColumn`` / ``referencesTable`` / ``renderedColumns`` /
``slotMatches``) is a concrete ``def`` in the ``pure`` region, validated == the
real unchanged reference classes out-of-band by axiom_check.py (G-AX). The method
has NO ``require`` clause (pre-conditions region empty), so the domain is total.

CARRIER — fully TRANSPARENT, so the whole reject lane is expressible by
``decide``. The discriminating carrier is ``TableSlot``: ``TableSlot.name s``
matches a queried table name by value (``s == t``), while ``TableSlot.wrapped _``
never matches a plain name (identity comparison against a value, always false) —
the exact Python behavior (a ``Table`` instance defines no ``__eq__``, so it
value-equals no string). Every clause reduces at a concrete input to a decidable
equality of concrete values.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, and
its postcondition carries unbounded ``∀ t col`` quantifiers, so the derived
``…Tester`` route cannot be made decidable. A witness therefore reaches the impl
through Velvet's extractor: ``extract_program_for buildUniqueStatement`` yields
``buildUniqueStatementExec : String → List String → DivM Stmt``. The frozen impl
is STRAIGHT-LINE (no loop), so its ``…Exec`` reduces under ``decide`` at a
concrete input — and so does every rival's. Each witness states, at one concrete
``(dbTable, columns)`` point, that the rival's extracted statement disagrees with
the grounded post-image RHS on a specific observable (a column query, a table
query, or the rendered payload): ``… ≠ …`` with ``decide``. The witness is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. Every witness binds nothing (concrete literal
inputs), so no consistency-probe obligation arises. (Verified out of band: each
witness elaborates against its rival and FAILS against the frozen solution — the
required discrimination.)

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the statement built inline in the return; the
    carriers bound to differently-named locals) must still verify, else the spec
    is SPEC-TOO-STRONG (over-fit to the frozen statement shape). The frozen
    ``loom_solve`` closes the byte-identical obligation on the reshaped bodies
    with no retune.
  * ADMISSIBILITY — the method carries NO ``require`` clause, so the nagini
    sibling's half-permission precondition-admissibility probe has no
    counterpart. The residual risk on this transparent carrier is a DEGENERATE
    post-image (a spec no impl can meet reads like a spec every impl meets), so
    the case is re-aimed: an in-region ``assert`` pins that the load-bearing
    clause genuinely DISCRIMINATES the two carriers — a name-slot column
    reference reports true where a wrapped-slot column reference reports false at
    an F2P-shaped point. The impl is kept verbatim so the method's own obligation
    still discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries a MANDATORY frame-mutation rival because its ``db_table`` input is
    held at a fractional heap permission (``Acc(list_pred(db_table), 1/2)``) an
    impl can illegally overwrite (``db_table[0] = 0``). Lean and Velvet are
    referentially transparent: ``dbTable`` and ``columns`` are immutable values
    (declared read-only, not ``mut``), there is no heap and no aliasing. There is
    no read-only input to mutate and no permission system to trip, so the class
    is vacuous. Not fabricated — reported as an omission in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A: every clause is a total function/relation of
    the two inputs (directive 8), and the ``axioms`` region is empty. There is no
    opaque answer key to echo; the cheapest correct impl builds the statement
    directly, which the positive controls cover honestly.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of the port. Wrong impls that
    diverge on some sub-domain and MUST be rejected: the opaque-wrapper bug (C1),
    a truncated column set (C1 + C3), an over-reported column set (C1 + C3), a
    reordered payload (C3 only — the velvet-specific rendered-columns observable),
    and a corrupted table name (C2).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
reference-class semantics the predicates model are A-references validated by
axiom_check.py (G-AX's job), not consumed contracts. The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14434"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The FULL executable body of the method (the three carrier bindings + return).
# Reject rivals and the return-shape positive replace this wholesale.
_IMPL = (
    "    let tableForColumns : TableSlot := TableSlot.name dbTable\n"
    "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }\n"
    "    let out : Stmt := { tableName := dbTable, cols := cols }\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "buildUniqueStatement impl region drifted from expected text"

# The FIRST executable line of the impl region. An in-region assert prepended
# here is discharged by the retuned proof without disturbing the obligation.
_IMPL_TOP = "    let tableForColumns : TableSlot := TableSlot.name dbTable"

# The FULL frozen proof body. The admissibility case prepends a live assert and
# retunes the tactic; both the impl region and the prove_correct body are elided
# from the spec view, so same_spec still holds and the obligation statement is
# byte-identical.
_PROOF = "prove_correct buildUniqueStatement by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- witness preamble. Reach the impl through Velvet's extractor:
# ---- `extract_program_for buildUniqueStatement` gives
# ---- `buildUniqueStatementExec : String → List String → DivM Stmt`. The frozen
# ---- impl is straight-line, so its `…Exec` reduces under `decide`; a witness
# ---- states, at a concrete input, that the rival's extracted statement
# ---- disagrees with the grounded post-image RHS on one observable.
_EXTRACT = "extract_program_for buildUniqueStatement\n\n"


def _wit_col(db, cols, qt, qc):
    """Witness on the C1 column-reference observable: the built statement's
    `referencesColumn qt qc` must equal `(dbTable == qt) && columns.contains qc`.
    """
    return (
        _EXTRACT +
        "example :\n"
        f"    (match buildUniqueStatementExec {db} {cols} with\n"
        f"     | DivM.res s => s.referencesColumn {qt} {qc}\n"
        "     | _ => false) ≠\n"
        f"    (({db} == {qt}) && ({cols}).contains {qc}) := by\n"
        "  decide\n")


def _wit_table(db, cols, qt):
    """Witness on the C2 table-reference observable: the built statement's
    `referencesTable qt` must equal `dbTable == qt`."""
    return (
        _EXTRACT +
        "example :\n"
        f"    (match buildUniqueStatementExec {db} {cols} with\n"
        f"     | DivM.res s => s.referencesTable {qt}\n"
        f"     | _ => false) ≠ ({db} == {qt}) := by\n"
        "  decide\n")


def _wit_render(db, cols):
    """Witness on the C3 rendered-payload observable: the built statement's
    `renderedColumns` must equal the given column sequence verbatim."""
    return (
        _EXTRACT +
        "example :\n"
        f"    (match buildUniqueStatementExec {db} {cols} with\n"
        f"     | DivM.res s => s.renderedColumns\n"
        f"     | _ => []) ≠ {cols} := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the frozen `loom_solve` closes it with no retune.
    # =====================================================================
    {
        "id": "pos-inline",
        "kind": "soundness",
        "expect": "verify",
        # Build the statement inline in the return, with the columns carrier
        # constructed as a name-slot in place — no named locals. Behaviourally
        # identical (still the bare, value-comparable name against the columns).
        "module": _swap(
            _BASE, _IMPL,
            "    return { tableName := dbTable,\n"
            "             cols := { tableSlot := TableSlot.name dbTable,\n"
            "                       columns := columns } }"),
        "rationale": "a loop-free, named-local-free impl that builds the statement "
                     "inline with the bare table name as the columns carrier still "
                     "satisfies C1/C2/C3 identically; a correct reshape verifying is "
                     "exactly what SPEC-TOO-STRONG would deny. Exercises the "
                     "obligation from a maximally different (inline) statement shape. "
                     "(Sibling: pos-inline.)",
    },
    {
        "id": "pos-let-bind",
        "kind": "soundness",
        "expect": "verify",
        # Bind the bare name to its own local first, then thread it into both the
        # columns carrier and the table part. Same value flow, distinct surface.
        "module": _swap(
            _BASE, _IMPL,
            "    let nm : String := dbTable\n"
            "    let slot : TableSlot := TableSlot.name nm\n"
            "    let cols : ColumnsRef := { tableSlot := slot, columns := columns }\n"
            "    return { tableName := nm, cols := cols }"),
        "rationale": "binding the bare table name to a local before threading it "
                     "into the columns carrier and the table part computes the "
                     "identical statement, so C1/C2/C3 still discharge and the "
                     "frozen proof closes; a second correct reshape must verify "
                     "(else SPEC-TOO-STRONG). (Sibling: pos-local-flag.)",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini sibling's precondition-admissibility probe is vacuous. Re-aimed at
    # the residual risk on a total domain: that the load-bearing clause is
    # DEGENERATE. The in-region assert pins that the column-reference predicate
    # genuinely DISCRIMINATES the two carriers at an F2P-shaped point — a
    # name-slot reports its column TRUE while a wrapped-slot reports it FALSE. The
    # frozen impl and obligation are kept verbatim; the proof gains one `decide`
    # arm to close the live assert, so the assert is live (a false claim would
    # leave an unsolved goal) and C1/C2/C3 still discharge.
    # =====================================================================
    {
        "id": "admiss-discriminating",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `adm\n"
                "      ((ColumnsRef.referencesColumn\n"
                "          { tableSlot := TableSlot.name \"t\", columns := [\"c\"] } "
                "\"t\" \"c\" = true)\n"
                "       ∧ (ColumnsRef.referencesColumn\n"
                "          { tableSlot := TableSlot.wrapped \"t\", columns := [\"c\"] } "
                "\"t\" \"c\" = false)))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct buildUniqueStatement by\n"
            "  loom_solve <;> first | decide | loom_solve"),
        "rationale": "the load-bearing clause is satisfiable AND non-degenerate at "
                     "the F2P-shaped point: a column-reference carrying the bare "
                     "table NAME reports its column TRUE, while the same reference "
                     "carrying an opaque WRAPPER of that name reports it FALSE. The "
                     "in-region assert must discharge (else the modeled behavior is "
                     "degenerate and C1 says nothing); the impl is kept verbatim so "
                     "C1/C2/C3 still verify. If it fails => the discriminating clause "
                     "is unsatisfiable/degenerate (PRECOND/degeneracy). (Sibling: "
                     "admiss-f2p-witness, re-aimed from precondition admissibility to "
                     "post-image non-degeneracy — this backend declares no require "
                     "clause.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a machine-checked refutation witness
    # at a DISTINCT concrete input and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-opaque-wrapper",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported bug. Thread the OPAQUE WRAPPER of the table name (compared
        # by identity, never value-equal to a plain name) into the columns
        # carrier instead of the bare name. `referencesColumn` then reports FALSE
        # for every column of the constraint's own table.
        "module": _swap(
            _BASE, _IMPL,
            "    let tableForColumns : TableSlot := TableSlot.wrapped dbTable\n"
            "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }\n"
            "    let out : Stmt := { tableName := dbTable, cols := cols }\n"
            "    return out"),
        "refinement": "this IS the pre-patch behaviour: the columns carrier is the "
                      "opaque table-reference object wrapping the name (compared by "
                      "identity) rather than the bare name. The failing test asserts "
                      "that the built statement references its own column and gets "
                      "FALSE for every column — the exact symptom the issue reports. "
                      "Its faithful real counterpart is the unchanged pre-patch "
                      "wiring; it would NOT resolve.",
        "rationale": "REJECT from C1 (`out.referencesColumn t col = (dbTable == t) "
                     "&& columns.contains col`): with the wrapper carrier, "
                     "`slotMatches` is identically false, so the LHS is false where "
                     "the RHS is true for a listed column of the own table. Refuted "
                     "at dbTable=\"t\", columns=[\"c\"], querying (\"t\",\"c\") — the "
                     "load-bearing sub-domain. If it verified => SPEC-TOO-WEAK "
                     "(admits the very bug). (Sibling: rival-opaque-holder.)",
        "witness": _wit_col('"t"', '["c"]', '"t"', '"c"'),
    },
    {
        "id": "weak-drop-first-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Record only the TAIL of the column set (drop the first column) while
        # keeping the bare name. A constraint over the dropped first column is no
        # longer reported, and the rendered payload loses that column.
        "module": _swap(
            _BASE, _IMPL,
            "    let tableForColumns : TableSlot := TableSlot.name dbTable\n"
            "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns.drop 1 }\n"
            "    let out : Stmt := { tableName := dbTable, cols := cols }\n"
            "    return out"),
        "refinement": "a real patch recording a column set missing the first field "
                      "would make the built statement report FALSE for a query on "
                      "that first field, and would emit DDL over the wrong column "
                      "set. The failing test's single/first constraint field would "
                      "then not be referenced; it would NOT resolve.",
        "rationale": "REJECT from C1 (and C3): for the dropped first column, the RHS "
                     "`columns.contains col` is true but the rival's carrier no "
                     "longer contains it, so `referencesColumn` is false. Refuted at "
                     "dbTable=\"u\", columns=[\"a\",\"b\"], querying (\"u\",\"a\") — "
                     "the dropped first column, a two-element list that also varies "
                     "the column-list length. If it verified => SPEC-TOO-WEAK (the "
                     "column set under-pinned). (Sibling: partial-domain-drop-first.)",
        "witness": _wit_col('"u"', '["a", "b"]', '"u"', '"a"'),
    },
    {
        "id": "weak-over-report-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Record a SUPERSET column set (append a spurious code) with the bare
        # name. An unconstrained column is then falsely reported for the own
        # table, and the rendered payload gains a phantom column.
        "module": _swap(
            _BASE, _IMPL,
            "    let tableForColumns : TableSlot := TableSlot.name dbTable\n"
            "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns ++ [\"z\"] }\n"
            "    let out : Stmt := { tableName := dbTable, cols := cols }\n"
            "    return out"),
        "refinement": "a real patch recording extra columns would make the built "
                      "statement report TRUE for a column the constraint does NOT "
                      "cover — a wrong-positive diverging from gold and emitting DDL "
                      "over a phantom column, mis-answering the introspection the "
                      "tests rely on; it would NOT resolve.",
        "rationale": "REJECT from C1 (and C3): for the spurious extra column, the "
                     "RHS `columns.contains col` is false but the rival's carrier "
                     "contains it, so `referencesColumn` is true. Refuted at "
                     "dbTable=\"v\", columns=[\"m\"], querying (\"v\",\"z\") — the "
                     "spurious code (`columns.contains \"z\"` is false). Attacks the "
                     "over-report direction, complementary to the drop rival. If it "
                     "verified => SPEC-TOO-WEAK (the query could over-report). "
                     "(Sibling: over-report-extra-column.)",
        "witness": _wit_col('"v"', '["m"]', '"v"', '"z"'),
    },
    {
        "id": "weak-reorder-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # Right MEMBERSHIP, wrong ORDER: store the column list REVERSED. C1 and
        # C2 are untouched (`contains` is order-insensitive and the table part is
        # unchanged), but the RENDERED payload (C3) diverges — the emitted DDL
        # would list the columns in the wrong order. This is the velvet-specific
        # observable the carrier adds (mapping.md §Rendered-columns observable).
        "module": _swap(
            _BASE, _IMPL,
            "    let tableForColumns : TableSlot := TableSlot.name dbTable\n"
            "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns.reverse }\n"
            "    let out : Stmt := { tableName := dbTable, cols := cols }\n"
            "    return out"),
        "refinement": "a real patch storing a reordered column list answers every "
                      "membership query identically but renders the columns into the "
                      "generated DDL in the WRONG order, so the constraint is "
                      "actually created over a different column sequence. The hidden "
                      "tests grade the emitted SQL (the constraint is created on the "
                      "DB, then inspected), so a reordered payload stays RED; it "
                      "would NOT resolve.",
        "rationale": "REJECT from C3 (`out.renderedColumns = columns`): the reversed "
                     "list differs from `columns` whenever the order is not "
                     "palindromic, even though C1/C2 hold. Refuted at dbTable=\"w\", "
                     "columns=[\"p\",\"q\"], whose reverse [\"q\",\"p\"] ≠ "
                     "[\"p\",\"q\"]. Attacks the rendered-columns clause no "
                     "membership-only rival reaches. If it verified => SPEC-TOO-WEAK "
                     "(the payload's order is unpinned). (ADDED: this observable is "
                     "specific to the velvet carrier — see mapping.md.)",
        "witness": _wit_render('"w"', '["p", "q"]'),
    },
    {
        "id": "weak-corrupt-table-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the TABLE part's stored name (append a character). C1 and C3 are
        # untouched (the columns carrier keeps the correct bare name and list),
        # but the statement now references the WRONG table name — attacks C2.
        "module": _swap(
            _BASE, _IMPL,
            "    let tableForColumns : TableSlot := TableSlot.name dbTable\n"
            "    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }\n"
            "    let out : Stmt := { tableName := dbTable ++ \"x\", cols := cols }\n"
            "    return out"),
        "refinement": "a real patch storing a corrupted table name in the table part "
                      "would make the statement claim to reference a table that does "
                      "not exist (and fail to reference its own), emitting DDL "
                      "against the wrong table name. The schema tests that create and "
                      "inspect the constraint on the real table would stay RED; it "
                      "would NOT resolve.",
        "rationale": "REJECT from C2 (`out.referencesTable t = (dbTable == t)`): the "
                     "corrupted name means `referencesTable dbTable` is false and "
                     "`referencesTable (dbTable ++ \"x\")` is true, both inverting "
                     "the RHS. Refuted at dbTable=\"s\", columns=[\"c\"], querying "
                     "table \"sx\" (`referencesTable \"sx\"` is true where `\"s\" == "
                     "\"sx\"` is false). Attacks the table-reference clause no "
                     "column/payload rival reaches. If it verified => SPEC-TOO-WEAK "
                     "(the table identity unpinned). (ADDED to attack C2.)",
        "witness": _wit_table('"s"', '["c"]', '"sx"'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness rivals — one of which is a
# MANDATORY frame-mutation rival) plus 2 AXIOM_TESTS. The sibling contracts one
# function, `build_constraint_columns`, over a half-permission read-only list
# input; this bundle contracts one method, `buildUniqueStatement`, over a table
# name (String) and a column list (List String) with deep transparent reference
# predicates and no axioms. The two surfaces model the SAME behaviour (a deferred
# reference that must compare its table by VALUE, not identity, and carry exactly
# the constraint's column set), so the value-rival port is near-1:1, with two
# carrier consequences: the frame-mutation rival is vacuous here, and this
# carrier exposes an extra observable (the rendered column payload) that admits a
# reorder rival with no nagini counterpart.
#
#   sibling case                  kind          -> here                       disposition
#   ----------------------------------------------------------------------------------------
#   pos-inline                    soundness     -> pos-inline                 PORTED
#   pos-local-flag                soundness     -> pos-let-bind               PORTED
#   admiss-f2p-witness            admissibility -> admiss-discriminating      RE-AIMED
#   rival-opaque-holder           uniqueness    -> weak-opaque-wrapper        PORTED (the bug)
#   partial-domain-drop-first     uniqueness    -> weak-drop-first-column     PORTED
#   over-report-extra-column      uniqueness    -> weak-over-report-column    PORTED
#   frame-mutate-db-table         uniqueness    -> (none)                     VACUOUS
#   (—)                           uniqueness    -> weak-reorder-payload       ADDED (C3)
#   (—)                           uniqueness    -> weak-corrupt-table-name    ADDED (C2)
#   AXIOM_TESTS (2)               axiom         -> (none)                     N/A (G-AX)
#
# PORTED (the two positives): pos-inline collapses the named locals into an
#   inline statement construction (still the bare name carrier); pos-let-bind
#   binds the bare name to its own local first. Both keep C1/C2/C3 and the frozen
#   `loom_solve` closes untouched.
# RE-AIMED (admiss-f2p-witness -> admiss-discriminating): the sibling asserts an
#   F2P-shaped input is admissible under its half-permission Requires. This
#   backend declares NO require clause, so there is no precondition to admit; the
#   sharper residual risk on this transparent carrier is a DEGENERATE post-image,
#   so the case is re-aimed to a live in-region assert pinning that the
#   load-bearing clause genuinely discriminates the two carriers (name-slot column
#   reference TRUE, wrapped-slot FALSE) at the F2P point.
# PORTED (the three value rivals): rival-opaque-holder ports directly to
#   weak-opaque-wrapper (the reported bug: the opaque wrapper carrier, refuted on
#   the load-bearing column query). partial-domain-drop-first ports to
#   weak-drop-first-column (refuted on the dropped-column sub-domain).
#   over-report-extra-column ports to weak-over-report-column (refuted on the
#   spurious column).
# VACUOUS (frame-mutate-db-table): the sibling's MANDATORY frame-mutation rival
#   writes through the half-permission read-only `db_table` (`db_table[0] = 0`)
#   and is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `dbTable`/`columns` are immutable values (not `mut`), there is no
#   heap and no aliasing, so there is no read-only input to overwrite and no
#   permission system to trip. Its ARGUMENT (mutating the model's table name would
#   corrupt every other schema operation) has no value footprint the spec can
#   force here. Omitted as a genuine carrier fact, NOT fabricated (porting map:
#   this class is vacuous here).
# ADDED (weak-reorder-payload): this carrier makes the rendered column payload an
#   explicit clause (C3, `renderedColumns = columns`), pinning order and
#   multiplicity — the observable mapping.md flags (the emitted DDL lists the
#   columns in order). A membership-preserving reorder passes C1/C2 but violates
#   C3; refutable only via the rendered payload, so it attacks a clause no nagini
#   rival reaches.
# ADDED (weak-corrupt-table-name): the sibling's postcondition includes
#   `constrains_table` but ships no rival dedicated to it. Here C2
#   (`referencesTable t = (dbTable == t)`) is an independent top-level clause, so
#   a rival that corrupts the stored table name attacks C2 with C1/C3 intact —
#   closing the clause-coverage gap.
#
# BINDER / CLAUSE COVERAGE. Two input binders — `dbTable : String`,
#   `columns : List String` — and three independent top-level clauses: C1
#   (column reference), C2 (table reference), C3 (rendered payload). The five
#   reject witnesses probe FIVE DISTINCT input points (pts=5):
#     * weak-opaque-wrapper     dbTable="t", columns=["c"]        (C1)
#     * weak-drop-first-column  dbTable="u", columns=["a","b"]    (C1 + C3)
#     * weak-over-report-column dbTable="v", columns=["m"]        (C1 + C3)
#     * weak-reorder-payload    dbTable="w", columns=["p","q"]    (C3)
#     * weak-corrupt-table-name dbTable="s", columns=["c"]        (C2)
#   `dbTable` ranges over {"t","u","v","w","s"} and `columns` over
#   {["c"],["a","b"],["m"],["p","q"]} (length 1 and 2, single- and multi-column),
#   so NEITHER binder is pinned. C1 is attacked by three rivals (wrapper carrier,
#   drop, over-report), C2 by the table-name rival, C3 by the reorder rival (and
#   incidentally by drop/over-report). Both directions of the column-membership
#   error are attacked (a column wrongly dropped AND a column wrongly added), the
#   carrier-identity bug is attacked, the table identity is attacked, and the
#   payload order is attacked — so no rival mishandling a single fixed-value
#   binder or a single clause could slip through.
#
# AXIOM_TESTS: dropped. The bundle declares no axiom (the unchanged reference-class
# semantics the predicates model are A-references validated by axiom_check.py, not
# consumed contracts), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
