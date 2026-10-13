# refinement.md — sphinx-doc__sphinx-8035

Maps every operation in `implementation_keepPrivateMember` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `keepPrivateMember` (the private-member arm of `filter_members`)

Post-patch repo code (`patch.diff`), the modeled branch:
```python
elif want_all and isprivate:
    if has_doc or self.options.undoc_members:
        if self.options.private_members is None:
            keep = False
        elif self.options.private_members is ALL:
            keep = True
        elif is_filtered_inherited_member(membername):
            keep = False
        else:
            keep = membername in self.options.private_members
    else:
        keep = False
```

Lean impl (`implementation_keepPrivateMember`): an imperative `Id.run do` keep
decision with the same nested `if`/`match` structure and the same guards.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `privateMembers : PrivateMembersOption` (`disabled`/`all`/`names ns`) | `self.options.private_members` ∈ {`None`, `ALL`, `list[str]`} | **R** | the option's runtime shape ↔ the three-constructor tag; the patch's `members_option` makes `None`→absent, `ALL` (the sentinel), and a list the only shapes the branch distinguishes (mapping.md bijection). |
| 2 | `memberName hasDoc undocMembers dropAsInherited` | `membername`, `has_doc`, `self.options.undoc_members`, `is_filtered_inherited_member(membername)` | **R** | `str`↔`String`, the two truthy flags↔`Bool`, and the inherited-member predicate's already-computed boolean result↔`dropAsInherited : Bool` (its boolean value is consumed, not its MRO walk; see mapping.md). |
| 3 | `let mut keep := false` | `keep = False` initialization (the branch always assigns `keep`) | **I** | initial accumulator; both legs overwrite it on every path. |
| 4 | `if hasDoc \|\| undocMembers then … else keep := false` | `if has_doc or self.options.undoc_members: … else: keep = False` | **I** | identical guard; the `else` drops the member outright. |
| 5 | `match privateMembers with \| disabled => keep := false` | `if self.options.private_members is None: keep = False` | **I** | the `disabled` arm. **part of the fixed behavior:** pre-patch an absent option made `private_members` falsy and dropped, post-patch `None` explicitly drops — same observable result for this arm, but now one branch of a three-way dispatch. |
| 6 | `\| all => keep := true` | `elif self.options.private_members is ALL: keep = True` | **I** | the `all` arm — keep every documented private member (the `:private-members:` with no argument case, via the `members_option` `ALL` sentinel). |
| 7 | `\| names ns => if dropAsInherited then keep := false else keep := ns.contains memberName` | `elif is_filtered_inherited_member(membername): keep = False / else: keep = membername in self.options.private_members` | **I** (the changed op, deeply modeled) | **the fixed operation.** This entire name-selective arm is NEW in the patch — pre-patch there was no list case at all (the option was a bool). `membername in self.options.private_members` ↔ `ns.contains memberName` (list membership over ASCII identifiers); the inherited-member carve-out is the `dropAsInherited` guard. The prepatch impl has no such arm (it keeps every documented private member whenever the option is present). |
| 8 | `return keep` (`Bool`) | the value of `keep` consumed by the surrounding `if keep: ret.append(...)` | **R** | result modeled as `Bool`; `True`⇒documented, `False`⇒dropped. The surrounding append / the `autodoc-skip-member` event hook are outside the modeled decision (the decision computes `keep`; downstream consumption is unchanged by the patch). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch private-member keep decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_keepPrivateMember` pins `result` for EVERY input combination
  (it is a single total `if/match` equation — directive 5 frame: nothing left
  unconstrained; directive 8: the result is grounded entirely in the inputs
  `privateMembers`/`memberName`/`hasDoc`/`undocMembers`/`dropAsInherited`, with no
  ungrounded oracle). A verifying impl MUST drop on `disabled`, keep on `all`,
  and on `names ns` keep exactly the listed, non-inherited members — and drop
  everything when the member is neither documented nor undoc-kept.
- The discriminating clause is the `names` arm: when `privateMembers = names ns`,
  `hasDoc = true`, `dropAsInherited = false`, the spec demands `result =
  ns.contains memberName`. The prepatch impl returns `enabled && (hasDoc ||
  undocMembers)` = `true` for ANY member when a selection is present — so for a
  member NOT in `ns` it returns `true` while the spec demands `false`. Hence the
  carried gold proof's `names`-arm `rfl` step fails to typecheck against the
  prepatch impl (G-DIFF/G-PANEL).
- This is exactly what `test_private_members` exercises: `private-members =
  ["_public_function"]` keeps `_public_function` but drops `private_function`
  (post-patch); pre-patch the bool flag kept both.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  decision, EXHAUSTIVELY over the modeled abstraction (3 option shapes × a small
  ASCII name alphabet × hasDoc/undocMembers/dropAsInherited booleans × list
  contents) plus ≥1e5 fuzzed points (0 disagreements).
