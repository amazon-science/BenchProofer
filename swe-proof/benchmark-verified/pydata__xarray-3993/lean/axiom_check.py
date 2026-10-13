#!/usr/bin/env python3
"""G-AX skip stub for pydata__xarray-3993.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`DataArray.integrate`) resolves which
coordinate the integration runs along, rejects a contradictory `dim`/`coord`
pair, and records whether a deprecation notice is raised. The downstream
integration step (`self._to_temp_dataset().integrate(coord, datetime_unit)` then
`_from_temp_dataset`) is left as a universally-quantified parameter
`integrateAlong : Option a -> DS` in Solution.lean -- the spec holds for EVERY
such step, so the proof consumes no property of it. There is no `opaque` callee
and no `axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The resolution impl (and its binding to the REAL downstream integrate
callee) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "pydata__xarray-3993",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "downstream integration step is universally quantified, so the "
                  "impl is all R/I/A-reference (validated by G-CONF against the "
                  "real DataArray._to_temp_dataset().integrate callee)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
