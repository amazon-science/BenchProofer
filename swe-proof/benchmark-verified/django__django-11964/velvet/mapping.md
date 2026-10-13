# mapping.md — django__django-11964

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fc2b1cc926e34041953738e58fa6ad3053059b22`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/models/enums.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `memberToStr (member : Member)` | `Choices.__str__(self)` — `django/db/models/enums.py:61` (the `Choices` class body; the method is *added* by the patch at line 62-66 post-patch) | the modeled changed function: how an enumerated member renders when cast to text |
| `Member.value` | `self.value` — the underlying payload of an enum member (set per member, e.g. `Suit.DIAMOND.value == 1`, `YearInSchool.FRESHMAN.value == 'FR'`) | the member's underlying value |
| `Member.defaultLabel` | the generic object rendering a member carries by default — `enum.Enum.__str__` returns `"%s.%s" % (self.__class__.__name__, self._name_)`, i.e. the qualified `Owner.NAME` token (e.g. `MyChoice.FIRST_CHOICE` in the problem statement) | the pre-fix rendering, modeled only so the prepatch can reproduce it |
| `renderValue (v : MemberValue)` | the `str(self.value)` coercion in the new `__str__` body | pure spec: the text form of a payload (decimal for a number, identity for text) |
| `MemberValue` (`intVal`/`strVal`) | the payload of an `IntegerChoices` member (a Python `int`) resp. a `TextChoices` member (a Python `str`) | the two payload shapes `str(...)` reacts to differently |

No axioms, no A-reference deep model of an outside callee: `str(self.value)` for
the `int`/`str` payloads of `IntegerChoices`/`TextChoices` is total, pure, and
modeled directly (`renderValue`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an `IntegerChoices` member value (a Python `int`) | `MemberValue.intVal (n : Int)` | Python `int` `n` ↔ `MemberValue.intVal n`; arbitrary-precision signed integer ↔ Lean `Int` (both unbounded). The image's `int` is unbounded, matching `Int`. |
| a `TextChoices` member value (a Python `str`) | `MemberValue.strVal (s : List Char)` | Python `str` `s` ↔ `MemberValue.strVal s.toList`; `len(s)` ↔ `s.length`; empty `str` ↔ `[]` |
| `str(self.value)` for a numeric payload (`str(int)`) | `(toString n).toList` | both render an integer as its decimal text: optional leading `-` for negatives, no `+`, no leading zeros, no thousands separators. Lean `toString (n : Int)` == Python `str(n)` on every integer. |
| `str(self.value)` for a textual payload (`str(str)`) | `s` (identity) | `str(s)` is the identity on a `str`; identity on `List Char`. |
| the method's `str` return | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char` |

The label/repr of the member, the enum machinery (metaclass, `_value2label_map_`,
`__contains__`, `names`/`choices`/`labels`/`values` properties) are UNCHANGED by
the patch and are not observed by `__str__`; they are outside the modeled frame.

## 3. Callee provenance

None. `renderValue` is a deep, self-contained model of `str(self.value)` for the
two payload types; it consumes no axiom and references no outside callee. G-AX is
therefore skipped (`meta.json gates.G-AX.status = "skip"`, no `axiom_check.py`).

The pre-fix behaviour `Member.defaultLabel` models `enum.Enum.__str__`'s
`Owner.NAME` token. It is used ONLY in `Solution_prepatch.lean` (to reproduce the
bug) and never appears in a postcondition the gold-faithful proof consumes, so it
is not an axiom either — it is an input field whose concrete value is irrelevant
to the post-patch spec.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11964`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`renderValue`/`memberToStr` (R/I-tagged ops) to Python and compares against the
oracle: real `IntegerChoices`/`TextChoices` members built (via the enum
functional API) with the fuzzed payloads, rendered by the patched
`Choices.__str__` (`str(self.value)`). There are no A-tagged callees in the impl
region, so the shadow is pure R/I.
