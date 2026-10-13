# refinement.md — sympy__sympy-17139

Operation-by-operation correspondence between `implementation_powerRewrite`
(Solution.lean impl region) and `patch.diff` (the gold edit to `_f` inside
`_TR56`). Tags: **R** type refinement · **A-consumed** proof uses an axiom ·
**A-reference** deep-modeled callee validated == real callee by G-AX · **I**
identical concrete op.

The patch inserts one guard into the per-node rewrite `_f`: after the existing
"is this a matching power?" test and before the existing exponent-comparison
body, return `rv` unchanged when the exponent is not real. Modeling `_f` as a
three-way early-return decision tree over the observable branch queries exposes
the difference: post-patch a matching power with a non-real exponent short-circuits
to `rv`; pre-patch it falls into the rewrite body (which, in reality, crashes on
the invalid complex order comparison `rv.exp < 0`).

| # | `implementation_powerRewrite` op | `patch.diff` / post-patch Python op | tag | note |
|---|---|---|---|---|
| 1 | `if !(isMatchingPow rv) then return rv` | `if not (rv.is_Pow and rv.base.func == f): return rv` | R/I | `isMatchingPow` ↔ the structural test; unchanged early exit |
| 2 | `if !(expIsReal rv) then return rv` | `if not rv.exp.is_real: return rv` | R | `expIsReal` ↔ `rv.exp.is_real`; this IS the fix (the added discriminating guard) |
| 3 | `return transform rv` | fall through to the exponent-driven rewrite body (`rv.exp < 0` … `h(g(...)**2)**e`) | R/I | `transform` ↔ the unchanged rewrite body; reached only for a matching real-exponent power |

Every op is R or I. No op is A-consumed or A-reference:

- The changed decision (op 2 — the realness guard / short-circuit) is modeled
  DEEPLY as a control-flow branch over the observable `expIsReal` query;
  SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so it is spelled
  out in the impl and pinned in the spec.
- `isMatchingPow`, `expIsReal`, `transform` are UNCHANGED operations carried as
  opaque SIGNATURES (no `_prop` axiom). Each appears identically in the spec and
  the impl, so they cancel in the differential test and the proof consumes no
  property of any. Hence the `axioms` region declares only signatures and
  **G-AX skips**.

The spec leaves NO output component free: for every input the result `result` is
pinned to exactly one of `rv` (ops 1, 2) or `transform rv` (op 3), keyed on the
two observable branch queries (directive 5 frame, directive 8 grounding — the
result is produced by the modeled branch, not echoed from an oracle).

## Pre-patch (the bug)

`Solution_prepatch.lean`'s impl reproduces the defect: the loop omits op 2, so
after the matching test it unconditionally `return transform rv` — exactly the
pre-patch `_f` with no `rv.exp.is_real` guard. Its `correct_powerRewrite` cannot
close: the spec's middle conjunct requires `isMatchingPow rv = true →
expIsReal rv = false → result = rv`, but the prepatch yields `transform rv` there;
for any expression with `isMatchingPow = true`, `expIsReal = false`, and
`transform rv ≠ rv` the prepatch violates the spec. This is precisely the
`cos(x)**I` / `sin(x)**I` scenario (a matching power with a non-real exponent that
must be returned untouched). (G-DIFF: the prepatch must fail G-VERIFY.)

## G-CONF (R/I differential)

`conformance_check.py` builds the Python shadow of the impl region (op-for-op,
with `is_matching`, `exp_real`, and `transform` modeled identically on both sides)
and diffs it against an in-process replica of the POST-PATCH `_f` decision tree
over the edge corpus + ≥1e5 fuzzed inputs; zero disagreements expected. Pinned
seed 17139. The impl region is NOT all-A-tagged (op 2 is R), so
`conf_skip = false`.
