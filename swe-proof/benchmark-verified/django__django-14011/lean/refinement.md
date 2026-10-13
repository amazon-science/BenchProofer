# refinement.md — operation correspondence (django__django-14011)

Maps every op in the two implementations to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch adds, to `ThreadedWSGIServer`, two value-level behaviors on the
per-thread connection registry (`django.db.connections`, an alias→connection map):

```python
def process_request_thread(self, request, client_address):
    if self.connections_override:
        for alias, conn in self.connections_override.items():
            connections[alias] = conn          # behavior 1: bind provided conns
    super().process_request_thread(request, client_address)

def _close_connections(self):
    connections.close_all()                    # behavior 2: release all conns
def close_request(self, request):
    self._close_connections()
    super().close_request(request)
```

`connections` is modeled as `List Resource` keyed by `.name` (unique keys); a
connection's "is it live" state (`conn.connection is not None`) is `Resource.isOpen`
(mapping.md). The `super().…` calls (request handling / socket teardown) are side
effects outside the connection-registry value kernel and are abstracted away — the
F2P tests observe the registry value state, which is exactly what the two triples pin.

## Behavior 1 — `implementation_bindResources` (process_request_thread loop)

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut r := reg` | the live registry `connections` before the loop | I | the registry value the thread starts from |
| 2 | `for c in provided do` | `for alias, conn in self.connections_override.items():` | R | `List Resource` ↔ the provided alias→conn collection (mapping.md); iteration order is the collection order |
| 3 | `r := setRes r c` | `connections[alias] = conn` (`BaseConnectionHandler.__setitem__`) | R | keyed insert/replace: replace the entry with matching key else append. `__setitem__` is an UNCHANGED callee modeled as the pure refinement `setRes`; no axiom |
| 4 | `return r` | the registry value after all overrides installed | I | resulting registry |

`__setitem__` is applied identically in spec-model and impl (both via `setRes`), so
the proof discharges it without any callee property — no A-consumed/A-reference row.

## Behavior 2 — `implementation_releaseResources` (_close_connections / close_all)

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 5 | `let mut out := []` | accumulator for the iterated registry | I | start of the close-all walk |
| 6 | `for c in reg do` | `for alias in self: …` inside `ConnectionHandler.close_all` | R | `List Resource` ↔ the registry iterated by `close_all`; one step per registered connection |
| 7 | `out := out ++ [releaseRes c]` | `connection.close()` for that alias | R | `connection.close()` is an UNCHANGED callee whose only in-scope observable effect is moving the connection to the closed state (`conn.connection is None`); modeled as the pure field update `releaseRes`; no axiom |
| 8 | `return out` | the registry with every connection closed | I | resulting registry, all keys preserved, all closed |

`close_all` / `connection.close()` are applied identically on both sides (both via
`releaseRes`), so the proof discharges them by the pure definition — no
A-consumed/A-reference row, and G-AX is a skip stub.

## Prepatch (the bug) — one per independently-fixed behavior

- `Solution_prepatch.lean` (behavior 2): at base_commit `ThreadedWSGIServer` has no
  `close_request`/`_close_connections` override, so connections are never released
  after a request — modeled by leaving each resource as found (`out ++ [c]`, still
  open). `correct_releaseResources` then cannot close the goal `∀ r ∈ result,
  r.isOpen = false` whenever the registry holds a live resource. This mirrors the
  F2P `test_closes_connections` assertion `assertIsNone(conn.connection)`.
- `Solution_prepatch_2.lean` (behavior 1): at base_commit the thread installs no
  provided connections — modeled by returning the registry unchanged. Then
  `correct_bindResources` cannot close the lookup characterization (a provided key
  must resolve to its provided value) whenever a provided resource is absent from
  `reg`. This mirrors the F2P
  requirement that the request thread uses the connections passed to the server
  (data written by a view is visible / fixtures load via the shared connection).

## Frame discipline (directive 5)

- `problem_spec_bindResources` pins the ENTIRE lookup function of the result (every
  provided key maps to its provided value; every other key keeps its prior registry
  value) AND requires the result to have no duplicate keys — so a wrong impl can
  neither perturb an untouched alias nor leave a stale/shadow duplicate entry for a
  provided alias (closing the list-as-dict frame hole).
- `problem_spec_releaseResources` pins the full key-list (order included) equal to
  the input's, so no entry may be added or dropped, AND every result entry closed —
  a wrong impl can neither lose a connection nor leave one open.

No A-tagged op; all ops are R or I, so G-CONF runs a full differential fuzz over both
behaviors and G-AX is a skip stub. No changed-inexpressible op.
