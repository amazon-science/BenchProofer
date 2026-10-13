# mapping.md — django__django-12965

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 437196da9a386bd4cc62b0ce3f2de4aba468613d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `directDeleteEligible (mut tableRefs : List Nat)` | `SQLDeleteCompiler.single_alias` — `django/db/models/sql/compiler.py:1408` (the `@cached_property`) | the modeled changed function |
| `withTarget` *(deep model — A-reference)* | `Query.get_initial_alias` — `django/db/models/sql/query.py:916` | the unchanged query-construction callee; its refcount side effect bumps the head (base-table) entry |
| `liveCount (rc : List Nat)` | the expression `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map)` — `compiler.py:1410` | pure spec: count of positively-referenced tables |

The boolean the property returns models the predicate
`sum(...) == 1`, i.e. "the query addresses exactly one active table" — when
true the deletion compiles to a direct `DELETE FROM <table> [WHERE ...]`; when
false it compiles to `DELETE ... WHERE pk IN (SELECT ...)` (a subquery).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo state. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the query's reference-count state, i.e. the multiset `[self.query.alias_refcount[t] for t in self.query.alias_map]` taken **in `alias_map` insertion order** | `tableRefs : List Nat` | the `i`-th `alias_map` key (a table alias `t`) ↔ the `i`-th `List Nat` entry `self.query.alias_refcount[t]`; `len(alias_map)` ↔ `tableRefs.length`; the head of the list is the **base table** (`Query.base_table` is the first `alias_map` key, `query.py:245`). A full-table delete (`Model.objects.all().delete()`) starts with an **empty** `alias_map` ⇔ `tableRefs = []`. |
| `self.query.get_initial_alias()` side effect on the refcount state | `withTarget (rc) = (rc.headD 0 + 1) :: rc.tail` | when `alias_map` is empty, the base table is `join`-ed in fresh with refcount 1 (`get_initial_alias` → `join(BaseTable(...))` → `table_alias(create=True)` sets `alias_refcount[alias] = 1`, `query.py:755`) ⇔ `withTarget [] = [1]` (`headD 0` on the empty list is `0`, so the head becomes `1` and the empty tail is preserved); when the base table already exists, `ref_alias` increments its count (`query.py:758-760`) ⇔ the head goes `h ↦ h+1` and the tail is unchanged. The single total equation covers both real branches. |
| `sum(bool for ...) == 1` (evaluated AFTER `get_initial_alias()`) | `liveCount tableRefs.tail == 0` returning `Bool` | Python `sum` of booleans counts the truthy entries; `liveCount` counts entries `≠ 0`. Because `get_initial_alias()` always leaves the head (base-table) refcount ≥ 1 and touches no other entry, the post-call total `sum(...)` is exactly `1 + liveCount tail`, so `sum(...) == 1` ⇔ `liveCount tail == 0` — pointwise, on every state. The equivalence is machine-checked exhaustively over all vectors of length ≤ 6 with entries ≤ 3 and, against the real patched property, over 100,016 real `Query` states (0 disagreements). `tableRefs` entries are `Nat` (counts are non-negative; `unref_alias` never drives a counted table below 0 on the delete path). |

`List Nat` is the carrier because `single_alias` observes **only** the
refcounts, in `alias_map` order, and whether each is positive — no other field
of the `Query`/`Compiler` object is touched. The `mut` frame is exact: the only
state the operation mutates is this reference-count vector, via `withTarget`
(post-state `tableRefs = withTarget tableRefsOld`), mirroring the sole side effect
of `get_initial_alias()`.

## 3. Callee provenance (kind A — checked by G-AX / axiom_check.py)

### 3.1 `withTarget` deep model ↔ `Query.get_initial_alias` (A-reference)
**Callee:** `django.db.models.sql.query.Query.get_initial_alias` (unchanged by
the patch). The change *adds a call to it* inside `single_alias`; it is not the
operation under change, so its effect is modeled **deeply** by `withTarget` (pure
region) and validated against the real callee — there is **no consumed axiom**.

Real behaviour on the refcount state (`query.py:916-925`):
```python
def get_initial_alias(self):
    if self.alias_map:
        alias = self.base_table          # first alias_map key
        self.ref_alias(alias)            # alias_refcount[alias] += 1
    else:
        alias = self.join(BaseTable(self.get_meta().db_table, None))  # fresh, refcount 1
    return alias
```
- `alias_map` empty ⇒ a new base-table alias is created with `alias_refcount = 1`
  ⇒ refcount state `[]` ↦ `[1]`. (`withTarget [] = (0+1) :: [] = [1]`, since
  `List.headD 0 [] = 0` and `List.tail [] = []`.)
- `alias_map` non-empty ⇒ the base table's (head) refcount is incremented by 1,
  every other entry unchanged ⇒ `(h :: t) ↦ (h+1) :: t`, which is exactly
  `(rc.headD 0 + 1) :: rc.tail` on a non-empty `rc`.

Both real branches are therefore the ONE total equation
`withTarget rc = (rc.headD 0 + 1) :: rc.tail`.

**Soundness check (G-AX):** `axiom_check.py` constructs real Django `Query`
objects at `base_commit`, drives their alias state into representative
configurations (empty base, single active table, multiple tables, a
zero-refcount table from `unref_alias`), runs the REAL `get_initial_alias()`,
and asserts the resulting `[alias_refcount[t] for t in alias_map]` equals
`withTarget` applied to the pre-state. Exit 0 iff sound.

G-AX checks **only** the A-reference callee `get_initial_alias`, never
`single_alias`. G-AX runs against the **unpatched** base_commit source (no
`apply_gold`), and `single_alias` is the function *under change* — at
base_commit it does not yet contain the `get_initial_alias()` call the patch
introduces, so on an empty `alias_map` it returns `sum([]) == 1 = False` while
the modeled (post-patch) decision returns `True`. Per SPEC_GUIDE §0.7 the
function under change is never axiom-checked. Its **patched** behaviour is
instead validated by **G-CONF** (`conformance_check.py`, run WITH the gold patch
applied — `docker_exec.run_in_container(..., apply_gold=True)`) over ≥10⁵ fuzzed
states including the empty full-delete case, and by the agentic G-EQ.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12965`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`withTarget`/`liveCount` (R/I-tagged ops) to Python and compares against the real
patched `SQLDeleteCompiler.single_alias` over real `Query` objects with fuzzed
alias-reference states (including the empty-`alias_map` full-delete case that
the F2P test exercises).
