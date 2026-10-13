#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16145 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`formatHost` /
              `displayAddress`) transliterated to Python over the *real* repo
              types (`bool` for `self._raw_ipv6`, `str` for `self.addr`), via
              the mapping.md bijection (`List Char` ↔ `str`, `Bool` ↔ `bool`,
              `['['] ++ host ++ [']']` ↔ `f"[{host}]"`). The impl region calls
              no callee, so there is no A leg to hold out — this is a pure R/I
              (non-skip) G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the patched display-address ladder of
              `Command.inner_run`, transliterated VERBATIM from the gold patch
              (django/core/management/commands/runserver.py:132-137).

WHY THE ORACLE IS THE PATCHED SOURCE LADDER (not a live `inner_run`):
  The display computation lives inside `Command.inner_run(self, *args,
  **options)`. Reaching it for real binds a socket and starts a blocking
  development server (the `run(...)` call a few lines later never returns), and
  needs a fully-initialised command with stdout/settings and a parsed addrport.
  The F2P test `ManageRunserver.test_zero_ip_addr` itself mocks `runserver.run`
  and `check_migrations` so the ONLY observable is the banner string. So, per
  the worker prompt, the ORACLE is the patched ladder transliterated verbatim;
  the SHADOW is Solution.lean's `displayAddress` post-image transliterated. They
  must agree on every input.

This mirrors the F2P test:
  self._raw_ipv6=False, self.addr="0"  ->  addr == "0.0.0.0"
    (the banner then reads "Starting development server at http://0.0.0.0:8000/")

Runs stdlib only; the fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.
"""
import random
import sys

SEED = 16145
N_FUZZ = 100_000


def shadow(bracketed, host):
    """displayAddress (host.toList) transliterated to str, via mapping.md §2:
        if bracketed: '[' ++ host ++ ']'
        elif host == '0': '0.0.0.0'
        else: host
    This is the R/I shadow of formatHost's impl region."""
    if bracketed:
        return "[" + host + "]"
    elif host == "0":
        return "0.0.0.0"
    else:
        return host


def oracle(bracketed, host):
    """patch.diff's behaviour: the patched `addr` ladder transliterated verbatim
    from django/core/management/commands/runserver.py:132-137. Here `bracketed`
    stands for self._raw_ipv6 and `host` for self.addr."""
    if bracketed:
        addr = f"[{host}]"
    elif host == "0":
        addr = "0.0.0.0"
    else:
        addr = host
    return addr


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary_hosts = [
        "0",            # the bare shorthand — the behaviour of interest
        "0.0.0.0",      # the expanded form (must pass through unchanged)
        "",             # empty host
        "00", "0.0", "10", "0x0",   # near-"0" strings that must NOT expand
        "127.0.0.1", "localhost", "192.168.1.1", "::1", "example.com",
        "0:8000",       # full addrport never reaches this code path, but harmless
        " 0", "0 ",     # whitespace variants must NOT expand
    ]
    for h in boundary_hosts:
        yield (True, h)
        yield (False, h)
    # randomized fuzz over (bool, str) pairs
    alphabet = list("0123456789.:[]abcdefz ") + ["é", "•"]
    for _ in range(n):
        k = rng.randint(0, 16)
        h = "".join(rng.choice(alphabet) for _ in range(k))
        yield (rng.choice((True, False)), h)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for bracketed, host in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(bracketed, host)
        orc = oracle(bracketed, host)
        if sh != orc:
            disagreements.append((bracketed, host, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for b, h, sh, orc in disagreements:
            print("  bracketed=%r host=%r shadow=%r oracle=%r" % (b, h, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of formatHost agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
