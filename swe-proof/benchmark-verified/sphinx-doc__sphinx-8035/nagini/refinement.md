# refinement.md — sphinx-doc__sphinx-8035

The operation-by-operation correspondence between `model.py`'s implementation
(`keep_private_member` + the deep `keep_private`, and `merge_selector_names` +
the deep `merged_at`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-reference** (deep model validated == the real
post-patch code by `axiom_check.py` / G-AX), **A-consumed** (proof uses an
axiom's `Ensures` — none in this bundle), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The private-member keep decision — `filter_members`

Gold hunk (`sphinx/ext/autodoc/__init__.py`, the `elif want_all and isprivate:`
branch):
```
-                # ignore members whose name starts with _ by default
-                keep = self.options.private_members and \
-                    (has_doc or self.options.undoc_members)
+                if has_doc or self.options.undoc_members:
+                    if self.options.private_members is None:
+                        keep = False
+                    elif self.options.private_members is ALL:
+                        keep = True
+                    elif is_filtered_inherited_member(membername):
+                        keep = False
+                    else:
+                        keep = membername in self.options.private_members
+                else:
+                    keep = False
```
plus the option-spec change `'private-members': bool_option` →
`'private-members': members_option` (lines 862, 1282), which is what makes
`self.options.private_members` carry the three states `None` / `ALL` / `List`.

| # | model.py impl op (`keep_private_member`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `mode: int`, `names: List[int]`, `membername: int` | `self.options.private_members` ∈ {None, ALL, List[str]}, and `membername: str` | R | option trichotomy ↔ `mode`+`names`; name `str` ↔ `int` token (mapping.md §2). The option-spec edit `bool_option`→`members_option` is exactly the source of this trichotomy. |
| A2 | `if not (has_doc or undoc_members): return False` | the outer `if has_doc or self.options.undoc_members: ... else: keep = False` | I + R | identical control: undocumentable ⇒ not kept. `has_doc`/`undoc_members` booleans (R, mapping.md §2). |
| A3 | `if mode == 0: return False` | `if self.options.private_members is None: keep = False` | R | `None` ↔ `mode==0`. |
| A4 | `if mode == 1: return True` | `elif self.options.private_members is ALL: keep = True` | R | `ALL` sentinel ↔ `mode==1`; the inherited filter is NOT applied here (faithfully: mode 1 returns True for any documentable member). |
| A5 | `if filtered_inherited: return False` | `elif is_filtered_inherited_member(membername): keep = False` | R | `is_filtered_inherited_member(membername)` ↔ the `filtered_inherited` boolean (its internals are unchanged by the patch; abstracted, mapping.md §2). |
| A6 | `return membername in ToSeq(names)` | `else: keep = membername in self.options.private_members` | R | list membership of name tokens ↔ `str`-list membership; this is the discriminating clause. |

The discriminating content — an explicit list keeps a documentable, non-filtered
private member iff its OWN name is in the list, NOT every private member — lives
in A6 (model) ⇔ `keep = membername in self.options.private_members` (real). The
pre-patch `keep = self.options.private_members and (has_doc or undoc)` collapsed
the (now-trichotomous) option to a truthy flag, keeping EVERY documentable
private member whenever the option was given; `model_prepatch.py` reproduces
that collapse (`return (mode != 0) and (has_doc or undoc_members)`) and **fails**
the postcondition `Result() == keep_private(mode, names, ...)` exactly on the
mode-2 case where a name is not in the list (G-DIFF). This is the F2P
discriminator: `private-members="_public_function"` must DROP `private_function`
(a documentable private member not in the list), which the prepatch keeps.

`keep_private` (model.py pure region) is the deep model of this post-patch
decision and is validated **== the real `filter_members` decision** out-of-band
by `axiom_check.py` (G-AX), over every option-state × member × flag combination,
with the option states produced through the REAL `members_option` converter
(**A-reference**, mapping.md §3.1). There is no consumed axiom about the
decision.

## B. The `*-members` selector merge — `merge_members_option`

Gold hunks: a new `merge_members_option(options)` is added; the
`ModuleDocumenter.__init__` and `ClassDocumenter.__init__` calls to
`merge_special_members_option(self.options)` become
`merge_members_option(self.options)` (lines 868, 1290). The new helper merges
both `private-members` and `special-members` explicit lists into `members`.

| # | model.py construct (`merge_selector_names`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if members_is_all: return members` (copy) | `if options.get('members') is ALL: return` (no-op) | R | `members` all-form ↔ `members_is_all`; the no-op returns the member list unchanged. |
| B2 | copy `members` into `result`, then for each `extra[j]`: append iff not already present | `members = options.setdefault('members', [])`; `for member in options[key]: if member not in members: members.append(member)` | R + I | append-if-absent over name tokens ↔ over `str` names; order preserved, duplicates avoided. |

`merge_selector_names` is the deep model of the new `merge_members_option` and is
validated **== the real callee** by `axiom_check.py` (G-AX) over 5000 randomized
inputs (**A-reference**, mapping.md §3.2). Why no separate failing
`model_prepatch` for site B: the F2P test supplies `members: ALL`, for which the
merge is a no-op (B1), so it does not affect the tested observation. The merge is
modeled for faithfulness of the multi-site change; its soundness is audited by
G-AX, and the tested differentiating behaviour is the keep decision (site A).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
changed — the private-members keep decision and the selector merge — are modeled
**deeply** (`keep_private` / `keep_private_member` and `merged_at` /
`merge_selector_names`), not hidden behind an axiom about the function under
change. There are **no consumed axioms** (no `@ContractOnly`): both deep models
are validated == the real post-patch code by G-AX (A-reference).

## D. verify(model) ⇒ resolved

`keep_private_member` verifies only if its decision equals the three-state rule
`keep_private` (A1-A6) — in particular, only if an explicit list keeps exactly
its named members (A6), the behaviour the F2P `test_private_members` observes. By
R (str ↔ int token, option-trichotomy ↔ `mode`/`names`, `is_filtered_inherited`
↔ boolean) the verified decision equals the gold patch's branch; by G-AX the
deep model `keep_private` equals the real `filter_members` decision and
`merge_selector_names` equals the real `merge_members_option` (A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited references — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
