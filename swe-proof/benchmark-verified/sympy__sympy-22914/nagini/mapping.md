# mapping.md — sympy__sympy-22914

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c4e836cdf73fc6aa7bab6a86719a0f08861ffb1d`, states the type
abstraction, and gives the provenance of the deep model that G-AX validates.

Repo file under change: `sympy/printing/pycode.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `print_function_call(name_code, joined_args, fallback)` | the function-application dispatch `CodePrinter._print_Function` (`sympy/printing/codeprinter.py:415`) together with the supported-function rendering `_print_known_func` (`sympy/printing/pycode.py:63`) wired in via `_kf` (`sympy/printing/pycode.py:80`) | the modeled rendering of a function application to a target-language call |
| `is_supported(name_code)` *(deep model — A-reference)* | membership of `expr.func.__name__` in `self.known_functions` (built from `_known_functions ∪ {math.*}` at `pycode.py:19-21,80`) — the table the gold edit extends | pure spec: the function identity is in the printer's supported table |
| `target_name(name_code)` *(deep model — A-reference)* | the table VALUE `self.known_functions[name]` (`'abs'`/`'min'`/`'max'`) emitted as the call name by `_print_known_func` / the `except TypeError` branch of `_print_Function` (`codeprinter.py:425-427`) | pure spec: the target call name for a supported function |
| `call_render(name_code, joined_args)` *(deep model — A-reference)* | the call rendering `"%s(%s)" % (func, self.stringify(expr.args, ", "))` (`codeprinter.py:427`) / `'{name}({args})'.format(...)` (`pycode.py:65`) | pure spec: `<target>(<comma-joined args>)` |
| `joined_args` (param) | `self.stringify(expr.args, ", ")` / `', '.join(self._print(arg) for arg in expr.args)` — the already-rendered, comma-and-space-joined argument text | the unchanged sub-computation common to every supported function |
| `fallback` (param) | the text the non-call paths of `_print_Function` emit for an unsupported identity (`_print_not_supported`, `codeprinter.py:560`, OR the `_rewriteable_functions` rewrite to a `Piecewise` conditional, `codeprinter.py:433-436`) | the unchanged surrounding machinery's output for this node, carried as one opaque pre-rendered sequence (read-only) |
| `name_min` / `name_max` / `name_abs` / `name_unknown` | the function identities `Min` / `Max` / `Abs` / any other `expr.func.__name__` | pure spec: name codes |

The unsupported branch of `print_function_call` abstracts the non-call paths of
`_print_Function` for an unsupported identity (`_print_not_supported`,
`codeprinter.py:560`, OR the `_rewriteable_functions` rewrite to a `Piecewise`
conditional, `codeprinter.py:433-436`). That machinery is unchanged, pre-existing
infrastructure, so its output arrives as the read-only input `fallback` and the
spec pins the unsupported result to it EXACTLY (`ToSeq(Result()) ==
ToSeq(fallback)`): an unsupported identity is emitted precisely as the unchanged
machinery would emit it — nothing but the supported-call emission may change.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` rendering produced by the printer (`doprint` result) | `List[int]` of Unicode code points; specification over `PSeq[int]` via `ToSeq` | `s[k]` ↔ `result[k] == ord(s[k])`; `str` concatenation ↔ `PSeq`/list `+`; `len` ↔ `len` |
| `expr.func.__name__` (a `str` key) + its membership/value in `self.known_functions` | integer `name_code` + `is_supported`/`target_name` | the only facets the dispatch reads are (a) is the name a table key and (b) its value; both are functions of the identity, abstracted by `name_code` |
| `self.stringify(expr.args, ", ")` / `', '.join(self._print(a) ...)` | `joined_args: List[int]` | already-rendered argument text; identical for every supported function (e.g. the pre-existing `Abs`), hence carried as one opaque pre-rendered sequence |
| `'min'` / `'max'` / `'abs'` target strings | `PSeq(109,105,110)` / `PSeq(109,97,120)` / `PSeq(97,98,115)` | per-character code points |
| `'('` `','` `' '` `')'` | `40` / `44` / `32` / `41` | code points |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]` and
the spec is phrased over `PSeq[int]`.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `is_supported` / `target_name` / `call_render` ↔ the real `PythonCodePrinter`
The changed operation — extending the printer's supported-function table so the
minimum/maximum selection functions render as target calls — is modeled
**deeply**: `is_supported` (the table membership) and `target_name` (the table
value) are spelled out in the `pure` region, and `call_render` spells out the
`<target>(<joined args>)` shape. There is **no consumed `@ContractOnly` axiom**;
the axioms region is empty.

The deep model is validated **== the real callee** out-of-band by
axiom_check.py (G-AX): it imports the real `PythonCodePrinter`, applies the gold
edit (the same `_known_functions` extension the patch makes — the deep model
encodes the POST-patch table, exactly as model.py is the verifiable face of the
patched function), and asserts that for `Min`/`Max`/`Abs` the real
`doprint(fn(*args))` equals `call_render(name_code, code_points(", ".join(
printed args)))`, and that an unsupported function never renders in that call
form. Source dispatch (`codeprinter.py:415-439`):

```python
def _print_Function(self, expr):
    if expr.func.__name__ in self.known_functions:
        cond_func = self.known_functions[expr.func.__name__]
        func = cond_func              # 'min' / 'max' / 'abs' (a str)
        ...
        if func is not None:
            try:
                return func(*[self.parenthesize(item, 0) for item in expr.args])
            except TypeError:         # a str is not callable -> here
                return "%s(%s)" % (func, self.stringify(expr.args, ", "))
    ...                               # rewriteable / not-supported fallbacks
```

`Min`/`Max` are `Application` subclasses (`sympy/functions/elementary/
miscellaneous.py:688,806`), so `expr.func.__name__` is `'Min'`/`'Max'` and the
expression routes through `_print_Function`. The known branch is consulted
BEFORE the `_rewriteable_functions` (Piecewise) branch, so once `'Min'`/`'Max'`
are table keys the rendering is the `min(...)`/`max(...)` call.

**Flag/configuration dependency:** the rendering uses the default printer
settings (`PythonCodePrinter()` with no `user_functions` overriding the table);
G-AX exercises that default configuration. The comma-join separator is the
literal `", "` (`codeprinter.py:427`).

**Soundness check (G-AX):** `axiom_check.py` runs the real `PythonCodePrinter`
on `Min`/`Max` with 2–4 distinct symbol arguments and `Abs` unary (600 renderings
over a 12-symbol pool, arg order taken from the canonicalised `expr.args`), plus
40 unsupported-function negatives, asserting deep model == real printer on every
one. It imports only the stdlib and `sympy` (the package the gold patch edits).
Exit 0 iff sound.
