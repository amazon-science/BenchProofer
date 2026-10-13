# mapping.md — sympy__sympy-22456

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a3475b3f9ac662cd425157dd3bdb93ad7111c090`, states the type
abstraction, and gives the provenance of the modelled operation.

Repo file under change: `sympy/codegen/ast.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| class `Atomic` (field `text: List[int]`) | `String` — `sympy/codegen/ast.py:872` (a `Token`/`Basic` subclass; `__slots__ = ('text',)`, `not_in_args = ['text']`) | the atomic string-valued AST token under specification; only the defining `text` payload is modelled |
| `arg_count(s)` | `len(s.args)` — `Basic.args` (`sympy/core/basic.py:720`, returns `self._args`) | number of positional arguments of the token; for `String` it is `0` because `text` is in `not_in_args`, so `Basic.__new__` receives no positional args |
| `rebuild_from_args(s)` | `s.func(*s.args)` — `Basic.func` (`sympy/core/basic.py:694`) applied to `Basic.args` | the canonical argument-invariance reconstruction; the operation the added assertion `st.func(*st.args) == st` exercises (`sympy/codegen/tests/test_ast.py:270`) |

The two reconstruction skeletons correspond to the two states of `func`:

* **post-fix** — `String.func` is overridden to return a nullary callable that
  yields the very same object (`sympy/codegen/ast.py`, gold hunk 4:
  `@property def func(self): return lambda: self`). Calling it on the empty
  argument list returns `self`, so `func(*args)` is `self`.
* **pre-fix** — `String` inherits `Basic.func`, which returns the class itself
  (`return self.__class__`, `sympy/core/basic.py:716`). `func(*args)` is then
  `String()` (empty positional args). `Token.__new__`
  (`sympy/codegen/ast.py:211`) walks `__slots__ = ('text',)`; `text` is neither
  supplied positionally (it is `not_in_args`, hence absent from `args`) nor has
  a default, so the generic constructor cannot recover `text`
  (`sympy/codegen/ast.py:235`: `raise TypeError('No value for %r given and
  attribute has no default')`). The reconstruction therefore fails to reproduce
  the original `text`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `String.text` (a Python `str`) | `List[int]` of Unicode code points | `s.text[k]` ↔ `text[k] == ord(s.text[k])`; `len(s.text)` ↔ `len(text)`; an empty `str` ↔ `[]` (Nagini bans `str` indexing) |
| `String.text` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the field as a `PSeq`; equality of texts ↔ `PSeq` equality |
| `self.args` (a `Tuple`) | length `arg_count(s)` only | the F2P invariance observes that `String.args == ()` (length 0); the element payload is empty, so only the count is modelled — the reconstruction consumes no positional element |
| token identity / `Token.__eq__` (`sympy/codegen/ast.py:255`: equal iff same class and all `__slots__` attributes equal) | equality of the modelled `text` payload | for the single-slot `String`, two tokens are equal iff their `text` fields are equal; modelled as `PSeq[int]` text equality |
| `func` (a property returning a callable) / `func(*args)` | the function `rebuild_from_args` whose result is the reconstructed token | the reconstruction is modelled directly; see refinement.md |

`str` indexing/iteration is banned in Nagini, so the `text` carrier is
`List[int]` throughout; the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance

No `@ContractOnly` axioms are consumed. The only operation that *changed* — how
an atomic string token reconstructs itself from its arguments — is modelled
**deeply**: the reconstruction is spelled out as a direct field-preserving
rebuild (post-fix) versus a generic positional rebuild that cannot source the
excluded `text` slot (pre-fix). No unchanged opaque callee is relied upon inside
the contract, so there is nothing for G-AX to validate against a real callee;
`axiom_check.py` instead exercises the REAL `String.func(*String.args)`
invariance directly (see §4) as the executable soundness witness for the deep
model.

`Basic.args`, `Basic.func`, and `Token.__new__` are SymPy core/codegen code (not
stdlib); they are read for provenance only and reproduced faithfully in the
skeleton — they are not axiomatized.

## 4. Executable soundness witness (axiom_check.py)

`axiom_check.py` imports the REAL `sympy.codegen.ast.String` and asserts, on a
boundary + fuzz family of texts (empty, single char, the test's `'foobar'`,
unicode, long), that the deep model agrees with reality: `String(t).args == ()`
(arg count 0), and — after the fix — `st.func(*st.args) == st` and
`st.func(**st.kwargs()) == st`. It also confirms that `String(t).text == t`, the
`text`-field bijection the model relies on. Imports only `sympy.codegen.ast`
(the very module the gold patch edits); exit 0 iff every observation matches the
model.

## G-CONF (differential conformance: `conformance_check.py`)

**Shadow.** The impl region of `model.py` copied VERBATIM, with only the
contract calls (`Requires` / `Ensures` / `Invariant` / `Assert`) and the
invariants markers deleted — no restructuring, renaming or simplification (a
verbatim-equality check of the two regions was run while authoring). The `@Pure`
helper `arg_count` and the carrier class `Atomic` are copied over the same way.
There are no `@ContractOnly` axioms in this bundle (§3), so no axiomatized callee
needs redirecting: the whole impl region is directly executable and is executed.
`PSeq` / `ToSeq` are realized as an immutable tuple shim, so the comparison is
made on exactly the `PSeq[int]` observable the postcondition states
(`ToSeq(Result().text) == ToSeq(s.text)`) rather than on a hand-rolled proxy.

**Oracle.** The REAL patched repo function is **called**, never transliterated:
`sympy.codegen.ast.String.func(*String.args)` (§1) — a real `String(text)` is
constructed, its real `.args` is read off it, and its real `.func` is applied to
those args. Post-fix `func` is the gold hunk's `lambda: self`; pre-fix it is the
inherited `Basic.func` (`sympy/core/basic.py:716`), whose reconstruction raises
because `Token.__new__` cannot source the `not_in_args` `text` slot from the
empty argument list. The gate applies the gold patch before the script runs.

**Type bridge (§2, inverted).** `to_model(t) = [ord(c) for c in t]` and
`from_model(cps) = ''.join(chr(c) for c in cps)` are mutually inverse on every
Python `str`; real `str` inputs are generated and lifted into the model's
`List[int]` code-point carrier. The model's `Requires` constrains only
permissions (`Acc(...)`), never values, so every generated input satisfies it —
the input domain is not narrowed anywhere. The `self.args` abstraction (length
only) is inverted by comparing `arg_count(s)` against real `len(st.args)`.

**Observables diffed** (three, per input): the arg count; the rebuilt text as a
`PSeq[int]`, where a real reconstruction that raised or returned a non-`String`
is a disagreement; and the model's token-equality abstraction (single-slot
`Token.__eq__` = text equality) against the real `rebuilt == st`.

**Inputs.** The modelled domain (all texts) is infinite, so: 18 boundary cases
first — empty text (loop body runs zero times), single char (exactly once), the
F2P literal `'foobar'`, whitespace / control / quote / markup / non-ascii /
astral / lone-surrogate / NUL, and a 200-char text (long loop) — then seeded
fuzz to fill the count. **100018 inputs total** (18 boundary + 100000 fuzz),
>= 1e5.

**Pinned seed: `SEED = 22456`** (module constant `SEED` in
`conformance_check.py`; `N_FUZZ = 100_000`).

**Recorded verdict.** `G-CONF=pass` — 0 disagreements over 100018 inputs.
Negative control: run against the UNPATCHED base commit the same script fails on
the first input (real `func(*args)` raises, oracle rebuild `None`), confirming
the check is capable of refuting the refinement rather than passing vacuously.
