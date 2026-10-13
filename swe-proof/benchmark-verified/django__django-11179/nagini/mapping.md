# mapping.md — django__django-11179

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 19fc6376ce67d01ca37a91ef2f55ef769f50513a`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/db/models/deletion.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `remove_single_independent(instance, using)` | the optimized single-object branch of `Collector.delete(self)` — `django/db/models/deletion.py:274-280` (the `if len(self.data) == 1 and len(instances) == 1:` block and its `if self.can_fast_delete(instance):` body) | the modeled changed function (the fast single-object removal path) |
| `PersistentObject` / `instance.pk` | the model **instance** object `instance` and its primary-key attribute reached by `model._meta.pk.attname` (the attribute `setattr`/`getattr` named at `deletion.py:279,280` and the patched line) | the in-memory object whose primary key the fix clears |
| `remove_rows(db, identifier)` *(axiom — A-consumed, effectful; the ONLY model of this callee)* | `sql.DeleteQuery(model).delete_batch([instance.pk], self.using)` → the callee as an **invocation**: it issues the SQL and returns the count | unchanged community callee: the database row-removal primitive. One invocation issues exactly ONE row-removal statement (a one-element `pk_list` makes `delete_batch`'s `range(0, 1, GET_ITERATOR_CHUNK_SIZE)` loop run once, so one `do_query`), which is why it **consumes** `RemovalBudget(LEDGER)` and nothing mints another; it targets the identifier it was handed and reports a non-negative row count, which is why being answered yields `CarriedOutRemoval(db, identifier, Result())` — the receipt naming that handle, that identifier and the count *that statement* returned. There is deliberately **no pure twin** of this callee, and now no readable tally either: an effect-free function (or a free read) returning the same row count would model a zero-cost operation that in reality issues SQL, so every model-side statement-count guarantee would be unsound for impls that used it |
| `RemovalBudget(LEDGER)` — an **abstract** (`@ContractOnly @Predicate`, bodyless) ghost resource, HELD not read | the branch's *entitlement* to issue exactly one row-removal statement against the stored data — the cost `assertNumQueries(1)` around a fast-deletable `delete()` measures. Its real counterpart is not a value anywhere in the process; it is the budget the test asserts | the cost, carried as a single-use permission rather than as a tally. Drawn against the module-wide `LEDGER` because every alias/handle reaches the same stored data: a `DELETE` issued through a connection of the branch's own making removes rows and costs a statement just the same, and a *per-handle* tally is structurally blind to it. Bodyless is load-bearing twice: an impl cannot `Fold` one into existence to buy a second statement (that fails at translation, `abstract.predicate.fold`), and there is nothing inside it to inspect, so holding it cannot tell an impl anything about what the store has done — which is what keeps it a legitimately free thing to hold, unlike a readable counter |
| `CarriedOutRemoval(db, identifier, count)` / `RefusedRemoval(db, identifier)` — **abstract** (`@ContractOnly @Predicate`, bodyless) ghost receipts, minted only by the primitive being answered | the two ways the real statement can come back: `do_query`'s `cursor.rowcount` reaching `deletion.py:280` as `count` (carried out), versus the `IntegrityError` propagating out of `cursor.execute` (refused). A receipt is the *fact that this branch issued this statement and got this answer* — the thing `execute_wrapper` observes from outside | the provenance, carried forward out of a statement actually issued rather than read back off a record. Holding `CarriedOutRemoval(db, Old(instance.pk), Result())` witnesses in one fact that a statement was issued, that it targeted the stored identifier, that the surfaced count is the count *that statement itself* reported, and that the store applied it. Bodyless means an impl can neither forge one nor alter the handle, identifier or count on one, so the count cannot be re-derived from anything else and still discharge the clause |
| `db` (`Database`, with `db.removal_statements`, `db.last_removal_target`, `db.last_removal_report`, `db.completed_removals`) | `self.using` (the database alias) *and* the **store's own** record of the removal: how many row-removal statements the connection received, which identifier the last one was parameterized with, the row count it reported, and how many of them the store actually carried out. `conformance_check.py` / `axiom_check.py` obtain these by wrapping the connection from OUTSIDE the branch (`execute_wrapper`) | the handle the removal runs against. The alias itself is an opaque tag the modeled behaviour never inspects. **The record is bound to what an outside observer of the connection measures, and the modeled path holds NO permission on any part of it — not even read.** That is the faithful binding: the fast branch at `deletion.py:274-280` has no such counter in hand, so the only way for it to learn any part of the record is to issue a `SELECT` and ask the store. A model that handed it over at `1/2` (readable) priced that read at zero, and impls that consulted it verified while their faithful refinement pays a real query — 2 statements where `test_do_nothing_qscount` asserts 1. The fields remain on the carrier because the satellite checkers ground the axiom against them from the outside; they are simply not the path's to see |
| the store's refusal, as a fact about a statement already answered | a statement is refused when a live row's `FOREIGN KEY` references the targeted row with the database's constraint enforced (`PRAGMA foreign_keys=1`, which Django's sqlite3 backend sets); it is *not* "a dependent row exists", since the same reference declared `db_constraint=False` leaves the removal un-refused, which `axiom_check.py` section (c.3) measures | modelled as the **receipt the answer produces** (`RefusedRemoval` vs `CarriedOutRemoval`), never as a pre-state predicate. Nothing the path holds says how a statement not yet issued will be answered, which mirrors reality: the only way to find out is to ask. This is the same reason the record above is unreadable — a readable "will it refuse" fact is exactly the zero-cost oracle whose real form costs a query |
| `RemovalRefused` (the exception the modeled path may end with) | `django.db.utils.IntegrityError('FOREIGN KEY constraint failed')`, raised out of `do_query`'s `cursor.execute` (`django/db/models/sql/subqueries.py:21-25` → `django/db/backends/sqlite3/base.py:387-391`) and propagated through `Collector.delete`'s fast branch (`deletion.py:274-280`) unhandled — there is no `try` anywhere on that path | the outcome the store forces. The real branch has exactly two ends: the `return count, {label: count}` at `deletion.py:280` and this propagating `IntegrityError`. `axiom_check.py` section (c.1) asserts the class of the real exception, so this binding is measured rather than asserted |
| `LEDGER` (`RemovalLedger`, with `LEDGER.total_removal_statements`) — the single module-wide ledger | the row-removal statements the database received **in total**, counted across every connection rather than against one alias — the quantity the suite's `assertNumQueries(1)` around a fast-deletable `delete()` actually observes | the total cost of a removal, and the quantity the entitlement is drawn against. There is exactly ONE ledger because every alias/handle reaches the same stored data: a `DELETE` issued through any connection removes rows and costs a statement, so the total is the cost the data really paid. It has to be the *total* and not a per-handle tally because a per-handle tally is structurally blind to a statement that is not on that handle — a branch can keep `self.using`'s tally at one while issuing a second `DELETE` through a connection of its own making, and no postcondition quantified over `db` can see it. Like the handle's record, the total is the store's and the modeled path holds **no permission on it at all**: it is the anchor `RemovalBudget(LEDGER)` names, not a number the path may read. The gold branch touches only the handle it was given and issues exactly one statement, so it needs exactly the one entitlement and never needs to consult the total |
| `Result()` (the `int` returned) | `count` in `return count, {model._meta.label: count}` (`deletion.py:280`) | the surfaced deleted-row count |

The gold patch (the one change, `deletion.py:280`) inserts, between the
`delete_batch` call and the `return`, the statement
`setattr(instance, model._meta.pk.attname, None)` — modelled by
`instance.pk = None`. Pre-patch, that statement is absent.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the model `instance` object | `PersistentObject` instance | a minimal class carrying only the one touched field |
| `getattr(instance, model._meta.pk.attname)` / `setattr(instance, model._meta.pk.attname, None)` — the primary-key attribute access via its dynamic name | the field `instance.pk` (`Optional[int]`) | the attribute named by `model._meta.pk.attname` IS the model's primary key; reading/writing it ↔ reading/writing `instance.pk`. A non-`None` stored pk ↔ `instance.pk is not None`; the cleared pk ↔ `instance.pk is None`. |
| the stored primary-key *value* (a database identifier) | `int` | the carrier of `[instance.pk]` passed to `delete_batch`; modelled as the scalar `identifier` |
| `self.using` (database alias string) + the DELETE statements issued against it | `Database` carrier with fields `removal_statements: int`, `last_removal_target: int`, `last_removal_report: int`, `completed_removals: int` — **none of them in the modeled path's permission set** | the alias is an opaque tag the modeled behaviour never inspects. The four fields are the image of what an outside observer of the connection measures (`execute_wrapper` in the satellites): `removal_statements` ↔ the number of row-removal statements the connection received, `last_removal_target` ↔ the identifier the most recent one was parameterized with, `last_removal_report` ↔ the row count it returned, `completed_removals` ↔ how many of them the store carried out. They exist so the satellite checkers can ground the axiom from outside, and the modeled path holds **no** permission on any of them. See §2.1: the reason is that these are not values the fast branch has, and a model that made them readable priced a real query at zero |
| the store's refusal of the `DELETE` — a live constrained `FOREIGN KEY` reference to the targeted row — and the `IntegrityError` it surfaces as | the `RefusedRemoval(db, identifier)` receipt (in place of `CarriedOutRemoval`) + the `RemovalRefused` exception | the receipt records the outcome *after* the statement was answered; the exception is that outcome reaching the caller. Carried as a receipt minted by the answer rather than as anything the path can consult beforehand, precisely so that nothing the path holds predicts the store's answer — an impl cannot learn the outcome without issuing the statement, which is what makes the exceptional exit unavailable to a path that never asked |
| `count, {model._meta.label: count}` (the `(int, dict)` return) | `int` (`Result()`) | only the `count` component is behaviourally tested (the deleted-row count surfaced to user code). The `{label: count}` dict literal is an identical construction over the same `count` (refinement.md, step I-ret); it carries no extra behaviour the F2P/P2P tests of this change observe. |

`model._meta.pk.attname` is a string-named attribute; Nagini bans dynamic
attribute access and `str` indexing, so the dynamic name is modelled as the
concrete field `pk`. This is sound because the patch's `setattr(...None)`
clears exactly that one primary-key attribute, and the test observes it via
`u.pk` (the same descriptor).

The identifier carrier is the **integer** primary key — the `AutoField` case the
F2P/P2P tests of this change exercise (`test_fast_delete_instance_set_pk_none`,
`test_do_nothing_qscount`) and the case `axiom_check.py` / `conformance_check.py`
drive. Its value range is the signed 64-bit window the store can represent
(§3.1). A model keyed by a non-integer pk (`UUIDField`, `CharField`) is a
different carrier and the modeled behaviour makes no claim about it; the branch
under change is indifferent to the pk's type (it hands `[instance.pk]` straight
to the primitive and clears the same attribute), so nothing about the fix is
hidden by modelling the integer case.

### 2.1 Why the store's record is UNREADABLE to the modeled path (the priced-read refinement)

This is the load-bearing modelling decision in the bundle, so it is recorded
separately with its repo grounding.

**The real branch holds no counter.** The modeled path is the optimized branch at
`django/db/models/deletion.py:274-280`. Read it: it has `self.data`, `instances`,
`model`, `instance` and `self.using` in scope, and it calls
`sql.DeleteQuery(model).delete_batch([instance.pk], self.using)`. There is no
value anywhere in that scope that says how many statements the connection has
received, which identifier the last one named, what it reported, or how many the
store carried out. Those quantities exist only in the database and in whatever an
observer has wrapped around the connection. `CaptureQueriesContext` /
`assertNumQueries` are exactly such an outside observer, and so are the
`execute_wrapper` hooks `conformance_check.py` and `axiom_check.py` use to ground
the axiom — all of them wrap the connection from OUTSIDE the branch.

**So a read of the record refines to a statement.** If the branch wanted any part
of that record it would have to ask the store, and asking is a query. That makes a
zero-cost model read unsound in the refining direction: it licenses an
implementation whose faithful form issues a `SELECT` before the `DELETE`.
`test_do_nothing_qscount` (`tests/delete/tests.py:85-93`) wraps `b.delete()` in
`assertNumQueries(1)` on a `Base` whose only referrer is a `DO_NOTHING` foreign
key with a real database constraint, so the object stays fast-deletable
(`can_fast_delete`, `deletion.py:145-155`, is true exactly when every referring FK
is `DO_NOTHING`) and the branch under change is the one entered. One extra read is
therefore 2 statements where 1 is asserted. This was not hypothetical: it is the
measured, recorded shape of the counterexamples this modelling closes — impls that
consulted the record verified against a spec that handed it over at `1/2`, and
their faithful patches passed the F2P test and failed exactly that P2P assertion.

**Hence: no permission, not read-only permission.** In Viper's discipline anything
a contract can name in a postcondition must be readable in the body, so a cost or
provenance clause stated as an *equation over a tally* forces the tally into the
implementation's read set, and the free read comes back with it. That is why cost
and provenance are carried as **abstract ghost resources** instead:
`RemovalBudget(LEDGER)` is a single-use entitlement (held, spent, never inspected —
being bodyless there is nothing in it to inspect) and
`CarriedOutRemoval` / `RefusedRemoval` are receipts minted only by the primitive
being answered. All three are `@ContractOnly @Predicate`, i.e. Viper predicates
with no body, so they can be neither folded into existence nor unfolded to look
inside; an attempt fails at translation (`abstract.predicate.fold`) rather than at
a clause. The facts the old equations carried are all still carried — one statement
against the handle, one in total across every handle, the stored identifier as
target, the count being that statement's own report, and the carried-out/refused
outcome being the store's to decide — but they now travel FORWARD out of a
statement actually issued, which is the only direction the real branch has them.

**What this does not claim.** The record's fields stay on the `Database` carrier
because the satellite checkers ground the axiom against them from the outside, and
their bindings in §1 are unchanged. The claim is only about who may see them: the
store's record is the store's, and the modeled path is given the entitlement and
the receipt instead.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `remove_rows` ↔ `DeleteQuery.delete_batch` (A-consumed)
**Callee:** `django.db.models.sql.subqueries.DeleteQuery.delete_batch(pk_list, using)`
(`django/db/models/sql/subqueries.py:27-42`). Source:

```python
def delete_batch(self, pk_list, using):
    # number of objects deleted
    num_deleted = 0
    field = self.get_meta().pk
    for offset in range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE):
        self.where = self.where_class()
        self.add_q(Q(**{field.attname + '__in': pk_list[offset:...]}))
        num_deleted += self.do_query(self.get_meta().db_table, self.where, using=using)
    return num_deleted
```

`num_deleted` is accumulated from `do_query`, which returns
`cursor.rowcount if cursor else 0` (`subqueries.py:21-25`) — always a
**non-negative integer** (the count of rows the DELETE removed; `0` when no row
matches). The primitive issues SQL against the database row only; it never
touches the in-memory Python `instance` object or its `pk` attribute.

**Domain of the axiom (`Requires(-(2 ** 63) <= identifier < 2 ** 63)`).** The
axiom's only exceptional case is `RemovalRefused` — the store refusing the
statement — so inside its domain the primitive must either report a count or
refuse, and any *other* way of failing would make the axiom unsound. It does not
report a count everywhere, and out here it does not refuse either: the
identifier reaches the backend as a real bind parameter
(`add_q(Q(**{field.attname + '__in': [...]}))` → `do_query` →
`SQLiteCursorWrapper.execute(query, params)`,
`django/db/backends/sqlite3/base.py:387-391`), and the driver cannot adapt a
value outside the signed 64-bit range — it raises
`OverflowError: Python int too large to convert to SQLite INTEGER`, so no count
is reported. Measured on the base_commit tree (`axiom_check.py` sections d/e):
`delete_batch([2**63 - 1])` and `delete_batch([-2**63])` return normally with one
statement and the DB's own count, while `2**63`, `2**63 + 1`, `2**64`, `2**70`,
`-2**63 - 1`, `-2**63 - 2` and `-2**70` all raise. The `Requires` is therefore
the primitive's real domain of definition, boundary-tight in both directions —
not one step narrower.

That restriction excludes **no reachable case** of the modeled behaviour, which
is a property of the domain rather than a demand on the removal path: the object
under removal is a *persistent* one, and no stored row can be keyed by an
out-of-range identifier in the first place. Measured (`axiom_check.py`
section f): `objects.create(pk=2**63 - 1)` and `objects.create(pk=-2**63)` store
and are found by `filter(pk=…)`, while `objects.create(pk=2**63)` and
`objects.create(pk=-2**63 - 1)` raise the *same* `OverflowError` on the INSERT.
So an object carrying an out-of-range identifier is one the store never held; the
F2P/P2P behaviour under specification (a saved dependency-free object being
deleted) lies wholly inside the stated domain. Both directions of this boundary
are asserted executably by G-AX, and the check is falsifiable in the honest
direction too: if the primitive ever returned a count for an out-of-range
identifier, `axiom_check.py` section e fails with "the Requires is then narrower
than the real domain and must be widened" (confirmed by control: moving one
in-range value into the out-of-range list makes G-AX exit 1).

The axiom encodes only the obligations the proof consumes:

* **cost, counted across every handle** — one invocation issues exactly one
  row-removal statement, so it **consumes** `RemovalBudget(LEDGER)` and nothing
  mints another. Grounded in the chunk loop above:
  `range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE)` runs once for a one-element
  `pk_list`, hence one `do_query`, hence one `DELETE`. The entitlement is drawn
  against the module-wide total rather than a per-handle tally because that
  `do_query` is one `DELETE` the database receives regardless of which alias
  `using` names: the primitive cannot issue a statement the total misses, which
  is exactly why the total is the sound place to state a cost budget — a
  per-handle tally is only the part of the cost that happened to be spent on the
  handle the caller named. Stating cost as a consumed entitlement rather than as
  an equation over a readable tally is the load-bearing choice: an equation
  requires the caller to hold the tally, and holding it is precisely what makes
  reading it free (see the note on unpriced reads below).
* **target and report, carried on the receipt** — being answered with a count
  yields `CarriedOutRemoval(db, identifier, Result())`. That the statement removes
  by the identifier it was handed is grounded in
  `self.add_q(Q(**{field.attname + '__in': pk_list[...]}))`: the `WHERE` is built
  from the given `pk_list` and nothing else. That the count is the row count that
  same statement produced, and is non-negative, is grounded in `num_deleted` being
  accumulated from `do_query`'s `cursor.rowcount if cursor else 0`. The receipt
  binds handle, identifier and count together in one bodyless resource the impl
  cannot mint or edit, so the count is available to the impl only as *what its own
  statement returned* — never as a number it could re-derive some other way.
* **the outcome the store forces** — `Ensures(CarriedOutRemoval(db, identifier, Result()))` and
  `Exsures(RemovalRefused, RefusedRemoval(db, identifier))`.
  The primitive does not always report a count: `do_query` runs
  `cursor.execute` (`subqueries.py:21-25`), and when the store holds a live
  constrained `FOREIGN KEY` reference to the targeted row sqlite fails the
  statement and the backend raises `IntegrityError('FOREIGN KEY constraint
  failed')` (`django/db/backends/sqlite3/base.py:387-391`), which propagates —
  nothing on the fast branch catches it. The two clauses are the two directions
  of that: a returned count means the store did *not* refuse, and the refusal is
  signalled only when it did. The exceptional clause also keeps the **cost**: the
  refusal is what the store answers a statement *with*, so the statement was
  issued (the `execute_wrapper` sees it before the store accepts or refuses it),
  it cost one against the handle and one in total, and it carried the identifier
  it was handed. Only the report is missing, there being no count to report.
  Grounded and measured in `axiom_check.py` section (c), in both directions and
  on the cost: the protected row is answered with no count and survives while the
  refused invocation still issued exactly ONE statement carrying its identifier
  (c.1), the *same* identifier with the protecting row deleted is answered with a
  count (c.2), and a dependent row behind a `db_constraint=False` reference is
  answered with a count (c.3) — which is what makes the refusal the store's
  own refusal rather than "a dependent exists". The refusal is reachable on the
  modeled path: `can_fast_delete(protected)` is asserted true first, because a
  `DO_NOTHING` back-reference does not disqualify the fast branch
  (`deletion.py:274-280`), so this is an input `remove_single_independent`
  genuinely receives.

These are the **weakest** contracts the modeled behaviour needs; the patch does
not change this callee, so it is a genuine kind-A axiom (not the operation under
change). The callee is modelled **once**, as this effectful invocation. Modelling
its return value a second time as an effect-free function of the identifier would
be unsound in the refining direction: a zero-cost model operation would refine to
a real operation that issues a `DELETE`, so an impl could surface a row count it
never paid a statement for while the modelled statement budget stayed at one.

The refinement additionally relies on the callee NOT clearing the in-memory pk
(only the patched `setattr` does); axiom_check.py asserts this property too.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
database and a minimal dependency-free model (the structural twin of the
test's `User`), then runs the real `DeleteQuery(model).delete_batch([pk], 'default')`
on (a) a live single row (50×, confirming `can_fast_delete` and that exactly
one row is reported removed and the in-memory pk is left untouched), (b) an
absent identifier (25×, count `0`), (c) **the refusal**, in both directions and
on the cost — a still-`can_fast_delete` row protected by a live `DO_NOTHING`
foreign key is answered with no count (and the real exception's class is checked
to be `IntegrityError`, the row is checked to survive, the in-memory pk is checked
to be untouched, and the refused invocation is checked to have issued exactly ONE
statement carrying that identifier), the same identifier with the protector
deleted is answered with count 1, and a dependent behind `db_constraint=False` is
answered with count 1 — (d) the **extremes of the stated domain** —
`2**63 - 1`, `-2**63`, `2**63 - 2`, `-2**63 + 1`, `±2**62`, `2**31`, `-2**31 - 1`,
each stored and observed live (count 1) then re-targeted absent (count 0), 16
further observations — and, as the domain claim's other half, (e) seven
identifiers **outside** the range, each of which must report no count at all, plus
(f) the inhabitance measurement above. 93 observations in total; every one
satisfies the axiom's `Result() >= 0`, single-statement, target and report
clauses, and the refusal is measured with `PRAGMA foreign_keys` read out of the
live connection rather than assumed (if the constraint were not enforced the
refusal sections are skipped and the reported refusal count is 0, so the probe
cannot pass by silently not exercising them). Sections (d)–(f) run *after*
(a)–(c) on purpose: on sqlite an `AutoField` primary key is `AUTOINCREMENT`, whose
high-water mark lives in `sqlite_sequence` and is never lowered, so once a row has
been stored at `2**63 - 1` no later `AutoField` insert can succeed — not even
after that row is deleted — and every section that needs a freshly created object
must come first. It imports only Django itself (the module the patch lives in);
nothing test-private. Exit 0 iff sound. (Outside the container Django is absent,
so it prints `G-AX SKIP` and returns 0; the orchestrator runs it in-container.)

The axiom is flag-independent: `delete_batch`'s return is the DB-reported row
count regardless of backend; G-AX exercises the default `sqlite3` backend the
harness uses. The stated domain is scoped to that same backend, which is the one
every gate and every graded test run of this instance uses: the signed 64-bit
window is where sqlite's `INTEGER` (and hence the `AutoField` primary key the
fast path removes by) is defined. A store whose integer column were wider would
make the `Requires` *narrower* than that backend's real domain — that is the
direction G-AX section (e) is written to catch, and it is checked on the backend
under test rather than assumed for all of them.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned seed: `SEED = 11179`** (module constant in `conformance_check.py`).
**Input count: 100000** Requires-satisfying trials (99 boundary — 11 identifiers
x 3 store states (row present / row absent / row present and protected) x 3 handle
tags — then seeded fuzz over the same space to the target); ~4 min in-container.
Of those, 33217 trials were ones the store REFUSED, on both legs.

| leg | what it is |
|---|---|
| SHADOW | the `# impl-start`/`# impl-end` region of `remove_single_independent` copied verbatim with the contract calls stripped, plus `PersistentObject` and `Database` minus their `Ensures`. The `@ContractOnly` axiom `remove_rows` has no body to copy, so the shadow **calls the real** `sql.DeleteQuery(model).delete_batch([identifier], using)` (§3.1) — the axiom is exercised, not assumed, and each of its record clauses is grounded in an observation of that real statement (statement count and bind parameters read through the connection's `execute_wrapper`, report taken from the real return value) rather than assigned by hand. |
| ORACLE | the **real patched** `Collector.delete` (§1, `django/db/models/deletion.py:274-280`), **called** — not transliterated. Each trial builds a live dependency-free ORM instance with a stored pk, collects it with the real `Collector`, and calls `collector.delete()`. |

**Observables diffed:** the returned `count` (vs the model's `Result()`),
`getattr(instance, model._meta.pk.attname)` after return (vs `instance.pk`), the
number of row-removal statements each leg issued on the alias it was given (vs
`db.removal_statements`), the number it issued **in total across every
configured connection** (vs the `LEDGER.total_removal_statements` delta — the
oracle leg wraps all connections, not just `self.using`, so a removal routed
elsewhere would be counted), and the identifier that statement was
parameterized with (vs `db.last_removal_target`), and **whether the removal was
refused at all**. The last of those diffs the shadow leg's `RemovalRefused` (raised where the store
refuses, since the shadow calls the real primitive) against the oracle leg's
propagating `IntegrityError` (vs the model's `Ensures(not
db.completed_removals == Old(db.completed_removals) + 1)` / `Exsures(RemovalRefused, …)` pair). Both legs must
refuse on the same trials and neither may refuse where the other returns, so the
condition is diffed in both directions rather than only where it fires; and the
refusal is additionally cross-checked against the store's own state (`refused` iff
the trial seeded a protecting row), so a leg that refused for some *other* reason
would be caught. On the refused trials the exceptional clause's own pins are
diffed too: each leg's per-handle statement count, total statement count and
observed removal target are compared on that path, which is what grounds
"the refused statement was still issued, still cost one, and still carried this
identifier" in a measurement rather than in the axiom. Each leg is additionally
checked to surface the row count that its own statement reported (vs
`db.last_removal_report`), so the count-provenance pin is diffed and not merely
restated. Both cost pins are asserted to be exactly one on the oracle leg, so
the per-handle and total clauses are each grounded in the real branch's
behaviour rather than in each other. The unmodeled
`{label: count}` component (§2) is additionally asserted equal to
`{label: count}` so the return-shape refinement cannot hide a count mismatch. If
the real statement's bind parameters are ever unobservable on the backend, the
script reports `unsupported` (an explicit gate skip) rather than passing with the
target clause unchecked.

**Bridge (§2, inverted).** `PersistentObject.pk` ↔ the pk attribute reached by
its dynamic name (`id` for the check's model); the scalar `identifier` ↔ the
singleton `[identifier]` handed to the primitive; the opaque `using: int` tag ↔
a configured sqlite alias. Each tag maps to a **pair** of aliases holding
identical row state (`shadow<u>` / `oracle<u>`), because both legs issue a real
`DELETE` and would otherwise steal each other's row.

**Domain.** The model's `Requires` are `Acc(instance.pk)`,
`instance.pk is not None` and `-(2 ** 63) <= instance.pk < 2 ** 63`: every
generated pk is an `int` (never `None`) drawn from the signed 64-bit range, so the
**sampled domain is exactly the stated domain** — boundary identifiers reach both
of its endpoints and the fuzz is `rng.randint(-2**63, 2**63 - 1)`, which is that
range and nothing narrower. Boundary — the F2P shape
(`test_fast_delete_instance_set_pk_none`), then identifiers
`1,2,3,0,-1,7,12345,±2^31,-2^63,2^63-1` × three store states × all 3 tags; then
seeded fuzz over the same space. The store states are row-present, row-absent and
**row-present-and-protected** (a live `DO_NOTHING` reference to it), so the
sampled domain covers the refused outcome as well as the two returning ones —
the divergent input the panel found is inside the sampled domain, not excluded
from it. The fourth combination (absent *and* protected) is not a state the store
can hold, protection presupposing a row to protect; and if the backend does not
enforce the reference constraint the refusal dimension drops out and the script
says `unsupported` rather than passing with it unexercised. Both reachable
primitive counts (`1` for a live row, `0` for an absent identifier) are observed
and reported, alongside the refused trials, which have no count at all. The
endpoints are
where the domain genuinely ends (§3.1): one step outside, the store can neither
hold such a row nor adapt the identifier, so there is no in-domain input the
sampling leaves out.

**Guard against a vacuous pass.** The general path of `delete`
(`deletion.py:324-326`) *also* clears every collected instance's pk and did so
pre-patch, so an oracle that fell through to it would agree with the shadow even
against unpatched code. Every trial therefore asserts the real code entered the
modeled branch (`len(data)==1`, `len(instances)==1`, `can_fast_delete`), and
startup asserts the pk-clearing statement is present in the live fast branch. The
protected trials are held to the same standard: `can_fast_delete` is asserted for
the protected instance too, so the refused observations are observations of the
modeled branch and not of the general path.

**Falsifiability, checked empirically:** against unpatched `/testbed` (guard
bypassed) the differential reports `shadow pk after = None` vs `real pk after = 1`
and exits 1. Four shadow mutants are caught: dropping `instance.pk = None`
(the prepatch impl) → pk disagreement; `count = 1` fabricated → count
disagreement on an absent row; clearing the pk *before* calling the primitive →
count disagreement on a live row; and swallowing the store's refusal
(`except RemovalRefused: count = 0` in the shadow) → measured control, exit 1
with `DISAGREEMENT on (pk=1, row_present=True, protected=True, tag=0): shadow
ended with count 0 / real ended with a refusal`. The refusal dimension is
therefore load-bearing in the gate and not merely observed.
