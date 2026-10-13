# mapping.md — sphinx-doc__sphinx-9230

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 567ff22716ac258b9edd2c1711d766b440ac0b11`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deeply-modeled callee.

Repo file under change: `sphinx/util/docfields.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveParamMethod (descriptor, mayCarryType)` | the `if typedesc.is_typed:` block of `DocFieldTransformer.transform` — `sphinx/util/docfields.py:299–307` | the modeled changed behaviour: resolve one field descriptor into `(name, optional inline type)` |
| `descriptor : List Char` | the local `fieldarg : str` at `docfields.py:301` | the field-argument text being resolved |
| `mayCarryType : Bool` | `typedesc.is_typed` (`docfields.py:299`; `TypedField.is_typed = True`, `docfields.py:163`; base `Field.is_typed = False`, `docfields.py:52`) | whether this field kind may carry an inline `:param type name:` type |
| `severTail (s : List Char)` *(deep model — A-reference)* | `str.rsplit(None, 1)` — CPython stdlib `str` method (called post-patch at `docfields.py:301`) | pure spec: separate on the LAST run of whitespace, at most once; `none` ↔ the `ValueError` (fewer than two whitespace-separated parts) |
| `resolveParam` | the whole `try: argtype, argname = …rsplit(None,1) except ValueError: pass else: …` block (`docfields.py:300–307`) | pure spec: the per-descriptor outcome (name + optional type) |
| `ParsedParam {name, typeName}` | the pair of locals `(argname, argtype)` plus the "type was recorded" outcome the `else:` branch produces (`docfields.py:305–307`) | structure holding the resolved name and optional inline type |
| `wsCodes` / `isWs` | the code points Python treats as whitespace when `str.split`/`str.rsplit` is called with separator `None` | per-code-point whitespace classifier the separation consults |

The pre-patch repo symbol the change replaces (refinement audit only, not in the
consumer spec view): `str.split(None, 1)` at `docfields.py:301`, which separates
on the FIRST run of whitespace.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `fieldarg : str` (the descriptor) | `List Char` | `s` (Python str) ↔ `s`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` slice/concat ↔ `List` operations; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `typedesc.is_typed : bool` | `mayCarryType : Bool` | direct boolean correspondence |
| the resolved `(argname, argtype-or-absent)` | `ParsedParam {name, typeName : Option (List Char)}` | `argname` ↔ `name`; a recorded type ↔ `typeName = some t`; "no type recorded / descriptor untouched" ↔ `typeName = none ∧ name = descriptor` |
| `str.rsplit(None, 1)` returning a 2-list `[t, a]` | `severTail s = some (t, a)` | success: type part `t`, name part `a` |
| `str.rsplit(None, 1)` returning a <2-list (→ `ValueError` on 2-tuple unpack) | `severTail s = none` | the `except ValueError: pass` branch (descriptor left untouched) |

Lean `List Char` indexing is total and sound; the carrier is `List Char`
because the operation is per-code-point whitespace separation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `severTail` deep model ↔ `str.rsplit(None, 1)` (A-reference)
**Callee:** CPython `str.rsplit(sep=None, maxsplit=1)`. The changed separation
operation is modeled **deeply** by `severTail` (with `rstripWs` / `tailWord` /
`beforeTailWord`) in the `pure` region; there is **no consumed axiom** for it.
With `sep=None`, `rsplit`:

- treats any run of whitespace as a single separator,
- ignores leading and trailing whitespace,
- with `maxsplit=1`, splits at the LAST such run,
- returns a 1-element list (the whole stripped string) when there is no interior
  whitespace separating two non-empty parts — and `[]` for an all-whitespace or
  empty string.

`resolveParam` consumes this as: a 2-element result `[t, a]` (⇔ `severTail =
some (t, a)`) records type `t` and name `a`; any other result (⇔ `severTail =
none`) triggers the `except ValueError: pass`, leaving the descriptor untouched
with no recorded type. The discriminating content for this instance: a
descriptor whose **type part itself contains whitespace** (e.g.
`dict(str, str) opc_meta`) must split at the LAST whitespace
(`severTail → some("dict(str, str)", "opc_meta")`), keeping the bracketed type
whole — whereas the pre-patch `split(None, 1)` split at the FIRST whitespace and
mangled it (`("dict(str,", "str) opc_meta")`).

**Whitespace alphabet (`wsCodes`):** the 29 code points Python's `str.split`/
`str.rsplit` treat as whitespace under `sep=None`. axiom_check.py confirms
`isWs(cp) == ("a"+chr(cp)+"b").split()` splits, for every cp in the BMP, so the
classifier is exact.

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.rsplit(None, 1)`
on boundary inputs (single word, empty, all-whitespace, leading/trailing/
interior whitespace, bracketed-type descriptors like the issue's
`dict(str, str) opc_meta`) plus randomized fuzz strings, asserting
`severTail == real str.rsplit(None,1)` (re-expressed as the 2-tuple/ValueError
outcome) on every input, and that the `wsCodes` classifier matches Python's
`str.split()` over the whole BMP. Imports only stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9230`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`severTail`/`resolveParam` (R/I-tagged ops) to Python and compares against
`patch.diff`'s behaviour: the patched `fieldarg.rsplit(None, 1)` path resolving
each descriptor into `(name, optional type)`.
