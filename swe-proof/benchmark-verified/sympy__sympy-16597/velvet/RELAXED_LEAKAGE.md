# RELAXED_LEAKAGE — sympy__sympy-16597

Disposition: **KEEP with relaxed leakage** (per `RELAXED_LEAKAGE.md`).
`meta.json relaxed_leakage = true`; the G-LEAK gate records status
`"relaxed"` mechanically (`src/swebench_unified/gates/leak.py`) from that
flag plus this file. In this unified repo the policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the
instance with the leak allowed"). Same disposition class as
django__django-11141 / django__django-11265 in this tree.

## The problem_statement ↔ gold mismatch

The public `problem_statement` reports a single symptom and one expectation:

> `a.is_even does not imply a.is_finite`
>
> `m = Symbol('m', even=True); print(m.is_finite)` → `None`
>
> "I would expect that a number should be finite before it can be even."

So the public issue is exclusively about the `even → finite` edge.

The gold patch does **not** add an `even → finite` rule directly. It adds a
`& finite` conjunct to the consequents of **rational / algebraic / irrational /
transcendental** in the assumption-rule table; `even → finite` then falls out
transitively (`even → integer → rational → finite`). The FAIL_TO_PASS tests are
`test_infinity`, `test_neg_infinity`, `test_other_symbol` — which pin the
boundedness-forcing edges and their contrapositives on `oo` / `-oo` and a generic
symbol, not the `even` symptom in isolation.

## What leaks, and why it is unavoidable

A **faithful** spec must pin the boundedness-forcing membership edges for the
"small" number sets (rational / algebraic / irrational / transcendental) and the
two-directional closure, because the F2P tests assert e.g.
`Symbol('x', rational=True).is_finite is True`,
`Symbol('x', irrational=True).is_finite is True`, and the `oo`/`-oo`
contrapositives (unbounded ⇒ not rational/algebraic/irrational/transcendental ⇒
not integer ⇒ …). A spec built only from the public `even → finite` symptom
would at most pin `even → finite`; that neither discriminates the gold (which
fixes `even → finite` *indirectly* via `even → integer → rational → finite`) nor
satisfies `test_infinity` / `test_neg_infinity`, so it would admit wrong impls
that verify yet fail the hidden tests — i.e. it would violate G-EQ /
`verify ⟹ correct`. The four class edges and the closure are therefore
**mandatory** for faithfulness.

But that discriminating vocabulary is absent from the public text. Token scan
against `instance.json`:

| token | in `problem_statement` | in `hints_text` |
|---|---:|---:|
| `even` | 3× | 2× |
| `finite` | 4× | 5× |
| `bounded` | **0×** | **0×** |
| `integer` | **0×** | 2× |
| `rational` | **0×** | 3× |
| `algebraic` | **0×** | **0×** |
| `irrational` | **0×** | **0×** |
| `transcendental` | **0×** | **0×** |

The `rational`-family boundedness mechanism appears in `hints_text` only for
`rational` (the suggested potential fix); `algebraic` / `irrational` /
`transcendental` / `bounded` appear in **neither** the `problem_statement` **nor**
`hints_text`, living only in the gold diff / hidden `test_patch`. The public
statement is the `even` symptom; the gold/tests are the rational-family
boundedness rules. The two are about different things.

Therefore any faithful spec necessarily reveals behavior the public task text
does not contain — the leak is in the *behavior itself* (the set-containment
edges that force boundedness, and their contrapositive closure), not in narration
that could be removed. No `problem_statement`-derivable reformulation models the
gold fix. This is the precise condition `RELAXED_LEAKAGE.md` accepts.

## Requirements check (RELAXED_LEAKAGE.md)

1. **Core is sound.** G-VERIFY pass (Solution.lean exit 0); G-DIFF fail — both
   prepatch variants (`Solution_prepatch.lean`, `Solution_prepatch_2.lean`) share
   the spec exactly (`same_spec` True) and each FAILS verification on the
   `consistentTheory` closure clause (one variant per independently-fixed
   deduction); G-EQ sound + tight (refinement is all R / A-reference, no consumed
   axiom, no kind-3; the closure theory is a spelled-out predicate over the
   three-valued fact record, not an answer-key oracle — directive 8 N/A); G-AX
   vacuous (no axioms); G-CONF agrees with the real patched assumption engine
   (407 observations, 0 disagreements; rc=1 against the prepatch engine);
   faithfulness clean (the deduction tables match the real engine on the F2P
   seeds; the model only under-deduces, the conservative direction);
   **G-RESOLVE**: `patch.diff` == gold verbatim, harness resolves.
2. **The leak is genuinely unavoidable**, established above: the
   `bounded` / `algebraic` / `irrational` / `transcendental` discriminators are
   0× in both `problem_statement` and `hints_text`, present only in
   gold / `test_patch`; the public `even → finite` symptom does not pin the
   tested `oo`/`-oo` contrapositives or distinguish the indirect gold mechanism.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still passes (the
   spec view names no patched path or symbol — no `_assume_rules`, `FactRules`,
   `FactKB`, `deduce_all`, `Symbol`, `S.Infinity`; only generic identifiers and
   the abstract containment vocabulary); the leak is semantic, as the policy
   expects.

## Scope of what is disclosed

The spec view discloses the abstract set-containment theory: membership in the
"small" number sets (rational / algebraic / irrational / transcendental) forces
boundedness (`finite`), integers are rational, even/odd are integers, and the
closure propagates contrapositives so an unbounded quantity is none of those.
Nothing about the patched file, the `_assume_rules` / `FactRules` / `FactKB`
assumption-engine symbols, the rule-table edit mechanism, or any diff line is
named in the spec view.
