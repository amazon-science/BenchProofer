#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16256 — SKIPPED.

WHY conf_skip=true:

The three modeled `do` blocks (`aCreate`, `aGetOrCreate`, `aUpdateOrCreate`)
are the related-manager async members the gold patch adds, e.g.

    async def acreate(self, **kwargs):
        return await sync_to_async(self.create)(**kwargs)

(`related_descriptors.py` / `contenttypes/fields.py`). The CHANGED behaviour the
spec pins is *which* synchronous member the coroutine runs: the gold patch routes
it to the RELATED MANAGER's own `create` / `get_or_create` / `update_or_create`,
which establish the parent↔child relation (set the FK, insert the m2m through-row,
or set the content-type + object-id fields), instead of the inherited `QuerySet`
coroutine, which creates the object but never links it to the parent.

That behaviour is NOT reproducible as a pure, DB-free R/I shadow this gate can
fuzz over >=1e5 inputs:

  * The only observable the fix produces is a SIDE EFFECT on a live backend: the
    new/updated object becomes reachable through the parent's related manager
    (the F2P tests assert `await mgr.acount() == 1`, `await mgr.aget()` returns
    it, `new.simple == self.s1`). It materializes only after the coroutine
    actually runs the related manager's sync member, which opens a database
    connection, runs the INSERT/UPDATE, and writes the relation row — inside a
    running event loop driven by `sync_to_async`. Reproducing it requires
    standing up a real database, model instances, an event loop and the related
    descriptors — i.e. the F2P integration tests themselves
    (`tests/async/test_async_related_managers.py`), not a transliteration this
    gate can fuzz.
  * The impl region's only non-trivial op is the relation-establishing step
    (`related := related ++ [newObj]`), which is the A-reference modeling the
    awaited `sync_to_async(self.<member>)(...)` call (mapping.md §3.1). There is
    no DB-free, input-dependent R/I computation on the inputs to differentially
    refute: the discriminating fact is WHICH callable the coroutine awaits
    (related-manager member vs inherited QuerySet coroutine), exercised only by
    the live ORM + event-loop machinery — which is covered by axiom_check.py
    (G-AX).

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the impl region's observable is a live
DB relation side effect with no DB-free, input-dependent R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. The pinned seed 16256
(mapping.md §4) is recorded for parity but unused. Soundness of the modeled
relation effect is carried instead by G-VERIFY (the spec provably forces
`related = relatedOld ++ [newObj]` for a fresh object), G-DIFF (each prepatch,
which omits the link, fails exactly that clause), and G-AX (the real
`sync_to_async` bridge preserves both the return value and the relation side
effect of the synchronous member it runs). See mapping.md §3/§4 and
refinement.md §C.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-16256 — the modeled do-blocks "
          "add related-manager async members that await the related manager's "
          "own sync create/get_or_create/update_or_create (which link the "
          "object to the parent) via sync_to_async, instead of the inherited "
          "QuerySet coroutine (which never links). The only observable is a "
          "live DB relation side effect with no DB-free, input-dependent R/I "
          "shadow. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + "
          "G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
