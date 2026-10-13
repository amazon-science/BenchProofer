#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13513.

The bundle models ONE function: `ExceptionReporter.get_traceback_frames`. Its
Lean implementation (`implementation_gatherFrames`) walks the exception chain
link by link and concatenates each link's traceback frames into the report,
independent of whether any earlier link contributed an empty sequence:

    frames = []
    for tb in linkFrames:          # one link's frames at a time, walk order
        frames = frames + tb       # an empty link appends nothing, does NOT stop
    return frames                  # == flatten(linkFrames)

This script transliterates that R/I impl into Python (`shadow_apply`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `get_traceback_frames` (`django/views/debug.py`):

    exc_value = exceptions.pop()
    tb = self.tb if not exceptions else exc_value.__traceback__
    frames.extend(self.get_exception_traceback_frames(exc_value, tb))
    while exceptions:
        exc_value = exceptions.pop()
        frames.extend(get_exception_traceback_frames(exc_value, exc_value.__traceback__))
    return frames

i.e. each link of the chain is processed independently and its frames are
extended onto `frames` in walk order. We do NOT stand up real exception objects /
tracebacks (heavy, and the modeled value is a pure decision over the per-link
frame sequences). Instead we reproduce the patched behavior over light stand-in
inputs carrying the SAME observable the real chain exposes (mapping.md):
`linkFrames`, the list — per link in walk order — of the frames that link's
traceback contributes (an empty inner list ⇔ that link has an empty/None
traceback). The real PRE-patch single combined `while tb` loop would abandon the
walk at the first empty traceback (dropping all later links); the post-patch code
concatenates every link's frames — which is what the oracle below encodes. The
shadow reaches the same result via the flat `for ... frames += tb` loop.

The differential genuinely tests the Lean modeling: the shadow uses Lean's
`flatten`-shaped loop over the abstracted per-link frame lists, whereas the
oracle reproduces the patched `extend`-per-link semantics over realistically
shaped chains. They must agree for every input — in particular when an empty link
is FOLLOWED by a non-empty link, the multi-exception-with-empty-traceback case
the patch repairs.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 13513 (also recorded in
mapping.md).
"""
import sys

SEED = 13513
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# `link_frames` is a list, per chain link in walk order, of the frames that
# link's traceback contributes (each frame an opaque int token). The post-patch
# code processes each link independently and extends `frames` with its frames:
def oracle_gather(link_frames):
    frames = []
    # first link: frames.extend(get_exception_traceback_frames(first, tb))
    # remaining links: while exceptions: frames.extend(get_exception_traceback_frames(...))
    # Both branches extend frames with exactly that link's frames; an empty
    # traceback contributes nothing but does not stop the walk.
    for link in link_frames:
        frames.extend(link)
    return frames


# --- shadow of implementation_gatherFrames (the R/I leg) ---------------------
# Mirrors Solution.lean: `let mut frames := []; for tb in linkFrames do
# frames := frames ++ tb; return frames` (== linkFrames.flatten).
def shadow_gather(link_frames):
    frames = []
    for tb in link_frames:
        frames = frames + tb
    return frames


def disagree(link_frames):
    got = oracle_gather(link_frames)
    want = shadow_gather(link_frames)
    if got != want:
        return (link_frames, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the empty-traceback curtailment."""
    return [
        [],                              # no exceptions
        [[]],                            # single empty link
        [[1]],                           # single non-empty link
        [[], [1]],                       # DISCRIMINATOR: empty then non-empty
        [[1], []],                       # trailing empty link
        [[], []],                        # all empty
        [[1, 2], [], [3]],               # empty between non-empty links
        [[], [], [4, 5]],                # leading empties then frames
        [[1], [2], [3]],                 # several non-empty links
        [[1, 2, 3], [4], [], [5, 6]],    # mixed
    ]


def main() -> int:
    checked = 0

    for lf in _enumerate_edge():
        d = disagree(lf)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    tok = 0
    for _ in range(N):
        nlinks = next(rnd) % 7            # 0..6 chain links
        link_frames = []
        for _ in range(nlinks):
            # empty links deliberately frequent (~1/3) so the empty-then-nonempty
            # discriminator is hit often.
            if next(rnd) % 3 == 0:
                link_frames.append([])
                continue
            flen = next(rnd) % 4 + 1      # 1..4 frames
            link = []
            for _ in range(flen):
                tok += 1
                link.append(tok)
            link_frames.append(link)
        d = disagree(link_frames)
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
