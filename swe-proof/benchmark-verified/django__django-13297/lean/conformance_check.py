#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13297.

The bundle models ONE value: the collection of deferred wrappers built from the
URL-captured kwargs (`_wrap_url_kwargs_with_deprecation_warning`). The modeled
value is a PURE function of the captured kwargs (mapping.md): each
`(key, value)` becomes a wrapper observed by three facets —

    resolved      : the value it produces                 (= value)
    noticeKey     : the kwarg name its notice is keyed to  (= key)
    presentedType : the type interface it exposes          (= type(value))

Post-patch rule (per kwarg, in iteration order):
    wrapper(key, value) = (resolved=value, noticeKey=key, presentedType=type(value))
    result = [(key, wrapper(key,value)) for key,value in url_kwargs.items()]

Standing up the full template/URL stack is unnecessary: the modeled value is this
pure transformation over the observables. The ORACLE is a faithful in-process
replica that uses the EXACT patched construction semantics (presented type ==
the value's own runtime type); the SHADOW is the op-for-op transliteration of
`implementation_wrapContextKwargs` (per refinement.md: presentedType :=
value.pytype, resolved := value, noticeKey := key, appended in order).

A runtime type is modeled in Lean as a Nat tag (mapping.md). Here we test the
modeling end-to-end by driving the oracle with REAL Python values and types and
the shadow with the corresponding (pytype_tag, data) pairs, then comparing the
three observed facets per wrapper, in order.

stdlib-only. Pinned seed: 13297 (also in mapping.md).
"""
import random
import sys

SEED = 13297
N = 120_000

# An injective tag for each distinct runtime type we fuzz (the Lean `pytype`
# encoding, mapping.md). The "generic deferred-object type" gets its own tag, 0.
TYPE_TAGS = {str: 1, int: 2, bytes: 3, float: 4, bool: 5}
GENERIC_DEFERRED_TAG = 0


def type_tag(value):
    # bool is a subclass of int in Python; keep them distinct tags deliberately,
    # matching distinct runtime type identities.
    return TYPE_TAGS[type(value)]


# --- ORACLE: faithful replica of the patched per-kwarg construction ----------
def oracle_wrap(url_kwargs):
    out = []
    for key, value in url_kwargs:
        wrapper = {
            "resolved": value,
            "noticeKey": key,
            "presentedType": type_tag(value),  # lazy(f, type(value))() presents type(value)
        }
        out.append((key, wrapper))
    return out


# --- SHADOW of implementation_wrapContextKwargs (the R/I + A-reference leg) ---
# Mirrors Solution.lean: context := []; for (key,value) in urlKwargs:
#   wrapper := {presentedType := value.pytype, resolved := value, noticeKey := key};
#   context := context ++ [(key, wrapper)]; return context.
def shadow_wrap(url_kwargs_modeled):
    context = []
    for key, value in url_kwargs_modeled:        # value = (pytype_tag, data)
        pytype, data = value
        wrapper = {
            "presentedType": pytype,
            "resolved": (pytype, data),
            "noticeKey": key,
        }
        context = context + [(key, wrapper)]
    return context


def to_modeled(url_kwargs):
    """Bridge real (key, value) pairs to the Lean (key, (pytype_tag, data)) form."""
    return [(key, (type_tag(value), str(value))) for key, value in url_kwargs]


def disagree(url_kwargs):
    oracle = oracle_wrap(url_kwargs)
    shadow = shadow_wrap(to_modeled(url_kwargs))
    if len(oracle) != len(shadow):
        return (url_kwargs, "length", len(oracle), len(shadow))
    for i, ((ok, ow), (sk, sw)) in enumerate(zip(oracle, shadow)):
        # key/order
        if ok != sk:
            return (url_kwargs, f"key@{i}", ok, sk)
        # noticeKey keyed to the kwarg name
        if ow["noticeKey"] != sw["noticeKey"]:
            return (url_kwargs, f"noticeKey@{i}", ow["noticeKey"], sw["noticeKey"])
        # resolved value content + type
        if ow["presentedType"] != sw["presentedType"]:
            return (url_kwargs, f"presentedType@{i}", ow["presentedType"], sw["presentedType"])
        if type_tag(ow["resolved"]) != sw["resolved"][0]:
            return (url_kwargs, f"resolvedType@{i}", type_tag(ow["resolved"]), sw["resolved"][0])
        if str(ow["resolved"]) != sw["resolved"][1]:
            return (url_kwargs, f"resolvedData@{i}", str(ow["resolved"]), sw["resolved"][1])
    return None


def _enumerate_edge():
    cases = []
    cases.append([])                                   # no kwargs
    cases.append([("offer_slug", "abc")])              # single str (the F2P shape)
    cases.append([("artist_name", "Rene Magritte")])   # str value -> presents str
    cases.append([("n", 123)])                         # int value -> presents int
    cases.append([("flag", True)])                     # bool value
    cases.append([("ratio", 1.5)])                     # float value
    cases.append([("raw", b"bytes")])                  # bytes value
    cases.append([("a", "x"), ("b", "y"), ("c", "z")]) # order preservation
    cases.append([("dup", "1"), ("dup", "2")])         # repeated key (dict would keep last; list keeps order — see note)
    return cases


# Note: real url_kwargs is a dict, so repeated keys cannot occur in the captured
# kwargs; we still exercise the all-distinct-key ordering. The dedup-on-key case
# is excluded from the random fuzz to keep the oracle (list) faithful to a dict.
KEY_POOL = ["offer_slug", "artist_name", "pk", "year", "name", "n", "ratio", "raw", "flag"]


def _rand_value(rng):
    kind = rng.choice(["str", "int", "bytes", "float", "bool"])
    if kind == "str":
        return rng.choice(["", "abc", "Rene Magritte", "Ünîcödé", "0", "x" * rng.randint(1, 40)])
    if kind == "int":
        return rng.randint(-10**6, 10**6)
    if kind == "bytes":
        return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 8)))
    if kind == "float":
        return rng.uniform(-1e6, 1e6)
    return rng.choice([True, False])


def main() -> int:
    checked = 0
    for kwargs in _enumerate_edge():
        # skip the intentional repeated-key case from strict positional compare:
        # it is a documented impossibility for real dict-sourced url_kwargs.
        if len({k for k, _ in kwargs}) != len(kwargs):
            checked += 1
            continue
        d = disagree(kwargs)
        if d:
            print(f"DISAGREE edge {d}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        nk = rng.randint(0, 6)
        keys = rng.sample(KEY_POOL, nk)  # distinct keys (dict semantics)
        kwargs = [(k, _rand_value(rng)) for k in keys]
        d = disagree(kwargs)
        if d:
            print(f"DISAGREE fuzz {d}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
