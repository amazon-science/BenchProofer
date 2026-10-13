# refinement.md — django__django-14155

Operation correspondence between `implementation_resolverMatchRepr` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. Every value the patched method consumes
(`isinstance(...)`, `repr(self.func)`, `self._func_path`, and each field's `%s`
and `%r` renderings) is supplied as a model input; the assembly of the output
line is modeled DEEPLY (spelled-out concatenation). Every row is **R** or **I**.
The R/I legs are differential-tested by G-CONF; G-AX is a skip stub.

## What the gold patch changes (`django/urls/resolvers.py`, `ResolverMatch.__repr__`)

Two coupled edits to how the one-line representation is built:

1. **Adds a partial-application case for the view slot.** Pre-patch the slot was
   always `self._func_path`; post-patch:
   ```python
   if isinstance(self.func, functools.partial):
       func = repr(self.func)
   else:
       func = self._func_path
   ```
   For a partial view the dotted path is uninformative (it does not reveal the
   underlying callable or its pre-bound arguments), so the partial's own `repr`
   is used instead.

2. **Switches the six remaining fields from `%s` to `%r`.** Pre-patch the format
   string rendered `args/kwargs/url_name/app_names/namespaces/route` with `%s`;
   post-patch with `%r`. For text values this adds the delimiting quotes that the
   F2P `test_repr` expects (`url_name='no-kwargs'`, `route='^…$'`).

## `implementation_resolverMatchRepr` ↔ the patched `__repr__`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `funcIsPartial : Bool`, `funcPath funcRepr : String`, six `Rendered` | `isinstance(self.func, functools.partial)`, `self._func_path`, `repr(self.func)`, and `(str(v), repr(v))` per field | R | the observables at the assembly point; `isinstance`/`repr`/`%`-format are UNCHANGED callees whose outputs are the model inputs (mapping.md bijection) |
| `let mut func := funcPath; if funcIsPartial then func := funcRepr` | `if isinstance(self.func, functools.partial): func = repr(self.func) else: func = self._func_path` | I | the EDITED view-slot selection, op-for-op |
| `"ResolverMatch(func=" ++ func ++ ", args=" ++ args.r ++ … ++ ", route=" ++ route.r ++ ")"` | `'ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, app_names=%r, namespaces=%r, route=%r)' % (func, self.args, …, self.route)` | I | the EDITED format assembly; `%s` of `func` ↦ `func` verbatim, each `%r` slot ↦ that field's `.r` rendering supplied as input |
| `return <the assembled string>` | `return (…)` | I | the method's return value |

The `Rendered.r` field carries `repr(v)` and `Rendered.s` carries `str(v)`; the
spec/impl bind the six remaining slots to `.r` (the post-patch `%r`), which is the
discriminator the prepatch-2 variant violates by binding to `.s`.

## Independently-observable behaviors (G-DIFF)

Two prepatch variants, one per coupled edit; each keeps the spec view
byte-identical to `Solution.lean`:

- **`Solution_prepatch.lean`** — the view slot always shows `funcPath`, with no
  partial-application case. Fails `correct_resolverMatchRepr` whenever
  `funcIsPartial = true` and `funcRepr ≠ funcPath`: the result shows the dotted
  path, but the spec demands `funcRepr`. This is the F2P behavior
  (`test_repr_functools_partial`: a partial view must render its own `repr`).

- **`Solution_prepatch_2.lean`** — the view slot is chosen correctly, but the six
  remaining fields are rendered with their plain form `.s` instead of the
  representation form `.r`. Fails `correct_resolverMatchRepr` whenever any of
  those fields has `.s ≠ .r` (e.g. a text `url_name` / `route`): the result omits
  the delimiting quotes, but the spec demands the representation form. This
  isolates the `%s → %r` edit (F2P `test_repr`, which now expects
  `url_name='no-kwargs'` and `route='^…$'`).
