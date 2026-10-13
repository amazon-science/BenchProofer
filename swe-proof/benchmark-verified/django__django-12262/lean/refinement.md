# refinement.md — django__django-12262

Maps every op in `implementation_parseTagArgs` to its `patch.diff` / real
`parse_bits` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom property), **A-reference** (deep-model boundary op validated ==
real callee by G-AX/G-CONF), **I** (identical concrete op).

| # | Lean impl op | Python `parse_bits` op | tag | note |
|---|---|---|---|---|
| 1 | `let mut params := params` | `params` local | I | |
| 2 | `if takesContext then match params …` context check + `params := rest` / `Except.error (msgContext name)` / `Except.error msgIndexError` on empty `params` | `if takes_context: if params[0]=='context': params=params[1:] else raise TemplateSyntaxError(…)` — on EMPTY `params`, `params[0]` raises an uncaught `IndexError` | I/R | R: the empty-`params` crash is modeled as its OWN failure value `msgIndexError` ("IndexError: list index out of range"), distinct from the `msgContext` diagnostic, so the model is faithful on every input: uncaught IndexError ↔ `Except.error msgIndexError` (mapping.md bridge); non-`context` first param ↔ the context diagnostic. G-CONF exercises both branches. |
| 3 | `BindState.pendingPositional := params` | `unhandled_params = list(params)` | I | |
| 4 | `BindState.pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults` | `unhandled_kwargs = [k for k in kwonly if not kwonly_defaults or k not in kwonly_defaults]` | I | `requiredKeywordOnly` is exactly this comprehension |
| 5 | `for tok in toks do match tok …` | `for bit in bits:` + `kwarg = token_kwargs([bit], parser)` classification | A-reference | the lexical `token_kwargs`/`compile_filter` classification is the input bridge (mapping.md); G-CONF drives the real callees |
| 6 | keyword guard `¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword` → `msgUnexpectedKeyword` | **patched** `if param not in params and param not in kwonly and varkw is None: raise "… unexpected keyword argument …"` | I | THE FIX. (Pre-patch uses `pendingKeyword`/`unhandled_kwargs`.) |
| 7 | `else if st.kwargs.any (·.1 == param)` → `msgMultipleValues` | `elif param in kwargs: raise "… multiple values …"` | I | `kwargs` membership ↔ key present in ordered assoc list |
| 8 | `st.kwargs := st.kwargs ++ [(param, value)]` | `kwargs[str(param)] = value` | R | dict ↔ ordered unique-key assoc list; key never re-added (guard 7) so append is faithful |
| 9 | `if st.pendingPositional.contains param then erase` `else if st.pendingKeyword.contains param then erase` | `if param in unhandled_params: unhandled_params.remove(param) elif param in unhandled_kwargs: unhandled_kwargs.remove(param)` | I | `List.erase` removes first occurrence ↔ `list.remove` |
| 10 | positional `if ¬ st.kwargs.isEmpty then msgPositionalAfterKeyword` | `else: if kwargs: raise "… positional … after … keyword …"` | I | |
| 11 | `st.args := st.args ++ [value]` | `args.append(parser.compile_filter(bit))` | A-reference | value compiled by real `compile_filter` (boundary); only args LENGTH observed |
| 12 | `match st.pendingPositional with [] => if ¬ hasVarArgs then msgTooManyPositional / _::rest => pop` | `try: unhandled_params.pop(0) except IndexError: if varargs is None: raise "… too many positional …"` | I | |
| 13 | `finalizeBind defaults name st`: `some 0 → pending = []`; `some n (n>0)` drops trailing `n` positional via `take (len - n)`; then `if pending ∨ pendingKeyword nonempty → msgMissing` | `if defaults is not None: unhandled_params = unhandled_params[:-len(defaults)]` then `if unhandled_params or unhandled_kwargs: raise "… did not receive value(s) …"` | I | `take (len-n)` ↔ `[:-n]` for `1 ≤ n ≤ len`; the `n = 0` case is Python's negative-slice quirk `[:-0]==[:0]==[]` (drops ALL pending) and is modeled EXACTLY (`some 0 → []`); missing list ordered `unhandled_params ++ unhandled_kwargs` |
| 14 | `Except.ok (st.args, st.kwargs)` | `return args, kwargs` | R | per row 8/11 |

No row is changed-inexpressible. No A-consumed axiom (the proof needs no callee
property). The only A-reference rows (5, 11) are the boundary lexical/compile
callees, exercised against the real implementation by G-CONF.
