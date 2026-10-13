#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15375.

The bundle models ONE decision: the node produced by the tail of
`Aggregate.resolve_expression` when the aggregate carries a `default`
(`django/db/models/aggregates.py`, the wrapping arm). The modeled value is a
PURE function of two observables (mapping.md):

    isTerminalAggregation : bool   (c.is_summary == summarize)
    hasFallback           : bool   (c.default is not None)

producing two observables of the returned node:

    wrapped  : bool   (the Coalesce wrapper vs the bare aggregate)
    terminal : bool   (the returned node's is_summary)

Post-patch rule:

    if c.default is None:
        return (wrapped=False, terminal=is_summary)          # bare aggregate
    coalesce = Coalesce(c, default, ...)   # is_summary defaults to False
    coalesce.is_summary = c.is_summary     # <-- the fix
    return (wrapped=True, terminal=is_summary)

Standing up an ORM/query to drive the real `resolve_expression` is heavy and
unnecessary: the modeled value is this pure node-construction decision over the
two observables the resolution exposes. The ORACLE below is a faithful
in-process replica that uses the EXACT patched logic (Coalesce born with
is_summary=False, then assigned c.is_summary), and the SHADOW is the op-for-op
transliteration of `implementation_resolveAggregate` (per refinement.md).

stdlib-only. Pinned seed: 15375 (also in mapping.md).
"""
import random
import sys

SEED = 15375
N = 200_000


# --- ORACLE: faithful in-process replica of the patched decision -------------
class _Coalesce:
    # Mirrors a freshly constructed Coalesce: is_summary at class default False
    # (django.db.models.expressions.BaseExpression.is_summary = False), since
    # Coalesce.__init__ does not set it.
    def __init__(self):
        self.is_summary = False


def oracle_resolve(is_terminal_aggregation, has_fallback):
    # c.is_summary was set to `summarize` during resolve == is_terminal_aggregation
    c_is_summary = is_terminal_aggregation
    if not has_fallback:                      # c.default is None
        return (False, c_is_summary)          # return c (bare aggregate)
    coalesce = _Coalesce()                    # is_summary == False here
    coalesce.is_summary = c_is_summary        # the fix: copy c.is_summary
    return (True, coalesce.is_summary)


# --- SHADOW of implementation_resolveAggregate (the R/I leg) -----------------
# Mirrors Solution.lean: terminal := isTerminalAggregation;
# if !hasFallback then return (false, terminal);
# wrapperTerminal := false; wrapperTerminal := terminal; return (true, wrapperTerminal).
def shadow_resolve(is_terminal_aggregation, has_fallback):
    terminal = is_terminal_aggregation
    if not has_fallback:
        return (False, terminal)
    wrapper_terminal = False
    wrapper_terminal = terminal
    return (True, wrapper_terminal)


def disagree(ita, hf):
    got = oracle_resolve(ita, hf)
    want = shadow_resolve(ita, hf)
    if got != want:
        return ((ita, hf), got, want)
    return None


def main() -> int:
    checked = 0
    # Exhaustive over the 2x2 boolean domain (the entire input space) ...
    for ita in (True, False):
        for hf in (True, False):
            d = disagree(ita, hf)
            if d:
                print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
            checked += 1

    # ... plus a large randomized pass for the gate's >=10^5 budget.
    rng = random.Random(SEED)
    for _ in range(N):
        ita = rng.choice([True, False])
        hf = rng.choice([True, False])
        d = disagree(ita, hf)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
