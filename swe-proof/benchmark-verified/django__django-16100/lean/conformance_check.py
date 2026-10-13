#!/usr/bin/env python3
"""G-CONF for django__django-16100.

Differential test: the R-shadow of `implementation_changelistView` (a faithful
Python translation of the Lean impl) vs. an independent reference model of the
patched behaviour (the `transaction.atomic` all-or-nothing semantics of the gold
fix). Bridged via mapping.md:

  store state         <-> int (abstract observable state; each successful step
                              transforms it deterministically)
  one changed form    <-> step: callable(state) -> ("ok", new_state) | ("err", e)
  formset.forms       <-> list of steps, in order
  propagated failure  <-> Optional[error tag]
  result              <-> (state, optional_error)

≥10^5 fuzzed inputs; exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 16100  # pinned (mapping.md)
N = 120_000


def make_step(rng):
    """A pending update: succeeds (advancing state) or raises."""
    if rng.random() < 0.30:
        e = rng.randint(1, 9)
        return ("err", e)
    delta = rng.randint(1, 1000)
    return ("ok", delta)


def impl_shadow(s0, steps):
    """Faithful translation of the Lean impl (post-patch):
    on first error, roll back to s0."""
    s = s0
    for kind, payload in steps:
        if kind == "ok":
            s = s + payload          # f s = .ok s'
        else:
            return (s0, payload)     # .error e => return (s0, some e)  [ROLLBACK]
    return (s, None)


def reference_atomic(s0, steps):
    """Independent model of the gold fix's transaction.atomic semantics:
    all-or-nothing. Compute the would-be final state; if ANY step raises, the
    block rolls back entirely and the FIRST error propagates."""
    s = s0
    first_err = None
    for kind, payload in steps:
        if kind == "err":
            first_err = payload
            break
        s = s + payload
    if first_err is not None:
        return (s0, first_err)       # rollback to original
    return (s, None)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    for _ in range(N):
        s0 = rng.randint(-500, 500)
        n = rng.randint(0, 12)
        steps = [make_step(rng) for _ in range(n)]
        a = impl_shadow(s0, steps)
        b = reference_atomic(s0, steps)
        if a != b:
            disagreements += 1
            if len(examples) < 5:
                examples.append({"s0": s0, "steps": steps, "impl": a, "ref": b})
    out = {"gate": "G-CONF", "checked": N, "disagreements": disagreements,
           "seed": SEED, "status": "pass" if disagreements == 0 else "fail"}
    if examples:
        out["examples"] = examples
    print(json.dumps(out))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
