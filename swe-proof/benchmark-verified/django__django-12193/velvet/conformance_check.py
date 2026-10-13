#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-12193 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`CheckboxInput.get_context`, exercised end-to-end by actually calling it on a
real widget instance with a caller-owned attribute mapping.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the
              real repo types via the mapping.md §2 bijection:
                  attrs (caller's attribute mapping)  <->  the `attrs` dict
                      passed into get_context (str -> bool entries; the touched
                      key is "checked")
                  checked                             <->  bool(check_test(value))
                  withChecked(attrsOld) = {**attrsOld, "checked": True}
                  effective = withChecked(attrsOld) if checked else attrsOld
              The shadow predicts (a) the onward attribute mapping the control
              hands to the base renderer and (b) that the caller's mapping is
              returned unchanged (directive-5 frame). There are NO A-tagged ops
              (no consumed axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `CheckboxInput`. We
              build one widget, hand it a caller-owned `attrs` dict, and read
              back BOTH the onward mapping it produced (the rendered context's
              widget attrs, with the empty base widget attrs merged in by
              build_attrs) AND the caller's dict AFTER the call (the bug is
              precisely that the pre-patch code mutated this caller dict in
              place, so a checkbox marked checked leaked the flag to every later
              element sharing the dict; the patched code rebuilds a fresh dict,
              leaving the caller's untouched).

They must agree on every input: shadow effective == oracle onward mapping, AND
the caller's dict is unchanged after the call (the directive-5 frame
`attrs = attrsOld`). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample. stdlib + django only. Fuzz seed pinned
(mapping.md §4).
"""
import itertools
import random
import sys

SEED = 12193
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


_bootstrap_django()

from django.forms.widgets import CheckboxInput  # noqa: E402  (after setup)


# --- the input space --------------------------------------------------------
# Caller attribute mappings: dicts over a small key pool with bool values,
# including the touched key "checked" (the F2P test passes {'checked': False}).
ATTR_KEYS = ["checked", "class", "id", "foo"]
BOOL_VALS = [True, False]

# Values whose boolean_check observation drives `checked`. Cover the affirmative
# branch (True / non-empty / nonzero) and the negative branch (False / None / '').
VALUES = [True, False, None, "", "x", 0, 1]


def _all_attr_dicts(max_size):
    """Every attribute dict using <= max_size distinct keys, bool values."""
    dicts = [{}]
    for size in range(1, max_size + 1):
        for keys in itertools.combinations(ATTR_KEYS, size):
            for vals in itertools.product(BOOL_VALS, repeat=size):
                dicts.append(dict(zip(keys, vals)))
    return dicts


# --- the R/I shadow: Solution.lean's modeled rule, transliterated -----------
def boolean_check(v):
    """Mirror of CheckboxInput's default check_test (= forms.widgets
    boolean_check). The observation feeding `checked`."""
    return not (v is False or v is None or v == "")


def shadow(attrs_old, value):
    """(effective_mapping, frame_ok) the model predicts.

    effective = withChecked(attrsOld) if checked else attrsOld, where
    withChecked sets "checked" -> True (overwrite if present, append if absent).
    The frame is always preserved by the model (attrs = attrsOld)."""
    checked = boolean_check(value)
    if checked:
        effective = {**attrs_old, "checked": True}
    else:
        effective = dict(attrs_old)
    return effective, True


# --- the ORACLE: the REAL patched CheckboxInput, end-to-end -----------------
def oracle(attrs_old, value):
    """patch.diff behaviour: (onward_mapping, caller_dict_after_call).

    The onward mapping is what the patched get_context hands to the base
    renderer; we read it from the produced context. The base widget's own attrs
    are empty, so build_attrs({}, effective) == effective — the merge is the
    identity here and the comparison stays faithful to the touched mapping."""
    widget = CheckboxInput()
    caller = dict(attrs_old)  # a fresh caller-owned dict per call
    ctx = widget.get_context("field", value, caller)
    onward = dict(ctx["widget"]["attrs"])
    return onward, caller


def main():
    rng = random.Random(SEED)
    boundary_attrs = _all_attr_dicts(max_size=len(ATTR_KEYS))

    disagreements = []
    frame_violations = []
    count = 0

    def one_case(attrs_old, value):
        nonlocal count
        count += 1
        sh_eff, _ = shadow(attrs_old, value)
        orc_onward, caller_after = oracle(attrs_old, value)
        if sh_eff != orc_onward:
            disagreements.append((dict(attrs_old), value, sh_eff, orc_onward))
        # Directive-5 frame: the caller's mapping must be unchanged by the call.
        # Pre-patch this fails when the control is affirmative (the flag is
        # written into the caller's dict in place).
        if caller_after != attrs_old:
            frame_violations.append((dict(attrs_old), value, caller_after))

    # Boundary sweep: every attribute dict x every value.
    for attrs_old in boundary_attrs:
        for value in VALUES:
            one_case(attrs_old, value)

    # Randomized fuzz to >= N_FUZZ.
    while count < N_FUZZ:
        size = rng.randint(0, len(ATTR_KEYS))
        keys = rng.sample(ATTR_KEYS, size)
        attrs_old = {k: rng.choice(BOOL_VALS) for k in keys}
        value = rng.choice(VALUES)
        one_case(attrs_old, value)
        if len(disagreements) >= 10 and len(frame_violations) >= 10:
            break

    if disagreements or frame_violations:
        if disagreements:
            print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
                  f"{count} cases (seed={SEED}):")
            for a, v, sh, orc in disagreements[:10]:
                print(f"  attrs={a} value={v!r} shadow={sh} oracle={orc}")
        if frame_violations:
            print(f"G-CONF FAIL: {len(frame_violations)} caller-mapping frame "
                  f"violation(s) (caller attrs dict mutated in place):")
            for a, v, after in frame_violations[:10]:
                print(f"  attrs={a} value={v!r} after={after}")
        return 1

    print(f"G-CONF OK: R/I shadow of computeContextAttrs agrees with patch.diff "
          f"behaviour on {count} cases (seed={SEED}), 0 disagreements; the "
          f"caller's attribute mapping stayed unchanged across every call "
          f"(directive-5 frame held).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
