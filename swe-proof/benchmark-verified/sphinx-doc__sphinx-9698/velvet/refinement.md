# refinement.md — sphinx-doc__sphinx-9698

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`indexEntryText` `do` block and the pure `indexText` / `rsplitDot` / `shownOwner`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A** (axiomatized callee — none here), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are no A legs (no axiomatized callees), so G-AX is `skip`. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on every input, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The single changed site — `PyMethod.get_index_text` (`sphinx/domains/python.py:784`)

Gold hunk:
```
         elif 'property' in self.options:
-            return _('%s() (%s property)') % (methname, clsname)
+            return _('%s (%s property)') % (methname, clsname)
```

| # | Solution.lean impl op (`indexEntryText`) | patch.diff / `get_index_text` op | tag | justification |
|---|---|---|---|---|
| A1 | params `name modname : List Char` | `name_cls = (name, cls)` arg + `modname` arg of `get_index_text` | R | `str` ↔ `List Char` (mapping.md §2). The `cls` half of `name_cls` is unused by the body, so only `name` is carried. G-CONF bridges via `s ↔ s.toList`. |
| A2 | `addModuleNames : Bool` | `self.env.config.add_module_names` | R | `bool` ↔ `Bool` (mapping.md §2). |
| A3 | `kind : MethodKind` | the resolved category in `self.options` (the `if/elif` chain over `'classmethod'/'property'/'staticmethod'`) | R | the four-way `self.options` membership outcome ↔ the four-constructor enum (mapping.md §2). Real precedence `classmethod>property>staticmethod>plain` is fixed and unchanged; `MethodKind` is its single resolved result. |
| A4 | `rsplitDot name` → `some (owner, member)` / `none` | `clsname, methname = name.rsplit('.', 1)` inside `try`, with the `except ValueError` fallback | R + I | `rsplit('.',1)` at the rightmost `.` ↔ `rsplitDot` (mapping.md §2); the split arithmetic itself is **I** (concrete, transliterated by G-CONF). `none` is the `ValueError` (no separator) branch. |
| A5 | `shown := if modname ≠ [] ∧ addModuleNames then modname ++ ['.'] ++ owner else owner` | `if modname and self.env.config.add_module_names: clsname = '.'.join([modname, clsname])` | I | identical concrete computation (module-prefix join) under the R bijection. |
| A6 | the four `match kind` arms emitting `member ++ "() (".toList ++ shown ++ " <cat>)".toList`, **except** `propertyKind` which emits `member ++ " (".toList ++ shown ++ " property)".toList` | the four `return _('%s() (%s <cat>)') % (methname, clsname)` arms, **except** the property arm `return _('%s (%s property)') % (methname, clsname)` | I | identical concrete `%`-format → `++` builds under R; `_` is identity (mapping.md §2,§3). **The single behavioural change** lives in the property arm: NO `()` after the member name. |
| A7 | `none` branch: `if modname ≠ [] then name ++ "() (in module ".toList ++ modname ++ ")".toList else name ++ "()".toList` | the `except ValueError` branch: `return _('%s() (in module %s)') % (name, modname)` / `return '%s()' % name` | I | identical concrete builds under R. Unchanged by the patch; carried for completeness so the model is the WHOLE function (verify ⟹ correct, not just on the property leg). |

Discriminating content of the change — the property category drops the empty
call marker `()` — lives in the `propertyKind` arm of `indexText`
(`member ++ " (".toList ++ …`, NO `()`), which the gold property arm
(`_('%s (%s property)')`) implements. The pre-patch emitted
`_('%s() (%s property)')`; `Solution_prepatch.lean` reproduces that
(`member ++ "() (".toList ++ …`) and **fails** `out = indexText …`, on the
`propertyKind` branch only (G-DIFF — verified: the unsolved goal is exactly the
property arm `'(' :: ')' :: …` vs `' ' :: …`).

## B. No second site

A single-line, single-function change. There is no second independently-fixed
behaviour, so there is exactly one `Solution_prepatch.lean`.

## C. No kind-A callees, no kind-3 steps

Every step is R or I. There is **no axiomatized callee**: the entire label is a
pure per-character string computation from the inputs (`rsplit`, `'.'.join`,
literal `%`-templates). The `_(...)` gettext wrapper is identity under the
no-catalog test default (mapping.md §3) and is modeled as identity, not as a
consumed contract. Hence no `axiom`, no A-reference, no `axiom_check.py`, and
G-AX = `skip` (as in the no-axiom exemplars `django__django-11138`,
`django__django-11400`). No operation that genuinely *changed* is inexpressible:
the change is the literal template of one arm, modeled directly (A6).

## D. verify(Solution) ⇒ resolved

`indexEntryText` verifies only if its output equals `indexText` on EVERY input —
in particular the property arm with no `()` (A6) and the unchanged arms with `()`
(A6/A7). By R (`str ↔ List Char`, `bool ↔ Bool`, the option↔`MethodKind`
bijection, `_` = identity) the verified label equals what the patched
`get_index_text` returns on every `(name, modname, add_module_names, options)`;
by G-CONF the R/I transliteration of the whole function agrees with `patch.diff`
behaviour on ≥10⁵ inputs (seed 9698), including the four categories, qualified /
unqualified names, and module-prefix on/off. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). With no axioms, the only trust point is
refinement fidelity (this doc, G-CONF); there is no axiom-soundness obligation.
