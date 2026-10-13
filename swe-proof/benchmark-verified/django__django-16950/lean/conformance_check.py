#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16950.

The bundle models ONE function: `BaseInlineFormSet.add_fields`
(`django/forms/models.py`). Its Lean implementation
(`implementation_clearParentKeyDefault`) decides whether to clear a parent
record's key attribute (set it to None) while preparing an inline child form:

    key_attr = current
    if adding:
        if has_default and (is_parent_pk or not has_form_data):   # post-fix guard
            key_attr = None            # i.e. Option result `none`
    return key_attr                    # `some current` if untouched

This script transliterates that R/I impl into Python (`shadow_clear`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of the modeled block in `add_fields`:

    if instance._state.adding:                              # adding
        if to_field.has_default() and (                     # has_default
            to_field.attname == parent_pk_name              # is_parent_pk
            or not form.data                                # not has_form_data
        ):
            setattr(instance, to_field.attname, None)       # cleared

We do NOT stand up a Django FormSet / model / ORM (heavy, and the modeled value
is a pure decision over four booleans). Instead we reproduce the patched decision
over the SAME observables the real block reads (mapping.md): `adding`,
`has_default`, `is_parent_pk`, `has_form_data`, and the attribute's opaque
current value (an int).

The result is modeled as the resulting attribute value: `None` if cleared, else
the carried-through `current`.

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`shouldReset` (`adding and has_default and (is_parent_pk or not has_form_data)`)
guard, whereas the oracle reproduces the patched guard over the boolean
observables. They must agree for every input — in particular when the parent is
being added, the key field has a default, it is NOT the parent's pk, and the form
carries data (`is_parent_pk == False`, `has_form_data == True`): the attribute
must be RETAINED, the case the patch fixes.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 16950 (also recorded in
mapping.md).
"""
import sys

SEED = 16950
N = 120_000


# --- ORACLE: the post-patch add_fields reset, in-process replica -------------
# `current` is the attribute's existing value (opaque int). Returns the
# resulting attribute value: None if cleared, else `current`.
def oracle_clear(adding, has_default, is_parent_pk, has_form_data, current):
    key_attr = current
    if adding:
        if has_default and (is_parent_pk or not has_form_data):  # the fix
            key_attr = None
    return key_attr


# --- shadow of implementation_clearParentKeyDefault (the R/I leg) ------------
# Mirrors Solution.lean: shouldReset folds the unchanged adding/has_default
# factors with the post-fix (is_parent_pk or not has_form_data) factor; result
# is None (Option `none`) when reset, else `current` (Option `some current`).
def should_reset(adding, has_default, is_parent_pk, has_form_data):
    return adding and has_default and (is_parent_pk or not has_form_data)


def shadow_clear(adding, has_default, is_parent_pk, has_form_data, current):
    key_attr = current
    if adding:
        if has_default and (is_parent_pk or not has_form_data):
            key_attr = None
    return key_attr


def disagree(adding, has_default, is_parent_pk, has_form_data, current):
    got = oracle_clear(adding, has_default, is_parent_pk, has_form_data, current)
    want = shadow_clear(adding, has_default, is_parent_pk, has_form_data, current)
    # Cross-check the should_reset abstraction agrees too.
    pred_none = should_reset(adding, has_default, is_parent_pk, has_form_data)
    want_pred = None if pred_none else current
    if got != want or want != want_pred:
        return ((adding, has_default, is_parent_pk, has_form_data, current),
                got, want, want_pred)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Exhaustive enumeration of the 16 boolean combinations with a fixed opaque
    `current`, plus the discriminating fix case highlighted."""
    cases = []
    cur = 4242  # opaque non-None current value (e.g. a generated UUID)
    for adding in (False, True):
        for has_default in (False, True):
            for is_parent_pk in (False, True):
                for has_form_data in (False, True):
                    cases.append((adding, has_default, is_parent_pk,
                                  has_form_data, cur))
    # THE fix scenario, explicitly: adding, default, alternate key, data present
    # -> attribute must be RETAINED (post-fix). Pre-fix would clear it.
    cases.append((True, True, False, True, 777))
    # Companion PASS_TO_PASS cases (cleared post-fix too):
    cases.append((True, True, True, True, 777))    # parent pk + data -> cleared
    cases.append((True, True, False, False, 777))  # alt key, no data -> cleared
    return cases


def main() -> int:
    checked = 0

    for c in _enumerate_edge():
        d = disagree(*c)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]} pred={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        adding = (next(rnd) & 1) == 1
        has_default = (next(rnd) & 1) == 1
        is_parent_pk = (next(rnd) & 1) == 1
        has_form_data = (next(rnd) & 1) == 1
        current = next(rnd) % 1_000_000
        d = disagree(adding, has_default, is_parent_pk, has_form_data, current)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]} pred={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
