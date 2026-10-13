# mapping.md — django__django-11603

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`f618e033acd37d59b536d6e6126e6c5be18037f6`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_construct` / `problem_spec_construct` / `correct_construct` | `Aggregate.__init__` distinct-validation + flag storage | `django/db/models/aggregates.py:24-29` |
| `permitsDistinct` (spec helper) | the `allow_distinct` class attribute, per aggregate kind | `django/db/models/aggregates.py:22` (base) + per-class overrides (`:108`) |

## The observable behavior

`Aggregate.__init__` is the single function whose behavior the gold patch
changes. At `base_commit`:

```python
class Aggregate(Func):
    ...
    allow_distinct = False

    def __init__(self, *expressions, distinct=False, filter=None, **extra):
        if distinct and not self.allow_distinct:
            raise TypeError("%s does not allow distinct." % self.__class__.__name__)
        self.distinct = distinct
        self.filter = filter
        super().__init__(*expressions, **extra)
```

`self.allow_distinct` is a class attribute. At `base_commit` it is `True` only
on the counting aggregate (`Count.allow_distinct = True`, `:108`) and `False`
everywhere else (inherited from `Aggregate.allow_distinct = False`). The gold
patch sets `allow_distinct = True` on the averaging aggregate (`Avg`) and the
summation aggregate (`Sum`).

The directly observable consequence (asserted by the F2P test
`test_distinct_on_aggregate`): constructing an aggregate with `distinct=True`
**raises `TypeError`** iff the aggregate kind does not allow distinct; otherwise
the construction succeeds and stores `self.distinct = distinct`,
`self.filter = filter`. Before the patch, `Avg(..., distinct=True)` and
`Sum(..., distinct=True)` raised; after, they construct successfully. (The
problem statement: "Before 2.2, these aggregations just ignored the parameter,
but now throw an exception … just involve setting these classes as allowing
DISTINCT.")

The `super().__init__(*expressions, **extra)` call (storing the wrapped
expressions on the `Func` base) is unchanged by the patch and is orthogonal to
the distinct-policy observable; it is abstracted away (the modeled state carries
only the touched fields `distinct`/`filter` plus the aggregate `kind` that
selects the policy).

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| the aggregate subclass (`Avg`/`Count`/`Sum`/`Max`/`Min`/`StdDev`/`Variance`) | `kind : AggKind` (`avg`/`count`/`sum`/`max`/`min`/`stdDev`/`variance`) | one constructor per concrete `Aggregate` subclass in `__all__` (aggregates.py:11-13) |
| `distinct: bool` keyword arg | `distinct : Bool` | identity |
| `filter` keyword arg (an expression or `None`) | `filter : Option String` | presence-only abstraction: `None ↔ none`, any filter expression ↦ `some _` (its concrete value is untouched by the distinct policy) |
| `self.allow_distinct` for that subclass | `permitsDistinct kind : Bool` | `True ↔ the subclass allows distinct` |
| successful construction (`self.distinct`, `self.filter` set) | `Except.ok { kind, distinct, filter }` | the constructed aggregate's touched fields |
| `raise TypeError("… does not allow distinct.")` | `Except.error AggError.distinctNotAllowed` | the one exception this branch raises |

`permitsDistinct` is the POST-patch (correct/desired) policy: `true` for
`avg`, `count`, `sum`; `false` for `max`, `min`, `stdDev`, `variance`. This is
the ground-truth contract the issue demands and lives in the spec view (it is
the behavior the problem statement asks for, stated abstractly — no patched
symbol named). The per-kind lookup that the *implementation* performs lives in
the impl region, so the prepatch can encode the buggy base_commit policy
(only `count` permits distinct) without altering the frozen spec.

## Callee provenance / flag deps

- No UNCHANGED callee needs an axiom. The distinct-validation + field storage is
  modeled DEEPLY with concrete Lean operations (a Boolean policy lookup, an
  early `return` raise, two field assignments). → `axioms` region is EMPTY;
  `axiom_check.py` is a skip stub.
- `super().__init__` (the `Func` base storing expressions) is NOT modeled: it is
  unchanged by the patch and does not affect the distinct observable. It is not
  a consumed axiom and not a reference callee — it is abstracted out of the
  state entirely.
- Flag dependency: the raise is gated on `distinct AND NOT allow_distinct`. The
  policy `allow_distinct` is per-kind (class attribute), captured as
  `permitsDistinct kind`.

## G-CONF fuzz seed

Pinned seed: **20240612**. `conformance_check.py` enumerates the full
`(kind, distinct, filter∈{None,present})` matrix against the real patched
aggregate classes in-container — observing whether `Cls(expr, distinct=…)`
raises `TypeError` or constructs (and, when it constructs, that `self.distinct`
/ `self.filter` match) — plus ≥10⁵ randomized draws over that discrete domain.
