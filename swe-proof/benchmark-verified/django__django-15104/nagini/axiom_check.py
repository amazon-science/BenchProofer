#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15104.

The two A-reference deep models in model.py are validated against the REAL
Python keyword-removal primitives they stand for. The keyword mapping is
modelled as a ``dict``; ``TO`` is the related-target keyword token. The model
contracts are functional (they relate a fresh result mapping to the input);
the real primitives the patch uses edit the mapping in place, so here we apply
the real primitive to a COPY and read the resulting mapping as the "result" --
observationally identical for the value comparison the detector performs.

  (A-reference) ``pop_default(d, k)``  ==  the broadly-applicable removal
      ``d.pop(k, None)``: applicable to EVERY mapping (never raises). Result:
      ``k`` absent, every other entry preserved, none introduced -- whether or
      not ``k`` was present.

  (A-reference) ``del_present(d, k)``  ==  the narrowly-applicable removal
      ``del d[k]``: applicable ONLY when ``k`` is present (its modelled
      precondition ``k in d``); on an absent ``k`` the real primitive RAISES
      ``KeyError`` -- i.e. it is undefined, exactly as the model's precondition
      states. When applicable: ``k`` absent, every other entry preserved.

The discriminating soundness fact the bundle relies on (G-DIFF / the issue):
``del d[k]`` is undefined (raises) on an absent key, whereas ``d.pop(k, None)``
is applicable everywhere -- so the model's ``del_present`` legitimately carries
the extra ``Requires(k in d)`` that ``pop_default`` does not.

Imports nothing repo-specific: only ``dict`` semantics from the language. Exit
0 iff every obligation holds.
"""
import copy
import random
import sys

TO = 0


def _assert_result_drops_key(before, result, k, label):
    """Assert `result` meets the shared Ensures of both removal models on the
    input `before`: k absent, every other entry preserved, none introduced."""
    assert k not in result, "%s unsound: key %r still present in result" % (label, k)
    for j, v in before.items():
        if j != k:
            assert j in result and result[j] == v, (
                "%s unsound: entry %r lost/changed (was %r, now %r)"
                % (label, j, v, result.get(j)))
    for j in result:
        assert j != k and j in before and result[j] == before[j], (
            "%s unsound: spurious/changed entry %r in result" % (label, j))


def check_pop_default(d, k):
    """Run the REAL d.pop(k, None) on a copy and assert pop_default's Ensures:
    applicable to every mapping (never raises), result drops k, rest preserved."""
    before = copy.deepcopy(d)
    result = copy.deepcopy(d)
    result.pop(k, None)                    # broadly-applicable primitive (no raise)
    _assert_result_drops_key(before, result, k, "pop_default")


def check_del_present(d, k):
    """del_present is modelled applicable ONLY when k in d. Validate BOTH halves:
      * when k in d: real `del d[k]` is applicable and meets the Ensures;
      * when k not in d: real `del d[k]` RAISES (undefined) -- which is exactly
        why the model carries Requires(k in d) and pop_default does not."""
    if k in d:
        before = copy.deepcopy(d)
        result = copy.deepcopy(d)
        del result[k]                      # narrowly-applicable primitive (here defined)
        _assert_result_drops_key(before, result, k, "del_present")
    else:
        raised = False
        result = copy.deepcopy(d)
        try:
            del result[k]
        except KeyError:
            raised = True
        assert raised, (
            "del_present precondition unsound: `del d[%r]` did NOT raise on an "
            "absent key %r (model wrongly claims it applicable)" % (k, k))


def main():
    # --- boundary mappings ----------------------------------------------------
    boundary = [
        {},                                    # empty -- the bug input shape
        {TO: 99},                              # only the target keyword
        {1: 10},                               # one non-target keyword, no TO
        {1: 10, 2: 20},                        # several non-target, no TO
        {TO: 99, 1: 10, 2: 20},                # target + others
        {TO: 0},                               # target with falsy value
        {0: 0, 1: 0, 2: 0, 3: 0},              # TO + others, repeated value
        {5: 5},                                # disjoint single key
        {TO: 7, 5: 5, 9: 9, 13: 13},           # target + scattered others
    ]
    for d in boundary:
        check_pop_default(d, TO)
        check_del_present(d, TO)

    # --- randomized fuzz -------------------------------------------------------
    rng = random.Random(15104)
    for _ in range(20000):
        d = {}
        n = rng.randint(0, 8)
        for _ in range(n):
            key = rng.randint(0, 6)            # key space straddles TO==0
            d[key] = rng.randint(-3, 50)
        # half the time guarantee TO present, half the time guarantee absent,
        # so both arms of del_present (applicable / raises) are exercised hard.
        coin = rng.random()
        if coin < 0.4:
            d[TO] = rng.randint(-3, 50)
        elif coin < 0.8:
            d.pop(TO, None)
        check_pop_default(d, TO)
        check_del_present(d, TO)

    print("G-AX OK: pop_default (== d.pop(k,None), applicable to any mapping) "
          "and del_present (== del d[k], applicable only when k present: raises "
          "on absent key) sound on %d boundary + 20000 fuzz mappings"
          % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
