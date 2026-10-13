# refinement.md — django__django-12209

Maps every op in `implementation_saveDecision` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op).

| # | Lean op (`implementation_saveDecision`) | Python (`_save_table`, base.py @ base_commit + patch) | tag | note |
|---|---|---|---|---|
| 1 | `let mut forced := forceFresh` | `force_insert` is the live value entering the decision block (`force_insert` param) | I | seed the mutable verdict with the caller-supplied flag |
| 2 | `if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then forced := true` | the gold block `if (not raw and not force_insert and self._state.adding and self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED): force_insert = True` | I (boolean refinement, R) | `verbatimLoad↔raw`, `forced↔force_insert`, `isNew↔self._state.adding`, `keyHasDefault↔(pk.default truthy ∧ ≠ NOT_PROVIDED)`. The patched conjunct `not raw` is `!verbatimLoad`. |
| 3 | `let attemptsUpdate := keySet && !forced` | the guard `if pk_set and not force_insert:` gating the `_do_update` attempt | I (R) | `keySet↔pk_set`; uses `force_insert` AFTER the block |
| 4 | `return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }` | the post-block state of `force_insert` and the update-attempt guard | I | both observable decision components returned |

All ops are I / boolean-R. There is **no A-tagged op** — no callee is
axiomatized and nothing is deeply-modeled-against-a-real-callee, because the
five inputs are exactly the booleans the real method reads, and the decision is
the gold boolean expression transliterated. The two-part `keyHasDefault`
conjunction (Python `pk.default` truthy ∧ `≠ NOT_PROVIDED`) is collapsed to one
input boolean (R) — its computation is unchanged by the patch and outside the
modeled boundary.

G-CONF mechanically refutes the I/R legs (exhaustive 32-point + ≥1e5 fuzz
differential vs the gold boolean oracle). G-AX is a skip stub (no consumed
callee axiom).

## No changed-inexpressible op
Every operation the patch touches is a boolean conjunction directly expressible
in Lean. Nothing required deep modeling beyond boolean algebra.
