# refinement.md — django__django-11179

The operation-by-operation correspondence between `model.py`'s implementation
(the `remove_single_independent` impl region + the `remove_rows` axiom)
and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fast single-object removal path — `Collector.delete()` (`django/db/models/deletion.py:274-280`)

Gold hunk (the one change, at `deletion.py:280`):
```
             if self.can_fast_delete(instance):
                 with transaction.mark_for_rollback_on_error():
                     count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
+                setattr(instance, model._meta.pk.attname, None)
                 return count, {model._meta.label: count}
```

The optimized branch is entered only when `len(self.data) == 1 and len(instances) == 1`
and `self.can_fast_delete(instance)` — i.e. a single object with no cascades,
no parents, and no signal listeners. The bug: this branch removed the row and
returned the count but never cleared the in-memory object's primary key, unlike
the general multi-object path (`deletion.py:324-326`,
`setattr(instance, model._meta.pk.attname, None)`). The fix adds the identical
clearing statement to the fast branch.

| # | model.py impl op (`remove_single_independent`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `instance: PersistentObject` with field `instance.pk` | the model `instance` object; its primary key reached via `model._meta.pk.attname` | R | the in-memory object with only its touched field modelled; the dynamically-named pk attribute ↔ `instance.pk` (mapping.md §1, §2). |
| A2 | `identifier = instance.pk` (the stored, non-`None` pk) | `[instance.pk]` — the pk passed to `delete_batch` | R | reading the primary-key attribute; the singleton list ↔ the scalar `identifier` (one object on the fast path; mapping.md §2). |
| A3 | `count = remove_rows(db, identifier)` | `count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)` (inside `with transaction.mark_for_rollback_on_error()`) | A-consumed | the unchanged row-removal primitive is axiomatized **once**, as an **effectful invocation**: one call issues exactly one row-removal statement (`db.removal_statements == Old(...) + 1`), that statement targets the identifier it was handed (`db.last_removal_target == identifier`), the value it returns is the non-negative DB-reported row count that same statement produced (`db.last_removal_report == Result()`, `Result() >= 0`), and the same one statement advances the module-wide total whichever handle it went through (`LEDGER.total_removal_statements == Old(...) + 1`) — mapping.md §3.1. The proof consumes all five Ensures: the tally clause discharges the per-handle single-statement postcondition, the total clause discharges the total-cost postcondition, the target clause discharges the removal-target postcondition, and the report clause discharges the count-provenance postcondition. The invocation has a **second outcome**, which the axiom carries too: where the store holds a live constrained reference to the targeted row the statement fails and `IntegrityError('FOREIGN KEY constraint failed')` propagates out of `do_query`'s `cursor.execute` (`django/db/backends/sqlite3/base.py:387-391`) — nothing on this branch catches it, and `mark_for_rollback_on_error` only marks the transaction on the way past. Modelled as `Exsures(RemovalRefused, … db.completed_removals == Old(db.completed_removals) and <tally> and <target> and <total>)` plus `Ensures(db.completed_removals == Old(db.completed_removals) + 1)`, i.e. a count comes back only from a removal the store carried out, the refusal leaves the carried-out tally standing still, and the refused statement was still issued (so it still cost one against the handle and one in total, and still carried the identifier it was handed). The proof consumes those too: they are what discharge the caller-side clauses (6a)/(6b) below. Grounded and measured in `axiom_check.py` section (c) in both directions and on the cost. One invocation ↔ one statement because a one-element `pk_list` makes `delete_batch`'s chunk loop run exactly once; the statement's `WHERE` is built from that `pk_list` and nothing else, which is why its target is the identifier passed in. The `with transaction.mark_for_rollback_on_error()` wrapper is transaction bookkeeping with no effect on the returned count, the in-memory pk, or the number of DELETE statements (it only marks the surrounding transaction for rollback if the body raises); it is not behaviour the F2P/P2P tests of this change observe. The axiom states those effects on the identifiers the store can represent (`Requires(-(2 ** 63) <= identifier < 2 ** 63)`), which is where the real primitive returns a count at all: past that window the driver cannot adapt the bind parameter and raises instead (mapping.md §3.1, measured by `axiom_check.py` sections d/e), and no stored row can be keyed by such a value in the first place (section f), so the bound is the primitive's real domain and not a narrowing of the modeled behaviour. |
| A4 | `instance.pk = None` | `setattr(instance, model._meta.pk.attname, None)` | **I** (under R on the attribute name) | the FIX. Identical concrete operation — clear the object's primary-key attribute to `None` — with the dynamic attribute name refined to the field `pk` (R, mapping.md §2). This is the single added statement of the gold patch. |
| A5 | `return count` | `return count, {model._meta.label: count}` | I-ret (under R on the return shape) | identical return of the same `count`; the `{model._meta.label: count}` dict literal is an identical construction over the same `count` value (no extra tested behaviour; mapping.md §2). |

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops step **A4**
(`instance.pk = None`) exactly as the pre-patch fast branch lacks the
`setattr(...None)` line. With the byte-identical frozen spec it **fails**
verification on the postcondition `Ensures(instance.pk is None)`
(`model_prepatch.py:63` — `Assertion (instance.pk is None) might not hold`).
That is precisely the behaviour the F2P test observes:
`test_fast_delete_instance_set_pk_none` deletes a fast-deletable `User` and
asserts `self.assertIsNone(u.pk)`. The spec is therefore strong enough that no
implementation omitting the pk-clearing can verify (spec sees the bug).

The cost clause `Ensures(db.removal_statements == Old(db.removal_statements) + 1)`
pins the removal's **cost**: removing one independent object issues exactly one
row-removal statement. This is behaviour of the real patched function, not an
incidental detail of it — the optimized branch exists precisely to spend one
statement, `delete_batch` on a one-element `pk_list` issues exactly one
`do_query` (its chunk loop runs once), and the P2P test
`test_do_nothing_qscount` wraps a fast-deletable `b.delete()` in
`self.assertNumQueries(1)`, so the statement count is asserted by the suite.

This clause is load-bearing for `verify ⇒ resolved`, and its absence was a real
hole. When the primitive was modelled as a `@Pure` function of the identifier
alone, invoking it twice was *mathematically indistinguishable* from invoking it
once: no postcondition over `instance.pk` and the return value could separate
them, because both invocations denote the same value. Same-spec impls that
duplicated the invocation (or added an extra unused one) therefore VERIFIED,
while their faithful patches issued a second `DELETE` and failed
`test_do_nothing_qscount` — verify ∧ ¬resolve. Expressing "exactly one removal
statement" requires the primitive to carry an *effect*, which is why
`remove_rows` is an effectful axiom over a `Database` carrier rather than a pure
function. The clause is stated as observable cost, not as a call count in the
model's own syntax, so behaviourally-equivalent reshapes (clearing the pk before
the captured removal, splitting the return through equivalent control flow) all
still verify.

The cost clause alone was **not sufficient**, and that insufficiency was also
demonstrated rather than theorised. A cost budget of one statement constrains
nothing about *which* removal the surfaced count came from. Two further clauses
close that:

`Ensures(db.last_removal_target == Old(instance.pk))` pins the **target** of the
one statement the path paid for: it must remove by the identifier the object
carried on entry. The real patched branch has this property — it builds the
removal from `[instance.pk]`, read before the clearing statement, and
`delete_batch`'s `WHERE` is built from that list and nothing else — and it is
tested behaviour: the F2P/P2P deletion and count tests observe the object that
was actually removed, so a branch spending its one statement on a different
identifier removes the wrong row (or none) and surfaces a count for the wrong
object.

`Ensures(Result() == db.last_removal_report)` pins the **provenance** of the
surfaced count: it is the row count that same statement itself reported. The real
branch has this property — `count` is the value `delete_batch` returned, and
`return count, {label: count}` surfaces exactly that — and it is what the
count-observing P2P tests (`test_model_delete_returns_num_rows`,
`test_queryset_delete_returns_num_rows`) assert: user code is told how many rows
*this* delete removed. Note this is strictly stronger than pinning the count to
some non-negative number of the identifier: it says the count must be produced by
the removal the path paid for, so a count obtained by consulting the database a
second time is excluded even when the number happens to agree.

A cost budget stated over ONE handle was still not sufficient, and this too was
demonstrated rather than theorised. Clauses (1)–(3) all quantify over the handle
the path was *given*, and a handle is a thing an implementation can obtain for
itself. An implementation that did the reference work correctly on `db` — one
statement, right target, own report returned, pk cleared — and *additionally*
issued a row-removal statement through a handle of its own making satisfied every
one of those clauses, because the extra statement was not on `db` at all. Its
faithful patch is a fast branch that performs two real `DELETE`s, which
`assertNumQueries(1)` catches: verify ∧ ¬resolve again, and this time not
closable by any postcondition over `db`. The defect was in the model, not in the
clauses: *total* cost was simply not an observable, so the patch's delta (a
one-statement removal) could not be distinguished from a two-statement one.

`Ensures(LEDGER.total_removal_statements == Old(LEDGER.total_removal_statements) + 1)`
makes it observable. There is exactly one ledger because there is exactly one
body of stored data behind every handle: a `DELETE` issued through any connection
removes rows and costs a statement, so the total is the cost the data really
paid, and it is precisely what the suite's exact-statement-count assertion
observes. The real patched branch has this property — it issues its single
`delete_batch` against `self.using` and nothing else, so its total is one — and
the property is behaviour of the real function rather than an incidental detail:
the optimized branch exists to spend one statement, and the number the caller
observes is the number the database received, not the number booked against a
particular alias. The clause is stated as a total, not as a ban on constructing
handles, so behaviourally-equivalent reshapes still verify while every rival that
removes rows twice over is rejected however it routes the second removal. Note
the per-handle clauses remain load-bearing alongside it: an implementation that
issues its one total statement through a handle other than the one it was given
satisfies the total pin and is rejected by (1)–(3). Together they say *exactly one
removal in total, and it was issued against the handle the caller named.*

Together the four clauses are what makes the model's statement budget mean what
it says. An earlier form of this spec pinned the count to a `@Pure` function of
the identifier alone, applicable from the implementation without cost, while the
same real callee was *also* modelled effectfully. That combination admitted
verify ∧ ¬resolve directly: an implementation could spend its one accounted-for
statement on anything (or redundantly) and obtain the surfaced count from the
effect-free path — one modelled statement, two real `DELETE`s. Two such impls
were EXECUTED through the official harness and did not resolve (F2P
`test_fast_delete_instance_set_pk_none` passes, P2P `test_do_nothing_qscount`
fails on `assertNumQueries(1)`; `resolved=false, completed=true`, 2/2 attempts,
consistent-not-flaky), recorded in `verdict.md` as `atk_3` / `atk_4`. The
correspondence defect was in the A-leg: a model operation with zero modelled cost
refined to a real operation that issues a `DELETE`, so every model-side
statement-count guarantee was unsound for impls that used it. The callee is now
modelled exactly once, effectfully, and the only value in the model naming a row
count is the record the paid-for statement wrote.

Finally, `Requires(MustTerminate(2))` makes the claim **total** rather than
partial correctness. Under partial correctness an implementation may satisfy
every clause above and then diverge, verifying vacuously; the faithful patch of
such an implementation never returns from a single `delete()`, hanging the suite
rather than resolving it. The real branch terminates (a straight-line body over a
callee whose chunk loop is bounded by the one-element `pk_list`), so the
termination obligation is a property the patched function genuinely has.

Total correctness claims the branch **ends**, and it ends in one of exactly two
ways: with the count, or with the store's refusal (the exceptional clause below).
It claims no *other* way of ending, and in particular it claims a normal return
except where the store refuses — which is only true on the identifiers the store
can represent, and that is
why the domain is bounded, in the axiom and in `remove_single_independent` alike
(`-(2 ** 63) <= instance.pk < 2 ** 63`). The identifier reaches the sqlite driver
as a real bind parameter, and a value outside that window cannot be adapted:
`delete_batch([2**63], using)` raises `OverflowError` out of
`SQLiteCursorWrapper.execute` (`django/db/backends/sqlite3/base.py:387-391`)
instead of reporting a count, so the pk-clearing statement at `deletion.py:280`
is never reached and neither counter advances. Two facts make bounding the domain
a statement *about* the domain rather than a dodged case, both measured by
`axiom_check.py` (sections d–f, 93 observations, mapping.md §3.1): the bound is
boundary-tight — `2**63 - 1` and `-2**63` really do return, with one statement and
the DB's own count, live and absent alike — and the excluded region is
uninhabited, because `objects.create(pk=2**63)` raises the *same* `OverflowError`
on the INSERT, so no stored row is ever keyed by an out-of-range identifier and no
*persistent* object can carry one. The behaviour under specification (a saved
dependency-free object being deleted, the F2P shape) therefore lies wholly inside
the stated domain, and the domain restriction removes no impl obligation on any
input the graded tests or any real database row can produce. The alternative —
giving the primitive an `Exsures` for the adaptation failure — would have had to
condition the exceptional postcondition on the identifier being unrepresentable
anyway, or else a rival could satisfy the spec by *always* raising and clearing
nothing; bounding the domain states the same fact without opening that door. That
conditioning requirement is not hypothetical: it is exactly what the refusal's
`Exsures` does below, and the rival it exists to stop
(`uniq-manufacture-refusal`) is measured.

### The store's refusal — the exceptional clause (6)

The five clauses above are the guarantees of a removal the store **carried out**.
The real branch has a second ending, and it is reachable on a *fast-deletable*
object: a live row whose `FOREIGN KEY` references the targeted row (declared
`on_delete=DO_NOTHING`, which leaves `can_fast_delete` true — Django asks the
database for nothing, so nothing is collected) makes sqlite fail the `DELETE`, and
`IntegrityError('FOREIGN KEY constraint failed')` propagates out of
`SQLiteCursorWrapper.execute` (`django/db/backends/sqlite3/base.py:387-391`)
through `do_query` (`django/db/models/sql/subqueries.py:21-25,27-42`) and out of
the fast branch (`deletion.py:274-280`) unhandled. On that input no row is
removed, no count exists, and `setattr(instance, …, None)` at `deletion.py:280` is
never reached. A spec that demanded clauses (1)–(5) unconditionally would be
demanding something the real patched branch does **not** do — it would be false of
the gold patch on an input the gold patch genuinely receives.

The honest repair is to model the outcome, not to shrink the domain. Two clauses
do it, and **both** are load-bearing:

* **(6a)** `Ensures(db.completed_removals == Old(db.completed_removals) + 1)` —
  returning a count *at all* is something only a carried-out removal entitles the
  path to.
* **(6b)** `Exsures(RemovalRefused, Acc(instance.pk) and <permissions> and
  db.completed_removals == Old(db.completed_removals) and
  db.removal_statements == Old(…) + 1 and
  db.last_removal_target == Old(instance.pk) and
  LEDGER.total_removal_statements == Old(…) + 1 and
  instance.pk is Old(instance.pk))` — the path may end without a
  count only where the store carried nothing out, and even then it has
  spent its one statement, in total as well as on the handle, on this object's
  stored identifier, and it has left the in-memory object as it found it.

Why the `Exsures` is **conditioned** on the carried-out tally standing still: an
unconditional exceptional clause is the cheapest hole in a total spec, because
every clause about a returning path is vacuous on a path that never returns. An
impl that simply raises satisfies (1)–(5) trivially and does no work at all. That
is measured: `uniq-manufacture-refusal` is rejected with *"Assertion
(db.removal_statements == (Old(db.removal_statements) + 1)) might not hold"*, and
its sibling `uniq-refuse-after-removing` — which does the whole job and then
throws the count away — is rejected by the carried-out half, since the axiom
advances `db.completed_removals` exactly when the store reported a count, so a
completed removal cannot be passed off as a refusal.

Why the tally, target and total are **pinned on the exceptional path**: without
them, the refusal is a licence to do less, and a rival can take a free exit over
the whole protected sub-domain. `uniq-refuse-without-asking` (refuse, truthfully,
but before issuing anything) was measured VERIFYING while those pins were absent;
with them it is rejected with *"Assertion (db.removal_statements ==
(Old(db.removal_statements) + 1)) might not hold"*. The pins are true of the real
callee for a concrete reason: the store's refusal is the **answer to a statement**,
so the statement was issued — the connection's `execute_wrapper` sees it before
the store accepts or refuses it, which is how `axiom_check.py` section (c.1) and
`conformance_check.py` measure the refused path's cost and target rather than
assuming them.

Why **(6a)** is needed *as well as* (6b): pinning the refused path's cost opened a
hole on the returning path, and the hole was measured before it was closed. With
(6b) alone, `uniq-swallow-stale-report` — catch the refusal, return
`db.last_removal_report`, clear the pk — VERIFIED: the count-provenance pin (3) is
satisfied by construction, and the tally/target/total come free out of the
refusal's own `Exsures`. Its faithful patch converts a constraint violation into a
plausible count belonging to some earlier statement and clears the pk of a row
that is still in the table. (6a) rejects it (*"Assertion (not
(db.completed_removals == Old(db.completed_removals)) might not hold"*).
Symmetrically (6a) alone admits
`uniq-refuse-without-asking`. Neither half is redundant.

Why `db.completed_removals` is held at **1/2**: were it writable, the clause
would be worthless — an impl could set it and take the free exit. Measured:
`uniq-forge-completed` is rejected with *"There might be insufficient permission
to access db.completed_removals"*. The framing mirrors the store: how many
removals the store has carried out is a record of what already happened to
statements that were issued, exactly like the statement tally, and nothing
readable predicts how the NEXT statement will be answered.

Why the exceptional clause ALSO pins **`instance.pk is Old(instance.pk)`** — the
in-memory object is left as it was found. This was the last free observable on
this path, and leaving it free was a measured hole rather than a modelling
nicety.

It is **true of the real patched function**. The clearing statement the fix adds
sits *after* the row-removal call and before the `return`
(`deletion.py:280`, between `delete_batch` and `return count, {label: count}`),
so where the store refuses, `IntegrityError` propagates out of `delete_batch` and
the clearing statement is **never reached** — the object keeps the identifier it
came in with. That is measured, not argued: `axiom_check.py` section (c.1)
asserts `protected.pk is not None` after a real refusal, and
`conformance_check.py` compares the pk after a refusal on both legs. It is also
not an accident of this one branch: the general multi-object path likewise clears
its instances' pks only *after* its `transaction.atomic(...)` block has completed
(`deletion.py:319-321`, outside the `with`), so "the identifier is surrendered
only once the row is actually gone" is the behaviour of the real code on both
paths, which is exactly what the docstring states.

It is **false of the recorded counterexamples**, and that is why the clause is
the repair rather than a decoration. While `instance.pk` was unpinned here, the
*returning* and *refused* outcomes were independently satisfiable by clearing the
identifier EARLY (before the store's answer is in) and by clearing it LATE: both
orders verified, and each was bracketed by a positive control. A rival could
therefore branch that permitted difference on anything it could read — including
the handle's own record — and satisfy every clause in **both** arms, which is
what `uniq-freeread-clear-order` and `uniq-freeread-clear-order-ledger` do. The
model prices no read, but the real branch holds no such counter: learning it
costs a `SELECT` before the `DELETE`, so the faithful patch pays two statements
where `test_do_nothing_qscount` asserts `assertNumQueries(1)`, and it does not
resolve.

An earlier version of this document drew the wrong conclusion from that and the
correction is the substance of the current repair, so it is recorded rather than
quietly replaced. It read: *"the free read was not itself the defect, it was only
usable because the spec left an observable difference for it to decide. Pinning
the observable is what removes the whole family at once, for every readable
field."* **That claim is false, and it was falsified by measurement.** Pinning
`instance.pk` on the refused path does kill the two rivals above, but it does not
price the read, and an impl that clears early can simply RESTORE the identifier
when the store refuses — satisfying the pin in *both* arms while still branching on
a counter it never paid for. That shape was measured verifying, with a faithful
patch that passes the F2P test and fails `test_do_nothing_qscount`, through both
readable fields. A second, independent lane survived the same way: an equation
between the return value and a readable record
(`Result() == db.last_removal_report`) is satisfiable by an impl that DISCARDS
what its own statement returned and surfaces the record instead — which is the
"consult the database a second time" behaviour guarantee (3)'s own prose excludes,
and which also does not resolve.

The right reading of the hole is therefore the opposite one: **the free read WAS
the defect.** So long as any part of the store's record sits in the
implementation's read set, an unpriced read stands ready to decide whatever the
spec has not nailed down, and pinning observables one at a time only moves the
family to the next unpinned difference — of which there is always another, because
a spec that pinned *every* difference would reject the correct alternatives that
legitimately differ. The repair is to remove the record from the read set
entirely, and to carry cost and provenance as abstract ghost resources instead
(`RemovalBudget(LEDGER)`, `CarriedOutRemoval`, `RefusedRemoval` — mapping.md §2.1
grounds all three and gives the repo evidence that the real branch holds no such
counter). With the record unreadable, both lanes die at the point of the read
rather than at a clause: the branch cannot be *written*, and the echo has no
readable field to echo. The `instance.pk` pin is kept — it is independently true
of the real function, as shown above — but it is no longer load-bearing against
this family.

With (5) the pair says the identifier is surrendered **exactly** when the row it
names has been removed and at no other time. This is what makes the clearing
order behaviour rather than choice, so no readable fact can license a rival to
pick it.

Consequently the clear-*before*-asking shapes are **not** faithful reshapes and
are no longer positive controls: they differ from the real callee precisely on
the refused outcome, handing back an object that names no row while its row is
still in the table. They are now the rejected rivals `uniq-clear-before-asking`
and `uniq-clear-before-asking-inline`. The bracket that keeps (6b) from being
SPEC-TOO-STRONG is supplied instead by controls that keep the real order:
`pos-control-guarded-clear` (clear after, under a guard on the report) and
`pos-control-late-name` both verify, as does `pos-control-rethrow`, which
confirms the exceptional clause is *establishable* by an impl that reaches the
exit deliberately (`try: … except RemovalRefused: raise`). Clearing late must
verify and clearing early must not — that is the bracket, and both halves are
measured.

The framing of cost and provenance as ghost resources is what makes all of these
clauses unforgeable, and it is strictly stronger than the read-only framing it
replaces. The modeled path holds **no permission at all** on
`db.removal_statements`, `db.last_removal_target`, `db.last_removal_report`,
`db.completed_removals` or `LEDGER.total_removal_statements`: they are not merely
unwritable, they are unreadable, for the reason above. What it holds instead is
one single-use entitlement and, after asking, one receipt. So the only way to
spend a statement is to consume the entitlement (and nothing mints a second), the
only way to name a count is to hold the receipt that the answering statement
minted, and the only way to reach the end-without-a-count outcome is for the store
to really refuse. This mirrors reality on both halves: the number of statements a
delete costs (on one connection or in total), the identifier they removed by, the
rowcount the database reported and whether the database refuses the removal are
facts about the database's behaviour, not values the calling branch gets to choose
— *and they are not values the calling branch can see for free either*, which is
the half the read-only framing got wrong. Forging is closed a level below the
clauses: all three resources are `@ContractOnly @Predicate` (bodyless), so an impl
cannot `Fold` an entitlement into existence to buy a second statement, cannot
`Fold` a receipt to mint provenance it did not earn, and cannot `Unfold` one to
look inside. Those attempts fail at TRANSLATION (`abstract.predicate.fold`), not
at a postcondition. Drawing the entitlement against the module-wide `LEDGER`
rather than the handle is what keeps the off-books lane closed: a removal routed
through a connection the impl obtained for itself still needs a budget it does not
have.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — adding the primary-key-clearing statement to the fast branch — is
an **I** step (the very same `setattr(...None)` concrete operation, only the
dynamically-named attribute refined to the field `pk` by R). There is no deep
model and therefore **no A-reference** here. The single consumed axiom
(`remove_rows`, **A-consumed**, step A3) covers an **unchanged** callee
(`DeleteQuery.delete_batch`) the fast branch invokes; G-AX validates it against
the real callee. We never axiomatize the function under change.

The axiom is **effectful**, and it is the **only** model of that callee — both
facts keep this claim honest. A `@Pure` axiom over the identifier alone would
silently import idempotence: invoking the primitive twice would denote the same
value as invoking it once, so the model could not express "one removal
statement", even though the number of statements is behaviour the P2P suite
asserts (`assertNumQueries(1)` in `test_do_nothing_qscount`). Making the primitive
consume a single-use entitlement closes that: the cost is *expressed*, so step A3
is A-consumed in substance and not just in label.

Retaining a pure twin *alongside* the effectful axiom would have reopened the same
hole from the other side, and did: two model symbols for one callee with
incompatible effect profiles (one costing a statement, one costing nothing) makes
the correspondence fail in the refining direction, because the zero-cost symbol's
only executable realization is a `DELETE`. Whatever the cost clause then certifies
about the model says nothing about the real statement count. Hence the callee is
modelled once, and every count the model can name is the report of a statement
that was actually issued.

**The generalized form of that lesson, which the current repair applies.** A pure
twin is one way to give an implementation something for free whose real
counterpart costs a statement; a *readable field* is another, and it is the one
this bundle kept missing. Dropping the pure twin priced the row COUNT. Grounding
the refusal on a post-state tally rather than a pre-state flag priced the REFUSAL
FACT. Neither priced the STATEMENT RECORD ITSELF — the tallies, the last target,
the last report — because the extra real statement a read of them refines to is a
`SELECT`, and every cost clause in the model counted only removals. So the rule
that governs this model is now stated in its general form: **no model symbol whose
real counterpart requires asking the store may sit in the implementation's read
set, at any permission, whether or not any clause currently mentions it.** By that
rule the record had to leave the read set, which is what mapping.md §2.1 does; and
the same rule forbids reintroducing it under another name — a `has_protecting_row`
predicate, a `row_present` flag, a `will_refuse` boolean, or a `@Pure` twin of the
count are all the same defect in fresh clothing. What may be handed to the path for
free is only what the real branch genuinely has for free: its arguments, the
in-memory object's own attributes (`instance.pk` is a plain attribute — reading it
issues nothing, which is why `pos-control-guarded-clear` and a branch on the
identifier are legitimate), and ghost resources that carry no store information —
an entitlement with nothing inside it, and a receipt it can only obtain by asking.

## D. verify(model) ⇒ resolved

`remove_single_independent` verifies only if it (A3) issues exactly ONE
row-removal statement against the handle it was given, (A3) issues exactly ONE
row-removal statement IN TOTAL across every handle, (A3) issues it for the
identifier the object carried on entry, (A3/A5) returns exactly the row count
that statement itself reported, (A4) clears `instance.pk` to `None`, and
terminates — **and** ends with a count only where the store carried the removal
out, ending without one only by passing on a refusal the store really made, with
the refused statement still paid for on the same identifier (clauses (6a)/(6b),
step A3's `Ensures(db.completed_removals == Old(db.completed_removals) + 1)` / `Exsures`). By R (the in-memory object
and its dynamically-named pk attribute ↔ `PersistentObject.pk`; the singleton pk
list ↔ the scalar identifier; the database alias and the record of statements
issued through it ↔ the `Database` carrier; the `(count, dict)` return ↔ `count`)
and the single **I** fix step, the verified path equals the gold fast branch
`… delete_batch([instance.pk], using) ;
setattr(instance, model._meta.pk.attname, None) ;
return count, {label: count}` on the tested inputs. By G-AX the real
`delete_batch` meets the axiom it stands in for (A-consumed) and never clears
the in-memory pk itself; by G-CONF both legs are observed to issue exactly one
DELETE per removal on the alias they were given AND exactly one in total across
every configured connection (the oracle leg wraps them all, so a removal routed
through another connection would be counted), to issue it for the object's stored
identifier (read from the real statement's bind parameters), and to surface that
statement's own reported rowcount — counted and read through `execute_wrapper`,
not assumed — and to refuse on exactly the same trials (33217 of 100000, always
and only where the store held a protecting row), with the refused path's cost and
target diffed there too. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
