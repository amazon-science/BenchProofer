# mapping.md — django__django-14155

## Symbol binding (file:line @ base_commit 2f13c476abe4ba787b6cb71131818341911f43cc)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_resolverMatchRepr` / `problem_spec_resolverMatchRepr` / `correct_resolverMatchRepr` | the body that builds the one-line representation string of a resolved URL match | `django/urls/resolvers.py:61-65` @ base_commit (`ResolverMatch.__repr__`) |
| `if funcIsPartial then funcRepr else funcPath` | `if isinstance(self.func, functools.partial): func = repr(self.func) else: func = self._func_path` | gold patch, `resolvers.py:61-65` (post-patch); pre-patch had no such branch and always used `self._func_path` |
| the six `++ ", <field>=" ++ <field>.r` slots | the `%r`-formatted fields in the post-patch format string | gold patch (post-patch); pre-patch formatted these six fields with `%s` |

## Modeled inputs (the renderings the method holds at the assembly point)

The function under spec is `ResolverMatch.__repr__`: it assembles a single string
from values the object already carries. Its observable inputs are:

| Lean | Python reality | meaning |
|---|---|---|
| `funcIsPartial : Bool` | `isinstance(self.func, functools.partial)` | is the view a partial application? |
| `funcPath : String` | `self._func_path` | the view's dotted import path (module + qualified name) |
| `funcRepr : String` | `repr(self.func)` | the view's own detailed representation (for a partial: the underlying callable + pre-bound arguments) |
| `args : Rendered` | `self.args` with `s = str(self.args)`, `r = repr(self.args)` | positional arguments, both renderings |
| `kwargs : Rendered` | `self.kwargs` | keyword arguments, both renderings |
| `urlName : Rendered` | `self.url_name` | the match's name, both renderings |
| `appNames : Rendered` | `self.app_names` | application-name chain, both renderings |
| `namespaces : Rendered` | `self.namespaces` | namespace chain, both renderings |
| `route : Rendered` | `self.route` | route pattern, both renderings |

`Rendered` carries `s` (the `%s`/`str()` form) and `r` (the `%r`/`repr()` form).
For text the two differ (`repr` adds delimiting quotes); for the tuple/dict/list
values Python's `str` and `repr` coincide, so `s == r` there.

## Output

| Lean | Python |
|---|---|
| `result : String` | the string returned by `ResolverMatch.__repr__` |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `isinstance(self.func, functools.partial)` | `funcIsPartial : Bool` | identity |
| `self._func_path` | `funcPath : String` | identity |
| `repr(self.func)` | `funcRepr : String` | identity |
| each field value | `Rendered` with `s`/`r` | `(str(v), repr(v))`; the post-patch `%r` slot binds to `.r`, the pre-patch `%s` slot to `.s` |
| `'ResolverMatch(func=%s, args=%r, …, route=%r)' % (func, …)` | the concatenation in `problem_spec` | the format template ↦ literal joins; `%s` of `func` ↦ `func` verbatim, `%r` of each remaining field ↦ that field's `.r` |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The patched code calls `isinstance`, `repr`,
  `functools.partial` (type only), and `%`-formatting — all UNCHANGED and modeled
  as inputs/concatenation. `funcRepr = repr(self.func)` and the per-field `%r`
  renderings are taken as the inputs `funcRepr` / `Rendered.r`; the assembly is
  modeled DEEPLY, so all rows are R/I, validated by G-CONF. `axiom_check.py` is a
  skip stub.
- **Flag dependency:** the view slot depends on `funcIsPartial`; G-CONF fuzzes
  both values, and the `%s`-vs-`%r` distinction is fuzzed over values whose two
  renderings differ (text) and coincide (collections).

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
