#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11477.

The bundle models ONE function: `RegexPattern.match` (`django/urls/resolvers.py`).
Its Lean implementation (`implementation_capture`) takes the outcome of scanning a
path against a route pattern and reshapes it into the consumer triple
`(leftover_path, positional, named)`:

    if outcome is None:        # no match
        return None
    named = [e for e in outcome.named if carries_value(e)]   # the fix: drop None
    positional = outcome.positional if not named else []
    return (path[outcome.consumed:], positional, named)

where `carries_value((name, value))` is `value is not None`.

This script transliterates that R/I impl into Python (`shadow_match`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH body of `RegexPattern.match`:

    match = outcome           # the re.Match object (or None)
    if match:
        kwargs = {k: v for k, v in match["groupdict"].items() if v is not None}
        args = () if kwargs else match["groups"]
        return (path[match["end"]:], args, kwargs)
    return None

We do NOT stand up Python's `re` engine: the modeled value is a pure reshaping of
the match observables (`end()`, `groupdict()`, `groups()`), so we feed both legs
the SAME synthetic match outcomes carrying those observables (mapping.md). The
captured string value is opaque — modeled by a small int or None (None == an
absent optional group, the case the patch fixes).

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`carriesValue` filter + the `named.isEmpty` positional fallback, whereas the
oracle reproduces the patched dict-comprehension + `() if kwargs else groups()`.
They must agree for every input — in particular when a named group is present
with value None (an absent optional group), the case the patch fixes.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11477 (also recorded in
mapping.md).
"""
import sys

SEED = 11477
N = 120_000


# --- ORACLE: the post-patch RegexPattern.match, faithful in-process replica ---
# An outcome is None (no match) or a dict with:
#   "end": int, "groupdict": list[(name, value-or-None)] (ordered, names distinct),
#   "groups": list[value-or-None].
# kwargs is an ordered association list (dict insertion order == declaration order).
def oracle_match(path, outcome):
    if outcome is None:
        return None
    # kwargs = {k: v for k, v in groupdict().items() if v is not None}
    kwargs = [(k, v) for (k, v) in outcome["groupdict"] if v is not None]
    # args = () if kwargs else groups()
    args = [] if kwargs else list(outcome["groups"])
    leftover = path[outcome["end"]:]
    return (leftover, args, kwargs)


# --- shadow of implementation_capture (the R/I leg) --------------------------
def carries_value(entry):
    # entry = (name, value-or-None); carriesValue = value.isSome
    return entry[1] is not None


def shadow_match(path, outcome):
    if outcome is None:
        return None
    named = []
    for entry in outcome["groupdict"]:
        if carries_value(entry):
            named.append(entry)
    positional = list(outcome["groups"]) if len(named) == 0 else []
    leftover = path[outcome["end"]:]
    return (leftover, positional, named)


def disagree(path, outcome):
    got = oracle_match(path, outcome)
    want = shadow_match(path, outcome)
    if got != want:
        return ((path, outcome), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the absent-optional-named-group fix."""
    p = "12rest"
    cases = [
        # no match
        ("anything", None),
        # both named groups present -> kwargs both, no positional
        (p, {"end": 2, "groupdict": [(1, "1"), (2, "2")], "groups": ["1", "2"]}),
        # optional named group absent (value None) -> dropped from kwargs.
        # /regex_optional/1/ : arg1 present, arg2 absent.
        ("1/", {"end": 2, "groupdict": [(1, "1"), (2, None)], "groups": ["1", None]}),
        # ALL named groups absent -> kwargs empty -> positional reported
        ("ab", {"end": 1, "groupdict": [(1, None)], "groups": ["x"]}),
        # no named groups at all -> kwargs empty -> positional reported
        ("xy", {"end": 1, "groupdict": [], "groups": ["x"]}),
        # named present but positional also present: positional suppressed
        ("z", {"end": 0, "groupdict": [(3, "v")], "groups": ["p", None]}),
        # consumed == len(path) -> leftover empty
        ("abc", {"end": 3, "groupdict": [(0, "a")], "groups": []}),
        # empty everything on a match
        ("", {"end": 0, "groupdict": [], "groups": []}),
    ]
    return cases


def _rand_value(rnd):
    # ~40% chance of None (an absent optional group); else a small int "string".
    if next(rnd) % 5 < 2:
        return None
    return next(rnd) % 100


def _rand_groupdict(rnd):
    length = next(rnd) % 7            # 0..6 named groups
    out = []
    used = set()
    for _ in range(length):
        nm = next(rnd) % 8            # names 0..7
        if nm in used:               # names are distinct in a regex
            continue
        used.add(nm)
        out.append((nm, _rand_value(rnd)))
    return out


def _rand_groups(rnd):
    length = next(rnd) % 5            # 0..4 positional groups
    return [_rand_value(rnd) for _ in range(length)]


def _rand_outcome(rnd, path):
    if next(rnd) % 7 == 0:
        return None                  # no match
    end = next(rnd) % (len(path) + 1)
    return {"end": end, "groupdict": _rand_groupdict(rnd), "groups": _rand_groups(rnd)}


def _rand_path(rnd):
    length = next(rnd) % 10
    return "".join(chr(ord("a") + (next(rnd) % 6)) for _ in range(length))


def main() -> int:
    checked = 0

    for path, outcome in _enumerate_edge():
        d = disagree(path, outcome)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        path = _rand_path(rnd)
        outcome = _rand_outcome(rnd, path)
        d = disagree(path, outcome)
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
