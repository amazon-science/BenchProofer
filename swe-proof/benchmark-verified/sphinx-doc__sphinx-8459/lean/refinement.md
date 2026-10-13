# refinement.md — sphinx-doc__sphinx-8459

Operation-by-operation correspondence between `implementation_aliasedLabels`
(Lean) and the gold `patch.diff` in `record_typehints`. Every row is tagged
**R** (type refinement), **A-consumed** (proof consumes a callee axiom),
**A-reference** (deep model validated `==` real callee by G-CONF), or **I**
(identical concrete op).

| # | Lean op (`implementation_aliasedLabels`) | `patch.diff` / `record_typehints` counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut annotation : List (String × String) := []` | `annotation = annotations.setdefault(name, OrderedDict())` (fresh ordered table) | R + I | empty insertion-ordered table; `OrderedDict ↔ List (String × String)` |
| 2 | `for (name, ann) in params do` | `for param in sig.parameters.values():` | I | iterate parameters in declaration order |
| 3 | `if let some nm := ann then …` | `if param.annotation is not param.empty:` | R | `Option`-presence ⇔ `is not param.empty` |
| 4 | `annotation := annotation ++ [(name, renderName render aliases nm)]` | `annotation[param.name] = typing.stringify(param.annotation)` **with `sig` resolved via `type_aliases`** | A-reference + R | label is alias-aware: `aliases.get(nm, render nm)`. The alias resolution is exactly what the gold `inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)` injects. Validated by G-CONF. |
| 5 | `if let some nm := ret then annotation := annotation ++ [("return", renderName render aliases nm)]` | `if sig.return_annotation is not sig.empty: annotation['return'] = typing.stringify(sig.return_annotation)` (same alias-aware `sig`) | A-reference + R | reserved `"return"` key; same alias-aware label rule |
| 6 | `return annotation` | the recorded `annotation` table | I | result is the ordered `(key,label)` table |

## The changed op, expressed (no changed-inexpressible op)

The gold patch changes a single line — `inspect.signature(obj)` →
`inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)` — but its
*observable* effect is on the labels emitted at lines 33 and 35: each annotation
is rendered alias-aware instead of by the default renderer alone. The impl
expresses this as `renderName render aliases nm` in BOTH the parameter loop
(op 4) and the return entry (op 5):

- **alias hit** → `renderName` returns the configured replacement;
- **alias miss** → `renderName` falls back to `render nm` (the default label).

Pre-patch model (`Solution_prepatch.lean`): the alias table is ignored — labels
are `render nm` directly in both op 4 and op 5. This is the actual bug: a
configured alias (e.g. `myint → myint`) is not honoured, so the documentation
shows the default rendering of the underlying type.

There is **no A-consumed** row: the proof needs no callee-property axiom. The
default renderer `typing.stringify` is the modeled function's *free input*
`render`, quantified universally in `correct_aliasedLabels` (the spec holds for
every renderer), not a consumed callee.

## Why no op is left inexpressible (SPEC_GUIDE §3)

The recorded table is built from totally-expressible operations: ordered
iteration, presence test on an optional annotation, an alias-table lookup with
default fallback, and ordered insertion under string keys. The default
annotation renderer is abstracted as an opaque-but-pure `String → String`
function and quantified over, so the spec pins the *aliasing* behaviour the fix
adds for ALL renderers and ALL inputs — not just the F2P `myint` sample.

## Discrimination (G-DIFF / verify ⟹ correct)

`renderName` differs from `render` exactly on aliased names. The F2P test
configures `autodoc_type_aliases = {'myint': 'myint'}` over a callable whose
parameters and return are annotated `myint`, and asserts every displayed label
is `myint` (the alias), where the default rendering would resolve `myint = int`
to `int`. The prepatch impl emits `render "myint"` (the default), so
`problem_spec_aliasedLabels` — which demands the alias-aware label — is violated
on that discriminating clause, and `correct_aliasedLabels` is unclosable against
the prepatch impl (G-DIFF). Order, key-presence, and per-entry label are all
pinned, so no wrong impl satisfies the spec while failing the test (directive 5
frame).
