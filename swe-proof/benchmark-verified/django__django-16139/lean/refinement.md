# refinement.md — operation correspondence (django__django-16139)

Maps every op in `implementation_passwordHelpText` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python is
`password.help_text = password.help_text.format(f"../../{self.instance.pk}/password/")`.
The only change vs pre-patch is the URL argument: `"../password/"` becomes
`f"../../{self.instance.pk}/password/"`. The substitution callee (`str.format`)
is unchanged; we model it deeply as `formatFirst` and reconstruct the URL
argument concretely as `mkUrl`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut helpText := template` | `password.help_text` (the template carrying one `{}`) bound for substitution | I | concrete template carrier; `str` ↔ `List Char` (mapping.md) |
| 2 | `let url := mkUrl pk` = `"../../" ++ toString pk ++ "/password/"` | `f"../../{self.instance.pk}/password/"` | R | f-string interpolation of an integer pk ↔ `toString (pk : Nat)` (decimal digits, no separators); the `pk : Nat ↔ self.instance.pk` bijection (mapping.md). This is the CHANGED expression, reconstructed concretely (not axiomatized). |
| 3 | `helpText := formatFirst helpText url` | `password.help_text.format(url)` | A-reference | the UNCHANGED single-positional-field `str.format` modeled deeply; validated == real `str.format` by G-AX. NOT axiomatized. |
| 4 | `return helpText` | assignment `password.help_text = …` and return of the computed string | I | identity return of the computed character sequence |

No A-consumed rows: the proof discharges `formatFirst`/`mkUrl` directly; no
UNCHANGED callee property is assumed (axioms region empty). No
changed-inexpressible op.

The discriminating clause is rows 2–3: the URL argument substituted into the
template. The post-patch spec pins `formatFirst template (mkUrl pk)` where
`mkUrl pk = "../../" ++ toString pk ++ "/password/"`. The prepatch impl uses
`mkUrlBug pk = "../password/"` (the fixed single-component path, ignoring `pk`),
so its `correct_passwordHelpText` cannot close against the frozen
`problem_spec_passwordHelpText`. That is the G-DIFF signal.
