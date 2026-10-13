# RELAXED-LEAKAGE ACCEPTANCE: django__django-14011

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** This instance is a `problem_statement <-> gold` MISMATCH between
the publicly-reported symptom and the behaviour the F2P tests actually flip.

The `problem_statement` reports ONLY a connection-CLOSING symptom:
"LiveServerTestCase's ThreadedWSGIServer doesn't close database connections
after each thread" — a race condition that ends a test run with
`OperationalError: database "..." is being accessed by other users`. That
publicly-named behaviour (closing DB connections on request teardown) is NOT a
resolution discriminator on the eval backend: its dedicated test
`servers.tests.LiveServerTestCloseConnectionTest.test_closes_connections` is
SKIPPED on in-memory sqlite (the gold's second hunk,
`django/db/backends/sqlite3/features.py`, adds it to `django_test_skips`), and it
is not in the FAIL_TO_PASS list.

The actually-tested F2P discriminator is the **connection hand-off / thread-
sharing** behaviour: the gold makes `ThreadedWSGIServer.__init__` accept and
store a parent-supplied `connections_override` set, and `process_request_thread`
install it into the worker thread's connection registry. Pre-patch, the test
harness's `setUpClass` calls `_create_server(..., connections_override=...)` and
hits a constructor that does not accept that keyword -> `TypeError` -> all 17 F2P
tests error in `setUpClass`. So a *faithful* spec (one whose prepatch fails and
no wrong impl verifies — G-EQ / G-DIFF) MUST pin the configuration-acceptance /
hand-off behaviour.

That hand-off / thread-sharing vocabulary lives ONLY in `hints_text` / the gold
internals / the hidden `test_patch`, NEVER in the solver-visible
`problem_statement`. Therefore a spec that is faithful (pins the tested
discriminator) cannot be non-leaking (directive 6, judged against
`problem_statement` only), and a spec that is non-leaking cannot pin the gold
behaviour: faithful + non-leaking is provably impossible. This is a genuine
PS<->gold mismatch, not lazy docstring narration — the *behaviour itself* is the
leak.

The verification CORE is fully SOUND (G-VERIFY / G-DIFF / G-EQ / G-AX /
faithfulness clean, and `patch.diff == gold` so G-RESOLVE is expected to
resolve), so this is a relaxed-leak, not a defect-in-spec. In this unified repo
the policy lives in the binding spec-construction rules,
`prompts/nagini/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
... for a proven `problem_statement ↔ gold` mismatch where the gold's tested
discriminator exists only in `hints_text`/gold internals, so a *faithful* spec
MUST name it ... KEEP the instance with the leak allowed"). Such instances are
KEPT in the verified set with the hints/gold-derived discriminator allowed in
the spec view, rather than excluded. The `verify => correct` guarantee is
UNAFFECTED; only the secondary no-leakage property is relaxed.

## Why the hand-off leak is genuinely unavoidable (not lazy de-narration)

The behaviour the gold actually fixes for the F2P tests — and that the test
harness measures — IS the leaked discriminator. There is no way to pin it
without naming the configuration-acceptance / parent-supplied-set / hand-off
idea, none of which the public issue ever raises.

### The gold's tested discriminator is the constructor accepting the set

Gold patch (`django/core/servers/basehttp.py`, the methods added to
`ThreadedWSGIServer`):

```python
class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    """A threaded version of the WSGIServer"""
    def __init__(self, *args, connections_override=None, **kwargs):   # <-- the tested discriminator
        super().__init__(*args, **kwargs)
        self.connections_override = connections_override

    def process_request_thread(self, request, client_address):
        if self.connections_override:
            # Override this thread's database connections with the ones
            # provided by the parent thread.
            for alias, conn in self.connections_override.items():
                connections[alias] = conn
        super().process_request_thread(request, client_address)

    def _close_connections(self):
        connections.close_all()                                       # the PUBLICLY-reported facet

    def close_request(self, request):
        self._close_connections()
        super().close_request(request)
```

The publicly-reported facet is `close_request` -> `_close_connections` ->
`connections.close_all()`. But the F2P tests never reach a backend where that is
observable (sqlite skip). What the 17 F2P tests DO require is that the harness
can construct `ThreadedWSGIServer(..., connections_override=...)` at all — i.e.
the constructor accepting/storing the parent-supplied set and the worker
installing it. That is the connection hand-off / thread-sharing behaviour.

### The hand-off discriminator is absent from the solver-visible problem_statement

Token check against `problem_statement` (solver-visible) vs. `hints_text` /
`test_patch` (never shown to the consumer):

| token / concept                              | problem_statement | hints_text | test_patch |
|----------------------------------------------|:-----------------:|:----------:|:----------:|
| close database connections (the symptom)     | present           | present    | present    |
| `connections_override`                       | absent            | absent     | present    |
| parent-supplied / parent thread              | absent            | absent     | present    |
| "thread-sharing" (the diagnosis)             | absent            | present    | absent     |
| configurable / accept the set                | absent            | absent     | absent     |
| override / install into the registry         | absent            | absent     | present    |
| `process_request_thread`                     | absent            | present    | present    |
| `__init__` accepts a kwarg                   | absent            | absent     | present    |
| `_create_server(connections_override=...)`   | absent            | absent     | present    |

The `problem_statement` is a connection-leak SYMPTOM report (a race condition
ending in `OperationalError`). It diagnoses only "doesn't close database
connections after each thread." The "thread-sharing needed for SQLite" idea
appears only in `hints_text` ("I wonder if it's also a problem that
ThreadingMixIn doesn't implement the same thread-sharing logic that
LiveServerThread does, which is needed for SQLite"), and the concrete
`connections_override` plumbing — the constructor kwarg, the parent-supplied
set, the worker installing it — appears only in the hidden `test_patch` and the
gold diff.

### Any faithful, G-DIFF-failing spec must name the hand-off

The model's spec view discloses, in its docstring and the primary discriminating
postcondition, the connection hand-off into the worker thread: that "the server
must be configurable with a parent-supplied set of connections, and that
supplied set must reach the worker thread," modelled as the unforgeable
per-server capability `connections_handed_off(server)`. This is load-bearing:
`model_prepatch.py` (the server that cannot be configured to accept the set)
FAILS exactly on `Ensures(connections_handed_off(server))` (model.py line 160),
which is the encoding of the real pre-patch `TypeError` in `setUpClass` that
errors all 17 F2P tests. Dropping it lets the pre-patch server verify. There is
no `problem_statement`-derivable reformulation of the hand-off because the public
issue is about connection-CLOSING only (which is itself untested on the eval
backend). The behaviour itself is the leak — a genuine PS<->gold mismatch, not
lazy docstring narration.

Note: the spec view correctly still avoids the patched path / symbol names
(`basehttp.py`, `features.py`, `ThreadedWSGIServer`, `connections_override`,
`process_request_thread`, `close_request`, `__init__`). Model identifiers
(`serve_request_on_worker`, `accept_connection_set`, `connections_handed_off`,
`teardown_request`, `has_override`, `override_tokens`) describe behaviour, not
the edit. The leak is SEMANTIC (the hand-off concept), not lexical — so the
mechanical G-LEAK screen passes, exactly as the relaxed-leakage exception in
`prompts/nagini/spec_guide.md` directive 6 predicts. The adversarial
reconstruction (G-PANEL attacker 3) independently re-verifies the disposition;
per the panel recording convention above, its honest recording for this
properly-dispositioned facet is NO-LEAKAGE (pass) + note, with LEAKAGE reserved
for a NEW leak beyond the facet or a broken disposition.

## Re-verify snapshot (soundness intact — this is a relaxed-leak, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies, no flags, ~31s < 300s, `float_encoding: null`.
- G-DIFF: PASS — `model_prepatch.py` (the server that cannot be configured to
  accept the parent-supplied set) FAILS on the discriminating postcondition
  `connections_handed_off(server)` (line 160; the tested F2P discriminator);
  `model_prepatch_2.py` (inherited teardown that does not close connections)
  FAILS on `closed[i] == True` (lines 220-221; secondary non-F2P facet).
- same_spec: TRUE — axioms / pure / pre-conditions / post-conditions
  byte-identical across `model.py` + both prepatch files (only the impl skeleton
  and its proof invariants differ).
- Static gates (G-INTEGRITY / G-HYGIENE / mechanical G-LEAK): pass. The
  mechanical G-LEAK screen is lexical and blind to this semantic hand-off leak.
- G-AX: SOUND. `axiom_check.py` returns RC=0 in the pinned eval container: R3
  applies `patch.diff` into `/testbed`, reloads `django.core.servers.basehttp`,
  and confirms the real fixed `__init__` accepts+stores `connections_override`
  and `process_request_thread` installs it (and, unpatched, that constructing
  with the kwarg raises `TypeError`); R1 (stdlib `TCPServer.close_request`
  releases the request only) and R2 (`connections.close_all` closes every
  registry connection) validated.
- G-EQ: SOUND/tight. The discriminating capability `connections_handed_off` is an
  opaque `@ContractOnly @Predicate` with no body — it cannot be Fold-ed or echoed
  (directive 8), its sole producer is `accept_connection_set`, and a capability
  for another server does not discharge it; it is load-bearing alongside the
  grounded value-level install postcondition. Refinement rows all
  R / A-consumed / A-reference / I; no kind-3.

## Conclusion

No prescribed code fix exists for the leakage axis (the hand-off facet's tested
behaviour is itself the leak). Per the relaxed-leakage policy the correct action
is to KEEP this instance in the verified set with the leak documented and
`meta.json gates.G-LEAK.status = "relaxed"`. The `verify => correct` guarantee is
fully intact.
