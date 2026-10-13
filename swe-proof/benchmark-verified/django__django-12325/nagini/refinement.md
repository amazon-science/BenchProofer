# refinement.md — django__django-12325

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_inheritance_links` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — none here),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The recording site — `ModelBase.__new__` (`django/db/models/base.py:204-207`)

Gold hunk:
```
  for field in base._meta.local_fields:
-     if isinstance(field, OneToOneField):
+     if isinstance(field, OneToOneField) and field.remote_field.parent_link:
          related = resolve_relation(new_class, field.remote_field.model)
          parent_links[make_model_tuple(related)] = field
```

| # | model.py impl op (`select_inheritance_links`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `while i < len(is_parent_link): ... i = i + 1` over scan positions | `for field in base._meta.local_fields:` (the `OneToOneField` subset) | R | the scanned one-to-one relations ↔ the parallel lists indexed by position (mapping.md §2); the unchanged `isinstance(field, OneToOneField)` gate selects the same subset on both sides, so it is absorbed into "what the lists enumerate". |
| A2 | `if is_parent_link[i]:` | the added conjunct `... and field.remote_field.parent_link` (the gates the recording) | I (over the refined `bool`) | `is_parent_link[i]` ↔ `field.remote_field.parent_link` is the identity on the `bool` carrier (mapping.md §2). This is THE changed operation: the new eligibility filter. |
| A3 | `result[related_key[i]] = i` | `parent_links[make_model_tuple(resolve_relation(new_class, field.remote_field.model))] = field` | R | dict assignment, last-writer-wins per key, identical in both worlds. The key `related_key[i]` ↔ the derived `make_model_tuple(resolve_relation(...))` token (R; the derivation is UNCHANGED by the patch). The value `i` ↔ `field`: the position uniquely identifies the relation object and keeps its `parent_link` designation observable (mapping.md §2). Post-condition clause (4) (`Result()[related_key[i]] >= i` for every parent-link `i`) pins last-writer-wins in the SPEC, so a rival that keeps the FIRST parent link per key (satisfying clauses (1)+(3) but recording a different relation object than the repo) does not verify. |
| A4 | `return result` | the `parent_links` dict left for `__new__` to store and `_prepare` to consume | R | the model returns the record `_prepare` later promotes from. |

The discriminating content of the change — record a one-to-one relation ONLY
when it is a designated parent link — lives in step A2 (`if is_parent_link[i]`
⇔ the `and field.remote_field.parent_link` conjunct). The pre-patch loop omits
the filter and records every relation (last-writer-wins); `model_prepatch.py`
reproduces that (`result[related_key[i]] = i` unconditionally) and **fails** the
post-condition clause (1) `is_parent_link[Result()[k]]`, which is exactly the
spec sensing the change (G-DIFF; the prepatch fails on that `Forall` at
`model_prepatch.py:93-99`).

Clause (4) (`Result()[related_key[i]] >= i` for every parent-link position
`i`) additionally pins WHICH relation is recorded when several designated
parent links target the same related model: the LAST-scanned one, exactly the
repo's dict last-writer-wins (step A3). Without it a first-writer-wins rival
(`if is_parent_link[i] and related_key[i] not in result:`) satisfies clauses
(1) and (3) yet records a different relation object than the patched repo —
the spec-too-weak finding the G-PANEL-1 audit produced; clause (4) rejects it
(properties.py case `weak-first-writer-wins`).

## B. The guard-removal site — `Options._prepare` (`django/db/models/options.py:254-257`)

Gold hunk (plus the dropped `ImproperlyConfigured` import at `options.py:8`):
```
  field.primary_key = True
  self.setup_pk(field)
- if not field.remote_field.parent_link:
-     raise ImproperlyConfigured(
-         'Add parent_link=True to %s.' % field,
-     )
```

This hunk **removes a guard that the model post-condition proves is never
taken**, so it is not a separate modeled behaviour — it is a consequence of
site A's clause (1). There is therefore no separate `model_prepatch_<k>` and no
extra modeled function for it.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | post-condition clause (1): `Forall k: k in Result() ==> is_parent_link[Result()[k]]` | the deletion of `if not field.remote_field.parent_link: raise ImproperlyConfigured(...)` | I (proof-level) | `_prepare` promotes `field = next(iter(self.parents.values()))` — a VALUE of the `parent_links` record. By clause (1) every recorded relation is a parent link, so `field.remote_field.parent_link` is True for the promoted field, so `not field.remote_field.parent_link` is False, so the guard never raises. Deleting an unreachable raise preserves behaviour. The guard's predicate is the exact negation of clause (1) (mapping.md §3). |
| B2 | (the dropped import) | `-from django.core.exceptions import ... ImproperlyConfigured` → `from django.core.exceptions import FieldDoesNotExist` | I | removing an import whose only use (B1) is removed is a no-op on behaviour. |

The F2P tests exercise exactly this coupling:
  * `test_onetoone_with_parent_model`: a child with a non-parent-link
    `OneToOneField` to its parent (and the implicit parent link) now records
    only the parent link (clause (1)) instead of the ordinary relation, so
    `_prepare` promotes the genuine parent link and the guard never fires —
    `check()` returns `[]` (pre-patch: `ImproperlyConfigured`).
  * `test_clash_parent_link`: with the filter in place the implicit parent link
    is the recorded one, and the extra ordinary `OneToOneField` produces the
    expected reverse-accessor/query-name clash errors (E304/E305) rather than
    the spurious configuration error.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or proof-level (B1/B2). The one operation that
genuinely *changed* — the eligibility filter on the recording loop — is modeled
**deeply** as the concrete branch `if is_parent_link[i]` (step A2), not hidden
behind an axiom. There is **no axiomatized callee**: the callees the loop
invokes (`isinstance`, `resolve_relation`, `make_model_tuple`) are UNCHANGED by
the patch and absorbed into the int/bool carrier as type refinements (mapping.md
§2), never contracted inside a `Requires`/`Ensures`. Hence no A-consumed and no
A-reference rows, and `axiom_check.py`/G-AX is vacuous for this bundle.

## D. verify(model) ⇒ resolved

`select_inheritance_links` verifies only if its output records every relation as a
parent link (clause (1)), never loses a parent link (clause (3)), and records
the LAST parent-link position per related model (clause (4), last-writer-wins
— pinning which relation object `_prepare` later promotes). By R
(scan-position ↔ field, `bool`/key identity, dict last-writer-wins) the verified
loop equals the patched `__new__` recording loop on the scanned relations; by
B1 clause (1) makes the deleted `_prepare` guard provably unreachable, so the
guard removal is behaviour-preserving. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The only trust point of PLAN §1.1 that applies is
refinement fidelity (this document, G-EQ); there is no axiom, so axiom soundness
(G-AX) is vacuous.
