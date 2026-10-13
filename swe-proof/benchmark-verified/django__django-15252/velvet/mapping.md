# mapping.md — django__django-15252

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 361bb8f786f112ee275be136795c0b1ecefff928`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/migrations/executor.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recordStoreGate (hasWork storePresent : Bool)` | the preparation phase of `MigrationExecutor.migrate(...)` — `django/db/migrations/executor.py:91` (the gate is the block at body lines 98-100 pre-patch / 98-104 post-patch) | the modeled changed function: the control-flow decision at the top of the step |
| `hasWork : Bool` | `plan != []` — whether the caller supplied a non-empty list of items to (un)apply this step (`executor.py:91` `plan` argument; the gate keys on `plan == []` at the post-patch line) | input fact #1 |
| `storePresent : Bool` | `self.recorder.has_table()` — `django/db/migrations/recorder.py:53` (returns whether the bookkeeping table already exists) | input fact #2 |
| `GateOutcome.ensured : Bool` | whether `self.recorder.ensure_schema()` (`recorder.py:59`) is invoked during the step | observed effect #1 |
| `GateOutcome.earlyExit : Bool` | whether the step short-circuits — returns `self._create_project_state(with_applied_migrations=False)` (`executor.py:74`) before reaching `self.check_replacements()` (`executor.py:132`) | observed effect #2 |

No symbol is axiomatised: see §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `plan` argument of `migrate` (a `list` of `(migration, backwards)` tuples, or `None`) restricted to the Requires-satisfying domain {empty list, non-empty all-forwards list} | `hasWork : Bool` | `plan == []` ↔ `hasWork = false`; any non-empty `plan` ↔ `hasWork = true`. The gate's only observation of `plan` is the emptiness test `plan == []`, so the boolean abstraction is exact on this domain. |
| `self.recorder.has_table()` (`bool`) | `storePresent : Bool` | identity on `Bool`: `True ↔ true`, `False ↔ false`. |
| "`ensure_schema()` was called during this step" (`bool`, observed by a call spy) | `GateOutcome.ensured : Bool` | identity on `Bool`. |
| "the step short-circuited before `check_replacements()`" (`bool`, observed: the early `return` ran ⟺ `check_replacements` was NOT called) | `GateOutcome.earlyExit : Bool` | identity on `Bool`: `True ↔ true`. |

Domain note (Requires): the modeled gate covers the inputs the fix governs and
the F2P tests exercise — `plan` is an explicit list (`[]` or non-empty forwards)
and `has_table()` returns a definite boolean. `plan is None` (recomputed
downstream) maps to `hasWork = true` (it is `!= []`), consistent with the
post-patch `else: ensure_schema()` branch; it is not separately fuzzed because
the F2P caller always passes an explicit `plan`.

## 3. Callee provenance — there are NO axioms and NO deep-model references

The behaviour under specification is a **pure control-flow decision**. The
functions the step touches are not contracts the proof consumes; they enter the
model only as the two boolean inputs (`has_table()` → `storePresent`; the
emptiness of `plan` → `hasWork`) and the two boolean effect-observations
(`ensure_schema` invocation → `ensured`; pre-`check_replacements` return →
`earlyExit`). Concretely:

- `ensure_schema()` / `has_table()` / `_create_project_state(...)` /
  `check_replacements()` / `migration_plan(...)` are **unchanged** by this fix
  and the gate's correctness does not depend on *what* any of them computes —
  only on *whether* the gate calls `ensure_schema` and *whether* it returns
  early. So none is axiomatised (directive 7: never axiomatise the function
  under spec; and there is no unchanged callee whose contract is load-bearing).
- The one operation that genuinely **changed** — the conditional that gates the
  `ensure_schema` effect and adds the early exit — is modeled **deeply** as the
  `if !hasWork then (if !storePresent then earlyExit := true) else ensured := true`
  branch in the impl region. It is therefore an **I/R** refinement throughout,
  not an axiom.

Consequence: `axioms` region is empty; `meta.json deep_model_references` is
empty; `meta.json conf_skip = false` (the impl region is all I/R, so G-CONF runs
a real verdict); **G-AX is vacuous** (no callee contract to execute against —
`axiom_check.py` records this and exits 0).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15252`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the `recordStoreGate` impl branch (the only ops, all I/R) to
Python; the oracle drives the **real patched `MigrationExecutor.migrate`** with
`ensure_schema` / `has_table` / the downstream steps replaced by call spies, and
reads back `ensured` (did `ensure_schema` fire) and `earlyExit` (did the step
return before `check_replacements`).
