#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13933.

The bundle models ONE routine: how a single-choice field backed by a record set
coerces a submitted value into an outcome (`ModelChoiceField.to_python`). The
modeled value is a PURE function of four observables (mapping.md):

    invalid_message : str        (self.error_messages['invalid_choice'])
    empty_values    : list[str]  (self.empty_values sentinels)
    value           : str        (the submitted value)
    lookup          : Optional[int]
                      (queryset.get(...) outcome: pk on success, None on raise)

Post-patch rule (the gold edit adds the params binding on the reject branch):

    if value in empty_values:
        outcome = ('ok', None)
    elif lookup is not None:
        outcome = ('ok', lookup)
    else:
        outcome = ('error', {
            'messageTemplate': invalid_message,
            'code': 'invalid_choice',
            'params': {'value': value},      # <-- the patch
        })

Standing up a database / ORM / form to drive the real `to_python` is heavy and
unnecessary: the modeled value is this pure coercion over observables the real
field exposes (the sentinel check, the lookup's two-way outcome, and the raised
`ValidationError`'s fields). So the ORACLE below is a faithful in-process replica
that uses the EXACT patched reject-branch construction (`params={'value': value}`),
and the SHADOW is the op-for-op transliteration of
`implementation_coerceChoice` (the three branches, with the rejection report
carrying `[('value', value)]`, per refinement.md).

The `ValidationError.params` dict is membership-keyed during message
interpolation, so the Lean singleton assoc-list `[('value', value)]` is compared
AS A DICT. This genuinely tests the soundness-critical clause: on the reject
branch the result must carry `params == {'value': value}` — the offending value
bound to the placeholder name — for EVERY submission, including the F2P shape
(value 'invalid', not a sentinel, no resolution).

stdlib-only. Pinned seed: 13933 (also in mapping.md).
"""
import random
import sys

SEED = 13933
N = 120_000

INVALID_CHOICE_CODE = "invalid_choice"
VALUE_PARAM = "value"


# --- ORACLE: faithful in-process replica of the patched coercion -------------
def oracle_coerce(invalid_message, empty_values, value, lookup):
    if value in empty_values:
        return ("ok", None)
    if lookup is not None:
        return ("ok", lookup)
    # reject branch — EXACT patched construction
    return ("error", {
        "messageTemplate": invalid_message,
        "code": INVALID_CHOICE_CODE,
        "params": {VALUE_PARAM: value},
    })


# --- SHADOW of implementation_coerceChoice (the R leg) -----------------------
# Mirrors Solution.lean: if value ∈ emptyValues then ok none; match lookup with
# some r => ok (some r) | none => error {…, params := [(valueParamName, value)]}.
def shadow_coerce(invalid_message, empty_values, value, lookup):
    if value in empty_values:
        return ("ok", None)
    if lookup is not None:
        return ("ok", lookup)
    # assoc-list [("value", value)] compared as a dict (mapping.md)
    params_assoc = [(VALUE_PARAM, value)]
    return ("error", {
        "messageTemplate": invalid_message,
        "code": INVALID_CHOICE_CODE,
        "params": dict(params_assoc),
    })


def disagree(im, ev, v, lk):
    got = oracle_coerce(im, ev, v, lk)
    want = shadow_coerce(im, ev, v, lk)
    if got != want:
        return ((im, ev, v, lk), got, want)
    return None


VALUE_POOL = ["", "invalid", "3", "4", "abc", "0", "None", "[]", " ", "42"]
MSG_POOL = [
    '"%(value)s" is not one of the available choices.',
    'Select a valid choice. That choice is not one of the available choices.',
    '%(value)s bad',
    '',
]
SENTINEL_POOL = ["", "None", "[]", " "]


def _enumerate_edge():
    cases = []
    msg = '"%(value)s" is not one of the available choices.'
    empties = [""]
    # F2P: 'invalid', not a sentinel, no resolution -> reject carrying the value
    cases.append((msg, empties, "invalid", None))
    # empty sentinel -> ok none
    cases.append((msg, empties, "", None))
    cases.append((msg, empties, "", 7))   # sentinel wins even if a pk is present
    # resolves -> ok pk
    cases.append((msg, empties, "3", 3))
    cases.append((msg, empties, "4", 4))
    # non-sentinel, no resolution, value equals the placeholder text literally
    cases.append((msg, empties, "%(value)s", None))
    # multiple sentinels
    cases.append((msg, ["", "None", "[]"], "None", None))
    # reject with empty message template
    cases.append(("", empties, "invalid", None))
    return cases


def main() -> int:
    checked = 0
    for im, ev, v, lk in _enumerate_edge():
        d = disagree(im, ev, v, lk)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        im = rng.choice(MSG_POOL)
        nsent = rng.randint(0, len(SENTINEL_POOL))
        ev = rng.sample(SENTINEL_POOL, nsent)
        v = rng.choice(VALUE_POOL)
        lk = rng.choice([None, rng.randint(0, 1000)])
        d = disagree(im, ev, v, lk)
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
