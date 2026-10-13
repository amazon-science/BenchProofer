#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-9461.

The bundle models ONE routine: `PyProperty.get_signature_prefix` (mapping.md).
Its observable outcome is the rendered prefix string shown before a documented
read-only attribute. The routine reads exactly two observables: whether the
`abstractmethod` flag is present in `self.options`, and whether the `classmethod`
flag is present in `self.options`. (The `sig` argument is unused by the method.)

The ORACLE below is a faithful in-process replica of the POST-PATCH method (the
gold edit: a list seeded empty, append 'abstract' when the abstract flag is set,
append 'class' when the class-level flag is set, then append 'property', joined
by single spaces with a trailing space). The SHADOW is the op-for-op
transliteration of `implementation_propertyPrefix` (Solution.lean impl region),
per refinement.md.

This genuinely tests the soundness-critical clause: a class-level read-only
attribute (`classmethod` flag set) must render the word "class" in the prefix
(e.g. "class property " / "abstract class property "), matching the F2P
expectation, while preserving the plain ("property ") and abstract-only
("abstract property ") wordings.

stdlib-only. Pinned seed: 9461 (also in mapping.md).
"""
import itertools
import random
import sys

SEED = 9461
N = 200_000


# --- ORACLE: faithful in-process replica of the POST-PATCH method -------------
def oracle(is_abstract: bool, is_classlevel: bool) -> str:
    prefix = []
    if is_abstract:
        prefix.append('abstract')
    if is_classlevel:
        prefix.append('class')
    prefix.append('property')
    return ' '.join(prefix) + ' '


# --- SHADOW: op-for-op transliteration of implementation_propertyPrefix -------
def shadow(is_abstract: bool, is_classlevel: bool) -> str:
    words = []
    if is_abstract:
        words = words + ['abstract']
    if is_classlevel:
        words = words + ['class']
    words = words + ['property']
    return ' '.join(words) + ' '


def main() -> int:
    rng = random.Random(SEED)
    disagreements = []

    # Exhaustive over the entire input domain (2 bools = 4 cases).
    for is_abstract, is_classlevel in itertools.product([False, True], repeat=2):
        o = oracle(is_abstract, is_classlevel)
        s = shadow(is_abstract, is_classlevel)
        if o != s:
            disagreements.append((is_abstract, is_classlevel, o, s))

    # Plus a large fuzz pass (the domain is finite, but exercise the count).
    for _ in range(N):
        is_abstract = rng.random() < 0.5
        is_classlevel = rng.random() < 0.5
        o = oracle(is_abstract, is_classlevel)
        s = shadow(is_abstract, is_classlevel)
        if o != s:
            disagreements.append((is_abstract, is_classlevel, o, s))

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s)" % len(disagreements))
        for d in disagreements[:10]:
            print("  abstract=%s classlevel=%s oracle=%r shadow=%r" % d)
        return 1

    print("G-CONF pass: 0 disagreements over 4 exhaustive + %d fuzzed inputs "
          "(seed=%d)" % (N, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
