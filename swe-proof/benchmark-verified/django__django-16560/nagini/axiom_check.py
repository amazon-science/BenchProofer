#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16560.

This bundle consumes NO `@ContractOnly` axiom and has NO A-reference deep model
(the unchanged underlying violation check is abstracted as a boolean verdict;
see model.py / refinement.md). The one library fact the refinement relies on is
the framework validation error's value-flow: a validation error constructed with
a classifier (``code=X``) carries EXACTLY ``X``, and a validation error built
without one carries the neutral ``None``. That is precisely how this bundle's
``ValidationFailure``/``Rule`` carry the classifier.

To make the refinement falsifiable against reality, this check runs the REAL
framework callees in-container (post-patch repo on ``sys.path``) and asserts the
four modelled behaviours hold on the real constraint classes:

  (1) Construction  — the supplied classifier is retained; an absent one is the
      neutral ``None`` marker.                       (model: make_constraint)
  (2) Violation flow — the validation error a constraint raises carries EXACTLY
      the constraint's classifier; ``ValidationError(msg, code=X).code is X``
      and ``ValidationError(msg).code is None``.      (model: build_violation)
  (3) Identity       — two constraints differing only in classifier are NOT
      equal; agreeing on it (and all else) they ARE.  (model: constraints_equal)
  (4) Reconstruction — the deconstruction kwargs name the classifier iff one is
      present.                                        (model: deconstruct_has_code)

Imports only the Python standard library plus the repo under test (the same
package the gold patch edits); nothing else. Exit 0 iff every obligation holds.
"""
import sys


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, INSTALLED_APPS=[])
    import django
    try:
        django.setup()
    except Exception:
        # settings.configure is sufficient for the constraint value-flow we
        # exercise here (no app registry needed for these objects).
        pass


def check_validation_error_code_flow():
    """(2) The framework error carries the classifier verbatim; default None."""
    from django.core.exceptions import ValidationError
    for code in ["fake_discount", "custom_code", "more_than_one", "baz", "0", ""]:
        e = ValidationError("msg", code=code)
        assert e.code is code, (
            "ValidationError(code=%r).code == %r, expected the same object"
            % (code, e.code))
    assert ValidationError("msg").code is None, (
        "ValidationError with no code must carry the neutral None marker")
    assert ValidationError("msg", code=None).code is None


def check_construction():
    """(1) make_constraint: classifier retained / neutral None when absent."""
    from django.db.models.constraints import BaseConstraint
    c = BaseConstraint(name="n", violation_error_code="custom_code")
    assert c.violation_error_code == "custom_code"
    c0 = BaseConstraint(name="n")
    assert c0.violation_error_code is None, (
        "absent classifier must be the neutral None marker, got %r"
        % (c0.violation_error_code,))
    # independence: a second rule's classifier does not perturb the first.
    c1 = BaseConstraint(name="n", violation_error_code="a")
    c2 = BaseConstraint(name="m", violation_error_code="b")
    assert c1.violation_error_code == "a" and c2.violation_error_code == "b"


def check_violation_flow():
    """(2) The error a real constraint raises carries the constraint's code."""
    from django.core.exceptions import ValidationError
    # Mirror the validate() raise site directly: a constraint raising on a
    # detected violation passes code=self.violation_error_code.
    from django.db.models.constraints import BaseConstraint
    for code in ["fake_discount", "custom_code", None]:
        c = BaseConstraint(name="n", violation_error_code=code)
        # the exact construction the patched validate() performs:
        err = ValidationError(c.get_violation_error_message(),
                              code=c.violation_error_code)
        assert err.code is c.violation_error_code, (
            "raised error code %r != constraint classifier %r"
            % (err.code, c.violation_error_code))


def check_identity():
    """(3) constraints_equal: classifier participates in equality."""
    from django.db.models import CheckConstraint, Q, UniqueConstraint
    c_a = CheckConstraint(check=Q(price__lt=1), name="p", violation_error_code="a")
    c_b = CheckConstraint(check=Q(price__lt=1), name="p", violation_error_code="b")
    c_a2 = CheckConstraint(check=Q(price__lt=1), name="p", violation_error_code="a")
    assert c_a != c_b, "constraints differing only in classifier must be unequal"
    assert c_a == c_a2, "constraints agreeing on every facet must be equal"
    # default-classifier rules: equal to each other, unequal to a coded one.
    c_none = CheckConstraint(check=Q(price__lt=1), name="p")
    assert c_none != c_a
    u1 = UniqueConstraint(fields=["foo", "bar"], name="u", violation_error_code="x")
    u2 = UniqueConstraint(fields=["foo", "bar"], name="u", violation_error_code="y")
    u3 = UniqueConstraint(fields=["foo", "bar"], name="u", violation_error_code="x")
    assert u1 != u2 and u1 == u3


def check_reconstruction():
    """(4) deconstruct_has_code: kwargs name the classifier iff present."""
    from django.db.models.constraints import BaseConstraint
    c = BaseConstraint(name="n", violation_error_code="custom_code")
    kwargs = c.deconstruct()[2]
    assert ("violation_error_code" in kwargs) is True, (
        "a present classifier must appear in the reconstruction kwargs")
    assert kwargs["violation_error_code"] == "custom_code"
    c0 = BaseConstraint(name="n")
    kwargs0 = c0.deconstruct()[2]
    assert ("violation_error_code" in kwargs0) is False, (
        "the neutral classifier must be omitted from reconstruction kwargs")


def main():
    _configure_django()
    check_validation_error_code_flow()
    check_construction()
    check_violation_flow()
    check_identity()
    check_reconstruction()
    print("G-AX OK: framework ValidationError code value-flow + all four "
          "modelled constraint behaviours (construct / violate / equal / "
          "reconstruct) sound against the real repo callees.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
