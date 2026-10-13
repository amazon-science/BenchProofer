#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-10081.

This bundle consumes NO `@ContractOnly` axiom: the only callee the changed code
invokes — the skip-marker probe `_is_skipped` — is UNCHANGED by the patch and is
modelled DEEPLY in model.py as `marked_skipped(flag) == flag` (an A-reference). This
script validates that deep model against the REAL callee, and validates the full
modeled decision `postpone_teardown` against the REAL repo guard.

It runs the genuine `_pytest.unittest._is_skipped` on objects decorated with the
genuine `@unittest.skip` decorator (class-level and method-level, in every
boundary combination), asserting:

  (A-reference) the deep model `marked_skipped(flag) == _is_skipped(obj)`, where
      `flag` is the boolean skip facet model.py records for `obj`
      (`obj_skip == _is_skipped(self.obj)`, `class_skip == _is_skipped(self.parent.obj)`);

  (decision)    the modeled `postpone_teardown(obj_skip, class_skip, usepdb)`
      equals the POST-PATCH repo guard
      `usepdb and not (_is_skipped(self.obj) or _is_skipped(self.parent.obj))`,
      and that the PRE-PATCH guard `usepdb and not _is_skipped(self.obj)`
      differs from it on exactly the class-skipped-only case — the bug the F2P
      test observes.

Imports only the standard library `unittest` and the real `_pytest.unittest`
module the patch edits (run in-container). Exit 0 iff every obligation holds.
"""
import sys
import unittest

# The real repository module the patch edits (provides the unchanged probe).
from _pytest.unittest import _is_skipped


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def marked_skipped_model(flag):
    """model.py deep model `marked_skipped`: the identity on the boolean skip flag."""
    return flag


def postpone_teardown_model(obj_skip, class_skip, usepdb):
    """model.py `postpone_teardown` result: postpone iff --pdb active and the
    test is not skipped (by its own marker OR its enclosing class's marker)."""
    skipped = marked_skipped_model(obj_skip) or marked_skipped_model(class_skip)
    return bool(usepdb and not skipped)


# --- real repo guards (pre- and post-patch), spelled out -----------------------

def guard_postpatch(obj, parent_obj, usepdb):
    """The POST-PATCH guard (gold): considers both the callable and the class."""
    skipped = _is_skipped(obj) or _is_skipped(parent_obj)
    return bool(usepdb and not skipped)


def guard_prepatch(obj, parent_obj, usepdb):
    """The PRE-PATCH guard (buggy): considers only the test callable."""
    return bool(usepdb and not _is_skipped(obj))


# --- object factory: real @unittest.skip on classes and methods ---------------

def make_objs(obj_skip, class_skip):
    """Build a (test-callable obj, enclosing-class obj) pair whose real
    `_is_skipped` results are exactly (obj_skip, class_skip), using the genuine
    @unittest.skip decorator."""

    class Base(unittest.TestCase):
        def test_it(self):
            pass

    if obj_skip:
        Base.test_it = unittest.skip("method skipped")(Base.test_it)

    cls = Base
    if class_skip:
        cls = unittest.skip("class skipped")(Base)

    method_obj = cls.test_it  # the test callable (self.obj)
    class_obj = cls           # the enclosing class (self.parent.obj)
    return method_obj, class_obj


def main():
    combos = [(False, False), (False, True), (True, False), (True, True)]
    n_checks = 0
    saw_discriminator = False

    for obj_skip, class_skip in combos:
        method_obj, class_obj = make_objs(obj_skip, class_skip)

        # (A-reference) the recorded facets must equal the REAL probe.
        real_obj_flag = _is_skipped(method_obj)
        real_class_flag = _is_skipped(class_obj)
        assert real_obj_flag == obj_skip, (
            "facet mismatch: _is_skipped(method)=%r but model records obj_skip=%r"
            % (real_obj_flag, obj_skip))
        assert real_class_flag == class_skip, (
            "facet mismatch: _is_skipped(class)=%r but model records class_skip=%r"
            % (real_class_flag, class_skip))
        # is_skipped(flag) == _is_skipped(obj) on both sites.
        assert marked_skipped_model(obj_skip) == real_obj_flag
        assert marked_skipped_model(class_skip) == real_class_flag

        for usepdb in (False, True):
            model = postpone_teardown_model(obj_skip, class_skip, usepdb)
            real = guard_postpatch(method_obj, class_obj, usepdb)
            assert model == real, (
                "decision mismatch obj_skip=%r class_skip=%r usepdb=%r: "
                "model=%r real-postpatch-guard=%r"
                % (obj_skip, class_skip, usepdb, model, real))
            n_checks += 1

            # The pre-patch guard must diverge from the model exactly on the
            # class-skipped-only case under --pdb (the bug the F2P test sees).
            pre = guard_prepatch(method_obj, class_obj, usepdb)
            if usepdb and class_skip and not obj_skip:
                assert pre != model and pre is True and model is False, (
                    "expected the pre-patch bug on class-only skip: "
                    "pre=%r model=%r" % (pre, model))
                saw_discriminator = True
            else:
                assert pre == model, (
                    "pre-patch guard should agree off the discriminator: "
                    "obj_skip=%r class_skip=%r usepdb=%r pre=%r model=%r"
                    % (obj_skip, class_skip, usepdb, pre, model))

    assert saw_discriminator, "the discriminating class-skip case was never exercised"

    print("G-AX OK: marked_skipped deep model == real _pytest.unittest._is_skipped "
          "and postpone_teardown == real post-patch guard over all %d "
          "(obj_skip, class_skip, usepdb) combinations; pre-patch guard diverges "
          "exactly on the class-only skip case under --pdb." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
