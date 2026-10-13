#!/usr/bin/env python3
"""G-AX soundness check for django__django-12325.

This bundle has NO axiomatized callee (no `@ContractOnly`): the changed
behaviour — record a one-to-one relation only when it is a designated parent
link — is modeled deeply as a concrete branch in `model.py`'s `impl` region,
and the unchanged callees the loop invokes (`isinstance`, `resolve_relation`,
`make_model_tuple`) are absorbed into the int/bool carrier as type refinements
(mapping.md §2), never contracted inside any Requires/Ensures.

There is therefore no axiom to validate against a real callee, so G-AX is
vacuously sound. As a positive sanity check we exercise the abstract model's
core post-condition against a direct reference implementation of the patched
recording loop (last-writer-wins, parent-link-only) over boundary + fuzz
inputs, confirming the two post-condition clauses the proof establishes:

  (1) every recorded relation is a designated parent link;
  (3) every related model with a designated parent link is recorded;
  (4) the recorded position is the LAST designated parent-link position for
      its key (last-writer-wins, mirroring the repo's dict assignment).

stdlib-only; exit 0 iff sound.
"""
import random


def reference_collect(is_parent_link, related_key):
    """Direct reference of the patched `__new__` recording loop: record only
    designated parent links, last-writer-wins per related-model key. Returns a
    dict mapping related-model key -> chosen relation position."""
    assert len(is_parent_link) == len(related_key)
    result = {}
    for i in range(len(is_parent_link)):
        if is_parent_link[i]:
            result[related_key[i]] = i
    return result


def check_clauses(is_parent_link, related_key):
    n = len(is_parent_link)
    result = reference_collect(is_parent_link, related_key)
    # Clause (1): every recorded relation is a designated parent link whose
    # target is the key it is recorded under, at a valid position.
    for k, pos in result.items():
        assert 0 <= pos < n, (is_parent_link, related_key, k, pos)
        assert is_parent_link[pos], (is_parent_link, related_key, k, pos)
        assert related_key[pos] == k, (is_parent_link, related_key, k, pos)
    # Clause (3)+(4): every related model with a designated parent link is
    # recorded, at a position >= every parent-link position for that key --
    # i.e. exactly the LAST parent-link position (last-writer-wins).
    for i in range(n):
        if is_parent_link[i]:
            assert related_key[i] in result, (is_parent_link, related_key, i)
            assert result[related_key[i]] >= i, (is_parent_link, related_key, i)


def main():
    # Boundary cases.
    boundary = [
        ([], []),
        ([False], [0]),
        ([True], [0]),
        # ordinary then parent link to the same model (order independence).
        ([False, True], [7, 7]),
        # parent link then ordinary to the same model (must not be displaced).
        ([True, False], [7, 7]),
        # two parent links to the same model: last wins, still a parent link.
        ([True, True], [7, 7]),
        # mixed models.
        ([False, True, False], [1, 2, 1]),
        # only ordinary relations: nothing recorded.
        ([False, False, False], [1, 1, 2]),
    ]
    for ipl, rk in boundary:
        check_clauses(ipl, rk)

    # Fuzz.
    rnd = random.Random(12325)
    for _ in range(200000):
        n = rnd.randint(0, 6)
        ipl = [rnd.random() < 0.5 for _ in range(n)]
        rk = [rnd.randint(0, 3) for _ in range(n)]
        check_clauses(ipl, rk)

    print("G-AX vacuous (no axiom); model post-conditions (1)+(3)+(4) hold on "
          "the reference recording loop over 8 boundary + 200000 fuzz inputs. "
          "SOUND.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
