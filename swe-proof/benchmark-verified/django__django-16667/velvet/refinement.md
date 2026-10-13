# refinement.md — django__django-16667

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `dateComponentsText` `do` block plus the deep `dateText` /
`pseudoTriple` / `orZero` / `allZeroTriple` models it dispatches to) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep model validated == the real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I — no kind-3.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed routing — `value_from_datadict` all-present branch (`django/forms/widgets.py:1158-1164`)

Gold hunk:
```
                 # Return pseudo-ISO dates with zeros for any unselected values,
                 # e.g. '2017-0-23'.
                 return "%s-%s-%s" % (y or 0, m or 0, d or 0)
+            except OverflowError:
+                return "0-0-0"
             return date_value.strftime(input_format)
```

The branch (post-patch) routes the three outcomes of
`datetime.date(int(y),int(m),int(d))` to a return value:
- success → `date_value.strftime(input_format)`;
- `ValueError` → `"%s-%s-%s" % (y or 0, m or 0, d or 0)`;
- `OverflowError` → `"0-0-0"` (the new leg).

| # | Solution.lean impl op (`dateComponentsText`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `y m d : List Char` | `y`, `m`, `d` `str` locals on the all-present branch | R | `str` ↔ `List Char` code-point-wise (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)` and the field templates `%s_year`/`%s_month`/`%s_day`. Read-only — not `mut` (directive 5). |
| A2 | param `outcome : ConstructOutcome` (free input) | the result of `datetime.date(int(y),int(m),int(d))` then success-path `strftime` — the UNCHANGED callee | A-reference | the construct-and-format callee is unchanged; its observable result is one of three shapes (`rendered`/`notCalendar`/`unrepresentable`). Modeled as a free input (weakest contract, directive 7); the partition's exhaustiveness/faithfulness over the real callee is the A-reference G-AX validates (mapping.md §3.1). No consumed axiom. |
| A3 | `match outcome with \| .rendered s => Except.ok s` | the success fall-through `return date_value.strftime(input_format)` | I | identical concrete dispatch: a rendered value is returned verbatim. The opaque `s` is the callee's `strftime` text (A2). G-CONF runs the real callee, so the real `strftime` string flows through unchanged. |
| A4 | `\| .notCalendar => Except.ok (pseudoTriple y m d)` | `except ValueError: return "%s-%s-%s" % (y or 0, m or 0, d or 0)` | I + R | the ValueError fallback. `pseudoTriple y m d = orZero y ++ "-" ++ orZero m ++ "-" ++ orZero d`; `orZero` ⇔ the `x or 0` per-component empty→`'0'` coercion (mapping.md §1). Concrete transliteration (I) over R-refined components; G-CONF checks it. |
| A5 | `\| .unrepresentable => Except.ok allZeroTriple` | `except OverflowError: return "0-0-0"` (**the changed leg**) | I | the single behavioural change, modeled deeply and concretely: the overflow outcome returns the constant `"0-0-0"` (`allZeroTriple`) and crucially **returns a value** (`Except.ok`) rather than letting the exception escape. |
| A6 | `return result` (`Except DateErr (List Char)`) | the `return` of the branch's `str` | R | a returned `str` `s` ↔ `Except.ok s.toList`; the result is always `Except.ok` (`ensures ∃ r, out = Except.ok r`) ⇔ the post-patch branch never lets `OverflowError` escape. |

Discriminating content of the change — the OverflowError outcome must yield a
returned value (`"0-0-0"`), not an escaping exception — lives in
`dateText … .unrepresentable = Except.ok allZeroTriple` (model) ⇔ the
`except OverflowError: return "0-0-0"` leg (real). `Solution_prepatch.lean`
reproduces the pre-patch behaviour (the `unrepresentable` outcome falls through
to `Except.error .valueEscaped` — the uncaught crash) and **fails** the clauses
`ensures outcome = .unrepresentable → out = Except.ok allZeroTriple` and
`ensures ∃ r, out = Except.ok r` (G-DIFF, confirmed: unsolved goal `⊢ False` on
the `unrepresentable` case).

## B. Unchanged context — not modeled

The patch touches nothing outside the all-present try/except. The outer framing
of `value_from_datadict` (`y = data.get(self.year_field % name)` and the `m`/`d`
analogues, the `y == m == d == ""` → `None` short-circuit, the all-present `if`
guard, and the trailing `return data.get(name)`) is byte-identical pre- and
post-patch — identical context, not a modeled op. `dateComponentsText` models
exactly the inner branch the hunk edits; the conformance oracle (G-CONF) calls
the full real `value_from_datadict` with all-present inputs so the unchanged
framing is exercised end-to-end against the patched behaviour.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — adding
the `except OverflowError: return "0-0-0"` leg — is modeled **deeply and
concretely** (A5/`dateText`'s `unrepresentable` leg, an I op over the free
`outcome` input), not hidden behind an axiom about the function under change.
There is no consumed axiom at all. The only kind-A construct is the **unchanged**
construct-and-format callee (A2), modeled as a free input and validated as an
A-reference partition by G-AX (mapping.md §3.1) — never the changed op.

## D. verify(Solution) ⇒ resolved

`dateComponentsText` verifies only if, for **every** construction outcome, its
result equals `dateText y m d outcome` — in particular the `unrepresentable`
outcome must yield `Except.ok allZeroTriple` (A5) and the result is always
`Except.ok` (never an escape, A6). By R (`str ↔ List Char`, returned-`str` ↔
`Except.ok`, `orZero` ⇔ `x or 0`) and by the G-AX-validated exhaustive partition
(A2), the verified routing equals the post-patch branch:
overflow → `"0-0-0"`, ValueError → pseudo-ISO triple, success → `strftime`. By
G-CONF the R/I transliteration agrees with the real patched `value_from_datadict`
on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited (unchanged) callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: the unchanged-callee partition's faithfulness (G-AX, A2) and refinement
fidelity (this doc, G-EQ + G-CONF).
