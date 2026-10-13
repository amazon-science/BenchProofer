# refinement.md — django__django-16100

Maps every op in `implementation_changelistView` to its `patch.diff`
counterpart. Tags: **R** type refinement, **A-consumed** proof uses axiom,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let mut s := s0` | initial store state before the loop (`changecount = 0`, no writes yet) | R | `s0` ↔ pre-loop DB state |
| 2 | `for f in steps do` | `for form in formset.forms: if form.has_changed():` | R | `steps` = changed forms' save sequences, in order |
| 3 | `match f s with .ok s' => s := s'` | one form's `save_form`/`save_model`/`save_related`/`construct_change_message`/`log_change` sequence committing under the open `transaction.atomic` block | R | success commits the new store state |
| 4 | `.error e => return (s0, some e)` | a raise inside the `with transaction.atomic(...)` block triggers rollback of ALL writes done in the block, then propagates the exception | R | THE FIX: rollback to `s0`, not partial `s`. This is the discriminating clause vs. prepatch. |
| 5 | `return (s, none)` | block exits normally; all changes committed; loop falls through to `changecount` message / redirect | R | success path: store = all steps applied |

All ops are R (type refinement). No A-consumed (no axiom), no A-reference (no
opaque callee — callees are universally-quantified input step-functions, so the
contract holds for every callee behavior). No I op. No changed-inexpressible op:
the atomic rollback IS modeled deeply via the spec's `.error` branch pinning the
result to `(s0, some e)`.

conf_skip = false (impl region is all-R, mechanically differential-testable).
