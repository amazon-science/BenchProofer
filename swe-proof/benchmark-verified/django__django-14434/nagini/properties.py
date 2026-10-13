# properties.py — PBT manifest for django__django-14434. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, writes each `module` to a temp file and runs
# Nagini verify + same_spec (spec lane), and each `probe` in the instance Docker
# image (axiom lane).
#
# Defended surface (read from model.py):
#   build_constraint_columns(db_table: List[int], columns: PSeq[int]) -> ConstraintPart
#   Requires(Acc(list_pred(db_table), 1/2))                      # db_table READ-ONLY
#   Ensures: Result().table is db_table          (identity pin)
#            Acc(list_pred(Result().table), 1/2) (half-perm flows through)
#            Result().columns == columns         (value pin)
#            Forall c: member(c,columns) => constrains_column(plain, table, cols, db_table, c)  [LOAD-BEARING]
#            Forall c: not member(c,columns) => not constrains_column(...)                       [no constant-True]
#            constrains_table(table, db_table)
#   constrains_column(plain,table,cols,q_table,q_col) = plain and table==q_table and member(q_col,cols)
#
# The only facet the impl is free to choose is `plain` (table is identity-pinned,
# columns is value-pinned). The discriminating fix is recording the bare table
# name (plain=True / value-comparable) rather than an opaque Table handle
# (plain=False / never value-equal) against the columns — exactly the gold patch
# (table = model._meta.db_table instead of Table(model._meta.db_table, ...)).
from pathlib import Path

INSTANCE = "django__django-14434"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl region (the ONLY text any variant edits — keeps same_spec).
_GOLD_IMPL = (
    "    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart\n"
    "    return part\n"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness, expect verify) — structurally different, correct.
# Inline the construction directly in the return (no named local). This keeps
# the entire gold proof valid: no loop, no induction, no dropped framing assert;
# only the executable shape (named-local vs inline) changes. plain stays True.
# If this fails to verify => SPEC-TOO-STRONG (over-fit to the named-local form).
_POS_INLINE = _swap(
    _BASE, _GOLD_IMPL,
    "    # Structurally different (inline construction, no named local) but\n"
    "    # behaviourally identical: still records the bare, value-comparable\n"
    "    # table name (plain=True) and the constraint's column set.\n"
    "    return ConstraintPart(True, db_table, columns)\n",
)

# POSITIVE CONTROL 2 (soundness, expect verify) — bind plain into a typed local
# first, then construct. Different statement shape, same semantics, gold proof
# intact. plain=True.
_POS_LOCAL = _swap(
    _BASE, _GOLD_IMPL,
    "    # Different shape: compute the (constant) plain flag into a typed local\n"
    "    # first, then build. Same recorded facets, gold proof unchanged.\n"
    "    is_plain = True  # type: bool\n"
    "    part = ConstraintPart(is_plain, db_table, columns)  # type: ConstraintPart\n"
    "    return part\n",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect verify) — exercise the postcondition predicates on the
# just-built part IN the impl region (so same_spec holds; adding a separate
# caller function would change the spec view). After building the gold part we
# Assert (redundantly, discharged by the gold proof) that for ANY column code
# that IS a member of `columns`, the part reports it constrained for THIS table
# by value — the exact shape of the F2P assertIs(sql.references_column(table,
# 'name'), True) — and the companion table query holds. If the spec could not
# admit a normal input these in-region facts would fail to discharge =>
# PRECOND/SPEC-TOO-STRONG. The trigger [[member(c, columns)]] matches the gold
# first-Forall trigger so the proof carries.
_ADMISS = _swap(
    _BASE, _GOLD_IMPL,
    "    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart\n"
    "    # ADMISSIBILITY WITNESS (in-region; redundant with the gold proof):\n"
    "    # an arbitrary constrained column is reported for THIS table by value\n"
    "    # (the F2P references_column(...) is True), and the table query holds.\n"
    "    Assert(Forall(int, lambda c: (\n"
    "        Implies(member(c, columns),\n"
    "                constrains_column(part.plain, ToSeq(part.table),\n"
    "                                  part.columns, ToSeq(db_table), c)),\n"
    "        [[member(c, columns)]])))\n"
    "    Assert(constrains_table(ToSeq(part.table), ToSeq(db_table)))\n"
    "    return part\n",
)


# ---------------------------------------------------------------------------
# REJECT RIVALS
# ---------------------------------------------------------------------------

# FRAME-MUTATION (MANDATORY — db_table is read-only Acc(list_pred(db_table),1/2)).
# This rival WRITES to db_table (db_table[0] = 0) before recording it. The store
# needs FULL permission on list_pred(db_table) but only 1/2 is held, so it MUST
# fail for INSUFFICIENT PERMISSION. The gold postcondition + construction are
# kept verbatim so the rejection is attributable solely to the write. A
# byte-fuzzer never thinks to mutate the input — this is the #1 weakness class.
_RIVAL_FRAME = _swap(
    _BASE, _GOLD_IMPL,
    "    # FRAME-MUTATION ATTACK: write through the read-only (1/2) db_table\n"
    "    # before recording it. Must be REJECTED for insufficient permission.\n"
    "    db_table[0] = 0\n"
    "    part = ConstraintPart(True, db_table, columns)  # type: ConstraintPart\n"
    "    return part\n",
)

# DISCRIMINATOR (the bug): record an OPAQUE HOLDER (plain=False) instead of the
# bare value-comparable name. Then constrains_column is identically False, so a
# constrained column is NOT reported -> the first Forall fails. This is exactly
# model_prepatch.py / the pre-patch Table-handle wiring (G-DIFF). MUST reject.
_RIVAL_PLAIN_FALSE = _swap(
    _BASE, _GOLD_IMPL,
    "    # WRONG DISCRIMINATOR: record an opaque holder (plain=False), i.e. the\n"
    "    # pre-patch Table-handle wiring. constrains_column then == False for all\n"
    "    # columns -> the first Forall fails. Must be REJECTED.\n"
    "    part = ConstraintPart(False, db_table, columns)  # type: ConstraintPart\n"
    "    return part\n",
)

# WRONG-COLUMNS / partial-domain: record a TRUNCATED column set (drop the first
# column) while recording the bare name (plain=True). For a column c that is the
# dropped first element of `columns`, member(c, recorded) is False even though
# member(c, columns) is True -> the first Forall fails on that sub-domain; and
# Result().columns == columns also fails. MUST reject. (Partial-domain: correct
# on the tail columns, wrong on the first.)
_RIVAL_DROP_FIRST = _swap(
    _BASE, _GOLD_IMPL,
    "    # PARTIAL-DOMAIN ATTACK: record only the tail of the column set\n"
    "    # (drop the first column). A constraint over the dropped first column\n"
    "    # is no longer reported -> first Forall fails on that sub-domain.\n"
    "    part = ConstraintPart(True, db_table, columns.drop(1))  # type: ConstraintPart\n"
    "    return part\n",
)

# CONSTANT-TRUE / second-Forall attack: record an EXTRA spurious column code so
# that an UNconstrained column (one not in `columns`) is falsely reported. Here
# we record columns + an extra element; for a c equal to that extra code,
# member(c, recorded) is True but member(c, columns) is False -> the SECOND
# Forall (not member => not constrains_column) fails, and Result().columns ==
# columns fails. MUST reject. (Targets the no-constant-True guard.)
_RIVAL_EXTRA_COL = _swap(
    _BASE, _GOLD_IMPL,
    "    # OVER-REPORTING ATTACK: record a superset column set (append a\n"
    "    # spurious code). An unconstrained column is then falsely reported ->\n"
    "    # the second Forall (not member => not constrains_column) fails.\n"
    "    wide = columns + PSeq(424242)  # type: PSeq[int]\n"
    "    part = ConstraintPart(True, db_table, wide)  # type: ConstraintPart\n"
    "    return part\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-inline", "kind": "soundness", "expect": "verify",
     "module": _POS_INLINE,
     "rationale": "structurally-different CORRECT impl (inline construction, no named "
                  "local) over the same gold facts (plain=True, identity table, exact "
                  "columns). No loop/induction/framing-assert is involved, so the gold "
                  "proof is preserved. If it fails => SPEC-TOO-STRONG (spec over-fit to "
                  "the named-local code form)."},
    {"id": "pos-local-flag", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "another correct shape: the (constant True) plain flag is bound into a "
                  "typed local first, then ConstraintPart is built. Same recorded facets; "
                  "gold proof unchanged. Confirms the spec admits a faithful correct impl "
                  "regardless of statement shape (else SPEC-TOO-STRONG)."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-f2p-witness", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "in-region admissibility witness (so same_spec holds; a separate caller "
                  "function would change the spec view). After building the gold part it "
                  "Asserts the postcondition shape on an arbitrary constrained column: the "
                  "part reports that column for THIS table by value (the exact "
                  "assertIs(sql.references_column(table,'name'), True) the F2P test makes) "
                  "and the companion table query holds. These redundant in-region facts "
                  "must discharge under the gold spec on a normal input; if they cannot, "
                  "the precondition/spec does not admit a legitimate input => "
                  "PRECOND/SPEC-TOO-STRONG. The trigger matches the gold first-Forall so "
                  "the proof carries (no extra lemma needed)."},

    # ---- uniqueness / completeness rivals (must be REJECTED) ----
    {"id": "frame-mutate-db-table", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this. The gold patch reads "
                   "model._meta.db_table (the bare name) and records it; it NEVER writes "
                   "to db_table. Mutating model._meta.db_table in place would corrupt the "
                   "model's table name globally and break every other schema operation / "
                   "constraint on that model (the PASS_TO_PASS schema tests that create "
                   "models, add fields, and build other constraints all read the same "
                   "db_table) — it could not resolve. A verifying rival here would be a "
                   "pure verify-not-resolve artifact (vacuous satisfaction via self-write).",
     "rationale": "MANDATORY frame-mutation probe. `db_table[0] = 0` stores through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a store "
                  "to list_pred needs FULL permission). Rejection source: the PERMISSION "
                  "SYSTEM, not a value mismatch — the gold postcondition and construction "
                  "are kept verbatim. If it verified => SPEC-TOO-WEAK (frame protection "
                  "hollow)."},
    {"id": "rival-opaque-holder", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PLAIN_FALSE,
     "refinement": "this IS the pre-patch behaviour (model_prepatch.py): recording an "
                   "opaque Table handle (plain=False) against the columns. Its faithful "
                   "real patch is the UNCHANGED pre-patch code "
                   "`table = Table(model._meta.db_table, self.quote_name)` passed to "
                   "_index_columns — precisely the bug the issue reports "
                   "('_create_unique_sql makes references_column always false'). The F2P "
                   "test asserts `sql.references_column(table, 'name') is True`, which is "
                   "always False with a Table handle recorded (Table defines no __eq__) — "
                   "it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes. Rejection source: the first "
                  "Forall `member(c,columns) => constrains_column(plain,...)` — with "
                  "plain=False, constrains_column is identically False, so a constrained "
                  "column is not reported. Mirrors G-DIFF (model_prepatch fails here). If "
                  "it verified => SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "partial-domain-drop-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FIRST,
     "refinement": "records only the tail of the column set (drops the first constrained "
                   "column). A faithful real patch of this shape (recording a column set "
                   "missing the first field) would make references_column(table, <first "
                   "field>) return False — the F2P UniqueConstraint(fields=['name']) has "
                   "'name' as its only/first field, so references_column(table,'name') "
                   "would be False and the F2P assertIs(..., True) would FAIL. It would "
                   "NOT resolve.",
     "rationale": "PARTIAL-DOMAIN rival: correct on tail columns, wrong on the first. "
                  "Rejection source: the first Forall fails for c = the dropped first "
                  "column code (member(c,columns) True but constrains_column False because "
                  "member(c, recorded) is False); also Result().columns == columns fails. "
                  "If it verified => SPEC-TOO-WEAK (the column set is under-pinned)."},
    {"id": "over-report-extra-column", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_COL,
     "refinement": "records a superset column set (an extra spurious code). A faithful "
                   "real patch recording extra columns would make references_column report "
                   "True for a column the constraint does NOT cover — a wrong-positive that "
                   "diverges from the gold (which records exactly the constraint's fields) "
                   "and would mis-answer queries the schema/introspection P2P tests rely "
                   "on; it would not be the gold behaviour and would not faithfully "
                   "resolve.",
     "rationale": "CONSTANT-TRUE / over-reporting rival, targets the no-constant-True "
                  "guard. Rejection source: the SECOND Forall `not member(c,columns) => "
                  "not constrains_column(...)` fails for c = the spurious extra code "
                  "(member(c, recorded) True but member(c,columns) False); also "
                  "Result().columns == columns fails. If it verified => SPEC-TOO-WEAK "
                  "(the query could be a constant True / over-report)."},
]


# ---------------------------------------------------------------------------
# AXIOM LANE — no @ContractOnly axioms are consumed (meta.axioms == []). The
# callees are modeled DEEPLY (A-reference): `member` == Python `in`, and
# `constrains_column` / `constrains_table` == the real unchanged
# django.db.backends.ddl_references {TableColumns.references_column,
# Table.references_table}. We persist the G-AX soundness check as a probe so the
# deep-model fidelity is re-runnable as a regression: it reproduces the real
# ddl_references value/identity semantics verbatim (the framework helpers are
# unchanged at base_commit; the == / in operators it exercises ARE the real
# builtins), and asserts the model predicates agree with them on the same
# boundary + fuzz grid as axiom_check.py — including the decisive fact that a
# Table handle (no __eq__) never value-equals a bare name (the pre-patch bug).
#
# The probe is self-contained (stdlib only); it does NOT import Django and does
# NOT read any bundle file (the runner mounts only the probe at /work). Mirrors
# axiom_check.py's logic so it is checkable in-container under the instance image
# regardless of Django being importable.
_AX_PROBE = r'''
import random, sys

# --- real unchanged ddl_references semantics (verbatim, base_commit) ----------
class Reference:
    def references_table(self, table): return False
    def references_column(self, table, column): return False

class Table(Reference):
    def __init__(self, table, quote_name):
        self.table = table
        self.quote_name = quote_name
    def references_table(self, table):
        return self.table == table
    # NB: no __eq__ => a Table instance value-equals nothing but itself.

class TableColumns(Table):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns
    def references_column(self, table, column):
        return self.table == table and column in self.columns

class Columns(TableColumns):
    def __init__(self, table, columns, quote_name, col_suffixes=()):
        self.quote_name = quote_name
        self.col_suffixes = col_suffixes
        super(Columns, self).__init__(table, columns)

# --- model.py deep-model reference encodings (lock-step with the pure region) -
def member(c, cols):
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols[1:])

def constrains_column(plain, table, cols, q_table, q_col):
    return plain and table == q_table and member(q_col, cols)

def constrains_table(table, q_table):
    return table == q_table

def check_member(c, cols):
    observed = (c in cols)
    modeled = member(c, list(cols))
    assert observed == modeled, ("member unsound: %r in %r => obs %r model %r"
                                 % (c, cols, observed, modeled))

def check_column(db_table, columns, q_table, q_col):
    quote = lambda s: '"%s"' % s
    post = Columns(db_table, list(columns), quote)
    real_post = post.references_column(q_table, q_col)
    model_post = constrains_column(True, db_table, list(columns), q_table, q_col)
    assert real_post == model_post, ("constrains_column(bare) real=%r model=%r"
                                     % (real_post, model_post))
    pre = Columns(Table(db_table, quote), list(columns), quote)
    real_pre = pre.references_column(q_table, q_col)
    model_pre = constrains_column(False, db_table, list(columns), q_table, q_col)
    assert real_pre is False, ("expected pre-patch references_column False, got %r"
                               % real_pre)
    assert real_pre == model_pre, ("constrains_column(handle) real=%r model=%r"
                                   % (real_pre, model_pre))

def check_table(db_table, q_table):
    quote = lambda s: '"%s"' % s
    real = Table(db_table, quote).references_table(q_table)
    modeled = constrains_table(db_table, q_table)
    assert real == modeled, ("constrains_table real=%r model=%r" % (real, modeled))

def main():
    tables = ["schema_author", "schema_book", "name_uq", "x", "", "T"]
    cols_sets = [["name"], ["name", "height"], [], ["a", "b", "c"],
                 ["name", "name"], ["id"]]
    queried = ["name", "height", "id", "missing", "a", "c", ""]
    boundary = 0
    for db in tables:
        for cols in cols_sets:
            for qc in queried + cols:
                check_member(qc, cols)
            for qt in tables:
                for qc in queried:
                    check_column(db, cols, qt, qc)
                    boundary += 1
                check_table(db, qt)
    # decisive F2P shape: constrained column of the constraint's own table is
    # referenced post-patch (bare name), never pre-patch (Table handle).
    quote = lambda s: '"%s"' % s
    assert Columns("schema_author", ["name"], quote).references_column(
        "schema_author", "name") is True
    assert Columns(Table("schema_author", quote), ["name"], quote).references_column(
        "schema_author", "name") is False
    rng = random.Random(14434)
    fuzz = 0
    for _ in range(20000):
        n = rng.randint(0, 8)
        cols = [rng.randint(0, 12) for _ in range(n)]
        c = rng.randint(0, 12)
        check_member(c, cols)
        plain = bool(rng.getrandbits(1))
        assert constrains_column(plain, [1, 2, 3], cols, [1, 2, 3], c) == (
            plain and member(c, cols))
        fuzz += 1
    print("AX OK: member == in, constrains_column/constrains_table == real "
          "ddl_references on %d boundary + %d fuzz; Table-handle wiring always "
          "False (pre-patch bug), bare-name wiring True for constrained columns."
          % (boundary, fuzz))
    sys.exit(0)

main()
'''


def _containment_probe():
    """Containment: enumerate the callee-inputs the MODEL can reach and assert
    each lies in the deep model's domain. The model's `member`/constrains_*
    deep models are TOTAL over PSeq[int] / List[int] (any finite int sequence,
    any int), with NO Requires restricting the domain. The caller
    build_constraint_columns only ever passes finite int sequences (table code
    points, column codes) and ints. So every reachable callee-input is trivially
    in-domain. We assert this by exercising the deep models on the same shapes
    the caller produces (and degenerate ones) without precondition violation."""
    return _AX_CONTAIN


_AX_CONTAIN = r'''
import sys

def member(c, cols):
    if len(cols) == 0:
        return False
    return cols[0] == c or member(c, cols[1:])

def constrains_column(plain, table, cols, q_table, q_col):
    return plain and table == q_table and member(q_col, cols)

def constrains_table(table, q_table):
    return table == q_table

# The caller build_constraint_columns reaches the deep models only with:
#   - table / q_table: finite List[int] of code points (incl. empty)
#   - cols: finite PSeq[int] (incl. empty, with repeats)
#   - q_col: any int
# The deep models are TOTAL (no Requires narrows the domain), so every
# caller-reachable input is in-domain. Exercise the full reachable shape grid;
# any IndexError / recursion failure would indicate a domain gap. There is no
# input the caller can reach that the deep models do not accept.
shapes = [[], [7], [1, 2, 3], [5, 5, 5], list(range(0, 9))]
ints = [-1, 0, 1, 5, 7, 1000000]
n = 0
for cols in shapes:
    for c in ints:
        _ = member(c, cols)
        for t in shapes:
            for qt in shapes:
                _ = constrains_column(True, t, cols, qt, c)
                _ = constrains_column(False, t, cols, qt, c)
                _ = constrains_table(t, qt)
                n += 1
print("AX-CONTAIN OK: deep models total over all %d caller-reachable "
      "(table, cols, q_table, q_col) shapes; no reachable input is outside "
      "the model domain." % n)
sys.exit(0)
'''


AXIOM_TESTS = [
    {"id": "ax-ref-ddl-references", "axiom": "member/constrains_column/constrains_table",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_PROBE,
     "rationale": "A-reference soundness (re-runnable G-AX): the deep models member / "
                  "constrains_column / constrains_table must equal the real unchanged "
                  "django.db.backends.ddl_references semantics (TableColumns.references_"
                  "column = self.table==table and column in self.columns; "
                  "Table.references_table = self.table==table) on every input in the "
                  "boundary + 20000-fuzz grid, INCLUDING the decisive identity fact that a "
                  "Table handle (no __eq__) never value-equals a bare name. The probe "
                  "reproduces the unchanged framework semantics verbatim (stdlib only, no "
                  "Django import, no bundle file) and exercises the REAL == / in operators. "
                  "If any observation disagrees => the deep model is unsound (AXIOM-UNSOUND)."},
    {"id": "ax-contain-deep-models", "axiom": "member/constrains_column/constrains_table",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _containment_probe(),
     "rationale": "containment: every callee-input the model build_constraint_columns can "
                  "reach (finite int code-point sequences for table/q_table, finite int "
                  "column sequences for cols, any int q_col) lies in the deep models' "
                  "domain. The deep models are TOTAL (no Requires narrows them), so the "
                  "full reachable shape grid is accepted with no domain gap. A reachable "
                  "input outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER; there is "
                  "none."},
]
