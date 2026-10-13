# mapping.md — django__django-11603

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f618e033acd37d59b536d6e6126e6c5be18037f6`, states the type
abstraction, and records that this bundle consumes NO axioms (the changed
behaviour is modelled deeply; the unchanged construction tail is unobserved).

Repo file under change: `django/db/models/aggregates.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `construct_dedup(allow_dedup, dedup)` | the deduplication-decision prologue of `Aggregate.__init__` — `django/db/models/aggregates.py:24` (body lines 25–27: `if distinct and not self.allow_distinct: raise TypeError(...)` then `self.distinct = distinct`) | the shared, **unchanged** constructor prologue, modelled deeply (not axiomatized): it decides accept-vs-refuse from the per-family capability and records the request |
| `build_mean(dedup)` | constructing an `Avg(...)` aggregate — `Avg` class `django/db/models/aggregates.py:99`; the post-patch addition `allow_distinct = True` on line 102 | one of the two changed families: the arithmetic-mean aggregate |
| `build_total(dedup)` | constructing a `Sum(...)` aggregate — `Sum` class `django/db/models/aggregates.py:142`; the post-patch addition `allow_distinct = True` on line 145 | the other changed family: the running-total aggregate |
| `CapabilityError` | the `TypeError("%s does not allow distinct." % ...)` raised at `aggregates.py:26` | user-defined exception modelling the refusal (a builtin-exception `Exsures` crashes the Nagini translator; §2) |
| `allow_dedup` parameter | the class attribute `allow_distinct` read as `self.allow_distinct` (`aggregates.py:25`); base default `False` on `Aggregate` (`aggregates.py:22`) | the per-family capability flag — the single datum the patch changes |
| `dedup` parameter | the `distinct` keyword argument of `Aggregate.__init__` (`aggregates.py:24`); recorded as `self.distinct` (`aggregates.py:27`) | the caller's deduplicate request |

The repo lines the patch ADDS (for the refinement audit; not referenced from the
consumer spec view): `allow_distinct = True` as a class attribute on `Avg`
(`aggregates.py:102`, between `name = 'Avg'` and the next class) and on `Sum`
(`aggregates.py:145`, between `name = 'Sum'` and the next class). The third
family already permitted, `Count`, carries `allow_distinct = True` at
`aggregates.py:108` (unchanged by the patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.allow_distinct` (a class attribute, always `True`/`False`) read inside `Aggregate.__init__` | `allow_dedup: bool` parameter | the per-family capability is a class-level constant resolved at construction; passing it as an explicit boolean parameter is the exact value. For `Avg`/`Sum` post-patch and `Count` it is `True`; for `Aggregate`/`Max`/`Min`/`StdDev`/`Variance` it is `False`. |
| `distinct: bool` keyword argument (default `False`) | `dedup: bool` parameter | identical boolean; defaulting is irrelevant to the modelled decision (the F2P passes `distinct=True` explicitly). |
| `self.distinct = distinct` (object state stored at `aggregates.py:27`) then later read back | `Result()` of `construct_dedup` (the recorded value) / `build_*` | the only observable of the prologue that the tests read is *which value got recorded*; `Result() == dedup` captures `self.distinct == distinct`. |
| `raise TypeError("%s does not allow distinct." % cls)` (`aggregates.py:26`) | `raise CapabilityError()` + `Exsures(CapabilityError, …)` | a builtin-exception `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so the single `TypeError` is modelled by one user-defined exception class. The tests observe *that* a `TypeError` is raised for a disallowed family, not its message. |
| the construction tail — `self.filter = filter`, `super().__init__(*expressions, **extra)` (`aggregates.py:28–29`), and the mixin/`Func` bases | abstracted away (a bare `return stored`) | this tail is UNCHANGED by the patch, independent of the `distinct`/`allow_distinct` decision, and not observed by this specification (the F2P only checks that distinct construction succeeds and aggregates the distinct values). It is therefore neither modelled deeply nor axiomatized — it is dropped, the standard treatment of an unchanged, decision-irrelevant suffix. |
| the call COMPLETES: constructing `Avg(...)`/`Sum(...)` returns the object (or the prologue raises) — ordinary Python evaluation of loop-free straight-line code | `Requires(MustTerminate(2))` on `build_mean`/`build_total` (and measure 1 on the `construct_dedup` prologue they invoke) | the real constructor is bounded straight-line work, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering. Nagini verifies partial correctness by default (no `Decreases`/termination proof required), so without this obligation a non-terminating body (`while b: Invariant(True)`) satisfies every `Ensures` vacuously while a real constructor that hangs would time out the F2P — the G-PANEL-1 witness class this obligation closes. |

No string or float modelling is needed: the entire decision is over two
booleans.

## 3. Callee provenance / axioms

**There are no `@ContractOnly` axioms in this bundle** (the `axioms` region is
empty). The one operation under the spotlight — the per-family capability that
decides whether a deduplicate request is honoured — is modelled **deeply**: the
`construct_dedup` prologue spells out the exact `if distinct and not
allow_distinct: raise` / `self.distinct = distinct` control flow of the real
`Aggregate.__init__`, and the two family constructors `build_mean`/`build_total`
invoke it with their (changed) capability flag `True`. Nothing is axiomatized,
so there is no A-consumed and no A-reference callee, and `axiom_check.py`
correspondingly validates the modelled *decision* end-to-end against the real
Django classes rather than a single callee contract (see §3.1).

### 3.1 What `axiom_check.py` validates (G-AX, in-container)
Although there is no axiom to over-approximate, `axiom_check.py` provides the
G-AX evidence that the deep model matches reality: it imports the real
`django.db.models.aggregates` (Avg, Sum, Count, Min, Max, StdDev, Variance,
Aggregate) and, for each family, observes the real `__init__` decision over
`distinct ∈ {False, True}`:

  * the model predicate `real_refuses(cls, distinct) := distinct and not
    cls.allow_distinct` must equal whether the real constructor raises
    `TypeError`;
  * when it does NOT raise, the constructed object's `.distinct` attribute must
    equal the requested `distinct` (read-back fidelity, the `Result() == dedup`
    post);
  * the discriminating post-patch behaviour is asserted against whichever tree
    is mounted: the checker DETECTS the tree (does `Avg('x', distinct=True)`
    raise?) and requires post-patch that `Avg`/`Sum`/`Count` accept distinct and
    record it, while `Min`/`Max`/`StdDev`/`Variance`/`Aggregate` still refuse it.

Exit 0 iff every observation matches the model. It imports only the repo under
test plus stdlib; nothing external.
