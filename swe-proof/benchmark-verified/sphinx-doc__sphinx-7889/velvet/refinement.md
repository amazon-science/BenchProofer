# refinement.md — sphinx-doc__sphinx-7889

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`subscriptMock` `do` block, the deep `buildSubclass` model, and the `textForm`
coercion) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so a verifying impl
must TERMINATE and produce `subscriptSpec displayName key`. (An earlier
revision used partial correctness, which a same-spec diverging impl — `while
true` with a trivial invariant followed by a wrong return value — vacuously
satisfied; the G-PANEL-1 audit found that counterexample, and total semantics
excludes the whole class. The real `__getitem__` body is a single straight-line
call with no loops, so it trivially terminates.)

## A. The subscription site — `_MockObject.__getitem__` (`sphinx/ext/autodoc/mock.py:55`)

Gold hunk:
```
-    def __getitem__(self, key: str) -> "_MockObject":
-        return _make_subclass(key, self.__display_name__, self.__class__)()
+    def __getitem__(self, key: Any) -> "_MockObject":
+        return _make_subclass(str(key), self.__display_name__, self.__class__)()
```

| # | Solution.lean impl op (`subscriptMock`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `key : Key` | `key: Any` arg of `__getitem__` | R | the runtime key (`Any`) ↔ `Key`: a textual key ↔ `.str s`, a non-textual object ↔ `.obj (str(o))` (mapping.md §2). The type annotation widening `str`→`Any` is a documentation-level change carrying no runtime behavior; the runtime content is the value modeled by `Key`. |
| A2 | parameter `displayName : String` | `self.__display_name__` | R | identity on the string content (mapping.md §2). |
| A3 | `let name := textForm key` | `str(key)` | I | the added coercion: take the textual form of the key. `textForm` is the concrete transliteration of `str(...)` — `str` of a string is itself, `str` of a non-textual object is its rendering (mapping.md §2). Transliterated and refuted by G-CONF. |
| A4 | `let out := buildSubclass displayName name` | `_make_subclass(str(key), self.__display_name__, self.__class__)` | A-reference + I | the unchanged callee `_make_subclass`, modeled **deeply** (`buildSubclass`, pure region): on an admissible textual name it succeeds with display name `module + '.' + name`; on a textual name carrying a NUL byte (`type()`-illegal) it raises `ValueError` (modeled `valueError` via `nameRejected`); on a non-textual name it raises `TypeError`. The equality of that deep model to the real callee — including the NUL-byte `ValueError` leg — is the **A-reference** G-AX validates (mapping.md §3.1). The call op itself is **I**. |
| A5 | `return out` (`Except MockErr String`) | `_make_subclass(...)()` instance returned | R | instantiation does not alter `__display_name__`, the only observed field; success/`TypeError` ↔ `Except.ok`/`Except.error` (mapping.md §2). |

Discriminating content of the change — the textual form is taken **before**
construction (A3), so a non-textual key (e.g. a `TypeVar`) reaches `_make_subclass`
as a `str` and construction SUCCEEDS instead of raising `TypeError`. This lives in
`subscriptSpec dn k = buildSubclass dn (textForm k)` (always `Except.ok`, model) ⇔
`_make_subclass(str(key), ...)` (real). The pre-patch `__getitem__` passed `key`
raw; `Solution_prepatch.lean` reproduces that (`buildSubclass displayName key`)
and **fails** `out = subscriptSpec displayName key` on a `.obj` key (error vs ok)
— the exact `TypeError`-vs-success the F2P `test_MockObject` (parametrized
`mock.SomeClass[T]` with a `TypeVar`) observes (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation the patch **adds** — the `str(key)`
coercion — is modeled **deeply** (`textForm`, step A3, an I op), not hidden behind
an axiom. The unchanged callee `_make_subclass` is an **A-reference** (deep model
`buildSubclass`, G-AX-validated), not a consumed axiom; there are no consumed
axioms, and nothing about the function under change is axiomatized.

## C. verify(Solution) ⇒ resolved

`subscriptMock` verifies only if its output equals `buildSubclass displayName
(textForm key)` (A3+A4): the textual form is taken first, so construction
succeeds for every key with display name `displayName ++ "." ++ <textual key>`.
By R (`Any ↔ Key`, `str(self.__display_name__)` identity, instantiation identity)
the verified subscription equals `_make_subclass(str(key), self.__display_name__,
...)()` on the tested inputs; by G-AX the deep model `buildSubclass` equals the
real `_make_subclass` (A-reference) and `str()` yields the assumed textual form;
by G-CONF the R/I transliteration of `textForm` + the real callee agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
callee — and the gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: the A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
