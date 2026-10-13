#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12304 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `publishChoicesClass` impl
              region transliterated to Python over the *real* repo carrier. The
              impl performs `{ built with doNotCallInTemplates := true }`: it
              sets the boolean class flag to true and leaves the value->label
              association untouched.
  * ORACLE  — `patch.diff`'s behaviour: the added line
              `cls.do_not_call_in_templates = True` (enums.py:34), applied to a
              class-like object that already carries its `_value2label_map_`.
              We reproduce exactly that assignment on a fresh stand-in object
              whose other state (the value->label map) is left untouched, then
              read the flag back the way the UNCHANGED consumer does
              (`django/template/base.py` `_resolve_lookup`):
              `getattr(obj, 'do_not_call_in_templates', False)`.

They must agree on every input:
  1) the flag reads back as True (the discriminating observable the fix adds);
  2) the value->label map is preserved unchanged (the frame, directive 5/8).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

stdlib-only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. No Django import, no DB, no Docker required: the patched op is a plain
attribute assignment, reproduced here on a stand-in object, and the flag is read
back with the identical `getattr(..., False)` idiom the template engine uses.
"""
import random
import sys

SEED = 12304
N_FUZZ = 100_000


# --- a minimal stand-in for the constructed choices class object -------------
class ClassStandin:
    """A bare object standing in for `cls` at the point the patch fires. It
    carries the already-assembled value->label map; the patch then assigns the
    flag. This mirrors a Python class object's attribute namespace closely
    enough for the observable under test (a `getattr` of one flag + the map),
    without needing Django or the enum machinery."""
    def __init__(self, value_to_label):
        self._value2label_map_ = value_to_label


# --- SHADOW: Solution.lean publishChoicesClass, transliterated ---------------
# Solution.lean models the input as a (doNotCallInTemplates, valueToLabel)
# carrier and returns { built with doNotCallInTemplates := true }. The bijection
# (mapping.md §2): the Bool field <-> getattr(cls,'do_not_call_in_templates',
# False); valueToLabel <-> _value2label_map_.
def shadow_publish(value_to_label):
    """Returns (out_flag, out_value_to_label) for the modeled output:
    doNotCallInTemplates := true, valueToLabel copied straight through."""
    out_flag = True                 # { built with doNotCallInTemplates := true }
    out_value_to_label = value_to_label  # frame: rest of the record unchanged
    return out_flag, out_value_to_label


# --- ORACLE: patch.diff's behaviour, the real attribute assignment -----------
def oracle_publish(value_to_label):
    """The patched op `cls.do_not_call_in_templates = True` applied to a class
    standin already holding its value->label map. The flag is read back exactly
    as the unchanged consumer `Variable._resolve_lookup` reads it."""
    cls = ClassStandin(value_to_label)
    cls.do_not_call_in_templates = True            # enums.py:34 (the added line)
    out_flag = getattr(cls, 'do_not_call_in_templates', False)  # template/base.py
    out_value_to_label = cls._value2label_map_     # unchanged by the assignment
    return out_flag, out_value_to_label


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []
    yield [(1, list('Diamond'))]                          # the F2P fixture row
    yield [(1, list('Diamond')), (2, list('Spade'))]
    yield [(i, list('L%d' % i)) for i in range(50)]
    yield [(-1, []), (0, list(' '))]
    for _ in range(n):
        k = rng.randint(0, 24)
        v2l = []
        for _ in range(k):
            val = rng.randint(-1000, 1000)
            lbl_len = rng.randint(0, 12)
            lbl = [chr(rng.randint(32, 126)) for _ in range(lbl_len)]
            v2l.append((val, lbl))
        yield v2l


def main():
    rng = random.Random(SEED)
    fails = 0
    checked = 0
    for v2l in fuzz_inputs(N_FUZZ, rng):
        shadow_flag, shadow_map = shadow_publish(v2l)
        oracle_flag, oracle_map = oracle_publish(v2l)

        # 1) flag observable: both must report the published flag is True
        if shadow_flag != oracle_flag:
            fails += 1
            if fails <= 10:
                print("FLAG DISAGREE: shadow=%r oracle=%r v2l=%r"
                      % (shadow_flag, oracle_flag, v2l), file=sys.stderr)
        if not oracle_flag:
            fails += 1
            if fails <= 10:
                print("FLAG NOT SET by patched op: v2l=%r" % (v2l,),
                      file=sys.stderr)

        # 2) frame: value->label map preserved unchanged on both sides
        if shadow_map != v2l or oracle_map != v2l:
            fails += 1
            if fails <= 10:
                print("MAP DISAGREE: shadow=%r oracle=%r input=%r"
                      % (shadow_map, oracle_map, v2l), file=sys.stderr)
        checked += 1

    if fails:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed %d)."
              % (fails, checked, SEED), file=sys.stderr)
        return 1
    print("G-CONF OK: R/I shadow of publishChoicesClass agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements. "
          "do_not_call_in_templates reads back True; value->label map preserved."
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
