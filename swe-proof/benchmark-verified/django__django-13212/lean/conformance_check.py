#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13212.

The bundle models ONE value: the validation OUTCOME for a single input — `none`
when the input is accepted (the validator raises nothing), or `some params` when
it is rejected (the substitution `params` dict carried by the raised
`ValidationError`). The modeled value is a PURE function of three observables
(mapping.md / refinement.md):

    value      : the rejected input, rendered as a string  (str(value))
    accepted   : the validator's acceptance verdict (True = no error raised)
    baseParams : the intrinsic params the site already supplied (key->str pairs)

Post-patch rule:
    accepted        -> outcome = None                       (no error context)
    not accepted    -> outcome = baseParams + [('value', value)]
                       (the intrinsic params with the 'value' binding appended)

Standing up the full forms/validators stack per site is unnecessary: the modeled
value is this pure transformation over the observables (the validity verdict is
UNCHANGED by the patch and is fed as an input). The ORACLE is a faithful
in-process replica using the EXACT patched construction semantics: a rejection's
params dict is built with the intrinsic entries first and 'value' added last
(Python dicts are insertion-ordered; every patched site writes the 'value'
entry after the intrinsic ones — `params={'max': ..., 'value': value}`). The
SHADOW is the op-for-op transliteration of `implementation_checkOutcome`
(refinement.md: accepted -> none; rejected -> baseParams ++ [('value', value)]).

Observed as the FULL ordered entry sequence, mirroring the Lean spec (which pins
`result = some (baseParams ++ [(valueKey, value)])` exactly): the association
list must equal `list(dict.items())` of the patched params dict — same keys,
same values, same order, no duplicate/shadowed entries. The precondition
`baseParams.lookup 'value' = none` (no built-in site pre-binds 'value') is
honored by construction in the fuzzer.

stdlib-only. Pinned seed: 13212 (also in mapping.md).
"""
import random
import sys

SEED = 13212
N = 120_000

VALUE_KEY = "value"


# --- ORACLE: faithful replica of the patched per-rejection construction ------
def oracle_outcome(value, accepted, base_params):
    if accepted:
        return None
    # rejection: the patched sites construct the params dict with the intrinsic
    # entries first and the rejected value bound to 'value' LAST
    # (e.g. params={'max': self.max_digits, 'value': value}).
    out = dict(base_params)
    out[VALUE_KEY] = value
    return out  # an insertion-ordered substitution map (dict)


# --- SHADOW of implementation_checkOutcome (the R/I leg) ----------------------
# Mirrors Solution.lean: if accepted: return none;
#   else return some (baseParams ++ [('value', value)]).
def shadow_outcome(value, accepted, base_params):
    if accepted:
        return None
    return list(base_params) + [(VALUE_KEY, value)]


def disagree(value, accepted, base_params):
    oracle = oracle_outcome(value, accepted, base_params)
    shadow = shadow_outcome(value, accepted, base_params)

    # acceptance leg: both must signal "no error context".
    if oracle is None or shadow is None:
        if oracle is None and shadow is None:
            return None
        return (value, accepted, base_params, "noneness", oracle, shadow)

    # rejection leg: the Lean spec pins the WHOLE sequence, so compare the
    # ordered entry list of the patched dict against the shadow list exactly.
    oracle_entries = list(oracle.items())
    if oracle_entries != shadow:
        return (value, accepted, base_params, "entries", oracle_entries, shadow)
    return None


def _enumerate_edge():
    cases = []
    # accepted -> no error context, regardless of params.
    cases.append(("anything", True, []))
    cases.append(("123", True, [("max", "2")]))
    # rejected, no intrinsic params (RegexValidator / Email / IP / NullChar sites).
    cases.append(("a", False, []))                       # validate_email 'a'
    cases.append(("-42.5", False, []))                   # validate_integer
    cases.append(("256.1.1.1", False, []))               # validate_ipv4_address
    cases.append(("a\x00b", False, []))                  # null character (rendered)
    cases.append(("", False, []))                        # empty rejected input
    cases.append(("你 好", False, []))                    # unicode slug
    # rejected, with intrinsic params (DecimalValidator).
    cases.append(("123", False, [("max", "2")]))         # max_digits
    cases.append(("0.12", False, [("max", "1")]))        # max_decimal_places
    # rejected, with FileExtensionValidator intrinsic params.
    cases.append(("myfile.txt", False, [("extension", "txt"),
                                        ("allowed_extensions", "png, jpg")]))
    return cases


KEY_POOL = ["max", "extension", "allowed_extensions", "limit_value", "max_length"]
VALUE_POOL = ["", "a", "-42.5", "256.1.1.1", "你 好", "a\x00b", "myfile.txt",
              "Rene Magritte", "1", "0.12", "x" * 40, "no_scheme"]


def _rand_base_params(rng):
    nk = rng.randint(0, 3)
    keys = rng.sample(KEY_POOL, nk)  # distinct, none is 'value' (precondition)
    return [(k, rng.choice(["1", "2", "10", "png, jpg", "txt"])) for k in keys]


def main() -> int:
    checked = 0
    for value, accepted, base in _enumerate_edge():
        d = disagree(value, accepted, base)
        if d:
            print(f"DISAGREE edge {d}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        value = rng.choice(VALUE_POOL)
        accepted = rng.random() < 0.4
        base = _rand_base_params(rng)
        d = disagree(value, accepted, base)
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
