# mapping.md — django__django-11603

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f618e033acd37d59b536d6e6126e6c5be18037f6`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the modeled construction guard. There are **no axioms** in this
bundle, so G-AX is not exercised.

Repo file under change: `django/db/models/aggregates.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `avgInit (distinct : Bool)` | constructing the averaging aggregate class (`django/db/models/aggregates.py:99`) via the shared `Aggregate.__init__` (`aggregates.py:24`) | one modeled changed behaviour: averaging aggregate accepts the duplicate-elimination option |
| `sumInit (distinct : Bool)` | constructing the summing aggregate class (`django/db/models/aggregates.py:142`) via the shared `Aggregate.__init__` (`aggregates.py:24`) | the second, independently-fixed modeled behaviour: summing aggregate accepts the duplicate-elimination option |
| `construct (function) (acceptsDistinct) (distinct)` *(deep model, pure region)* | the shared construction guard `Aggregate.__init__` (`aggregates.py:24-29`): `if distinct and not self.allow_distinct: raise TypeError(...)`, then `self.distinct = distinct` | pure spec of the guard + the recorded option; the per-kind capability `acceptsDistinct` models the class attribute `allow_distinct` |
| `AggState { function, distinct }` | the touched fields of the constructed aggregate object: its SQL `function` name and its recorded `self.distinct` | the observable content (mapping.md §2) |
| `InitErr.distinctNotAccepted` | the `TypeError("%s does not allow distinct." ...)` raised by the guard | the one distinguished failure outcome |

The gold patch's actual edit is the per-class capability datum: each of the two
classes gains `allow_distinct = True` (overriding the base-class default
`allow_distinct = False` at `aggregates.py:22`). In the model this is the
`acceptsDistinct := true` step in each method's impl region; the prepatch
variants restore the inherited `false` to exhibit the pre-fix behaviour.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `distinct` keyword argument (a `bool`) | `Bool` | identity: `True ↔ true`, `False ↔ false` |
| the constructed aggregate object | `AggState` | only the two touched fields are modeled: `agg.function` (a `str`) ↔ `AggState.function : String`; `bool(agg.distinct)` ↔ `AggState.distinct : Bool`. All other fields (`filter`, `source_expressions`, `output_field`, …) are orthogonal to the guarded behaviour and omitted. |
| the SQL function name `agg.function` | `String` | `"AVG" ↔ "AVG"`, `"SUM" ↔ "SUM"` (class attribute `function`) |
| `Aggregate.__init__` raising `TypeError("… does not allow distinct.")` | `Except.error InitErr.distinctNotAccepted` | a refused construction ↔ the error variant |
| a successful `cls(expr, distinct=d)` build | `Except.ok { function, distinct := d }` | a built object whose recorded flag equals the request ↔ the ok variant |
| the class attribute `allow_distinct` | the `acceptsDistinct` argument of `construct` (concrete `Bool`) | `True ↔ true`. For the two modeled kinds the patch sets it `true`; the base default is `false`. |
| the wrapped source expression `*expressions` / `super().__init__` | omitted (R: identity) | the guard's outcome is independent of the source expression; G-CONF passes a fixed field name `"a_field"` and observes only `function`/`distinct`. |

The input space is finite and total (`function ∈ {AVG, SUM} × distinct ∈
{false, true}`), so G-CONF enumerates the full cross product and then re-samples
to exceed the §4.1 fuzz floor deterministically. No partial/undefined inputs;
no `require` clause is needed.

## 3. Callee provenance (kind-A)

**None.** This bundle consumes no axioms and has no `:|` imperative-callee
stubs. The only behaviour under spec — the construction guard and the per-kind
capability it consults — is modeled **deeply** in the `pure` region
(`construct` + the concrete `acceptsDistinct` flag) and is fully transliterable
to Python, so it is validated end-to-end by G-CONF against the real patched
classes rather than by any axiom. `axiom_check.py` is therefore absent and G-AX
is skipped (gates.py `gate_ax` returns `skip` when no `axiom_check.py` exists).

The `super().__init__(*expressions, **extra)` call the guard makes after
recording the flag (expression parsing, `output_field` handling) is an
**unchanged** orthogonal callee whose outcome does not affect the guarded
behaviour; it is abstracted away as an R-identity (mapping.md §2), not
axiomatized.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11603`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`construct`/`avgInit`/`sumInit` (all R/I ops; there are no A-tagged callees in
the impl region) to Python and observes the real patched `Avg`/`Sum`
constructors as the oracle (the gold patch is git-applied by the gate harness
before the script runs).
