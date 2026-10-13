# refinement.md — django__django-11292

The operation-by-operation correspondence between `model.py`'s implementation
(`parser_offers_skip`, `will_run_validation`, and the deep pure helpers) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/library-semantics by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The parser-exposure site — `create_parser` (`django/core/management/base.py:289`)

Gold hunk:
```
+ if self.requires_system_checks:
+     parser.add_argument(
+         '--skip-checks', action='store_true',
+         help='Skip system checks.',
+     )
```

Modeled by `parser_offers_skip(requires_validation)`.

| # | model.py impl op (`parser_offers_skip`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requires_validation: bool` | `self.requires_system_checks` | R | bool ↔ bool identity (mapping.md §2). |
| A2 | `if requires_validation: return True else return False` | `if self.requires_system_checks: parser.add_argument('--skip-checks', store_true, ...)` | I + A-reference | the control-flow guard is the identical concrete branch (I); registering the option ↔ the parser "offering" the skip request is the **A-reference**: `axiom_check.py` (G-AX §3.1) validates that a real `argparse` parser built with this guard exposes `skip_checks` in its namespace iff `requires_validation` and rejects the token otherwise. There is no consumed axiom — the exposure is modeled deeply as the boolean `Result() == requires_validation`. |

## B. The validation-gate site — `execute` (`django/core/management/base.py:360`)

Gold hunk:
```
- if self.requires_system_checks and not options.get('skip_checks'):
+ if self.requires_system_checks and not options['skip_checks']:
      self.check()
```

This single line is the gate. The *behavioural* change that makes the gate honour
a command-line skip request lives in site A (the parser now supplies a real
`skip_checks` value); the `.get(...)` → `[...]` edit is observationally identical
given site A (the key is always present for a validating command, R2). Modeled
by `will_run_validation(requires_validation, requested_skip)`.

| # | model.py impl op (`will_run_validation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `skip = parser_offers_skip(requires_validation) and requested_skip` | the value `options['skip_checks']` for a validating command — present iff the option was registered (site A), holding the user's `--skip-checks` token (`store_true`) | R + A-reference | `parser_offers_skip(...)` is the modeled site-A result (under spec, not an axiom); `and requested_skip` refines `options['skip_checks']`: the request is effective only when the option was offered (mapping.md §2, §3.2). G-AX validates the `store_true` default+presence semantics against real `argparse`. |
| B2 | `if requires_validation and not skip: return True else return False` | `if self.requires_system_checks and not options['skip_checks']: self.check()` | I | the identical concrete boolean gate; `Result() == True` ↔ `self.check()` is invoked. `requires_validation` ↔ `self.requires_system_checks` (R, A1). |

The spec helper `effective_skip(rv, rs)` equals `parser_offers_skip(rv) and rs`
(since `skip_request_offered(rv) == rv`), so the impl's `skip` equals the spec's
`effective_skip` and the postcondition
`Result() == (requires_validation and not effective_skip(...))` is exactly the
gold gate.

## C. The discriminating behaviour and the prepatches

The change exists so that, for a command that requires validation, a
command-line skip request is **honoured** (the validation pass does not run).
This is the postcondition
`Implies(requires_validation and requested_skip, not Result())` of
`will_run_validation`, and `Result() == requires_validation` of
`parser_offers_skip`.

- `model_prepatch.py` reverts **site A**: the parser never offers the skip
  request (`create_parser` pre-patch has no `--skip-checks` registration). It
  fails `parser_offers_skip`'s postcondition `Result() == requires_validation`
  (returns `False` for a validating command). Downstream, with the skip request
  always dropped, `will_run_validation` would run validation even when a skip was
  asked — exactly the pre-fix behaviour the F2P test `test_skip_checks` catches
  (running a validating command with broken settings + `--skip-checks` errored
  pre-patch because the request was never effective).
- `model_prepatch_2.py` reverts **site B**: the gate ignores the (effective)
  skip request and runs validation whenever required (`if requires_validation:
  return True`). It fails the gate postcondition
  `Result() == (requires_validation and not effective_skip(...))` (and the
  discriminating `Implies(requires_validation and requested_skip, not Result())`).

Both prepatches keep the spec byte-identical (G-DIFF same-spec; verified by
region-hash equality) and FAIL verification on the discriminating clause.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The two genuinely-changed operations —
the parser registering the skip option, and the gate reading the resulting
namespace value — are modeled **deeply** as boolean logic (no `@ContractOnly`
axiom is consumed). Their reliance on standard-library `argparse` semantics
(option exposed iff registered; `store_true` default `False`/present) is the
**A-reference** that `axiom_check.py` (G-AX) validates against the real
`argparse`. There are no consumed axioms and no dead axioms.

## E. verify(model) ⇒ resolved

`parser_offers_skip` verifies only if it offers the skip request exactly for
validating commands (site A); `will_run_validation` verifies only if it runs
validation iff required AND no effective skip is in force, and in particular
honours a skip request for a validating command (site B). By R (bool ↔ bool;
`options['skip_checks']` ↔ `effective_skip`) and A-reference (the real `argparse`
exposes/defaults the `store_true` option exactly as the deep model assumes,
G-AX), the verified decision equals the gold `execute` gate after the gold
`create_parser` registers the option. The gold patch resolves (G-RESOLVE).
Trust points: refinement fidelity (this document, G-EQ) and the single
A-reference's soundness (G-AX) — no consumed axiom.
