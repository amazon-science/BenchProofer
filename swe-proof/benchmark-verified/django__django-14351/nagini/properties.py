# properties.py — PBT falsification battery for django__django-14351.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC case is a full model.py variant built by region-surgery (edits ONLY inside
# the # impl-start/# impl-end region — including the nested invariants block,
# which spec_view elides as part of the impl), so the FROZEN spec
# (axioms/pure/pre/post-conditions + signatures) is never touched and same_spec
# is guaranteed. AXIOM cases are self-contained probes the runner executes in the
# instance Docker image against the real Django callees.
#
# Defended surface (membership_group_by_cols):
#   - lhs_cols       : Requires/Ensures Acc(list_pred(lhs_cols), 1/2)  => READ-ONLY
#   - rhs.default_cols, rhs.pk_col : Acc(..., 1/2)                      => READ-ONLY facets
#   - rhs.has_fields, rhs.explicit_cols : full Acc                      => writable (the
#       normalisation mutates exactly these two facets)
#   Load-bearing postconditions:
#     (P1) not rhs_is_query                       => Result == lhs_cols
#     (P2) rhs_is_query and Old(has_fields)       => Result == lhs_cols + Old(explicit_cols)   (grounded, untouched)
#     (P3) rhs_is_query and not Old(has_fields)   => Result == lhs_cols + PSeq(pk_col)          (discriminating constant)
#     (P4) rhs_is_query and not Old(has_fields)   => rhs.has_fields and explicit_cols==PSeq(pk_col)  (PRODUCED-BY post-state)
#     (P5) rhs_is_query and not Old(has_fields)   => Result == lhs_cols + nested_group_by_cols(rhs)   (PRODUCED-BY reader-output)
#     (P6) not (rhs_is_query and not Old(has_fields)) => rhs.has_fields == Old(has_fields)
#          and rhs.explicit_cols == Old(explicit_cols)   (FRAME: rhs untouched off the
#          field-less branch — no gratuitous normalisation of an explicit or literal rhs)

from pathlib import Path

INSTANCE = "django__django-14351"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors inside the impl region (lines 131-164). Every _swap below edits text
# that lives between # impl-start and # impl-end (invariants block included), so
# spec_view elides it and same_spec holds.
# ---------------------------------------------------------------------------

# The gold prelude + normalisation block, used as a unique anchor.
_GOLD_NORMALISE = (
    "    if rhs_is_query:\n"
    "        if not rhs.has_fields:\n"
    "            clear_output_columns(rhs)\n"
    "            add_identity_column(rhs)\n"
    "        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]\n"
)

_GOLD_COLS_INIT = "    cols = list(lhs_cols)  # type: List[int]\n"

_GOLD_LOOP_BODY = (
    "            cols.append(rhs_cols[i])\n"
    "            i = i + 1\n"
)


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT; MUST verify.
# Reshape: capture the per-iteration element into a typed local before the
# append (a local-variable reshape, not a loop-direction flip), and reorder the
# prelude `orig_*` captures. The gold invariants/asserts are kept verbatim so the
# loop-invariant proof still discharges (avoids pilot bug #2/#3). If a faithful
# correct impl like this cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS = _swap(
    _BASE,
    _GOLD_LOOP_BODY,
    "            elem = rhs_cols[i]  # type: int\n"
    "            cols.append(elem)\n"
    "            i = i + 1\n",
)
# also reorder the orig_* prelude captures (pure local reshape, no spec effect)
_POS = _swap(
    _POS,
    "    orig_default = rhs.default_cols  # type: PSeq[int]\n"
    "    orig_explicit = rhs.explicit_cols  # type: PSeq[int]\n"
    "    orig_had_fields = rhs.has_fields  # type: bool\n"
    "    orig_pk = rhs.pk_col  # type: int\n",
    "    orig_pk = rhs.pk_col  # type: int\n"
    "    orig_had_fields = rhs.has_fields  # type: bool\n"
    "    orig_explicit = rhs.explicit_cols  # type: PSeq[int]\n"
    "    orig_default = rhs.default_cols  # type: PSeq[int]\n",
)


# ===========================================================================
# (2) ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
# Add an in-impl Assert immediately after the prelude that the read-only facets
# are readable and the captured representative state is internally consistent
# (an F2P-shaped field-less query: rhs_is_query True, has_fields capturable).
# This exercises that the Requires established the half-permissions on a normal
# input. If the assert (or any subsequent obligation) fails to establish for a
# legitimate input => PRECOND-TOO-STRONG. Kept the rest of the gold impl intact.
# ===========================================================================
_ADMISS = _swap(
    _BASE,
    "    cols = list(lhs_cols)  # type: List[int]\n",
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    Assert(orig_pk == rhs.pk_col)\n"
    "    Assert(orig_default == rhs.default_cols)\n"
    "    Assert(orig_had_fields == rhs.has_fields)\n",
)


# ===========================================================================
# (3) FRAME-MUTATION on lhs_cols (MANDATORY — lhs_cols is Acc(.,1/2) read-only).
# A rival that WRITES to the read-only lhs_cols (appends a column to the caller's
# list) to satisfy the postcondition. It must be REJECTED for INSUFFICIENT
# PERMISSION (only 1/2 of list_pred(lhs_cols) is held). Gold invariants kept
# verbatim so the rejection is attributable solely to the write.
# refinement: the gold patch does `cols = self.lhs.get_group_by_cols()` and only
#   mutates the *local* copy; it never appends to / overwrites the lhs grouping
#   columns object. A faithful real patch that mutated the lhs list in place
#   would corrupt the GROUP BY's left-hand columns for every caller sharing that
#   list (the lhs columns are computed independently of the rhs branch) and
#   would NOT resolve the F2P (the SELECT/GROUP-BY shape would change).
# ===========================================================================
_FRAME_LHS = _swap(
    _BASE,
    "    cols = list(lhs_cols)  # type: List[int]\n",
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    lhs_cols.append(rhs.pk_col)\n",  # WRITE to read-only input
)


# ===========================================================================
# (4) FRAME-MUTATION on rhs.default_cols (read-only facet, Acc(.,1/2)).
# A rival that overwrites the read-only default-column facet (e.g. to force the
# field-less reader to a single column without running the real normalisation).
# Must be REJECTED for INSUFFICIENT PERMISSION (default_cols held at 1/2).
# refinement: the gold normalisation is `clear_select_clause()+add_fields(['pk'])`
#   which manipulates the SELECT/mask facet (has_fields/explicit), NOT the
#   model's default_cols. A patch that reassigned the query's default-column set
#   is not the gold mechanism and would not reproduce the one-column subquery
#   rendering (default_cols=False vs a fabricated value) — would not resolve.
# ===========================================================================
_FRAME_DEFAULT = _swap(
    _BASE,
    "    cols = list(lhs_cols)  # type: List[int]\n",
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    rhs.default_cols = PSeq(rhs.pk_col)\n",  # WRITE to read-only facet
)


# ===========================================================================
# (5) UNGROUNDED-ORACLE ECHO / FABRICATION on the field-less branch.
# A rival that, for a field-less query, FABRICATES the single pk column and
# appends it WITHOUT ever calling clear_output_columns/add_identity_column — it
# never mutates rhs. It satisfies the constant clause (P3) but must FAIL the
# PRODUCED-BY post-state clause (P4: rhs.has_fields and explicit_cols==PSeq(pk))
# and the reader-output clause (P5). expect reject.
# refinement: gold MUTATES self.rhs (clear_select_clause + add_fields(['pk'])) so
#   the subquery expression itself renders exactly one column at SQL time. An
#   impl that fabricates a bare pk col in the returned list but leaves rhs
#   un-normalised does NOT change what the subquery renders — the real
#   `(SELECT U0."id", U0."created", ...)` still emits all default columns =>
#   Postgres "subquery must return only one column" persists => F2P stays RED.
# ===========================================================================
_ECHO = _swap(
    _BASE,
    _GOLD_NORMALISE,
    "    if rhs_is_query:\n"
    "        if not rhs.has_fields:\n"
    "            # FABRICATE the pk contribution without normalising rhs.\n"
    "            cols.append(rhs.pk_col)\n"
    "            return cols\n"
    "        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]\n",
)


# ===========================================================================
# (6) UNCONDITIONAL NORMALISE — partial-domain attacker.
# A rival that runs clear+add on EVERY query rhs (drops the `if not has_fields`
# guard). Correct on the field-less sub-domain, but on the already-explicit
# sub-domain it forces explicit_cols to PSeq(pk_col), so it appends PSeq(pk_col)
# instead of Old(explicit_cols) — violating P2 when Old(explicit_cols) != PSeq(pk).
# expect reject.
# refinement: a query built with values('name') carries explicit columns = [name]
#   (NOT the pk); the gold patch leaves it UNTOUCHED. An impl that unconditionally
#   normalises would rewrite that subquery's SELECT to just `pk`, changing the
#   emitted SQL for every explicit-fields IN-subquery (and the P2P/regression
#   semantics) => would not be a faithful patch and would regress.
# ===========================================================================
_UNCOND = _swap(
    _BASE,
    _GOLD_NORMALISE,
    "    if rhs_is_query:\n"
    "        clear_output_columns(rhs)\n"
    "        add_identity_column(rhs)\n"
    "        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]\n",
)


# ===========================================================================
# (7) PARTIAL-DOMAIN on the literal branch — drop the lhs contribution.
# A rival that, for the non-query (literal-collection) rhs, returns an empty list
# instead of the lhs columns. Correct on the query branches, wrong on the
# `not rhs_is_query` sub-domain (violates P1: Result == lhs_cols). expect reject.
# Implemented by initialising cols empty and only filling it from lhs inside the
# query branch (so the literal branch returns []).
# refinement: when the rhs is a plain literal collection the gold patch returns
#   `cols = self.lhs.get_group_by_cols()` unchanged — the left operand's grouping
#   columns. An impl that dropped them would emit the wrong GROUP BY for every
#   literal-rhs IN lookup (the overwhelmingly common case), regressing the P2P
#   aggregation tests => not a faithful patch, would not resolve.
# ===========================================================================
_PARTIAL_LIT = _swap(
    _BASE,
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    if rhs_is_query:\n",
    "    empty = []  # type: List[int]\n"
    "    cols = empty  # type: List[int]\n"
    "    if rhs_is_query:\n"
    "        cols = list(lhs_cols)\n",
)


# ===========================================================================
# (8) GRATUITOUS NORMALISE of an already-explicit rhs AFTER the result is built
# (the G-PANEL-1 attack class). Behaviourally the returned list is correct on
# every branch, but the impl then rewrites an already-explicit nested query's
# output columns to just the pk before returning — a side effect the gold patch
# does not have (gold leaves an explicit rhs UNTOUCHED). Must be REJECTED by the
# FRAME clause P6 (off the field-less branch, has_fields/explicit_cols must be
# preserved). expect reject.
# refinement: gold only mutates self.rhs inside `if not has_select_fields:`;
#   an impl that afterwards clear_select_clause()+add_fields(['pk'])s an
#   explicit values('name') subquery would rewrite that subquery's SELECT to
#   just `pk` at SQL time, changing the emitted SQL for every explicit-fields
#   IN lookup => regresses P2P semantics, not the gold mechanism.
# ===========================================================================
_TRAILING_NORMALISE = _swap(
    _BASE,
    "    return cols\n"
    "    # impl-end",
    "    if rhs_is_query and orig_had_fields:\n"
    "        clear_output_columns(rhs)\n"
    "        add_identity_column(rhs)\n"
    "    return cols\n"
    "    # impl-end",
)


# ===========================================================================
# (9) GRATUITOUS NORMALISE on the literal branch. The rhs object is normalised
# even when the right operand is a plain literal collection (not a query). The
# returned list is still exactly lhs_cols (P1 holds), but the rhs post-state is
# corrupted. Must be REJECTED by the FRAME clause P6. expect reject.
# refinement: when the rhs is a literal collection the gold patch never touches
#   self.rhs at all (the hasattr guard skips the whole rhs block); mutating the
#   rhs object on this branch has no gold counterpart.
# ===========================================================================
_LITERAL_NORMALISE = _swap(
    _BASE,
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    if rhs_is_query:\n",
    "    cols = list(lhs_cols)  # type: List[int]\n"
    "    if not rhs_is_query:\n"
    "        clear_output_columns(rhs)\n"
    "        add_identity_column(rhs)\n"
    "    if rhs_is_query:\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "structurally-different CORRECT impl (per-element typed local "
                     "before append + reordered orig_* prelude); keeps every gold "
                     "loop invariant/framing assert so the proof still discharges. "
                     "Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fieldless-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "in-impl Asserts that the read-only facets (pk_col, "
                     "default_cols, has_fields) captured at entry equal their live "
                     "values confirm the precondition's half-permissions admit a "
                     "normal F2P-shaped input; if this cannot establish for a "
                     "legitimate input => PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mut-lhs-cols",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_LHS,
        "refinement": "gold copies the lhs grouping columns (cols = "
                      "self.lhs.get_group_by_cols()) and mutates only the local "
                      "copy; a patch appending to the caller's lhs list in place "
                      "would corrupt the left-hand GROUP BY columns and change the "
                      "emitted SQL — would NOT resolve the F2P.",
        "rationale": "lhs_cols is Acc(list_pred(lhs_cols), 1/2) (read-only). "
                     "lhs_cols.append(...) needs FULL permission; rejected for "
                     "INSUFFICIENT PERMISSION by the permission system, not by a "
                     "value postcondition.",
    },
    {
        "id": "frame-mut-rhs-default-cols",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_DEFAULT,
        "refinement": "gold normalises via clear_select_clause()+add_fields(['pk']) "
                      "which touches the SELECT/mask facet (has_select_fields), "
                      "never the model's default-column set; a patch reassigning "
                      "default_cols is not the gold mechanism and would not render "
                      "the one-column subquery — would NOT resolve.",
        "rationale": "rhs.default_cols is held at Acc(rhs.default_cols, 1/2) "
                     "(read-only). Assigning rhs.default_cols = ... needs full "
                     "permission; rejected for INSUFFICIENT PERMISSION.",
    },
    {
        "id": "echo-fabricate-pk-no-normalise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ECHO,
        "refinement": "gold MUTATES self.rhs so the subquery expression renders "
                      "exactly one column at SQL time. Fabricating a bare pk col "
                      "in the returned list while leaving rhs un-normalised does "
                      "not change what the subquery renders — the real `(SELECT "
                      "U0.\"id\", U0.\"created\", ...)` still emits all default "
                      "columns => 'subquery must return only one column' persists "
                      "=> F2P stays RED.",
        "rationale": "satisfies the constant clause P3 but FAILS the PRODUCED-BY "
                     "post-state P4 (rhs.has_fields and explicit_cols==PSeq(pk_col)) "
                     "because it never calls add_identity_column; add_identity_column "
                     "is the only producer of explicit_cols==PSeq(pk_col). Rejection "
                     "comes from postcondition P4.",
    },
    {
        "id": "uncond-normalise-explicit-rhs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _UNCOND,
        "refinement": "a values('name') IN-subquery carries explicit columns "
                      "[name] (not the pk); gold leaves it UNTOUCHED. Unconditional "
                      "normalisation rewrites that subquery's SELECT to just `pk`, "
                      "changing the emitted SQL for every explicit-fields IN lookup "
                      "and regressing P2P semantics — not a faithful patch, would "
                      "not resolve.",
        "rationale": "on the already-explicit sub-domain it appends PSeq(pk_col) "
                     "instead of Old(rhs.explicit_cols), violating postcondition P2 "
                     "(Result == lhs_cols + Old(rhs.explicit_cols)) whenever "
                     "Old(explicit_cols) != PSeq(pk_col). Rejection comes from P2 "
                     "(grounded explicit-fields clause).",
    },
    {
        "id": "partial-domain-drop-lhs-literal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_LIT,
        "refinement": "for a plain literal-collection rhs the gold patch returns "
                      "self.lhs.get_group_by_cols() unchanged; dropping the lhs "
                      "columns emits the wrong GROUP BY for the common literal-rhs "
                      "IN lookup, regressing the P2P aggregation tests — not a "
                      "faithful patch, would not resolve.",
        "rationale": "the literal branch returns [] instead of lhs_cols, violating "
                     "postcondition P1 (not rhs_is_query => Result == lhs_cols). "
                     "Rejection comes from P1.",
    },
    {
        "id": "gratuitous-normalise-explicit-after-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _TRAILING_NORMALISE,
        "refinement": "gold mutates self.rhs ONLY inside the `if not "
                      "has_select_fields:` guard; an impl that afterwards runs "
                      "clear_select_clause()+add_fields(['pk']) on an explicit "
                      "values('name') subquery rewrites its SELECT to just `pk` "
                      "at SQL time, changing the emitted SQL for every "
                      "explicit-fields IN lookup — regresses P2P semantics, not "
                      "the gold mechanism.",
        "rationale": "returned list is correct on every branch (P1-P5 hold) but "
                     "the trailing normalisation of an already-explicit rhs "
                     "violates the FRAME clause P6 (Old(has_fields) => "
                     "explicit_cols preserved). This is the exact same-spec "
                     "attack class G-PANEL-1 exploited; rejection comes from P6.",
    },
    {
        "id": "gratuitous-normalise-literal-rhs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _LITERAL_NORMALISE,
        "refinement": "for a literal-collection rhs the gold patch never touches "
                      "self.rhs (the hasattr guard skips the whole rhs block); "
                      "mutating the rhs object on this branch has no gold "
                      "counterpart.",
        "rationale": "P1 still holds (result == lhs_cols) but the rhs object is "
                     "normalised on the literal branch, violating the FRAME "
                     "clause P6 (rhs untouched off the field-less branch). "
                     "Rejection comes from P6.",
    },
]


# ===========================================================================
# AXIOM lane — three A-consumed axioms over UNCHANGED Django callees. The patch
# does not touch get_group_by_cols / clear_select_clause / add_fields, so the
# axioms describe identical behaviour at base_commit and post-gold; apply_gold is
# harmless. Each probe builds an in-process sqlite Django, a multi-field model,
# and drives the REAL callee (never scrapes source). Files opened utf-8. The
# probe is self-contained: it embeds axiom_check.py's executable logic so it does
# not depend on any host file being mounted (runner mounts only the probe).
# ===========================================================================

# The shared Django-bootstrap + observable helpers, embedded verbatim into each
# probe (host-side concatenation; nothing is read in-container except the probe).
_PROBE_PRELUDE = r'''
import os, sys
def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def _rendered_select_cols(query):
    compiler = query.get_compiler(using="default")
    compiler.pre_sql_setup()
    return len(compiler.select)

def _rendered_select_target_names(query):
    compiler = query.get_compiler(using="default")
    compiler.pre_sql_setup()
    names = []
    for col, _sql, _alias in compiler.select:
        target = getattr(col, "target", None)
        names.append(getattr(target, "name", None) if target is not None else None)
    return names

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
try:
    _configure_django()
except Exception as exc:
    print("AXIOM SKIP: Django not configurable: %r" % (exc,))
    sys.exit(0)

from django.db import connection, models

class GroupTarget(models.Model):
    name = models.CharField(max_length=50)
    f1 = models.IntegerField(default=0)
    f2 = models.IntegerField(default=0)
    f3 = models.IntegerField(default=0)
    f4 = models.IntegerField(default=0)
    f5 = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as editor:
    editor.create_model(GroupTarget)

N_DEFAULT = 1 + 6  # id + six declared fields
'''


# ---- axiom-soundness: nested_group_by_cols (the rhs grouping-column reader) ----
_PROBE_AX_READER = _PROBE_PRELUDE + r'''
obs = 0

# not has_fields => reader yields the full default set (> 1 col): the bug surface.
q = GroupTarget.objects.all().query
assert q.has_select_fields is False, q.has_select_fields
n_before = _rendered_select_cols(q)
assert n_before == N_DEFAULT, (n_before, N_DEFAULT)
assert n_before > 1, n_before
obs += 1

# has_fields => reader yields exactly the query's OWN explicit columns (NOT the
# pk). Fuzz the falsifying shapes that a too-strong has_fields=>PSeq(pk) reading
# would wrongly accept.
for fields, want_n, expect_non_pk in [
    (['pk'], 1, False), (['name'], 1, True), (['id', 'name'], 2, True),
    (['name', 'f1'], 2, True), (['f1', 'f2', 'f3'], 3, True),
]:
    qx = GroupTarget.objects.values(*fields).query
    assert qx.has_select_fields is True, (fields, qx.has_select_fields)
    n_x = _rendered_select_cols(qx)
    assert n_x == want_n, (fields, n_x, want_n)
    names = _rendered_select_target_names(qx)
    if expect_non_pk:
        assert 'name' in names or set(fields) & {'f1', 'f2', 'f3'}, (fields, names)
        assert names != ['id'], (fields, names)
    obs += 1

print("AX-SOUND reader OK: not has_fields => %d default cols (>1); has_fields => "
      "exactly the chosen explicit columns (values('name')=>1 non-pk, "
      "values('id','name')=>2, ...) over %d observations" % (N_DEFAULT, obs))
sys.exit(0)
'''


# ---- axiom-soundness: clear_output_columns + add_identity_column ----
_PROBE_AX_NORMALISE = _PROBE_PRELUDE + r'''
obs = 0
# clear_select_clause leaves has_select_fields False; add_fields(['pk']) sets it
# True and the query renders EXACTLY ONE column (the pk). Preserves pk/default
# facets (the reader collapses to one col after normalisation). Fuzz over 60
# fresh field-less queries.
for _ in range(60):
    qi = GroupTarget.objects.all().query
    assert qi.has_select_fields is False
    assert _rendered_select_cols(qi) == N_DEFAULT
    qi.clear_select_clause()              # clear_output_columns
    assert qi.has_select_fields is False, qi.has_select_fields
    qi.add_fields(['pk'])                 # add_identity_column
    assert qi.has_select_fields is True, qi.has_select_fields
    n_after = _rendered_select_cols(qi)
    assert n_after == 1, n_after
    names = _rendered_select_target_names(qi)
    assert names == ['id'], names   # the identity (pk) column is `id`
    obs += 1

# also: applying the normalisation to an ALREADY-explicit query still collapses
# to exactly the pk (idempotent producer of explicit_cols == PSeq(pk_col)).
for fields in (['name'], ['id', 'name'], ['f1', 'f2']):
    qe = GroupTarget.objects.values(*fields).query
    assert qe.has_select_fields is True
    qe.clear_select_clause()
    assert qe.has_select_fields is False
    qe.add_fields(['pk'])
    assert qe.has_select_fields is True
    assert _rendered_select_cols(qe) == 1, (fields, _rendered_select_cols(qe))
    assert _rendered_select_target_names(qe) == ['id'], fields
    obs += 1

print("AX-SOUND normalise OK: clear_select_clause => has_select_fields False; "
      "add_fields(['pk']) => has_select_fields True and exactly 1 col (the pk) "
      "over %d observations" % (obs,))
sys.exit(0)
'''


# ---- axiom-containment: caller-reachable inputs lie in each callee's domain ----
# The model only ever passes a Query rhs (rhs_is_query branch). nested_group_by_cols
# is read after normalisation on a field-less rhs (has_fields True, explicit ==
# PSeq(pk)) OR directly on an already-explicit rhs. clear/add are only ever called
# on a field-less rhs (the `if not has_fields` guard). Confirm the real callees
# accept exactly these reachable states and never raise on them.
_PROBE_AX_CONTAIN = _PROBE_PRELUDE + r'''
obs = 0
# Reachable state A: already-explicit rhs read directly (clear/add skipped).
for fields in (['pk'], ['name'], ['id', 'name'], ['name', 'f1', 'f2']):
    qa = GroupTarget.objects.values(*fields).query
    assert qa.has_select_fields is True
    _ = _rendered_select_cols(qa)   # nested_group_by_cols reachable input: accepted
    obs += 1

# Reachable state B: field-less rhs -> clear -> add -> read (the normalised path).
for _ in range(10):
    qb = GroupTarget.objects.all().query
    assert qb.has_select_fields is False    # clear/add reachable only here
    qb.clear_select_clause()
    qb.add_fields(['pk'])
    assert qb.has_select_fields is True
    _ = _rendered_select_cols(qb)           # nested_group_by_cols on the post-state
    obs += 1

# The model NEVER calls clear/add on an already-explicit rhs (guarded), and the
# reader is the only callee on an explicit rhs — both states above are exactly
# what the callees' real domains accept (no exception raised). Covering MORE
# (e.g. clear/add on explicit rhs, shown idempotent in the soundness probe) is
# SOUND, not a defect; the containment claim is that every reachable input is
# accepted, which holds.
print("AX-CONTAIN OK: every caller-reachable callee-input (explicit-read, "
      "fieldless->clear->add->read) accepted by the real callees over %d "
      "observations" % (obs,))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-nested_group_by_cols",
        "axiom": "nested_group_by_cols",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_AX_READER,
        "rationale": "the real rhs grouping-column reader (Query.get_group_by_cols / "
                     "rendered compiler.select) must match has_fields => "
                     "Result()==explicit_cols and not has_fields => "
                     "Result()==default_cols; fuzzed on values('name')/('id','name')/... "
                     "to falsify any too-strong has_fields=>PSeq(pk) reading. Violation "
                     "=> AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-clear-add-normalise",
        "axiom": "add_identity_column",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_AX_NORMALISE,
        "rationale": "the real clear_select_clause leaves has_select_fields False and "
                     "add_fields(['pk']) sets it True with the query rendering exactly "
                     "one column (the pk) — the explicit_cols==PSeq(pk_col) post-state "
                     "the proof consumes. Violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-caller-domain",
        "axiom": "nested_group_by_cols",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_AX_CONTAIN,
        "rationale": "every callee-input the model can reach (explicit rhs read "
                     "directly; field-less rhs after clear+add) lies in the real "
                     "callees' accepted domain. A reachable input outside the domain "
                     "=> AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
