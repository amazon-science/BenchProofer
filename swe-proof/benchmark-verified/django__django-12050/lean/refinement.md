# refinement.md — django__django-12050

Maps every operation in `implementation_resolveLookupValue` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `resolveLookupValue` (`Query.resolve_lookup_value`)

Post-patch repo code (`patch.diff`):
```python
def resolve_lookup_value(self, value, can_reuse, allow_joins, simple_col):
    if hasattr(value, 'resolve_expression'):
        kwargs = {'reuse': can_reuse, 'allow_joins': allow_joins}
        if isinstance(value, F):
            kwargs['simple_col'] = simple_col
        value = value.resolve_expression(self, **kwargs)
    elif isinstance(value, (list, tuple)):
        # The items of the iterable may be expressions and therefore need
        # to be resolved independently.
        return type(value)(
            self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col)
            for sub_value in value
        )
    return value
```

Lean impl (`implementation_resolveLookupValue`):
```lean
def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.lst resolved
  | LV.tup xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.tup resolved
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `\| LV.expr e => resolveExpression e` | `if hasattr(value, 'resolve_expression'): … value = value.resolve_expression(self, **kwargs); return value` | **A-reference** (opaque, NO consumed property) | the expression branch (UNCHANGED by the patch). `LV.expr` ↔ a value carrying `resolve_expression`; `resolveExpression` ↔ the real `value.resolve_expression(...)` callee. The `kwargs`/`F`/`simple_col` keyword-selection is folded into the opaque callee (mapping.md): it picks which kwargs the callee receives, not the dispatch or the rebuilt container, so it is unobservable in the modeled behavior. The proof consumes NO property of it (it appears IDENTICALLY in `resolveSpec` and `implementation_resolveLookupValue`, so it cancels): there is no `axiom resolveExpression_prop`, hence G-AX is a skip (nothing to validate). G-CONF stubs it identically on both legs so it cancels there too. |
| 2 | `\| LV.plain n => LV.plain n` | the trailing `return value` for a `value` that is neither an expression nor a `list`/`tuple` | **I** | the scalar fall-through; the value is returned unchanged. |
| 3 | `\| LV.lst xs => Id.run do … return LV.lst resolved` | `elif isinstance(value, (list, tuple)): return type(value)(... for sub_value in value)` with `value` a `list` | **R** | the changed branch, list case. `type(value)(...)` for a `list` rebuilds a `list` ↔ `LV.lst`. The generator-comprehension `for sub_value in value` ↔ the `for sub in xs` accumulator loop preserving order/arity. |
| 4 | `\| LV.tup xs => Id.run do … return LV.tup resolved` | same branch with `value` a `tuple` | **R** | `type(value)(...)` for a `tuple` rebuilds a `tuple` ↔ `LV.tup`. Same loop structure. |
| 5 | `resolved := resolved ++ [implementation_resolveLookupValue sub]` | `self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col)` | **R** (recursive self-call) | each element is resolved by RE-ENTERING the full dispatch — the recursive `self.resolve_lookup_value(...)` ↔ the recursive `implementation_resolveLookupValue sub`. This is what makes a nested `list`/`tuple` keep its own kind and an expression element get resolved. `can_reuse/allow_joins/simple_col` are threaded into the recursive call unchanged; absorbed into `resolveExpression` at the leaves (mapping.md). |
| 6 | `return LV.lst resolved` / `return LV.tup resolved` | the value returned by `type(value)(generator)` | **R** | the rebuilt collection of resolved entries, same kind as the input. |

The impl region mixes **R/I** ops with ONE **A-reference** (the expression
branch's `resolveExpression`). It is NOT all-A-tagged: `conf_skip = false`, and
`conformance_check.py` mechanically differential-tests the R/I shadow against an
in-process replica of the patched `resolve_lookup_value` (`type(value)(...)`
recursion), with the `expr`-leaf resolution stubbed identically on both legs so
the A-reference cancels and only the R/I container/recursion behavior is tested.

## Soundness check (verify ⟹ correct)

- `problem_spec_resolveLookupValue value result := result = resolveSpec value`
  pins the result EXACTLY (full structural equality to an input-grounded
  expression), directive 5 (frame): the result's kind, the result collection's
  kind/arity/order, and each entry's resolution are all determined by the input
  `value` and `resolveSpec`. No output component is unconstrained; no ungrounded
  oracle (directive 8) — `resolveSpec` is a concrete recursive function over the
  actual input `LV` tree (NOT an axiomatized answer-key); its only opaque leaf is
  `resolveExpression`, which the impl invokes IDENTICALLY (so the spec is
  dischargeable only by actually performing the same recursion). The crucial
  clauses: `LV.lst xs ↦ LV.lst (xs.map resolveSpec)` (a list stays a list) and the
  recursion through `resolveSpec` (a nested entry keeps its kind), both of which a
  tuple-coercing or non-recursive impl violates.
- The prepatch impl reproduces the PRE-FIX bug TWICE over: (a) it emits `LV.tup`
  for BOTH the list and tuple branches (`value = tuple(resolved_values)` —
  always a tuple), and (b) it resolves each element in a single non-recursive
  pass (only `expr` elements are resolved; a nested `lst`/`tup` element is left
  verbatim, never re-entering the collection rule). It violates the spec on the
  discriminating clause `LV.lst xs` with any `xs`: the spec requires `LV.lst (…)`
  but the prepatch returns `LV.tup (…)` — different constructors, so the equality
  in `problem_spec` is unprovable. (A second discriminator: `LV.lst [LV.lst []]`
  — the prepatch leaves the inner `LV.lst []` unresolved AND wraps the outer in a
  tuple.) Its carried proof cannot close (G-DIFF/G-PANEL); the failing case is the
  top-level list branch.
- This discriminating case is precisely the FAIL_TO_PASS assertion added by the
  test patch: `Query(Item).build_where(Q(name=['a', 'b']))` keeps the right-hand
  side as `"['a', 'b']"` (a list repr), where the pre-fix code rendered it as the
  coerced tuple `"('a', 'b')"`. The PASS_TO_PASS cases (scalar / expression
  values) are unaffected: a non-collection value flows through the `expr`/`plain`
  branches identically pre- and post-fix.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `resolve_lookup_value` over hand-picked edge cases (top-level list, top-level
  tuple, nested list-in-tuple / tuple-in-list, list/tuple of expressions, empty
  list, empty tuple, bare scalar) plus ≥1e5 fuzzed `LV` trees.
