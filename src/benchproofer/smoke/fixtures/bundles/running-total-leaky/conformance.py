"""Compare the verified implementation with the code the task's own fix leaves.

The shadow below is `shadow.py` verbatim. The module beside it is the task as the
benchmark solves it, so `totals.running_total` is the function the shadow represents.
"""

# benchproofer:target totals.py
"""The verified implementation, copied to run where the benchmark's tests run."""


# benchproofer:begin impl
def impl(values):
    out = []
    carried = 0
    for item in values:
        carried = carried + item
        out.append(carried)
    return out
# benchproofer:end impl


def running_total(values):
    """Expose the verified implementation under the name the task uses."""
    return impl(values)

import random

import totals

LIMIT = 100_000
#: Drawn small and awkward on purpose: empty, singleton, negatives and zeroes are
#: where a partial-sum implementation stops agreeing with another one.
VALUES = (-97, -1, 0, 0, 1, 3, 1_000_000)


def main():
    rng = random.Random(20260922)
    disagreed = 0
    for index in range(LIMIT):
        length = 0 if index == 0 else rng.randrange(0, 7)
        values = [rng.choice(VALUES) for _ in range(length)]
        theirs = totals.running_total(list(values))
        ours = running_total(list(values))
        if theirs != ours:
            disagreed += 1
            if disagreed <= 5:
                print(
                    f"benchproofer:disagrees totals.running_total {values} -> the "
                    f"repository returns {theirs}, the shadow returns {ours}"
                )
    print(
        f"benchproofer:compared totals.running_total {LIMIT} sequences of up to six "
        "values drawn from a seeded generator, the empty sequence included"
    )
    raise SystemExit(1 if disagreed else 0)


main()
