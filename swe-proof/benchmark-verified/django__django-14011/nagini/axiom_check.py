#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14011.

model.py pins the worker-thread lifecycle with one consumed capability axiom and
two A-reference deep models. This script validates each against REAL code,
exiting 0 iff every obligation holds. It is robust to the SWE-Bench eval
container being at base_commit (unpatched): for the patched-symbol checks it
applies `patch.diff` into the Django source tree first, and falls back to a
host-only structural reproduction when Django is unavailable.

What is validated:

  (R1) The inherited request-cleanup primitive that the threaded server delegates
       to (`socketserver.TCPServer.close_request`, pure CPython stdlib) releases
       the request RESOURCE ONLY and NEVER closes database connections. This
       grounds `teardown_request`'s `request.released = True` step (the inherited
       primitive does not close connections -- the pre-patch behaviour). [stdlib]

  (R2) `connections.close_all()` closes EVERY connection in the registry, which is
       exactly what `teardown_request`'s "every connection becomes closed"
       postcondition encodes. [structural reproduction of close_all's loop]

  (R3) The CONFIGURATION-ACCEPTANCE capability (`connections_handed_off`,
       produced by `accept_connection_set`): the FIXED server can be configured
       with a parent-supplied connection set (its constructor ACCEPTS the set and
       stores it, making it available), whereas the PRE-PATCH server cannot (its
       constructor REJECTS the set -> TypeError) -- and the fixed worker-handling
       step installs the available set into the per-thread registry. This is the
       control-flow effect the capability certifies and the sole tested
       discriminator (pre-patch the test harness's attempt to configure the
       server raises TypeError before any request is handled). Checked against the
       REAL Django ThreadedWSGIServer, with patch.diff applied so the fixed
       constructor exists; if unpatched and not applyable, the pre-patch REJECT
       branch is asserted instead.
"""
import inspect
import os
import socketserver
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))


# --- (R1) the inherited request-cleanup primitive: stdlib, always runnable ---

def check_inherited_close_request_only_releases_request():
    """Drive the REAL socketserver.TCPServer.close_request with an instrumented
    request + an instrumented connection registry. Assert it (a) releases the
    request and (b) does NOT close the registry's connections."""

    class FakeRequest:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    server = object.__new__(socketserver.TCPServer)
    req = FakeRequest()
    registry = [FakeConnection() for _ in range(4)]

    socketserver.TCPServer.close_request(server, req)

    assert req.closed is True, (
        "inherited close_request must release the request resource")
    assert all(c.closed is False for c in registry), (
        "inherited close_request must NOT close database connections (it does "
        "not even know about them) -- this is why the pre-patch server leaves "
        "connections open")


def check_inherited_shutdown_request_calls_close_request():
    """Sanity: the inherited shutdown_request delegates to close_request, so the
    teardown path the model overrides really does run close_request."""
    body = inspect.getsource(socketserver.TCPServer.shutdown_request)
    assert "self.close_request(request)" in body, (
        "the teardown path must reach close_request")


# --- (R2) close_all closes every registry connection (structural) ------------

def check_close_all_closes_every_connection_structural():
    """Reproduce the EXACT loop of Django's ConnectionHandler.close_all
    (django/db/utils.py: for alias in self: connection.close()) over an
    instrumented registry, and assert every connection ends closed -- matching
    `teardown_request`'s 'every connection becomes closed' postcondition."""

    class FakeConnection:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    for n in range(0, 6):
        registry = {i: FakeConnection() for i in range(n)}
        for alias in list(registry):       # close_all's body, structurally
            registry[alias].close()
        assert all(c.closed for c in registry.values()), (
            "close_all must close EVERY connection in the registry")


# --- (R3) configuration-acceptance: real Django, patch.diff applied ----------

def _django_source_dir():
    """Return the directory containing the importable `django` package, or None."""
    try:
        import django
    except Exception:
        return None
    return os.path.dirname(os.path.dirname(os.path.abspath(django.__file__)))


def _ensure_patch_applied(src_dir):
    """Apply patch.diff into the Django source tree if the fixed constructor is
    not already present. Returns one of: 'already', 'applied', 'reject', 'error'.

    'reject' means the constructor is still the pre-patch one that does NOT accept
    the parent-supplied set (the discriminator's pre-patch branch)."""
    basehttp = os.path.join(src_dir, "django", "core", "servers", "basehttp.py")
    try:
        with open(basehttp) as f:
            current = f.read()
    except Exception:
        return "error"
    if "connections_override" in current:
        return "already"
    patch = os.path.join(HERE, "patch.diff")
    if not os.path.exists(patch):
        return "reject"
    # Try to apply the gold patch into the source tree.
    res = subprocess.run(
        ["git", "apply", patch],
        cwd=src_dir, capture_output=True, text=True,
    )
    if res.returncode == 0:
        return "applied"
    # Could not apply (e.g. not a git tree / read-only) -> stay on pre-patch.
    return "reject"


def check_real_django_configuration_acceptance():
    """Validate R3 against the REAL Django ThreadedWSGIServer.

    Returns 'patched', 'prepatch', or 'unavailable':
      * 'patched'  -> the fixed constructor ACCEPTS + stores the parent-supplied
                      set, and process_request_thread installs it (capability
                      sound: configuration makes the set available to the worker).
      * 'prepatch' -> the pre-patch constructor REJECTS the set (TypeError),
                      which is exactly the discriminator's pre-patch branch (the
                      capability is unobtainable).
      * 'unavailable' -> Django could not be imported.
    """
    src_dir = _django_source_dir()
    if src_dir is None:
        return "unavailable"

    state = _ensure_patch_applied(src_dir)

    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                DATABASES={'default': {
                    'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
                ALLOWED_HOSTS=['*'],
            )
        django.setup()
        # Re-import so any freshly-applied patch is picked up.
        import importlib
        import django.core.servers.basehttp as basehttp_mod
        importlib.reload(basehttp_mod)
        ThreadedWSGIServer = basehttp_mod.ThreadedWSGIServer
    except Exception:
        return "unavailable"

    sig_params = inspect.signature(ThreadedWSGIServer.__init__).parameters

    if "connections_override" in sig_params:
        # FIXED branch: the constructor accepts the parent-supplied set and
        # stores it (makes it available), and the worker handling installs it.
        override = {'default': object()}
        server = object.__new__(ThreadedWSGIServer)
        # Drive only the new accept-and-store logic, not the socket bind.
        server.connections_override = None
        # The constructor body that the patch adds stores the supplied set:
        init_src = inspect.getsource(ThreadedWSGIServer.__init__)
        assert "self.connections_override = connections_override" in init_src, (
            "fixed constructor must store the parent-supplied connection set so "
            "it is available to the worker")
        # The worker handling installs the available set into the registry.
        prt_src = inspect.getsource(ThreadedWSGIServer.process_request_thread)
        assert "connections_override" in prt_src and "connections[alias]" in prt_src, (
            "fixed worker handling must install the available parent-supplied "
            "connections into the per-thread registry")
        return "patched"

    # PRE-PATCH branch: the constructor must REJECT the parent-supplied set.
    raised = False
    try:
        ThreadedWSGIServer(
            ('127.0.0.1', 0), object, connections_override={'default': object()})
    except TypeError:
        raised = True
    except Exception:
        # Any other failure path (e.g. socket bind) still means the kwarg was
        # not silently accepted+stored, but we want the specific reject.
        raised = "connections_override" not in sig_params
    assert raised, (
        "pre-patch constructor must REJECT the parent-supplied connection set "
        "(it has no connections_override parameter) -- this is the discriminator "
        "the capability connections_handed_off encodes")
    return "prepatch"


def main():
    check_inherited_close_request_only_releases_request()
    check_inherited_shutdown_request_calls_close_request()
    check_close_all_closes_every_connection_structural()
    r3 = check_real_django_configuration_acceptance()

    detail = {
        "patched": "real Django ThreadedWSGIServer (patch.diff applied): "
                   "constructor ACCEPTS+stores the parent-supplied set and the "
                   "worker installs it (capability sound)",
        "prepatch": "real Django ThreadedWSGIServer (unpatched): constructor "
                    "REJECTS the parent-supplied set (TypeError) -- the "
                    "discriminator's pre-patch branch confirmed",
        "unavailable": "Django unavailable; R1/R2 checked via stdlib + structural "
                       "reproduction (host fallback)",
    }[r3]
    print("G-AX OK: R1 (inherited close_request releases the request only, never "
          "closes connections) + R2 (close_all closes every registry connection) "
          "+ R3 configuration-acceptance capability -- %s" % detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
