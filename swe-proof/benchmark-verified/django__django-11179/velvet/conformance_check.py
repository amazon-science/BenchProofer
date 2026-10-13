#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11179 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`fastDelete`) is the single-object, no-dependency
fast-delete short-circuit of `Collector.delete`:

    if self.can_fast_delete(instance):
        with transaction.mark_for_rollback_on_error():
            count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
        setattr(instance, model._meta.pk.attname, None)   # <-- the fix
        return count, {model._meta.label: count}

The CHANGED op the spec pins is `setattr(instance, model._meta.pk.attname, None)`
— clearing the primary-key attribute of a LIVE ORM model instance AFTER a real
database fast-delete. Its only observable is a side effect on that instance
(`instance.pk` becomes `None`), and it is not reproducible as a pure, DB-free
R/I shadow:

  * The state change materializes only after `Collector.delete()` has run
    `sql.DeleteQuery(model).delete_batch([instance.pk], self.using)` against a
    real backend, inside `transaction.mark_for_rollback_on_error()`. Standing
    that up requires a Django model + DB connection + a saved instance and a
    `.delete()` call — i.e. the F2P integration test itself
    (`test_fast_delete_instance_set_pk_none`), not a transliteration this gate
    can fuzz over >=1e5 inputs.
  * The changed op's content is the constant state assignment `pk := none`; its
    only R/I shadow is the constant `None`. Diffing `None == None` carries no
    information — there is no input-dependent computation to refute.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region is the deep state
mutation of a live ORM instance with no DB-free R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. Soundness of the
modeled mutation is carried instead by G-VERIFY (the spec provably forces
`pk = none` and `count = removed` on return) and G-DIFF (the prepatch, which
never assigns `pk`, fails exactly the `pk = none` clause). See mapping.md
section 4 and refinement.md section B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-11179 — the modeled do-block "
          "clears a live ORM instance's primary-key attribute "
          "(setattr(instance, model._meta.pk.attname, None)) after a real DB "
          "fast-delete; the changed op is a constant state mutation (pk:=none) "
          "with no DB-free, input-dependent R/I shadow. conf_skip=true. "
          "Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
