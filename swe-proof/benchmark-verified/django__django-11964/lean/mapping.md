# mapping.md — symbol binding & type bijection (django__django-11964)

## Modeled function
- **Lean** `implementation_memberStr : EnumMember → String`
- **Python** `Choices.__str__(self)` — `django/db/models/enums.py:61-67 @ fc2b1cc`
  (post-patch: a `__str__` method on `Choices` returning `str(self.value)`).

The function under spec is the `str()` conversion of an enumerated-choices
member. Pre-patch, `Choices` inherits `enum.Enum.__str__`, which returns the
owner-qualified member identifier `"<ClassName>.<MEMBER_NAME>"`. The patch adds
a `__str__` that returns `str(self.value)`. The observable behavior the F2P
tests demand: `str(member)` equals `str(member.value)` for every member.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| enumerated member `self` | `EnumMember` structure | only the touched fields modeled: the owner-qualified name + the underlying value |
| `str(member)` (the inherited `Enum.__str__`) | `EnumMember.qualifiedName : String` | `"ClassName.NAME"`; the pre-patch result |
| `member.value` | `EnumMember.value : MemberValue` | the underlying value, text (`TextChoices`) or int (`IntegerChoices`) |
| `str(self.value)` | `pyStr m.value` | textual value → itself; integral value → decimal numeral |
| `str` output | Lean `String` | value-level string |
| `int` value | `Int` | `IntegerChoices` member values are ints |
| `str` value | `String` | `TextChoices` member values are strings |

`MemberValue` covers exactly the two value kinds the F2P enums use:
`IntegerChoices` (Suit, Vehicle) carry `int`; `TextChoices` (YearInSchool,
Gender) carry `str`. `pyStr (.num n) = toString n` mirrors CPython `str(int)`;
`pyStr (.text s) = s` mirrors CPython `str(str)` (identity).

## Callee provenance
- The textual conversion of the member's underlying value (`str(self.value)`) is
  the changed operation itself; it is modeled DEEPLY as `pyStr` (an
  **A-reference**, validated by G-AX against the real Python `str(value)` on
  int/str values), NOT axiomatized.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
None. `Choices.__str__` is unconditional; both `IntegerChoices` and
`TextChoices` inherit it via `Choices`.

## G-CONF fuzz seed
Pinned seed: **11964**. ≥10^5 fuzzed inputs over a domain that mixes textual
member values (random unicode strings, including empty) and integral values
(negative, zero, large), each paired with an arbitrary owner-qualified name.
