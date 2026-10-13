#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16595 (nagini).

SHADOW  — the `# impl-start` / `# impl-end` region of `model.py::reduce`, copied
          VERBATIM below with only the contract calls stripped (the model IS
          Python, so there is no transliteration step).  The region's
          dependencies copy over the same way: the `MigrationStep` carrier class
          (its `Ensures` lines dropped) and the `@Pure` helpers `is_same_field`
          and `joined_by_field_rule` (their `Requires` lines dropped).  Nothing
          else is touched -- no renaming, no restructuring, no `PSeq`/`ToSeq`
          carriers in this bundle (the model's only carriers are `int`
          identifiers, `bool` and a Python list).  There are NO `@ContractOnly`
          callees (mapping.md §3), so every line of the shadow is real modeled
          computation.

ORACLE  — the REAL patched repo function, CALLED, not transliterated:
          `django.db.migrations.operations.fields.AlterField.reduce(operation,
          app_label)` (`django/db/migrations/operations/fields.py:249-267` @
          base_commit f9fe062de5, the symbol mapping.md §1 binds `reduce` to).
          Its fall-through arm `super().reduce(operation, app_label)` is
          `Operation.reduce` (`django/db/migrations/operations/base.py:129-139`),
          which is ALSO really executed -- it is the same call chain, not a
          replica.  The gate applies the gold patch to /testbed and sets
          PYTHONPATH before this script runs, so `AlterField` imported here IS
          the patched class.  Driving it needs no app registry, no database and
          no migration state: the chain reads only the two operations' class,
          their cached lower-cased names, `self.field.db_column` and the two
          `elidable` marks, so genuine `AlterField` / `RemoveField` /
          `RenameField` / `AddField` / `CreateModel` / `DeleteModel` / `RunSQL` /
          `RunPython` instances (elidable and not) are constructed directly and
          handed to the real method.  (Contrast the lean sibling, which
          replicates the method in-process; here it is invoked for real.)

BRIDGE  — mapping.md §2 inverted.  Generation is CONCRETE-FIRST: every input is
          a real Django operation pair, and the abstraction function
          `abstract_step` maps it onto the model's carrier, so no generated
          input can fall outside the model's `Requires`:
            * runtime class  ->  kind tag.  `isinstance(op, AlterField)` ->
              KIND_ALTER, `RemoveField` -> KIND_REMOVE, `RenameField` ->
              KIND_RENAME, anything else -> KIND_OTHER.
            * `model_name_lower` / `name_lower` (`str`, case-folded) -> `int`.
              A single injective interner maps each case-folded name to a
              distinct integer, so integer equality IS case-insensitive string
              equality (mapping.md §2: "any injective str->int encoding
              preserves the tested behaviour").  Non-field operations carry
              neither attribute; they get FRESH never-repeated ids, which is
              sound because the real method's `isinstance` guard short-circuits
              before `is_same_field_operation` is ever reached for them (and the
              shadow's kind test likewise never consults their names).
            * `RenameField.new_name` -> `new_name_lower: int`, same interner.
            * `self.field.db_column is None` -> `not has_explicit_column`.
            * `op.elidable` (`Operation.elidable`, class-level `False` by
              default, declared True by a subclass or by the `RunSQL`/`RunPython`
              constructor kwarg) -> `elidable: bool`, read directly.
            * the whole return protocol -> `Tuple[Optional[List[MigrationStep]],
              bool]`: a returned LIST maps to a list of carriers plus a verdict
              normalised to False, and the *bool* the fall-through yields when
              neither step is elidable maps to `None` plus THAT BOOL, whose
              value is compared (not erased): `AlterField.reduce`'s `super()` is
              `FieldOperation.reduce` (`fields.py:69-72`), which post-processes
              `Operation.reduce`'s bool with
              `... or not operation.references_field(...)`, and the optimizer
              driver reads the difference (`optimizer.py:46-47`, `:50`).
              Results are compared
              as (shape, first-element IDENTITY, carried content): a 1-list must
              hold the very object it names -- `[operation]` and `[self]` are
              DISTINCT normalized results, so the fall-through's two list arms
              cannot be confused with each other -- and the rename branch's
              carried step is compared on all five facets the spec pins (kind /
              owning model / renamed field name / pinned-column status /
              elidable mark), the real carried `AlterField` being run back
              through the same abstraction function.
            * `app_label` is unread on every path (mapping.md §3) and is a fixed
              dummy.

INPUTS  — 13 next-step families (each modeled kind plus non-field classes, in
          elidable and non-elidable form) x self elidable/not x the full
          same/different-name and db_column grid, then seeded fuzz to >= 1e5
          total.  Boundary coverage is asserted, not hoped for: the run aborts
          if any modeled kind tag, any of the FIVE distinct shadow results
          (reorder-granted / reorder-withheld / [nxt] / [this] /
          [nxt, carried]), the matching real shapes, the
          F2P alter-then-alter collapse, or either elidable fall-through arm
          (including the both-elidable precedence case and the same-field pair
          whose rename guard rejects it) went unexercised.  Pinned seed: 16595
          (recorded in mapping.md "## G-CONF").  stdlib + the repo under test
          only.

Exit 0 iff zero disagreements.
"""
import json
import random
import sys
from typing import List, Optional      # noqa: F401  (model.py's own imports;
#                                       keeps the copied `# type:` comments valid)

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.db import migrations, models                        # noqa: E402
from django.db.migrations.operations.fields import (             # noqa: E402
    AddField, AlterField, FieldOperation, RemoveField, RenameField,
)

SEED = 16595
N_FUZZ = 100_000
APP_LABEL = "migrations"          # unread on every path (mapping.md §3)


# ===========================================================================
# SHADOW: model.py, contracts stripped, otherwise verbatim.
# ===========================================================================

# Step-kind tags (distinct small integers).
KIND_OTHER = 0
KIND_ALTER = 1
KIND_REMOVE = 2
KIND_RENAME = 3


class MigrationStep:
    def __init__(self, kind, model_name_lower, name_lower,
                 new_name_lower, has_explicit_column, elidable):
        self.kind = kind
        self.model_name_lower = model_name_lower
        self.name_lower = name_lower
        self.new_name_lower = new_name_lower
        self.has_explicit_column = has_explicit_column
        self.elidable = elidable


# pure-start (model.py @Pure helpers, Requires stripped)
def is_same_field(this, other):
    """Two field steps act on the same field iff they name the same model and
    the same field (compared case-insensitively, hence on the lower-cased
    names)."""
    return (this.model_name_lower == other.model_name_lower
            and this.name_lower == other.name_lower)


def joined_by_field_rule(this, nxt):
    """The same-field rules resolve this pair: the two steps touch the same
    field and the later one either alters it again, removes it, or renames it
    while the alteration pins no explicit stored-column name."""
    return (is_same_field(this, nxt)
            and (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE
                 or (nxt.kind == KIND_RENAME
                     and not this.has_explicit_column)))
# pure-end


def reduce(this, nxt, nxt_references_altered_field):
    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end


# ===========================================================================
# BRIDGE: concrete Django operation -> model carrier (mapping.md §2 inverted).
# ===========================================================================

_INTERN = {}


def _ident(name):
    """Injective case-folded-str -> int (mapping.md §2)."""
    key = name.lower()
    if key not in _INTERN:
        _INTERN[key] = len(_INTERN) + 1
    return _INTERN[key]


_FRESH = [10 ** 6]


def _fresh():
    """A never-repeated id, for a name the modeled path provably never reads."""
    _FRESH[0] += 1
    return _FRESH[0]


def abstract_step(op):
    """The abstraction function alpha: real migration operation -> MigrationStep.

    Total on every operation the optimizer can hand to `AlterField.reduce`, so
    every generated concrete pair lands inside the model's input domain.

    Whether the operand references the altered field is NOT part of alpha: the
    repository asks it as a query over the pair
    (`op.references_field(altered.model_name, altered.name, app_label)`), and no
    operation instance carries it as state, so `abstract_pair_reference` below
    computes it separately and it is passed as an argument to the reduction.
    """
    if isinstance(op, AlterField):
        kind = KIND_ALTER
    elif isinstance(op, RemoveField):
        kind = KIND_REMOVE
    elif isinstance(op, RenameField):
        kind = KIND_RENAME
    else:
        kind = KIND_OTHER
    if isinstance(op, FieldOperation):
        model_name_lower = _ident(op.model_name)
        name_lower = _ident(op.name)
    else:
        # No model/field name exists, and none is read: the real method's
        # isinstance guard fails before is_same_field_operation, and the
        # shadow's kind test fails before is_same_field.
        model_name_lower = _fresh()
        name_lower = _fresh()
    if isinstance(op, RenameField):
        new_name_lower = _ident(op.new_name)
    else:
        new_name_lower = _fresh()
    field = getattr(op, "field", None)
    has_explicit_column = (field is not None
                           and getattr(field, "db_column", None) is not None)
    return MigrationStep(kind, model_name_lower, name_lower, new_name_lower,
                         has_explicit_column, bool(op.elidable))


def abstract_pair_reference(nxt_op, altered_op):
    """The pair-level fact, from the REAL predicate, called -- whichever
    override the operand's own class supplies."""
    return bool(nxt_op.references_field(altered_op.model_name,
                                        altered_op.name, APP_LABEL))


def _carried_facets(step):
    return (step.kind, step.model_name_lower, step.name_lower,
            step.has_explicit_column, step.elidable)


def norm_shadow(pair, this_a, nxt_a):
    """Shadow result -> (shape, first-element identity, carried facets).

    The shadow returns (steps, optimize_across). When steps is None the pair is
    not combined here and the REORDERING VERDICT is the answer, so it is carried
    into the normal form -- the two not-combined answers are DISTINCT results,
    not one.
    """
    res, across = pair
    if res is None:
        return ("flag", bool(across))
    if len(res) == 1:
        who = "nxt" if res[0] is nxt_a else ("this" if res[0] is this_a
                                             else "other")
        return ("one", who)
    if len(res) == 2:
        who = "nxt" if res[0] is nxt_a else ("this" if res[0] is this_a
                                             else "other")
        return ("two", who, _carried_facets(res[1]))
    return ("list%d" % len(res),)


def norm_real(res, self_op, nxt_op):
    """Real result -> the same normal form, via mapping.md §2's bridge.

    A non-list return is the REORDERING VERDICT, and its VALUE is carried into
    the normal form rather than erased. `AlterField.reduce`'s `super()` is
    `FieldOperation.reduce` (`fields.py:69-72`), whose
    `... or not operation.references_field(...)` post-processes
    `Operation.reduce`'s bool, so the non-list answer is genuinely True OR
    False and the optimizer reads the difference (`optimizer.py:46-47` keeps
    right-reduction alive only on True, and `optimizer.py:50` licenses a left
    reduction only when every in-between operation answers exactly True).
    Collapsing both onto one tag would blind this check on precisely the axis
    the model must get right. Both LIST arms of the fall-through
    (`[operation]` when self elides, `[self]` when the operand does) normalize
    to a 1-list tagged with WHICH object survived, so they stay distinguished.
    """
    if not isinstance(res, list):
        return ("flag", bool(res))
    if len(res) == 1:
        who = "nxt" if res[0] is nxt_op else ("this" if res[0] is self_op
                                              else "other")
        return ("one", who)
    if len(res) == 2:
        who = "nxt" if res[0] is nxt_op else ("this" if res[0] is self_op
                                              else "other")
        return ("two", who, _carried_facets(abstract_step(res[1])))
    return ("list%d" % len(res),)


# ===========================================================================
# Concrete input construction.
# ===========================================================================

MODELS = ("Book", "book", "BOOK", "Author", "shelf")
FIELDS = ("title", "Title", "TITLE", "name", "pages")
DBCOLS = (None, "title_col")
NEWNAMES = ("renamed", "Renamed", "title", "name")


# An operation declares itself elidable ("safe to elide and to optimize
# across") either with a class-level attribute -- the documented way for a
# custom field operation -- or, for RunSQL/RunPython, with the constructor
# kwarg. Both set `op.elidable`, which is all `Operation.reduce` reads. The
# subclasses stay `isinstance` of their base, so the real method's isinstance
# guards and the bridge's kind tag both see the same class as before.
class ElidableAlterField(AlterField):
    elidable = True


class ElidableRemoveField(RemoveField):
    elidable = True


class ElidableRenameField(RenameField):
    elidable = True


class ElidableAddField(AddField):
    elidable = True


# Kinds of "next" operation. alter/remove/rename map to the modeled kind tags;
# the rest all abstract to KIND_OTHER. Every family appears in a non-elidable
# and an elidable form, so the fall-through's tri-state is driven from genuinely
# different runtime classes rather than from one synthetic flag.
NEXT_KINDS = ("alter", "alter_elidable", "remove", "remove_elidable",
              "rename", "rename_elidable", "add", "add_elidable",
              "create_model", "delete_model", "run_sql", "run_sql_elidable",
              "run_python_elidable")


def make_self(model, field, db_column, elidable=False, max_length=128):
    cls = ElidableAlterField if elidable else AlterField
    return cls(
        model_name=model, name=field,
        field=models.CharField(max_length=max_length, db_column=db_column),
    )


def make_next(kind, model, field, new_name, db_column):
    if kind in ("alter", "alter_elidable"):
        cls = ElidableAlterField if kind.endswith("_elidable") else AlterField
        return cls(model_name=model, name=field,
                   field=models.CharField(max_length=64, db_column=db_column))
    if kind in ("remove", "remove_elidable"):
        cls = ElidableRemoveField if kind.endswith("_elidable") else RemoveField
        return cls(model_name=model, name=field)
    if kind in ("rename", "rename_elidable"):
        cls = ElidableRenameField if kind.endswith("_elidable") else RenameField
        return cls(model_name=model, old_name=field, new_name=new_name)
    if kind in ("add", "add_elidable"):
        cls = ElidableAddField if kind.endswith("_elidable") else AddField
        return cls(model_name=model, name=field,
                   field=models.IntegerField(db_column=db_column))
    if kind == "create_model":
        return migrations.CreateModel(
            name=model, fields=[(field, models.IntegerField())])
    if kind == "delete_model":
        return migrations.DeleteModel(name=model)
    if kind == "run_sql":
        return migrations.RunSQL("SELECT 1")
    if kind == "run_sql_elidable":
        return migrations.RunSQL("SELECT 1", elidable=True)
    if kind == "run_python_elidable":
        return migrations.RunPython(migrations.RunPython.noop, elidable=True)
    raise AssertionError(kind)


# ===========================================================================
# The differential.
# ===========================================================================

class Run:
    def __init__(self):
        self.checked = 0
        self.disagreements = []
        self.shadow_arms = set()
        self.real_shapes = set()
        self.next_kinds = set()
        self.f2p_seen = 0
        self.self_elides = 0        # fall-through arm 1: earlier step elidable
        self.nxt_elides = 0         # fall-through arm 2: only later step elidable
        self.both_elidable = 0      # the precedence case (earlier mark wins)
        self.same_field_fallthrough = 0   # same field, yet no field rule fires


def check(run, tag, kind, self_model, self_field, self_db, nxt_model,
          nxt_field, new_name, nxt_db, self_elidable=False):
    self_op = make_self(self_model, self_field, self_db, elidable=self_elidable)
    nxt_op = make_next(kind, nxt_model, nxt_field, new_name, nxt_db)

    this_a = abstract_step(self_op)
    nxt_a = abstract_step(nxt_op)
    nxt_ref = abstract_pair_reference(nxt_op, self_op)

    shadow = norm_shadow(reduce(this_a, nxt_a, nxt_ref), this_a, nxt_a)
    raw_real = self_op.reduce(nxt_op, APP_LABEL)
    real = norm_real(raw_real, self_op, nxt_op)

    run.checked += 1
    run.shadow_arms.add(shadow[:2])
    run.real_shapes.add(real[:2])
    run.next_kinds.add(nxt_a.kind)
    if kind == "alter" and shadow == ("one", "nxt"):
        run.f2p_seen += 1
    if not joined_by_field_rule(this_a, nxt_a):
        if this_a.elidable:
            run.self_elides += 1
            if nxt_a.elidable:
                run.both_elidable += 1
        elif nxt_a.elidable:
            run.nxt_elides += 1
        if is_same_field(this_a, nxt_a):
            run.same_field_fallthrough += 1

    if shadow != real:
        if len(run.disagreements) < 8:
            run.disagreements.append({
                "where": tag,
                "self": "AlterField(model_name=%r, name=%r, db_column=%r, "
                        "elidable=%r)"
                        % (self_model, self_field, self_db, self_elidable),
                "next": "%s(model_name=%r, name=%r, new_name=%r, db_column=%r)"
                        % (kind, nxt_model, nxt_field, new_name, nxt_db),
                "abstract_self": "kind=%d model=%d name=%d explicit_column=%r "
                                 "elidable=%r"
                                 % (this_a.kind, this_a.model_name_lower,
                                    this_a.name_lower,
                                    this_a.has_explicit_column,
                                    this_a.elidable),
                "abstract_next": "kind=%d model=%d name=%d new_name=%d "
                                 "elidable=%r"
                                 % (nxt_a.kind, nxt_a.model_name_lower,
                                    nxt_a.name_lower, nxt_a.new_name_lower,
                                    nxt_a.elidable),
                "shadow": repr(shadow),
                "real": repr(real),
                "real_raw": repr(raw_real),
            })
        return False
    return True


def main():
    rng = random.Random(SEED)
    run = Run()

    # --- boundary: exhaustive over the modeled distinctions -----------------
    # every next-kind x self elidable/not x same/different model x same/different
    # field name x case-variation x self db_column present/absent x new_name.
    for kind in NEXT_KINDS:
        for self_elidable in (False, True):
            for same_model in (True, False):
                for same_field in (True, False):
                    for case_shift in (False, True):
                        for self_db in DBCOLS:
                            for new_name in NEWNAMES:
                                sm, sf = "Book", "title"
                                if same_model:
                                    nm = "BOOK" if case_shift else "Book"
                                else:
                                    nm = "Author"
                                if same_field:
                                    nf = "TITLE" if case_shift else "title"
                                else:
                                    nf = "pages"
                                check(run, "boundary", kind, sm, sf, self_db,
                                      nm, nf, new_name, None,
                                      self_elidable=self_elidable)

    n_boundary = run.checked

    # --- the exact F2P shape, spelled out ----------------------------------
    # test_alter_alter_field: two AlterFields on the same field collapse to the
    # second one alone.
    check(run, "f2p", "alter", "Foo", "name", None, "Foo", "name",
          "renamed", None)

    # --- the fall-through's three outcomes, spelled out ---------------------
    # (a) neither step elidable, unrelated later step -> not combined here
    check(run, "fallthrough-none", "create_model", "Book", "title", None,
          "Zed", "other", "renamed", None)
    # (b) only the later step elidable -> the earlier step survives alone
    check(run, "fallthrough-nxt-elides", "run_sql_elidable", "Book", "title",
          None, "Zed", "other", "renamed", None)
    # (c) the earlier step elidable -> the later step survives alone
    check(run, "fallthrough-self-elides", "create_model", "Book", "title",
          None, "Zed", "other", "renamed", None, self_elidable=True)
    # (d) BOTH elidable -> the earlier step's mark takes precedence
    check(run, "fallthrough-both-elidable", "run_sql_elidable", "Book",
          "title", None, "Zed", "other", "renamed", None, self_elidable=True)
    # (e) SAME field, yet no field rule fires: a rename the pinned db_column
    #     rejects, with the rename itself elidable -> the earlier step survives.
    #     (This is why the fall-through clauses are guarded on
    #     joined_by_field_rule and not merely on "different field".)
    check(run, "fallthrough-same-field-pinned-rename", "rename_elidable",
          "Book", "title", "title_col", "Book", "title", "renamed", None)

    # --- seeded fuzz to fill the count -------------------------------------
    while run.checked < n_boundary + 6 + N_FUZZ:
        if run.disagreements:
            break
        kind = rng.choice(NEXT_KINDS)
        sm = rng.choice(MODELS)
        sf = rng.choice(FIELDS)
        self_db = rng.choice(DBCOLS)
        # bias toward the same model/field so the changed guard stays hot
        nm = sm if rng.random() < 0.55 else rng.choice(MODELS)
        nf = sf if rng.random() < 0.55 else rng.choice(FIELDS)
        check(run, "fuzz", kind, sm, sf, self_db, nm, nf,
              rng.choice(NEWNAMES), rng.choice(DBCOLS),
              self_elidable=rng.random() < 0.35)

    if run.disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d)"
              % (len(run.disagreements), run.checked, SEED))
        for d in run.disagreements:
            print("  [%s] self=%s" % (d["where"], d["self"]))
            print("        next=%s" % d["next"])
            print("        alpha(self)=%s" % d["abstract_self"])
            print("        alpha(next)=%s" % d["abstract_next"])
            print("        shadow=%s" % d["shadow"])
            print("        real  =%s   raw=%s" % (d["real"], d["real_raw"]))
        print(json.dumps({"status": "fail", "checked": run.checked,
                          "disagreements": len(run.disagreements),
                          "seed": SEED,
                          "shadow": "direct (contract-stripped impl region)",
                          "examples": run.disagreements}))
        return 1

    # --- coverage obligations: a green run must have exercised the branches --
    # The FIVE DISTINCT results the model can produce, each named by shape AND
    # surviving identity, so "the [this] arm was never taken" cannot hide behind
    # the "one" shape the [nxt] arm also produces -- and both values of the
    # reordering verdict must be seen, so a run that only ever exercised one of
    # them cannot pass while the other stays untested.
    missing = []
    ARMS = (("flag", False), ("flag", True), ("one", "nxt"), ("one", "this"),
            ("two", "nxt"))
    for arm in ARMS:
        if arm not in run.shadow_arms:
            missing.append("shadow result %r never produced" % (arm,))
    for shape in ARMS:
        if shape not in run.real_shapes:
            missing.append("real result %r never produced" % (shape,))
    for k in (KIND_OTHER, KIND_ALTER, KIND_REMOVE, KIND_RENAME):
        if k not in run.next_kinds:
            missing.append("next-step kind %d never generated" % k)
    if run.f2p_seen == 0:
        missing.append("the F2P alter-then-alter collapse was never exercised")
    if run.self_elides == 0:
        missing.append("the fall-through arm for an elidable EARLIER step was "
                       "never exercised")
    if run.nxt_elides == 0:
        missing.append("the fall-through arm for an elidable LATER step was "
                       "never exercised")
    if run.both_elidable == 0:
        missing.append("the both-elidable precedence case was never exercised")
    if run.same_field_fallthrough == 0:
        missing.append("no same-field pair ever reached the fall-through (the "
                       "rename guard's rejection path)")
    if missing:
        print("G-CONF FAIL: input generation is vacuous: " + "; ".join(missing))
        print(json.dumps({"status": "fail", "checked": run.checked,
                          "seed": SEED, "coverage_gaps": missing}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py::reduce agrees "
          "with the real patched AlterField.reduce on %d inputs (boundary grid "
          "+ fuzz, seed=%d), 0 disagreements. Fall-through coverage: "
          "earlier-elides=%d later-elides=%d both-elidable=%d "
          "same-field-fallthrough=%d."
          % (run.checked, SEED, run.self_elides, run.nxt_elides,
             run.both_elidable, run.same_field_fallthrough))
    print(json.dumps({"status": "pass", "checked": run.checked,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "django.db.migrations.operations.fields."
                                "AlterField.reduce (called, patched; its "
                                "super().reduce fall-through is the real "
                                "Operation.reduce)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
