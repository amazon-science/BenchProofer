#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11880.

SKIPPED for this bundle. The modeled function `deepCopyField`'s impl region is
all-A-tagged: its only non-trivial operations are the three imperative-callee
`:|` stubs for the UNCHANGED standard copy helpers — `freshDistinct w` for
`copy.deepcopy(widget, memo)` and `freshCopy em/v` for `self.error_messages.copy()`
and `self.validators[:]` — plus record updates that re-point the clone's
attributes to those fresh objects. There is no R/I computational content to
transliterate and differentially test against patch.diff: the entire observable
behavior (each copied attribute is a distinct object; the value-typed ones also
content-equal) is carried by the A-consumed `freshDistinct`/`freshCopy`
contracts, whose soundness is covered by G-AX (axiom_check.py). Per SPEC_GUIDE
("If the impl region is all-A-tagged, set meta.json conf_skip=true and write a
stub that exits with status=skip").

meta.json records conf_skip=true.
"""
import sys


def main():
    print("status=skip: impl region all-A-tagged (three A-consumed copy-callee "
          "stubs `freshDistinct`/`freshCopy`; no R/I content to differentially "
          "test). Soundness of the A legs is covered by G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
