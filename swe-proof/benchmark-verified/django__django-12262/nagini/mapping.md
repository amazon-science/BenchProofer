# mapping.md — django__django-12262

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 69331bb851c34f05bc77e9fc24020fe6908b9cd5`, states the type
abstraction, and documents callee provenance.

Repo file under change: `django/template/library.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bind_keywords(supplied, positional, keyword_only, keyword_only_with_default, catch_all)` | `parse_bits(parser, bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults, takes_context, name)` — `django/template/library.py:237` (the keyword-handling branch, body lines 258-283) | the modeled changed function (custom-tag argument binder), reduced to its keyword-binding decision |
| `outcome(supplied, seen, positional, keyword_only, catch_all)` | the `for bit in bits:` keyword loop body, `django/template/library.py:258-283` (post-patch) | pure spec / deep model: the outcome of the keyword loop (OK / UNEXPECTED / DUPLICATE), as a front-recursive fold |
| `acceptable(positional, keyword_only, catch_all, name)` | the *fixed* condition `param not in params and param not in kwonly and varkw is None` (`library.py:264`, post-patch) | pure spec: whether a supplied keyword is acceptable (negation of the UNEXPECTED guard) |
| `contains(s, x)` | Python `in` membership on the `params` / `kwonly` / recorded-`kwargs` lists | pure spec: list membership |

The changed line (the entire patch):
```
- if param not in params and param not in unhandled_kwargs and varkw is None:
+ if param not in params and param not in kwonly and varkw is None:
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `bits` — the token list, each element a successfully-extracted keyword (the `if kwarg:` branch) identified by a parameter *name* string | `supplied: List[int]` of parameter-name codes | each repo string parameter-name ↔ a distinct `int` code; an element of `bits` that `token_kwargs` extracts as a kwarg ↔ that element's `param` code. (Positional bits — the `else` branch — are orthogonal to the changed line and are not part of the modeled decision; see §3.) |
| `params` (positional parameter names, a `list`) | `positional: PSeq[int]` | string name ↔ int code; `param in params` ↔ `contains(positional, name)` |
| `kwonly` (keyword-only parameter names, a `list`) | `keyword_only: PSeq[int]` | string name ↔ int code; `param in kwonly` ↔ `contains(keyword_only, name)` |
| `kwonly_defaults` (the keyword-only names carrying a default; a dict or `None`) | `keyword_only_with_default: PSeq[int]` | the set of names with defaults ↔ the sequence's membership; `not kwonly_defaults or k not in kwonly_defaults` (the `unhandled_kwargs` comprehension, `library.py:254-257`) ↔ `contains(keyword_only, k) and not contains(keyword_only_with_default, k)`. Used ONLY by the pre-patch skeleton (`model_prepatch.py`); the fixed decision ignores it. |
| `varkw is None` (no `**kwargs` catch-all) | `catch_all: bool` = `varkw is not None` | `varkw is None` ↔ `not catch_all`; the UNEXPECTED guard requires `varkw is None`, i.e. `not catch_all` |
| `kwargs` dict keys (recorded keyword args so far) | `seen: PSeq[int]` accumulator | `param in kwargs` ↔ `contains(seen, name)`; recording a kwarg ↔ `seen + PSeq(name)` |
| raise `TemplateSyntaxError("…unexpected keyword argument…")` | `outcome` / `Result()` == 1 | the UNEXPECTED control-flow outcome, as an integer code |
| raise `TemplateSyntaxError("…multiple values for keyword argument…")` | `outcome` / `Result()` == 2 | the DUPLICATE control-flow outcome |
| normal completion of the keyword loop | `outcome` / `Result()` == 0 | the OK outcome |

The well-formedness `Requires` (defaults ⊆ keyword-only) mirrors the repo
invariant that `kwonly_defaults`' keys are a subset of `kwonly` (a defaulted
keyword-only parameter is a keyword-only parameter): it holds for every real
callable's signature.

The termination obligation `Requires(MustTerminate(2))` (discharged in the loop
by `Invariant(MustTerminate(len(supplied) - i + 1))`) mirrors the repo reality
that the keyword loop is a bounded `for bit in bits:` scan over a finite token
list: `parse_bits` always answers (returns the bound args or raises
`TemplateSyntaxError`). Nagini verifies partial correctness by default, so
without this obligation a non-terminating implementation would satisfy the
value postcondition vacuously while its faithful real counterpart hangs
template compilation; the obligation excludes exactly those diverging impls and
no terminating one.

## 3. Callee provenance — NO axioms

There is **no `@ContractOnly` axiom** in this bundle and **no A-reference deep
model of a library callee**: the changed line is a pure membership test in the
binder's own control flow, modeled deeply by `outcome`/`acceptable`/`contains`.

The two callees the keyword loop invokes are unchanged and orthogonal to the
modeled decision, so they are abstracted away (not axiomatized):

- `token_kwargs([bit], parser)` (`django/template/base.py:1001`, called at
  `library.py:260`) extracts a `{param: value}` mapping from one token. Whether
  a bit IS a keyword and WHICH parameter name it carries is its job; the modeled
  decision takes that as given (`supplied` is exactly the run of extracted
  keyword parameter names). The patch does not touch it.
- `parser.compile_filter(...)` (`django/template/base.py:559`) compiles a value
  expression. It produces the `value` half of the kwarg, which the changed line
  never inspects (the UNEXPECTED/DUPLICATE decision is on `param` alone). The
  patch does not touch it.

Because the bug and fix live entirely in the `param`-membership condition, the
value/extraction machinery is observationally irrelevant to the pinned behaviour
and is elided under the R-refinement above. `axiom_check.py` validates the deep
`outcome` model **== the real post-patch `parse_bits` keyword decision** (a
faithful transcription including the real `unhandled_kwargs` construction and
consumption) over an exhaustive small enumeration plus 40 000 randomized fuzz
inputs, and confirms the pre-patch differential on both issue witnesses (G-AX).
