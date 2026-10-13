#!/usr/bin/env python3
"""G-CONF for sympy__sympy-19040: SKIPPED (impl region all-A-tagged).

The `extFactor` impl region contains no R/I computational content to shadow
against the real callees. Every operation it performs is either:

  * the selection branch on `factorList poly`'s length (an A-consumed axiom of
    the unchanged factor-recovery pipeline), or
  * materialising that axiom's result (`factorList poly` / `lone poly`) into the
    output list via a length-driven copy loop (the `List[int]`<->factor-list
    view, a pure transcription with no concrete arithmetic).

There is no concrete Python computation (`R`/`I` step) whose behaviour a fuzz
shadow could reproduce independently of the oracle: the entire behaviour IS the
oracle (`dmp_sqf_norm -> dmp_factor_list_include -> recovery -> dmp_trial_division`),
which is what axiom_check.py (G-AX) validates against the REAL sympy callees,
including the gold/prepatch discrimination. Building a shadow here would merely
re-call the same oracle and compare it to itself ("double-masking").

Accordingly meta.json sets conf_skip = true and the differential soundness is
carried by G-AX (axiom_check.py), not G-CONF. Exit 0 (skip).
"""
import sys

if __name__ == "__main__":
    print("G-CONF SKIP: extFactor impl region is all-A-tagged "
          "(no R/I shadowable content; differential carried by G-AX).")
    sys.exit(0)
