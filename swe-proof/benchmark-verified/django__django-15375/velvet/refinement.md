# refinement.md — django__django-15375

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`prepareAggregate` `do` block, plus the `prepared`/`Resolved` pure model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/deep-modeled callee — none in this bundle), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4);
the unchanged-callee facts the direct model depends on are audited by **G-AX**
(`axiom_check.py`) against the real Django objects; the narrative is audited by
**G-EQ**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The marker-propagating fallback wrapper — `Aggregate.resolve_expression`

Gold hunk (`django/db/models/aggregates.py`, the `default` branch):
```
         c.default = None  # Reset the default argument before wrapping.
-        return Coalesce(c, default, output_field=c._output_field_or_none)
+        coalesce = Coalesce(c, default, output_field=c._output_field_or_none)
+        coalesce.is_summary = c.is_summary
+        return coalesce
```

The function: resolves the aggregate to `c` (base resolution sets
`c.is_summary = summarize`), and — when a `default` is supplied — returns a
`Coalesce(c, default)` fallback wrapper instead of the bare aggregate. The fix
copies the terminal marker onto that wrapper (`coalesce.is_summary = c.is_summary`).

| # | Solution.lean impl op (`prepareAggregate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `terminal : Bool` | the `summarize` arg of `resolve_expression` | R | `bool` ↔ `Bool` (mapping.md §2). `super().resolve_expression(..., summarize)` sets `c.is_summary = summarize` — the marker the wrapper must carry. G-AX §3.1 confirms `c.is_summary == summarize` for the unchanged base resolution. |
| A2 | parameter `defaultVal : Option Int` | the `default=` keyword argument | R | `None` ↔ `none`, any supplied value ↔ `some n` (mapping.md §2). Only **presence** is observable in the prepared clause's shape; the value content flows unchanged into the wrapper's fallback slot (I, see A5). `Int` is a concrete fuzzable carrier for the value. |
| A3 | `if defaultVal.isSome then … else …` | `if (default := c.default) is None: return c` (the branch on whether a fallback is supplied) | I | the same two-way branch on fallback presence; the `else` arm is the bare aggregation, the `then` arm the fallback form. (The model returns the bare clause in the `else`; the gold returns `c` directly at the earlier `return c`.) |
| A4 | `else` arm: `{ isTerminal := terminal, hasFallback := false }` | `return c` (no `default`) | R + I | the bare resolved aggregation carries the terminal marker `c.is_summary == summarize` (G-AX §3.1) and is not a fallback wrapper. `isTerminal := terminal` ↔ `c.is_summary`; `hasFallback := false` ↔ `not isinstance(c, Coalesce)`. |
| A5 | `then` arm: `{ isTerminal := terminal, hasFallback := true }` | `coalesce = Coalesce(c, default, …); coalesce.is_summary = c.is_summary; return coalesce` | R + I | the fallback form. **R:** `hasFallback := true` ↔ `isinstance(result, Coalesce)`; `isTerminal := terminal` ↔ `result.is_summary`. The model sets `isTerminal := terminal` (i.e. `= c.is_summary`), which is EXACTLY the propagation `coalesce.is_summary = c.is_summary` the fix adds. **I:** wrapping the aggregate and its default into the fallback form is a concrete transliterated op (the default value content is carried through unchanged). |

Discriminating content of the change — the fallback form MUST carry the same
terminal marker the bare aggregation carries — lives in the model's
`then`-arm `isTerminal := terminal` (⇔ `coalesce.is_summary = c.is_summary`).
The pre-patch built the wrapper without propagating the marker, so it inherited
the class default `False`; `Solution_prepatch.lean` reproduces that
(`isTerminal := false` in the fallback arm) and **fails** the postcondition
`out.isTerminal = terminal` (G-DIFF) on the `some` case.

## B. Single site, one independently-observable behaviour

The gold patch touches a single function in a single branch. There is one
independently-observable fixed behaviour — a top-level aggregation with a
fallback retains its terminal marker (so the query builder places it at the
outer level, producing valid SQL) — exercised by the F2P test
`test_aggregation_default_after_annotation`. (The companion test added in the
test_patch, `test_aggregation_default_not_in_aggregate`, exercises the same code
path from the orthogonal direction and is in PASS_TO_PASS terms covered by the
same fix.) One failing prepatch suffices.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — propagating the
terminal marker onto the fallback wrapper — is modeled **directly**
(`Resolved.isTerminal` carried into the fallback arm, A5), not hidden behind an
axiom about the function under change or any unchanged callee. There is **no
consumed axiom and no deep-model reference** (`axioms` region empty). The two
unchanged-callee facts the direct model relies on (base resolution sets
`is_summary == summarize`, §3.1; a freshly built `Coalesce` defaults to `False`,
§3.2) are executable-checked against real Django by G-AX.

## D. verify(Solution) ⇒ resolved

`prepareAggregate` verifies only if (i) its output equals `prepared terminal
defaultVal`, (ii) `out.isTerminal = terminal` for BOTH branches — in particular
the fallback (`some`) branch, which is the bug — and (iii) `out.hasFallback =
defaultVal.isSome`. By R (`summarize ↔ terminal`, `default ↔ Option`,
`is_summary ↔ isTerminal`, `isinstance Coalesce ↔ hasFallback`) the verified
function equals the patched `Aggregate.resolve_expression`'s observable on the
tested inputs; by G-AX the base marker really is `summarize` and a bare wrapper
really defaults to `False` (so the propagation is load-bearing, not vacuous); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed inputs across the full `terminal × fallback` grid. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). Trust points: refinement
fidelity (this doc, G-EQ + G-CONF) and the executable callee-fact audit (G-AX);
there are no axioms to trust.
