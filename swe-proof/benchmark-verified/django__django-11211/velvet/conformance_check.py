#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11211.

SKIPPED for this bundle. The modeled function `preparedValue`'s impl region is
all-A-tagged: its two ops are the unchanged callees `preCoerce` (base
`Field.get_prep_value`) and `canonicalize` (`UUIDField.to_python`), written as
`:|` choice stubs. There is no R/I computational content to transliterate and
differentially test against patch.diff — the entire behavior is the two
A-consumed callees, whose soundness is covered by G-AX (axiom_check.py). Per
SPEC_GUIDE §4.1 ("If the impl region is all-A-tagged, set meta.json
conf_skip=true and write a stub that exits with status=skip").

meta.json records conf_skip=true.
"""
import sys


def main():
    print("status=skip: impl region all-A-tagged (A-consumed callees preCoerce "
          "+ canonicalize); no R/I content to differentially test. Soundness of "
          "the A legs is covered by G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
