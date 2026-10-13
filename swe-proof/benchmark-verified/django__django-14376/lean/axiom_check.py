#!/usr/bin/env python3
"""G-AX skip stub for django__django-14376.

No consumed callee axiom is declared in the bundle. The behaviors the patch
changes are modeled DEEPLY in Lean as R/I implementations, validated against the
real post-patch behavior by the differential `conformance_check.py` (G-CONF), not
by an axiom:

  * `dbArg` (mysql/client.py): the precedence among option sources for the
    trailing database-name argument ('database' key, then deprecated 'db' key,
    then NAME) is modeled as nested `Option.getD` selection over optional-string
    inputs;
  * `connParams` (mysql/base.py): the keys under which the database name and
    password are recorded in the connection-kwargs mapping ('database'/'password')
    are modeled as association-list construction.

The settings/option reads (`settings_dict[...]`, `OPTIONS.get(...)`) and per-source
truthiness are abstracted at the boundary into the optional-string / string
inputs; there is no `opaque`/`axiom` callee whose contract the proof consumes.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-14376",
    "reason": "no consumed callee axiom and no A-reference; both impls are all "
              "R/I (database-name precedence + connection-kwargs keys validated "
              "by G-CONF)",
}))
sys.exit(0)
