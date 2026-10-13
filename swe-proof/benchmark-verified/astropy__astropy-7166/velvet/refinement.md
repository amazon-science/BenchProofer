# refinement.md — astropy__astropy-7166

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveMemberDocstrings` `do` block plus the deep `eligible`/`finalDoc`/
`resolvedDocs` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (a deep model validated == the real callee
by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). The gold patch's other
hunks are import/blank-line cosmetics with no behavior — see §C.

## A. The membership guard — `InheritDocstrings.__init__` (`astropy/utils/misc.py:530-537`)

Gold hunk (the only behavioral change):
```
-            if (inspect.isfunction(val) and
-                is_public_member(key) and
-                val.__doc__ is None):
+            if ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and
+                    is_public_member(key) and
+                    val.__doc__ is None):
```

| # | Solution.lean impl op (`resolveMemberDocstrings`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `members : List Member` | the iteration `for key, val in dct.items()` | R | `dct.items()` ↔ `List Member`; each `(key, val)` ↔ a `Member` whose fields are the observations the loop reads (mapping.md §2). G-CONF bridges via the real metaclass. |
| A2 | `m.isCallable` | `inspect.isfunction(val)` | R | `bool ↔ Bool` (mapping.md §2). The real callee is run by G-AX/G-CONF. |
| A3 | `m.isProperty` | `inspect.isdatadescriptor(val)` | R + A-reference | `bool ↔ Bool`. The **changed** disjunct: it is modeled as the field `isProperty`, and the equality of `eligible`'s use of it to the real `inspect.isdatadescriptor(val)` is the A-reference G-AX validates (`isdatadescriptor(property)==True`, `isfunction(property)==False`). mapping.md §3.1. |
| A4 | `m.isPublic` | `is_public_member(key)` | R | `bool ↔ Bool`; `is_public_member` is the unchanged nested predicate, run verbatim by G-AX/G-CONF. |
| A5 | `m.ownDoc.isNone` | `val.__doc__ is None` | R + I | `None ↔ none`; `Option.isNone` ↔ `is None`. The `is None` test is the identical concrete op. |
| A6 | `eligible m = (m.isCallable ∨ m.isProperty) ∧ m.isPublic ∧ m.ownDoc.isNone` | the full `if (...)` guard | A-reference + I | the changed eligibility op is modeled **deeply**: `eligible` IS the guard. The boolean composition (`∨`, `∧`) is **I** (concrete, transliterated by G-CONF); the equality of the deep model to the real guard over real member objects is the **A-reference** G-AX validates. mapping.md §3.1. |
| A7 | `finalDoc m = if eligible m then m.inheritedDoc else m.ownDoc` | `val.__doc__ = super_method.__doc__` taken iff the guard holds, else `val.__doc__` unchanged (`misc.py:534-537`) | R + I | the MRO walk's *result* is the input field `inheritedDoc` (R, unchanged callee — mapping.md §2); the conditional assignment is **I**. The walk itself (`for base in cls.__mro__[1:]`, `getattr`, the `break`) is unchanged by the patch. |
| A8 | the backward `while` fold building `result = resolvedDocs members` | the `for key, val in dct.items()` loop applying the body to each member | I | the loop is the per-member map `resolvedDocs`; the fold computes exactly the left-to-right `finalDoc`-of-each-member list. Transliterated by G-CONF. |

Discriminating content of the change — a **property** with no own documentation
inherits its base's documentation — lives in the `m.isProperty` disjunct of
`eligible` (model) ⇔ the `or inspect.isdatadescriptor(val)` term of the guard
(real). The pre-patch guard admitted only `isfunction`;
`Solution_prepatch.lean` reproduces that (its inline guard drops the
`isProperty` disjunct) and **fails** `out = resolvedDocs members` (G-DIFF) on
exactly the clause where a property's `finalDoc` differs.

## B. No A-consumed steps

There is no consumed axiom. The only deeply-modeled callee is the changed guard
(`eligible`, an A-reference validated by G-AX); every other callee
(`inspect.isfunction`, `is_public_member`, the MRO documentation walk) is
unchanged and enters as an R-refined input field, differential-tested live by
G-CONF/G-AX against the real objects. `Solution.lean` has an empty `axioms`
region.

## C. The cosmetic hunks of the gold patch

`patch.diff` also removes blank lines in the module docstring tail
(`misc.py:4-9`) and a stray blank line before `__all__` (`misc.py:27`). These
touch neither control flow nor data flow of any function; they are
behavior-preserving whitespace edits required only for the patch to apply
cleanly as gold. They have **no** Solution.lean counterpart and are not
refinement steps. (G-CONF/G-RESOLVE observe identical behavior with or without
them.)

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the membership guard broadening to admit properties — is modeled **deeply** (the
spelled-out `eligible`, step A6, an A-reference + I), not hidden behind an axiom
about the function under change. There are no consumed axioms.

## E. verify(Solution) ⇒ resolved

`resolveMemberDocstrings` verifies only if its output equals the exact
per-member map `resolvedDocs`, whose `eligible` admits both callables AND
properties (A6) and whose `finalDoc` takes the inherited documentation for
eligible members (A7). By R (`dct.items() ↔ List Member`, the `bool`/`Option`
field bijections) the verified map equals the patched metaclass's effect on each
member's `__doc__` over the tested class bodies; by G-AX the deep model
`eligible` equals the real post-patch guard (A-reference) on real member objects;
by G-CONF the R/I transliteration of the fold agrees with `patch.diff`'s behavior
on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited A-reference — and the
gold patch resolves (G-RESOLVE). Trust points: A-reference soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
