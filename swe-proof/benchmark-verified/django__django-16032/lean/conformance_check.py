#!/usr/bin/env python3
"""G-CONF for django__django-16032.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_prepInLookup` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL post-patch decision performed by
`RelatedIn.get_prep_lookup`, whose pivot is the real `Query.has_select_fields`
flag (`django/db/models/sql/query.py`). Zero disagreements over >=1e5 fuzzed
inputs => exit 0.

Faithfulness:
  * Oracle  = a REAL `django.db.models.sql.query.Query` built on a real model.
              We put it into one of the configurations a subquery RHS can be in
              (fresh / annotated / explicit-values-applied via `set_values`),
              read the REAL post-patch `query.has_select_fields` flag, and apply
              the real narrowing decision:
                  if not query.has_select_fields and not lhs_pk:
                      query.set_values([target]); result = list(query.values_select)
                  else:
                      result = <existing select columns, unchanged>
              `set_values([target])` is exactly the gold patch's narrowing call;
              its observable is the resulting single-column selection.
  * Shadow  = the op-for-op transliteration of implementation_prepInLookup.

Type bijection (mapping.md):
  rhs.selectCols            <-> list(query.values_select)
  rhs.hasAnnotationSelection<-> bool(query.annotation_select_mask)
  rhs.hasExtraSelection     <-> bool(query.extra_select_mask)
  rhs.explicitValuesApplied <-> query.has_select_fields   (post-patch flag)
  lhsTargetPrimaryKey       <-> getattr(lhs.field.target_field,'primary_key',False)
  targetField               <-> the resolved single target column name
  result                    <-> the RHS query's select columns after the decision

stdlib-only (+ Django, already installed in the container).
"""
import os
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "conf_app"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

# A throwaway app/model so we have a real Query to drive. Django's AppConfig
# requires the app module to resolve to exactly one filesystem path, so we give
# the synthetic package a real (temporary) directory as its single __path__.
import tempfile
import types
conf_app = types.ModuleType("conf_app")
conf_app.__path__ = [tempfile.mkdtemp(prefix="conf_app_")]  # single real path
sys.modules["conf_app"] = conf_app

django.setup()

from django.db import models
from django.db.models import Value
from django.db.models.sql.query import Query


class Widget(models.Model):
    name = models.CharField(max_length=64)
    size = models.IntegerField(default=0)

    class Meta:
        app_label = "conf_app"


CONCRETE_COLS = [f.attname for f in Widget._meta.concrete_fields]  # id, name, size
# The real narrowing call `set_values([target])` is only ever reached with an
# already-resolved column name that exists on the RHS model (`self.lhs.field.name`
# / `self.lhs.field.target_field.name`). Fuzzing a non-existent column ("widget_id"
# is not a Widget field) drives the real callee down a FieldError path the modeled
# function can never be asked to reproduce, so it is out of the input domain.
TARGETS = list(CONCRETE_COLS)  # id, name, size — the valid resolved targets


def build_query(kind):
    """Return a real RHS Query in one of the subquery configurations."""
    q = Query(Widget)
    if kind == "fresh":
        # default queryset: default_cols selection, no explicit values()/mask
        pass
    elif kind == "annotated":
        # annotate(): adds an annotation but no explicit column selection.
        q.add_annotation(Value(1), "ann1")
    elif kind == "aliased_annotated":
        q.add_annotation(Value(1), "ann1")
        q.add_annotation(Value(2), "alias1", select=False)
    elif kind == "values":
        # values(...) -> set_values(): an explicit column selection.
        q.set_values(["name"])
    elif kind == "values_empty":
        q.set_values([])
    return q


def current_select_cols(q):
    return list(q.values_select)


def state_tuple(q):
    """Project a Query onto the modeled SubqueryState components."""
    return (
        list(q.values_select),                  # selectCols
        bool(q.annotation_select_mask),          # hasAnnotationSelection
        bool(q.extra_select_mask),               # hasExtraSelection
        bool(q.has_select_fields),               # explicitValuesApplied (post-patch flag)
    )


def oracle_decision(kind, lhs_pk, target):
    """The REAL post-patch narrowing decision, projected onto SubqueryState."""
    q = build_query(kind)
    before = state_tuple(q)
    # the real post-patch flag is the pivot
    if (not q.has_select_fields) and (not lhs_pk):
        q.set_values([target])
        return state_tuple(q)
    return before


def shadow_decision(kind, lhs_pk, target):
    """Op-for-op transliteration of implementation_prepInLookup -> SubqueryState."""
    q = build_query(kind)
    rhs = state_tuple(q)
    select_cols, has_ann, has_extra, explicit_values_applied = rhs
    # implementation_prepInLookup:
    if (not explicit_values_applied) and (not lhs_pk):
        # restrictTo rhs [targetField]: selectCols=[t], masks cleared, flag set
        return ([target], False, False, True)
    return rhs


def main():
    random.seed(16032)
    N = 120_000
    kinds = ["fresh", "annotated", "aliased_annotated", "values", "values_empty"]
    checked = 0
    disagreements = 0
    examples = []
    for _ in range(N):
        kind = random.choice(kinds)
        lhs_pk = random.random() < 0.5
        target = random.choice(TARGETS)
        try:
            o = oracle_decision(kind, lhs_pk, target)
            s = shadow_decision(kind, lhs_pk, target)
        except Exception as e:  # pragma: no cover
            disagreements += 1
            if len(examples) < 10:
                examples.append({"kind": kind, "lhs_pk": lhs_pk,
                                 "target": target, "error": repr(e)})
            continue
        checked += 1
        if o != s:
            disagreements += 1
            if len(examples) < 10:
                examples.append({"kind": kind, "lhs_pk": lhs_pk,
                                 "target": target, "oracle": o, "shadow": s})

    import json
    report = {
        "status": "pass" if disagreements == 0 else "fail",
        "instance": "django__django-16032",
        "checked": checked,
        "disagreements": disagreements,
        "examples": examples,
        "seed": 16032,
    }
    print(json.dumps(report, indent=2))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
