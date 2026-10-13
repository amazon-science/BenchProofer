# refinement.md — django__django-11964

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_to_text` impl region — a deep, element-for-element copy of the
member's value text) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The rendering site — `Choices.__str__` (`django/db/models/enums.py:61`)

Gold hunk (the bare `pass` body of `Choices` is replaced by a `__str__`):
```
- class Choices(enum.Enum, metaclass=ChoicesMeta):
-     """Class for creating enumerated choices."""
-     pass
+ class Choices(enum.Enum, metaclass=ChoicesMeta):
+     """Class for creating enumerated choices."""
+
+     def __str__(self):
+         return str(self.value)
```

| # | model.py impl op (`render_to_text`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self: Member` with field `self.value_text: List[int]` | `self` (a `Choices` member) and its `self.value` | R | the member is a minimal object exposing only the touched character sequences; `self.value` rendered ↔ `self.value_text` as `List[int]` code points (mapping.md §1–2). |
| A2 | the result is `ToSeq(self.value_text)`, produced by copying `self.value_text` element-for-element into a fresh list | `return str(self.value)` | A-reference | the changed operation is modelled **deeply**: the impl loop IS the rendering — it returns the member's value text character for character. There is no consumed `str_of_value` axiom; the proof never depends on one. The one primitive abstracted (the standard coercion `str(value)` that yields `value_text`) is validated **== real Python `str`** out-of-band by G-AX (axiom_check.py): `str(member) == str(member.value)` over boundary + 20 000 fuzz int/str values. (mapping.md §3.) |
| A3 | `result` returned (a fresh `List[int]`) | the `str` returned by `__str__` | R | `str` ↔ `List[int]` code points; the F2P `test_str` compares the rendered characters (`str(test[member.name]) == str(member.value)`), which the code-point list carries exactly. |

The discriminating content of the change — render the member as its **value
text**, not as the default diagnostic **`"Owner.NAME"`** label — lives in the
postcondition `ToSeq(Result()) == ToSeq(self.value_text)` (model) ⇔ the
`return str(self.value)` body (real). The pre-patch `Choices` has an empty body,
so a member inherits `enum.Enum.__str__`, which returns `"Owner.NAME"`;
`model_prepatch.py` reproduces that (the impl copies `self.qualified_label`) and
**fails** the postcondition `ToSeq(Result()) == ToSeq(self.value_text)` — exactly
the spec sensing the change (G-DIFF), because the value text and the qualified
label differ for every tested member (e.g. `"FR"` vs `"YearInSchool.FRESHMAN"`,
`"1"` vs `"Suit.DIAMOND"`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the member's textual rendering — is modelled **deeply** (the spelled-out
element-for-element copy of `value_text` in `render_to_text`, step A2, an
**A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `str_of_value` `@ContractOnly` axiom. The only abstracted
primitive, the standard string coercion `str(value)` that produces `value_text`
(an **unchanged** Python builtin the new code invokes), appears solely as the
**A-reference** that G-AX validates the deep model against. There are therefore
**no A-consumed axioms** in this bundle.

## C. verify(model) ⇒ resolved

`render_to_text` verifies only if its output equals the member's value text
character-for-character (A2) and only if `self` is left untouched (fractional
permission, directive 5 — a rendering that mutated the member to satisfy the
postcondition vacuously is rejected). By R (`str` ↔ `List[int]`, the member-field
bijection) the verified rendering equals `str(self.value)` on the tested inputs;
by G-AX the deep model equals real Python `str(self.value)` (the A-reference)
and is never the default `"Owner.NAME"` label. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited coercion — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
