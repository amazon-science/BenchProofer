# mapping.md — astropy__astropy-7166

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 26d147868f8a891a6009a25cd6a8576d2e1bd747`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `astropy/utils/misc.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveMemberDocstrings (members : List Member)` | `InheritDocstrings.__init__(cls, name, bases, dct)` — `astropy/utils/misc.py:523` (member loop at `:530-537`) | the modeled changed function: the metaclass initializer that fills in each member's documentation from the base classes |
| `Member` *(structure)* | one iteration item `(key, val)` of `dct.items()` (`misc.py:530`) abstracted to the observations the loop reads | the touched fields of a single class member |
| `Member.isCallable` | `inspect.isfunction(val)` (`misc.py:531`) | callee observation: is the member a plain function |
| `Member.isProperty` *(deep-model reference — A-reference)* | `inspect.isdatadescriptor(val)` (post-patch `misc.py:531`) | callee observation: is the member a data descriptor (a `property` is one). The post-patch disjunct. |
| `Member.isPublic` | `is_public_member(key)` (`misc.py:524-528`, called `:532`) | callee observation: nested visibility predicate |
| `Member.ownDoc` | `val.__doc__` read at `misc.py:533` (`None` ↔ `none`) | the member's own documentation before the loop runs |
| `Member.inheritedDoc` | the `super_method.__doc__` of the first base in `cls.__mro__[1:]` that has the member (`misc.py:534-537`); `none` if no base supplies it | the documentation resolved from base classes in MRO order |
| `eligible (m : Member)` | the `if (...)` guard at `misc.py:531-533` (post-patch) | pure spec: a member qualifies for inheritance |
| `finalDoc (m : Member)` | the per-member outcome of the loop body: `val.__doc__` is set to `super_method.__doc__` iff the guard holds, else unchanged | pure spec: a single member's resulting documentation |
| `resolvedDocs (ms : List Member)` | the loop's effect on every member's `__doc__`, in `dct.items()` order | pure spec: all members' resulting documentation |

The pre-patch guard (refinement audit only, not in the consumer spec view) is
`inspect.isfunction(val) and is_public_member(key) and val.__doc__ is None`
(`misc.py:531-533` pre-patch) — the property disjunct is absent.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the repo. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `dct.items()` — the members of one class body, in insertion order | `List Member` | the `i`-th `(key, val)` pair ↔ `members[i]`; `len(dct)` ↔ `members.length`; iteration order ↔ `List` order |
| `bool(inspect.isfunction(val))` | `Member.isCallable : Bool` | `True ↔ true`, `False ↔ false` |
| `bool(inspect.isdatadescriptor(val))` | `Member.isProperty : Bool` | `True ↔ true`, `False ↔ false`. A `property` object is a data descriptor; G-AX confirms `isdatadescriptor(property) == True`, `isfunction(property) == False`. |
| `bool(is_public_member(key))` | `Member.isPublic : Bool` | `True ↔ true`, `False ↔ false` |
| `val.__doc__` (a `str` or `None`) | `Member.ownDoc : Option (List Char)` | `None ↔ none`; `s ↔ some s.toList`; documentation text compared character-wise |
| the resolved base documentation `super_method.__doc__` (`str` or `None`) | `Member.inheritedDoc : Option (List Char)` | `None ↔ none`; `s ↔ some s.toList`. Captures the *result* of the `for base in cls.__mro__[1:]` walk: the first base that has the member supplies its `__doc__`; if none does, `none`. |
| the member's `__doc__` after the loop | one element of `resolvedDocs members` | `None ↔ none`; `s ↔ some s.toList` |

`List Char`/`Option` indexing in Lean is total and sound. The carrier for member
documentation is `Option (List Char)` because the operation either keeps the
member's own (possibly absent) documentation or replaces it with the resolved
base documentation (also possibly absent) — `None`/`none` is a first-class value.

The MRO walk (`for base in cls.__mro__[1:] … getattr(base, key, None)`) is
**unchanged** by the patch; its result is pre-computed into `Member.inheritedDoc`
(an input field, an R-refinement of an unchanged callee chain). The patch
changes ONLY the membership guard, so collapsing the unchanged walk to its
observed result is faithful and keeps the model focused on the changed op.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `isProperty` / `eligible` deep model ↔ the post-patch guard (A-reference)
**Callees:** CPython `inspect.isfunction`, `inspect.isdatadescriptor`, and the
nested `is_public_member`. The changed eligibility operation is modeled
**deeply** by `eligible` (over the `Member` fields) in the `pure` region; there
is **no consumed axiom**. The post-patch guard is, verbatim:

```python
if ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and
        is_public_member(key) and
        val.__doc__ is None):
```

which is exactly `(isCallable ∨ isProperty) ∧ isPublic ∧ ownDoc.isNone` =
`eligible m`. The single behavioral change is the added `or
inspect.isdatadescriptor(val)` disjunct: a `property` (and any data descriptor)
now qualifies. The F2P test `test_inherit_docstrings` observes precisely this —
a `@property` with no own docstring inherits the base property's docstring.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `inspect.isfunction`,
`inspect.isdatadescriptor`, the REAL `is_public_member` (lifted verbatim from
the metaclass), and the REAL metaclass-style MRO documentation walk over a
matrix of member kinds (plain functions, properties, other data descriptors,
non-descriptors), visibilities (dunder / public / private / short underscore
names), and own-doc states, plus randomized fuzzing. It asserts that for every
case the deep model `eligible`/`finalDoc` over the bridged `Member` equals the
post-patch guard's outcome on the real objects. Imports only stdlib `inspect`.
Exit 0 iff sound.

### 3.2 No consumed axioms
The MRO documentation walk is unchanged by the patch and is collapsed to the
input field `inheritedDoc` (an R-refinement of an unchanged callee, not an
axiom the proof consumes). There is no `axiom` declaration in `Solution.lean`;
`meta.json axioms` is empty.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7166`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `eligible`/`finalDoc`/`resolvedDocs` (R/I-tagged ops) to Python
and bridges I/O via this table; the ORACLE is the real patched
`InheritDocstrings` metaclass driven over randomly generated class bodies.
