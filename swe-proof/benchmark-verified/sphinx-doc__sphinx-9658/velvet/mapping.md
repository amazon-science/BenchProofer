# mapping.md — sphinx-doc__sphinx-9658

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 232dbe41c5250eb7d559d40438c4743483e95f15`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `sphinx/ext/autodoc/mock.py`. The behavior is observed
through `sphinx/util/typing.py::restify` (the F2P test `test_restify_mock`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderReference (modulePath createdName : List Char)` | the reference `restify(cls)` renders for a stand-in placeholder, where `cls` is a `_MockObject` subclass instance (`sphinx/ext/autodoc/mock.py:25-79`). `restify` is a dispatch over `cls`, and which arm it takes is decided by `cls.__module__` and (for one arm) `cls.__qualname__` — see the four rows below | the modeled behavior: build the reference from a placeholder's module path and reported simple name, through `restify`'s own dispatch |
| `renderedReference` rule 1 (`abbreviatedNamespace` + `aliasFactoryName`) | `restify`'s `inspect.isNewType(cls)` arm, `':py:class:`%s`' % cls.__name__` (`sphinx/util/typing.py:119-125`, py<3.10 branch at `:125`). `isNewType` is True exactly when `cls.__module__ == 'typing'` and `cls.__qualname__ == 'NewType.<locals>.new_type'` (`sphinx/util/inspect.py:213-223`) | reserved: module path dropped, reported name alone |
| `renderedReference` rule 2 (`coreNamespaceA`/`coreNamespaceB`) | `restify`'s `cls.__module__ in ('__builtin__', 'builtins')` arm (`sphinx/util/typing.py:133-140`). A placeholder has `__args__` (every attribute access on a `_MockObject` succeeds), so the `hasattr(cls, '__args__')` sub-branch is taken and renders `':py:class:`%s`\\ [%s]' % (cls.__name__, ', '.join(...))` with `cls.__args__` an empty mock iterable (`_MockObject.__iter__` yields nothing), i.e. an empty element list | reserved: module path dropped, reported name, empty element-list tail |
| `renderedReference` rule 3 (`abbreviatedNamespace`, other names) | `_restify_py37`'s `hasattr(cls, '__qualname__')` arm, `cls.__module__ == 'typing'` sub-branch: `':py:class:`~%s.%s`' % (cls.__module__, cls.__qualname__)` (`sphinx/util/typing.py:193-195`) | reserved: dotted path behind the abbreviation mark |
| `renderedReference` rule 4 (any other module path) | `_restify_py37`'s `hasattr(cls, '__qualname__')` arm, `else` sub-branch: `':py:class:`%s.%s`' % (cls.__module__, cls.__qualname__)` (`sphinx/util/typing.py:193, 196`) | general: plain dotted path |
| `modulePath` argument | the placeholder's `__module__`: the parent placeholder's `__display_name__` (= `module + '.' + name`), set in `_make_subclass` (`sphinx/ext/autodoc/mock.py:74-75`) | dotted module path the placeholder lives under |
| `createdName` argument | the `name` a placeholder was created to stand for: the `name` arg of `_make_subclass`, stored post-patch as the class attribute `__name__` (`sphinx/ext/autodoc/mock.py:77`) | the simple name the placeholder stands for |
| `reportedName (createdName)` | the placeholder's `__qualname__`, set in `_MockObject.__init__` to `self.__name__` post-patch (`sphinx/ext/autodoc/mock.py:44`) | the simple name the placeholder reports to `restify` |
| `coreNamespaceA` / `coreNamespaceB` / `abbreviatedNamespace` / `aliasFactoryName` | the string literals `'__builtin__'` / `'builtins'` (`sphinx/util/typing.py:133`), `'typing'` (`sphinx/util/typing.py:194`, `sphinx/util/inspect.py:221`) and `'NewType.<locals>.new_type'` (`sphinx/util/inspect.py:221`) | the module paths and the one simple name `restify`'s dispatch reserves |
| `openMark` / `closeMark` / `elementListTail` / `abbreviationMark` | the literal fragments of `restify`'s format strings: `':py:class:`'`, `'`'`, `'`\\ []'`'s tail `'\\ []'`, and the `'~'` of `':py:class:`~%s.%s`'` | the input-independent decorations of each rule |

**Post-patch `__name__` reaches both dispatch keys.** The patch stores the
creation name as `__name__` *and* makes `__qualname__` equal `__name__`. `restify`
rule 2 reads `cls.__name__`; rules 3/4 and `isNewType`'s second test read
`cls.__qualname__`. Post-patch these are the same string, so a single
`reportedName createdName` models the trailing segment of all four rules. This is
also why rule 1 is reachable at all: pre-patch `__qualname__` was `''`, so
`isNewType` was never True for a placeholder.

The pre-patch repo state the change fixes (refinement audit only, not in the
consumer spec view): `_MockObject.__init__` hard-coded `self.__qualname__ = ''`
(`mock.py:43` pre-patch) and `_make_subclass` carried no `__name__` attribute, so
every placeholder reported the empty simple name regardless of the name it was
created for — the rendered reference dropped its trailing segment. The patch
changes behavior in ALL FOUR rules (measured, not argued: see §5), so no rule may
be excluded from the modeled domain.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python `str` (`__module__`, `__name__`, `__qualname__`, and `restify`'s rendered output) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; the dot literal `'.'` ↔ `['.']` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `restify`'s per-rule format strings | modeled explicitly, NOT abstracted away | The decorations `restify` places around the symbol text are **not** a single input-independent wrapper: which decoration is used depends on `cls.__module__` (and, for rule 1, on `cls.__qualname__`). The model therefore reproduces `restify`'s arm order and each arm's decoration literally (`openMark`, `closeMark`, `elementListTail`, `abbreviationMark`), and G-CONF compares the FULL rendered string against the real `restify`. |
| `cls.__args__` on a placeholder in rule 2 | modeled as the constant `elementListTail` | a placeholder answers every attribute access, so `hasattr(cls, '__args__')` is True, and the resulting mock object iterates empty (`_MockObject.__iter__` returns `iter([])`), so `', '.join(restify(arg) for arg in cls.__args__)` is `''` for every placeholder. The bracketed element list is therefore the constant `'[]'` on the modeled domain — an input-independent constant, verified over all rule-2 inputs by G-CONF. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point string concatenation.

## 3. Callee provenance (kind-A)

**None.** There is no axiomatized callee and no A-reference deep model of an
outside callee. The behavior under specification — that a placeholder's reported
simple name is the name it was created to stand for, and the reference is
whichever of `restify`'s four rules the module path selects with that name in the
trailing position — is a total function of the placeholder's own carried data
(`__module__`, the creation `name`), modeled DEEPLY in the `pure` region
(`reportedName`, `renderedReference`). The surrounding object machinery
(`_MockObject.__getattr__`, `_make_subclass`) is collapsed into the two string
inputs; `restify`'s dispatch is *not* collapsed — it is modeled leg by leg — and
so nothing is owed a contract. Hence `axioms` is empty and `axiom_check.py` is
omitted (G-AX = skip, mirroring the no-axiom exemplar `astropy__astropy-13236`).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`9658`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`reportedName`/`renderedReference` (R/I-tagged ops) to Python — the reported name
is the creation name; the rendered reference is the four-rule dispatch on the
module path — and compares it against the patched repo's real `restify` applied to
a real placeholder of the same shape. The run prints per-rule hit counts and
FAILS if any of the four rules is never exercised, so a shadow that is silently
untested on a rule cannot pass.

**Two oracle constructors, cross-validated.** `oracle_by_walk` is the literal F2P
access path (`mock([root])` + attribute access). `oracle_direct` calls
`_make_subclass(created_name, module_path)()` — the very constructor
`_MockModule.__getattr__`/`_MockObject.__getattr__` invoke (`mock.py:94`, `:62`).
Every walk-reachable input is checked against BOTH, so the direct constructor is
not taken on trust; the last run agreed on all of them.

The direct constructor is *necessary*: a leaf reached by an attribute walk always
carries a module path prefixed by its mock root, and the root must not name an
already-importable module (below), so the walk can never realise the reserved
module paths `__builtin__` / `builtins` / `typing`. Fuzzing only the walk exercises
rule 4 alone and is blind to rules 1-3 — which is exactly how an earlier
single-rule shadow passed while the model diverged on `('__builtin__', 'Class')`.

Fuzz-root discipline (walk leg): `mock([mod])` only intercepts an import whose
name is (a descendant of) a name passed to `mock`. A *bare* random identifier that
happens to name an already-imported real stdlib module (e.g. `os`, `string`,
`time`) makes `importlib.import_module(mod)` return the REAL module, not a mock
root, and the attribute walk then fails on a non-existent attribute — a fuzzer
artifact, not a behavioral disagreement. Random walk roots therefore carry the
fixed, not-importable prefix `mockroot9658_`, guaranteeing a fresh mock root every
iteration. The canonical boundary roots (`unknown`, `torch`, `a`, `pkg`) were each
checked to be non-findable modules at the pinned base/patched commit.

The direct leg's distribution draws a reserved module path with weight ≈0.30 and
a near-miss on one with weight ≈0.10 (`typings`, `__builtins__`, `builtin`,
`a.typing`, `TYPING`), and draws the reserved simple name and near-misses of it
with weight ≈0.25/≈0.075, so the exact extent of each guard is fuzzed rather than
assumed.

## 5. Per-rule behavior change (why the domain is not narrowed)

Measured at `base_commit` vs the patched tree by importing each tree's own
`sphinx` under an explicit `PYTHONPATH` (an earlier reading that showed "no
delta" was a harness bug: the scratch dir shadowed the cwd on `sys.path`, so both
trees imported the same `sphinx`). Real `restify` output, pre-patch → post-patch:

| rule | input (`__module__`, creation name) | pre-patch | post-patch |
|---|---|---|---|
| 1 | `('typing', 'NewType.<locals>.new_type')` | `` :py:class:`~typing.` `` (rule 1 not taken: `isNewType` is False because `__qualname__` is `''`, so it falls through to rule 3) | `` :py:class:`NewType.<locals>.new_type` `` |
| 2 | `('__builtin__', 'Class')` | `` :py:class:`__builtin__.Class.__name__`\ [] `` (no `__name__` attribute exists pre-patch, so `cls.__name__` itself resolves through `_MockObject.__getattr__` to a further placeholder whose `repr` is its `__display_name__`) | `` :py:class:`Class`\ [] `` |
| 3 | `('typing', 'Foo')` | `` :py:class:`~typing.` `` | `` :py:class:`~typing.Foo` `` |
| 4 | `('unknown.secret', 'Class')` | `` :py:class:`unknown.secret.` `` | `` :py:class:`unknown.secret.Class` `` |

The gold patch changes the rendered reference on every one of the four rules
(rule 1 additionally becomes *reachable* only post-patch). Excluding the reserved
module paths by precondition would therefore drop real fixed behavior, so the
model covers all four rules instead and the pre-conditions region stays empty.

`Solution_prepatch.lean` encodes the pre-image of the one modeled line —
`__qualname__ = ''`, i.e. `simpleName := []` — which is exactly the pre-patch
rendering on rules 1, 3 and 4 (a dropped trailing segment). On rule 2 the real
pre-patch output carries the `__name__`-lookup artifact above instead of an empty
segment; the twin renders the empty segment there, which is *conservative*: it
still contradicts the rule-2 postcondition (which demands the trailing segment be
`createdName`), so the twin fails. The twin's contract is to fail the repaired
spec, and it does so on all five clauses (§ verdict).
