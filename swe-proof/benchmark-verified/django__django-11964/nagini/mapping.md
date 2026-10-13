# mapping.md — django__django-11964

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fc2b1cc926e34041953738e58fa6ad3053059b22`, states the type
abstraction, and gives the provenance of the single A-reference (the standard
string coercion the deep model is validated against).

Repo file under change: `django/db/models/enums.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_to_text(self)` | `Choices.__str__(self)` — the method ADDED to `Choices` (`django/db/models/enums.py:61`, inserted in the class body where the bare `pass` was at line 63) | the modeled changed behaviour: coercing a choice member to text |
| `Member` (model class) | a member of a `Choices`/`IntegerChoices`/`TextChoices` enumeration (`django/db/models/enums.py:61,66,71`) | minimal stand-in carrying only the two touched character sequences |
| `Member.value_text` | `str(self.value)` — the textual rendering of the member's `.value` (`enums.py`, the patched `__str__` body) | the member's value rendered as text (code points) |
| `Member.qualified_label` | `enum.Enum.__str__(self)` — the default diagnostic rendering `"Owner.NAME"` (CPython `Lib/enum.py`, the base `Enum.__str__`) | the pre-patch rendering the default `__str__` produced |

The pre-patch repo state the change replaces (for the refinement audit, not
referenced from the consumer spec view): `Choices` has an empty body (`pass`,
`enums.py:63`), so a member inherits `enum.Enum.__str__`, which returns the
diagnostic `"<ClassName>.<MEMBER_NAME>"` qualified label. The gold patch adds a
`__str__` returning `str(self.value)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` returned by `__str__` (and the value text it renders) | `List[int]` of Unicode code points | `s[k]` ↔ `value_text[k] == ord(s[k])`; `len(s)` ↔ `len(value_text)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |
| the choice member object | `Member` (minimal class with only the two touched character sequences) | `self.value` rendered ↔ `self.value_text`; the default `Enum.__str__` rendering ↔ `self.qualified_label` |
| `str(self.value)` coercion (the patched `__str__` body) | identity on the pre-rendered code-point list `value_text` | the value is carried already rendered to its text form; the int→decimal / str→identity coercion is the A-reference validated by axiom_check.py (§3) |

`str` indexing/iteration is banned in Nagini, so both renderings are carried as
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance — the single A-reference (checked by G-AX / axiom_check.py)

### `value_text` deep model ↔ standard string coercion `str(value)` (A-reference)
**Behaviour:** the patched `__str__` returns `str(self.value)`. The changed
operation — "render the member to text as its value, not as its qualified
name" — is modelled **deeply** by carrying the value already rendered as the
code-point sequence `value_text` and copying it element-for-element into the
result. There is **no consumed `@ContractOnly` axiom**: the proof does not
depend on any opaque callee's `Ensures`.

The one Python primitive the deep model abstracts is the standard string
coercion `str(value)` that turns the underlying value into `value_text`
(`str("first") == "first"`; `str(1) == "1"`). It is validated equal to real
Python out-of-band by `axiom_check.py` (G-AX): the script reconstructs the
patched member rendering (a `Choices` enum whose `__str__` returns
`str(self.value)`, with the `IntegerChoices`/`TextChoices` int/str mix-ins the
issue names — the exact construction the gold patch edits) and asserts, over
boundary + 20 000 fuzz integer and text values, that

  * `str(member)` equals real Python `str(member.value)` (the A-reference), and
  * `str(member)` is **never** the default diagnostic `"Owner.NAME"` label when
    the value text differs from it (the discriminating behaviour the fix adds).

`axiom_check.py` imports only the standard-library `enum` module (the very
module the patched code builds on); nothing repo-specific. Exit 0 iff sound.

Docs: https://docs.python.org/3/library/enum.html (the default `Enum.__str__`
produces `"<class>.<name>"`; the patch overrides it to `str(self.value)`).
