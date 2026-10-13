# P2 adversarial audit — django__django-14011

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,6 @@
     # impl-start
     # Configure the server so the parent-supplied set is available to this
     # worker (the configuration step that accepts the set).
-    accept_connection_set(server, has_override, override_tokens)
     # Make the available parent-supplied connections take effect in this worker
     # thread's registry.
     i = 0
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,8 +199,7 @@
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(tokens),
                                                   tokens[k] == Old(tokens[k])))))
         # invariants-end
-        if has_override[i]:
-            tokens[i] = override_tokens[i]
+        # (install omitted)
         i = i + 1
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -237,7 +237,7 @@
     # impl-start
     # Close every connection in this worker thread's registry.
     i = 0
-    while i < len(closed):
+    while i < len(closed) - 1:
         # invariants-start
         Invariant(list_pred(closed))
         Invariant(Acc(list_pred(tokens), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,8 +199,7 @@
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(tokens),
                                                   tokens[k] == Old(tokens[k])))))
         # invariants-end
-        if has_override[i]:
-            tokens[i] = override_tokens[i]
+        tokens[i] = override_tokens[i]
         i = i + 1
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -256,5 +256,5 @@
         i = i + 1
     # Release the request resource (the inherited request cleanup, which releases
     # the request resource only and does NOT touch the registry).
-    request.released = True
+    # release omitted
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -252,7 +252,7 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   closed[k] == True))))
         # invariants-end
-        closed[i] = True
+        # close omitted
         i = i + 1
     # Release the request resource (the inherited request cleanup, which releases
     # the request resource only and does NOT touch the registry).
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,8 @@
     # impl-start
     # Configure the server so the parent-supplied set is available to this
     # worker (the configuration step that accepts the set).
-    accept_connection_set(server, has_override, override_tokens)
+    other = Server()
+    accept_connection_set(other, has_override, override_tokens)
     # Make the available parent-supplied connections take effect in this worker
     # thread's registry.
     i = 0
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,7 @@
     # impl-start
     # Configure the server so the parent-supplied set is available to this
     # worker (the configuration step that accepts the set).
-    accept_connection_set(server, has_override, override_tokens)
+    serve_request_on_worker(server, tokens, has_override, override_tokens)
     # Make the available parent-supplied connections take effect in this worker
     # thread's registry.
     i = 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14011.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A threaded request server runs each request on its own worker thread, and each
  worker thread keeps a per-thread registry of live database connections. For the
  worker threads to operate on the SAME data the parent prepared (rather than on
  fresh, empty connections of their own), the server must be configurable with a
  parent-supplied set of connections, and that supplied set must reach the worker
  thread. Two guarantees describe the worker-thread lifecycle.

  (1) Connection hand-off into the worker thread (the discriminating behaviour).
      The server can be CONFIGURED with a parent-supplied set of connections.
      Configuration is a step that can FAIL: a server that cannot be configured
      with such a set leaves it UNAVAILABLE, and then nothing the worker does can
      make the parent-supplied connections reach the worker thread's registry.
      The desired behaviour is therefore: configuring the server with the
      parent-supplied set must SUCCEED, so that the set becomes available; and a
      worker thread, when handling a request, makes the available parent-supplied
      connections take effect in its registry (each supplied alias's entry is set
      to the supplied connection; aliases with no override are left as they were).
      A server whose configuration did not make the set available cannot have a
      worker that operates on the parent-supplied connections.

  (2) Connection teardown after a request (a secondary, non-discriminating
      behaviour). When the server finishes cleaning up an individual request,
      every database connection in that worker thread's registry must be left
      CLOSED, and the request resource itself must be released. Releasing the
      request resource alone is not sufficient: a connection that was still open
      when the request finished must end up closed. The connections are closed
      BEFORE the request resource is released.

Modelling choices (Nagini fragment):
  * A worker thread's connection registry is modelled as two index-aligned
    `List`s over the registry's aliases: `closed[i]` (a `bool`: is alias i's
    connection currently closed?) and `tokens[i]` (an `int`: the identity of the
    connection object currently bound to alias i). Aliases are positions.
  * The "request resource" is a minimal object carrying only its released flag.
  * The parent-supplied set is an index-aligned pair: `has_override[i]` (was a
    connection supplied for alias i?) and `override_tokens[i]` (the identity of
    the supplied connection for alias i).
  * "The server was configured so the parent-supplied set is available to the
    worker" is NOT a copyable value (configuring either succeeds or fails; the
    stored references would look identical either way, so no value witnesses it).
    It is modelled as an abstract, unforgeable per-server CAPABILITY
    `connections_handed_off(server)` -- an opaque `@ContractOnly @Predicate` with
    no body. Nothing can `Fold` it into existence, and a capability for some other
    server does not discharge it. Its SOLE producer is the configuration step
    (`accept_connection_set`'s `Ensures`): the capability can be held only by
    actually performing the configuration that accepts the supplied set. The
    worker-handling step REQUIRES it, so a worker can operate on the
    parent-supplied connections only when the server was configured to accept
    them -- exactly the control-flow effect that distinguishes a server able to
    accept the set from one that cannot be configured with the set at all.
  * Closing every connection in the registry is modelled deeply as the per-alias
    state transition "every connection becomes closed"; the unchanged
    request-release primitive only releases the request and never touches the
    registry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Server:
    """The worker request server. It carries no readable configuration value:
    whether it was configured to accept the parent-supplied connection set is the
    abstract per-server capability `connections_handed_off(server)` below, not a
    field an implementation could copy or set by fiat."""

    def __init__(self) -> None:
        Ensures(True)

# axioms-start
# Abstract, unforgeable per-server capability: holding `connections_handed_off(s)`
# means server `s` was CONFIGURED so the parent-supplied connection set is
# available to its worker threads. It is an opaque `@ContractOnly @Predicate` with
# NO body. Consequences:
#   * an implementation cannot `Fold` it into existence (no body to fold), so the
#     "configured / available" fact cannot be fabricated by fiat;
#   * it names the specific server `s`, so a capability obtained for a different
#     server does not discharge `connections_handed_off(s)`.
# The SOLE producer is `accept_connection_set`'s `Ensures` (the configuration
# step that accepts the supplied set). This is the directive-8 / control-flow
# grounding of the "available" fact: configuring a server with the set either
# succeeds (capability granted) or is impossible (a server that cannot be
# configured with the set), with no value-level witness either way. Provenance +
# executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def connections_handed_off(server: Server) -> bool:
    pass

@ContractOnly
def accept_connection_set(
    server: Server, has_override: List[bool], override_tokens: List[int]
) -> None:
    """The configuration step: it ACCEPTS the parent-supplied connection set and
    makes it available to the server's worker threads. The underlying primitive
    is storing a supplied reference (an unchanged operation); what is pinned here
    is that the server is actually configured to accept the set. On success it
    grants the per-server capability `connections_handed_off(server)` -- it is the
    SOLE producer of that capability, the evidence that the supplied set was
    accepted at configuration. A server that cannot be configured with the set
    (the configuration is impossible / rejects the set) does not run this step and
    so never holds the capability. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(has_override) == Old(len(has_override)))
    Ensures(len(override_tokens) == Old(len(override_tokens)))
    Ensures(connections_handed_off(server))
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class Request:
    def __init__(self) -> None:
        Ensures(Acc(self.released) and self.released == False)  # type: ignore
        self.released = False  # type: bool

def serve_request_on_worker(
    server: Server,
    tokens: List[int],
    has_override: List[bool],
    override_tokens: List[int],
) -> None:
    # pre-conditions-start
    # The registry identities are mutated (the available set takes effect); the
    # supplied-set lists are read-only at fractional permission.
    # Terminates: handling is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(tokens))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Requires(len(tokens) == len(has_override))
    Requires(len(tokens) == len(override_tokens))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(tokens))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(tokens) == Old(len(tokens)))
    Ensures(len(tokens) == len(has_override))
    Ensures(len(tokens) == len(override_tokens))
    # (1, discriminating) The worker operates on the parent-supplied connections
    # ONLY because the server was configured to accept the set: the result must
    # carry the per-server capability `connections_handed_off(server)`. Because
    # that capability is unforgeable and produced only by the configuration step,
    # a server that cannot be configured with the set can never discharge this --
    # it is the control-flow effect required of a configurable server.
    Ensures(connections_handed_off(server))
    # (1, secondary value-level) Where the supplied set is available, each
    # supplied alias's entry in the registry takes the supplied connection, and
    # aliases with no supplied connection are left as they were.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and has_override[i],
                                            tokens[i] == override_tokens[i]))))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and not has_override[i],
                                            tokens[i] == Old(tokens[i])))))
    # post-conditions-end
    # impl-start
    # Configure the server so the parent-supplied set is available to this
    # worker (the configuration step that accepts the set).
    accept_connection_set(server, has_override, override_tokens)
    # Make the available parent-supplied connections take effect in this worker
    # thread's registry.
    i = 0
    while i < len(tokens):
        # invariants-start
        Invariant(list_pred(tokens))
        Invariant(Acc(list_pred(has_override), 1 / 2))
        Invariant(Acc(list_pred(override_tokens), 1 / 2))
        Invariant(connections_handed_off(server))
        Invariant(len(tokens) == Old(len(tokens)))
        Invariant(len(tokens) == len(has_override))
        Invariant(len(tokens) == len(override_tokens))
        Invariant(0 <= i and i <= len(tokens))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(tokens) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and has_override[k],
                                                  tokens[k] == override_tokens[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not has_override[k],
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        # invariants-end
        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1
    # impl-end

def teardown_request(closed: List[bool], tokens: List[int], request: Request) -> None:
    # pre-conditions-start
    # The registry's closed-flags are fully owned (they are mutated). The
    # connection-identity list is read-only here, held at fractional permission.
    # Terminates: cleanup is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(closed))
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(closed) == len(tokens))
    Requires(Acc(request.released))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(closed))
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(len(closed) == Old(len(closed)))
    Ensures(len(closed) == len(tokens))
    Ensures(Acc(request.released))
    # The registry is left over the same connection identities (teardown does
    # not create or rebind connections, it only closes them).
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens),
                                            tokens[i] == Old(tokens[i])))))
    # (2a) Every connection in the registry is left closed.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(closed),
                                            closed[i] == True))))
    # (2b) The request resource is released.
    Ensures(request.released == True)
    # post-conditions-end
    # impl-start
    # Close every connection in this worker thread's registry.
    i = 0
    while i < len(closed):
        # invariants-start
        Invariant(list_pred(closed))
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(len(closed) == Old(len(closed)))
        Invariant(len(closed) == len(tokens))
        Invariant(0 <= i and i <= len(closed))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(closed) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  closed[k] == True))))
        # invariants-end
        closed[i] = True
        i = i + 1
    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry).
    request.released = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14011 (nagini). Focus on A-legs + model↔patch correspondence per assignment.

Ran adversary via python -m swebench_unified.adversary with and SBU_BENCHMARK_DIR=benchmark-verified. Verifier: bash scripts/nagini_verify.sh.

SPEC SHAPE: serve_request_on_worker and teardown_request both FULLY PIN observable final state via Forall postconditions (each override alias -> override_tokens; non-override alias -> Old; every closed[i]==True; request.released==True; tokens identity preserved in teardown). serve additionally REQUIRES the unforgeable abstract capability Ensures(connections_handed_off(server)) whose SOLE producer is accept_connection_set (@ContractOnly @Predicate, no body -> cannot Fold). MustTerminate obligations on both functions and the axiom.

ATTACK SUITE (8 distinct same-spec wrong impls; edited ONLY impl regions, axioms/@Pure/Requires/Ensures byte-identical). same-spec: all 8 exit 0 (SAME). weakness command: all 8 exit 2 = NOT-A-COUNTEREXAMPLE (verification failed). Genuine, distinct spec-relevant failures (from verifier logs):
  atk_1 (prepatch bug / omit accept_connection_set): loop invariant 'insufficient permission to access connections_handed_off(server)' (capability undischargeable) — reproduces the real pre-patch TypeError-fails-all-17-F2P.
  atk_2 (partial-domain: accept but skip install): loop invariant Forall(has_override[k] -> tokens[k]==override_tokens[k]) not preserved.
  atk_3 (boundary off-by-one: while i < len(closed)-1): postcondition Forall closed[i]==True fails (last connection open).
  atk_4 (wrong-install: unconditional tokens[i]=override_tokens[i]): invariant Forall(not has_override[k] -> tokens[k]==Old) not preserved.
  atk_5 (teardown omit release): postcondition request.released==True fails.
  atk_6 (control-flow-effect: release but skip close loop): invariant Forall closed[k]==True not preserved.
  atk_7 (ungrounded-oracle echo: accept_connection_set on a DIFFERENT Server()): obligation leak / capability held for 'other' not 'server' -> Ensures(connections_handed_off(server)) undischarged.
  atk_8 (self-recursive capability forge): MustTerminate obligation-leak check rejects the same-measure self-call (matches refinement.md §C2).

ZERO CANDIDATES => no verifying wrong impl exists => no faithful refined patch to materialize/run through run_resolve (task vacuous by construction; nothing to falsify).

POSITIVE CONTROL: model.py verifies (nagini_verify exit 0). PREPATCH: model_prepatch.py is same-spec (exit 0) and atk_1 (its impl skeleton) fails exactly the capability postcondition — prepatch bug reproduced.

REFINEMENT.MD AUDIT (A-legs + correspondence): every leg is R / A-consumed / A-reference / I; NO kind-3 (unexpressible-changed-op). Exactly one A-consumed axiom A2 accept_connection_set -> the added __init__(*, connections_override=None) accepting+storing the set (verbatim in patch.diff lines 16-18). A-references: A4 process_request_thread trailing super() (registry no-op), B2 close_all deep model (django/db/utils.py loop), B3 TCPServer.close_request (releases request only). The two registry-changing ops (A3 install, B2 close) are modelled DEEPLY, not axiomatized. patch.diff read and matches mapping.md/refinement.md exactly (basehttp.py 4 added members + sqlite3/features.py skip-set line — test-infra, unmodeled, correctly noted non-F2P). axiom_check.py executed on host: exit 0, 'G-AX OK: R1+R2+R3' (R3 host-fallback structural since Django not importable outside container; R1/R2 checked against real stdlib socketserver + close_all loop reproduction).

VERDICT: SOUND. >=5 distinct attacks (8) all run and mechanically confirmed NOT-A-COUNTEREXAMPLE; positive control verifies; prepatch reproduced; refinement legs all R/A/I with A-leg correspondence holding. No verify-but-wrong impl found; verify=>correct not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14011.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A threaded request server runs each request on its own worker thread, and each
  worker thread keeps a per-thread registry of live database connections. For the
  worker threads to operate on the SAME data the parent prepared (rather than on
  fresh, empty connections of their own), the server must be configurable with a
  parent-supplied set of connections, and that supplied set must reach the worker
  thread. Two guarantees describe the worker-thread lifecycle.

  (1) Connection hand-off into the worker thread (the discriminating behaviour).
      The server can be CONFIGURED with a parent-supplied set of connections.
      Configuration is a step that can FAIL: a server that cannot be configured
      with such a set leaves it UNAVAILABLE, and then nothing the worker does can
      make the parent-supplied connections reach the worker thread's registry.
      The desired behaviour is therefore: configuring the server with the
      parent-supplied set must SUCCEED, so that the set becomes available; and a
      worker thread, when handling a request, makes the available parent-supplied
      connections take effect in its registry (each supplied alias's entry is set
      to the supplied connection; aliases with no override are left as they were).
      A server whose configuration did not make the set available cannot have a
      worker that operates on the parent-supplied connections.

  (2) Connection teardown after a request (a secondary, non-discriminating
      behaviour). When the server finishes cleaning up an individual request,
      every database connection in that worker thread's registry must be left
      CLOSED, and the request resource itself must be released. Releasing the
      request resource alone is not sufficient: a connection that was still open
      when the request finished must end up closed. The connections are closed
      BEFORE the request resource is released.

Modelling choices (Nagini fragment):
  * A worker thread's connection registry is modelled as two index-aligned
    `List`s over the registry's aliases: `closed[i]` (a `bool`: is alias i's
    connection currently closed?) and `tokens[i]` (an `int`: the identity of the
    connection object currently bound to alias i). Aliases are positions.
  * The "request resource" is a minimal object carrying only its released flag.
  * The parent-supplied set is an index-aligned pair: `has_override[i]` (was a
    connection supplied for alias i?) and `override_tokens[i]` (the identity of
    the supplied connection for alias i).
  * "The server was configured so the parent-supplied set is available to the
    worker" is NOT a copyable value (configuring either succeeds or fails; the
    stored references would look identical either way, so no value witnesses it).
    It is modelled as an abstract, unforgeable per-server CAPABILITY
    `connections_handed_off(server)` -- an opaque `@ContractOnly @Predicate` with
    no body. Nothing can `Fold` it into existence, and a capability for some other
    server does not discharge it. Its SOLE producer is the configuration step
    (`accept_connection_set`'s `Ensures`): the capability can be held only by
    actually performing the configuration that accepts the supplied set. The
    worker-handling step REQUIRES it, so a worker can operate on the
    parent-supplied connections only when the server was configured to accept
    them -- exactly the control-flow effect that distinguishes a server able to
    accept the set from one that cannot be configured with the set at all.
  * Closing every connection in the registry is modelled deeply as the per-alias
    state transition "every connection becomes closed"; the unchanged
    request-release primitive only releases the request and never touches the
    registry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Server:
    """The worker request server. It carries no readable configuration value:
    whether it was configured to accept the parent-supplied connection set is the
    abstract per-server capability `connections_handed_off(server)` below, not a
    field an implementation could copy or set by fiat."""

    def __init__(self) -> None:
        Ensures(True)

# axioms-start
# Abstract, unforgeable per-server capability: holding `connections_handed_off(s)`
# means server `s` was CONFIGURED so the parent-supplied connection set is
# available to its worker threads. It is an opaque `@ContractOnly @Predicate` with
# NO body. Consequences:
#   * an implementation cannot `Fold` it into existence (no body to fold), so the
#     "configured / available" fact cannot be fabricated by fiat;
#   * it names the specific server `s`, so a capability obtained for a different
#     server does not discharge `connections_handed_off(s)`.
# The SOLE producer is `accept_connection_set`'s `Ensures` (the configuration
# step that accepts the supplied set). This is the directive-8 / control-flow
# grounding of the "available" fact: configuring a server with the set either
# succeeds (capability granted) or is impossible (a server that cannot be
# configured with the set), with no value-level witness either way. Provenance +
# executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def connections_handed_off(server: Server) -> bool:
    pass

@ContractOnly
def accept_connection_set(
    server: Server, has_override: List[bool], override_tokens: List[int]
) -> None:
    """The configuration step: it ACCEPTS the parent-supplied connection set and
    makes it available to the server's worker threads. The underlying primitive
    is storing a supplied reference (an unchanged operation); what is pinned here
    is that the server is actually configured to accept the set. On success it
    grants the per-server capability `connections_handed_off(server)` -- it is the
    SOLE producer of that capability, the evidence that the supplied set was
    accepted at configuration. A server that cannot be configured with the set
    (the configuration is impossible / rejects the set) does not run this step and
    so never holds the capability. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(has_override) == Old(len(has_override)))
    Ensures(len(override_tokens) == Old(len(override_tokens)))
    Ensures(connections_handed_off(server))
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class Request:
    def __init__(self) -> None:
        Ensures(Acc(self.released) and self.released == False)  # type: ignore
        self.released = False  # type: bool

def serve_request_on_worker(
    server: Server,
    tokens: List[int],
    has_override: List[bool],
    override_tokens: List[int],
) -> None:
    # pre-conditions-start
    # The registry identities are mutated (the available set takes effect); the
    # supplied-set lists are read-only at fractional permission.
    # Terminates: handling is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(tokens))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Requires(len(tokens) == len(has_override))
    Requires(len(tokens) == len(override_tokens))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(tokens))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(tokens) == Old(len(tokens)))
    Ensures(len(tokens) == len(has_override))
    Ensures(len(tokens) == len(override_tokens))
    # (1, discriminating) The worker operates on the parent-supplied connections
    # ONLY because the server was configured to accept the set: the result must
    # carry the per-server capability `connections_handed_off(server)`. Because
    # that capability is unforgeable and produced only by the configuration step,
    # a server that cannot be configured with the set can never discharge this --
    # it is the control-flow effect required of a configurable server.
    Ensures(connections_handed_off(server))
    # (1, secondary value-level) Where the supplied set is available, each
    # supplied alias's entry in the registry takes the supplied connection, and
    # aliases with no supplied connection are left as they were.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and has_override[i],
                                            tokens[i] == override_tokens[i]))))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and not has_override[i],
                                            tokens[i] == Old(tokens[i])))))
    # post-conditions-end
    # impl-start
    # Configure the server so the parent-supplied set is available to this
    # worker (the configuration step that accepts the set).
    accept_connection_set(server, has_override, override_tokens)
    # Make the available parent-supplied connections take effect in this worker
    # thread's registry.
    i = 0
    while i < len(tokens):
        # invariants-start
        Invariant(list_pred(tokens))
        Invariant(Acc(list_pred(has_override), 1 / 2))
        Invariant(Acc(list_pred(override_tokens), 1 / 2))
        Invariant(connections_handed_off(server))
        Invariant(len(tokens) == Old(len(tokens)))
        Invariant(len(tokens) == len(has_override))
        Invariant(len(tokens) == len(override_tokens))
        Invariant(0 <= i and i <= len(tokens))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(tokens) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and has_override[k],
                                                  tokens[k] == override_tokens[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not has_override[k],
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        # invariants-end
        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1
    # impl-end

def teardown_request(closed: List[bool], tokens: List[int], request: Request) -> None:
    # pre-conditions-start
    # The registry's closed-flags are fully owned (they are mutated). The
    # connection-identity list is read-only here, held at fractional permission.
    # Terminates: cleanup is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(closed))
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(closed) == len(tokens))
    Requires(Acc(request.released))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(closed))
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(len(closed) == Old(len(closed)))
    Ensures(len(closed) == len(tokens))
    Ensures(Acc(request.released))
    # The registry is left over the same connection identities (teardown does
    # not create or rebind connections, it only closes them).
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens),
                                            tokens[i] == Old(tokens[i])))))
    # (2a) Every connection in the registry is left closed.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(closed),
                                            closed[i] == True))))
    # (2b) The request resource is released.
    Ensures(request.released == True)
    # post-conditions-end
    # impl-start
    # Close every connection in this worker thread's registry.
    i = 0
    while i < len(closed):
        # invariants-start
        Invariant(list_pred(closed))
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(len(closed) == Old(len(closed)))
        Invariant(len(closed) == len(tokens))
        Invariant(0 <= i and i <= len(closed))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(closed) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  closed[k] == True))))
        # invariants-end
        closed[i] = True
        i = i + 1
    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry).
    request.released = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14011 (nagini). Focus on A-legs + model↔patch correspondence per assignment.

Ran adversary via python -m swebench_unified.adversary with and SBU_BENCHMARK_DIR=benchmark-verified. Verifier: bash scripts/nagini_verify.sh.

SPEC SHAPE: serve_request_on_worker and teardown_request both FULLY PIN observable final state via Forall postconditions (each override alias -> override_tokens; non-override alias -> Old; every closed[i]==True; request.released==True; tokens identity preserved in teardown). serve additionally REQUIRES the unforgeable abstract capability Ensures(connections_handed_off(server)) whose SOLE producer is accept_connection_set (@ContractOnly @Predicate, no body -> cannot Fold). MustTerminate obligations on both functions and the axiom.

ATTACK SUITE (8 distinct same-spec wrong impls; edited ONLY impl regions, axioms/@Pure/Requires/Ensures byte-identical). same-spec: all 8 exit 0 (SAME). weakness command: all 8 exit 2 = NOT-A-COUNTEREXAMPLE (verification failed). Genuine, distinct spec-relevant failures (from verifier logs):
  atk_1 (prepatch bug / omit accept_connection_set): loop invariant 'insufficient permission to access connections_handed_off(server)' (capability undischargeable) — reproduces the real pre-patch TypeError-fails-all-17-F2P.
  atk_2 (partial-domain: accept but skip install): loop invariant Forall(has_override[k] -> tokens[k]==override_tokens[k]) not preserved.
  atk_3 (boundary off-by-one: while i < len(closed)-1): postcondition Forall closed[i]==True fails (last connection open).
  atk_4 (wrong-install: unconditional tokens[i]=override_tokens[i]): invariant Forall(not has_override[k] -> tokens[k]==Old) not preserved.
  atk_5 (teardown omit release): postcondition request.released==True fails.
  atk_6 (control-flow-effect: release but skip close loop): invariant Forall closed[k]==True not preserved.
  atk_7 (ungrounded-oracle echo: accept_connection_set on a DIFFERENT Server()): obligation leak / capability held for 'other' not 'server' -> Ensures(connections_handed_off(server)) undischarged.
  atk_8 (self-recursive capability forge): MustTerminate obligation-leak check rejects the same-measure self-call (matches refinement.md §C2).

ZERO CANDIDATES => no verifying wrong impl exists => no faithful refined patch to materialize/run through run_resolve (task vacuous by construction; nothing to falsify).

POSITIVE CONTROL: model.py verifies (nagini_verify exit 0). PREPATCH: model_prepatch.py is same-spec (exit 0) and atk_1 (its impl skeleton) fails exactly the capability postcondition — prepatch bug reproduced.

REFINEMENT.MD AUDIT (A-legs + correspondence): every leg is R / A-consumed / A-reference / I; NO kind-3 (unexpressible-changed-op). Exactly one A-consumed axiom A2 accept_connection_set -> the added __init__(*, connections_override=None) accepting+storing the set (verbatim in patch.diff lines 16-18). A-references: A4 process_request_thread trailing super() (registry no-op), B2 close_all deep model (django/db/utils.py loop), B3 TCPServer.close_request (releases request only). The two registry-changing ops (A3 install, B2 close) are modelled DEEPLY, not axiomatized. patch.diff read and matches mapping.md/refinement.md exactly (basehttp.py 4 added members + sqlite3/features.py skip-set line — test-infra, unmodeled, correctly noted non-F2P). axiom_check.py executed on host: exit 0, 'G-AX OK: R1+R2+R3' (R3 host-fallback structural since Django not importable outside container; R1/R2 checked against real stdlib socketserver + close_all loop reproduction).

VERDICT: SOUND. >=5 distinct attacks (8) all run and mechanically confirmed NOT-A-COUNTEREXAMPLE; positive control verifies; prepatch reproduced; refinement legs all R/A/I with A-leg correspondence holding. No verify-but-wrong impl found; verify=>correct not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-14011 (nagini). Conclusion: FAITHFUL — no diverging input between the modeled functions and the real repo callees in the modeled domain.

### Machine facts
- same-spec on identical copy of model.py => rc=0 (SAME; spec markers well-formed).
- Pinned Nagini verifier on model.py => exit 0 (18.7s): the bundle model IS a gold-equivalent impl and it verifies against the frozen spec, so the spec is NOT too strong.
- model_prepatch.py (drops accept_connection_set) FAILS exactly Ensures(connections_handed_off(server)) at line 166 => the discriminating clause is load-bearing, not vacuous. model_prepatch_2 (drops close loop) FAILS the 'every connection closed' clause. same-spec rc=0 for both prepatch files (axioms/pure/pre/post byte-identical; only impl+invariants differ).
- Gold patch (patch_gold.diff) confirmed: __init__(*,connections_override=None) stores the set; process_request_thread installs connections[alias]=conn for each override; close_request -> _close_connections()->close_all() then super().close_request().

OP-BY-OP FAITHFULNESS vs base_commit e4430f22:
- serve_request_on_worker <-> __init__(*,connections_override)+process_request_thread. Model pins tokens[i]==override_tokens[i] where has_override[i], else tokens[i]==Old(tokens[i]) — a faithful index-aligned refinement of the dict-keyed unconditional install; untouched-alias preservation matches. connections_handed_off(server) is always granted by accept_connection_set, which models the control-flow fact 'the constructor ACCEPTED the connections_override kwarg' (pre-patch: TypeError) — the sole tested discriminator. This is a config-level fact, NOT 'connections physically installed', which is faithful and not over-strong.
- teardown_request <-> close_request. Model: close-all loop (closed[i]=True) then request.released=True, identities preserved. Matches gold's _close_connections()->close_all() then super().close_request(). Spec does not over-assert ordering (disjoint resources commute).

ABSTRACTION BOUNDARIES (not disagreements): close_all's try/except AttributeError skip of never-created connections and dict semantics for aliases absent from the registry lie OUTSIDE the index-aligned modeled carrier over the existing aliases the F2P tests exercise (the 'default' alias). The positional-list refinement observes only WHICH aliases are bound/closed — exactly what the tests discriminate. No input in the modeled carrier space makes a modeled function disagree with its real callee.

Since a gold-equivalent implementation verifies against the frozen spec and the gold resolves (patch.diff==gold, G-RESOLVE), the spec is not too strong. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.json relaxed_leakage=true, gates.G-LEAK=relaxed; RELAXED_LEAKAGE.md present). Independently re-verified the disposition rather than rubber-stamping: (1) Re-scanned the spec view (model.py docstring + axioms + pre/post-conditions) against problem_statement — the ONLY leak is the already-dispositioned connection hand-off / thread-sharing facet (the capability postcondition connections_handed_off(server) at line 166, the accept_connection_set configuration step, and the value-level install postconditions keyed on has_override/override_tokens, lines 170-173). That behaviour is a proven problem_statement<->gold mismatch: the public issue reports ONLY the connection-CLOSING symptom, whose dedicated test is skipped on in-memory sqlite (gold's features.py hunk) and is NOT in FAIL_TO_PASS; the actually-tested F2P discriminator is the constructor accepting a parent-supplied connections_override set + worker install, vocabulary that appears only in hints_text/test_patch/gold internals, never in problem_statement. Faithful (G-DIFF-failing: model_prepatch.py fails exactly on Ensures(connections_handed_off(server))) + non-leaking is provably impossible, so the facet is unavoidable, not lazy narration. (2) Found NO new leak beyond the facet: the spec view contains none of the patched paths/repo symbols — no basehttp.py, features.py, ThreadedWSGIServer, connections_override, process_request_thread, close_request, __init__ kwarg, close_all, socketserver, WSGIServer, sqlite, or LiveServer; model identifiers name behaviour, not the edit; no line quotes the gold diff. (3) Disposition unbroken: core gates sound in meta.json (G-VERIFY/G-DIFF/G-EQ/G-AX pass), same_spec command returns SAME (exit 0) confirming the spec region is byte-identical, and the unavoidability argument re-derives cleanly. Per the panel recording convention in RELAXED_LEAKAGE.md and gates/_audit.py (relaxed-leakage panel is recorded pass + note; there is no separate 'relaxed' panel status), the honest recording for this properly-dispositioned facet is NO-LEAKAGE (pass). LEAKAGE is reserved for a new leak beyond the facet or a broken disposition; neither is present.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.