#!/usr/bin/env python
"""G-AX skip stub for sphinx-doc__sphinx-9658.

No consumed callee axiom is declared in the bundle: the operation the patch
introduces (`self.__qualname__ = self.__name__`, i.e. report the short name the
stand-in was created with) is a value-level string identity, modeled DEEPLY in
Lean as the `String` identity `result = name`. It is validated against the real
patched stand-in by the differential `conformance_check.py` (G-CONF), not by an
axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (qualified-name identity "
          "modeled deeply; validated by G-CONF)")
    sys.exit(0)
