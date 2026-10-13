# refinement.md — django__django-15629

Operation-by-operation correspondence between `Solution.lean`'s impl regions and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. There are **no A-tagged ops**: no
consumed axioms and no deep-model references (mapping.md §1). Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the harness backend (sqlite3), so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. `ForeignKey.db_parameters` — the FK collation propagation (`related.py:1182`)

Gold hunk (site `django/db/models/fields/related.py`):
```
- return {"type": self.db_type(connection), "check": self.db_check(connection)}
+ target_db_parameters = self.target_field.db_parameters(connection)
+ return {
+     "type": self.db_type(connection),
+     "check": self.db_check(connection),
+     "collation": target_db_parameters.get("collation"),
+ }
```

| # | Solution.lean impl op (`foreignReferenceColumnDesc`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `refType : String` | `self.db_type(connection)` | R | the FK's own storage type, UNCHANGED by the patch; abstracted as an input (mapping.md §2). |
| A2 | param `refCheck : Option String` | `self.db_check(connection)` | R | the FK's own check, UNCHANGED; abstracted as an input (`None ↔ none`). |
| A3 | param `targetCollation : Option String` | `target_db_parameters.get("collation")` where `target_db_parameters = self.target_field.db_parameters(connection)` | R | the referenced column's collation, read from the target field's descriptor; abstracted as an input. `get` ↔ `Option` (`None`/absent ↔ `none`). |
| A4 | `return { sqlType := refType, check := refCheck, collation := targetCollation }` | the post-patch dict literal | I | identical record construction: each key is placed verbatim. The collation key is set to the target's collation — the single new behaviour. |

Discriminating content: the reported collation EQUALS `targetCollation`
(`ensures out.collation = targetCollation`). The pre-patch returned no collation
key at all (≡ `none`); `Solution_prepatch.lean` reproduces that
(`collation := none`) and **fails** `out = referencingColumnDesc …` /
`out.collation = targetCollation` whenever the target carries a collation
(G-DIFF). G-CONF site 1 runs the REAL patched `ForeignKey.db_parameters` and
confirms `out.collation` equals the target's collation.

## B. sqlite3 `_alter_field` rebuild predicate (`sqlite3/schema.py:458`)

Gold hunk (site `django/db/backends/sqlite3/schema.py`):
```
- if new_field.unique and old_type != new_type:
+ old_collation = old_db_params.get("collation")
+ new_collation = new_db_params.get("collation")
+ if new_field.unique and (
+     old_type != new_type or old_collation != new_collation
+ ):
```

| # | Solution.lean impl op (`shouldReissueReferences`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `targetUnique : Bool` | `new_field.unique` | R | identity (mapping.md §2): references may target the altered column iff it is unique. |
| B2 | param `oldType`/`newType : String` | `old_type`/`new_type` | R | identity on the rendered storage type string. |
| B3 | param `oldCollation`/`newCollation : Option String` | `old_db_params.get("collation")`/`new_db_params.get("collation")` | R | the altered column's collation before/after; `get` ↔ `Option`. |
| B4 | `return targetUnique && ((oldType != newType) || (oldCollation != newCollation))` | `new_field.unique and (old_type != new_type or old_collation != new_collation)` | I | identical boolean decision: `and`/`or`/`!=` map verbatim to `&&`/`\|\|`/`!=`. |

Discriminating content: reissue is forced when ONLY the collation differs
(`(targetUnique ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true`).
The pre-patch triggered only on a type difference;
`Solution_prepatch_2.lean` reproduces that (`targetUnique && (oldType != newType)`)
and **fails** the collation-only clause (G-DIFF). G-CONF site 2 diffs the R/I
shadow against the patched predicate's literal decision over ≥10⁵ inputs.

## C. No kind-3 (inexpressible-changed-op) steps; no A-tagged ops

Every step is R or I. Both changed operations are pure data-flow — a record
construction (A) and a boolean decision (B) — fully expressible in Velvet; there
is no operation modeled behind an axiom and no deep-model reference. The values
the operations consume (the FK's own type/check, the target's collation, the
before/after descriptors) are UNCHANGED by the patch and are abstracted as
inputs, so they need no axiom.

## D. Inert sites (not modeled — mapping.md §3.3/§3.4)

Two gold hunks do not run on the harness backend (sqlite3): the base
`_alter_field` collation handling (`base/schema.py`) is dead because sqlite fully
overrides `_alter_field`, and the `oracle/features.py` hunk is test-skip
bookkeeping for an unused backend. They are the MySQL/Postgres/Oracle face of
the same fix and carry no sqlite-observable behaviour, so omitting them does not
weaken `verify ⟹ resolved` on this instance.

## E. verify(Solution) ⇒ resolved

`foreignReferenceColumnDesc` verifies only if the reported collation equals the
referenced column's collation (A4); `shouldReissueReferences` verifies only if a
collation-only change forces reissue (B4). By R (the descriptor/collation/bool
bijections, mapping.md §2) these are exactly the patched
`ForeignKey.db_parameters` and the patched sqlite rebuild predicate. Together
they are the two sqlite-observable fix points: the FK column adopts the PK's
collation (so the creation test sees `COLLATE` on `pony_id`), and an
alter-collation forces the referencing tables to be remade (so the alter test
sees the propagated collation on `rider`/`stable_ponies`). By G-CONF the R/I
transliterations agree with `patch.diff` on ≥10⁵ inputs (and disagree on the
unpatched tree). Therefore a model satisfying this spec, refined by the map
above, resolves (G-RESOLVE). The only trust point is refinement fidelity (this
doc + G-CONF + G-EQ); there are no axioms (G-AX is vacuous).
