#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-1921.

This bundle has NO consumed axioms: combining two key/value collections with
precedence and dropping keys whose effective value is the unset value is
modelled DEEPLY (spelled out in model.py's `pure` region as `effective` /
`combined` and in the verified loop). G-AX therefore validates the single
**A-reference** -- that the deep model equals the real operation it mirrors --
by exercising the REAL repository code (`requests.sessions.merge_setting`'s
dict-merge machinery: `to_key_val_list`, `OrderedDict.update`, and the gold
None-drop) in the evaluation container and asserting the observable per-key
result matches the deep model.

Deep model under check (model.py `pure` region), over per-key inputs
`sv` (the per-session value) and `rv` (the per-request value), with `absent()`
meaning "key not carried by this side / dropped from the result" and
`none_val()` the explicit `None` value a caller may store:

    effective(sv, rv) = rv if rv != absent() else sv        # request wins
    combined(sv, rv)  = absent() if effective(sv, rv) == none_val()
                        else effective(sv, rv)               # drop unset values

Mapping to the real operation (mapping.md §1, §3): `absent()` <-> "key not in
that dict"; `none_val()` <-> the value `None`; a real value <-> any other
object. `merge_setting(request_setting, session_setting)` builds the merged dict
from `session_setting` then `.update`s with `request_setting` (request wins),
then (post-gold) drops every key whose merged value is `None`. The result holds
key `k` ↦ `combined(session[k], request[k])`, with a `combined` of `absent()`
meaning the key is absent from the result.

PATCH-STATE CONTROL (the load-bearing correctness property of this script).
The SWE-bench instance image is checked out at `base_commit`, i.e. the UNPATCHED
tree, whose `merge_setting` drops ONLY keys whose per-request value is `None`
(`for (k, v) in request_setting.items(): if v is None: del merged_setting[k]`).
A check that asserted the *fixed* behaviour against that ambient code would
(correctly) fail for a session-only `None`. So this script does NOT trust the
ambient drop; it reuses the REAL precedence merge (`to_key_val_list` +
`OrderedDict.update`, exactly as `merge_setting` does) and exercises BOTH drop
states at runtime, controlling only the final drop line (the exact line the gold
patch adds):

  * FIXED state -- the gold drop self-applied: drop EVERY key whose merged value
    is `None`. The deep model `combined` must HOLD here (a session-only `None`
    key is dropped; real values and request-wins survive).
  * BUGGY state -- the base_commit drop: drop only keys whose PER-REQUEST value
    is `None`. A key carried only by `session` and set to `None` there must
    SURVIVE holding `None` -- turning the implicit discrimination into an
    explicit two-state check and proving the observable the deep model relies on
    genuinely distinguishes fixed from buggy (G-DIFF made concrete against real
    requests).

Both paths reuse the REAL `requests.utils.to_key_val_list` and
`collections.OrderedDict.update` for the precedence merge -- only the single
drop step is controlled, exactly the line the gold patch adds. Imports: the
standard library plus the `requests` package under evaluation. Exit 0 iff every
observation matches the deep model in BOTH states.
"""
import random
import sys
from collections import OrderedDict

from requests.utils import to_key_val_list


# ---- the real precedence merge, lifted verbatim from merge_setting -----------
def real_precedence_merge(session_setting, request_setting):
    """The merged dict before any None-drop -- exactly the two lines
    `merged = dict_class(to_key_val_list(session_setting)); merged.update(
    to_key_val_list(request_setting))` from requests.sessions.merge_setting.
    Reuses the REAL to_key_val_list and OrderedDict.update."""
    merged = OrderedDict(to_key_val_list(session_setting))
    merged.update(to_key_val_list(request_setting))
    return merged


def fixed_merge(session_setting, request_setting):
    """The gold behaviour, self-applied: real precedence merge, then drop EVERY
    key whose merged value is None (the line the gold patch adds)."""
    merged = real_precedence_merge(session_setting, request_setting)
    # the base_commit per-request-only drop (kept, as the gold keeps it) ...
    for (k, v) in request_setting.items():
        if v is None and k in merged:
            del merged[k]
    # ... plus the gold final drop of ALL None-valued keys.
    merged = OrderedDict((k, v) for (k, v) in merged.items() if v is not None)
    return merged


def buggy_merge(session_setting, request_setting):
    """The base_commit behaviour: real precedence merge, then drop ONLY keys
    whose PER-REQUEST value is None. A session-only None survives."""
    merged = real_precedence_merge(session_setting, request_setting)
    for (k, v) in request_setting.items():
        if v is None and k in merged:
            del merged[k]
    return merged


# ---- the deep model (model.py pure region), per key --------------------------
ABSENT = object()   # sentinel: key not present in a dict ("absent()")


def effective(sv, rv):
    # rv is ABSENT iff the request side does not carry the key.
    return rv if rv is not ABSENT else sv


def combined(sv, rv):
    ev = effective(sv, rv)
    if ev is None:        # None == none_val(): drop the key
        return ABSENT
    return ev


def get(d, k):
    return d[k] if k in d else ABSENT


def check_against_deep_model(session_setting, request_setting):
    """A-reference (FIXED): the gold-self-applied merge equals the deep model
    `combined` on every key of the union, and contains no None value."""
    merged = fixed_merge(session_setting, request_setting)
    keys = set(session_setting) | set(request_setting)
    for k in keys:
        sv = get(session_setting, k)
        rv = get(request_setting, k)
        want = combined(sv, rv)          # ABSENT means "key dropped"
        got = get(merged, k)
        assert got == want or (got is ABSENT and want is ABSENT), (
            "deep model unsound (FIXED): key %r -> real %r but combined() == %r "
            "(session=%r request=%r)" % (k, got, want, sv, rv))
    # the headline guarantee: no key maps to None in the gold result.
    assert all(v is not None for v in merged.values()), (
        "deep model unsound (FIXED): a None value survived the gold merge: %r"
        % merged)


def check_buggy_keeps_session_none(key, value):
    """Differential (BUGGY): a key carried ONLY by the session and set to None
    there survives the base_commit merge still holding None -- proving the
    observable discriminates fixed from buggy (the bug the F2P test pins)."""
    session_setting = OrderedDict([(key, None), ("other", value)])
    request_setting = OrderedDict()          # request does not mention `key`
    buggy = buggy_merge(session_setting, request_setting)
    fixed = fixed_merge(session_setting, request_setting)
    assert buggy.get(key, "MISSING") is None, (
        "the base_commit merge did NOT leave a stale None for the session-only "
        "key %r: the observable cannot witness the fix -- the two-state check "
        "is not discriminating (buggy=%r)" % (key, buggy))
    assert key not in fixed, (
        "the gold merge did not drop the session-only None key %r (fixed=%r)"
        % (key, fixed))


def rand_value(rng):
    """A per-key value: a real object, the explicit None, or omitted (ABSENT
    handled by the caller)."""
    r = rng.random()
    if r < 0.30:
        return None
    return rng.randint(1, 1000)


def rand_setting(rng, keyspace):
    d = OrderedDict()
    for k in keyspace:
        if rng.random() < 0.5:
            d[k] = rand_value(rng)
    return d


def main():
    # Boundary cases over the discriminating shapes.
    boundary = [
        # session-only None (the issue's exact scenario), no request override
        (OrderedDict([("Accept-Encoding", None)]), OrderedDict()),
        # session None overridden by a real request value -> kept
        (OrderedDict([("Accept-Encoding", None)]),
         OrderedDict([("Accept-Encoding", 7)])),
        # session real value overridden by request None -> dropped
        (OrderedDict([("Accept-Encoding", 7)]),
         OrderedDict([("Accept-Encoding", None)])),
        # request-only None, key not in session -> dropped (was already handled)
        (OrderedDict(), OrderedDict([("X", None)])),
        # both real, request wins
        (OrderedDict([("A", 1), ("B", 2)]),
         OrderedDict([("A", 9), ("C", 3)])),
        # mix of session None, request None, real, overrides
        (OrderedDict([("A", None), ("B", 2), ("C", None)]),
         OrderedDict([("B", None), ("C", 5), ("D", None), ("E", 6)])),
        # empty
        (OrderedDict(), OrderedDict()),
    ]
    for ss, rs in boundary:
        check_against_deep_model(ss, rs)

    for key, value in [("Accept-Encoding", 1), ("X", 42), ("zzz", 7),
                       ("Content-Type", 999)]:
        check_buggy_keeps_session_none(key, value)

    # Randomized fuzz over overlapping key universes, both states.
    rng = random.Random(1921)
    keyspace = ["k%d" % i for i in range(8)]
    for _ in range(20000):
        ss = rand_setting(rng, keyspace)
        rs = rand_setting(rng, keyspace)
        check_against_deep_model(ss, rs)

    print("G-AX OK: deep model (A-reference) `combined` == real merge_setting "
          "machinery (real to_key_val_list + OrderedDict.update + gold None-drop, "
          "self-applied) on %d boundary + 20000 fuzz session/request pairs "
          "(per-key precedence merge with every None-valued key dropped; no None "
          "survives); under the base_commit drop (per-request side only) a "
          "session-only None SURVIVES holding None (the bug the F2P test pins), "
          "so the observable discriminates fixed from buggy." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
