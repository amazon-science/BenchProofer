# mapping.md — sympy__sympy-16597

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6fd65310fa3167b9626c38a5487e171ca407d988`, states the type
abstraction, and gives the provenance of the deep-model reference (the
property-deduction engine) the model is validated against.

Repo subsystem under change: `sympy/core/assumptions.py` (the rule source
`_assume_rules`), its compiled mirror `sympy/assumptions/ask_generated.py`, and
the runtime closure `sympy/core/facts.py` (`FactRules.deduce_all_facts`, the
forward-chaining engine those rules compile into).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `KB` (record of `Option Bool` facts) | the `StdFactKB` / `FactKB` knowledge base populated for a `Basic` object (`sympy/core/assumptions.py:208` `StdFactKB`; `sympy/core/facts.py:473` `FactKB(dict)`); each field ↔ one `is_<fact>` entry | a deduced three-valued fact table for one quantity |
| `consistentTheory k` *(deep model — A-reference)* | the implication rule set `_assume_rules = FactRules([...])` (`sympy/core/assumptions.py:163-201`) as realized by the forward-chaining closure `FactKB.deduce_all_facts` (`sympy/core/facts.py:501-537`) | pure spec: the fact table is closed under the containment relations |
| `implementation_deduceEven` / `problem_spec_deduceEven` / `correct_deduceEven` | the deduction made when a `Symbol('x', even=True)` is queried — `make_property` / `_ask` driving `deduce_all_facts` from the seed `even=True` (`sympy/core/assumptions.py:238-310`) | the closure of the seed `even=True` |
| `implementation_deduceInfinite` / `problem_spec_deduceInfinite` / `correct_deduceInfinite` | the deduction made for an unbounded real quantity such as `S.Infinity` / `S.NegativeInfinity` (`infinite=True, real=True, …`), the same engine driven from that seed | the closure of an unbounded-real seed |

The behavioural delta is in the **rule data**, not the engine: the consequent of
each "small-set" membership (`rational`, `algebraic`, `transcendental`,
`irrational`) gains a boundedness conjunct, and the compiled CNF / dict mirrors
are regenerated. The runtime closure is unchanged; it simply propagates the new
edges (and their automatically-derived contrapositives).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a fact value `True` / `False` / `None` (the three-valued result of `is_<fact>`) | `Option Bool` field (`some true` / `some false` / `none`) | identity: `obj.is_<fact>` ↔ `k.<fact>` |
| the `StdFactKB` dict keyed by fact name | a `KB` record with one field per relevant fact | `kb[fact]` ↔ `k.<fact>`; only the facts the witnessed queries touch are carried |
| `FactKB.deduce_all_facts` forward-chaining fixpoint (`facts.py:501`) | the closed fact tables `implementation_deduceEven` / `implementation_deduceInfinite` return | the closure's *result* — a fact table closed under the rules — is what both sides produce, captured by `consistentTheory` |
| the seed assumption set passed to `StdFactKB(facts)` | the seeded facts the returned table fixes (`even := some true`, resp. `infinite/real := some true`) | identity on the seeded facts |

The only observable is the trit fact table; it is modelled field-for-field.

## 3. Deep-model reference provenance (A-reference — checked by G-CONF)

### 3.1 `consistentTheory` + deducers ↔ the edited rule engine (A-reference)
**Reference:** the forward-chaining closure of `_assume_rules` after the gold
edit. The changed behaviour (the rule set) is modelled **deeply** as the closure
predicate `consistentTheory` and the two closed fact tables; there is **no
opaque consumed callee**.

The gold edit (`sympy/core/assumptions.py:163-201`) adds a boundedness conjunct
to the consequents of the four small-set memberships:
`rational → real ∧ finite`, `algebraic → complex ∧ finite`,
`transcendental ≡ complex ∧ ¬algebraic ∧ finite`,
`irrational ≡ real ∧ ¬rational ∧ finite`. The engine derives every
**contrapositive** automatically (`facts.py:deduce_alpha_implications` adds
`(¬j, ¬i)` for each `i → j`, `facts.py:116`), which is why `consistentTheory`
carries `¬finite → ¬{rational, algebraic, irrational, transcendental}`,
`¬rational → ¬integer`, and `¬integer → ¬{even, odd, prime, composite}`. The
pre-existing edges the witnessed queries also reach (`integer → rational`,
`real → complex`, `even/odd → integer`, the `¬odd` direction of
`even ≡ integer ∧ ¬odd`, `prime/composite → integer`, `infinite → ¬finite`, and
both directions of `noninteger ≡ real ∧ ¬integer`) are carried too; over-covering
a reachable fact is sound and each is exactly what the real engine deduces.

**Soundness / conformance (G-CONF):** `conformance_check.py` imports the REAL
`sympy` package (the patched library) and (1) asserts the witnessed deductions
directly and enumerated — `Symbol('e', even=True).is_finite is True`
(deduceEven) and `S.Infinity` / `S.NegativeInfinity` resolving the finite /
rational / integer / even / odd / algebraic / transcendental / irrational /
composite facts to False and noninteger to True (deduceInfinite); and (2) reads
the relevant `is_*` properties of a wide family of seeds (every relevant single
assumption, every satisfiable pair, and the numeric singletons `oo, -oo, 0, 1,
1/2, pi, E, I`) into a trit record and asserts that record satisfies **every
clause of `consistentTheory`** at the fact level (no value-membership proxy, no
double mask). Exit 0 iff the real engine's deduced facts are closed under the
modelled theory. Run against the *pre-patch* engine the same check fails
immediately on `even=True → is_finite True` (it returns None), so the check is
bound to the actual change.

## 4. Other gold hunks not modelled (faithfulness note)

The gold patch also edits `sympy/core/power.py` (a fast-path early-exit in the
rationality decision for integer powers of rationals), `sympy/printing/tree.py`
(adds boundedness lines to a docstring example), and `sympy/tensor/indexed.py`
(an index-bound check accepts unbounded bounds). None of these are exercised by
the FAIL_TO_PASS tests (`test_infinity`, `test_neg_infinity`,
`test_other_symbol`); they are performance / cosmetic / unrelated-domain changes
shipped in the same commit. `patch.diff` is the gold patch **verbatim** (it
applies at base_commit and resolves the harness, G-RESOLVE), so these hunks ship
intact; the verified model faithfully captures the **tested** behaviour (the
boundedness-containment theory the F2P tests observe).
