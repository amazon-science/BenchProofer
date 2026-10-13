"""Put the model of `posixpath.normpath` beside the callee it stands for.

The specification may not import `posixpath`, so it carries a model of the one
function it needs and declares that the model stands in for the real thing. That
declaration is what this program is about. It draws every relative path the
implementation could hand the normalizer, and a good many it could not, and asks the
two to agree on each one.
"""

import posixpath

# Collapsing `.` and `..` out of a path is the standard library's job, and this task
# is not about how it does it, so the specification models it: the definition below
# stands for `posixpath.normpath` over relative paths, which is the only kind the
# implementation ever hands it. `axioms.py` is what puts the two side by side.
# benchproofer:models posixpath.normpath
def normpath(path):
    parts = []
    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        if segment == ".." and parts and parts[-1] != "..":
            parts.pop()
            continue
        parts.append(segment)
    return "/".join(parts) or "."


# The roots the specification draws, and the segments a request is built from -- plus
# several the specification never draws, because a model that agrees only on the tidy
# inputs is not one this task can lean on.
ROOTS = ("static", "var/data")
SEGMENTS = ("a", "b", "css", "app.css", "logs", ".", "..", "", "...", ".hidden", "a b")
DEPTH = 3


def requests():
    """Every path of up to DEPTH segments drawn from SEGMENTS."""
    found = {""}
    for _ in range(DEPTH):
        found |= {
            f"{head}/{segment}" if head else segment
            for head in found
            for segment in SEGMENTS
        }
    return found


def candidates():
    """What to compare on: each request, and each request joined onto a root."""
    asked = requests()
    return sorted(asked | {f"{root}/{request}" for root in ROOTS for request in asked})


def main():
    """Compare the model against the real callee, and say what was covered."""
    disagreements = []
    checked = 0
    for path in candidates():
        if path.startswith("/"):
            continue
        checked += 1
        mine, theirs = normpath(path), posixpath.normpath(path)
        if mine != theirs:
            disagreements.append((path, theirs, mine))

    for path, theirs, mine in disagreements[:20]:
        print(
            f"benchproofer:refuted posixpath.normpath normpath({path!r}) is {theirs!r}, "
            f"the model says {mine!r}"
        )
    if disagreements:
        return 1
    print(
        f"benchproofer:grounded posixpath.normpath {checked} relative paths: every "
        f"request of up to {DEPTH} segments over {len(SEGMENTS)} literals, each one "
        "also joined onto both roots"
    )
    return 0


raise SystemExit(main())
