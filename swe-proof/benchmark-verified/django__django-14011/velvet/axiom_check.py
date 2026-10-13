#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14011.

Runs the REAL repo callees that the two modeled methods deeply model, in the
prebuilt SWE-Bench instance container, and asserts every observation matches the
A-reference model. There are NO consumed axioms in this bundle; both A legs are
A-references (deep models validated == the real callee).

  (A-reference #1) installPreferred / override-precedence merge ==
      the real `BaseConnectionHandler.__setitem__` / `__getitem__`
      (django/utils/connection.py). Installing the override bindings then
      looking up each alias must agree with the model `preferred ++ registry`
      under first-match lookup (mapping.md §3.1).

  (A-reference #2) releaseAll / releasedSeq ==
      the real `ConnectionHandler.close_all` (django/db/utils.py:207). After
      close_all, every connection present in the registry must be closed,
      regardless of its prior state (mapping.md §3.2).

The real callee bodies only manipulate `self._connections` via
setattr/getattr/delattr and iterate `self.settings`. We instantiate the REAL
classes and exercise the REAL methods; `_connections` is a plain namespace so
the check needs no live database or asgiref Local context, while the method
bodies under test are unchanged repo code. Exit 0 iff every obligation holds.
"""
import random
import sys
import types


def _make_handler(aliases):
    """A REAL BaseConnectionHandler with controlled settings and a plain
    namespace registry (so no DB / Local context is needed). The methods under
    test (__setitem__/__getitem__/close_all) are unchanged repo code."""
    from django.utils.connection import BaseConnectionHandler
    h = BaseConnectionHandler(settings={a: {} for a in aliases})
    # `settings` is a cached_property over configure_settings (identity here);
    # force it so __iter__ yields exactly `aliases`.
    h.__dict__['settings'] = {a: {} for a in aliases}
    h._connections = types.SimpleNamespace()
    return h


# ---------- A-reference #1: override-precedence install --------------------

def model_lookup(preferred, registry, alias):
    """installPreferred model: lookup over `preferred ++ registry`, first match."""
    for a, v in list(preferred) + list(registry):
        if a == alias:
            return v
    return None


def check_install(preferred, registry):
    """Drive the REAL __setitem__/__getitem__ and compare to the merge model."""
    from django.utils.connection import BaseConnectionHandler
    aliases = [a for a, _ in registry] + [a for a, _ in preferred]
    h = _make_handler(aliases)
    # Pre-populate the worker's registry, then install the override — exactly
    # the patch's `for alias, conn in connections_override.items():
    # connections[alias] = conn` layered over the pre-existing registry.
    for a, v in registry:
        BaseConnectionHandler.__setitem__(h, a, v)   # REAL callee
    for a, v in preferred:
        BaseConnectionHandler.__setitem__(h, a, v)   # REAL callee (override)
    for a in set(aliases):
        observed = BaseConnectionHandler.__getitem__(h, a)   # REAL callee
        expected = model_lookup(preferred, registry, a)
        assert observed == expected, (
            "install A-reference unsound: alias %r real lookup=%r model=%r "
            "(preferred=%r registry=%r)" % (a, observed, expected, preferred, registry))


# ---------- A-reference #2: release-all -----------------------------------

class _FakeConn:
    def __init__(self, is_open):
        self.is_open = is_open
    def close(self):
        self.is_open = False


def check_close_all(states):
    """states: list of (alias, is_open_bool) or (alias, None) for a
    never-instantiated alias. Drive the REAL ConnectionHandler.close_all and
    assert every PRESENT connection ends closed (== releasedSeq)."""
    from django.db.utils import ConnectionHandler
    aliases = [a for a, _ in states]
    h = _make_handler(aliases)
    conns = {}
    for a, st in states:
        if st is None:
            continue  # never instantiated: no stored attr (AttributeError path)
        c = _FakeConn(st)
        conns[a] = c
        setattr(h._connections, a, c)
    ConnectionHandler.close_all(h)   # REAL callee
    for a, st in states:
        if st is None:
            # close_all's try/except AttributeError must have skipped it safely
            assert not hasattr(h._connections, a), (
                "close_all A-reference unsound: created a connection for "
                "never-instantiated alias %r" % a)
            continue
        assert conns[a].is_open is False, (
            "close_all A-reference unsound: alias %r left open after close_all "
            "(initial=%r)" % (a, st))


# ---------- driver --------------------------------------------------------

def main():
    rng = random.Random(14011)
    alias_pool = ["default", "replica", "other", "analytics", "legacy",
                  "shard0", "shard1", "cache_db", "ro", "rw"]

    # The connection registry and `connections_override` are both dicts, so
    # aliases are UNIQUE within each side (mapping.md §2). The fuzz respects
    # that; first-match lookup over preferred++registry then agrees exactly with
    # the real dict-semantics (last setattr wins, override before registry).

    # --- install A-reference: boundary cases ------------------------------
    boundary = [
        ([], []),
        ([], [("default", 1)]),
        ([("default", 99)], []),
        ([("default", 99)], [("default", 1)]),                  # override wins
        ([("default", 99)], [("replica", 2)]),                  # disjoint
        ([("default", 99), ("replica", 88)],
         [("default", 1), ("other", 3)]),                       # mixed overlap
    ]
    for pref, reg in boundary:
        check_install(pref, reg)

    # --- install A-reference: randomized fuzz (unique aliases per side) ----
    for _ in range(20000):
        nreg = rng.randint(0, 6)
        npre = rng.randint(0, 6)
        rkeys = rng.sample(alias_pool, min(nreg, len(alias_pool)))
        pkeys = rng.sample(alias_pool, min(npre, len(alias_pool)))
        reg = [(k, rng.randint(0, 10_000)) for k in rkeys]
        pre = [(k, rng.randint(0, 10_000)) for k in pkeys]
        check_install(pre, reg)

    # --- close_all A-reference: boundary cases ----------------------------
    cb = [
        [],
        [("default", True)],
        [("default", False)],
        [("default", True), ("replica", True)],                 # all open
        [("default", False), ("replica", False)],               # all closed
        [("default", True), ("replica", False), ("other", True)],  # mixed
        [("default", None)],                                    # never instantiated
        [("default", True), ("replica", None), ("other", False)],
    ]
    for states in cb:
        check_close_all(states)

    # --- close_all A-reference: randomized fuzz ---------------------------
    for _ in range(20000):
        n = rng.randint(0, 6)
        used = rng.sample(alias_pool, min(n, len(alias_pool)))
        states = []
        for a in used:
            r = rng.random()
            st = None if r < 0.15 else (r < 0.55)   # 15% never-instantiated
            states.append((a, st))
        check_close_all(states)

    print("G-AX OK: install A-reference (== BaseConnectionHandler "
          "__setitem__/__getitem__) and close_all A-reference (== "
          "ConnectionHandler.close_all) sound on boundary + 40000 fuzz cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
