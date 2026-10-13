# refinement.md — django__django-14011

The operation-by-operation correspondence between `model.py`'s implementation
(the `serve_request_on_worker` and `teardown_request` impl regions) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## What the tests actually discriminate (oracle coverage)

The 17 FAIL_TO_PASS tests are the ordinary LiveServer functional tests
(`test_view`, `test_404`, `test_media_files`, "Data written to the database by a
view can be read", …). With the hidden `test_patch` applied, the test harness
configures the server with a parent-supplied connection set
(`_create_server(..., connections_override=connections_override)`). **Pre-patch
the server's constructor does not accept that configuration, so it raises
`TypeError` in `setUpClass` and ALL 17 F2P tests error before any request is
handled.** The sole tested discriminator is therefore *whether the server can be
configured with the parent-supplied connection set so that set becomes available
to the worker* — a control-flow effect (configure-succeeds vs configure-is-
impossible) with no value-level witness. `model.py` pins exactly this as the
discriminating clause of `serve_request_on_worker` via the unforgeable per-server
capability `connections_handed_off(server)` (§A). The connection-CLOSING
behaviour (`test_closes_connections`) is **skipped on the in-memory-sqlite eval
backend** (the gold's `sqlite3/features.py` hunk adds it to the skip set), so it
is NOT an F2P discriminator; it is modelled as a secondary, documented behaviour
(§B), faithful to the gold but not load-bearing for resolution.

## A. Connection hand-off / configuration — `__init__` + `process_request_thread`

Gold hunks (added to `ThreadedWSGIServer`, `django/core/servers/basehttp.py`):
```python
def __init__(self, *args, connections_override=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.connections_override = connections_override

def process_request_thread(self, request, client_address):
    if self.connections_override:
        for alias, conn in self.connections_override.items():
            connections[alias] = conn
    super().process_request_thread(request, client_address)
```

Modeled by `serve_request_on_worker(server, tokens, has_override, override_tokens)`,
which carries the discriminating capability `connections_handed_off(server)`.

| # | model.py impl op (`serve_request_on_worker`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `has_override: List[bool]` + `override_tokens: List[int]` (the parent-supplied set); `tokens: List[int]` (the worker registry identities) | `self.connections_override` (a `{alias: conn}` dict, stored by `__init__`); `connections` (the `{alias: conn}` per-thread registry) | R | registry/override dict ↔ index-aligned parallel lists over alias positions (mapping.md §2). `has_override[i]` ↔ `alias in connections_override`; `override_tokens[i]` ↔ `connections_override[alias]` identity; `tokens[i]` ↔ `connections[alias]` identity. |
| A2 | `accept_connection_set(server, has_override, override_tokens)` → grants `connections_handed_off(server)` | the added `__init__(*, connections_override=None)` **accepting** the supplied set and storing `self.connections_override = connections_override` (so it is available to the worker) | A-consumed | the proof uses this axiom's `Ensures(connections_handed_off(server))`. The capability certifies the control-flow effect "the server was configured to accept the set"; pre-patch the constructor cannot accept the kwarg (TypeError), so the step is impossible and the capability unobtainable. The underlying primitive (storing a supplied reference) is unchanged Python; the patch adds the parameter+store. G-AX (axiom_check.py R3) drives the REAL Django constructor with `patch.diff` applied and confirms it accepts+stores the set (and, unpatched, that it rejects it). |
| A3 | `for i: if has_override[i]: tokens[i] = override_tokens[i]` (install the available set into the registry) | `if self.connections_override: for alias, conn in ...: connections[alias] = conn` | I (over R-typed carriers) | identical control/data flow: install each supplied connection into the worker registry; aliases with no supplied connection untouched. The `if self.connections_override:` truthiness guard is the per-alias `has_override[i]` test under the parallel-list refinement. This is the *secondary value-level* facet (the `tokens[i]==override_tokens[i]` postcondition); the *discriminating* facet is A2's capability. |
| A4 | (the trailing `super().process_request_thread(...)` is a no-op on the registry; not emitted in the model) | `super().process_request_thread(request, client_address)` | A-reference | the inherited `socketserver.ThreadingMixIn.process_request_thread` handles the request and does not undo the installation (mapping.md §3.3). The model performs no registry op after the install; G-AX confirms the inherited primitive handles the request without altering the installed registry. |

The discriminating content — *the server must be configurable with the
parent-supplied set so it reaches the worker* — lives in
`Ensures(connections_handed_off(server))`. The capability is an abstract
`@ContractOnly @Predicate` with no body: it cannot be `Fold`ed into existence
(Nagini rejects `abstract.predicate.fold`) and a capability for another server
does not discharge it, so the ONLY way a verifying impl can satisfy it is to run
`accept_connection_set` (A2). `model_prepatch.py` reproduces the pre-patch server
that cannot be configured with the set (it omits A2) and **fails** exactly that
postcondition (G-DIFF) — mirroring the real pre-patch `TypeError` that fails all
17 F2P tests.

## B. Connection teardown — `close_request` (secondary, non-F2P)

Gold hunks (added):
```python
def _close_connections(self):
    connections.close_all()

def close_request(self, request):
    self._close_connections()
    super().close_request(request)
```

Modeled by `teardown_request(closed, tokens, request)`. This is the publicly
reported behaviour (the issue is "connections aren't closed after each thread"),
faithful to the gold, but NOT an F2P discriminator: its F2P test
(`test_closes_connections`) is skipped on the in-memory-sqlite eval backend.

| # | model.py impl op (`teardown_request`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the registry is `closed: List[bool]` + `tokens: List[int]` over aliases | `connections` (the `{alias: conn}` per-thread registry) | R | registry ↔ parallel lists indexed by alias position. `closed[i]` ↔ `connections[alias]` is closed; `tokens[i]` ↔ its connection identity. |
| B2 | the loop `for i: closed[i] = True` (`_close_connections`-equivalent) | `self._close_connections()` → `connections.close_all()` | A-reference | the close-all step is modelled **deeply** as "every connection becomes closed". `close_all`'s real loop (`django/db/utils.py:207`) is validated == this deep model by axiom_check.py R2. No consumed axiom. |
| B3 | `request.released = True` | `super().close_request(request)` | A-reference | the inherited `socketserver.TCPServer.close_request` does `request.close()` only and never touches connections (mapping.md §3.1). Modeled as the single `released` write; axiom_check.py R1 drives the real CPython primitive and asserts it releases the request but closes no connection. |
| B4 | the close loop precedes the `released` write | `_close_connections()` precedes `super().close_request(...)` | I | the model orders the close loop before the release write, identically to the gold's `_close_connections()` before `super().close_request(...)`. The *spec* does not assert ordering (close and release touch disjoint resources, so the two writes commute); this row records the impl-skeleton ordering only, which matches the gold textually. |

The connection-closing content lives in `Ensures(Forall i: closed[i] == True)`.
`model_prepatch_2.py` reproduces the pre-patch server that inherits only the
request primitive (drops B2) and **fails** exactly that postcondition (G-DIFF).

### B5. Documented exclusion: the *per-element* frame-mutation rival on `tokens`
### cannot be judged by this verifier (prover resource death), so the same
### violation is probed once, before the close loop

The battery's mandatory frame-mutation probe on `teardown_request`
(`frame-mutate-tokens-teardown`) writes through the read-only (`Acc(...,1/2)`)
`tokens` reference, which must fail for **insufficient permission**. It used to do
that per element, inside the close loop:

```python
        closed[i] = True
        tokens[i] = 0          # store through a 1/2 reference
        i = i + 1
```

That file **reaches no verdict at all** on this toolchain, reproducibly:

| run | cap | wall | outcome |
|---|---|---|---|
| G-PBT (recorded) | ≥590s | 578.5s / 589.2s / 590.0s | `ProverInteractionFailed` — no verdict |
| direct `nagini_verify.sh` (store 2nd in body) | 1500s | 593s, 630s | same crash |
| direct `nagini_verify.sh` (store 1st in body) | 900s | 528s | same crash |

Evidence that this is a **prover resource death and not a refusal to judge, and
not a wall-clock cap**:

* Silicon's message is `viper.silicon.reporting.ProverInteractionFailed:
  Interaction with prover yielded null. This might indicate that the prover
  crashed.` — raised at `ProverStdIO.readLineFromInput` after
  `assertUsingPushPop`, i.e. silicon read EOF from the prover's pipe.
* Sampled every 10s, the Z3 child's RSS climbs monotonically (0.7 GB at 20s →
  10.7 GB at 220s → **20.4 GB** at the last sample) and then the process is gone.
  Nothing bounds it artificially: `ulimit -v/-m` are unlimited and the cgroup's
  `memory.max` is `max`, so the prover is exhausting the host, not hitting a
  configured limit. A larger `timeout_seconds` therefore cannot help — the prover
  dies ~590s in, long before any cap this corpus uses would fire.
* The java stack puts the death inside `consumer.evalAndAssert` under
  `executionFlowController.tryOrFail` (the state-consolidation **retry** of the
  failing permission assertion), with dozens of nested `joiner.join` /
  `evals2` frames — the retry is re-evaluating this loop's whole-range framing
  invariant `Forall k: 0 <= k < len(tokens) => tokens[k] == Old(tokens[k])` in a
  state whose permission for `tokens` has just been exhausted.
* It is specific to that position, not to the violation: the same store hoisted
  out of the loop is judged in 28.6s / 43.1s, and the *serve*-side in-loop stores
  through 1/2 references (`override_tokens[i] = tokens[i]`,
  `has_override[i] = False`) are judged in 54.3s / 29.4s. The trigger is storing
  into the fractional list inside a loop whose invariant pins that list's **whole
  range** against `Old`.

The case is therefore **re-expressed, not deleted**: the identical violation is
performed once, before the close loop, and the close loop plus every gold
invariant is kept verbatim.

```python
    if len(tokens) > 0:
        tokens[0] = 0
```

Measured outcome (two runs, 28.6s and 43.1s): `Verification failed` —
`The precondition of tokens[0] = 0 might not hold. There might be insufficient
permission.` The rejection source is the permission system, exactly as the probe
requires.

The `len(tokens) > 0` guard is there for **attribution**, not to soften the
obligation: it discharges the in-bounds conjunct of `__setitem__`'s precondition
so permission is the only conjunct that can fail (an unguarded `tokens[0] = 0`
could be turned down on bounds and would then attest nothing about the frame).
Both branches are feasible — a zero-length registry is admitted by the
precondition — so the store lies on a path silicon actually explores and judges;
it is not an infeasible guard leaving the obligation vacuous.

**Control that the guard is innocent** (the analogue of dropping `Assert(False)`
into the branch to show it is reachable and load-bearing): the same file with the
STORE replaced by a READ through the same 1/2 reference in the same branch,

```python
    if len(tokens) > 0:
        probe = tokens[0]  # type: int
        Assert(probe == tokens[0])
```

**verifies** — `Verification successful`, 24.8s. So the branch shape costs the
proof nothing and the rejection recorded for this case is attributable solely to
the store, i.e. to the permission system. What is genuinely
lost relative to the in-loop form is only the *multiplicity* of the violation
(one store instead of one per alias); a single store through a 1/2 reference is
already a permission violation, so the weakness class (frame mutation on the
read-only connection-identity list) remains covered.

Compensating strengthening, added in the same pass: `frame-mutate-flags-serve`
probes the third read-only carrier, `has_override`, which had no frame rival.
Clearing `has_override[i]` is the write a *hollow* spec would admit — with the
flags cleared the install pin `Forall i: has_override[i] => tokens[i] ==
override_tokens[i]` has no hypothesis left to discharge, and the untouched pin is
satisfied by an implementation that installs nothing, so under full permission
that rival would **verify while handing no parent-supplied connection to the
worker thread**. Measured: rejected in 29.4s with `The precondition of
has_override[i] = False might not hold. There might be insufficient permission.`

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. There is exactly one
**A-consumed** axiom: `accept_connection_set` (A2), whose `Ensures` grants the
discriminating capability `connections_handed_off(server)`. It is NOT the
function under specification (that is `serve_request_on_worker`) and it is NOT a
re-imagining of the changed algorithm: it abstracts the control-flow effect of
the added constructor accepting the parent-supplied set, the only thing that
distinguishes the fixed server from one that cannot be configured at all. The
install step (A3) and the close step (B2) — the operations that change the
registry — are modelled **deeply** (the per-alias state transitions
`tokens[i] = override_tokens[i]` and `closed[i] = True`), not hidden behind an
axiom. The remaining axiomatized-by-reference callees are the **unchanged**
primitives the new code delegates to: `connections.close_all`'s loop (B2),
`TCPServer.close_request` (B3), and `ThreadingMixIn.process_request_thread` (A4).

## C2. Impl-region attack surface (for auditors): the two universal vacuity
## routes are closed by the harness, not by this spec

Two same-spec "wrong impl" shapes deserve explicit note because they are
spec-independent verifier escapes, not weaknesses of this contract:

- **`Assume(...)` / `Refute(...)` vacuity.** An impl region containing
  `Assume(False)` discharges ANY postcondition vacuously — for every spec in
  the benchmark, not just this one. These call spellings are **banned tokens**
  for the nagini backend (`src/swebench_unified/backends/nagini.py
  banned_tokens=("Assume(", "Refute(")`), and G-HYGIENE mechanically rejects
  any model containing them (`banned calls: ['Assume']`). An attack that
  verifies only via a banned token is therefore not an admissible counterexample:
  the harness's hygiene screen, which pre-clears the impl region, excludes it.
  (Precedent: the django__django-11885 nagini audit reached exactly this
  disposition and recorded SOUND.)
- **Self-recursive capability forging.** Obtaining
  `connections_handed_off(server)` from the function's own postcondition via a
  recursive self-call is rejected by the verifier itself: the spec's
  `MustTerminate` obligations require every callee's measure to be strictly
  smaller than the caller's, so a same-measure self-call fails the obligation
  check (confirmed: such an impl does not verify against this spec).

Neither route is available to a genuinely-wrong terminating implementation;
the load-bearing rejections are the capability postcondition (A2) and the
value-level pins (A3/B2), exercised case-by-case in `properties.py`.

## D. verify(model) ⇒ resolved

`serve_request_on_worker` verifies only if `connections_handed_off(server)` holds
in its postcondition, which is obtainable ONLY by running the configuration step
`accept_connection_set` (A2) — by R, the gold `__init__` accepting and storing
`connections_override`. The pre-patch server cannot run that step (its
constructor rejects the kwarg → `TypeError`), so `model_prepatch.py` fails the
clause, exactly as the 17 F2P tests fail pre-patch. The secondary install (A3)
and teardown-close (B2) are modelled deeply and validated == the real callees by
G-AX. The trust points are the two of PLAN §1.1: axiom soundness (A2's capability
plus the A-reference callees — axiom_check.py / G-AX) and refinement fidelity
(this document, G-EQ). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the gold
patch resolves (G-RESOLVE).
