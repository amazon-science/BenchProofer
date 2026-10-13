#!/usr/bin/env python3
"""G-AX skip stub for django__django-15252.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the head of `MigrationExecutor.migrate`,
executor.py:91-100) is a pure control-flow guard over two inputs: the planned
batch `plan` (None / [] / non-empty) and whether the bookkeeping table already
exists (`recorder.has_table()`). Both enter the model as plain data
(`plannedOps : Option (List PlannedOp)`, `tableExists : Bool`), and the guarded
decision the patch adds is modeled DEEPLY (SPEC_GUIDE §3: a deeply-modeled
changed decision is never axiomatized). The unchanged callees
(`recorder.ensure_schema`, `recorder.has_table`, `_create_project_state`, and the
unchanged remainder) contribute no property the proof consumes: the provisioning
step is observed only as the boolean `Outcome.provisionedTable`, the table-
presence query is the input `tableExists`, and the two returned project states
are opaque structural carriers (`State.projectState false` /
`State.continuationResult plannedOps`). There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The R/I impl (and its binding to the real patched control flow) is differential-
tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-15252",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "table-provisioning guard is a pure control-flow decision over "
                  "plannedOps and tableExists, modeled deeply, so the impl is all "
                  "R/I (validated by G-CONF against the real patched migrate head)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
