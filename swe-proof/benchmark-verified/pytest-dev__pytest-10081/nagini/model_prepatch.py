"""Twin-artifact model for pytest-dev__pytest-10081.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A standard-library test-case item, when run under the interactive
  post-mortem debugger option, may postpone its instance-level teardown so the
  debugger can inspect the instance state at the moment of failure. That
  postponement must happen ONLY for a test that is actually going to run — i.e.
  one that is NOT skipped.

  A test counts as skipped if EITHER its own callable carries the
  skip marker OR the enclosing test-case class carries it: a class-level skip
  marker skips every test the class contains, exactly as a marker placed
  directly on the test callable does. Therefore the teardown is postponed iff
  the debugger option is active AND neither the test callable nor its enclosing
  class is marked skipped.

A test-case item is modelled as a minimal class carrying only the two touched
facets: whether the test callable itself is marked skipped, and whether its
enclosing class is. The skip-marker probe is modelled deeply as the read of
that boolean facet (it is the inspection of a single skip flag); nothing opaque
is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TestItem:
    def __init__(self, obj_skip: bool, class_skip: bool) -> None:
        # Level 1: the constructor only writes two fields and calls nothing, so it
        # needs no room beneath it. The lowest level leaves every obligated caller
        # (which must be strictly greater) able to construct a TestItem.
        Requires(MustTerminate(1))
        Ensures(Acc(self.obj_skip) and self.obj_skip == obj_skip)      # type: ignore
        Ensures(Acc(self.class_skip) and self.class_skip == class_skip)  # type: ignore
        self.obj_skip = obj_skip
        self.class_skip = class_skip


# axioms-start
# (no opaque callee is axiomatized: the skip-marker probe is the read of a
#  boolean skip flag, modelled deeply below as `is_skipped`.)
# axioms-end


# pure-start
@Pure
def marked_skipped(flag: bool) -> bool:
    """The skip-marker probe on one object: it reports whether that object
    carries the skip marker. Modelled deeply as the read of the single boolean
    skip flag the probe inspects."""
    return flag
# pure-end


def postpone_teardown(item: TestItem, under_debugger: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(item.obj_skip, 1 / 2) and Acc(item.class_skip, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(item.obj_skip, 1 / 2) and Acc(item.class_skip, 1 / 2))
    # The instance teardown is postponed iff the debugger option is active AND
    # the test is not skipped, where "skipped" holds when EITHER the test
    # callable itself OR its enclosing class carries the skip marker. A
    # class-level skip must suppress the postponement just as a callable-level
    # skip does.
    Ensures(Result() == (under_debugger
                         and not (marked_skipped(item.obj_skip)
                                  or marked_skipped(item.class_skip))))
    # Equivalently pinned on the carriers, so a class-only skip is decisive:
    # whenever the enclosing class is skipped the teardown is never postponed.
    Ensures(Implies(item.class_skip, not Result()))
    Ensures(Implies(item.obj_skip, not Result()))
    Ensures(Implies(not under_debugger, not Result()))
    Ensures(Implies(under_debugger and not item.obj_skip and not item.class_skip,
                    Result()))
    # post-conditions-end
    # impl-start
    skipped = marked_skipped(item.obj_skip)
    if under_debugger and not skipped:
        return True
    return False
    # impl-end
