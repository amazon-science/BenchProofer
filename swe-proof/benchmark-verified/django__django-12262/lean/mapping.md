# mapping.md — django__django-12262

## Symbol binding (base_commit 69331bb851c34f05bc77e9fc24020fe6908b9cd5)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_parseTagArgs` / `problem_spec_parseTagArgs` / `parseTagArgsRef` | `parse_bits(parser, bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults, takes_context, name)` | `django/template/library.py:237-309` |

The changed function is `parse_bits`. The fix is one line (library.py:264):
`if param not in params and param not in unhandled_kwargs and varkw is None:`
becomes
`if param not in params and param not in kwonly and varkw is None:`.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python (parse_bits) | Lean | bridge |
|---|---|---|
| `params` (list[str], declared positional names; first may be `'context'`) | `params : List String` | identity (ordered) |
| `varargs` (str name or `None`) | `hasVarArgs : Bool` | `hasVarArgs ↔ varargs is not None` |
| `varkw` (str name or `None`) | `hasVarKeyword : Bool` | `hasVarKeyword ↔ varkw is not None` |
| `defaults` (tuple of default values or `None`) | `defaults : Option Nat` | `none ↔ None`; `some n ↔ a tuple of length n`, INCLUDING `some 0 ↔ ()` (only the COUNT is observed — `unhandled_params[:-len(defaults)]`; the `len == 0` case is the negative-slice quirk `[:-0]==[:0]==[]`, modeled exactly by `some 0 → pending = []`) |
| `kwonly` (list[str], all keyword-only names) | `keywordOnly : List String` | identity (ordered) |
| `kwonly_defaults` (dict name→default, or `None`/falsey) | `keywordDefaults : Option (List String)` | `none ↔ None/empty`; `some ks ↔ a dict whose key-set is ks` (only membership is observed by `kwarg not in kwonly_defaults`) |
| `takes_context` (bool/None) | `takesContext : Bool` | truthiness |
| `name` (str) | `name : String` | identity |
| `bits` (list[str] raw token strings) | `toks : List Tok` | **I/O bridge (lexical, boundary):** each raw bit is classified by `token_kwargs([bit], parser)`. A bit of form `k=v` (matching `kwarg_re`) → `Tok.keyword k v'`; any other bit → `Tok.positional bit`. The conformance harness renders `Tok.keyword k v` as the bit string `"k=v"` and `Tok.positional s` as the bit string `s`, then feeds the REAL `parse_bits`, so the real `token_kwargs`/`compile_filter` perform the classification — validating this bridge as an A-reference (boundary op), not an axiom. |
| return `(args, kwargs)` (lists/dicts of compiled `FilterExpression`) | `Except String (List String × List (String × String))` | success → `Except.ok (argValues, kwargPairs)`; raised `TemplateSyntaxError(msg)` → `Except.error msg`; the uncaught `IndexError` raised by `params[0]` when `takes_context` is set and `params` is empty → `Except.error "IndexError: list index out of range"` (a dedicated failure value distinct from every template diagnostic, so the crash mode is modeled, not conflated). Compiled values are opaque at the boundary, so G-CONF compares the **kwargs key sequence (ordered)**, the **args length**, and the **exact error text** — everything `parse_bits` itself decides. |

## `unhandled_kwargs` (the buggy quantity) ↔ Lean

`parse_bits` computes `unhandled_kwargs = [k for k in kwonly if not kwonly_defaults or k not in kwonly_defaults]`
— the keyword-only names that still REQUIRE a value (those without a default). It
mutates this list as values arrive. Lean models the initial list as
`requiredKeywordOnly keywordOnly keywordDefaults` and threads its remainder as
`BindState.pendingKeyword`. The pre-patch bug (Solution_prepatch.lean) tests
membership of the supplied name against this `pendingKeyword` list (the analog of
`unhandled_kwargs`) in the unexpected-keyword guard; the fix tests against the
full `keywordOnly` list instead.

## Callee provenance + flag deps

- `token_kwargs`, `parser.compile_filter` — UNCHANGED boundary callees. Folded
  into the `Tok` input encoding (the lexical/compile step). Validated as the
  A-reference bridge by G-CONF (the harness drives the real callees), NOT
  axiomatized. No flag dependence relevant to the fix.
- No callee requires a consumed `_prop` axiom: every decision the function makes
  is modeled directly in `implementation_parseTagArgs`.

## G-CONF fuzz seed

Pinned seed: **12262** (see conformance_check.py `random.Random(12262)`).
