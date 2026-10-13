# mapping.md — django__django-13012

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 22a59c01c00cf9fbefaee0e8e67fab82bbaf1fd2`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the one unchanged callee modeled as a free input.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `groupingColumns (selfCol, innerHasAggregate, innerCols, innerColsDefaultContext)` | the `get_group_by_cols(self, alias=None)` method of the transparent wrapping expression class `ExpressionWrapper` — `django/db/models/expressions.py:850` (class), method ADDED post-patch at line 866 | the modeled changed function: which grouping columns a wrapping expression contributes |
| `selfCol : GroupCol` | `self` (the `ExpressionWrapper` instance) viewed as a candidate grouping column | the wrapping expression's own identity |
| `innerCols : List GroupCol` *(free input)* | `self.expression.get_group_by_cols(alias=alias)` — the wrapped inner expression's grouping columns for the **requested** context `alias` (`get_source_expressions` returns `[self.expression]`, `expressions.py:863`) | the delegated, unchanged observation (directive 7 free input) |
| `innerColsDefaultContext : List GroupCol` *(free input)* | `self.expression.get_group_by_cols()` — the wrapped inner expression's grouping columns when the context `alias` is **not forwarded** (the default-arg call the inherited base method makes) | a second free observation, used only by the pre-patch skeleton |
| `innerHasAggregate : Bool` *(free input)* | `self.contains_aggregate` (`expressions.py:221`) — whether the wrapped expression tree aggregates | a free observation the inherited base method branches on |

The wrapping-expression class `ExpressionWrapper` provides extra context (an
`output_field`) to the inner expression but is **not itself a database column**;
it is transparent for grouping. Pre-patch it had no dedicated grouping method, so
it inherited the generic rule (`BaseExpression.get_group_by_cols`,
`expressions.py:350`): a non-aggregating expression returns `[self]`, an
aggregating one returns the columns its sources contribute, queried WITHOUT
forwarding `alias`. Both branches differ from the desired transparent delegation.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an expression that may appear as a GROUP BY column (its **identity** is what a grouping clause de-duplicates on) | `GroupCol` (opaque `structure`, `DecidableEq`) | a distinct expression object ↔ a distinct `GroupCol`; object identity (`a is b`) ↔ `GroupCol` equality. Internal content is never inspected. |
| `list` of grouping columns returned by `get_group_by_cols` | `List GroupCol` | Python `list` ↔ Lean `List`; order and length preserved; element-wise identity bijection above |
| `alias=None` / `alias='...'` requested grouping context | (carried implicitly: `innerCols` is the inner's columns *for that context*) | the SAME `alias` is forwarded on both sides; the model pins that the requested context is preserved by returning `innerCols` (the inner's columns for that context), never `innerColsDefaultContext` |
| `self.contains_aggregate` | `Bool` | `True ↔ true`, `False ↔ false` |

`get_group_by_cols` returns the actual expression objects; downstream GROUP BY
construction de-duplicates by identity/equality. Hence G-CONF compares the
contributed columns by **object identity** (`id(c)`), which is exactly what the
`GroupCol` abstraction (identity-only, `DecidableEq`) models.

## 3. Callee provenance — the one delegated step is a FREE input (directive 7)

There is **no `axiom`** and **no deep-model reference** in this bundle. The single
unchanged step the operation delegates to is `self.expression.get_group_by_cols(
alias=alias)` — the wrapped inner expression deciding its own grouping columns.
Its result is modeled as the FREE input `innerCols`: the postcondition
`out = innerCols` holds for EVERY value of that input, so the callee is owed no
contract (it is strictly weaker than any concrete implementation of the delegated
step). This is the directive-7-correct treatment of an unchanged callee that the
fix merely *forwards to*: there is nothing to axiomatize, hence no G-AX.

The behaviour the bundle pins is not a property of that callee but of the
**caller**: that the wrapping expression returns exactly what the callee returns
for the same context, rather than substituting its own identity (the base
`[self]` rule) or dropping the requested context (the base aggregate rule). That
is a structural relation between `out` and the free input, dischargeable only by
the delegating branch — not by echoing an oracle (directive 8).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13012`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`groupingColumns` (`out = innerCols`) to Python and derives `innerCols` exactly
as the gold delegation does — `inner.get_group_by_cols(alias=alias)` — then
compares by object identity against the real patched
`ExpressionWrapper.get_group_by_cols(alias=alias)` over the F2P matrix
(constant/aggregate/transform inner expressions × requested contexts) plus
10⁵ fuzzed inner-expression/context pairs.
