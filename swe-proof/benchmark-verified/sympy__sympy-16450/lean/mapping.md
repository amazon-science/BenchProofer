# mapping.md — sympy__sympy-16450

## Symbol binding (file:line @ base_commit aefdd023dc)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_posify` / `problem_spec_posify` / `correct_posify` | the scalar branch of `posify(eq)` — building the replacement dummy symbols for the free symbols whose sign is undetermined | `sympy/simplify/simplify.py:251-254` @ base_commit (edited line `251`) |
| `signUndetermined a` | `s.is_positive is None` (filter predicate over `eq.free_symbols`) | `simplify.py:252` |
| `assertPositive a` (= `("positive",true) :: a`) | `positive=True, **s.assumptions0` (the kwargs passed to `Dummy`, post-patch) — the leading pair is the explicit keyword, the tail is the splatted record | `simplify.py:251` (pre-patch: `positive=True` only) |
| `declAccepted decl` | whether the call `Dummy(s.name, **decl)` COMPLETES — a total probe of the declaration, answered `false` where the call would not complete | `Dummy.__new__` → `StdFactKB` / `sympy.core.facts` |
| `resolveAssumptions decl h` | `Dummy(s.name, **decl).assumptions0` — the full inferred property record of a freshly built dummy declared with `decl`, applicable only where the probe answered yes | `Dummy.__new__` + `Symbol.assumptions0` (`sympy/core/symbol.py:260`) |

The modeled function is the **scalar branch** of `posify`:

```python
reps = {s: Dummy(s.name, positive=True, **s.assumptions0)      # POST-PATCH
             for s in eq.free_symbols if s.is_positive is None}
eq = eq.subs(reps)
return eq, {r: s for s, r in reps.items()}
```

For every free symbol `s` whose sign is undetermined (`s.is_positive is None`),
`posify` substitutes a fresh `Dummy` declared *positive*. The PRE-PATCH code
declared the dummy with `positive=True` **only**, silently discarding every other
property `s` carried (finiteness, integrality, …). The POST-PATCH code adds
`**s.assumptions0`, so the replacement is declared with the original symbol's full
property set augmented by positivity. The observable is each replacement's
`assumptions0` (its full inferred property record) — exactly what the F2P test
`test_posify` asserts for `Symbol('k', finite=True)` (the replacement must still
report `finite: True`, `infinite: False`).

## The declaration is PARTIAL, and the routine inherits its definedness

`Dummy(name, **decl)` does not complete for every `decl`. Two ways it does not,
both reachable from this call site and both measured in the base worktree with the
gold patch applied:

| `decl` | outcome | reached from |
|---|---|---|
| states a property twice, e.g. `positive=True, **{'positive': True, …}` | `TypeError: Dummy() got multiple values for keyword argument 'positive'` | a symbol whose record already states `positive` — i.e. exactly the symbols the `is_positive is None` filter EXCLUDES, so `posify` never forms this declaration |
| states values that cannot hold together, e.g. `positive=True, **{'rational': False, 'irrational': False, …}` | `sympy.core.facts.InconsistentAssumptions` | a symbol whose sign IS undetermined, so `posify` does form this declaration and the whole call raises |

Measurement (base worktree at `aefdd023dc` + `patch.diff`, `PYTHONPATH` set to the
worktree, `sympy.__file__` confirmed inside it): enumerating every 1-, 2- and
3-key declaration over the 22 keys below (13288 candidates, 8761 of which build a
symbol, 3280 of those sign-undetermined), **74 of the 3280 sign-undetermined
symbols — 2.26% — have an augmented declaration that is refused** as
`InconsistentAssumptions`. The smallest is
`Symbol('x', rational=False, irrational=False)`; others are
`{irrational: False, algebraic: False}`,
`{irrational: False, transcendental: True}` and
`{algebraic: False, transcendental: False}`:

```
>>> posify(Symbol('x', rational=False, irrational=False))     # post-patch
sympy.core.facts.InconsistentAssumptions: {…, positive: True, rational: False, …}, irrational=True
>>> posify(Symbol('x', rational=False, irrational=False))     # pre-patch
(_x, {_x: x})
```

So the exceptional outcome is a behaviour of the patched routine, not of the
original one, and it is part of what a faithful model of the patched routine must
say. It is carried in Lean the way a partial operation is carried: `declAccepted`
is the total question "is this property set a declaration that has a record", and
`resolveAssumptions` takes the answer as an argument, so no Lean term names the
record of a property set that has none. `result : Option (List Assumptions)` is
then the return value, or the call RAISING.

The two rows of the table above are also why definedness is scoped to the KEPT
symbols in the spec: a declaration formed from a symbol that is not replaced is
never formed by the real routine at all, so its acceptance cannot influence
whether the call has a value. `conformance_check.py` asserts that scoping in both
directions and reports the coverage counts.

## Modeled branch / configuration

This bundle models the **scalar** (`not iterable(eq)`) branch — the lines the
patch edits. The iterable branch (`if iterable(eq):`) merely recurses into this
scalar branch per element via `posify(s)`, so it is covered transitively and is
out of scope as an independent behavior.

`is_positive is None` is equivalent to `'positive' not in s.assumptions0`:
`assumptions0` records only properties with a known (non-`None`) value, and an
inferred-positive symbol (e.g. `prime=True`) has `positive` present and is
correctly excluded. (Verified over fuzzed assumption sets: 0 mismatches.)

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a symbol's `assumptions0` (`dict[str, bool]`, only known props) | `a : Assumptions = List (String × Bool)` | one `(name, value)` pair per known property; absent key ↦ undetermined |
| `eq.free_symbols` (a `set[Symbol]`) | `syms : List Assumptions` | each symbol ↦ its `assumptions0`; order is not observable (G-CONF compares the replacements as a multiset) |
| the call `Dummy(name, **decl)` completing | `declAccepted decl = true` | a total probe; `false` is an answer, not a failure. `name` is irrelevant to it |
| `Dummy(name, **decl).assumptions0` | `resolveAssumptions decl h` | full inferred property record of a dummy declared with `decl`; `name` is irrelevant to the record. The `h` argument is the probe's yes-answer, and is proof-irrelevant |
| `posify(eq)` returning, with `{r: s …}` replacement dummies' `assumptions0` records | `result = some records` | the per-undetermined-symbol replacement records |
| `posify(eq)` RAISING (`InconsistentAssumptions` from a replacement declaration) | `result = none` | the call has no value; there is no partial list of records |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The changed operation — building the replacement
  declared property set from the original symbol's properties plus positivity
  (`assertPositive`) and the filter (`signUndetermined`) — is modeled DEEPLY
  (spelled out in the impl/spec), so it is never axiomatized (§0.7).
- `declAccepted` and `resolveAssumptions` (the symbol-construction + assumption
  inference closure, carried as a domain question plus an operation on that
  domain) are UNCHANGED dependencies the fix calls but does not alter. Both are
  declared `opaque` and tagged **A-reference**: validated == the real callee
  (`Dummy(name, **decl)` completing, and its `assumptions0`) by the differential
  `conformance_check.py` (G-CONF). The proof of `correct_posify` consumes no
  property of either — they occur identically in the specification and the
  implementation — so G-AX is a skip stub.
- No flag dependency: `posify`'s scalar branch takes no mode flag.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
