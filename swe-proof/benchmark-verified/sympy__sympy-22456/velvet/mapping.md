# mapping.md — sympy__sympy-22456

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a3475b3f9ac662cd425157dd3bdb93ad7111c090`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-model reference.

Repo file under change: `sympy/codegen/ast.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reconstructInvariance (s : StrObj)` | the `String` atomic-string class — `sympy/codegen/ast.py:872` (its `func`/`kwargs`/`args` reconstruction contract) | the modeled changed behavior (argument invariance of an atomic string object) |
| `StrObj` (`text : List Char`) | an instance of the `String` class — its sole defining field is its text content (`__slots__ = ('text',)`, `sympy/codegen/ast.py:897`) | the rich object, modeled by its one touched field (SPEC_GUIDE §2 "rich object → structure with only the touched fields") |
| `exposedArgs (s) = []` *(deep model — A-reference)* | `expr.args` for a `String` instance — empty because `text` is excluded from the constructor args (`not_in_args = ['text']`, `sympy/codegen/ast.py:898`), so the object exposes no positional sub-arguments | pure spec: the positional arguments the object exposes; deep model of the UNCHANGED structural inspection `args`, validated `exposedArgs == []` against the real `String('...').args` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `applyPos` / `applyKw` | the result of *calling* `expr.func` positionally (`expr.func(*expr.args)`) and by keyword (`expr.func(**expr.kwargs())`) | pure spec: the reconstruction-call semantics for each `func` signature |
| `FuncKind.noArgForm` | post-patch `func` — `@property func(self): return lambda: self` (`sympy/codegen/ast.py` added at `String`) plus `kwargs()` returning `{}` | the fixed reconstruction function (accepts a no-argument call) |
| `FuncKind.oneArgForm` | pre-patch `func` — the inherited `Basic.func` returning the class `self.__class__` (a constructor needing the single `text` specifier), with `kwargs()` returning `{'text': self.text}` (`Token.kwargs`, `ast.py:320`) | the buggy/legacy reconstruction function |

The post-patch repo additions (refinement audit only, not in the consumer spec
view): the `String.func` property (`lambda: self`) and the `String.kwargs()`
override (returns `{}`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `String` instance `expr` | `StrObj` with `text : List Char` | `expr` ↔ `{ text := expr.text.toList }`; equality of `String` instances (`Token.__eq__` compares `text`) ↔ `StrObj` `DecidableEq` on `text` |
| a Python `str` (the `text` attr; a keyword name like `"text"`) | `List Char` | `s` ↔ `s.toList`; `len(s)` ↔ `l.length`; on the BMP this is total and exact |
| `expr.args` (a tuple of sub-objects) | `List StrObj` | the empty tuple `()` ↔ `[]`; for `String` this is always `()` |
| `expr.kwargs()` (a dict) | the list of its keyword NAMES, `List (List Char)` | the dict's key set ↔ the list of names; `{}` ↔ `[]`; `{'text': ...}` ↔ `["text".toList]`. Only the key set matters for whether a keyword call type-checks (the values are the object's own fields, so reconstruction reproduces it iff the keyword set matches the signature) |
| `func(*pos)` raising `TypeError` (arity/keyword mismatch) | `applyPos`/`applyKw` returning `none` | a failed reconstruction call (exception) ↔ `none`; a successful one reproducing the object ↔ `some s` |
| `func(*pos) == self` / `func(**kw) == self` | `applyPos … = some s` / `applyKw … = some s` | the argument-invariance identities the issue demands |

`String` indexing/equality is by text content only; the carrier `StrObj` keeps
just `text`, the one field the F2P test (`st.func(*st.args) == st`) observes.

## 3. Callee provenance

### 3.1 `exposedArgs` deep model ↔ `String(...).args` (A-reference)
**Callee:** the UNCHANGED structural inspection `expr.args` on a `String`
instance. The patch does NOT change how `String` computes `args`; `args` is `()`
both pre- and post-patch (because `text` is in `not_in_args`, so it is never
passed to the `Basic` constructor). The model `exposedArgs s = []` is the deep
model of this UNCHANGED inspection; there is **no consumed axiom** about it. It
is the empty positional-argument view that makes `func(*args)` a zero-argument
call — exactly the call the new nullary `func` is built to accept.

**Soundness check (G-AX):** `axiom_check.py` constructs real `String` instances
over boundary + fuzz text values and asserts `String(t).args == ()` (the
`exposedArgs == []` A-reference) — and ONLY that. G-AX runs against the repo
**as-is** (the gold patch is NOT applied; only G-CONF applies it), so it may
validate only callees the patch leaves UNCHANGED. `String.args` is `()` both
pre- and post-patch (`text ∈ not_in_args`), so it is a legitimate A-reference.
The reconstruction-call semantics that `applyPos`/`applyKw` encode (post-patch
`func(*args) == self`, `func(**kwargs()) == self`, `kwargs() == {}`) are the
operation the patch CHANGES; per SPEC_GUIDE §0.7 they are NOT asserted in G-AX
(they would raise on the unpatched tree — the very bug). They are instead
checked by G-CONF against the patched `String`. Imports only `sympy`. Exit 0
iff the unchanged A-reference holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22456`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`applyPos`/`applyKw`/`exposedArgs` (R/I-tagged ops) to Python and diffs the two
reconstruction outcomes against `patch.diff`'s behaviour — the patched real
`String` instance's `func(*args)`/`func(**kwargs())` reproduction — over the
fuzzed text inputs. The A-reference `exposedArgs` leg (== real `String.args`)
stays with G-AX.
