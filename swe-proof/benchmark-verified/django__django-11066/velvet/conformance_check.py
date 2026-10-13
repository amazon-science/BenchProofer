#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11066 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`resolveTarget`) is the write-target resolution of the
content-type persist step in `RenameContentType._rename`
(`django/contrib/contenttypes/management/__init__.py:24-27`):

    with transaction.atomic(using=db):
        content_type.save(using=db, update_fields={'model'})   # <-- the fix

Under the hood `Model.save` / `Model.save_base` resolves the write target as

    using = using or router.db_for_write(self.__class__, instance=self)

(`django/db/models/base.py`). The CHANGED behaviour the spec pins is *which
database alias the single-field UPDATE is committed to*: post-patch an explicit
`using=db` is supplied so the `or` short-circuits to `db`; pre-patch no explicit
alias is supplied so the resolution falls through to `router.db_for_write(...)`.

This is not reproducible as a pure, DB-free R/I shadow this gate can fuzz over
>=1e5 inputs:

  * The only observable the fix produces is a SIDE EFFECT on a live backend —
    the renamed row appears in the database named by the resolved alias. It
    materializes only after `content_type.save(...)` opens the connection named
    by `using` and runs the UPDATE there, inside `transaction.atomic(using=db)`.
    Reproducing it requires standing up two real databases, a ContentType row, a
    `DATABASE_ROUTERS` policy and a `migrate` call — i.e. the F2P integration
    test itself (`test_existing_content_type_rename_other_database`), not a
    transliteration this gate can fuzz.
  * The resolution's R/I content (`src = db if db present else routed`) reduces,
    once an explicit present alias is supplied, to the constant `db`; its R/I
    shadow is just `db` echoed back. There is no input-dependent computation on
    the alias contents to differentially refute — the discriminating fact is the
    BRANCH taken (explicit vs router fallback), which is exercised only by the
    live save/router machinery, covered by axiom_check.py (G-AX).

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region's observable is a
live DB write-routing side effect with no DB-free, input-dependent R/I shadow,
set meta.json conf_skip=true and ship this status=skip stub. Soundness of the
modeled resolution is carried instead by G-VERIFY (the spec provably forces the
resolved alias to equal `db` for an arbitrary routing-policy choice `routed`),
G-DIFF (the prepatch, which falls through to `routed`, fails exactly the
`aliasEq out db` clause), and G-AX (the real `router.db_for_write` can return an
alias != db, and `Model.save(using=db, ...)` commits to db regardless of the
router). See mapping.md section 3/4 and refinement.md section B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-11066 — the modeled do-block "
          "resolves which database alias a content-type UPDATE commits to "
          "(using = using or router.db_for_write(...)); post-patch an explicit "
          "using=db short-circuits the routing fallback. The only observable is "
          "a live DB write-routing side effect with no DB-free, input-dependent "
          "R/I shadow. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + "
          "G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
