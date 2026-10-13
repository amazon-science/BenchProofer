# mapping.md — django__django-14011

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e4430f22c8e3d29ce5d9d0263fba57121938d06d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

`spec_provenance: "cold"` — derived only from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`, read in the provided worktree
`$SCRATCH`. No prior solution consulted.

Repo files under change:
- `django/core/servers/basehttp.py` (`ThreadedWSGIServer`) — Site A.
- `django/db/backends/sqlite3/features.py` (`django_test_skips`) — Site B.

## 0. What actually computes (why this is NOT blocked)

The gold patch gives `ThreadedWSGIServer` (the per-request worker the live-server
test harness spawns) two behaviors over a **keyed registry of database
connections** (`django.db.connections`, a `ConnectionHandler` — a mapping
`alias ↦ connection`):

1. **Install preferred bindings** (`process_request_thread`): before doing the
   request, for every `alias, conn` in `connections_override`, do
   `connections[alias] = conn`. `ConnectionHandler.__setitem__`
   (`django/utils/connection.py:66`) is `setattr(self._connections, key, value)`,
   and `__getitem__` (`:56`) returns the stored attribute if present **else lazily
   creates a fresh connection**. So installing the override makes the worker
   thread resolve those aliases to the *parent's* connections instead of opening
   *fresh, empty* in-memory databases. This is the behavior the DB-visibility
   F2P tests depend on (see §5): without it the worker sees an empty DB and
   `Data written by a view can be read` / `Fixtures ... visible` /
   `test_check_model_instance_from_subview` fail.

2. **Release all held connections** (`close_request` → `_close_connections` →
   `connections.close_all()`): after each request, close every connection in the
   registry. `ConnectionHandler.close_all` (`django/db/utils.py:207`) iterates
   the registry and calls `connection.close()` on each. This is the per-handle
   release that fixes the reappearance of #22414 (a still-open connection at
   teardown ⇒ `database ... is being accessed by other users`).

Both are **functions over a data carrier** (a keyed collection / a list of
connection states), and are modeled deeply and concretely — there is no
consumed oracle axiom. What is genuinely framework-mediated — that CPython
`socketserver.ThreadingMixIn` dispatches `process_request_thread` on a worker
thread and `socketserver.BaseServer` calls `close_request` after each request —
is the **I-refinement leg**: the `do` block runs the same data operations in the
same order the framework invokes them. This is exactly the abstraction the
exemplar uses when it models a Python `str` object as `List Char` and drops the
`mark_safe` wrapper: the *carrier* is modeled, the *plumbing* is the refinement.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `installPreferred (preferred registry : List (String × Int))` | the override-install loop in `ThreadedWSGIServer.process_request_thread` — `django/core/servers/basehttp.py:90-95` (post-patch); the `for alias, conn in self.connections_override.items(): connections[alias] = conn` over `django.db.connections` | modeled changed function #1: install preferred bindings into the keyed connection registry with override precedence |
| `releaseAll (handles : List Bool)` | `ThreadedWSGIServer._close_connections` (`basehttp.py:97-99`, post-patch), the body of which is the unchanged callee `connections.close_all()` (`django/db/utils.py:207`); reached via `close_request` (`basehttp.py:101-103`) | modeled changed function #2: release every held connection before the worker is recycled |
| `releasedSeq (cs : List Bool)` *(deep model — A-reference)* | `ConnectionHandler.close_all` — `django/db/utils.py:207` | pure spec: the post-state of the registry after `close_all`; deep model of the unchanged callee, validated `releasedSeq == close_all`-post-state by axiom_check.py (G-AX), NOT consumed as an axiom |
| `installPreferred`'s `preferred ++ registry` with first-match lookup | `ConnectionHandler.__setitem__` / `__getitem__` — `django/utils/connection.py:56,66` | pure spec: override-precedence keyed lookup; deep model (A-reference), G-AX-validated |

Site B (`django_test_skips` += one test-name string) is a **test-skip-list
datum**, not a computation over any carrier; it carries no discriminating
behavior modelable as a grounded postcondition (it only affects which tests the
eval *runs*, and that test is not in FAIL_TO_PASS). It is recorded here for
completeness and reproduced verbatim in `patch.diff`; it is intentionally not a
modeled `method`. See refinement.md §C.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `django.db.connections`, a `ConnectionHandler` mapping `alias ↦ connection` | `List (String × Int)` (assoc-list, first-match lookup) | a registry `{a₀: c₀, a₁: c₁, …}` ↔ the list `[(a₀, id c₀), (a₁, id c₁), …]`; the connection object is abstracted to a stable integer identity `id(conn)` (only object identity is observed by the test — `assertIsNone(conn.connection)` and DB-visibility); `connections[a]` first-match ↔ `List.find?`/first occurrence |
| `connections_override`, a `dict` `alias ↦ conn` | `List (String × Int)` (`preferred`) | same encoding; the dict the parent thread hands the worker |
| installing the override: `for a,c in override.items(): connections[a]=c` | `preferred ++ registry` (preferred prepended so first-match wins) | `__setitem__` makes the alias resolve to the override conn; modeled as override-precedence merge. Aliases only in `registry` keep their binding; aliases in `preferred` resolve to the preferred conn. (The *physical* mutation order is irrelevant to the observed lookup result — net effect is precedence, which prepend captures.) |
| a single connection's open/closed state | Lean `Bool` (`true`=active/open, `false`=released/closed) | `conn.connection is not None` ↔ `true`; after `conn.close()`, `conn.connection is None` ↔ `false` |
| the registry as a list of connection states | `List Bool` (`handles`) | `[s(c) for c in connections.all()]` where `s(c) = (c.connection is not None)` |
| `connections.close_all()` | `releasedSeq` (every entry → `false`) | each `connection.close()` sets that connection's state to released regardless of prior state |

`List` first-match lookup is total and sound; the carrier is `List` (not
`HashMap`) because the operations observed are *precedence* (install) and
*universal release* (close-all), both expressible structurally without hashing.

## 3. Callee provenance (deep models — checked by G-AX / axiom_check.py)

### 3.1 `installPreferred` / override-precedence merge ↔ `ConnectionHandler.__setitem__`+`__getitem__` (A-reference)
**Callee:** `django.utils.connection.ConnectionHandler` (`__setitem__`,
`__getitem__`), at base (UNCHANGED by the patch — the patch only *calls* it).
`__setitem__(key, value)` is `setattr(self._connections, key, value)`;
`__getitem__(alias)` returns the stored attribute if set, else lazily creates
one. So after installing an override for `alias`, `connections[alias]` returns
the override object (identity preserved); aliases never installed keep their own
binding. This is exactly `preferred ++ registry` under first-match lookup. There
is **no consumed axiom** — the merge is spelled out in the `do` block.

**Soundness check (G-AX):** `axiom_check.py` instantiates a real
`ConnectionHandler` in-container, installs a fuzzed set of override bindings via
`__setitem__`, and asserts that for every alias the post-install lookup
(`__getitem__` identity) equals the override-precedence merge model
(`preferred ++ registry`, first-match) over the same inputs. Boundary + fuzz.

### 3.2 `releaseAll` / `releasedSeq` ↔ `ConnectionHandler.close_all` (A-reference)
**Callee:** `django.db.utils.ConnectionHandler.close_all` (`utils.py:207`),
UNCHANGED. Its body iterates the registry and calls `connection.close()` on
each present connection. After it returns, **every** connection in the registry
that was instantiated is closed (state `false`), regardless of its prior state —
which is `releasedSeq` (map every entry to `false`).

**Soundness check (G-AX):** `axiom_check.py` builds a real `ConnectionHandler`
holding fake connection objects whose `close()` flips an `is_open` flag, with a
fuzzed mix of open/closed initial states, runs `close_all()`, and asserts every
connection's post-state is closed (`false`) — i.e. the observed post-state ==
`releasedSeq` of the initial-state list. Boundary (empty, all-open, all-closed,
mixed) + fuzz. stdlib-only (`unittest.mock` from the standard library) — no DB.

No flag-dependent callees. No exceptions are assumed away: `close_all` swallows
`AttributeError` for never-instantiated aliases (its `try/except`), which the
model handles because such aliases simply have no observable open state to flip;
G-AX includes never-instantiated aliases in the fuzz.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`14011`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`installPreferred` (override-precedence merge) and `releaseAll` (universal
release) to Python and diffs them against the patch.diff behaviour — the real
`ConnectionHandler.__setitem__`/`__getitem__` for install and the real
`close_all` post-state for release — over ≥10⁵ fuzzed registries/overrides.

## 5. Why these flip the FAIL_TO_PASS tests (grounding the spec strength)

The mandatory `test_patch` rewrites `LiveServerThread._create_server` to pass
`connections_override=` to the server class and, in `setUpClass`, builds the
override from the in-memory sqlite connections (and `inc_thread_sharing()`s
them). On the eval backend (in-memory sqlite — `is_in_memory_db()` true):

- **Install (`installPreferred`) is load-bearing for DB-visibility F2P tests.**
  The worker thread is a *different* thread from the one that created the test
  fixtures. `connections[DEFAULT_DB_ALIAS]` in the worker, absent an override,
  lazily creates a **fresh** connection — and for in-memory sqlite a fresh
  connection is a **fresh empty database**. Installing the parent's connection
  object makes the worker share the populated in-memory DB. Tests that require
  this: `Data written to the database by a view can be read.`,
  `Fixtures are properly loaded and visible to the live server thread.`,
  `test_check_model_instance_from_subview`, `test_view_calls_subview`. With the
  override-install reverted (`Solution_prepatch.lean`), the spec clause
  `out = preferred ++ registry` is violated (the worker keeps the registry as-is
  ⇒ fresh empty DB), so the prepatch fails — matching the real test failures.

- **Release (`releaseAll`) is the issue fix.** Closing the worker's connections
  after each request is what prevents the teardown race (#22414 reappearance).
  Reverting it (`Solution_prepatch_2.lean`) violates `∀ b ∈ out, b = false`.

- **The constructor accepting `connections_override=`** is a precondition for
  *either* behavior to run (without it the test_patch's `_create_server` raises
  `TypeError`). It is modeled implicitly: `installPreferred` *takes* `preferred`
  as a parameter — a function that consumes the override argument can only exist
  if the constructor accepts and stores it. The signature change is the R-leg
  framing (parameter passing), not a separate modeled computation.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).
