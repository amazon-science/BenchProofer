# refinement.md — sympy__sympy-15976

The operation-by-operation correspondence between `model.py`'s implementation
(the `print_symbol` impl region, the deep structural model `root_tag_for` /
`child_tags_for` / `sub_group_tag` / `sup_group_tag`, and the `MNode` carrier) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-reference** (a deep
model validated == the real unchanged callee by axiom_check.py / G-AX),
**A-consumed** (the proof uses an axiom's `Ensures` — none here), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The renderer — `MathMLPresentationPrinter._print_Symbol` (`mathml.py:745`)

Gold hunk (essence): the pre-patch created `x = createElement('mi')` at the top,
set the bold attribute on it, then in each of the four sub/super branches built a
structural element and appended it *inside* `x`. The fix removes the outer `<mi>`:
`x` is BOUND to the structural element itself (`x = mname` / `x = createElement('msub')`
/ `'msup'` / `'msubsup'`, appending the name and group children directly to it),
and the bold attribute is moved to the end onto that chosen `x`.

| # | model.py impl op (`print_symbol`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `has_subs, has_supers, subs_multi, supers_multi` | `name, supers, subs = split_super_sub(sym.name)` then `len(...)==0` / `len(...)>1` tests | R + A-reference | `str` decomposition is abstracted to the four flags; the unchanged helper `split_super_sub` is run by G-AX to derive them (mapping.md §3.1). `has_*` ↔ `len(...) > 0`, `*_multi` ↔ `len(...) > 1`. |
| A2 | `x = MNode(TAG_MI, [])` when `not has_supers and not has_subs` | `x = mname` (the `<mi>` holding the name text) | R + I | the bare-identifier root is an `mi` whose name is its `#text` content (no element child → empty `ctags`); mirrors gold's `x = mname`. The bare `mi` already had its name text appended. |
| A3 | `x = MNode(TAG_MSUB, [TAG_MNAME, sub_group_tag(subs_multi)])` when subs only | `x = createElement('msub'); x.appendChild(mname); x.appendChild(join(subs))` | R + I | the root IS the `msub`; its direct element children are `mname` (the base-name identifier, kind `TAG_MNAME` under §2's role-identity refinement) FIRST and the subscript group SECOND. Because `TAG_MNAME != TAG_MI`, the ordered `ctags` sequence pins the base-name child's position even when the group is a single-part identifier. `join` returns `mrow` for >1 part else `mi` — captured by `sub_group_tag(subs_multi)` (A5). |
| A4 | `x = MNode(TAG_MSUP, [TAG_MNAME, sup_group_tag(supers_multi)])` / `x = MNode(TAG_MSUBSUP, [TAG_MNAME, sub_group_tag(subs_multi), sup_group_tag(supers_multi)])` | the gold `'msup'` branch and the `'msubsup'` branch (`appendChild(mname)`, then `join(subs)` then `join(supers)` for the combined kind) | R + I | identical structural construction; combined kind appends subs before supers, matching gold's order, with the base-name child pinned FIRST and each script group pinned to ITS OWN slot by its distinct role code — so the ordered sequence discriminates the subs/supers slot order on every multiplicity combination, including the both-single and both-multi cases where the two groups take the same element kind. |
| A5 | `sub_group_tag(multi)` / `sup_group_tag(multi)` — the several-part code when `multi`, the one-part code otherwise, each naming its own role | `def join(items): mrow if len(items)>1 else mi` (`mathml.py:751-766`), applied to `subs` and to `supers` respectively | A-reference + I | `join` is UNCHANGED by the patch; its `mrow`/`mi` output kind is modelled deeply and validated == the real `join` output by G-AX. The two role-specific codes record WHICH part list the slot renders as well as the kind, so the abstraction keeps `join(subs)` and `join(supers)` distinct even when both take the same kind; G-AX/G-CONF check that positionally against the real child's content. |
| A6 | the bold mutation `x.bold = bold` after the branch | `if style == 'bold': x.setAttribute('mathvariant', 'bold')` at the END (post the structural choice) | R + I | bold lands on the produced root `x` (whichever kind), matching the moved gold hunk; in the model it sets the `MNode.bold` marker on the root and provably leaves `tag`/`ctags` unchanged. |

The structural element kind and child placement are modelled DEEPLY
(`root_tag_for` / `child_tags_for`), not behind an axiom: G-AX validates the deep
model == the real fixed `_print_Symbol` (A-reference, mapping.md §3.2).

## B. The discriminator the spec senses (G-DIFF)

The behavioural change is purely the **removal of the outer `<mi>` wrapper**:
post-fix the root of the produced tree is the structural element itself; pre-fix
it was always an `<mi>` whose single child was that structural element.
`model_prepatch.py` reproduces the pre-fix skeleton (`x = MNode(TAG_MI, [...])`
always, with the structural element as its lone child) and **fails** the
postcondition `node_tag(Result()) == root_tag_for(has_subs, has_supers)` — for
any name with a sub/superscript the buggy root tag is `mi` (=1) but the spec
requires the structural tag (`msub`=2 etc.). That clause is exactly the spec
sensing the bug; the secondary clause
`node_ctags(Result()) == child_tags_for(...)` independently senses the extra
wrapper (buggy root's children are `[msub]`, the spec requires
`[mname, group]`). Because every direct child carries a code naming
the ROLE it fills as well as its element kind (§2's role-identity refinement),
the ordered `ctags` equality ALSO pins the base-name child's position (name
FIRST) on every branch AND pins which script list occupies each group slot — a
same-spec impl that emits the group before the name, or that puts the
superscript group in the subscript slot, fails this clause even when every child
is `mi`-named in the DOM and the ordered sequence of nodeNames is identical to
gold's.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— the element-kind choice for the root and the depth at which the name/group
children sit — is modelled **deeply** (`root_tag_for`, `child_tags_for`,
`sub_group_tag`/`sup_group_tag`, the verified `print_symbol` builder), validated as an **A-reference**
against the real fixed `_print_Symbol`. The only callees the code invokes
(`split_super_sub`, the nested `join`) are UNCHANGED; they are A-references G-AX
checks, never consumed `@ContractOnly` axioms. There is no consumed axiom.

## D. verify(model) ⇒ resolved

`print_symbol` verifies only if (i) its root element kind equals
`root_tag_for(has_subs, has_supers)` — so the structural element is the root, not
an `<mi>` wrapper — and (ii) its direct element children equal
`child_tags_for(...)` — so the name identifier sits at depth one AND first
among the children (its `TAG_MNAME` kind code is distinct from every other
child kind, so the ordered sequence equality pins its position, and each script group's
role code pins its slot). By R (the
DOM-element ↔ `MNode` abstraction, the `str` ↔ flag refinement of A1, the
unchanged `split_super_sub`/`join` validated by G-AX) the verified renderer
produces, on every tested symbol name, the same `(nodeName, child nodeNames,
bold)` triple as the gold `_print_Symbol`. The gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: A-reference soundness (G-AX:
deep model == real `_print_Symbol`/`split_super_sub`/`join`) and refinement
fidelity (this document, G-EQ).
