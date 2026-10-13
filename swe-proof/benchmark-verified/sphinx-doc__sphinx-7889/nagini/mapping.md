# mapping.md — sphinx-doc__sphinx-7889

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ec9af606c6cfa515f946d74da9b51574f2f9b16f`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sphinx/ext/autodoc/mock.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `subscript_placeholder(key_is_text, key_text, module)` | `_MockObject.__getitem__(self, key)` — `sphinx/ext/autodoc/mock.py:55` (body line 56) | the modeled changed function (subscripting a mock placeholder) |
| `display_name(name_is_text, name, module)` *(axiom — A-consumed)* | `_make_subclass(name, module, superclass, attributes)` — `sphinx/ext/autodoc/mock.py:71` (body 73-76) | unchanged callee the changed `__getitem__` invokes; fabricates the placeholder subclass |
| `render_text(value_text)` | `str(key)` builtin coercion (added in the patch at `mock.py:56`) | pure spec: canonical textual rendering of the index; identity on the text content the spec observes |

The pre-patch repo facts the change concerns (for the refinement audit, not
referenced from the consumer spec view): `__getitem__`'s parameter was annotated
`key: str` and passed `key` to `_make_subclass` unchanged
(`sphinx/ext/autodoc/mock.py:55-56`). `_make_subclass` (`mock.py:71-76`) builds
`'__display_name__': module + '.' + name` and `type(name, (superclass,), attrs)`
— both string operations on `name`. `__getattr__` (`mock.py:58-59`) also calls
`_make_subclass(key, ...)` but is NOT changed by the patch, because attribute
keys are always `str` (Python's attribute protocol), so no coercion is needed
there; only subscript (`__getitem__`) can receive a non-`str` index.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `key: Any` (the subscript index; `str` pre-patch) | a pair `(key_is_text: bool, key_text: List[int])` | `key_is_text == isinstance(key, str)`; `key_text == [ord(c) for c in str(key)]` — the code points of the index's textual rendering. The `str → Any` widening is "the index need not be textual". |
| `str` (`self.__display_name__`, `_make_subclass`'s `module`/`name`, the resulting `__display_name__`) | `List[int]` of Unicode code points; spec carried by `PSeq[int]` via `ToSeq` | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concat ↔ `PSeq`/list `+`; `'.'` ↔ `46`. |
| `str(key)` coercion (`mock.py:56`, post-patch) | `render_text` (identity on the text content) + the flag `name_is_text = True` | `str(x)` is total and always returns a `str`, so the modelled name is unconditionally textual; the F2P test never inspects the rendered glyphs, only that construction succeeds, so the identity rendering is observationally exact. |
| the fabricated `type(...)` object + trailing `()` instantiation (`mock.py:56`) | the display-name `List[int]` result (`_MockObject`-subclass identity folded in) | the F2P test observes that the construction succeeds and that the result behaves as a `_MockObject` subclass (`isinstance(obj2, SubClass2)`, `SubClass2.__doc__`); the display content is the fabricator's contract (§3). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `display_name` ↔ `_make_subclass` (A-consumed)
**Callee:** `sphinx/ext/autodoc/mock.py:71-76`, unchanged by the patch:

```python
def _make_subclass(name: str, module: str, superclass: Any = _MockObject,
                   attributes: Any = None) -> Any:
    attrs = {'__module__': module, '__display_name__': module + '.' + name}
    attrs.update(attributes or {})
    return type(name, (superclass,), attrs)
```

The axiom encodes only the two obligations the subscript site relies on:

  * **Ensures** — the fabricated subclass's display name is `module + '.' + name`
    (the `'__display_name__': module + '.' + name` entry, with `'.'` == code
    point 46). model.py: `display_name(True, name, module) == module ++ PSeq(46)
    ++ name`.
  * **Requires** — `_make_subclass` is defined ONLY for a textual `name` whose
    code points are all honest scalar values: no interior NUL (code point 0)
    and no surrogate code point (U+D800..U+DFFF, i.e. 55296..57343). Three
    real-callee facts force the three halves:
      - a NON-textual `name` fails: both `module + '.' + name` (string
        concatenation; `str + non-str` raises `TypeError`) and
        `type(name, (superclass,), attrs)` (CPython requires `type()`'s first
        argument to be a `str`; otherwise `TypeError: type.__new__() argument 1
        must be str`) reject it;
      - a textual `name` that contains a NUL also fails: `type(name, ...)`
        raises `ValueError: type name must not contain null characters`
        (CPython rejects a NUL code point in a type name). Being a `str` is NOT
        sufficient.
      - a textual `name` that contains a lone SURROGATE code point also fails:
        `type(name, ...)` must encode the class name and a surrogate has no
        encoded form, so CPython raises `UnicodeEncodeError` ("surrogates not
        allowed"). Being a NUL-free `str` is not sufficient either.
    model.py: `Requires(name_is_text and not (0 in name))` plus
    `Requires(Forall(k, 0 <= k < len(name) ==> not (55296 <= name[k] <= 57343)))`.
    This is the **weakest** contract the proof needs and matches the real
    callee — it claims nothing about any class of input the real callee
    rejects, so it does not over-claim. (The NUL half was added per the
    batch-06 adversarial verdict, which found the prior
    `Requires(name_is_text)` over-claimed on a NUL-bearing str; the surrogate
    half was added per the unified-pipeline faithfulness audit, which found
    the NUL-only precondition still over-claimed on a surrogate-bearing str —
    the real callee raises `UnicodeEncodeError` where the axiom promised a
    display name.)

The patch does not touch `_make_subclass`; it only changes WHAT `__getitem__`
hands it (`str(key)` instead of `key`). So `_make_subclass` is correctly an
**unchanged axiomatized callee**, and the fix lives entirely in the argument
(the deep `render_text`/`name_is_text = True` step), not in the axiom.

**Soundness check (G-AX):** `axiom_check.py` imports the REAL
`sphinx.ext.autodoc.mock._make_subclass` (the very module the gold patch edits)
and asserts:
  (Ensures) `_make_subclass(name, module).__display_name__ == module + '.' +
    name` on 98 boundary + 20 000 fuzz textual `(name, module)` pairs (including
    `name` = `''`, `'~T'`, `'9'`, dotted, non-ASCII), and the result is a
    `_MockObject` subclass;
  (Requires) `_make_subclass(name, module)` RAISES for every input the
    precondition excludes — `TypeError` for every non-textual `name` (`TypeVar`,
    `object`, `list`, `dict`, `tuple`, `int`), `ValueError` for a textual
    `name` carrying a NUL (a 9-position NUL sweep: leading / interior / trailing
    / sole) AND `UnicodeEncodeError` for a textual `name` carrying a lone
    surrogate (an 8-name sweep over the D800/DBFF/DC00/DFFF boundaries in
    leading / interior / trailing / sole positions) — confirming the
    textual + NUL-free + surrogate-free precondition is genuinely required on
    all three halves, not over-claimed;
  (end-to-end) the subscript behaviour the fix targets: `_make_subclass(str(key),
    module)` succeeds for a `TypeVar` index and names the result `module +
    '.' + str(key)` (e.g. `mod.~T`), whereas `_make_subclass(key, module)` with
    the raw `TypeVar` index raises — exactly the issue's `mock.SomeClass[T]`
    failure. Exit 0 iff every observation matches.
Imports nothing beyond the standard library `typing` and the repo module under
test; no flag dependency (the callee takes no relevant keyword). Docs/source:
the function body shown above at `mock.py:71-76`.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned fuzz seed: `7889`** (module constant `SEED`; `N_FUZZ = 100_000`).

**Shadow.** The `impl-start`..`impl-end` region of `model.py` copied VERBATIM
(comments included) with only the contract calls removed — the two `Assert(...)`
lines and the two `# invariants-start`/`-end` blocks. Verified mechanically:
after stripping those, the shadow body is line-for-line identical to the impl
region, so both `while` loops that materialise the display name code point by
code point execute as written. The `@Pure` helper `render_text` is copied the
same way (minus its `Ensures`); `PSeq`/`ToSeq` are realised by an immutable
tuple shim (`take`/`drop`/`+`/`len`/`[]`/`==`).

**`@ContractOnly` callee is CALLED, not assumed.** `display_name` has no body to
copy, so the shim invokes the REAL `sphinx.ext.autodoc.mock._make_subclass`
(§1/§3.1, `mock.py:71-76`) and reads `__display_name__` off the fabricated class.
Its return value (`produced`) is dead in the model once `Assert` is stripped, so
it is captured through a trace slot and diffed against the oracle as a SECOND
observable alongside the loop-built `result` — the axiom's Ensures is therefore
exercised on every input rather than trusted.

**Oracle.** The real patched repo function, **called** (not transliterated):
`_MockObject.__getitem__` (§1, `mock.py:55`, body 56), which the gold patch
rewrites to `_make_subclass(str(key), self.__display_name__, self.__class__)()`.
The gate applies `patch.diff` and sets `PYTHONPATH=/testbed`, so `mock[key]` IS
the patched subscript. The parent placeholder carrying the module under test is
built in-container exactly as `_make_subclass` builds one
(`type(name, (_MockObject,), {...})`), so no context is unavailable and nothing
needs transliterating. Observable: `type(mock[key]).__display_name__`.

**Type bridge (§2, inverted).** The real input is generated first and the model
input derived from it, so every sample is by construction the bridge image of a
real one: `key_is_text = isinstance(key, str)`,
`key_text = [ord(c) for c in str(key)]`, `module = [ord(c) for c in display_name]`;
on the output side `List[int]` → `str` via `chr`, with `46 == ord('.')`. A raise
on either side is captured as `("err", <exception type>)`, so the two sides are
compared on failure as well as on success.

**Input domain.** `Requires` constrains only the index's textual rendering (no
NUL, no surrogate 55296..57343) — exactly the names CPython's `type()` rejects
per §3.1 — so renderings carrying either are out of domain and excluded (G-AX
covers that the real callee raises there). The domain is not narrowed further:
`module` is unconstrained by `Requires`, so NUL-bearing and surrogate-bearing
modules ARE generated and must still agree (the callee only concatenates
`module`). Every sample is asserted to satisfy `Requires` before use, and the
axiom shim re-asserts its own precondition, so a bridge bug exits 2 rather than
passing silently.

**Inputs: 100 324 Requires-satisfying** (324 boundary + 100 000 seeded fuzz;
≈50 041 textual / ≈50 283 non-textual indices). Boundary block covers the empty
module (outer loop zero iterations), the empty index (inner loop zero
iterations), both empty, single code point, non-ASCII/space/tab indices, the
exact F2P shape `TypeVar('T')` (the issue's `mock.SomeClass[T]`), covariant and
contravariant TypeVars, classes, ints, big ints, floats, `inf`, `None`, bools,
list/tuple/dict/frozenset/bytes/complex/`Ellipsis`/`range`/`slice` indices, and
NUL-/surrogate-bearing modules — so both `key_is_text` branches and both
loop-taken/loop-skipped shapes are exercised.

**Capability to fail (recorded negative controls).** Against a replica whose
`__getitem__` is the PRE-PATCH `_make_subclass(key, ...)`, the check FAILS on the
non-textual indices (`~T`, `int`, …: shadow `'.~T'` vs oracle `TypeError`) — it
genuinely exercises the branch the gold patch changed. Six shadow mutations were
all caught: separator `46→47` (exit 1), separator dropped (1), `name_is_text =
True` → `key_is_text`, i.e. the pre-patch omit-render mutation (2), key loop
skipped (1), module loop skipped (1), and module/key swapped at the axiom call
(1).

**Verdict.** Exit 0 iff zero disagreements; the final stdout line is a JSON
object with `status`, `checked`, `disagreements`, and `seed`. stdlib + the repo
module under test only.
