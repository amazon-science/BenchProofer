"""Compare the verified implementation with the code the task's own fix leaves.

The shadow below is `shadow.py` verbatim. The module beside it is the task as the
benchmark solves it, so `paths.safe_join` is the function the shadow represents.
"""

# benchproofer:target paths.py
"""The verified implementation, copied to run where the benchmark's tests run.

`normpath` is bound here to the callee the specification only modeled, which is the
whole point of this copy: the checker reasoned about a model of it, and this
is the same implementation running against the real thing.
"""

from posixpath import normpath


# benchproofer:begin impl
def impl(root, relative):
    if relative.startswith("/"):
        return None
    joined = normpath(root + "/" + relative)
    if joined == root or joined.startswith(root + "/"):
        return joined
    return None
# benchproofer:end impl


def safe_join(root, relative):
    """Expose the verified implementation under the name the task uses."""
    return impl(root, relative)

import random

import paths

LIMIT = 100_000
ROOTS = ("static", "var/data", "a")
#: The segments an attacker reaches for, plus the ones that merely look odd.
SEGMENTS = ("..", ".", "", "x", "y.txt", "/", "//", "..x", "x..", "\u00e9")


def main():
    rng = random.Random(20260922)
    disagreed = 0
    for _ in range(LIMIT):
        root = rng.choice(ROOTS)
        relative = "/".join(rng.choice(SEGMENTS) for _ in range(rng.randrange(1, 4)))
        theirs = paths.safe_join(root, relative)
        ours = safe_join(root, relative)
        if theirs != ours:
            disagreed += 1
            if disagreed <= 5:
                print(
                    f"benchproofer:disagrees paths.safe_join ({root!r}, {relative!r}) "
                    f"-> the repository returns {theirs!r}, the shadow returns {ours!r}"
                )
    print(
        f"benchproofer:compared paths.safe_join {LIMIT} joins of a root with a "
        "relative path built from traversal, empty and unicode segments"
    )
    raise SystemExit(1 if disagreed else 0)


main()
