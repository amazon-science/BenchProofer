#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13128.

This bundle consumes NO @ContractOnly axiom. The changed operation — the
resolve-time classification of a binary combined database expression into the
plain / duration / temporal-subtraction forms — is modelled DEEPLY in model.py
(`resolved_kind`, the dispatch over the operand output-type codes). This script
validates that deep model as an A-REFERENCE: it drives the REAL Django
`CombinedExpression.resolve_expression` POST-PATCH (gold-applied, in the
official container) over the full enumeration of (operand type, operand type,
connector, already-temporal) cases and asserts that the class of expression the
real resolution yields is exactly the kind the deep model predicts.

IMPORTANT — the A-reference is the *patched* callee. The resolve-time
classification this script checks is exactly the branch the gold patch INSERTS
into `resolve_expression`; at base_commit that branch does not exist (the
dispatch lived only in `as_sql`), so the check is only meaningful with the gold
patch applied. To be correct regardless of how the G-AX runner invokes it
(`apply_gold` True or False), this script SELF-APPLIES the gold patch
(`/work/patch.diff`, == the gold patch verbatim) to /testbed before importing
Django, idempotently (it is a no-op if the runner already applied it).

Mapping of the deep model's integer type codes to real Django field instances:

    T_UNKNOWN (0) -> a Value with NO output_field (its output type is
                     unresolvable: output_field raises FieldError)
    T_DATE    (1) -> DateField
    T_DATETIME(2) -> DateTimeField
    T_TIME    (3) -> TimeField
    T_DURATION(4) -> DurationField
    T_OTHER   (5) -> IntegerField

Resolution-outcome kinds (the DISPATCH DECISION the patched branch makes, i.e.
which specialised wrapper — if any — the resolution NEWLY creates):

    K_PLAIN    (0) <-> no new wrapper: the resolution returns a copy of self
                       (the plain branch). For an already-temporal self this is
                       always the branch taken (the isinstance guard fires), so
                       the result's class equals self's class and no NEW
                       Duration/Temporal wrapper distinct from self is created.
    K_DURATION (1) <-> the resolution NEWLY creates a DurationExpression
                       (and not a TemporalSubtraction) from a plain self.
    K_TEMPORAL (2) <-> the resolution NEWLY creates a TemporalSubtraction from
                       a plain self.

`is_already_temporal` is exercised by starting from a DurationExpression /
TemporalSubtraction instance instead of a plain CombinedExpression, confirming
an already-specialised expression is NOT re-classified (the plain branch fires:
K_PLAIN under the dispatch-decision semantics).

stdlib + Django only (Django is the system under test; available at base_commit
in the container). Exit 0 iff every observation matches the deep model.
"""
import os
import subprocess
import sys


def _ensure_gold_applied():
    """Idempotently git-apply the gold patch (/work/patch.diff, == gold
    verbatim) to /testbed so the REAL `resolve_expression` carries the inserted
    classification branch under test. A no-op if the patch is already applied
    (e.g. the G-AX runner ran with apply_gold=True), and silently skipped if the
    artifacts are not present (running outside the container)."""
    testbed = "/testbed"
    patch = "/work/patch.diff"
    if not (os.path.isdir(testbed) and os.path.isfile(patch)):
        return
    # (Python 3.6 in the eval container: no subprocess.run(capture_output=)/text=.)
    def _git(*argv):
        return subprocess.run(
            ["git", *argv], cwd=testbed,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    # Already applied? `git apply --reverse --check` succeeds iff the patch is
    # already present in the worktree.
    if _git("apply", "--reverse", "--check", patch).returncode == 0:
        return
    res = _git("apply", "-v", patch)
    if res.returncode != 0:
        sys.stderr.write(
            "axiom_check: failed to apply gold patch to /testbed:\n"
            + (res.stderr or res.stdout))
        sys.exit(2)


_ensure_gold_applied()

# --- minimal Django configuration (no database access is performed) ----------
import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={},
        USE_TZ=False,
    )
    django.setup()

from django.db.models import (  # noqa: E402
    DateField, DateTimeField, TimeField, DurationField, IntegerField,
)
from django.db.models.expressions import (  # noqa: E402
    Value, CombinedExpression, DurationExpression, TemporalSubtraction,
)

# --- model.py deep-model encoding (kept in lock-step with model.py) ----------

T_UNKNOWN, T_DATE, T_DATETIME, T_TIME, T_DURATION, T_OTHER = 0, 1, 2, 3, 4, 5
K_PLAIN, K_DURATION, K_TEMPORAL = 0, 1, 2

_DATETIME = {T_DATE, T_DATETIME, T_TIME}


def is_datetime_type(t):
    return t in _DATETIME


def wants_duration(t_lhs, t_rhs):
    return (t_lhs == T_DURATION or t_rhs == T_DURATION) and t_lhs != t_rhs


def wants_temporal(is_sub, t_lhs, t_rhs):
    return is_sub and is_datetime_type(t_lhs) and t_lhs == t_rhs


def resolved_kind(is_already_temporal, is_sub, t_lhs, t_rhs):
    """Reference of model.py's `resolved_kind` deep model."""
    if is_already_temporal:
        return K_PLAIN
    if wants_duration(t_lhs, t_rhs):
        return K_DURATION
    if wants_temporal(is_sub, t_lhs, t_rhs):
        return K_TEMPORAL
    return K_PLAIN


# --- bridge: type code -> a real operand expression --------------------------

def operand(type_code):
    """A Value whose resolved output type is the given code.

    T_UNKNOWN -> a Value with no output_field, whose .output_field raises
    FieldError (exactly the 'no usable output type' the model encodes)."""
    if type_code == T_UNKNOWN:
        return Value(1)                       # no output_field -> FieldError
    field = {
        T_DATE: DateField,
        T_DATETIME: DateTimeField,
        T_TIME: TimeField,
        T_DURATION: DurationField,
        T_OTHER: IntegerField,
    }[type_code]()
    return Value(None, output_field=field)


SUB = CombinedExpression.SUB
ADD = CombinedExpression.ADD


def real_kind(is_already_temporal, is_sub, t_lhs, t_rhs):
    """Drive the REAL Django resolve_expression and read off the DISPATCH
    DECISION (which wrapper, if any, the resolution NEWLY creates)."""
    connector = SUB if is_sub else ADD
    lhs, rhs = operand(t_lhs), operand(t_rhs)
    if is_already_temporal:
        # An already-specialised temporal/duration expression. TemporalSubtraction
        # only accepts (lhs, rhs); use it for SUB, DurationExpression otherwise.
        if is_sub:
            self_expr = TemporalSubtraction(lhs, rhs)
        else:
            self_expr = DurationExpression(lhs, connector, rhs)
    else:
        self_expr = CombinedExpression(lhs, connector, rhs)
    resolved = self_expr.resolve_expression(query=None)
    # The dispatch decision is K_PLAIN exactly when the resolution did not
    # create a NEW specialised wrapper, i.e. the result's class is the same as
    # self's class (the plain copy branch). A new wrapper is created only from a
    # plain self, so we compare against self's class.
    if type(resolved) is type(self_expr):
        return K_PLAIN
    if isinstance(resolved, TemporalSubtraction):
        return K_TEMPORAL
    if isinstance(resolved, DurationExpression):
        return K_DURATION
    return K_PLAIN


def main():
    type_codes = [T_UNKNOWN, T_DATE, T_DATETIME, T_TIME, T_DURATION, T_OTHER]
    checked = 0
    for is_already_temporal in (False, True):
        for is_sub in (False, True):
            for t_lhs in type_codes:
                for t_rhs in type_codes:
                    want = resolved_kind(is_already_temporal, is_sub,
                                         t_lhs, t_rhs)
                    got = real_kind(is_already_temporal, is_sub, t_lhs, t_rhs)
                    assert got == want, (
                        "deep model unsound on (already_temporal=%r, is_sub=%r,"
                        " t_lhs=%d, t_rhs=%d): real Django resolution yields "
                        "kind %d, deep model predicts %d"
                        % (is_already_temporal, is_sub, t_lhs, t_rhs, got, want))
                    checked += 1

    # Explicit F2P witness: a bare temporal subtraction (DateTimeField -
    # DateTimeField, SUB, not already temporal) MUST classify as temporal and
    # MUST NOT raise the mixed-types FieldError that motivated the fix.
    expr = CombinedExpression(operand(T_DATETIME), SUB, operand(T_DATETIME))
    resolved = expr.resolve_expression(query=None)
    assert isinstance(resolved, TemporalSubtraction), (
        "F2P witness failed: bare DateTimeField - DateTimeField did not "
        "resolve to TemporalSubtraction (got %r)" % type(resolved).__name__)
    # The resolved temporal subtraction has a well-defined DurationField output
    # type (no mixed-types FieldError) — the whole point of the change.
    assert resolved.output_field.get_internal_type() == 'DurationField', (
        "F2P witness failed: resolved temporal subtraction lacks a "
        "DurationField output_field")

    # Witness: a duration mixed-type case (DateTimeField - DurationField) -> the
    # duration form, also previously needing an explicit wrapper.
    expr = CombinedExpression(operand(T_DATETIME), SUB, operand(T_DURATION))
    resolved = expr.resolve_expression(query=None)
    assert isinstance(resolved, DurationExpression) and not isinstance(
        resolved, TemporalSubtraction), (
        "duration witness failed: DateTimeField - DurationField did not "
        "resolve to DurationExpression")

    print("G-AX OK: deep model `resolved_kind` == real Django "
          "CombinedExpression.resolve_expression classification over %d "
          "enumerated cases + F2P temporal/duration witnesses" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
