# mapping.md — django__django-12125

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 89d41cba392b759732ba9f1db4ff29ed47da6a56`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance. There are **no axioms** in this bundle (§3): the changed
operation is a pure straight-line dispatch that builds a reference string from
attributes of the input type object; nothing external is consumed.

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `typeReference (t : PyType)` | `TypeSerializer.serialize(self)` — `django/db/migrations/serializer.py:259` (changed line `:272`) | the modeled changed function: render the code reference + import for a type value |
| `renderType` *(pure)* | the body of that `serialize` method, modeled deeply | the per-kind reference string + import, spelled out |
| `PyType` *(structure)* | the type object `self.value` (a Python `type`), reduced to the attributes the method reads | input carrier |
| `RenderedType` *(structure)* | the `(string, imports)` 2-tuple the method returns | output carrier |

No `axiom`/`opaque` declarations: every operation in the `do` block is a closed
string/`Option` construction over the input fields (all R/I), so the bundle has
no consumed axiom and no A-reference deep model of an outside callee. G-AX skips.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the type object `self.value` (a Python `type`) | `PyType` structure | the five attributes the method reads, below |
| `self.value is models.Model` | `PyType.isSpecialModel : Bool` | the first special-case identity test |
| `self.value is type(None)` | `PyType.isNoneType : Bool` | the second special-case identity test |
| `self.value.__module__ == builtins.__name__` | `PyType.isBuiltin : Bool` | the module-is-builtins test (the method assumes `hasattr(__module__)`, true of every `type`) |
| `self.value.__module__` (a `str`) | `PyType.module : List Char` | `s` ↔ `s.toList`; `len` ↔ `.length`; `"."` join ↔ `['.']`; `++` ↔ str concat |
| `self.value.__qualname__` (a `str`) | `PyType.dottedName : List Char` | the within-module dotted location **including any enclosing classes** (e.g. `Outer.Inner`); for a top-level type it equals `shortName` |
| `self.value.__name__` (a `str`) | `PyType.shortName : List Char` | the type's own name without enclosing scope (e.g. `Inner`); the last dotted component of `dottedName` |
| `("models.Model", set())` | `⟨"models.Model".toList, none⟩` | special-case literal, empty import set |
| `("type(None)", set())` | `⟨"type(None)".toList, none⟩` | special-case literal, empty import set |
| `(__name__, set())` for a builtin | `⟨shortName, none⟩` | builtins branch, no module prefix, empty import set |
| `("%s.%s" % (module, __qualname__), {"import %s" % module})` | `⟨module ++ ['.'] ++ dottedName, some ("import ".toList ++ module)⟩` | the general branch — **the patched line** |
| the `imports` set (always ∅ or a singleton in these branches) | `Option (List Char)` | `none` ↔ `set()`; `some s` ↔ `{s}` |

`List Char` is the carrier for every string because the operation is
string-construction (concatenation), total and sound in Lean.

## 3. Callee provenance — none

The method calls no operation it does not change: it only reads attributes of the
input type object and concatenates strings. The behavioural change is a property
of the **input attribute selected** (the enclosing-class-qualified dotted name
vs. the bare short name) when building the general-branch reference, modeled
deeply in `renderType`. Hence: no consumed axiom, no A-reference, no G-AX
obligation (G-AX skips, as in django__django-12713 / astropy__astropy-13236).

### 3.1 Flag dependency (for G-CONF construction)
The branch precedence is: special-model → none-type → builtins → general. The
general branch (the patched one) fires exactly when the type is neither special
case nor a builtin. `dottedName` and `shortName` differ **iff** the type is
nested inside another class (an inner class); for a top-level type they coincide,
so the patch is observable only on nested classes — the F2P case.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12125`**. Its ORACLE
constructs **real `type` objects** with controlled `__module__` / `__qualname__`
/ `__name__` (plus the genuine `models.Model`, `type(None)`, and a builtin) and
runs the **real patched `TypeSerializer.serialize`** in-container; the SHADOW is
`renderType` transliterated to Python. All ops are R/I (`conf_skip = false`).

## 5. F2P note

`test_serialize_nested_class` is the test the modeled change drives: it asserts a
nested class serializes to `module.Outer.Inner` (the enclosing-class-qualified
path), not `module.Inner`. The co-listed `test_serialize_numbers` is **not driven
by the changed function** (it exercises `Decimal`/`Money`/float serialization via
the deconstruct path, untouched by this patch); it co-flips in the harness and is
not modeled here.
