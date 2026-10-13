#!/usr/bin/env python3
"""G-AX skip stub for django__django-11066.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`RenameContentType._rename`) renames one
content-type row located on the database the migration runs against (`db`) and
persists the change to that same database. The behavior the patch changes —
which database the save is directed to — is modeled DEEPLY by `saveTarget` over
an explicit destination (`Option Alias`) versus the router's free choice
(SPEC_GUIDE §3: a deeply-modeled changed decision is never axiomatized). The row
update is modeled deeply by `renameInStore`. The unchanged callees
(`router.allow_migrate_model`, `transaction.atomic`, `db_manager(db)
.get_by_natural_key`) contribute no property the proof consumes: the read is
explicitly directed at `db` and is captured directly by `hasKey (world db)`, and
`transaction.atomic(using=db)` does not route the query (per the issue/hints —
only `save(using=…)` routes). There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The R/I impl (and its binding to the real patched routing) is differential-tested
by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11066",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "save-target routing decision and the row update are modeled "
                  "deeply (saveTarget / renameInStore), so the impl is all R/I "
                  "(validated by G-CONF against the real patched _rename routing)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
