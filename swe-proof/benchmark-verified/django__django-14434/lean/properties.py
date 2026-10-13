"""properties.py — G-PBT falsification battery for django__django-14434 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct__create_unique_sql``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function; modeled domain ``columns ≠ []``):

  implementation__create_unique_sql
      (dbTable : String) (columns : List String) : Statement

  builds a deferred statement whose column part stores a table identifier and a
  column list. The frozen postcondition pins five inseparable facets:

    (1) ∀ col, references_column dbTable col = columns.contains col
        — a query for the statement's OWN table answers exact column membership;
    (2) ∀ t ≠ dbTable, ∀ col, references_column t col = false;
    (3) references_table dbTable = true;
    (4) ∀ t ≠ dbTable, references_table t = false;
    (5) renderedColumns = columns
        — the column part renders exactly the given column sequence, in order.

  The discriminating facet is which KIND of table identifier the column part
  stores. A bare-name identifier compares equal to a query table-name string, so
  (1) holds; a wrapped reference identifier never string-compares, so (1)
  collapses to a constant ``false`` — that is the reported defect. Facets
  (2)/(3)/(4) route through the SAME table-identifier comparison as (1) plus the
  table part's own name, so on this carrier they are structurally coupled to (1)
  rather than independently attackable (see ADVERSARIAL READ). Facet (5) is a
  DISTINCT observable — the stored column PAYLOAD, order and multiplicity — that
  the membership facets cannot see; a statement can answer every membership query
  correctly yet render the wrong column sequence.

  CORRECTION (audit a5): facet (4) `∀ t ≠ dbTable, references_table t = false`
  is NOT coupled to (1). ``Statement.references_table`` folds
  ``tablePart.name == t || columnsPart.tableId.matchesName t`` over BOTH parts,
  and ``tablePart.name`` (the ``Table(table, …)`` handle the statement stores)
  is a FREE knob that the column-membership facets never touch. A rival that
  keeps the column part gold but stores a wrong table-part name answers every
  references_column query correctly and still reports references_table = true
  for its own table (facet (3), which the correct column part alone satisfies),
  yet falsely reports the wrong name's table, violating facet (4) alone.
  Refuted by ``weak-wrong-tablepart`` — verified (audit a5) rival-exit 0,
  gold-exit 1 (semantic: `¬("t" == "zzz" || "t" == "zzz") = false` is false).
  Facet (2) DOES route through the same column-part table id as (1) (only the
  column part answers references_column), and facet (3) is satisfiable by the
  column part alone, so those two remain coupled to (1); facet (4) is the one
  the table part exposes independently.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack (``db_table[0] = 0`` through a read-only 1/2-permission
    reference) MANDATORY and expects rejection for insufficient permission. Lean
    is referentially transparent: ``dbTable``/``columns`` are immutable values
    with no fractional permission to violate and no aliasing to exploit, so this
    class has NO expressible instance here. No substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: equalities
    against terms built only from the two inputs (string comparison, list
    membership/order), fully unfolded. The bundle declares no ``opaque``/``axiom``
    (axioms region empty, deep_model_references == []), so there is no answer key
    an implementation could echo. The honest analogue is the POSITIVE CONTROLS.

  * WRONG-DISCRIMINATOR (nagini ``rival-opaque-holder``, plain=False) — APPLIES,
    and is THE load-bearing rival: store a WRAPPED reference identifier instead
    of a bare name. Facet (1) then answers ``false`` for every column, exactly the
    pre-patch behavior the issue reports. Refuted by ``weak-wrapped-tableid``.

  * PARTIAL-DOMAIN / OVER-REPORTING (nagini ``partial-domain-drop-first`` /
    ``over-report-extra-column``) — APPLY against facet (1): store a TRUNCATED
    column set (a genuinely-constrained column is no longer reported) or a
    SUPERSET column set (an unconstrained column is falsely reported). Refuted by
    ``weak-drop-first-column`` and ``weak-over-report-column`` respectively.

  * RENDER-PAYLOAD (no nagini counterpart at this granularity) — APPLIES against
    facet (5), which the Lean carrier separates from membership. nagini pinned a
    single value-equal column set; here membership (1) and the rendered order (5)
    are distinct observables, so a rival that PERMUTES the stored columns answers
    every membership query correctly yet renders the wrong sequence. Refuted by
    ``weak-reordered-render`` — a near-miss that is correct on (1)-(4) and wrong
    only on (5), so it carries its own distinguishing witness.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that instantiates the offending universally-
quantified facet at ONE concrete column (or destructures the render facet) and
derives a contradiction. Because the facets quantify over the infinite ``String``
domain, the witness selects the guilty conjunct and refutes it at a literal
column rather than ``decide``-ing the whole negated spec. Each witness was built
and checked to ELABORATE against its rival and to FAIL against the frozen
solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. Both input binders are varied across the reject witnesses:
  * ``dbTable`` — probed at "t", "u" (distinct table names).
  * ``columns`` — probed at ["name"], ["x","y"], ["p"], ["a","b"] (distinct
    lengths and contents; the reorder witness needs length ≥ 2).
``pts`` = 4 distinct input points. Facets (1), (4) and (5) are each attacked by
a dedicated rival; facets (2) and (3) route through the column part's table id
and column list (the only answerers of references_column / the column-side
references_table), so a rival that breaks them breaks (1) first — see
ADVERSARIAL READ (CORRECTION, audit a5) for why facet (4) is the exception,
independently attackable through the table part.

AXIOM lane: EMPTY. The reference objects are modeled deeply as Lean structures
(axioms region empty, no ``opaque``), so there is no axiom-soundness /
axiom-containment obligation for this gate to re-discharge. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-14434"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, so every replacement lands entirely inside the
# region it means to edit. The PROOF anchor is the first two lines of the frozen
# tactic body (intro + unfold), used only by the admissibility case to splice in
# a ground `have` ahead of the frozen script.
_IMPL_GOLD = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }\n"
    "  return { tablePart := { name := table }, columnsPart := columnsPart }\n"
)

_PROOF_HEAD = (
    "  intro dbTable columns _\n"
    "  unfold problem_spec__create_unique_sql implementation__create_unique_sql\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_HEAD) == 1, "proof region drifted; update _PROOF_HEAD"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced (proof kept).

    Used for reject rivals and the differently-shaped positive controls. For the
    positives the frozen proof still closes (the reshape leaves the elaborated
    term definitionally equal); for the rivals the frozen proof no longer applies
    (that is the reject signal — the witness attributes the failure to the spec).
    """
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL impl bodies (structurally different, behaviourally identical).
# ---------------------------------------------------------------------------

# No mutable-accumulator `Id.run do`: build the statement as one functional
# expression. Same recorded facets; the elaborated result is definitionally the
# gold one, so the frozen proof carries.
_POS_FUNCTIONAL = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement :=\n"
    "  { tablePart := { name := dbTable },\n"
    "    columnsPart := { tableId := TableId.name dbTable, columns := columns } }\n"
)

# Keep `Id.run do` but drop the intermediate `let table := dbTable` and inline
# `dbTable` at both use sites. Different statement shape, identical result.
_POS_NO_LOCAL = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns }\n"
    "  return { tablePart := { name := dbTable }, columnsPart := columnsPart }\n"
)


# ---------------------------------------------------------------------------
# REJECT rival impl bodies (only the impl changes; spec + theorem STATEMENT stay
# byte-identical; the frozen proof body is retained and no longer closes).
# ---------------------------------------------------------------------------

# WRONG DISCRIMINATOR (= the pre-patch bug): store a WRAPPED reference identifier
# instead of the bare name. Facet (1) collapses to constant false.
_RIVAL_WRAPPED = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.wrapped table, columns := columns }\n"
    "  return { tablePart := { name := table }, columnsPart := columnsPart }\n"
)

# PARTIAL-DOMAIN (under-report): store only the tail of the column set, dropping
# the first column. Facet (1) fails for the dropped first column; facet (5) too.
_RIVAL_DROP = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns.drop 1 }\n"
    "  return { tablePart := { name := table }, columnsPart := columnsPart }\n"
)

# OVER-REPORTING (superset): append a spurious column code. Facet (1) fails for
# that spurious column (reported yet not in `columns`); facet (5) too.
_RIVAL_EXTRA = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns ++ [\"__spurious__\"] }\n"
    "  return { tablePart := { name := table }, columnsPart := columnsPart }\n"
)

# RENDER-PAYLOAD near-miss: store the columns REVERSED. Membership is invariant
# under reversal, so facets (1)-(4) all still hold; only facet (5) (the rendered
# order) is wrong. Needs a length-≥2 witness to distinguish.
_RIVAL_REVERSE = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns.reverse }\n"
    "  return { tablePart := { name := table }, columnsPart := columnsPart }\n"
)

# WRONG TABLE-PART NAME: keep the column part gold (so facets (1),(2),(3),(5)
# all still hold — references_column is answered by the column part alone, and
# references_table dbTable = true holds because the correct column part's
# tableId already matches dbTable), but store a FIXED WRONG name in the table
# part. Facet (4) `∀ t ≠ dbTable, references_table t = false` then fails at the
# wrong name, since the table part's `name == t` fires for it. This is the one
# facet the table part exposes independently of the column-membership facets.
_RIVAL_TABLEPART = (
    "def implementation__create_unique_sql\n"
    "    (dbTable : String) (columns : List String) : Statement := Id.run do\n"
    "  let table : String := dbTable\n"
    "  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }\n"
    "  return { tablePart := { name := \"zzz\" }, columnsPart := columnsPart }\n"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY variant: splice two ground F2P observables (the exact
# assertIs(references_table)=True and assertIs(references_column(table,'name'))
# =True the F2P test checks) into the proof region ahead of the frozen script,
# then close the frozen obligation verbatim. Confirms the modeled behavior is
# satisfiable at the F2P-shaped input. No new declaration/axiom/sorry; the
# theorem STATEMENT is byte-identical.
# ---------------------------------------------------------------------------
_ADMISS_GROUND = (
    "  have _ground_col : (implementation__create_unique_sql \"schema_author\" [\"name\"]).references_column \"schema_author\" \"name\" = true := by\n"
    "    decide\n"
    "  have _ground_tab : (implementation__create_unique_sql \"schema_author\" [\"name\"]).references_table \"schema_author\" = true := by\n"
    "    decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different CORRECT impls that
    # MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The theorem STATEMENT is
    # byte-identical and the frozen tactic body is retained; no helper lemma,
    # axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_FUNCTIONAL),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` and "
            "builds the statement as one functional record expression. Records the "
            "same facets (bare-name table identifier, verbatim column list), so "
            "references_column / references_table / renderedColumns are unchanged; "
            "the elaborated result is definitionally the gold one and the frozen "
            "proof closes. If it failed => SPEC-TOO-STRONG (spec over-fit to the "
            "`Id.run do` code form)."
        ),
    },
    {
        "id": "pos-no-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_NO_LOCAL),
        "rationale": (
            "another correct shape: keep `Id.run do` but drop the intermediate "
            "`let table := dbTable` and inline `dbTable` at both use sites. Same "
            "recorded facets, same references_column / references_table / "
            "renderedColumns answers; the frozen proof carries. Confirms the spec "
            "admits a faithful correct impl regardless of the intermediate-binding "
            "shape (else SPEC-TOO-STRONG)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (must VERIFY) — the obligation is discharged AND two ground
    # F2P observables are checked at the normal F2P-shaped input, so the modeled
    # behavior is shown satisfiable (non-vacuous) at exactly the input the F2P
    # exercises. The frozen theorem carries only the `columns ≠ []` hypothesis,
    # which the ground input `["name"]` satisfies.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_HEAD, _ADMISS_GROUND + _PROOF_HEAD),
        "rationale": (
            "the obligation is closed verbatim, preceded by two `have`s that "
            "discharge the F2P ground observables by `decide`: for a statement "
            "built over table \"schema_author\" and columns [\"name\"], "
            "references_table \"schema_author\" = true and references_column "
            "\"schema_author\" \"name\" = true (the exact "
            "assertIs(sql.references_table(table), True) and "
            "assertIs(sql.references_column(table, 'name'), True) the F2P asserts). "
            "Verifies (else the modeled behavior is unsatisfiable at the F2P input, "
            "the analogue of PRECOND/SPEC-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground facts are `have`s "
            "inside the existing tactic body, and no new declaration/axiom/sorry "
            "is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violated facet at one concrete input.
    # =====================================================================
    {
        "id": "weak-wrapped-tableid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_WRAPPED),
        "refinement": (
            "this IS the pre-patch behavior: the column part stores a WRAPPED "
            "reference identifier (the object) rather than the bare table-name "
            "string. Its faithful real patch is precisely the unchanged pre-patch "
            "wiring the issue reports ('references_column always false'). A wrapped "
            "identifier never string-compares equal to the query table-name string, "
            "so references_column(table, 'name') is always false and the F2P "
            "assertIs(sql.references_column(table, 'name'), True) FAILS. It does NOT "
            "resolve — a verifying rival here would be a true verify-does-not-imply-"
            "resolve break."
        ),
        "rationale": (
            "the DISCRIMINATING bug. REJECT from facet (1) `∀ col, "
            "references_column dbTable col = columns.contains col`: with a wrapped "
            "identifier the left side is constant false while `columns.contains "
            "\"name\"` is true, so the facet fails at col = \"name\". Refuted at "
            "dbTable = \"t\", columns = [\"name\"]. If it verified => SPEC-TOO-WEAK "
            "(admits the very bug)."
        ),
        "witness": (
            "-- Facet (1) fails at col = \"name\": a wrapped table identifier never\n"
            "-- string-compares, so the query answers false though \"name\" ∈ columns.\n"
            "example : ¬ problem_spec__create_unique_sql \"t\" [\"name\"]\n"
            "    (implementation__create_unique_sql \"t\" [\"name\"]) := by\n"
            "  intro h\n"
            "  have h1 := h.1 \"name\"\n"
            "  simp only [implementation__create_unique_sql, Statement.references_column,\n"
            "    ColumnsRef.references_column, TableId.matchesName, Id.run, pure] at h1\n"
            "  exact absurd h1 (by decide)\n"
        ),
    },
    {
        "id": "weak-drop-first-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_DROP),
        "refinement": (
            "stores only the tail of the column set (drops the first column). A "
            "faithful real patch recording a column set missing the first field "
            "makes references_column(table, <first field>) return false; the F2P "
            "constraint UniqueConstraint(fields=['name']) has 'name' as its only "
            "(and first) field, so references_column(table, 'name') would be false "
            "and the F2P assertIs(..., True) FAILS. It also renders the wrong column "
            "sequence into the created DDL. It does NOT resolve."
        ),
        "rationale": (
            "PARTIAL-DOMAIN (under-report). REJECT from facet (1): at columns = "
            "[\"x\", \"y\"] the dropped first column \"x\" has `columns.contains "
            "\"x\" = true` but is no longer stored, so references_column dbTable "
            "\"x\" = false. Refuted at dbTable = \"t\", columns = [\"x\", \"y\"] "
            "(a distinct table name and column set from the other rivals)."
        ),
        "witness": (
            "-- Facet (1) fails at the dropped first column \"x\": it is in columns\n"
            "-- but no longer stored, so the query answers false.\n"
            "example : ¬ problem_spec__create_unique_sql \"t\" [\"x\", \"y\"]\n"
            "    (implementation__create_unique_sql \"t\" [\"x\", \"y\"]) := by\n"
            "  intro h\n"
            "  have h1 := h.1 \"x\"\n"
            "  simp only [implementation__create_unique_sql, Statement.references_column,\n"
            "    ColumnsRef.references_column, TableId.matchesName, Id.run, pure] at h1\n"
            "  exact absurd h1 (by decide)\n"
        ),
    },
    {
        "id": "weak-over-report-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EXTRA),
        "refinement": (
            "stores a superset column set (appends a spurious column). A faithful "
            "real patch recording extra columns makes references_column report True "
            "for a column the constraint does NOT cover — a wrong-positive that "
            "diverges from the gold (which records exactly the constraint's fields) "
            "and renders an extra column into the created DDL, so the constraint "
            "actually built on the DB differs from the one the F2P/PASS_TO_PASS "
            "schema tests expect. It does NOT resolve."
        ),
        "rationale": (
            "OVER-REPORTING, targets the no-constant-True guard. REJECT from facet "
            "(1): for the spurious column \"__spurious__\" the impl stores it so "
            "references_column dbTable \"__spurious__\" = true, but `columns.contains "
            "\"__spurious__\" = false`. Refuted at dbTable = \"u\", columns = "
            "[\"p\"] (again a distinct point). If it verified => SPEC-TOO-WEAK (the "
            "membership query could over-report)."
        ),
        "witness": (
            "-- Facet (1) fails at the spurious column: it is stored (query true) but\n"
            "-- not in columns (contains false).\n"
            "example : ¬ problem_spec__create_unique_sql \"u\" [\"p\"]\n"
            "    (implementation__create_unique_sql \"u\" [\"p\"]) := by\n"
            "  intro h\n"
            "  have h1 := h.1 \"__spurious__\"\n"
            "  simp only [implementation__create_unique_sql, Statement.references_column,\n"
            "    ColumnsRef.references_column, TableId.matchesName, Id.run, pure] at h1\n"
            "  exact absurd h1 (by decide)\n"
        ),
    },
    {
        "id": "weak-reordered-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_REVERSE),
        "refinement": (
            "stores the columns REVERSED. Membership is invariant under reversal, so "
            "every references_column / references_table query still answers "
            "correctly — this rival would PASS a test that only probes the membership "
            "predicates. But the stored column list also renders, in order, into the "
            "generated DDL text; a reversed list emits the columns in the wrong "
            "order, so the constraint actually created on the DB differs from the one "
            "the hidden test creates-then-drops. A faithful real patch of this shape "
            "generates wrong SQL and does NOT resolve — this is exactly the "
            "membership-right / payload-wrong gap facet (5) closes."
        ),
        "rationale": (
            "RENDER-PAYLOAD near-miss (correct on facets (1)-(4), wrong only on "
            "(5)). REJECT from facet (5) `renderedColumns = columns`: at columns = "
            "[\"a\", \"b\"] the stored (rendered) list is [\"b\", \"a\"] ≠ [\"a\", "
            "\"b\"]. Because it agrees with gold on the membership facets, it carries "
            "its own witness at a distinguishing length-2 input. If it verified => "
            "SPEC-TOO-WEAK (the rendered column payload is under-pinned)."
        ),
        "witness": (
            "-- Facet (5) fails: reversal preserves membership but not order, so the\n"
            "-- rendered column sequence [\"b\",\"a\"] ≠ the given [\"a\",\"b\"].\n"
            "example : ¬ problem_spec__create_unique_sql \"t\" [\"a\", \"b\"]\n"
            "    (implementation__create_unique_sql \"t\" [\"a\", \"b\"]) := by\n"
            "  intro h\n"
            "  have h5 := h.2.2.2.2\n"
            "  simp only [implementation__create_unique_sql, Statement.renderedColumns,\n"
            "    Id.run, pure] at h5\n"
            "  exact absurd h5 (by decide)\n"
        ),
    },
    {
        "id": "weak-wrong-tablepart",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_TABLEPART),
        "refinement": (
            "keeps the column part gold but stores a WRONG name in the table "
            "part. This attacks facet (4) `∀ t ≠ dbTable, references_table t = "
            "false` — the observable that the table part answers and the "
            "column-membership facets do not touch. A faithful real patch that "
            "recorded the wrong name in the statement's table part would make "
            "references_table report true for a table the statement does not "
            "belong to (a wrong-positive on table membership), diverging from "
            "the gold behavior the schema P2P tests rely on; it does NOT "
            "resolve. Without a rival here the battery leaves facet (4) unpinned "
            "even though the table part is a knob independent of the column part "
            "(the original manifest wrongly claimed (4) was coupled to (1))."
        ),
        "rationale": (
            "TABLE-PART near-miss (correct on facets (1),(2),(3),(5); wrong only "
            "on (4)). REJECT from facet (4): the table part reports its stored "
            "name, so `references_table \"zzz\" = true` though \"zzz\" ≠ dbTable, "
            "while the spec requires false. Refuted at dbTable = \"t\", columns = "
            "[\"name\"], queried table \"zzz\". If it verified => SPEC-TOO-WEAK "
            "(the table part's name is under-pinned)."
        ),
        "witness": (
            "-- Facet (4) fails at t = \"zzz\": the table part stores the wrong\n"
            "-- name, so references_table \"zzz\" = true though \"zzz\" ≠ dbTable.\n"
            "example : ¬ problem_spec__create_unique_sql \"t\" [\"name\"]\n"
            "    (implementation__create_unique_sql \"t\" [\"name\"]) := by\n"
            "  intro h\n"
            "  have h4 := h.2.2.2.1 \"zzz\" (by decide)\n"
            "  simp only [implementation__create_unique_sql, Statement.references_table,\n"
            "    TableRef.references_table, ColumnsRef.references_table, TableId.matchesName,\n"
            "    Id.run, pure] at h4\n"
            "  exact absurd h4 (by decide)\n"
        ),
    },
]


# Axioms region is empty and there are no deep-model references: the reference
# objects are modeled directly as Lean structures, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
