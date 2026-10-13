#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14011 (nagini).

SHADOW: the impl regions of model.py's ``serve_request_on_worker`` and
``teardown_request``, copied VERBATIM below with only the contract calls
(Requires / Ensures / Invariant / Assert / MustTerminate) stripped. The model
has no @Pure helpers. The one @ContractOnly callee
(``accept_connection_set``) is delegated to the REAL repo configuration step
it maps to per mapping.md section 1: the patched threaded server's
constructor accepting the parent-supplied connection set — the shadow's
callee actually CONSTRUCTS the real (patched) server with that set, so the
capability the model grants corresponds to a real, observable acceptance
(pre-patch it would raise TypeError, i.e. the capability is unobtainable).

ORACLE: the REAL patched repo methods per mapping.md section 1 —
``django.core.servers.basehttp.ThreadedWSGIServer.process_request_thread``
(run after the real constructor accepted the set; it installs the available
set into the per-thread registry and delegates the handling) and
``ThreadedWSGIServer.close_request`` (closes every registry connection, then
delegates the request cleanup). The gate applies patch.diff to /testbed and
sets PYTHONPATH=/testbed before this script runs, so the imports resolve to
the patched module. Each probe drives the real method over the real
``django.db.connections`` registry (this thread's), populated with
instrumented connection objects, and reads the registry back afterwards.

TYPE BRIDGE (mapping.md section 2): aliases-as-positions over a fixed alias
vector; ``tokens[i]`` is the identity of the object bound at alias i (int
token <-> one FakeConnection object per probe); ``has_override[i]`` /
``override_tokens[i]`` encode the supplied ``{alias: conn}`` dict
(membership + supplied identity); ``closed[i]`` is the connection object's
closed state; ``request.released`` is "the inherited cleanup released the
request resource" (its ``close()`` ran). The handling delegated by the
worker is driven with a no-op handler class and an instrumented request
object (constructor parameters / request inputs, not stubs of the methods
under test), so no real socket traffic occurs. Note the worker's delegated
handling ends by running the (patched) per-request cleanup, which closes
connections; that touches only the closed-state facet, which is OUTSIDE
``serve_request_on_worker``'s carrier (tokens only), so the token
comparison is unaffected — exactly the mapping's carrier split.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): exhaustive small-arity
boundary cases (empty registry; every override mask for 1-2 aliases crossed
with equal/distinct token patterns; all/none overridden at max arity;
duplicate identities; empty-set-vs-absent-set configuration) plus 60000
random serve probes and 45000 random teardown probes over 0..8 aliases.
Pinned fuzz seed: 14011 (recorded in mapping.md section 4). Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits
1. stdlib only.
"""
import json
import random
import sys

SEED = 14011
N_FUZZ_SERVE = 60000
N_FUZZ_TEARDOWN = 45000
MAX_N = 8


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def serve_request_on_worker(server, tokens, has_override, override_tokens):
    # Configure the server so the parent-supplied set is available to this
    # worker (the configuration step that accepts the set).
    accept_connection_set(server, has_override, override_tokens)
    # Make the available parent-supplied connections take effect in this worker
    # thread's registry.
    i = 0
    while i < len(tokens):
        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1


def teardown_request(closed, tokens, request):
    # Close every connection in this worker thread's registry.
    i = 0
    while i < len(closed):
        closed[i] = True
        i = i + 1
    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry).
    request.released = True


# --- @ContractOnly callee: the REAL configuration-acceptance step ------------

def accept_connection_set(server, has_override, override_tokens):
    """The axiomatized configuration step, delegated to the REAL repo
    counterpart (mapping.md sections 1 and 3.1): constructing the patched
    threaded server with the parent-supplied connection set. `server` is the
    per-probe context; on acceptance it holds the real configured server."""
    server.configure(has_override, override_tokens)


# --- instrumented carriers (bridge objects, not stubs of tested code) --------

class FakeConnection(object):
    """A registry entry: carries its identity token and a closed flag; its
    close() is what the real registry-wide close step invokes."""

    def __init__(self, token, closed=False):
        self._token = token
        self.closed = closed

    def close(self):
        self.closed = True


class FakeSocketRequest(object):
    """The per-request resource handed to the real methods: supports the
    shutdown()/close() the inherited teardown path performs."""

    def __init__(self):
        self.was_closed = False

    def shutdown(self, how):
        pass

    def close(self):
        self.was_closed = True


class ModelRequest(object):
    """model.py's Request: only a released flag (shadow side)."""

    def __init__(self):
        self.released = False


class NullHandler(object):
    """No-op RequestHandlerClass: a constructor parameter of the server (an
    input), so the delegated handling performs no socket traffic."""

    def __init__(self, request, client_address, server):
        pass


class ServerCtx(object):
    """Per-probe server context. configure() performs the REAL configuration
    acceptance (the patched constructor taking the parent-supplied set) and
    keeps the real server instance for the oracle run."""

    def __init__(self, aliases, obj_for, use_none_when_empty=False):
        self._aliases = aliases
        self._obj_for = obj_for
        self._use_none = use_none_when_empty
        self.real = None
        self.accepted = False

    def configure(self, has_override, override_tokens):
        import django.core.servers.basehttp as basehttp
        ov = {}
        for i in range(len(has_override)):
            if has_override[i]:
                ov[self._aliases[i]] = self._obj_for(override_tokens[i])
        supplied = None if (not ov and self._use_none) else ov
        try:
            # bind_and_activate=False: the socket is created but never bound,
            # so configuration is observed without network side effects.
            self.real = basehttp.ThreadedWSGIServer(
                ('127.0.0.1', 0), NullHandler, False,
                connections_override=supplied)
            self.accepted = True
        except TypeError:
            self.accepted = False

    def close(self):
        if self.real is not None:
            try:
                self.real.server_close()
            except Exception:
                pass
            self.real = None


# --- oracle environment --------------------------------------------------------

ALIASES = ['default', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7']


def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={alias: {'ENGINE': 'django.db.backends.dummy'}
                       for alias in ALIASES},
            ALLOWED_HOSTS=['*'],
        )
    django.setup()


def get_registry():
    from django.db import connections
    return connections


def reset_registry(connections):
    for alias in ALIASES:
        try:
            delattr(connections._connections, alias)
        except AttributeError:
            pass


def read_bound_token(connections, alias):
    try:
        return getattr(connections._connections, alias)._token
    except AttributeError:
        return None


# --- differential probes ---------------------------------------------------------

def check_serve(connections, tokens, has_override, override_tokens,
                use_none_when_empty=False):
    """Run shadow and real worker-serve on one input; return an error string
    on disagreement, else None."""
    n = len(tokens)
    objs = {}

    def obj_for(t):
        if t not in objs:
            objs[t] = FakeConnection(t)
        return objs[t]

    ctx = ServerCtx(ALIASES, obj_for, use_none_when_empty)
    try:
        # SHADOW (its accept_connection_set performs the REAL configuration)
        shadow_tokens = list(tokens)
        serve_request_on_worker(ctx, shadow_tokens, list(has_override),
                                list(override_tokens))
        if not ctx.accepted:
            return ("DISAGREEMENT (capability) on tokens=%r has_override=%r "
                    "override_tokens=%r:\n  shadow grants the configuration-"
                    "acceptance capability, but the real constructor did NOT "
                    "accept the supplied set (TypeError)"
                    % (tokens, has_override, override_tokens))

        # ORACLE: bind the initial registry, run the real worker handling
        reset_registry(connections)
        for i in range(n):
            connections[ALIASES[i]] = obj_for(tokens[i])
        req = FakeSocketRequest()
        ctx.real.process_request_thread(req, ('127.0.0.1', 0))
        real_tokens = [read_bound_token(connections, ALIASES[i])
                       for i in range(n)]
    finally:
        ctx.close()

    if shadow_tokens != real_tokens:
        return ("DISAGREEMENT on serve input tokens=%r has_override=%r "
                "override_tokens=%r (empty-set-as-absent=%r):\n"
                "  shadow (impl region) registry tokens = %r\n"
                "  real (patched repo)  registry tokens = %r"
                % (tokens, has_override, override_tokens,
                   use_none_when_empty, shadow_tokens, real_tokens))
    return None


def check_teardown(connections, srv, closed, tokens):
    """Run shadow and real per-request cleanup on one input; return an error
    string on disagreement, else None."""
    n = len(closed)
    objs = {}
    for i in range(n):
        if tokens[i] not in objs:
            objs[tokens[i]] = FakeConnection(tokens[i], closed[i])

    # SHADOW
    shadow_closed = list(closed)
    shadow_tokens = list(tokens)
    shadow_req = ModelRequest()
    teardown_request(shadow_closed, shadow_tokens, shadow_req)

    # ORACLE: bind the registry, run the real patched cleanup
    reset_registry(connections)
    for i in range(n):
        connections[ALIASES[i]] = objs[tokens[i]]
    req = FakeSocketRequest()
    srv.close_request(req)
    real_tokens = [read_bound_token(connections, ALIASES[i]) for i in range(n)]
    real_closed = []
    for i in range(n):
        t = real_tokens[i]
        real_closed.append(objs[t].closed if t in objs else None)

    if (shadow_closed != real_closed or shadow_tokens != real_tokens
            or shadow_req.released != req.was_closed):
        return ("DISAGREEMENT on teardown input closed=%r tokens=%r:\n"
                "  shadow (impl region): closed=%r tokens=%r released=%r\n"
                "  real (patched repo):  closed=%r tokens=%r released=%r"
                % (closed, tokens, shadow_closed, shadow_tokens,
                   shadow_req.released, real_closed, real_tokens,
                   req.was_closed))
    return None


# --- input generation -------------------------------------------------------------

def serve_boundary_cases():
    """(tokens, has_override, override_tokens, use_none_when_empty)"""
    cases = []
    # empty registry, supplied set absent vs supplied-but-empty
    cases.append(([], [], [], True))
    cases.append(([], [], [], False))
    # n=1: every mask x equal/distinct token patterns x absent/empty forms
    for t in (0, 1):
        for ot in (0, 1):
            for m in (False, True):
                for un in (False, True):
                    cases.append(([t], [m], [ot], un))
    # n=2: every mask over two aliases, several token patterns
    pat2 = [([0, 1], [2, 3]), ([0, 0], [1, 1]), ([5, 5], [5, 5]),
            ([1, 2], [2, 1])]
    for toks, ovs in pat2:
        for m0 in (False, True):
            for m1 in (False, True):
                cases.append((list(toks), [m0, m1], list(ovs), False))
    # max arity: none / all / alternating overridden; duplicate identities
    full = list(range(MAX_N))
    cases.append((full, [False] * MAX_N, [t + 10 for t in full], True))
    cases.append((full, [True] * MAX_N, [t + 10 for t in full], False))
    cases.append((full, [i % 2 == 0 for i in range(MAX_N)],
                  [t + 10 for t in full], False))
    cases.append(([7] * MAX_N, [True] * MAX_N, [7] * MAX_N, False))
    cases.append(([7] * MAX_N, [True] * MAX_N, [9] * MAX_N, False))
    return cases


def teardown_boundary_cases():
    """(closed, tokens) — identities distinct unless closed flags agree
    (closed state is per connection object, so aliases sharing an identity
    share a flag: that is the bridge's representable input set)."""
    cases = [([], [])]
    for c in (False, True):
        cases.append(([c], [0]))
    cases.append(([False, False], [0, 1]))
    cases.append(([True, True], [0, 1]))
    cases.append(([False, True], [0, 1]))
    cases.append(([True, False], [0, 1]))
    # duplicate identity, consistent flags
    cases.append(([False, False], [3, 3]))
    cases.append(([True, True], [3, 3]))
    cases.append(([False] * MAX_N, list(range(MAX_N))))
    cases.append(([True] * MAX_N, list(range(MAX_N))))
    cases.append(([i % 2 == 0 for i in range(MAX_N)], list(range(MAX_N))))
    return cases


def main():
    setup_django()
    connections = get_registry()

    # one real configured server for the teardown probes (its per-request
    # cleanup does not read the supplied-set field)
    import django.core.servers.basehttp as basehttp
    try:
        teardown_srv = basehttp.ThreadedWSGIServer(
            ('127.0.0.1', 0), NullHandler, False, connections_override=None)
    except TypeError:
        print("DISAGREEMENT (capability): the real constructor does not "
              "accept the parent-supplied connection set at all")
        return 1

    checked = 0
    try:
        serve_bnd = serve_boundary_cases()
        for tokens, mask, ovt, un in serve_bnd:
            err = check_serve(connections, tokens, mask, ovt, un)
            if err:
                print(err)
                return 1
            checked += 1

        tear_bnd = teardown_boundary_cases()
        for closed, tokens in tear_bnd:
            err = check_teardown(connections, teardown_srv, closed, tokens)
            if err:
                print(err)
                return 1
            checked += 1

        rng = random.Random(SEED)

        for _ in range(N_FUZZ_SERVE):
            n = rng.randint(0, MAX_N)
            tokens = [rng.randint(0, 11) for _ in range(n)]
            p = rng.choice((0.0, 0.15, 0.5, 0.85, 1.0))
            mask = [rng.random() < p for _ in range(n)]
            ovt = [rng.randint(0, 11) for _ in range(n)]
            un = rng.random() < 0.5
            err = check_serve(connections, tokens, mask, ovt, un)
            if err:
                print(err)
                return 1
            checked += 1

        for _ in range(N_FUZZ_TEARDOWN):
            n = rng.randint(0, MAX_N)
            if rng.random() < 0.85:
                tokens = rng.sample(range(64), n)
                closed = [rng.random() < 0.5 for _ in range(n)]
            else:
                # duplicated identities with per-identity-consistent flags
                tokens = [rng.randint(0, max(1, n // 2)) for _ in range(n)]
                flag_of = {t: rng.random() < 0.5 for t in set(tokens)}
                closed = [flag_of[t] for t in tokens]
            err = check_teardown(connections, teardown_srv, closed, tokens)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        try:
            teardown_srv.server_close()
        except Exception:
            pass

    print("G-CONF OK: shadow impl == real patched worker-serve/teardown on "
          "%d inputs (%d serve boundary + %d teardown boundary + %d serve "
          "fuzz + %d teardown fuzz, seed %d); 0 disagreements."
          % (checked, len(serve_bnd), len(tear_bnd), N_FUZZ_SERVE,
             N_FUZZ_TEARDOWN, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
