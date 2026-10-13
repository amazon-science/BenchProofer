# refinement.md — sphinx-doc__sphinx-8035

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectMembers` `do` block, the deep `shownMembers`/`memberShown`/`selKeeps`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model / abstracted input validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I; there is no kind-3
(inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
mapping.md §5); the A-reference legs by **G-AX** (`axiom_check.py`). Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the modeled scenario (mapping.md §2),
so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The keep-decision site — `Documenter.filter_members` (`sphinx/ext/autodoc/__init__.py:559`)

Gold hunk (the `want_all and isprivate` branch, the behaviour the F2P test
exercises):
```
- # ignore members whose name starts with _ by default
- keep = self.options.private_members and \
-     (has_doc or self.options.undoc_members)
+ if has_doc or self.options.undoc_members:
+     if self.options.private_members is None:
+         keep = False
+     elif self.options.private_members is ALL:
+         keep = True
+     elif is_filtered_inherited_member(membername):
+         keep = False
+     else:
+         keep = membername in self.options.private_members
+ else:
+     keep = False
```
plus the option-spec re-route `'private-members': bool_option → members_option`
(ModuleDocumenter `__init__.py:890`, ClassDocumenter `__init__.py:1310`) and the
`merge_special_members_option → merge_members_option` rename in the two
`__init__`s. In the modeled scenario `objtype = module` ⇒
`is_filtered_inherited_member` ≡ `False` (mapping.md §2), so its branch collapses
into the `membername in self.options.private_members` arm.

| # | Solution.lean impl op (`selectMembers`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `members : List Member` | the `members: List[Tuple[str, Any]]` arg of `filter_members` (each abstracted to `(name, isRestricted, hasDoc)`) | R | `[(name, member)] ↔ List Member`; `isRestricted`/`hasDoc` are the abstracted results of the unchanged classifier callees (A-reference 2). mapping.md §3. |
| A2 | param `sel : Sel` | `self.options.private_members ∈ {None, ALL, list[str]}` after the option-spec re-route to `members_option` | R + A-reference | `None↔Sel.none`, `ALL↔Sel.all`, `list↔Sel.only`. The parser is the unchanged `members_option`; G-AX validates `members_option == Sel`. mapping.md §4.1. |
| A3 | param `showUndocumented : Bool` | `self.options.undoc_members` | R | `bool(undoc_members) ↔ Bool`. mapping.md §3. |
| A4 | `memberShown sel su m` for a restricted `m`: `(hasDoc‖su) && selKeeps sel name` | the post-patch private branch: `(has_doc or undoc) and (None→F / ALL→T / name in private_members)` | I | the changed keep-decision is modeled **deeply** (spelled out in `memberShown`/`selKeeps`), not behind an axiom; transliterated 1:1 by G-CONF. `selKeeps` exactly reproduces the tri-state. |
| A5 | `memberShown sel su m` for a non-restricted `m`: `hasDoc ‖ su` | the `else` documented branch `keep = has_doc or self.options.undoc_members` | I | unchanged behaviour for non-private members; concrete, transliterated by G-CONF. |
| A6 | the backward `while` fold accumulating kept members into `result` (= `shownMembers sel su members`) | the `for … in members: … if keep: ret.append(...)` loop building `ret` | I | order-preserving filter; the fold computes the same kept sublist (proven via `shownMembers_drop_step`). G-CONF checks `out == ret` (names) on ≥10⁵ inputs. |

Discriminating content of the change — a **specific** `:private-members:`
selection surfaces only the **named** restricted members, not all of them —
lives in `selKeeps (.only names) name = names.contains name` (model) ⇔ `keep =
membername in self.options.private_members` (real). The pre-patch decision
`keep = private_members and (has_doc or undoc)` treats any truthy option (a
non-empty list IS truthy) as "show all private members";
`Solution_prepatch.lean` reproduces that (a restricted member's keep consults
only whether *any* selection was given, the `.only _ => true` arm) and **fails**
`out = shownMembers sel su members` (G-DIFF) at exactly that clause.

## B. No consumed axioms; the A-references

No module-level `axiom` is consumed by the proof. The two A-references are
unchanged callees whose results are abstracted into the modeled inputs, each
validated == its real callee by G-AX:

| ref | Solution.lean construct | real callee | tag | justification |
|---|---|---|---|---|
| B1 | `Sel` value domain (consumed only via `selKeeps`'s `names.contains`) | `members_option` (`__init__.py:76`, unchanged) | A-reference | the parsed comma-split list IS the set membership is tested against; G-AX `members_option == Sel`. mapping.md §4.1. |
| B2 | `Member.isRestricted` / `Member.hasDoc` | `getdoc` + `extract_metadata` / `startswith('_')` (unchanged) | A-reference | the upstream classification feeding the decision; G-AX confirms the F2P members classify as `_public_function→(¬restricted, doc)`, `private_function→(restricted, doc)` and fuzzes the rule. mapping.md §4.2. |

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
restricted-member keep-decision moving from an all-or-nothing boolean to a
per-identifier tri-state — is modeled **deeply** (`memberShown`/`selKeeps`, step
A4, an **I** op), not hidden behind an axiom about the function under change.
The only A-tagged constructs are **A-references** to unchanged callees
(`members_option`, `getdoc`/`extract_metadata`); there is no consumed axiom and
no dead axiom.

## C2. Termination (total-correctness semantics)

The spec runs under `loom.semantics.termination "total"` (with a `decreasing i`
annotation on the loop): a verifying implementation must TERMINATE, matching the
real `filter_members`, whose member loop is a finite `for` over the input list.
Under the earlier partial-correctness setting a diverging implementation (an
inserted infinite loop ahead of an otherwise-correct filter) satisfied the spec
vacuously while its translated patch hung the hidden tests — the G-EQ/P1 defect
this section records the repair of. Total correctness closes that class: an
infinite loop now fails verification (decreasing annotations are required, and a
fabricated `decreasing` measure on a non-terminating loop leaves an unprovable
`False` goal).

## D. verify(Solution) ⇒ resolved

`selectMembers` verifies only if its output equals the exact per-member
keep-decision with the per-identifier `selKeeps` (A4) preserving input order
(A6). By R (`List Member ↔ members`, `Sel ↔ private_members`, `Bool ↔
undoc_members`) the verified filter equals the post-patch `filter_members`
keep-loop on the modeled scenario; by G-AX the abstracted inputs (`Sel`,
`isRestricted`/`hasDoc`) equal the real unchanged callees; by G-CONF the R/I
transliteration agrees with the real patched `filter_members` on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
