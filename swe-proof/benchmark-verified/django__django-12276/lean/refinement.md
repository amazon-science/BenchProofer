# refinement.md — django__django-12276

Operation-by-operation correspondence between `implementation_useRequiredAttribute`
(Solution.lean impl region) and `patch.diff` (the ADDED
`FileInput.use_required_attribute`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `return (!isHidden) && (!initialPresent)` | `return super().use_required_attribute(initial) and not initial` where `super().use_required_attribute(initial)` = `not self.is_hidden` | R |

Decomposition of op 1:

| sub-op | Lean | Python | tag |
|---|---|---|---|
| 1a | `!isHidden` | `super().use_required_attribute(initial)` ≡ `not self.is_hidden` (the unchanged base rule, inlined) | R |
| 1b | `!initialPresent` | `not initial` (truthiness negated) | R |
| 1c | `_ && _` | `_ and _` (boolean conjunction) | I |

Notes:

- **Every step is R or I — no A.** The base rule `not self.is_hidden` is short,
  unchanged, and inlined DEEPLY as `!isHidden`; SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled decision and §0.7 forbids shipping a dead axiom.
  The `axioms` region is empty; **G-AX skips**.
- **1a (R):** Python `super().use_required_attribute(initial)` resolves through
  `Input` to `Widget.use_required_attribute`, which returns `not self.is_hidden`
  (it ignores `initial`). The refinement carries `self.is_hidden` as the Boolean
  input `isHidden`. The result class component is fully pinned — no output hole.
- **1b (R):** Python `not initial` tests `initial`'s truthiness; the refinement
  abstracts `initial` to the Boolean `initialPresent` (`bool(initial)`), the only
  property the decision reads. `not initial` ↔ `!initialPresent`.
- **1c (I):** Python `and` over two booleans is Lean `&&` (both short-circuit
  with identical truth tables on `Bool`).
- The **fix itself** is the ADDITION of this method to `FileInput`: pre-patch,
  `FileInput` had no override and inherited only the base rule `not is_hidden`
  (ignoring `initial`). The pre-patch impl (`Solution_prepatch.lean`) returns
  `(!isHidden)` — exactly the inherited base rule — which disagrees with the spec
  on the discriminating slice (`isHidden=false`, `initialPresent=true`): spec
  demands `false`, the bug yields `true`. That is the F2P observation
  (`use_required_attribute('resume.txt')` must be `False`).
- The patch's removal of the identical override from `ClearableFileInput` is a
  pure refactor (it inherits the same method from its new parent `FileInput`);
  `ClearableFileInput`'s observable behavior is unchanged, so it contributes no
  independently-fixed behavior and needs no separate triple/prepatch.
- **G-CONF** mechanically refutes the single R/I leg: the Python shadow of the
  impl is diffed against the post-patch decision over the full `Bool × Bool`
  domain plus ≥1e5 fuzzed inputs.
