# refinement.md — operation correspondence (django__django-11999)

Maps every op in `implementation_registerDisplay` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python registers the auto-generated display accessor for a field
that carries an enumerated choice set. The bug installed it unconditionally; the
fix guards the installation with a presence test so a user-declared accessor is
preserved.

```
        if self.choices is not None:
-           setattr(cls, 'get_%s_display' % self.name, partialmethod(...))
+           if not hasattr(cls, 'get_%s_display' % self.name):
+               setattr(cls, 'get_%s_display' % self.name, partialmethod(...))
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `attrs : Attrs` (`List (String × Int)`) | the class attribute namespace `cls` as observed by `hasattr`/`setattr` | R | dict/namespace ↔ assoc-list bijection (mapping.md); only key presence and stored value are observable |
| 2 | `let mut result := attrs` | the namespace threaded through the block | I | identity initialisation |
| 3 | `if hasChoices then …` | `if self.choices is not None:` | R | `choices is not None` ↔ `hasChoices : Bool` |
| 4 | `let key := displayKey name` | `'get_%s_display' % self.name` | I | `%`-format of a fixed template ↔ `"get_" ++ name ++ "_display"`; identical string |
| 5 | `if !hasKey result key then …` | `if not hasattr(cls, 'get_%s_display' % self.name):` | R | **the changed op** modeled deeply: `hasattr` ↔ key membership of the namespace mapping. NOT axiomatized. |
| 6 | `result := setKey result key display` | `setattr(cls, 'get_%s_display' % self.name, partialmethod(...))` | R | `setattr` ↔ replace-or-append in the namespace; the generated accessor object `partialmethod(...)` is the `display` input (its construction is out of scope, mapping.md) |
| 7 | `return result` | (block falls through; `cls` mutated in place) | I | returned namespace |

No A-consumed rows: the proof discharges the membership/assignment reasoning
directly over the assoc-list model; no UNCHANGED callee property is assumed
(axioms region empty, G-AX is a skip stub).
No A-reference rows: `hasattr`/`setattr`/`%`-format are reproduced concretely as
`hasKey`/`setKey`/`displayKey` (I/R ops), not abstracted behind a model that
needs G-AX validation. No changed-inexpressible op.

The spec pins the WHOLE result exactly:
`result = if hasChoices && !hasKey attrs key then attrs ++ [(key, display)] else attrs`.
This is the frame discipline in full — no output component is left
unconstrained, so no implementation that mutates the namespace in any other way
(reorders, drops, duplicates, or clobbers an existing accessor) can satisfy it.

The discriminating clause is rows 5–6: the fix adds the `!hasKey` guard. When
`hasChoices = true` AND the accessor key is already present (the user-override
case from the F2P test), the post-patch impl leaves the namespace untouched
(`result = attrs`, matching the `else` branch of the spec). The prepatch impl
drops the guard and runs `setKey result key display`, producing
`attrs ++ [(key, display)]` (key absent) or an in-place overwrite (key present) —
either way `result ≠ attrs` whenever the prior accessor differs. Hence the
prepatch `correct_registerDisplay` cannot close — the G-DIFF signal. (Validated
mechanically: `¬ problem_spec_registerDisplay [("get_foo_bar_display",7)]
"foo_bar" true 99 (implementation_prepatch …)` reduces to `True` by
`native_decide`.)
