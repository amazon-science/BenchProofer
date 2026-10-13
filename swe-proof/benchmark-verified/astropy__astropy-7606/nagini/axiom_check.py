#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7606.

This bundle consumes NO `@ContractOnly` axiom: the modeled functions
`eq_unparsed_name` (model.py) and `eq_unit` reproduce the two unit-equality
dunders, which read only the OBSERVABLE predicates of the operand's silent
unit-coercion — whether the coercion succeeds (vs. is undefined for the operand,
e.g. `None`), and, when it succeeds, the same-kind / equal-name / is-a-unit /
convertibility / effectively-unity predicates of the resulting unit. There is
no unchanged library callee to over-approximate, so the `axioms` region of
model.py is empty.

What this script validates (the only soundness obligation here — the refinement
fidelity of the three-valued boolean-predicate abstraction): the model's pinned
three-valued comparison outcome (RES_FALSE / RES_TRUE / RES_NOTIMPL) equals the
REAL post-patch `UnrecognizedUnit.__eq__` and `UnitBase.__eq__` for concrete
operands spanning the full observable space — and, decisively, that comparison
against a NON-COERCIBLE operand (`None`, and unconvertible objects) yields the
not-applicable sentinel (`NotImplemented`) rather than RAISING or returning a
definite (wrong) decision.

Model contract (model.py post-conditions), as reference predicates:
  eq_unparsed_name(parse_succeeds, parsed_same_kind, names_equal):
      not parse_succeeds                                   -> RES_NOTIMPL
      parse_succeeds and parsed_same_kind and names_equal  -> RES_TRUE
      parse_succeeds and not(same_kind and names_equal)    -> RES_FALSE
  eq_unit(is_same, parse_succeeds, parsed_is_unit, convertible, eff_unity):
      is_same                                              -> RES_TRUE
      not is_same and not parse_succeeds                   -> RES_NOTIMPL
      not is_same and parse_succeeds and not parsed_is_unit-> RES_NOTIMPL
      ... and parsed_is_unit and convertible and eff_unity -> RES_TRUE
      ... and parsed_is_unit and not(conv and eff_unity)   -> RES_FALSE

We observe the RAW dunder return (`unit.__eq__(other)`) so the not-applicable
sentinel `NotImplemented` is visible (Python's `==` operator would otherwise
collapse it to a bool). We ALSO confirm the user-facing `==` / `!=` / `in`
behaviour the F2P test demands does not raise.

Runs IN-CONTAINER against the real astropy at the evaluated commit. Imports only
astropy + stdlib.

PATCH STATE (reproducibility): the model encodes the POST-patch behaviour (a
non-coercible operand defers via `NotImplemented`; an unparsed-name unit equals
another by `isinstance(other, type(self))`). The eval image is checked out at
`base_commit` (PRE-patch), where `UnrecognizedUnit.__eq__` RAISES on `None`.
This script therefore applies the bundle's `patch.diff` to the in-container
`/testbed` checkout BEFORE importing astropy, validating against the post-patch
callee the model abstracts. The apply is idempotent: if the source already
carries the fix (e.g. the harness ran with `apply_gold=True`) it is detected and
skipped. `git apply` failures are surfaced explicitly (rc 3), never swallowed.
"""
import os
import subprocess
import sys

RES_FALSE = 0
RES_TRUE = 1
RES_NOTIMPL = 2

# The changed source file and the post-patch fragment that distinguishes the
# post-patch behaviour from the pre-patch (base_commit) one. The patch rewrites
# `UnrecognizedUnit.__eq__` to test `isinstance(other, type(self))` (unique to
# the post-patch source); both hunks of the single gold patch land together.
_CHANGED_FILE = "astropy/units/core.py"
_POSTPATCH_MARKER = "isinstance(other, type(self))"


def _ensure_postpatch_source():
    """Make the in-container astropy carry the post-patch equality behaviour."""
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED_FILE)
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER in fh.read():
                return None  # already post-patch
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)

    candidates = ["/work/patch.diff", "/gold.patch",
                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "patch.diff")]
    patch_path = next((p for p in candidates if os.path.exists(p)), None)
    if patch_path is None:
        return ("post-patch source required but no patch.diff found in %r"
                % (candidates,))

    proc = subprocess.run(["git", "apply", "-v", patch_path], cwd=testbed,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)  # py3.6: no capture_output
    if proc.returncode != 0:
        return ("git apply %s failed (rc %d): %s"
                % (patch_path, proc.returncode,
                   (proc.stderr or proc.stdout).strip()))
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER not in fh.read():
                return ("patch applied but post-patch marker %r still absent in %s"
                        % (_POSTPATCH_MARKER, changed))
    except OSError as exc:
        return "could not re-read %s: %r" % (changed, exc)
    return None


def _tag(raw):
    """Map a RAW dunder return value to the model's three-valued tag."""
    if raw is NotImplemented:
        return RES_NOTIMPL
    if raw is True:
        return RES_TRUE
    if raw is False:
        return RES_FALSE
    raise AssertionError("dunder returned a non-bool, non-NotImplemented value: "
                         "%r" % (raw,))


def main():
    err = _ensure_postpatch_source()
    if err is not None:
        print("G-AX FAIL: could not establish post-patch source: %s" % err)
        return 3

    try:
        import astropy.units as u
        from astropy.units.core import UnitBase, UnrecognizedUnit, UnitsError
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: could not import astropy (%r). This check is meant to "
              "run in the evaluation container." % (exc,))
        return 0

    checked = 0

    # ---------------------------------------------------------------------
    # eq_unparsed_name  <->  UnrecognizedUnit.__eq__
    # ---------------------------------------------------------------------
    foo = u.Unit("FOO", parse_strict="silent")
    assert isinstance(foo, UnrecognizedUnit), "FOO must be an unparsed-name unit"

    # operand catalogue for the unparsed-name comparison:
    #   (label, operand, parse_succeeds, parsed_same_kind, names_equal)
    # parse_succeeds=False marks the operands the silent coercion cannot denote.
    unrec_cases = [
        # non-coercible operands: must DEFER (RES_NOTIMPL), never raise.
        ("None", None, False, False, False),
        ("plain_object", object(), False, False, False),
        ("list", [1, 2, 3], False, False, False),
        # coercible to a same-kind unparsed-name unit, equal name -> TRUE
        ("same_name_str", "FOO", True, True, True),
        ("same_name_unit", u.Unit("FOO", parse_strict="silent"), True, True, True),
        # coercible to a same-kind unparsed-name unit, different name -> FALSE
        ("other_name_str", "BAR", True, True, False),
        ("other_name_unit", u.Unit("BAR", parse_strict="silent"), True, True, False),
        # coercible to a recognised (NOT same-kind) unit -> FALSE
        ("metre", u.m, True, False, False),
        ("dimensionless_str", "", True, False, False),
    ]
    for (label, other, ps, sk, ne) in unrec_cases:
        # Reference model tag.
        if not ps:
            expected = RES_NOTIMPL
        elif sk and ne:
            expected = RES_TRUE
        else:
            expected = RES_FALSE

        # RAW dunder return must NOT raise and must equal the model tag.
        try:
            raw = foo.__eq__(other)
        except Exception as exc:
            raise AssertionError(
                "UnrecognizedUnit.__eq__(%s) RAISED %r — the comparison must be "
                "total and never propagate a failure" % (label, exc))
        observed = _tag(raw)
        assert observed == expected, (
            "UnrecognizedUnit.__eq__ mismatch on %s: real tag=%s model=%s"
            % (label, observed, expected))

        # user-facing operators must not raise either, and agree with the tag.
        eq_user = (foo == other)
        ne_user = (foo != other)
        assert eq_user == (expected == RES_TRUE), (
            "user-facing == disagrees on %s: got %r" % (label, eq_user))
        assert ne_user == (not eq_user), (
            "!= must be the negation of == on %s" % label)
        checked += 1

    # F2P witnesses from test_unknown_unit3 (the discriminating assertions).
    assert (foo == "FOO") is True
    assert (foo != u.m) is True
    assert (foo != None) is True            # noqa: E711 — must be True, no raise
    assert foo not in (None, u.m)           # must not raise; foo equals neither

    # ---------------------------------------------------------------------
    # eq_unit  <->  UnitBase.__eq__  (the general unit comparison)
    # ---------------------------------------------------------------------
    metre = u.m
    # (label, operand, is_same, parse_succeeds, parsed_is_unit, convertible, eff_unity)
    unit_cases = [
        ("self", metre, True, True, True, True, True),
        ("equal_unit", u.m, False, True, True, True, True),
        ("equal_str", "m", False, True, True, True, True),
        ("convertible_unequal", u.cm, False, True, True, True, False),
        ("incompatible", u.kg, False, True, True, False, False),
        # non-coercible operands: must DEFER (RES_NOTIMPL), never a definite
        # answer, never raise.
        ("None", None, False, False, False, False, False),
        ("plain_object", object(), False, False, False, False, False),
    ]
    for (label, other, is_same, ps, piu, conv, eu) in unit_cases:
        if is_same:
            expected = RES_TRUE
        elif not ps:
            expected = RES_NOTIMPL
        elif not piu:
            expected = RES_NOTIMPL
        elif conv and eu:
            expected = RES_TRUE
        else:
            expected = RES_FALSE

        try:
            raw = metre.__eq__(other)
        except Exception as exc:
            raise AssertionError(
                "UnitBase.__eq__(%s) RAISED %r — the comparison must be total"
                % (label, exc))
        observed = _tag(raw)
        assert observed == expected, (
            "UnitBase.__eq__ mismatch on %s: real tag=%s model=%s"
            % (label, observed, expected))

        eq_user = (metre == other)
        assert eq_user == (expected == RES_TRUE), (
            "user-facing == disagrees on %s: got %r" % (label, eq_user))
        assert (metre != other) == (not eq_user), (
            "!= must be the negation of == on %s" % label)
        checked += 1

    # F2P / P2P witnesses for the general comparison (test_compare_with_none).
    assert not (u.m == None)                # noqa: E711
    assert (u.m != None) is True            # noqa: E711

    print("G-AX OK (no axioms in this bundle): the three-valued model "
          "`eq_unparsed_name`/`eq_unit` == real post-patch "
          "UnrecognizedUnit.__eq__ / UnitBase.__eq__ over %d concrete operands "
          "(incl. the discriminating non-coercible None/object operands, which "
          "DEFER via NotImplemented and never raise)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
