#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15525 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`naturalKeyForLoadedRecord`) is the natural-key branch
of `build_instance(Model, data, db)`:

    obj = Model(**data)
    obj._state.db = db                 # <-- the fix: associate with target DB
    natural_key = obj.natural_key()    # derivation routed by obj._state.db

The CHANGED op the spec pins is `obj._state.db = db` — associating a LIVE ORM
model instance with the target database, executed BEFORE the natural-key
derivation. Its only observable is a side effect on routing: which database the
reference-following query inside `obj.natural_key()` (e.g.
`self.author.natural_key()`) targets. It is not reproducible as a pure, DB-free
R/I shadow:

  * The behavioural difference between fixed and buggy code is *which database*
    the FK lookup in `natural_key()` reads from. Observing it requires standing
    up >=2 Django databases, a model whose `natural_key()` follows a foreign key
    (a natural-key dependency), and a fixture whose related row exists only in
    the non-default database — i.e. the F2P integration test itself
    (NaturalKeyFixtureOnOtherDatabaseTests.test_natural_key_dependencies), not a
    transliteration this gate can fuzz over >=1e5 inputs.
  * The changed op's content is the constant state assignment
    `obj._state.db = db`; its only DB-free R/I shadow is the constant target
    alias. Diffing `db == db` carries no information — there is no
    input-dependent computation to refute. The natural-key derivation
    (`naturalKeyVia`) is the A-tagged opaque callee, left as the real
    `obj.natural_key()`, and its value is exactly the DB-routed read that
    cannot be reproduced DB-free.

Per SPEC_GUIDE section 0 / WORKER_PROMPT (django-11179 / django-13089
precedent): when the impl region is the deep state mutation of a live ORM
instance with no DB-free R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub. Soundness of the modeled mutation is carried instead by
G-VERIFY (the spec provably forces `storeHandle = some targetDb` and
`key = naturalKeyVia (some targetDb)` on return — derive AFTER associate) and
G-DIFF (the prepatch, which derives the key before associating the record and
never sets the handle, fails exactly those clauses). See mapping.md section 4
and refinement.md section C.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-15525 — the modeled do-block "
          "associates a live ORM instance with the target database "
          "(obj._state.db = db) before deriving its natural key; the changed op "
          "is a constant state mutation with no DB-free, input-dependent R/I "
          "shadow (the only observable is which database natural_key()'s "
          "foreign-key lookup routes to). conf_skip=true. Soundness covered by "
          "G-VERIFY + G-DIFF + G-RESOLVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
