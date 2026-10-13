#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9711.

The changed operation — comparing two dotted release numbers — is modelled
DEEPLY in model.py by the @Pure comparator `version_gt` (segment-wise integer
comparison, a missing trailing segment counting as zero). There is NO consumed
@ContractOnly axiom; instead this script validates that deep model **== the real
release-number comparator** out of band (the A-reference of refinement.md).

The real comparator is `packaging.version.Version`'s ordering — the very
library the gold patch calls (``Version(reqversion) > Version(extension.version)``).
This script:

  (A-reference) asserts, for every tested pair of dotted release numbers (a..b),
      that the deep model `version_gt(a, b)` equals the real
      ``Version("a.b.…") > Version("c.d.…")``:
        - boundary cases: the issue's own examples, the F2P test's examples,
          equal versions, prefixes/zero-padding, single segment, long tails;
        - randomized fuzz over 1..4 segments with values 0..99.

The modelled domain is *valid dotted release numbers* — the inputs the
requirement check actually compares for the tested behaviour (the F2P test uses
"3.9", "3.10", "3.11"; the issue uses "0.6", "0.10"). For such inputs
``packaging.version.Version`` parses without raising ``InvalidVersion``, so the
modelled comparison path is exactly the executed path (the gold patch's
``InvalidVersion`` text fallback is never taken on these inputs; mapping.md §3).

Imports nothing repo-specific: `packaging` is the dependency the gold patch
imports. Exit 0 iff every obligation holds.
"""
import random
import sys

from packaging.version import InvalidVersion, Version


# --- model.py reference encoding (kept in lock-step with `version_gt`) --------

def version_gt(a, b):
    """Reference implementation of model.py's deep model `version_gt`, over the
    release-segment lists a and b: segment-wise integer comparison, a missing
    trailing segment counting as zero. Front-recursion in model.py is the same
    function here."""
    n = max(len(a), len(b))
    for i in range(n):
        sa = a[i] if i < len(a) else 0
        sb = b[i] if i < len(b) else 0
        if sa > sb:
            return True
        if sa < sb:
            return False
    return False


def _vstr(segments):
    return ".".join(str(s) for s in segments)


def check_version_reference(a, b):
    """Assert the deep model version_gt(a, b) == the REAL packaging ordering."""
    sa, sb = _vstr(a), _vstr(b)
    # both must parse (modelled domain = valid release numbers); InvalidVersion
    # here would mean the test input is outside the modelled domain.
    real = Version(sa) > Version(sb)            # real comparator
    model = version_gt(a, b)                    # deep model
    assert real == model, (
        "version_gt deep model unsound on (%r, %r): real Version compare gave "
        "%r, deep model gives %r" % (sa, sb, real, model))


def main():
    boundary = [
        # the issue's own example: 0.6 minimum, 0.10 loaded -> 0.6 NOT > 0.10
        ([0, 6], [0, 10]),
        ([0, 6, 0], [0, 10, 0]),
        ([0, 10], [0, 6]),
        # the F2P test's examples
        ([3, 9], [3, 10]),      # req 3.9 vs loaded 3.10 -> not greater
        ([3, 11], [3, 10]),     # req 3.11 vs loaded 3.10 -> greater
        ([3, 10], [3, 10]),     # equal
        # zero-padding / prefixes
        ([3], [3, 0]),
        ([3, 0], [3]),
        ([3, 0, 0], [3]),
        ([1], [2]),
        ([2], [1]),
        ([1, 0], [1, 0, 0]),
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, 3], [1, 2, 4]),
        ([1, 2, 4], [1, 2, 3]),
        ([0], [0]),
        ([10], [9]),            # the very inversion the issue describes
        ([9], [10]),
        ([0, 0, 1], [0, 0, 0]),
    ]
    for a, b in boundary:
        check_version_reference(a, b)

    # randomized fuzz over valid dotted release numbers
    rng = random.Random(9711)
    for _ in range(200000):
        na = rng.randint(1, 4)
        nb = rng.randint(1, 4)
        a = [rng.randint(0, 99) for _ in range(na)]
        b = [rng.randint(0, 99) for _ in range(nb)]
        check_version_reference(a, b)

    # sanity: confirm the modelled-domain assumption — these all parse
    for a, b in boundary:
        try:
            Version(_vstr(a))
            Version(_vstr(b))
        except InvalidVersion:  # pragma: no cover
            raise AssertionError(
                "boundary input %r/%r left the modelled valid-release domain"
                % (a, b))

    print("G-AX OK: version_gt deep model (== packaging.version.Version "
          "ordering) sound on %d boundary + 200000 fuzz release-number pairs"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
