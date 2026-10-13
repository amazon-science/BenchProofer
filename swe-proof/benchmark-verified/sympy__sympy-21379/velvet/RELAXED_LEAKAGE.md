# RELAXED_LEAKAGE — sympy__sympy-21379 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition is not new analysis: the bundle's recorded P2 audit
(`verdict.md`, sub-review 3) already judged leakage = **RELAXED** and named
this exact fix ("re-disposition `G-LEAK.status` to `relaxed` and add an
in-bundle `RELAXED_LEAKAGE.md`"). The bundle had been mislabeled as a clean
G-LEAK pass, so a later standalone G-PANEL-3 run had no disposition to honor
and recorded the raw LEAKAGE verdict. This file records the disposition.

## The mismatch

The gold fix wraps the gcd-extraction block of `Mod.eval`
(`sympy/core/mod.py:168-173` @ base_commit) in a `try/except`:

```
try:
    G = gcd(p, q)
    if G != 1:
        p, q = [gcd_terms(i/G, clear=False, fraction=False)
                for i in (p, q)]
except PolynomialError:  # issue 21373
    G = S.One
```

i.e. when the shared-factor computation raises `PolynomialError` (which it
does on `Piecewise`-bearing operands), RECOVER with the trivial factor
`S.One` and both operands unchanged, instead of letting the exception
propagate out of `Mod.eval`.

**The public `problem_statement` is a pure symptom report.** It shows an
unexpected `PolynomialError` from `expr.subs({1: 1.0})` on
`exp(sinh(Piecewise(...) / z))` with real symbols, and the reporter states
"I am not really sure where the issue is" and "Not too sure how to debug
this one". Token scan of problem_statement: `PolynomialError` ×3,
`Piecewise` ×4 (both public), but `Mod` / `mod.py` / `gcd` / `gcd_terms` /
`S.One` / factor / common / extract / recover / catch / trivial / propagate
/ operand all = 0. The diagnosis and mechanism (some functions call `Mod`
when evaluated; `Mod.eval`'s `gcd` call raises on Piecewise operands; catch
it and fall back to `G = S.One`) live ONLY in `hints_text` (jksuom's diff +
Mod→gcd analysis), which is excluded from the solver-visible baseline.

**The leaking content is semantic, fully de-narrated at the token level.**
The spec view (docstrings of `extractSpec` / `extractCommonFactor`)
discloses: (a) the fix localizes to a shared-factor-extraction step over two
operands, (b) that computation can raise the polynomial error on
out-of-domain operands, and (c) the recovery is "factor = trivial `1`, both
operands unchanged, failure not propagated". No gold lexical token is
echoed: the spec view never names `mod.py`, `Mod`, `Mod.eval`, `gcd`,
`gcd_terms`, `S.One`, or the `try/except`; all are de-narrated to abstract
identifiers (`commonFactor`, `reduceTerm`, `extractCommonFactor`). The
patched file/symbol/callee cannot be reconstructed from the spec view; only
the abstract desired behavior can.

## Why the leak is unavoidable

Faithfulness forces the recovery semantics into the spec:

- The discriminating clause of the gold patch is precisely the recovery leg:
  on a raised polynomial error, factor := trivial `1` and both operands kept
  unchanged, failure NOT propagated. `Solution_prepatch.lean` (propagating
  `Except.error e`) fails verification exactly on that leg (G-DIFF).
- A spec that pinned only the PS-derivable symptom ("the step never fails")
  would admit wrong recoveries. The recorded G-EQ audit demonstrates the
  spec must reject them: atk_2 (error leg reduces the operands instead of
  leaving them unchanged) and atk_5 (recover with factor `0` instead of `1`)
  are wrong implementations whose refined patches corrupt `Mod.eval`'s
  downstream result (`G`, `p`, `q` feed the subsequent simplification and
  the returned `Mod`), breaking hidden-test behavior (`test_Mod` has 91
  PASS_TO_PASS companions pinning Mod semantics) — a `verify ⟹ correct`
  violation. So a faithful spec MUST pin the exact recovery triple
  `(1, p, q)`.
- No PS-only reformulation expresses that: the problem_statement contains
  neither the factor-extraction localization nor any recovery semantics
  (its author explicitly does not know where the issue is). Faithful +
  non-leaking is therefore provably impossible here.

This is the same faithful-must-leak shape as the dispositioned
matplotlib__matplotlib-24870 (lean) and sphinx-doc__sphinx-10466 (velvet)
instances: the discriminator exists only in hints_text + gold, and the spec
cannot be both faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit, `verdict.md`)

- G-VERIFY: `Solution.lean` verifies (3.0 s), proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (propagates the failure) fails to verify
  precisely on the `Except.error` leg — the right reason.
- G-EQ: SOUND / TIGHT — 6 spec-too-weak attacks (incl. propagate-the-error,
  reduce-on-error, constant-echo, drop-trivial-guard, recover-with-0,
  swapped-operands) all rejected; a structurally distinct positive control
  verifies (non-vacuous).
- G-PANEL-2 (faithfulness): FAITHFUL — only the changed block is modeled;
  the opaque no-`ensures` callee modeling is the least-presumptuous shape;
  in-container confirmation post-gold vs pre-gold.
- G-CONF: 0 / 100012 disagreements (seed 21379). G-AX: sound/vacuous
  (`"axioms": []`; A-reference facts confirmed — real `gcd` raises exactly
  `PolynomialError` on 6 Piecewise operands +327 fuzz, returns on 7
  polynomial operands +2000 fuzz). G-RESOLVE: resolved (gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the recover-with-trivial-factor-1, operands-unchanged semantics of
the shared-factor-extraction step).
