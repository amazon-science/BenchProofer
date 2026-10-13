# refinement.md — sympy__sympy-19040

Maps every op in `implementation_extFactor` to its `patch.diff` / base-source
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses a callee
axiom), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op).

The gold patch changes exactly one data-flow edge: the argument fed to the
square-free-norm step changes from the square-free part `f` to the full monic
original `F`. Every operation in the impl is an UNCHANGED opaque algebra callee;
the modeled behaviour is the routing of values among them. There is therefore no
R/I concrete Lean computation to differential-test (conf_skip = true), and no
consumed callee property (no shipped axiom).

| Lean op (impl) | patch.diff / base counterpart | tag | note |
|---|---|---|---|
| `let lc := groundLC f` | `lc = dmp_ground_LC(f, u, K)` (1143) | A-reference | opaque carrier identical in spec+impl; unchanged callee |
| `let mono := groundMonic f` | `f = dmp_ground_monic(f, u, K)` (1144) | A-reference | the monic original = `F` in the source |
| `if degreesNonpos (degreeList mono)` | `if all(d <= 0 for d in dmp_degree_list(f, u))` (1146) | A-reference + R | `degreeList` opaque callee; `degreesNonpos` = `all(d<=0)` pure refinement (R) |
| `return (lc, [])` | `return lc, []` (1147) | I | trivial-degree short circuit |
| `let fSqf := sqfPart mono` | `f, F = dmp_sqf_part(f,u,K), f` (1149) | A-reference | `fSqf` = post-patch local `f`; `mono` = `F` |
| `let (s,g,r) := sqfNorm mono` | `s, g, r = dmp_sqf_norm(F, u, K)` (**1150, the fix**) | A-reference | THE rerouted edge: argument is `mono`(=`F`), not `fSqf` |
| `let factors0 := factorListInclude r` | `factors = dmp_factor_list_include(r, u, K.dom)` (1152) | A-reference | unchanged callee |
| `if factors0.length = 1 then factors := [fSqf]` | `if len(factors)==1: factors=[f]` (1154-1155) | I | single-factor branch returns the square-free part |
| `let H := raiseShift s` | `H = dmp_raise([K.one, s*K.unit], u, 0, K)` (1157) | A-reference | unchanged callee |
| `for entry in factors0 do … recoverOne H gCur entry.1` | the `for i,(factor,_) in enumerate(factors)` body: `dmp_convert`∘`dmp_inner_gcd`∘`dmp_compose` (1159-1163) | A-reference | one opaque recovery step per ground factor, threading `g` |
| `factors := factors ++ [h]` | `factors[i] = h` | I | accumulate recovered factors in order |
| `trialDivision mono factors` | `dmp_trial_division(F, factors, u, K)` (1165) | A-reference | unchanged callee; divides against `F`(=`mono`) |

## Why no consumed axiom
The `correct_extFactor` obligation is: the impl's result equals the spec's
right-hand side. The spec is written as the SAME data flow the impl performs
(same opaque callees in the same order). The only non-definitional step is the
`for`-loop ↔ `recoverLoop` front-recursive fold (PROOF_PLAYBOOK Route B,
`List.forIn_cons`, generalizing the gcd accumulator) — a list-shape induction
that consumes NO property of any opaque callee. Hence no `axiom _prop` is shipped;
`axiom_check.py` is a skip stub.

## Why conf_skip
Every impl row is A-reference or I-over-opaque-carriers. There is no R/I leg that
computes a concrete observable value in Lean independently of the real callees,
so the cross-language differential test (G-CONF) has nothing to compare. The
behavioural equivalence of the spec's data routing to the gold patch is carried
by patch.diff (gold verbatim, G-RESOLVE/G-GOLD) and the impl↔patch op
correspondence above (G-EQ). conf_skip = true.
