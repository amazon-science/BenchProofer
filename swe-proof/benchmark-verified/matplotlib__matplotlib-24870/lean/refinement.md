# refinement.md — matplotlib__matplotlib-24870

Maps every operation in `implementation_chooseLevels` to its `patch.diff`
counterpart. Tags: **R** type refinement, **A-consumed** proof-consumed axiom,
**A-reference** deeply-modeled callee validated == real callee by G-AX, **I**
identical concrete op.

The modeled function is the `levels_arg` selection block inside
`_process_contour_level_args` (the only behaviour the patch changes). The patch
also threads `z.dtype` through `_contour_args`/`_check_xyz` (both the quad-grid
and the triangular-grid paths); that plumbing is a pure data-flow refactor that
makes the data dtype available to the selection — it carries no behaviour of its
own and is represented by the `zIsBool` input to the modeled function.

| # | Lean op (`implementation_chooseLevels`) | patch.diff / source counterpart | tag |
|---|---|---|---|
| 1 | `match userLevels with \| some lv => return lv` | `else: levels_arg = self.levels` (the `self.levels is not None` arm — caller gave an explicit spec) | I |
| 2 | `\| none => match args with \| a :: _ => return a` | `if args: levels_arg = args[0]` (post-patch truthiness test on the leftover positional level args) | R |
| 3 | `\| [] => if zIsBool then if filled then return .explicit [0,1/2,1]` | `elif np.issubdtype(z_dtype, bool): if self.filled: levels_arg = [0, .5, 1]` | R |
| 4 | `else return .explicit [1/2]` | `else: levels_arg = [.5]` (boolean data, line contour) | R |
| 5 | `else return .count 7` | `else: levels_arg = 7  # Default, hard-wired.` (non-boolean data) | R |

Refinement (R) details:
- **Op 2** `args : List LevelsArg`, `args[0]` ↔ Python `args[0]`. The pre-patch
  `len(args) == 0` test and the post-patch `if args:` truthiness test are
  equivalent for the level-args list (it holds only plain elements). Modeled by
  `match args with | a :: _ | []`.
- **Ops 3–5** `zIsBool : Bool` ↔ `np.issubdtype(z_dtype, bool)`; `filled : Bool`
  ↔ `self.filled`. The literal `[0, .5, 1]` / `[.5]` ↔ `LevelsArg.explicit
  [0,1/2,1]` / `[1/2]` with exact `Rat`s (`.5 = 1/2`). The hard-wired count `7`
  ↔ `LevelsArg.count 7`.

No A-consumed axioms: the selection is modeled value-exactly; nothing the proof
needs is assumed about a callee.

A-reference: the downstream expansion of `LevelsArg.count n` into concrete
automatic levels (`_autolev`) and the `np.asarray`/in-range conversion are NOT
part of the modeled function (they run after the selection and are unchanged by
the patch). `conformance_check.py` reconciles the `count` leg against the REAL
`_autolev`-driven `levels` output and the `explicit` legs against the real
`levels` output, so the chosen `LevelsArg` is validated as faithfully producing
the observable `cs.levels` (G-CONF). No op is changed-yet-inexpressible.
