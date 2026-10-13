# mapping.md — sphinx-doc__sphinx-9461

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 939c7bb7ff7c53a4d27df067cea637540f0e1dad`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and the scoping of the change sites.

Repo files under change: `sphinx/domains/python.py`,
`sphinx/ext/autodoc/__init__.py`, `sphinx/util/inspect.py`.

The modeled site is `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleModifierTokens (firstFlag secondFlag : Bool)` | `PyProperty.get_signature_prefix(self, sig)` — `sphinx/domains/python.py:866` (class `PyProperty` at `:849`) | the modeled changed function: assembles the rendered modifier-token prefix |
| `annotationTokens (firstFlag secondFlag : Bool)` | the post-patch token-list assembly inside `get_signature_prefix` (`python.py:868-875` post-patch) | pure spec: the ordered modifier tokens for the two flags |
| `firstFlag : Bool` | `'abstractmethod' in self.options` (`python.py`, option declared at `:855`) | the abstract-method modifier flag |
| `secondFlag : Bool` | `'classmethod' in self.options` (NEW option `'classmethod': directives.flag`, post-patch `python.py:855`) | the class-method modifier flag — the behaviour the issue adds |

The pre-patch repo behaviour the change replaces (refinement audit only, not in
the consumer spec view): `prefix = ['property']` seeded with the kind token, the
abstract token inserted at the front via `prefix.insert(0, 'abstract')`, and **no
handling of the second flag** (`python.py:868-871` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `'abstractmethod' in self.options` (bool) | `firstFlag : Bool` | dict-membership truth ↔ `Bool`; present ↔ `true`, absent ↔ `false` |
| `'classmethod' in self.options` (bool) | `secondFlag : Bool` | dict-membership truth ↔ `Bool`; present ↔ `true`, absent ↔ `false` |
| each prefix token (`'abstract'`, `'class'`, `'property'`) — a Python `str` literal | a Lean `String` element of `out` | byte-identical string literal ↔ `String`; list order ↔ `List` order |
| the returned prefix string `' '.join(prefix) + ' '` | `out : List String` joined by the SAME `' '.join(...) + ' '` | the join is an unchanged R/I trailing op applied to the modeled token list; the observable (`test_pyproperty`) is the joined string. G-CONF compares the joined strings. |

The space-join and trailing-space are identical pre- and post-patch and on both
the model and the repo; the entire behavioural content of the change lives in
WHICH tokens, in WHAT order, populate the list — which is what `annotationTokens`
encodes. The carrier is `List String` because the operation is per-token list
assembly.

## 3. Callee provenance and change-site scoping

### 3.1 No axioms, no deep-model references
The modeled function calls no unchanged external callee whose contract the proof
must consume: it reads two dict-membership booleans and assembles a literal token
list. There is therefore **no axiom and no deep-model reference** (G-AX emits a
`status=skip` verdict, `axiom_check.py`). The one library op — the fixed
`str.join` + trailing space — is an R/I identity (§2), checked by G-CONF against
the real patched `get_signature_prefix`, not axiomatized.

### 3.2 Additional change sites (NOT separately modeled)
The gold patch also edits two further files, both pure Python *runtime
introspection* over the descriptor protocol and the class MRO, which lie outside
Velvet's expressible fragment and which it would be unsound to axiomatize (they
ARE changed functions — SPEC_GUIDE directive 7 forbids axiomatizing the function
under change):

- **`sphinx/util/inspect.py`** — `isclassmethod(obj, cls=None, name=None)` gains
  an MRO-walking branch (`for basecls in getmro(cls): basecls.__dict__.get(name)`)
  and `getdoc(...)` gains a classmethod-property docstring-lookup branch. These
  operate on live Python class objects, `__dict__`, `__func__`, and `getmro` —
  runtime reflection, not pure value computation.
- **`sphinx/ext/autodoc/__init__.py`** — `PropertyDocumenter.can_document_member`
  / `import_object` / `add_directive_header` gain handling for a
  `classmethod`-wrapped `property` (`isinstance(obj, classmethod) and
  inspect.isproperty(obj.__func__)`, `self.isclassmethod`), and `Documenter`'s
  `getdoc` call switches its `(self.parent, self.object_name)` arguments to
  `(self.object, membername)`. Again: descriptor-protocol introspection over live
  objects.

These two sites implement the *recognition and docstring-extraction* half of the
feature (so that a `@classmethod @property` is discovered and documented at all);
the modeled `python.py` site implements the *rendering* half (the
`:classmethod:` flag → `"class property "` prefix). The F2P test
`tests/test_domain_py.py::test_pyproperty` directly observes the modeled
rendering behaviour (the `[desc_annotation, "class property "]` node and the new
`:classmethod:` option). The other two F2P tests
(`test_ext_autodoc_autoclass::test_properties`,
`test_ext_autodoc_autoproperty::test_class_properties`) exercise the
introspection half. `patch.diff` is the gold patch **verbatim**, so all three
F2P tests are resolved by the shipped twin (G-RESOLVE); only the cleanly
expressible rendering site is given a Velvet `method`. (Precedent: sphinx-7590,
sphinx-10673 — multi-file patches whose F2P-relevant, expressible core is modeled
while reflection/rendering-only co-changes are documented here, not modeled.)

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9461`** so the
consumer-side verdict is reproducible. The input space is the four
flag-combinations (enumerated exhaustively first), re-sampled to honour the
≥10⁵-input budget; the R/I shadow transliterates `annotationTokens` + the space-join
and compares the joined string against the real patched `get_signature_prefix`.
