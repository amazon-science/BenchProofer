# refinement.md — django__django-12262

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`bindTagArguments` `do` block + the deep `stepBit` / `finalize` / `parseBits`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I; no kind-3 (changed inexpressible op).

There are **NO axioms** in this bundle: the two callees the per-bit scan consults
(`token_kwargs([bit], parser)` and `parser.compile_filter(bit)`) are UNCHANGED
and folded into the free input `bits : List Bit` (mapping.md §2/§3), so no row is
A-consumed or A-reference, and G-AX is `skip`. The whole impl region is R/I,
mechanically refuted by **G-CONF** (`conformance_check.py`); the narrative below
is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — `parse_bits`'s per-bit binding loop (`django/template/library.py:264`)

Gold hunk (the single changed line):
```
-            if param not in params and param not in unhandled_kwargs and varkw is None:
+            if param not in params and param not in kwonly and varkw is None:
```

The fix swaps the unexpected-keyword admissibility test from the MUTATING
`unhandled_kwargs` (keyword-only params still pending a value) to the CONSTANT
`kwonly` (the full set of declared keyword-only param names).

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | seed `initState pos kwonly kwdef = {recorded=[], pendingPositional=pos, pendingKeywordOnly=(kwonly.filter ∉ kwdef), error=none}` | `args=[]; kwargs={}; unhandled_params=list(params); unhandled_kwargs=[k for k in kwonly if not kwonly_defaults or k not in kwonly_defaults]` (loop pre-state) | R | `kwargs` keys ↔ `recorded`, `unhandled_params` ↔ `pendingPositional`, `unhandled_kwargs` ↔ `pendingKeywordOnly`. mapping.md §2. The unchanged `takes_context` stripping (`:245-253`) is folded into the input `positionalParams` (mapping.md §4). |
| 2 | `while i < bits.length … st := stepBit … st bits[i]!` (forward fold of `stepBit` over `bits`) | `for bit in bits:` body | I | one loop iteration per bit; the `take`-fold computes the same `foldl`. `walk`-style `scan_take_step` lemma is the per-step unfold. |
| 3 | `match bit with \| .keyword p => …` (the bit was classified a keyword) | `kwarg = token_kwargs([bit], parser); if kwarg: param, value = kwarg.popitem()` | R | `token_kwargs` returning a 1-entry dict ⇔ `keyword p`; UNCHANGED callee, folded into the input bit classification (mapping.md §3). The kwarg `value` is dropped (no decision reads it). |
| 4 | **`if !positionalParams.contains p && !keywordOnlyParams.contains p && !acceptsExtraKeywords then error := unexpectedKeyword p`** | **`if param not in params and param not in kwonly and varkw is None: raise …unexpected keyword argument`** | R | **the fixed line.** `params` ↔ `positionalParams`, **`kwonly` ↔ `keywordOnlyParams` (the constant full declared set)**, `varkw is None` ↔ `!acceptsExtraKeywords`. The buggy pre-image tested `unhandled_kwargs` ↔ `pendingKeywordOnly` (the mutating set) — see G-DIFF below. |
| 5 | `else if st.recorded.contains p then error := duplicateKeyword p` | `elif param in kwargs: raise …multiple values for keyword argument` | R + I | `param in kwargs` ↔ `recorded.contains p`. Unchanged; carried so the fix's second observable effect (a 2nd supply of an admissible keyword now reaches THIS branch) is part of the frozen spec. |
| 6 | `else { recorded := recorded ++ [p]; if pendingPositional.contains p then erase from pendingPositional else if pendingKeywordOnly.contains p then erase from pendingKeywordOnly }` | `else: kwargs[str(param)] = value; if param in unhandled_params: unhandled_params.remove(param); elif param in unhandled_kwargs: unhandled_kwargs.remove(param)` | R + I | recording + consuming the matched pending parameter. `list.remove(x)` (first occurrence) ↔ `List.erase`; param names are distinct in these lists so first-occurrence vs all-occurrence is immaterial. Unchanged. |
| 7 | `\| .positional => if !recorded.isEmpty then error := positionalAfterKeyword` | `else: if kwargs: raise …positional argument(s) after some keyword argument(s)` | R + I | a positional after any keyword recorded. `kwargs` non-empty ↔ `!recorded.isEmpty`. Unchanged. |
| 8 | `else match pendingPositional with \| [] => if acceptsExtraPositional then st else error := tooManyPositional \| _::rest => pendingPositional := rest` | `else: args.append(parser.compile_filter(bit)); try: unhandled_params.pop(0) except IndexError: if varargs is None: raise …too many positional arguments` | R + I | consume next pending positional (`pop(0)`) or, when none left and no `*args`, too many. `compile_filter` (UNCHANGED) only builds the stored value, irrelevant to the decision (mapping.md §3); `args` list dropped. `varargs is None` ↔ `!acceptsExtraPositional`. |
| 9 | `finalize st hasDefaults numDefaults`: if error then it; else `leftover := if hasDefaults then pendingPositional.take (len - numDefaults) else pendingPositional; missing := leftover ++ pendingKeywordOnly; if missing.isEmpty then none else missingArguments missing` | `if defaults is not None: unhandled_params = unhandled_params[:-len(defaults)]; if unhandled_params or unhandled_kwargs: raise …did not receive value(s) for the argument(s): …` | R + I | the final missing-argument check. `unhandled_params[:-n]` ↔ `pendingPositional.take (len - n)`. Unchanged by the patch but in scope because the FIX changes which keyword-only params remain in `unhandled_kwargs`/`pendingKeywordOnly` at this point (a keyword-only-with-default supplied once must NOT be reported missing — see G-DIFF). |
| 10 | `return out` = the `Option Err` | function raises the first `TemplateSyntaxError`, else returns `(args, kwargs)` | R | the modeled observable is *which error (if any) is raised* — exactly what the F2P tests assert (the exact error string ↔ the `Err` constructor + name; success ↔ `none`). mapping.md §2. |

### Why the spec sees the bug (G-DIFF)

`Solution_prepatch.lean` inlines `stepBit` with row 4's test reading
`st.pendingKeywordOnly` (the mutating set) instead of `keywordOnlyParams` (the
full declared set) — the literal pre-patch line `param not in unhandled_kwargs`.
This diverges from the frozen spec on the two behaviors the issue names:

- **keyword-only WITH a default** (`def hello(*, greeting='hi')`, `{% hello
  greeting='hi' %}`): `greeting` is in `kwonly` but, carrying a default, is NEVER
  in `unhandled_kwargs`/`pendingKeywordOnly`. The buggy test fires →
  `unexpectedKeyword`. The frozen `stepBit` tests `keywordOnlyParams` (contains
  `greeting`) → no error, the keyword is recorded. The loop-body invariant
  `st = (take …).foldl stepBit …` is then unprovable → `prove_correct` fails.
- **keyword-only supplied twice** (`{% hi greeting='hi' greeting='hello' %}`):
  the first supply removes `greeting` from `pendingKeywordOnly`; on the second
  bit the buggy test fires `unexpectedKeyword` instead of falling through to the
  `duplicateKeyword` branch (row 5). The frozen `stepBit` keeps `greeting` in
  `keywordOnlyParams`, so the second bit reaches `recorded.contains` →
  `duplicateKeyword`. Again the invariant diverges → `prove_correct` fails.

Both fixed behaviors flow from the single changed line and the single modeled
function, so ONE `Solution_prepatch.lean` carries them (one independently-fixed
behavior — the admissibility set — with two observable manifestations). It fails
on the `stepBit` loop-body clause, the discriminating content of the bug.

## No kind-3

Every changed op is expressible: the patch reroutes one membership test from a
mutating list to a constant list over abstracted name lists. Nothing
inexpressible; no BLOCKED.
