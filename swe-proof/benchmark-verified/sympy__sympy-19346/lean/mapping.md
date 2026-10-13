# mapping.md — sympy__sympy-19346

## Instance
- repo: sympy/sympy
- base_commit: 94fb720696f5f5d12bad8bc813699fd696afd2fb
- spec_provenance: **cold** (derived from problem_statement + gold patch + repo
  source at base_commit only).

## Symbol binding (file:line @ base_commit)
- `sympy/printing/repr.py:19` — `class ReprPrinter(Printer)`, the printer behind
  the public `srepr` entrypoint (`sympy/printing/repr.py:343`, `srepr(expr) =
  ReprPrinter(settings).doprint(expr)`).
- `sympy/printing/repr.py:144-145` — `_print_list`, the existing exemplar:
  `"[%s]" % self.reprify(expr, ", ")`.
- The gold patch inserts, right after `_print_list` (between lines 145 and 147):
  - `_print_dict(self, expr)` — joins `"%s: %s" % (self.doprint(key),
    self.doprint(value))` over `expr.items()` with `", "`, wraps in `{ … }`.
  - `_print_set(self, expr)` — returns `"set()"` when empty, else
    `"{%s}" % self.reprify(expr, ", ")`.
- `reprify(self, args, sep)` (`repr.py:27-31`) — `sep.join([self.doprint(item)
  for item in args])`.
- `doprint(self, expr)` (`sympy/printing/printer.py:249-251`) — `self._str(
  self._print(expr))`; `_print` dispatches recursively to the per-type
  `_print_*` method, i.e. the canonical recursive renderer.

## The defect, abstractly
`srepr` produces a canonical textual representation from which a value can be
reconstructed; every contained element must be rendered through the SAME
canonical recursive renderer (`self.doprint`/`self._print`). At base_commit the
printer had dedicated methods for `list` and `tuple` but NONE for `dict` or
`set`. A `dict`/`set` therefore fell through `_print` to the generic
`emptyPrinter` fallback (`repr.py:33-49`), whose final clause returns
`str(expr)` — the container's ordinary Python text form. That renders each
contained element via the element's own `__str__` (a NON-canonical conversion),
e.g. `{x, y}` → `"{x, y}"` and `{x: y}` → `"{x: y}"`, instead of the canonical
`"{Symbol('x'), Symbol('y')}"` / `"{Symbol('x'): Symbol('y')}"`. Nested
structure is lost and the string can no longer be `eval`'d back.

The fix adds the two missing `_print_*` methods so that:
- a mapping renders each entry as `srepr(key) ": " srepr(value)`, entries joined
  by `", "`, wrapped in `{ … }`; the empty mapping is `"{}"`;
- an unordered collection renders each element via `srepr`, joined by `", "`,
  wrapped in `{ … }`; the empty collection is the dedicated literal `"set()"`.

Worked F2P cases (from `test_dict` / `test_set`):
- `srepr({}) == "{}"`
- `srepr({x: y}) == "{Symbol('x'): Symbol('y')}"`
- `srepr({x: {y: z}}) == "{Symbol('x'): {Symbol('y'): Symbol('z')}}"`  (nesting)
- `srepr(set()) == "set()"`
- `srepr({x, y}) in ("{Symbol('x'), Symbol('y')}", "{Symbol('y'), Symbol('x')}")`

## Lean ↔ Python type bijection  (used by G-CONF / G-AX)
| Python (post-patch observable) | Lean model |
|---|---|
| a `dict` whose `.items()` enumerate in iteration order | `entries : List (SymExpr × SymExpr)`, one pair per item, in order |
| a `set` enumerated in iteration order | `elems : List SymExpr`, one element per member, in order |
| one contained value `v` (key, value, or element) | one `SymExpr` (opaque; only its rendering matters) |
| `self.doprint(v)` / `srepr(v)` — the canonical recursive renderer on `v` | `elemRepr v : String` |
| the element's own plain text form `str(v)` (the pre-patch fallthrough) | `nativeRepr v : String` (used only in the prepatch impl) |
| `", "` separator, `"%s: %s"` entry format, `{ … }` braces, `"set()"`, `"{}"` | the literal string ops in the impl/spec |
| the returned `srepr(container)` string | `result : String` |

`SymExpr`, `elemRepr`, `nativeRepr` are declared `opaque` (signatures only); the
proof consumes no property of them. The discriminator between fix and bug is
purely which renderer wraps each element (`elemRepr` vs `nativeRepr`) plus the
empty-set special case — a structural string identity, so no numeric/`Real`
modeling is needed.

## Callee provenance
- `elemRepr` models `self.doprint` (== `srepr` on a sub-value), an UNCHANGED
  callee the new methods CALL. It is NOT axiomatized: it appears identically in
  spec and impl as an opaque carrier (the recursion lives inside it), and the
  claim "the impl threads each element through the real canonical renderer" is
  checked end-to-end by G-CONF (an A-reference). `opaque_callees =
  [SymExpr, elemRepr, nativeRepr]`, `axioms = []` → G-AX skips.
- Flag deps: none. The `_print_dict`/`_print_set` methods fire whenever the
  argument's type name is exactly `dict` / `set` (dispatch keys on
  `type(expr).__name__`), independent of any printer setting (`order`,
  `perm_cyclic`).

## G-CONF fuzz seed
- pinned seed: **19346** ; N_random ≥ 1e5. Sets/dicts are driven over the SAME
  live object for both `srepr` and the shadow, so iteration order matches and the
  comparison is byte-exact.
