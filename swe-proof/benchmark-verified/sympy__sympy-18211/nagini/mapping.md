# mapping.md — sympy__sympy-18211

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b4f1aa3540fe68d078d76e78ba59d022dd6df39f`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/core/relational.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `solution_set_of_relation(rel)` | `Relational._eval_as_set(self)` — `sympy/core/relational.py:389` | the modeled changed method (turns a univariate relation into its real solution set) |
| `solve_univariate(rel)` *(axiom — A-consumed)* | `solve_univariate_inequality(expr, gen, relational=False)` — `sympy/solvers/inequalities.py:397` (called in `_eval_as_set` at `relational.py:395`) | unchanged solver callee the method invokes; partial — returns a `Set` or raises `NotImplementedError` |
| `solved_cond(rel)` *(axiom — A-consumed)* | the `Set` object `solve_univariate_inequality(...)` returns on a determined relation — `sympy/solvers/inequalities.py:397` (return value) | pure accessor pinning the determined-branch result to the solver's own returned set (condition field) |
| `solved_sym(rel)` *(axiom — A-consumed)* | the same solver-returned `Set` viewed through the model's `sym` field | pure accessor (value abstract) pinning the determined-branch result's `sym` field to the solver's own returned set |
| `solved_reals(rel)` *(axiom — A-consumed)* | the same solver-returned `Set` viewed through the model's `over_reals` field | pure accessor (value abstract) pinning the determined-branch result's `over_reals` field to the solver's own returned set |
| `SolverUndecided` (exception class) | `NotImplementedError` raised by `solve_univariate_inequality` — `sympy/solvers/inequalities.py:531,561,587,593,595,820,911,986` (and via `solvify`) | the solver's undecidability signal; user-defined stand-in (builtin-exception `Exsures` crashes the translator) |
| `SolutionSet` (class) | `sympy.sets.Set` (its subclasses `Interval`/`Union`/`FiniteSet`/`EmptySet`/… for a solver result, and `ConditionSet` for the fallback) | the conversion's return value, modeled by only the observable fields |
| `Relation` (class) | `self` — a `Relational` (e.g. `Equality`) — `sympy/core/relational.py:18` | the relation under conversion, modeled by only the observable fields |
| `SolutionSet(True, rel.token, x, True)` (fallback construction) | `ConditionSet(x, self, S.Reals)` — built in the patched `except` branch, `sympy/core/relational.py:393-403` post-patch; `ConditionSet.__new__(cls, sym, condition, base_set)` at `sympy/sets/conditionset.py:117` | the symbolic fallback set returned when the solver is undecided |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `_eval_as_set` returned
`solve_univariate_inequality(self, x, relational=False)` directly, with no
handler — so the solver's `NotImplementedError` propagated to the caller of
`as_set()` (`relational.py:395` pre-patch). The patch wraps the call in
`try/except NotImplementedError` and, on the exception, returns
`ConditionSet(x, self, S.Reals)` (`relational.py:392-403` post-patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self` (a `Relational`) | `Relation` object with fields `n_free`, `token`, `sym`, `solvability` | `len(self.free_symbols)` ↔ `rel.n_free`; the identity of `self` (passed as the `ConditionSet` condition) ↔ `rel.token`; the popped free symbol `x` ↔ `rel.sym`; "solver determines vs. is undecided about this relation" ↔ `rel.solvability ∈ {0,1}`. The relation's algebraic structure is NOT modelled: the only observable of the pinned behaviour is WHICH set the conversion produces, which is a function of the solver's determined/undecided verdict. |
| `self.free_symbols` + `assert len(syms) == 1` + `x = syms.pop()` | `rel.n_free == 1` precondition; `x = rel.sym` | the univariate precondition (`_eval_as_set`'s own `assert len(syms) == 1`, `relational.py:393`) and the single-variable pop are modeled by the `n_free == 1` Requires and the `sym` accessor. |
| solver result `Set` (`Interval`/`Union`/`FiniteSet`/`EmptySet`/`UniversalSet`/…) | `SolutionSet` with `is_fallback == False`, `cond == solved_cond(rel)` | a genuine solver-produced solution set is never the symbolic fallback; its identity is pinned to the solver's own returned token. The set's element-membership content is unobserved by the conversion's totality behaviour. |
| `ConditionSet(x, self, S.Reals)` | `SolutionSet(is_fallback=True, cond=rel.token, sym=rel.sym, over_reals=True)` | the fallback set's three arguments: bound symbol `x` ↔ `sym`, condition `self` ↔ `cond == rel.token`, base set `S.Reals` ↔ `over_reals == True`. `ConditionSet.__new__(cls, sym, condition, base_set)` (`conditionset.py:117`) so the positional order is (symbol, condition, base). |
| `NotImplementedError` (raised by the solver) | `SolverUndecided` user-defined exception | a builtin exception in an `Exsures` crashes the Nagini translator; the solver's undecidability signal is modeled by a user-defined class. The solver raises it on relations `solvify`/`solve_univariate_inequality` cannot decide (`inequalities.py` docstring "Raises NotImplementedError", lines 531/561/587/593/595/820/911/986). |

The relation's symbolic contents are not indexable/expressible in Nagini's
fragment; collapsing the relation to its observable fields (free-variable count,
identity token, variable token, solver verdict) is faithful because the pinned
behaviour is the totality of the conversion — WHICH set is returned — not the
algebraic form of the relation.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `solve_univariate` ↔ `solve_univariate_inequality(..., relational=False)` (A-consumed)
**Callee:** `sympy.solvers.inequalities.solve_univariate_inequality(expr, gen,
relational=True, domain=S.Reals, continuous=False)` — `inequalities.py:397`.
`_eval_as_set` calls it with `relational=False` (`relational.py:395`), so the
result, when determined, is a `Set` (not a `Relational`).

The function is **partial**. Its own docstring (lines 415-420) states:

> Raises
> ======
> NotImplementedError
>     The solution of the inequality cannot be determined due to limitation
>     in :func:`sympy.solvers.solveset.solvify`.

The function is partial in TWO senses. First, on many univariate relations it
either returns a `Set` (the solution set) OR raises `NotImplementedError`
(the undecidability signal documented above). Second — and this is the stated
domain carve-out the axiom relies on — on OTHER univariate relations it reports a
DIFFERENT outcome entirely: a domain error (`ValueError`, e.g.
`sign(x) > 0`, `Eq(log(x), 0)` → "Inequalities in the complex domain are not
supported" / "contains imaginary parts"), a malformed-argument error
(`TypeError`, e.g. `cbrt(x) > 0`), a recursion-bound exhaustion (`RecursionError`,
e.g. `Eq(Min(1, x), 0)`, `Max(0, x) > 1`), or non-termination (e.g.
`2*x**(1/3) + 3*x**2 - 3 <= 0`). The gold patch catches ONLY
`NotImplementedError`, so on these other-outcome relations the patched
`_eval_as_set` ALSO raises/hangs — it does not resolve them to a fallback set.
(Reproduced in the pinned eval container; see axiom_check.py's third probe.)

**Stated domain carve-out (Directive 7 soundness).** The integer `solvability`
tag is a TOTAL function only over the first family — the relations on which the
solver returns a `Set` or raises `NotImplementedError`. It has NO value for the
other-outcome relations, so no `Relation` carrier can be built for them:
`solvability ∈ {0,1}` has no preimage there, and the precondition
`solvability == 0 or solvability == 1` admits ONLY the return/NotImplementedError
relations. The axiom therefore encodes EXACTLY this dichotomy over its stated
domain:

  * `solvability == 0` (determined) → returns normally a `SolutionSet` with
    `is_fallback == False` (a genuine solution set is never the `ConditionSet`
    fallback the conversion fabricates) and `cond == solved_cond(rel)` (pinned to
    the solver's own returned set);
  * `solvability == 1` (undecided) → raises `SolverUndecided`
    (`NotImplementedError`).

The axiom is the **weakest** contract the conversion's totality postcondition
needs over its stated domain: which verdict (return vs. raise-NotImplementedError)
the solver gives, plus the determined-result pin. It does NOT claim anything
about the solution set's membership content — only that a determined result is
not the fabricated fallback and is the solver's own set. Crucially, it does NOT
claim the solver is total (raise-free / terminating) over ALL univariate
relations: the other-outcome relations are carved out of the modeled domain by
construction, exactly mirroring the gold patch's `except NotImplementedError`
(which lets every other outcome escape). **(Directive 7: NOT stronger than the
real callee — over the stated two-way domain the callee genuinely returns a Set
or raises `NotImplementedError`, which the F2P test exercises with
`Eq(x*cos(x) - 3*sin(x), 0)`; the callee's other failure outcomes are not
asserted away, they simply have no carrier in the abstraction, so a verifying
impl makes no claim on them and the conversion behaves identically to the gold
patch — both raise/hang — on those out-of-domain inputs.)**

This is why a no-`Exsures` (totality) postcondition on `solution_set_of_relation`
is sound despite wrapping a partial callee: totality is conditional on the
stated `solvability ∈ {0,1}` precondition, which provably excludes every
non-`NotImplementedError` failure mode — not on implicit test coverage. (SPEC_GUIDE
directive 7's totality-of-a-partial-callee trap, handled by a stated `Requires`
mechanism per the verdict's fix option A.)

### 3.2 `solved_cond` / `solved_sym` / `solved_reals` ↔ the solver's returned `Set` (A-consumed)
**Callee:** the same `solve_univariate_inequality(...)` viewed as a value
accessor: its returned `Set` on a determined relation (`inequalities.py:397`
return value), projected onto each of the model's three data fields (`cond`,
`sym`, `over_reals`). Each accessor is `Requires(rel.solvability == 0)`,
`Ensures(True)` (value abstract). Together they pin the conversion's
determined-branch result FIELD-FOR-FIELD
(`Result().cond == solved_cond(rel)`, `Result().sym == solved_sym(rel)`,
`Result().over_reals == solved_reals(rel)`) to the solver's own returned set, so
a wrong impl cannot fabricate ANY modelled field of the determined result — not
just the condition token (closes the spec-too-weak hole the panel hunts for,
symmetric with django-13023's `accepted_value`). Only identities are claimed;
nothing about membership, so the axioms never over-claim: the real solver
deterministically returns ONE `Set` per determined relation, and each accessor
merely names one modelled projection of that returned object.

The fallback set `ConditionSet(x, self, S.Reals)` is built directly in the
patched `except` branch (`relational.py:393-403` post-patch). It is NOT the
solver callee — it is the conversion's own construction — so it is modeled
DIRECTLY by `SolutionSet(True, rel.token, x, True)` in the impl, not by an axiom.
`ConditionSet.__new__(cls, sym, condition, base_set=S.UniversalSet)`
(`conditionset.py:117`); the patch passes `(x, self, S.Reals)`, i.e. bound
symbol `x`, condition `self`, base set the whole real line `S.Reals`. Docs:
https://docs.sympy.org/latest/modules/sets.html#sympy.sets.conditionset.ConditionSet

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`solve_univariate_inequality(self, x, relational=False)` under a per-call
wall-clock timeout (non-termination is treated as an out-of-domain outcome, not
a hang) on:

  (a) the two F2P relations `Eq(x*cos(x) - 3*sin(x), 0)` and
      `Eq(x**2 + sqrt(x*2) + sin(x), 0)` (which must raise `NotImplementedError`
      → `solvability == 1`);
  (b) a battery of solvable univariate relations (polynomials, simple
      inequalities, equalities) that must return a `Set` and NOT raise
      (→ `solvability == 0`);
  (c) **the broader relation families the verdict identified** — transcendental,
      rational/root (`cbrt`), `sign`, `log`/`log∘log`, `Min`/`Max`, `floor`,
      `Piecewise`, and `Abs` relations — exercising the solver's OTHER failure
      modes (`ValueError`/`TypeError`/`RecursionError`/non-termination). These are
      the OUT-OF-DOMAIN family: they have no `solvability` value, so the check
      asserts NOTHING about their result; it CLASSIFIES each as in-domain
      (returned a Set ⇒ 0, or raised `NotImplementedError` ⇒ 1) or domain-excluded
      (any other exception / timeout) and confirms the domain carve-out is
      well-defined and non-empty;
  (d) a randomized fuzz spanning all the above families.

For every relation it classifies the real outcome and asserts the axiom ONLY
over the in-domain ones: undecided ⇒ raised `NotImplementedError`; determined ⇒
returned an `sympy.sets.Set` instance, did NOT raise, and is never a
`ConditionSet` wrapping the original relation over `S.Reals` (i.e. the solver
does not itself return the fallback — the fallback is genuinely the conversion's
own construction). A relation whose real outcome is any OTHER exception or a
timeout is recorded as DOMAIN-EXCLUDED (no `solvability` carrier) — which is
SOUND, not a failure, because the abstraction makes no claim there (this is the
stated carve-out above). The check FAILS only if a relation the axiom would tag
in-domain disobeys the determined/undecided dichotomy. Imports only `sympy` (the
library under test). Exit 0 iff sound; it reports the per-family counts so the
domain boundary is auditable.

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow.** The `# impl-start` / `# impl-end` region of
`solution_set_of_relation`, copied VERBATIM with only the contract call
`Assert(syms == 1)` deleted (no other contract call lives inside the impl
region), plus the `SolutionSet` / `Relation` constructor impl regions verbatim
minus their `Requires`/`Ensures`. No transliteration and no restructuring: the
model IS Python, so the shadow is the model's own code.

**Axiom callee, exercised not assumed.** The `@ContractOnly` `solve_univariate`
has no body to copy, so the shadow calls the REAL callee it axiomatizes,
`solve_univariate_inequality(self, x, relational=False)`
(`sympy/solvers/inequalities.py:397`, §1/§3.1). Its return leg is driven by the
real returned `Set` and its `Exsures` leg by the real `NotImplementedError`. The
spec-only accessors `solved_cond` / `solved_sym` / `solved_reals` appear in no
impl region; the bridge below realizes their abstract values as deterministic
projections of the solver's own returned set.

**Oracle.** The REAL gold-patched `Relational._eval_as_set(self)`
(`sympy/core/relational.py:389`), **called** — not transliterated. The gate
applies `patch.diff` to /testbed and sets `PYTHONPATH` before the script runs;
the script never applies a patch itself. Driving the oracle needs only a
univariate sympy `Relational`, which is buildable in-container, so the velvet
sibling's transliteration caveat does not apply here.

**Type bridge (§2, inverted).** Generation runs concrete → abstract, so every
generated input satisfies the `Requires` by construction: a real univariate
relation `rel` with popped free symbol `x` becomes
`Relation(n_free=len(rel.free_symbols), token=tok(rel), sym=tok(x),
solvability=the real solver's verdict on rel)`, where `tok` is a deterministic
injective interning table over `srepr` (token equality ≡ structural equality).
Results are abstracted on BOTH sides by the same `alpha`: a `ConditionSet` →
`SolutionSet(True, tok(.condition), tok(.sym), .base_set == S.Reals)`; any other
`Set` S → `SolutionSet(False, tok(S), tok(x), S == S.Reals)` — so the determined
leg's comparison is as strong as full structural equality of the returned set.

**Domain carve-out (§3.1) is enforced, not assumed.** Each candidate relation is
classified by running the real solver under a 10 s per-call wall-clock budget. A
relation whose real outcome is anything other than `Set` / `NotImplementedError`
(`ValueError` / `TypeError` / `RecursionError` / non-termination) has no
`solvability` value and hence no `Relation` carrier, so no input is built for it;
the count is reported in the structured summary rather than silently dropped.

**Inputs.** The ABSTRACT input space is finite and tiny — `n_free == 1` is forced
and `solvability ∈ {0,1}`, i.e. exactly the two impl branches — so both abstract
shapes are enumerated exhaustively, and each is lowered to many distinct concrete
relations (the tokens are what the fallback branch actually moves, so that is
where the fidelity risk lives). Boundary first: the F2P relation of issue 18188
`Eq(x*cos(x) - 3*sin(x), 0)` and its companion `Eq(x**2 + sqrt(x*2) + sin(x), 0)`;
the P2P `test_univariate_relational_as_set` relations; the degenerate empty /
singleton / whole-line determined sets (`Eq(x**2 + 1, 0)`, `x**2 + 1 > 0` — the
only determined case driving `over_reals == True`); then seeded fuzz over bounded
families (polynomials deg 1–3 × all six relation constructors, `x·f(x) − k·g(x)`
trig, the F2P `x**2 + sqrt(k·x) + sin(x)` shape, exp, Abs). Real observations are
memoized per distinct relation (both callees are pure deterministic functions of
the relation); every generated input is still individually pushed through the
full shadow and individually diffed.

**Count / seed.** 100 000 inputs over 332 distinct in-domain relations (182
determined / 150 undecided), 14 non-univariate candidates rejected.
**Pinned fuzz seed: `SEED = 182110`** (module constant).

**Anti-vacuity control.** The run FAILS if either impl branch is never taken, and
an escaping `SolverUndecided` is reported as a totality disagreement rather than
crashing — a green run that never took the branch the gold patch adds would
certify nothing. Verified capable of failing: three mutated shadows (fallback
`over_reals=False`; fallback `cond` = the symbol instead of the relation; the
pre-patch shape that lets the undecided signal propagate) each exit 1 with a
printed counterexample, while the verbatim shadow exits 0.
