# Relaxed-leakage disposition — sympy__sympy-18199

This bundle takes the **relaxed-leakage** disposition (see
`RELAXED_LEAKAGE.md`). The spec view discloses the gold's tested
discriminator — the behaviour of `nth_roots` for a **non-prime (composite)
modulus** — because this instance is a genuine `problem_statement` ↔ gold
MISMATCH and a *faithful* spec cannot avoid naming it. The mechanical G-LEAK
lexical screen still passes (no diff line, no patched symbol —
`nthroot_mod` / `_nthroot_mod_composite` / `isprime` / `is_nthpow_residue` /
`cartes` — appears in any identifier, docstring, or comment of the spec view);
the residual leak is semantic (the composite *behaviour itself*), not token
level.

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text` or the hidden `test_patch`.

**What the `problem_statement` actually says.** The public issue is titled
"`nthroot_mod` function misses one root of `x = 0 mod p`" and reads, in full:

> When in the equation `x**n = a mod p`, when `a % p == 0`. Then `x = 0 mod p`
> is also a root of this equation. But right now `nthroot_mod` does not check for
> this condition. `nthroot_mod(17*17, 5, 17)` has a root `0 mod 17`. But it does
> not return it.

The issue is **exclusively about the zero-root case** (`a % p == 0`, with the
worked example `nthroot_mod(17*17, 5, 17)` — note 17 is **prime**). It says
nothing about composite moduli, prime-power factorisation, or the pre-patch
`NotImplementedError("Not implemented for composite p")` guard. The
`hints_text` is a single non-technical line ("I will submit a pr regarding
this.") and discloses nothing.

**What the gold patch actually does, and what the F2P test exercises.** The gold
reorders the `n > 2` dispatch and adds *two* independently-observable fixes:
  1. the zero-root special case `if a % p == 0: return [0]` (the public issue);
  2. a **composite-modulus solver** — the pre-patch code *raised*
     `NotImplementedError` for non-prime `p`; the gold instead returns the real
     root set.

The single FAIL_TO_PASS test is `test_solve_modular`. It reaches the changed
function via `solveset` → `_invert_modular` →
`nthroot_mod(rhs, expo, m, all_roots=True)` with the **composite** moduli
`m = 8` (`solveset(Mod(x**3, 8) - 1)` → `{1}`) and `m = 9`
(`solveset(Mod(x**4, 9) - 4)` → `{4, 5}`). Both are non-prime. The zero-root
fix alone does NOT make `test_solve_modular` pass — without the composite path
the call raises and the test errors. So the **only F2P discriminator is the
composite-modulus behaviour**, which is entirely absent from the
`problem_statement`.

**The mismatch.** A spec that is *faithful* (pins the gold's actually-tested
behaviour, so the prepatch fails — G-DIFF — and no wrong impl verifies — G-EQ)
MUST state the composite-modulus result (the F2P discriminator). A spec
restricted to the `problem_statement` surface (the prime zero-root case only)
cannot pin the F2P behaviour at all: the public issue and the F2P-tested fix are
about different moduli classes. Hence **faithful + non-leaking is provably
impossible** here — not lazy de-narration, but a true PS↔gold mismatch.

**De-narration still performed (no mechanism leak).** Even under the
relaxation, the docstring was de-narrated from a bug→fix story to an abstract
behavioural contract. Removed: "assembled per prime-power factor and
recombined" (the CRT *mechanism*), "rather than declining the input" (the
pre-patch raise *diagnosis*), and "recognised before the residue machinery,
which otherwise omits the zero solution" (the dispatch-*reorder* narration). The
spec view now states only the abstract behaviour: "When `p` is not prime the
result is the full set of in-range roots for that modulus." The relaxation
licenses disclosing the composite *behaviour* (forced by the F2P); it does not
license narrating the CRT mechanism, the raise it replaces, or the reorder.

## The input domain: why the `composite_validated` enumeration is forced

The facet dispositioned above is the composite *behaviour*. The relaxation also
covers a second, more concrete facet, and because it is the one a reader is
likeliest to challenge it is dispositioned here explicitly rather than left
implicit: the regime predicate `composite_validated` (`model.py:147-164`)
enumerates SIX `(a, n, p)` triples as integer literals (`model.py:159-164`),
and two of those triples are inputs the graded test reaches. They are genuinely
consumer-visible: the helper sits inside the `pure` region and the projection
elides only `impl` regions (`_python_spec_view`,
`src/swebench_unified/markers.py:201-226`), so running the real projection
(`markers.spec_view` over this bundle's `model.py`) returns all six triples
verbatim. The predicate is consumed by the domain
`Requires` at `model.py:207` and guards the composite `Ensures` at
`model.py:218`.

**Two of the six are graded; four are not.** The frozen benchmark row
(`data/swe_bench_verified/test.jsonl`) records `FAIL_TO_PASS` as
`['test_solve_modular']` plus 113 `PASS_TO_PASS` entries, not one of which is an
ntheory residue test. Instrumenting the real `nthroot_mod` on a gold-patched
worktree at `base_commit ba80d1e493` and running that graded test, the only
calls reaching the modelled tail (`n > 2`) with a non-prime modulus are
`(1, 3, 8)`, from `solveset(Mod(x**3, 8) - 1)`, and `(4, 4, 9)`, from
`solveset(Mod(x**4, 9) - 4)`; the test's one other non-prime modulus,
`(9, 2, 160)`, has `n == 2` and returns through the unchanged `sqrt_mod` front,
outside this spec's domain. The remaining four triples -- `(16, 5, 36)`,
`(9, 16, 36)`, `(4, 3, 3249000)`, `(0, 7, 100)` -- occur only in
`test_residue`, which is in NEITHER the F2P nor the P2P list, so the harness
never scores them; and two of those four are already in that test file at
`base_commit`, in its pre-patch `raises(NotImplementedError, ...)` lines
(`nthroot_mod(16, 5, 36)` and `nthroot_mod(9, 16, 36)`). So the enumeration is
not a copy of the graded test's input set: it is a modulus regime that happens
to cover it.

**The regime cannot be narrowed.** `8 == 2**3` and `9 == 3**2` are both
non-squarefree, so narrowing `composite_validated` to `is_squarefree(p)` alone
drops exactly the two graded triples, and the spec would then claim nothing at
all on the graded inputs. That weakening is measured, not hypothetical. The
velvet twin measured the verifier half: with the regime narrowed that way, a
rival that declines every non-squarefree modulus VERIFIES (exit 0)
(`../velvet/verdict.md:692`, item (4) of its G-PANEL-3 account, recorded also in
`../velvet/meta.json` under `gates."G-PANEL-3".note`). The implementation half
is re-measured for this file: on a copy of a gold-patched worktree at
`base_commit ba80d1e493` with the frozen `test_patch` applied, gold PASSES
`test_solve_modular`, while the same routine guarded to decline any modulus with
a repeated prime factor FAILS it. A narrowed regime therefore admits a verifying
implementation that loses the graded test, which is the spec-too-weak defect
(G-EQ / G-DIFF) the enumeration exists to prevent.

**The regime cannot be widened either.** Outside it the reference routine is
only partially correct, so a wider regime would make the completeness claim
false of the gold patch itself. Measured on the same gold worktree over every
non-squarefree modulus `4 <= p < 120` with `3 <= n < 9` and `0 <= a < p`, the
six enumerated triples excluded (15,836 triples): the real
`nthroot_mod(a, n, p, True)` disagrees with the complete in-range root set on
1038 of them, and on every one of the 1038 it both returns a non-root and drops
a real root. Two witnesses, the pair this bundle's own G-PANEL-2 role records
(`verdict.md:996`): `nthroot_mod(379, 3, 8, True)` returns `[5]`, but
`379 == 3 (mod 8)` while `5**3 == 5 (mod 8)`, so 5 is not a root of that
congruence at all (its only root is 3); and `nthroot_mod(253, 3, 16, True)`
returns `[1]`, but `253 == 13 (mod 16)` and its only root is 5. The velvet
twin's independent sweep over the same bounds reached the same count of 1038
(`../velvet/verdict.md:694`, item (5)). Inside the regime the equality is exact:
every enumerated triple equals the brute-force complete root set --
`(1, 3, 8)` -> `[1]`, `(4, 4, 9)` -> `[4, 5]`, `(16, 5, 36)` -> `[4, 22]`,
`(9, 16, 36)` -> `[3, 9, 15, 21, 27, 33]`, `(0, 7, 100)` ->
`[0, 10, ..., 90]`, and `(4, 3, 3249000)` -> `[]` by enumeration of all
3,249,000 residues.

The six-element set is therefore the largest sound regime and the smallest
faithful one: widening is unsound against the reference, narrowing loses the
F2P discriminator. The enumeration is forced, not chosen.

**What the literals disclose is the DOMAIN of the claim, not its answer.**
`composite_validated` appears only in `Requires` (`model.py:184`,
`model.py:207`) and as the guard of the composite `Ensures` (`model.py:218`);
the result stays pinned to `roots_below` / `composite_roots`, the structural
fold over the real modular exponentiation, never to the predicate. The six
literals therefore say WHERE the specification claims something, not WHAT it
claims there. What it claims there is the facet this file already admits above,
"the full set of in-range roots for that modulus", and an implementation that
simply searches the residues of the modulus needs none of these literals: it
makes no per-modulus case distinction, and it meets the spec on the two graded
triples for the same reason it meets it everywhere else in the domain. Reading
the enumeration buys reach into the regime, not a shortcut to the answer.

**One lexical excess, recorded rather than repaired.** The prose around the
predicate labels its domain with the words "test-suite triples"
(`model.py:151-153`) and "the enumerated test-suite moduli" (`model.py:204`),
and the projection carries both wordings into the spec view. That describes the
values by where they were first written down instead of by the property that
admits them (the reference routine is exact on them), and for four of the six it
was not the graded test that wrote them down. The excess is in the wording only:
the domain those words describe is spelled out immediately below them as integer
literals, so the words add nothing a reader does not already have from the
enumeration itself. It is left uncorrected deliberately. The spec view is the
attack-admissibility key -- `spec_signature` is the spec view minus blank lines
(`src/swebench_unified/markers.py:326-331`), an attack whose spec view differs
is rejected as not-same-spec (`check_attack`,
`src/swebench_unified/adversary.py:134-135`), and the two prepatch twins are
admitted through that same check (`src/swebench_unified/gates/diff.py:31`). Re-wording either line is thus not
free: replacing "test-suite triples" with "enumerated triples" and changing
nothing else moves the spec signature from `ec19f6def439835a` (the shipped
`model.py`) to `72118b80122c4869` and makes `same_spec` False against every
retained attack in this cell, forcing a full re-audit to buy a synonym. This
file records the wording; the specification stays byte-frozen.

## Requirements satisfied (RELAXED_LEAKAGE.md §"Requirements")

1. **Core is sound.** G-VERIFY pass (model.py verifies, ~59s, <300s, no flags);
   G-DIFF fail (both `model_prepatch.py` and `model_prepatch_1.py` are
   `same_spec True` and fail exactly their discriminating postconditions — the
   `[0]` zero-root singleton, and the guarded composite-root-set equality on the
   F2P input `(1, 3, 8)` respectively); G-EQ sound/tight (every refinement step
   R / A-consumed / A-reference / I, no kind-3; the result is pinned to the
   grounded root-set references `prime_roots` / `composite_roots` and the
   structural `is_root` predicate over the real modular exponentiation, never to
   an opaque answer-key oracle — directive 8); G-AX sound (axiom_check.py exits
   RC=0 in the pinned eval container with the gold applied; `composite_roots`'s
   soundness Ensures is scoped to its validated regime via `composite_validated`,
   and the regime predicate is validated both faithful — exact inside — and
   load-bearing — the gold returns non-roots outside it); G-RESOLVE:
   `patch.diff` == gold verbatim, applies cleanly at `base_commit`.
2. **The leak is genuinely unavoidable**, established above: the composite-
   modulus discriminator (the only F2P discriminator) is demonstrably absent
   from the `problem_statement` (which is exclusively the prime zero-root case),
   and no PS-derivable reformulation models the F2P fix. The second facet, the
   enumerated input domain of `composite_validated`, is unavoidable on the same
   footing and for measured reasons: see §"The input domain: why the
   `composite_validated` enumeration is forced" (it cannot be narrowed without
   admitting a verifying implementation that loses the graded test, and it
   cannot be widened without claiming behaviour the gold patch does not have).
3. **Documented in-bundle.** This file; `meta.json` records
   `gates.G-LEAK.status = "relaxed"` with a pointer here.

`verify ⟹ correct` is unaffected; only the secondary no-leakage property is
relaxed, for this documented PS↔gold mismatch.
