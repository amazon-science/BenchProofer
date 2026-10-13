#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15127.

The bundle models ONE decision: the value the cached level->tag mapping
(`base.LEVEL_TAGS`) takes after a configuration change, as maintained by the
gold `update_level_tags` receiver. The modeled value is a PURE function of four
observables (mapping.md):

    tagsSettingChanged : bool                 (setting == 'MESSAGE_TAGS')
    defaultTags        : list[(int, str)]     (constants.DEFAULT_TAGS items)
    overrideTags       : list[(int, str)]     (settings.MESSAGE_TAGS items)
    prevTagMap         : list[(int, str)]     (cached LEVEL_TAGS before the change)

Post-patch rule (the receiver):

    if setting == 'MESSAGE_TAGS':
        base.LEVEL_TAGS = get_level_tags()    # {**DEFAULT_TAGS, **MESSAGE_TAGS}
    # else: base.LEVEL_TAGS unchanged

Standing up Django's apps/signals machinery to drive the real receiver is heavy
and unnecessary: the modeled value is this pure decision over observables. So the
ORACLE below is a faithful in-process replica that uses the EXACT patched
expression (`{**defaults, **overrides}` dict-spread), and the SHADOW is the
op-for-op transliteration of `implementation_resolveTagMap`
(`overrideTags ++ defaultTags` under first-match lookup, per refinement.md).

A dict[int,str] is membership/override determined, so we compare the two legs AS
THE DICT THEY DENOTE (mapping.md): the shadow reaches the mapping via an
assoc-list `overrides ++ defaults` collapsed by first-match, the oracle via the
dict spread; they must agree for every input -- in particular when a level is
present in both sources (override-wins) and when the changed setting is not the
override (cache left untouched).

stdlib-only. Pinned seed: 15127 (also in mapping.md).
"""
import random
import sys

SEED = 15127
N = 120_000


# --- ORACLE: faithful in-process replica of the patched receiver -------------
def oracle_resolve(tags_changed, default_tags, override_tags, prev_map):
    if tags_changed:
        # get_level_tags() == {**DEFAULT_TAGS, **MESSAGE_TAGS}
        return {**dict(default_tags), **dict(override_tags)}
    return dict(prev_map)


# --- SHADOW of implementation_resolveTagMap (the R/I leg) --------------------
# Mirrors Solution.lean: tagMap := prevTagMap; if tagsSettingChanged then
# tagMap := mergeTags defaultTags overrideTags (= overrideTags ++ defaultTags);
# return tagMap.  Collapsed to its denoted dict by FIRST-match lookup.
def _assoc_to_dict_first_match(pairs):
    d = {}
    for k, v in pairs:
        if k not in d:          # first occurrence wins
            d[k] = v
    return d


def shadow_resolve(tags_changed, default_tags, override_tags, prev_map):
    tag_map = list(prev_map)
    if tags_changed:
        tag_map = list(override_tags) + list(default_tags)   # mergeTags
    return _assoc_to_dict_first_match(tag_map)


def disagree(tc, dt, ot, pm):
    got = oracle_resolve(tc, dt, ot, pm)        # compared as dicts (mapping.md)
    want = shadow_resolve(tc, dt, ot, pm)
    if got != want:
        return ((tc, dt, ot, pm), got, want)
    return None


# Django message levels (constants.py) + a custom level (the F2P uses 12).
LEVELS = [10, 20, 25, 30, 40, 12, 50, 0]
TAGVALS = ["debug", "info", "success", "warning", "error", "", "custom", "bad",
           "x"]
DEFAULT_TAGS = [(10, "debug"), (20, "info"), (25, "success"),
                (30, "warning"), (40, "error")]


def _enumerate_edge():
    cases = []
    # The F2P shape: override remaps several levels (some to '') + adds custom 12.
    f2p_override = [(20, "info"), (10, ""), (30, ""), (40, "bad"),
                    (25, ""), (12, "custom")]
    for tc in (True, False):
        # empty override -> merged == defaults
        cases.append((tc, DEFAULT_TAGS, [], []))
        cases.append((tc, DEFAULT_TAGS, [], list(DEFAULT_TAGS)))
        # the F2P override
        cases.append((tc, DEFAULT_TAGS, f2p_override, list(DEFAULT_TAGS)))
        # override that only overlaps (override-wins precedence)
        cases.append((tc, DEFAULT_TAGS, [(20, "INFO"), (40, "ERR")],
                      list(DEFAULT_TAGS)))
        # override adds a brand-new key not in defaults
        cases.append((tc, DEFAULT_TAGS, [(12, "custom")], list(DEFAULT_TAGS)))
        # stale prev map distinct from both -> when not changed, must be returned
        cases.append((tc, DEFAULT_TAGS, f2p_override, [(99, "stale")]))
        # empty defaults
        cases.append((tc, [], f2p_override, list(DEFAULT_TAGS)))
    return cases


def _rand_pairs(rng, maxlen):
    # The Python sources (DEFAULT_TAGS, MESSAGE_TAGS, LEVEL_TAGS) are genuine
    # dicts: keys are UNIQUE within a single source (mapping.md). Keys still
    # OVERLAP across defaults vs overrides -- that cross-source overlap is what
    # exercises override-wins precedence; intra-source duplicates cannot occur.
    n = rng.randint(0, min(maxlen, len(LEVELS)))
    keys = rng.sample(LEVELS, n)
    return [(k, rng.choice(TAGVALS)) for k in keys]


def main() -> int:
    checked = 0
    for tc, dt, ot, pm in _enumerate_edge():
        d = disagree(tc, dt, ot, pm)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        tc = rng.choice([True, False])
        # defaults: usually the real DEFAULT_TAGS, sometimes fuzzed
        dt = list(DEFAULT_TAGS) if rng.random() < 0.5 else _rand_pairs(rng, 6)
        ot = _rand_pairs(rng, 6)
        pm = _rand_pairs(rng, 6)
        d = disagree(tc, dt, ot, pm)
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
