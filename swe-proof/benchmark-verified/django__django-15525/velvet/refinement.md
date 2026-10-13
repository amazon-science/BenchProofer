# refinement.md — django__django-15525

Correspondence between `Solution.lean`'s `naturalKeyForLoadedRecord` impl and
`patch.diff` (the gold patch, which associates the freshly built record with
the target database — `obj._state.db = db` — before deriving its natural key in
`build_instance`). `patch.diff` is the gold **verbatim** (applies at
base_commit, resolves — G-RESOLVE).

Each step is tagged **R** (type refinement), **A** (axiomatized/opaque callee —
**A-consumed** where the proof uses a contract, **A-reference** where a callee
is deferred to as an opaque/free value), or **I** (identical concrete op).
There are no consumed axioms in this bundle; the R/I legs are not differential-
tested (conf_skip=true, see mapping.md §4), so soundness rests on G-VERIFY +
G-DIFF + G-RESOLVE.

## A. The natural-key branch — `build_instance(Model, data, db)`

Gold hunk (context + the change):
```
-        natural_key = Model(**data).natural_key()
+        obj = Model(**data)
+        obj._state.db = db
+        natural_key = obj.natural_key()
```

| # | Solution.lean impl op (`naturalKeyForLoadedRecord`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `targetDb : String` | `db` arg of `build_instance` | R | target database alias `str` ↔ `String` (mapping.md §2). |
| A2 | `require storeHandle = none` (entry handle of the fresh record) | `obj = Model(**data)` — a freshly built instance with `_state.db` at its default `None` | R | `Model(**data)` sets `_state = ModelState()` whose `db = None` (base.py:454,489); `None` ↔ `none` (mapping.md §2). The fresh-record construction is unchanged; it supplies the precondition. |
| A3 | `storeHandle := some targetDb` (assign the mutable handle) | `obj._state.db = db` | **I** | identical concrete op: the CHANGED op (the patch's central added line), modeled deeply as the state assignment that associates the record with the target DB. `obj._state.db = db` ↔ `storeHandle := some targetDb`; `db` ↔ `some targetDb` (mapping.md §2). |
| A4 | `let key := naturalKeyVia storeHandle` — derive the key from the **updated** handle | `natural_key = obj.natural_key()` (evaluated after the assignment) | **A-reference** (opaque) | the UNCHANGED derivation `obj.natural_key()` deferred to as the opaque `naturalKeyVia`, applied to the post-assignment handle. Its reference-following (`self.author.natural_key()`) routes its DB read through `obj._state.db` (related_descriptors.py:121,164-168 → `db_manager(hints={instance: obj})`), so the result is a function of the handle. Because the handle is now `some targetDb`, the derivation is routed to the target DB. No contract is asserted about its value (refined, never replaced); nothing for G-AX. |
| A5 | `return key` | `natural_key` bound, used next as `get_by_natural_key(*natural_key)` | **I** | the derived key is returned/used unchanged; the model observes the derivation's value as the returned `key`. |

The ORDER is the soundness crux: A3 (set handle) precedes A4 (derive key), so
the key is `naturalKeyVia (some targetDb)`. The spec pins `key = naturalKeyVia
(some targetDb)` (the *post*-assignment handle), which is dischargeable only by
deriving the key AFTER the assignment. No consumed axiom; no kind-3
(inexpressible-changed-op) step — the changed op (A3) is the state assignment,
modeled deeply and tagged **I**; the deferred derivation (A4) is an opaque
A-reference whose argument the operation controls.

## B. verify(Solution) ⇒ resolved; prepatch fails

`naturalKeyForLoadedRecord` verifies only if both `storeHandle = some targetDb`
(forced by A3) and `key = naturalKeyVia (some targetDb)` (forced by A3 then A4,
i.e. derive-after-associate) hold. By R (mapping.md §2) the verified post-state
equals: `obj._state.db == db` after the assignment, and `natural_key ==
obj.natural_key()` evaluated with that handle in place — exactly the gold patch.
The F2P test `NaturalKeyFixtureOnOtherDatabaseTests.test_natural_key_dependencies`
loads a fixture into the `"other"` database where the related row (the FK
`author`) exists; with the handle set, `natural_key()`'s `self.author` lookup
routes to `"other"` and succeeds. Both clauses are pinned by the spec.

The prepatch (`Solution_prepatch.lean`) derives the key from the store handle
while it is still unset (`naturalKeyVia storeHandle` with `storeHandle = none`)
and never assigns it — the freshly built record was never associated with the
target DB before deriving the key. `prove_correct` fails on exactly the
discriminating clauses:
```
case «ensures_1: key = naturalKeyVia (some targetDb)»
⊢ naturalKeyVia storeHandleOld = naturalKeyVia (some targetDb)   -- unprovable: derived at none, not (some targetDb)

case «ensures_2: storeHandle = some targetDb»
⊢ storeHandleOld = some targetDb                                 -- unprovable: handle left unset
```
This is the precise bug the issue describes: on a non-default database, the
freshly built record's `natural_key()` follows its foreign key against the
*default* database (the unset handle), the related row is absent there, and the
load fails. G-DIFF passes.

## C. G-CONF / G-AX

- **G-CONF: conf_skip=true.** The impl's executable content is the deep state
  association `storeHandle := some targetDb` followed by a derivation whose
  observable value is a real DB read routed by the handle. There is no DB-free,
  input-dependent R/I shadow to differential-test (mapping.md §4); the oracle is
  the F2P integration test. `conformance_check.py` is a `status=skip` stub.
- **G-AX: skip.** No consumed axioms and no asserted callee contract. The
  unchanged callee `obj.natural_key()` is the opaque `naturalKeyVia` with no
  asserted `ensures`, so there is nothing to validate against the real routine
  — no `axiom_check.py` (django-12276 precedent).
