# mapping.md — django__django-11815

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e02f67ef2d03d48128e7a118bf75f0418e24e8ac`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every callee the modeled function relies on.

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `referenceEnumMember (module className memberName payloadText payloadImports)` | `EnumSerializer.serialize(self)` — `django/db/migrations/serializer.py:120` (body `120`–`125`) | the modeled changed function (serializes one enum member to source text + imports) |
| `memberReference (module className memberName)` | the `'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)` format expression — `serializer.py:124` post-patch | pure spec: the source reference text for one enum member |
| `referenceImports (module)` | the `{'import %s' % module}` import set — `serializer.py:125` post-patch | pure spec: the imports the reference needs |
| `quotedName (name)` | the `%r` formatting of the member name (`serializer.py:124` post-patch) | pure spec: a symbolic name rendered as a single-quoted token |

Inputs of `referenceEnumMember` and their repo origin (all read at `serializer.py:121`–`123`):

| Lean param | repo expression | notes |
|---|---|---|
| `module` | `enum_class.__module__` where `enum_class = self.value.__class__` | the enum type's defining module |
| `className` | `enum_class.__name__` | the enum type's name |
| `memberName` | `self.value.name` | the member's symbolic name (the post-patch key) |
| `payloadText` | `serializer_factory(self.value.value).serialize()[0]` | the member's stored value, serialized — the pre-patch key; **read-only, must not reach output** (directive 5) |
| `payloadImports` | `serializer_factory(self.value.value).serialize()[1]` | imports of the serialized payload — pre-patch merged into the import set; **read-only, must not reach output** |

The pre-patch repo symbols the change removes (refinement audit only, not in the
consumer spec view): the `v_string, v_imports = serializer_factory(self.value.value).serialize()`
call (`serializer.py:123`) and the `*v_imports` splat into the import set
(`serializer.py:124`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (`module`, `enum_class.__name__`, `self.value.name`, the returned reference string) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat / `%`-interpolation of plain `%s` ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| the returned `set` of import strings | `List (List Char)` | the post-patch import set is the singleton `{'import %s' % module}`; modeled as the one-element list `["import " ++ module]`. Set membership ↔ list membership; the post-patch set has exactly one element so order is immaterial |
| `'%r'` applied to a symbolic name (the member name) | `quotedName` = `['\''] ++ name ++ ['\'']`, under the spec's `require ∀ c ∈ memberName, isIdentChar c` | on the identifier alphabet (letters/digits/underscore — `isIdentChar`, encoded as an explicit `require` precondition of `referenceEnumMember`), `repr(name)` is exactly `'` + name + `'` — single quotes, no escaping. The spec claims nothing outside this domain. mapping.md §3 records why the alphabet makes this exact. |
| `self.value.value` (the member payload) | `payloadText : List Char` (+ `payloadImports`) | the already-serialized payload string and its imports — supplied but unused post-patch (the bug fix) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because every operation is plain string concatenation /
interpolation over code points.

## 3. Callee provenance and the `%r` exactness argument

### 3.1 No consumed axioms, no A-reference deep model
The changed operation — choosing the member's **symbolic name in subscript form**
(`module.Class['NAME']`) over the member's **serialized value in call form**
(`module.Class(value)`), and emitting only the module import — is built entirely
from plain string interpolation over the inputs. It is modeled DEEPLY in the
`pure` region (`memberReference`, `quotedName`, `referenceImports`). Per
directive 7 the operation the patch changes is never axiomatized; there is no
outside callee whose contract the proof consumes and no A-reference deep model.
`axiom_check.py` (G-AX) is therefore a skip stub.

The callees the surrounding (unchanged) code uses — `serializer_factory(...).serialize()`
on the payload, and `enum_class.__module__` / `__name__` / `self.value.name`
attribute reads — are NOT modeled: post-patch the payload serialization is no
longer called for the reference at all (its result is dead), and the three
attribute reads are pure data the bijection maps straight onto the inputs
`module` / `className` / `memberName`.

### 3.2 The `%r` exactness premise (the one subtlety)
Post-patch the member name is interpolated with `%r` (`repr`), not `%s`. For an
arbitrary `str`, `repr` may pick double quotes or insert backslash escapes
(e.g. `repr("has'quote")` is double-quoted, `repr("back\\slash")` doubles the
backslash), which plain `'` + name + `'` would NOT reproduce. The spec therefore
does not claim exactness for arbitrary strings: `referenceEnumMember` carries the
explicit precondition `require ∀ c ∈ memberName, isIdentChar c` (letters, digits,
underscore), and on that domain `repr(s)` is exactly `"'" + s + "'"` — single
quotes, no escaping. Enum members declared in a class body always lie in this
domain (their names are attribute names); names outside it are constructible
only through the functional `enum.Enum(name, dict)` API and never arise in
migration serialization of class-body enums. G-CONF restricts its fuzz alphabet
to the same identifier alphabet (letters/digits/underscore, non-empty, not
starting with a digit) — matching the spec's `require`, not silently narrower
than the spec — and the F2P member names (`A`, `B`, `DOTALL`) all lie in it.
This is recorded as an R-refinement over the `require`-pinned input domain, not
an axiom, because it is a property of the input domain, not of an external
callee.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`11815`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`memberReference` / `quotedName` / `referenceImports` (all R/I-tagged ops) to
Python and drives the REAL patched `EnumSerializer.serialize` via a minimal
stand-in enum member exposing only the attributes the method reads
(`__class__.__module__`, `__class__.__name__`, `.name`, `.value`). There are no
A-tagged callees to leave as real, because the post-patch reference construction
calls none.
