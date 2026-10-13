# mapping.md — django__django-15368

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e972620ada4f9ed7bc57f28e133e85c85b0a7b20`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled property.

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `routeOperands (attrs : List AttrVal)` | the inner `for obj in batch_objs` loop of `QuerySet.bulk_update` — `django/db/models/query.py:668-675` (the `attr = getattr(...); if …: attr = Value(...); when_statements.append(When(pk=…, then=attr))` body) | the modeled changed function: per assignment value, the routing decision (wrap as literal vs apply directly) |
| `AttrVal` | the runtime object bound to `attr = getattr(obj, field.attname)` (`query.py:672`) | structure carrying only the two classification bits the decision reads |
| `AttrVal.isDbExpr` | `hasattr(attr, 'resolve_expression')` — the **post-patch** predicate (`query.py:673`) | the value is a database-side expression (resolves itself to SQL) |
| `AttrVal.strictMatch` | `isinstance(attr, Expression)` — the **pre-patch** predicate (`query.py:673`, with `Expression` imported at `query.py:20`) | coarser secondary classification, strictly narrower than `isDbExpr` |
| `wrapPlan (s : List AttrVal)` | the sequence of `if not <predicate>(attr): attr = Value(attr, output_field=field)` decisions over `batch_objs` | pure spec: per element, wrap-as-literal iff not a database-side expression |

The downstream constructs the routing feeds — `Value(attr, output_field=field)`,
`When(pk=obj.pk, then=attr)`, `Case(*when_statements, ...)`, the optional
`Cast`, and the emitted `UPDATE … CASE WHEN …` SQL (`query.py:674-682`) — are an
**unchanged shared continuation**: identical on the pre- and post-patch branch
and reached regardless of the routing bit. They are neither consumed as a
contract nor deep-modeled (refinement.md §C).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the batch's sequence of `attr = getattr(obj, field.attname)` values | `List AttrVal` | one `AttrVal` per `obj` in `batch_objs`, in iteration order; `len(batch_objs)` ↔ `attrs.length`; empty batch ↔ `[]` |
| a single assignment value `attr` | `AttrVal` | `attr` ↔ `⟨isDbExpr := hasattr(attr,'resolve_expression'), strictMatch := isinstance(attr, Expression)⟩`. Only these two booleans are observed by the change; all other value content is irrelevant to the routing decision and omitted. |
| the per-element outcome "this value is wrapped in `Value(...)`" | `Bool` (`true` = wrapped) | `True` ↔ `true`. The model's `out[k]` is `True` iff the real code rebinds `attr = Value(attr, output_field=field)` for element `k` before appending the `When`. |

Note the **type bijection itself is the bug's locus**: the pre-patch predicate is
`isinstance(attr, Expression)` (→ `strictMatch`), the post-patch is
`hasattr(attr,'resolve_expression')` (→ `isDbExpr`). The two differ exactly on
values that are database-side expressions yet not subclasses of `Expression` —
in this repo, `F` (a `Combinable`, not an `Expression`, but it defines
`resolve_expression`). See §3.

## 3. Classification provenance (kind-R — checked by G-AX / axiom_check.py)

There are **no axioms and no A-reference deep models** in this bundle (axioms
region empty). The single soundness obligation is that the type bijection of §2
is real, i.e. that for the values `bulk_update` actually receives the two
classification bits behave as the model claims and `isDbExpr` is the correct
routing predicate. `axiom_check.py` (G-AX) discharges this by constructing the
real value classes and asserting, on the REAL repo predicates:

* **Strictness / soundness of the bijection.** For each value class the bundle's
  bridge maps to an `AttrVal`, `axiom_check.py` checks
  `isDbExpr == hasattr(attr,'resolve_expression')` and
  `strictMatch == isinstance(attr, Expression)` — i.e. the structure fields equal
  what the real predicates report. It further confirms `strictMatch → isDbExpr`
  (the coarser bit is strictly narrower) and that the witness `F('x')` realizes
  the strict gap (`isDbExpr=True, strictMatch=False`) — the value the issue's
  repro exhibits.
* **Routing correctness.** For each class it checks that the post-patch real code
  wraps the value in `Value(...)` **iff** `not hasattr(attr,'resolve_expression')`
  — i.e. `wrapPlan`'s per-element rule (`! isDbExpr`) equals the real post-patch
  decision. Witness values: `F('name')`, `F('a') + 1`, `Value('x')`,
  `When(pk=1, then=Value(1))`, a plain `str`, a plain `int`, a plain `date`.

Imports only `django.db.models.expressions` (the same module the patched
`bulk_update` imports `F`/`Value`/`Case`/`When` from) plus stdlib. Exit 0 iff
every obligation holds.

The pre-patch repo symbol the change removes (refinement audit only, not in the
consumer spec view): the import `Expression` on `query.py:20` and its use in the
`isinstance(attr, Expression)` guard on `query.py:673`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15368`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `wrapPlan`/`routeOperands` (R/I-tagged ops) to Python over real
assignment values and compares against `patch.diff`'s behaviour, observed
end-to-end: it runs the real patched `QuerySet.bulk_update` against an in-memory
SQLite database and reads back, per element, whether the value resolved on the
database side (a database-side expression applied directly) or was stored as its
literal/string form (wrapped in `Value`). There are no A-tagged callees in the
impl region, so the shadow is pure R/I.
