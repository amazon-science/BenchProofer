# refinement.md — operation correspondence (django__django-13670)

Maps every op in `implementation_twoDigitYear` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python is `return '%02d' % (self.data.year % 100)`. There is no
external callee: `%` (modulo) and `%02d`-formatting are language primitives,
modeled deeply as integer arithmetic plus ASCII digit emission.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `year : Nat` (input) | `self.data.year` : `int` (≥ 0) | R | int ↔ Nat bijection on non-negative years (mapping.md). |
| 2 | `let r := year % 100` | `self.data.year % 100` | I | identical integer reduction modulo 100 |
| 3 | `let tens := r / 10` | tens digit of `'%02d' % r` (since `r < 100`) | I | high decimal digit; `%02d` pads to two digits, so `tens = r / 10` even when `r < 10` (gives leading `0`) |
| 4 | `let ones := r % 10` | units digit of `'%02d' % r` | I | low decimal digit |
| 5 | `return [digitChar tens, digitChar ones]` | `'%02d' % r` builds the two-character string | I/R | the two zero-padded decimal digits, each rendered ASCII via `Char.ofNat (48 + d)`; `str`↔`List Char` (R) |

No A-consumed rows: the proof discharges `twoDigitYear` directly; no UNCHANGED
callee property is assumed (axioms region empty). No A-reference rows: the
changed op underlies no external callee — it is closed arithmetic, modeled
deeply. No changed-inexpressible op.

The discriminating behaviour is the leading-zero / modulo treatment of years
below 1000 (rows 2–5). The prepatch impl computes `(toString year).drop 2` —
string-slicing the decimal rendering — which for `year < 1000` loses digits and
never pads (e.g. `476 → ['6']`, `42 → []`, `4 → []`), so its `correct_twoDigitYear`
cannot close against the frozen `problem_spec_twoDigitYear` (which pins
`twoDigitYear`, i.e. `476 → ['7','6']`, `4 → ['0','4']`). That is the G-DIFF signal.
