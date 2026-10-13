# refinement.md — django__django-12209

The operation-by-operation correspondence between `model.py`'s implementation
(the `store_single_table` impl region, the `shortcut_engaged`/`forces_insert`
pure spec, and the `update_matched_row` axiom) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee
— split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The save-decision site — `Model._save_table()` (`django/db/models/base.py:850-857`)

Gold hunk (the one change, at `base.py:852`):
```
         updated = False
         # Skip an UPDATE when adding an instance and primary key has a default.
         if (
+            not raw and
             not force_insert and
             self._state.adding and
             self._meta.pk.default and
             self._meta.pk.default is not NOT_PROVIDED
         ):
             force_insert = True
```

The guarded block re-assigns the local `force_insert = True`, engaging the
straight-to-insertion short-cut (it makes the subsequent
`if pk_set and not force_insert:` UPDATE attempt be skipped). The bug: the
short-cut also engaged in unprocessed-data mode (`raw=True`), the mode the
(de)serialisation machinery uses, so re-saving an instance with an explicit,
already-stored identifier did a blind INSERT instead of an UPDATE. The fix adds
the leading `not raw and` conjunct, suppressing the short-cut in that mode.

| # | model.py impl op (`store_single_table`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameters `pk_explicit, force_insert, pk_set, adding, pk_has_default : bool` | `self._save_table(..., raw, ..., force_insert, ...)`, the locals `pk_set` (`base.py:846`), `self._state.adding` (`base.py:853`), and `self._meta.pk.default and ... is not NOT_PROVIDED` (`base.py:854-855`) | R | the five booleans that feed the changed decision modelled as plain `bool`; model `pk_explicit` ↔ repo `raw` (mapping.md §1–2); every other field/operation of `_save_table` is untouched by the change and abstracted (mapping.md §2). |
| A2 | `force_insert_eff = force_insert` then `if (not pk_explicit) and (not force_insert) and adding and pk_has_default: force_insert_eff = True` | the `if ( not raw and not force_insert and self._state.adding and self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED ): force_insert = True` block (`base.py:851-857`) | **I** (under R on the operands) | the FIX. Identical concrete boolean decision — the same four-conjunct guard with the **same added conjunct** as the patch (model `not pk_explicit` ↔ repo `not raw`) — re-assigning the effective force-insert flag. The two `self._meta.pk.default …` operands are the single `pk_has_default` (R, mapping.md §2); `self._state.adding ↔ adding`. The model uses a fresh local `force_insert_eff` only because the parameter `force_insert` is read again in the spec; this is the same value the patch leaves in the re-assigned `force_insert`. |
| A3 | `updated = False; if pk_set and not force_insert_eff: updated = update_matched_row()` | `updated = False` (`base.py:849`); `if pk_set and not force_insert: ... updated = self._do_update(base_qs, using, pk_val, values, update_fields, forced_update)` (`base.py:859-865`) | A-consumed | the unchanged UPDATE primitive is axiomatized: `update_matched_row()` is the bool `_do_update` reports — True iff a stored row matched the identifier (mapping.md §3.1). The proof consumes it as the value returned along the update path. The intervening `base_qs`/`values`/`forced_update` setup and the `force_update`/`update_fields` "did not affect any rows" raises are unchanged bookkeeping that the changed decision does not observe. |
| A4 | `return updated` | `return updated` (`base.py:890`, after the `if not updated: ... _do_insert(...)` fallback) | **I** (under R on the return shape) | identical return of the same `updated` bool. The `if not updated: … _do_insert(…)` INSERT fallback is unchanged: it runs in BOTH the short-cut and the non-short-cut case and does not alter `updated`; it is abstracted as it carries no behaviour the changed decision observes (the F2P observes whether the UPDATE path was taken, surfaced as `updated`). |

The discriminating content of the change — the added conjunct — lives in
`shortcut_engaged`'s leading `not pk_explicit` (model) ⇔ the added `not raw and`
line of the gold `if` (real). The pre-patch guard omitted it;
`model_prepatch.py` reproduces that (drops `(not pk_explicit) and` from the impl `if`)
and **fails** the postcondition
`Result() == pk_set and not forces_insert(...) and update_matched_row()`,
which is exactly the spec sensing the change (G-DIFF, §B).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its impl guard is
`if (not force_insert) and adding and pk_has_default:` — the pre-patch guard
**without** the `not pk_explicit` conjunct (model symbol; repo `not raw`,
mirroring `base.py:851-856` pre-patch). With the byte-identical frozen spec it
**fails** verification on the postcondition
`Ensures(Result() == (pk_set and not forces_insert(pk_explicit, force_insert, adding, pk_has_default) and update_matched_row()))`
(`model_prepatch.py:84-87` — *Postcondition … might not hold*). The witness is
exactly the tested case: `pk_explicit=True, force_insert=False, pk_set=True,
adding=True, pk_has_default=True` (and `update_matched_row()` True, i.e. the
row already exists). There `forces_insert(...)` is False (the short-cut is
suppressed for a caller-supplied identifier), so the spec requires
`Result() == update_matched_row() == True` — an UPDATE; but the pre-patch impl
sets the short-cut and returns `False` (a blind INSERT). That is precisely the
regression the serializer re-save tests (`UUIDDefaultData` round-trip, raw save
of an explicit, pre-existing UUID primary key) observe: the second save must
UPDATE, not re-INSERT. The spec is therefore strong enough that no
implementation omitting the conjunct (`not pk_explicit` / repo `not raw`) can
verify (spec sees the bug).

The companion clause
`Ensures(Implies(pk_explicit and pk_set and not force_insert, Result() == update_matched_row()))`
states the same desired behaviour positively: when the identifier was
caller-supplied, an identifier-bearing, non-force-inserted instance is offered
to the update primitive and the routine returns its outcome — pinning that the
update path is reached, not bypassed.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — adding the conjunct (model `not pk_explicit` / repo `not raw`) to
the short-cut guard — is an **I** step (the very same boolean decision, only the
rich `self`-field operands refined to plain `bool` by R, model `pk_explicit` ↔
repo `raw`). There is no deep model and therefore **no
A-reference** here. The only consumed axiom, `update_matched_row`
(**A-consumed**, step A3), covers an **unchanged** callee (`Model._do_update`)
that the update path invokes; G-AX validates it against the real callee. We
never axiomatize the function under change (`_save_table` itself is modelled,
its changed decision spelled out in the impl).

## D. verify(model) ⇒ resolved

`store_single_table` verifies only if (A2) its effective force-insert decision
is exactly `force_insert or shortcut_engaged(pk_explicit, …)` — i.e. the
short-cut is suppressed when `pk_explicit` (repo `raw`) — and (A3/A4) it returns
`pk_set and not (that decision)
and update_matched_row()`. By R (the `self`-fields and the doubled
`pk.default` operand ↔ the five booleans; `_do_update`'s bool ↔
`update_matched_row()`; the unchanged INSERT fallback abstracted) and the
single **I** fix step, the verified path equals the gold guard
`if not raw and not force_insert and self._state.adding and
self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED:
force_insert = True` followed by the unchanged `if pk_set and not force_insert:
… _do_update(…)` on the tested inputs. By G-AX the real `_do_update` meets the
`update_matched_row` axiom it stands in for (A-consumed) — returning True for an
already-stored identifier — and the patched guard routes control as specified.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
