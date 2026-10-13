# mapping.md — django__django-14765

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4e8121e8e42a24acc3565851c9ef50ca8322b15c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the modeled sub-steps.

Repo file under change: `django/db/migrations/state.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalizeSetArg (arg : SetArg)` | `ProjectState.__init__` — `django/db/migrations/state.py:91` (the `real_apps` normalization block, body lines 94-97) | the modeled changed function: how the optional set-typed argument is normalized at construction |
| `SetArg` (`absent` / `alreadySet` / `coercible`) | the outcome of the two primitive tests `real_apps is None` and `isinstance(real_apps, set)` performed on the `real_apps` parameter | free input: the argument's shape (see §2) |
| `normalizeSpec` (`pure`) | the desired post-patch normalization: `None`→`set()`, set→kept, non-set→`AssertionError` | deep model of the changed behaviour |
| `InitErr.rejected` | the `AssertionError` raised by `assert isinstance(real_apps, set)` | the rejection outcome the patch introduces |

There are **no axioms** and **no deep-model reference to a library callee**: the
two distinguishing tests are Python primitives (`is None`, `isinstance(_, set)`),
modeled as the free input `SetArg`; the changed action is modeled deeply by
`normalizeSpec`. No `axiom_check.py` (G-AX is N/A — no axioms).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `real_apps` parameter's *shape* | `SetArg` | `None`/omitted ↔ `absent`; an actual `set` ↔ `alreadySet xs` (members `xs`); any other non-None value ↔ `coercible ys` (members `ys` it would iterate to) — the partition induced by `is None` then `isinstance(_, set)` |
| a `set[str]` value | `List String` | a Python set's members ↔ the carrier `List String`; G-CONF compares as Python `set(...)` so ORDER and MULTIPLICITY of the carrier are irrelevant (a set has neither). `set()` ↔ `[]`. |
| the stored `self.real_apps` (accepting branch) | `Except.ok (xs : List String)` | the stored Python set ↔ `set(xs)` |
| `raise AssertionError` (rejecting branch) | `Except.error .rejected` | construction raises ↔ `Except.error` |

The `models` parameter of `__init__` and the other body statements
(`self.models = models or {}`, `self.is_delayed`, `self.relations`) are
UNCHANGED by the patch and behaviourally inert for the modeled behaviour; they
are not modeled (directive 5: not `mut`, not in the carrier). The single
observable the patch alters is the `real_apps` normalization, which is what
`normalizeSetArg` pins.

### Note on the empty-set / falsy subtlety
Pre-patch the guard was `if real_apps:` (truthiness), so an empty but genuine
`set()` fell to the `else` branch and was replaced by a *fresh* `set()`.
Post-patch the guard is `if real_apps is None:`, so an empty `set()` is kept
as-is. Both are observationally the empty set (`set() == set()`), so this
distinction is invisible to any observer of `self.real_apps` and the model need
not track it — `alreadySet []` and the `absent` default both yield an empty
stored collection, agreeing with the gold patch. (Confirmed by G-CONF, which
fuzzes empty sets, empty lists, and the omitted argument.)

## 3. Free-input justification (directive 7)

`SetArg` is owed no contract: the method's postconditions hold for EVERY value of
it. It is strictly weaker than any concrete pair of tests `(is None,
isinstance _ set)`. The two tests are UNCHANGED by the patch (both pre- and
post-patch consult `isinstance(real_apps, set)` and a None/falsy check); only the
*action taken* on the non-set branch changed (silent `set(real_apps)` → `assert`
→ raise). That action is the deeply-modeled `normalizeSpec`. Hence there is no
callee to axiomatize and no G-AX obligation.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14765`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `normalizeSpec` (the R/I-tagged dispatch) to Python and drives the
real gold-patched `ProjectState.__init__` as the oracle, comparing the pair
`(raised AssertionError?, stored real_apps as a Python set)` over the boundary
corpus (omitted / None / empty set / sets / frozenset / list / tuple / str /
dict / iterator / scalars / object) plus ≥1.2·10⁵ fuzzed arguments. The
unchanged primitive tests (`is None`, `isinstance _ set`) are exercised LIVE
inside the shadow's `classify` (not a model), matching the free-input treatment.
