"""Compare the verified implementation with the code the task's own fix leaves.

The shadow below is `shadow.py` verbatim. The module beside it is the task as the
benchmark solves it, so `change.make_change` is the function the shadow represents.
"""

# benchproofer:target change.py
"""The verified implementation, copied to run where the benchmark's tests run."""


# benchproofer:begin impl
def impl(cents):
    quarters = cents // 25
    remainder = cents - quarters * 25
    dimes = remainder // 10
    remainder = remainder - dimes * 10
    nickels = remainder // 5
    pennies = remainder - nickels * 5
    return (quarters, dimes, nickels, pennies)
# benchproofer:end impl


def make_change(cents):
    """Expose the verified implementation under the name the task uses."""
    return impl(cents)

import change

LIMIT = 100_000


def main():
    disagreed = 0
    for cents in range(LIMIT):
        try:
            theirs = change.make_change(cents)
        except Exception as error:  # noqa: BLE001 - a raise is a result to compare
            theirs = ("raised", type(error).__name__)
        try:
            ours = make_change(cents)
        except Exception as error:  # noqa: BLE001
            ours = ("raised", type(error).__name__)
        if theirs != ours:
            disagreed += 1
            if disagreed <= 5:
                print(
                    f"benchproofer:disagrees change.make_change {cents} -> the "
                    f"repository returns {theirs}, the shadow returns {ours}"
                )
    print(
        f"benchproofer:compared change.make_change {LIMIT} every amount from 0 to "
        f"{LIMIT - 1}, the boundary at 0 included"
    )
    raise SystemExit(1 if disagreed else 0)


main()
