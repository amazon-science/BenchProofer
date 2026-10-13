# refinement.md — django__django-11964

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`memberToStr` `do` block and the deep `renderValue` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `Choices.__str__` (`django/db/models/enums.py:61`)

Gold hunk:
```
 class Choices(enum.Enum, metaclass=ChoicesMeta):
     """Class for creating enumerated choices."""
-    pass
+
+    def __str__(self):
+        """Use value when cast to str ..."""
+        return str(self.value)
```

`Choices` is the common base of `IntegerChoices` (also subclassing `int`) and
`TextChoices` (also subclassing `str`). Before the patch a member inherits
`enum.Enum.__str__`, which returns the qualified `Owner.NAME` token (e.g.
`MyChoice.FIRST_CHOICE`); after, `str(member)` returns `str(member.value)`.

| # | Solution.lean impl op (`memberToStr`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `member : Member` | `self` (the enum member) of `Choices.__str__` | R | a member abstracted to the only datum the rendering reads: its `value` (the `defaultLabel` field carries the pre-fix token, used only by the prepatch). mapping.md §1. |
| A2 | `member.value : MemberValue` (`intVal n` / `strVal s`) | `self.value` (a Python `int` for `IntegerChoices`, a `str` for `TextChoices`) | R | the payload bijection: `int ↔ intVal n`, `str ↔ strVal s.toList` (mapping.md §2). |
| A3 | result is `renderValue member.value`: `(toString n).toList` for `intVal n`, `s` for `strVal s` | `return str(self.value)` | R + I | the changed op is modeled **deeply**: `renderValue` (pure region) IS the `str(...)` coercion — decimal text for a number, identity for text. The dispatch + concatenation are **I** (concrete, transliterated by G-CONF); the `int→decimal` / `str→identity` rendering is the **R** bijection `toString n ↔ str(n)`, `s ↔ str(s)` (mapping.md §2). No consumed axiom: `str(int)` / `str(str)` are total stdlib coercions modeled exactly. |
| A4 | `result` returned (`List Char`) | the `str` the method returns | R | `str ↔ List Char` (mapping.md §2); the F2P `test_str` compares `str(member)` to `str(member.value)` as text. |

Discriminating content of the change — a member renders as its own value's text
(`renderValue member.value`), NOT the generic `Owner.NAME` token (`defaultLabel`).
The pre-patch inherited `enum.Enum.__str__` produced `Owner.NAME`;
`Solution_prepatch.lean` reproduces that (`return member.defaultLabel`) and
**fails** all three `ensures` clauses (G-DIFF) — most sharply
`out = renderValue member.value`, the clause the F2P test pins.

## B. No other change sites

The patch touches exactly one class body (adds one method). No callee is changed
or swapped; the enum metaclass, the `value`/`label`/`choices` machinery, and the
`int`/`str` mixins are all untouched and unobserved by `__str__`. There is no
site B and no consumed axiom.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — what
`str(member)` returns — is modeled **deeply** (`renderValue`, step A3, R + I),
not hidden behind an axiom about the function under change. There is no consumed
axiom at all (G-AX skipped).

## D. verify(Solution) ⇒ resolved

`memberToStr` verifies only if its output equals `renderValue member.value` (A3)
— the decimal text of a numeric payload, the identity of a textual payload. By R
(`int ↔ intVal`/`toString ↔ str`, `str ↔ strVal`/identity, `str ↔ List Char`) the
verified renderer equals `str(self.value)` on the `IntegerChoices`/`TextChoices`
members the F2P `test_str` builds; by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour (real members rendered by the patched `__str__`) on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms (G-AX skipped).
