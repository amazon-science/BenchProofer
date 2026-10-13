# refinement.md — operation correspondence (django__django-14089)

Maps every op in `implementation_reversed` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch adds `OrderedSet.__reversed__(self): return reversed(self.dict)`. The
carrier's members are the keys of `self.dict` in insertion order (modeled as
`xs : List Int`); `reversed(self.dict)` yields those members in reverse order.
We model that order-reversal deeply as `List.reverse`, realized by an
accumulator prepend-fold (`acc := x :: acc`) so the last-seen element ends up
first.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `xs : List Int` (the carrier's ordered members) | `self.dict` keys in insertion order | R | dict-of-ordered-keys ↔ `List Int` bijection (mapping.md); the member sequence passed through unchanged |
| 2 | `let mut acc := []` ; `for x in xs do acc := x :: acc` ; `return acc` | `reversed(self.dict)` | R/I | the **changed op** modeled deeply: prepending each element onto the accumulator in forward order produces the exact reverse of the input order, == `xs.reverse`; this is what `reversed` over an insertion-ordered dict computes. NOT axiomatized. |

No A-consumed rows: the proof discharges the reversal directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: the only callee (`reversed` over an order-preserving dict) is
reproduced concretely as a `List.reverse`-equivalent prepend-fold, not abstracted
behind a model that needs G-AX validation. No changed-inexpressible op.

The discriminating clause is row 2: post-patch the elements are produced in
reverse insertion order (`xs.reverse`); the prepatch impl (no `__reversed__`
method existed → iterating yields forward order) produces them in their original
order (`acc := acc ++ [x]`, i.e. `xs` itself). The two agree only when
`xs = xs.reverse` (e.g. empty or singleton or palindromic lists) and differ on
every other input — e.g. `[1,2,3]` ↦ `[3,2,1]` (post-patch) vs `[1,2,3]`
(prepatch). Hence the prepatch `correct_reversed` cannot close against the frozen
`problem_spec_reversed` (`result = xs.reverse`) — the G-DIFF signal. The F2P test
`list(reversed(OrderedSet([1,2,3]))) == [3,2,1]` is exactly this discriminator.
