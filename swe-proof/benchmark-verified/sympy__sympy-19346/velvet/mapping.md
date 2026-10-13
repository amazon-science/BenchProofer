# mapping.md — sympy__sympy-19346

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 94fb720696f5f5d12bad8bc813699fd696afd2fb`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled helper.

Repo file under change: `sympy/printing/repr.py` (the `ReprPrinter` used by
`srepr`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `printDict (items : List (Obj × Obj))` | `ReprPrinter._print_dict(self, expr)` — `sympy/printing/repr.py:147` (added by the patch, immediately after `_print_list` at :144) | the modeled changed function (mapping renderer) |
| `printSet (elems : List Obj)` | `ReprPrinter._print_set(self, expr)` — `sympy/printing/repr.py:152` (added by the patch, after `_print_dict`) | the modeled changed function (collection renderer) |
| `doprint (o : Obj) = o.reprText` | `self.doprint(x)` / `self._print(x)` — `ReprPrinter`/`Printer.doprint`, `sympy/printing/printer.py` | the **unchanged** recursive element renderer; its per-element output is supplied as the input carrier (`Obj.reprText`), not re-modeled (R) |
| `joinComma (frags : List (List Char))` | `", ".join(...)` over the per-element rendered fragments (the `sep.join` in `reprify` / the explicit `", ".join(dict_kvs)`) | pure spec: join with ", " (no leading/trailing separator) |
| `kvText (p : Obj × Obj)` | `"%s: %s" % (self.doprint(key), self.doprint(value))` (`repr.py:149` post-patch) | pure spec: one "key: value" entry from the two recursive renderings |
| `dictRender` | the body of `_print_dict`: `"{%s}" % ", ".join(dict_kvs)` | pure spec: braces + comma-joined entries |
| `setRender` | the body of `_print_set`: `"set()"` when empty, else `"{%s}" % self.reprify(expr, ", ")` | pure spec: empty→"set()", else braces + comma-joined recursive element renderings |

The pre-patch repo behaviour the change replaces (refinement audit only, not in
the consumer spec view): `dict`/`set` had **no** `_print_*` method, so `srepr`
fell through `Printer._print` → `ReprPrinter.emptyPrinter` → `str(expr)`, which
formats each element by its **shallow** textual form (Python's default
`repr`/`str` of the contained objects), not the recursive `srepr` renderer.
Concretely `srepr({x: y})` gave `"{x: y}"` instead of
`"{Symbol('x'): Symbol('y')}"`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a printed code fragment (`str` returned by `doprint`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| one container element `e` | a Lean `Obj` | `Obj.reprText` ↔ `self.doprint(e)` (the recursive `srepr` rendering of `e`); `Obj.strText` ↔ `str(e)` (the shallow fallback form, used only by the pre-image skeletons). On the tested inputs both are total. |
| a `dict` `d` (ordered, py≥3.7) | `List (Obj × Obj)` | `d.items()` in iteration order ↔ the `List (Obj × Obj)`; each `(k, v)` ↔ `(⟨doprint k, str k⟩, ⟨doprint v, str v⟩)` |
| a `set`/`frozenset` `s` | `List Obj` | the elements of `s` in the SAME single-process iteration order the real `reprify` uses ↔ the `List Obj`; empty set ↔ `[]` |
| `", ".join(frags)` | `joinComma frags` | both interleave the 2-char separator ", " between consecutive fragments; no leading/trailing separator; `[]→""`, `[x]→x` |

Lean `String`/`List Char` indexing is total and sound; the carrier for a
fragment is `List Char` because the operation is character-level string
assembly. Set iteration order is not modeled as a behaviour — it is a property
of the same Python `set` object, so the oracle and the shadow iterate the *same
object* and observe the *same order* (the F2P `test_dict` only asserts on
dicts, whose order IS deterministic; `test_set` accepts either order).

## 3. Callee provenance

**No consumed axioms and no deep-model references.** The only callee the changed
functions invoke is the recursive element renderer `self.doprint` /
`self._print` — which is **unchanged** by the patch. Following the
input-carrier discipline (cf. sympy__sympy-16766, where `str(base)` /
`self._print(ind)` were treated as input carrier), the recursive rendering of
each element is supplied as the carrier field `Obj.reprText` and is **not**
re-modeled behind an axiom: it is the output of an unchanged helper, part of the
input. The behaviour under specification — selecting the **recursive** element
text (`doprint`, not the shallow `strText`), assembling the brace-delimited,
comma-separated string, and the `set()` empty-collection token — is modeled
DEEPLY by `kvText`/`doprint`, `joinComma`, `dictRender`, `setRender` and the
verified backward `while` folds. Hence `axioms = []`,
`deep_model_references = []`, and **G-AX is skipped** (no `axiom_check.py`).

The discriminating content of the change — each key/value/element is rendered
**recursively** (`doprint o = o.reprText`) rather than by the shallow fallback
(`o.strText`) — lives in `kvText`/`setRender` using `doprint`. The pre-image
skeletons (`Solution_prepatch*.lean`) substitute `.strText` and **fail**
`out = dictRender items` / `out = setRender elems` (G-DIFF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`19346`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `joinComma`/`kvText`/`dictRender`/`setRender` to Python and takes
each per-element rendered string from the REAL `ReprPrinter.doprint` (the
unchanged helper → input carrier, R), exactly as the gold `_print_dict` /
`_print_set` do. There are no A-tagged ops in the impl region, so `conf_skip`
is false and the shadow is pure R/I.
