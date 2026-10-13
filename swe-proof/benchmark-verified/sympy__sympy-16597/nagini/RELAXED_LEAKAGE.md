# RELAXED_LEAKAGE — sympy__sympy-16597 (nagini)

Disposition: **KEEP with relaxed leakage.** `meta.json relaxed_leakage = true`
plus this file; `src/swebench_unified/gates/leak.py` then records G-LEAK with
status `"relaxed"`. The governing policy is
`prompts/nagini/spec_guide.md` directive 6, "**Exception — relaxed-leakage:**
a few instances are `problem_statement ↔ gold` MISMATCHES where the gold's
tested discriminator exists only in `hints_text`/gold internals, so a
*faithful* spec MUST name it." Same disposition class as the velvet cell of
this instance and as django__django-11141 / django__django-11265 in this tree.

This document describes the spec text
`model.py` sha256 `b4000ef55fedfcca88f2239650063f50c865534186be678eaff69a3537db91f7`
(`sha256sum model.py`). Everything below is a measurement re-run against THAT
text, with the command that produced it, not an assertion inherited from an
earlier revision of the bundle or from another cell.

## 1. The public statement and the gold edit are about different things

Solver-visible `problem_statement` (whole text, `instance.json`): the title
`a.is_even does not imply a.is_finite`, a transcript of
`Symbol('m', even=True).is_finite` printing `None`, and the sentence "I would
expect that a number should be finite before it can be even." That is one edge:
`even -> finite`.

The gold patch adds no `even -> finite` rule. It appends a `& finite` conjunct
to the consequents of four *other* classes in the assumption-rule table
(`sympy/core/assumptions.py` post-patch L166 `'rational -> real & finite'`,
L168 `'algebraic -> complex & finite'`, L179
`'transcendental == complex & !algebraic & finite'`, L194
`'irrational == real & !rational & finite'` — line numbers re-read with
`grep -n` in the patched worktree), regenerates the compiled CNF/dict mirrors,
and lets `even -> finite` fall out transitively through
`even -> integer -> rational -> finite`.

FAIL_TO_PASS is `test_infinity`, `test_neg_infinity`, `test_other_symbol`.

### 1.1 The public fix does not resolve — measured

`base_commit = 6fd65310fa3167b9626c38a5487e171ca407d988` in the instance image
`swebench/sweb.eval.x86_64.sympy_1776_sympy-16597:latest`; per row
`git checkout -- . && git apply <test_patch>`, then one candidate rule inserted
into `_assume_rules`, then the three F2P test functions called in-process
(`sympy.core.tests.test_assumptions`, one `try/except AssertionError` per
function, first failing assertion recovered from the traceback line). The image
ships no `pytest`, so the in-process call is the runner; it is the same code
path the harness's `bin/test` invocation drives.

| candidate rule added | F2P | first failing assertion | `Symbol('m',even=True).is_finite` |
|---|---|---|---|
| *nothing* (pre-patch) | **3 failed** | `oo.is_integer is False` → `None` | `None` |
| `'even -> finite'` (the literal public expectation) | **3 failed** | `oo.is_integer is False` → `None` | `True` |
| `'integer -> finite'` (the strongest public-adjacent guess) | **3 failed** | `oo.is_rational is False` → `None` | `True` |
| `'rational -> real & finite'` (the exact `hints_text` suggestion, alone) | **3 failed** | `oo.is_algebraic is False` → `None` | `True` |
| the gold patch | **3 passed** | — | `True` |

Three candidate impls therefore deliver exactly what the public text asks for —
`is_finite` on an `even` symbol stops being `None` — and still fail every F2P
test. The discriminator is not "make `even` imply `finite`". It is *which*
number sets force boundedness — all four of rational / algebraic / irrational /
transcendental — because the hidden assertions on `oo` / `-oo` are the
**contrapositives** of exactly those four edges (`oo.is_rational is False`,
`oo.is_algebraic is False`, `oo.is_transcendental is False`,
`oo.is_irrational is False`, `oo.is_noninteger is True`).

The `hints_text` single-edge fix is not merely one class short, it is wrong:
with `'rational -> real & finite'` alone the engine deduces
`oo.is_irrational = True` (measured in the same run — `oo` is real and now
provably not rational, and nothing yet blocks the `irrational == real &
!rational` equivalence), while the hidden test asserts
`oo.is_irrational is False`. Only the gold's `& finite` on the `irrational`
rule blocks it.

### 1.2 The discriminating vocabulary is absent from the public text

Word-bounded, case-insensitive counts over `instance.json`
(`(?<![\w-])<token>(?![\w-])`, so the `is_<token>` attribute spellings in the
transcript are excluded, being attribute names rather than concepts):

| token | `problem_statement` | `hints_text` |
|---|---:|---:|
| `even` | 2 | 2 |
| `finite` | 1 | 4 |
| `real` | **0** | 5 |
| `rational` | **0** | 3 |
| `integer` | **0** | 2 |
| `bounded` | **0** | **0** |
| `algebraic` | **0** | **0** |
| `irrational` | **0** | **0** |
| `transcendental` | **0** | **0** |
| `complex` | **0** | **0** |
| `odd` / `prime` / `composite` | **0** | **0** |
| `noninteger` | **0** | **0** |
| `infinite` / `infinity` | **0** | **0** |
| `contrapositive` | **0** | **0** |

`algebraic`, `irrational`, `transcendental`, `bounded`, `complex` and the whole
infinity/contrapositive mechanism are 0× in **both** the public statement and
the hints; they exist only in the gold diff and the hidden `test_patch`. And
the leakage baseline is the `problem_statement` alone, where `real`, `rational`
and `integer` are 0× as well.

## 2. Why a faithful spec cannot avoid naming it

The obligation `verify ⟹ correct` requires the spec to REJECT every impl whose
repo counterpart fails F2P. §1.1 exhibits three such impls whose only content is
"boundedness is forced by `even`/`integer`/`rational`". A spec built from the
public statement alone can pin at most `even -> finite`, which all three of them
satisfy — it would admit an impl that verifies and fails the hidden tests. To
exclude them the spec must state that membership in *each* of the four sets
forces boundedness, and that the closure runs two-directionally so an unbounded
quantity is in none of them. That statement IS the disclosure. The leak is in
the behaviour, not in narration that could be deleted: it cannot be removed
without deleting the clause that rejects the §1.1 impls.

Checked mechanically, in the direction the policy prescribes (strip the clause
and see whether the spec still rejects the pre-patch impl):
`model_prepatch.py` and `model_prepatch_2.py` share the spec byte-identically
(`swebench_unified.markers.same_spec` → True for both) and each FAILS
verification on precisely that clause (`bash scripts/nagini_verify.sh`, both
re-run against this revision):

```
model_prepatch.py:184  error: Postcondition of deduce_even might not hold.
                              Assertion consistent_theory(Result()) might not hold.
model_prepatch_2.py:244 error: Postcondition of deduce_infinite might not hold.
                              Assertion consistent_theory(Result()) might not hold.
```

The boundedness closure is therefore load-bearing, not decorative. The
sharper form of the same check is rival R2 in §4: an impl that propagates
unboundedness to `rational` only — the §1.1 `hints_text` fix, transcribed into
this model — is REJECTED by the spec. Delete the boundedness clauses and that
impl verifies.

## 3. What the spec view discloses, and what it does not

Facet disclosed: the abstract theory of the number sets — containments
(integer ⊆ rational ⊆ algebraic ⊆ complex, rational ⊆ real ⊆ complex,
irrational ⊆ real, transcendental ⊆ complex, even/odd/prime/composite ⊆
integer), boundedness (the rationals, algebraic numbers, irrationals and
transcendentals are sets of finite quantities), exclusions (rational vs
irrational, algebraic vs transcendental, even vs odd, integer vs non-integer),
and the two-directional closure; plus the two witnessed fact tables that the
theory forces for an `even` seed and for an unbounded real seed.

Where that disclosure lives, exhaustively, in `model.py` line numbers (the spec
view is this file minus the two `impl` regions, so every line cited here is at
the same number in both):

* the docstring's BOUNDEDNESS group, L14-17, and the contrapositive sentence,
  L24-26;
* the two witnessed queries, L30-36;
* the four boundedness implications, L123 / L128 / L144 / L148, and the four
  `finite is False` contrapositives, L153-156, inside `consistent_theory`;
* the pinned outcomes: `Ensures(Result().finite is True)` at L188 for the
  `even` seed, and L249-258 for the unbounded seed.

Not disclosed anywhere in `model.py`: no patched path, no diff line, no diff
marker, no repo symbol (`_assume_rules`, `FactRules`, `FactKB`,
`deduce_all_facts`, `StdFactKB`, `Symbol`, `S.Infinity`, `get_known_facts` all
grep to 0 in the spec view), no rule-table string of the patched table, no "the
rule X was extended to Y" narration, and no pointer to the hidden test suite.
The mechanical screen agrees: `swebench_unified.leakage.screen(model.py, …)`
returns `passed=True` with `hard_failures == []` and `warnings == []`, so the
leak that remains is purely semantic — the shape this relaxation exists for.
`swebench_unified.leakage.reviewer_directed` on this file returns `[]`.

### 3.1 The recorded leakage finding, item by item

A review of an earlier revision of this bundle recorded the disclosure as a
LEAKAGE finding: the docstring rendered the four edited rules one class at a
time (`rational` → real & algebraic & bounded, `algebraic` → complex & bounded,
`irrational` → real & !rational & bounded, `transcendental` → complex &
!algebraic & bounded), conjunct for conjunct, alongside the `oo` fact table.
That reading of the text was accurate, and the token counts in §1.2 are the same
ones it measured.

Two things changed in response, and one did not:

* The per-class list was restated as the CONTAINMENT / BOUNDEDNESS / EXCLUSION
  groups now at L9-22, and the heading over the two witnessed queries no longer
  carries a FAIL_TO_PASS label. That removes a shape that read as a rendering of
  four specific rule strings.
* The grouping does not reduce the semantic content, and this document does not
  claim it does. A reader can still derive "membership in rational, algebraic,
  irrational or transcendental forces boundedness" from L14-17 — and, with the
  docstring deleted entirely, from the executable clauses at L123 / L128 / L144
  / L148 on their own.
* Nothing was removed from the obligations. §2 is the measurement of why:
  every one of those clauses is what rejects a §1.1 impl, and §4 re-runs the
  rival that proves it.

So the residual disclosure is carried by the formal content, and the honest
description of this cell is a `problem_statement ↔ gold` mismatch under
directive 6, not a de-narration debt. The same disclosure appears in the
`lean` cell of this instance, whose `Solution.lean` names
`irrational`/`transcendental` 28 times (`grep -ic`) — the vocabulary is forced
by the behaviour, not by this bundle's prose style.

## 4. The core the relaxation leans on

Only no-leakage relaxes; `verify ⟹ correct` is unaffected and was re-measured
against this revision:

* **G-VERIFY** — `bash scripts/nagini_verify.sh model.py` → `Verification
  successful`, 17.2 s verifier time (18.5 s wall as recorded by the gate).
* **G-DIFF** — both prepatch twins `same_spec` True and both fail, each on the
  `consistent_theory` postcondition of a different deducer (one twin per
  independently-fixed deduction); the error lines are quoted in §2.
* **Falsification** — 8 fresh same-spec rivals plus a vacuity control, authored
  by rewriting only the two `impl` regions and each run through
  `python -m swebench_unified.adversary weakness nagini sympy__sympy-16597`.
  All nine came back `NOT-A-COUNTEREXAMPLE: attack does not verify`; the clause
  that rejected each, from the verifier:

  | rival | family | rejected by |
  |---|---|---|
  | R1 | over-approximation: resolves primality for the `even` seed | `Assertion (Result().prime is None) might not hold` |
  | R2 | partial domain: unboundedness propagated to `rational` only (the §1.1 hints fix) | `consistent_theory` on `deduce_infinite` |
  | R3 | boundary token swap: flips the one True-valued outcome, `noninteger` | `consistent_theory` on `deduce_infinite` |
  | R4 | oracle echo: sets only the explicitly-named `Ensures` fields, closure-derived ones Unknown | `consistent_theory` on BOTH deducers |
  | R5 | drops the even/odd exclusion (`odd` left Unknown) | `consistent_theory` on `deduce_even` |
  | R6 | leaves `complex` and `prime` Unknown for the unbounded seed | `consistent_theory` on `deduce_infinite` |
  | R7 | keeps every other pinned field but leaves `finite` Unknown for the `even` seed (the pre-patch reading) | `consistent_theory` on `deduce_even` |
  | R8 | divergence: the deduction never hands the record back | `Obligation leak check failed` (the `MustTerminate` obligation) |
  | C0 | `Assert(False)` vacuity control | `Assert might fail` — the contracts are satisfiable, not contradictory |

* **G-AX** — no `@ContractOnly` axiom is consumed; `axiom_check.py` validates
  the deep theory clause-by-clause against the real patched engine on 425
  observations and fails against the pre-patch engine.
* **G-CONF / G-RESOLVE** — conformance shadows the model against the real engine
  on 100012 checks with 0 disagreements; `patch.diff` is the gold patch verbatim
  and the harness resolves the instance.
* **G-MUT / G-PBT** — 20/20 mutants killed; 11/11 battery cases behaved as
  expected.
* **Full-table pinning** — every one of the 14 `KB` fields is pinned for both
  seeds (explicitly, or forced by `consistent_theory` from the seed), so no
  field of the observable is left free; see mapping.md §3.1. The `even` seed's
  pinned table was re-read off the patched engine in the image and agrees field
  for field, including the two fields the engine leaves Unknown
  (`prime`, `composite`).
