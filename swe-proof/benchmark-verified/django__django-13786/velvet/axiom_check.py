#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13786.

The bundle has NO consumed `axiom` / `@ContractOnly` contract. The changed
operation (the `options=` map a `CreateModel.reduce` emits when reducing against
an `AlterModelOptions`) is modeled DEEPLY by `mergeMaps`/`pruneFold`
(Solution.lean pure region). Map union (`{**a, **b}`) and key deletion
(`dict.pop(k, None)`) are language builtins, not repo callees, so they are not
axiomatized.

The ONE repository datum the spec references is the managed-key list bound to the
free input `trackedKeys`; in the real reduction that is the class constant
`AlterModelOptions.ALTER_OPTION_KEYS`. That is the single A-reference, and the
only thing G-AX is positioned to check soundly.

  (A-reference)  The pinned key list this bundle binds to `trackedKeys` is
      BYTE-EQUAL, in order, to the real `AlterModelOptions.ALTER_OPTION_KEYS`.
      This constant is UNCHANGED by the fix (the patch only adds the prune loop
      that *iterates* it), so it is the same on the base tree the orchestrator
      runs G-AX against and on the patched tree.

Why there is no second G-AX obligation here. G-AX runs against the REAL repo at
`base_commit` WITHOUT applying the gold patch (it validates references to
*unchanged* callees). The deeply-modeled operation — the `options=` value emitted
by `CreateModel.reduce(AlterModelOptions(...))` — is the FUNCTION UNDER CHANGE
itself: at base_commit it is the buggy pre-fix code (options not cleared), so it
deliberately disagrees with the deep model, which encodes the fixed behavior.
Validating the deep model against the real callee therefore belongs to G-CONF
(`conformance_check.py`), which runs against the PATCHED tree (`apply_gold=True`)
and confirms `pruneFold(mergeMaps(...))` == the patched `reduce` output over 10^5
fuzzed inputs. Re-checking it here against the unpatched callee would be both
unsound (it must fail by construction) and redundant with G-CONF.

Imports only the standard library and `django.db.migrations` (the module the gold
patch edits, used only to read the untouched `ALTER_OPTION_KEYS` constant). Exit 0
iff the A-reference holds.
"""
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={})

from django.db.migrations.operations.models import AlterModelOptions  # noqa: E402

# The key list this bundle binds to Solution.lean's `trackedKeys` input (the
# A-reference). Kept here verbatim; the check below asserts it == the real
# class constant, byte-for-byte and in order.
PINNED_TRACKED_KEYS = [
    "base_manager_name", "default_manager_name", "default_related_name",
    "get_latest_by", "managed", "ordering", "permissions",
    "default_permissions", "select_on_save", "verbose_name",
    "verbose_name_plural",
]


def main():
    # A-reference: the pinned key list == the real class constant, in order.
    real_keys = list(AlterModelOptions.ALTER_OPTION_KEYS)
    assert PINNED_TRACKED_KEYS == real_keys, (
        "trackedKeys A-reference unsound: pinned %r != real "
        "AlterModelOptions.ALTER_OPTION_KEYS %r" % (PINNED_TRACKED_KEYS, real_keys))

    print("G-AX OK: trackedKeys A-reference sound -- pinned key list == real "
          "AlterModelOptions.ALTER_OPTION_KEYS (%d keys, byte-equal in order). "
          "The deep model's equivalence to the patched reduce is validated by "
          "G-CONF (patched tree), not here." % (len(real_keys),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
