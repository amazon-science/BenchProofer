#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12304.

The bundle models ONE behavior: the enumerated-choices class produced by the
metaclass constructor (`ChoicesMeta.__new__`, `django/db/models/enums.py`),
restricted to its two touched observables (mapping.md):

    value2label            : list[(int, str)]  (cls._value2label_map_, member order)
    do_not_call_in_templates : bool            (the attribute the patch adds)

Post-patch rule (the gold fix): the constructed class exposes the value→label
association built from its members UNCHANGED, and is marked
`do_not_call_in_templates = True`.

The behavioral consequence the F2P test exercises is the template variable
resolver's call decision (`Variable._resolve_lookup`, django/template/base.py:
851-856):

    if callable(current):
        if getattr(current, 'do_not_call_in_templates', False):
            pass                       # leave the class intact -> member lookup works
        elif getattr(current, 'alters_data', False):
            current = string_if_invalid
        else:
            current = current()        # call with no args -> TypeError for an enum class

An enum class is always callable and never alters_data, so the engine invokes it
iff the flag is absent. Standing up Django's template engine over a live enum is
heavy and unnecessary: the modeled value is this pure decision over the two
observables. So the ORACLE is a faithful in-process replica of the patched
constructor + the engine's call decision, and the SHADOW is the op-for-op
transliteration of `implementation_buildChoicesClass` fed through the same
decision `templateWouldCall` (per refinement.md).

We compare, for every input:
  * the produced value→label association (frame clause), AND
  * whether the engine WOULD invoke the produced class (must be False).

stdlib-only. Pinned seed: 12304 (also in mapping.md).
"""
import random
import sys

SEED = 12304
N = 120_000


# An enum class is always callable and never alters_data (mapping.md).
IS_CALLABLE = True
ALTERS_DATA = False


def template_would_call(is_callable, do_not_call, alters_data):
    # Variable._resolve_lookup, base.py:851-856.
    return is_callable and (not do_not_call) and (not alters_data)


# --- ORACLE: faithful in-process replica of the PATCHED constructor ----------
def oracle_build(member_values):
    # cls._value2label_map_ is built from the members (unchanged);
    # cls.do_not_call_in_templates = True (the added line).
    value2label = list(member_values)
    do_not_call = True
    return value2label, do_not_call


# --- SHADOW of implementation_buildChoicesClass (R/I leg, op-for-op) ----------
def shadow_build(member_values):
    value2label = list(member_values)          # cls.value2label := memberValues
    do_not_call = False                        # accumulator init
    value2label = list(member_values)          # cls with value2label := memberValues
    do_not_call = True                         # cls with doNotCallInTemplates := true
    return value2label, do_not_call


def disagree(member_values):
    o_v2l, o_dnc = oracle_build(member_values)
    s_v2l, s_dnc = shadow_build(member_values)
    # frame clause: value->label association unchanged and equal on both legs.
    if o_v2l != s_v2l:
        return (member_values, "value2label", o_v2l, s_v2l)
    # discriminating clause: the engine must NOT invoke the produced class.
    o_call = template_would_call(IS_CALLABLE, o_dnc, ALTERS_DATA)
    s_call = template_would_call(IS_CALLABLE, s_dnc, ALTERS_DATA)
    if o_call != s_call:
        return (member_values, "would_call", o_call, s_call)
    if o_call is not False:
        return (member_values, "would_call_not_false", o_call, s_call)
    return None


LABEL_POOL = ["Diamond", "Heart", "Spade", "Club", "Fresh man", "Sophomore",
              "", "A b C", "Senior", "Junior"]


def _enumerate_edge():
    cases = []
    # the reported Suit shape: integer values 1..4 with labels.
    cases.append([(1, "Diamond"), (2, "Heart"), (3, "Spade"), (4, "Club")])
    # the precise F2P read: Suit.DIAMOND -> value 1, label 'Diamond'.
    cases.append([(1, "Diamond")])
    # empty enum (no members).
    cases.append([])
    # negative / zero values.
    cases.append([(0, "Zero"), (-1, "Neg")])
    # duplicate labels across members.
    cases.append([(1, "X"), (2, "X")])
    return cases


def main() -> int:
    checked = 0
    for mv in _enumerate_edge():
        d = disagree(mv)
        if d:
            print(f"DISAGREE edge {d[0]!r}: clause={d[1]} oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 8)
        mv = [(rng.randint(-1000, 1000), rng.choice(LABEL_POOL)) for _ in range(k)]
        d = disagree(mv)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: clause={d[1]} oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
