# mapping.md — sympy__sympy-13852

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c935e1d106743efd5bf0705fbeedbd18fadff4dc`, states the type
abstraction, and gives the provenance of each A-reference (the real callee the
deep/concrete model is validated against by G-AX).

Repo file under change: `sympy/functions/special/zeta_functions.py`.

The model.py spec view uses NEUTRAL identifiers (the dispatch is described
structurally — z-keyed clauses, distinguished-s special arguments, s-keyed
clauses — without naming the closed forms) to avoid leaking gold-internal
vocabulary not present in the public problem_statement. This file (the
construction-time audit, not a consumer artifact) binds those neutral
identifiers to their concrete repo counterparts.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recognize_closed_form(s, z_tag)` | `polylog.eval(cls, s, z)` — `sympy/functions/special/zeta_functions.py:273` (body 274-279) | the modeled changed function: the value-dispatch (auto-evaluation) of the special function |
| `series_expansion_at_one(s)` | the `s == 1` branch of `polylog._eval_expand_func` — `sympy/functions/special/zeta_functions.py:290` (branch 293-294) | the modeled changed function: the series-expansion at s = 1 |
| `closed_form_for(s, z_tag)` *(concrete `@Pure` map)* | the priority cascade of `polylog.eval` (the `if/elif` chain at lines 274-279 post-patch) | pure spec: WHICH closed-form code each recognised pattern produces; A-reference validated against the real `polylog` |
| `expansion_code(s)` *(concrete `@Pure` map)* | the `s == 1` return of `polylog._eval_expand_func` (line 294 post-patch) | pure spec: the s=1 expansion code; A-reference validated against the real `expand_func` |
| `CF_ZA / CF_ZB` (Z_A / Z_B clauses) | `zeta(s)` / `-dirichlet_eta(s)` (lines 275/277) | closed-form codes for the unchanged z = ±1 (z-keyed) clauses |
| `CF_ZC` (Z_C clause) | `S.Zero` (line 279 post-patch; pre-patch python `0`) | closed-form code for z = 0 |
| `CF_P1/CF_P2/CF_P3/CF_P4/CF_P5/CF_P6` (S_SPECIAL, Z_1..Z_6) | the six `s == 2` dilog returns (post-patch lines) | closed-form codes for the six s = 2 special arguments (z = 1/2, 2, and the four golden-ratio points) |
| `CF_SA / CF_SB` (S_KEY_A / S_KEY_B clauses) | `z/(1 - z)` / `z/(1 - z)**2` (post-patch) | closed-form codes for s = 0 / s = -1 |
| `CF_UNEVAL` | the implicit `None` fall-through (the call stays a `polylog` instance) | closed-form code for an unrecognised pattern |
| `EXP_PLAIN / EXP_POLAR` | `-log(1 - z)` (post-patch) / `-log(1 + exp_polar(-I*pi)*z)` (pre-patch) | the s = 1 expansion codes (fixed vs buggy) |

Neutral-name ↔ concrete-argument key (for the audit; the integer code VALUES are
identical to those used in `axiom_check.py`'s `gold_closed_form`):
`Z_A↔z==1`, `Z_B↔z==-1`, `Z_C↔z==0`; `S_SPECIAL↔s==2` with
`Z_1↔z==S.Half, Z_2↔z==2, Z_3↔z==-(sqrt5-1)/2, Z_4↔z==-(sqrt5+1)/2,
Z_5↔z==(3-sqrt5)/2, Z_6↔z==(sqrt5-1)/2`; `S_KEY_A↔s==0`, `S_KEY_B↔s==-1`;
`S_EXPAND↔s==1` (the expansion site).

The pre-patch repo state the change replaces (for the refinement audit, not
referenced from the consumer spec view): `polylog.eval` recognised only
`z == 1/-1/0` (returning the python int `0` for `z == 0`) and otherwise returned
`None`; `polylog._eval_expand_func` returned `-log(1 + exp_polar(-I*pi)*z)` at
`s == 1`. The patch also adds the imports `I` and `sqrt` (lines 1-12) — pure
import plumbing for the new closed forms, not a behavioural step.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `s` (a SymPy expression) | `int` | the dispatch branches only on the discrete predicates `s == 2` (`S_SPECIAL`), `s == 0` (`S_KEY_A`), `s == -1` (`S_KEY_B`) (else); the integer `s` realises exactly those (`s = 2 ↔ s == 2`, etc., any other int ↔ none). The s = 1 expansion site is the singleton `s == 1` (`S_EXPAND`). |
| `z` (a SymPy expression) | `int` tag `z_tag ∈ {0..9}` | `z` enters the dispatch only through the equality tests `z == 1, -1, 0, 1/2, 2, -(√5-1)/2, -(√5+1)/2, (3-√5)/2, (√5-1)/2`; `z_tag` is the finite quotient of `z` by those nine equalities (`Z_A…Z_6`), with `Z_OTHER = 0` for any `z` matching none. The dispatch is constant on each class, so the quotient is faithful. |
| the returned SymPy closed-form expression | `int` code (CF_*) / `int` code (EXP_*) | each code names one concrete gold closed form (see §1); the code abstraction is exact because `eval` / `_eval_expand_func` return exactly one of these per matched pattern. The mathematical identity of each named closed form with the real function is the A-reference (§3). |

SymPy expression arithmetic / symbolic equality is not expressible in Nagini's
fragment; the dispatch is therefore modelled at the level of its discrete
case-quotient, with the closed-form mathematics validated executably by G-AX.

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The changed operation is the
dispatch itself, modelled concretely; what must be validated against the real
callee is that each code names the mathematically-correct closed form, and that
the dispatch fires exactly on the recognised patterns.

### 3.1 The eval dispatch ↔ real `polylog.eval` (A-reference)
**Callee:** the gold-patched `polylog` auto-evaluation
(`sympy/functions/special/zeta_functions.py`, `polylog.eval`). `axiom_check.py`
runs the REAL `polylog(s, z)` and asserts:

- the six s = 2 special arguments evaluate to EXACTLY the gold dilog closed
  forms CF_P1…CF_P6 (symbolic equality for the two F2P symbolic assertions
  `polylog(2,2) == pi**2/4 - I*pi*log(2)`, `polylog(2,1/2) == pi**2/12 -
  log(2)**2/2`; high-precision numeric equality for all six, the F2P evalf loop);
- `polylog(s, 0) == S.Zero` (CF_ZC) for every s tried;
- `polylog(0, z) == z/(1-z)` (CF_SA) and `polylog(-1, z) == z/(1-z)**2` (CF_SB)
  over 80 random complex z (the F2P s ∈ {0,-1} numeric loop);
- the **priority cascade**: `polylog(0,1) == zeta(0)` (the z = 1 clause wins over
  the s = 0 rational, which would divide by zero), `polylog(0,0)/polylog(-1,0) ==
  0`;
- the dispatch does **not over-fire**: at unrecognised patterns (`s = 2, z = 1/3`;
  `s = 3, z = 1/2`; `s = 2, z = 7/5`) the real `polylog(s,z)` stays a `polylog`
  instance (unevaluated).

Numerical ground truth (mpmath, dps 30, independently confirmed during
construction): all six s = 2 closed forms agree with `mpmath.polylog(2, z)` to
< 1e-31; `polylog(0,z)=z/(1-z)`, `polylog(-1,z)=z/(1-z)**2`, `polylog(1,z)=
-log(1-z)` agree to machine precision over random complex z.

### 3.2 The s = 1 expansion ↔ real `expand_func(polylog(1, z))` (A-reference)
**Callee:** the gold-patched `polylog._eval_expand_func` at `s == 1`, exercised
via `expand_func`. `axiom_check.py` asserts `expand_func(polylog(1, z)) ==
-log(1 - z)` (EXP_PLAIN) and that the result is FREE of `exp_polar`
(`not e.has(exp_polar)`), plus high-precision numeric agreement of
`polylog(1, z)` with `-log(1 - z)` over 40 random complex z. The pre-patch form
`-log(1 + exp_polar(-I*pi)*z)` (EXP_POLAR) carries the spurious polar factor
the issue removes.

**Soundness check (G-AX) — patch-applied execution.** `axiom_check.py` imports
only `sympy` (the library under change) and runs in-container on the eval image
(Python 3.6). The eval image ships the **PRE-patch** sympy at `base_commit`, so
the script **applies `patch.diff` to /testbed itself** (idempotently — it skips
re-applying if the gold patch is already applied, e.g. when the runner passes
`apply_gold=True`) BEFORE importing sympy, so it validates the model against the
REAL gold-patched callee. It then enumerates every `test_polylog_values` F2P
assertion plus the priority/over-fire/boundary cases. It gracefully SKIPs
(exit 0, loud message) only if sympy is not importable; on the eval image it
applies the patch and executes the real callee. Exit 0 iff every observation
matches the model.

Verified in-container (eval image, py3.6, gold-patched sympy 1.1):
- `apply_gold=False` (runner does not pre-apply): script self-applies, **RC=0**
  ("applied gold patch.diff to /testbed").
- `apply_gold=True` (runner pre-applies): script detects already-applied,
  skips, **RC=0**.
- discrimination control: a deliberately WRONG code↔closed-form binding (CF_P1↔
  CF_P2 swap) makes the check **FAIL** loudly ("does NOT equal gold closed
  form"), confirming the A-reference is discriminating, not vacuous.
