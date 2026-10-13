#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12193 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl markers carry none). The @Pure helpers
(attr_selected / val_false / val_absent / val_empty_text / counts_as_selected)
copy over as plain functions. The two @ContractOnly callees, `mapping_with`
and `mapping_copy`, model unchanged Python language primitives (mapping.md
section 3: the dict-display merge and the dict copy), so they bridge to the
REAL primitives `{**base, key: flag}` and `{**base}`.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.forms.widgets.CheckboxInput.get_context` -- imported from /testbed
(the gate applies patch.diff before this script runs; PYTHONPATH=/testbed).
The model's Result() is the attribute mapping handed to the shared rendering
step; with the widget's own attribute mapping empty, the rendering step's
`context['widget']['attrs']` is a contents-identical copy of exactly that
mapping (the shared step reads only contents, never object identity --
mapping.md section 2), so it is the faithful contents observation. The
read-only guarantee on the caller's mapping is observed directly: the
caller's dict contents after the call are part of the diffed observation
(the shadow never writes its input, so any write by the oracle would
disagree).

Type bridge (mapping.md section 2):
  model attribute key k (int)  <->  'checked' if k == 0 else 'k<k>' (str)
  model flag (bool)            <->  the same bool
  model value code v (int)     <->  False / None / '' for the three
                                    not-selected sentinels -1 / -2 / -3;
                                    a deterministic pick from a pool of
                                    selected runtime values otherwise
  model empty mapping {}       <->  both a present empty dict and the
                                    absent-mapping (None) call, which the
                                    repo coalesces to empty
Observations compare in model-carrier space: (received-mapping contents,
caller-mapping contents after the call), both abstracted back to
Dict[int, bool] via the inverse key map.

Input domain: the model's Requires places only an access permission on the
caller's mapping, so every (int value code, Dict[int, bool]) pair is
Requires-satisfying. Boundary cases cover the three sentinels and several
selected codes against the empty mapping, mappings already carrying the
selection key with either flag, and multi-key mappings; fuzz draws value
codes across the sentinel/selected split and random small mappings.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz.
Pinned fuzz seed: 12193.

Exit 0 iff zero disagreements; on disagreement prints the input and both
observations and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12193
N_FUZZ = 100_000


# --- pure helpers from model.py, decorators stripped --------------------------

def attr_selected():
    # The attribute-name token for the selection flag the widget establishes.
    return 0


def val_false():
    # Value code for the boolean-false sentinel (one of the three "empty"
    # values that count as NOT selected).
    return -1


def val_absent():
    # Value code for the absent-value sentinel.
    return -2


def val_empty_text():
    # Value code for the empty-text sentinel.
    return -3


def counts_as_selected(value):
    """The definite selection predicate: a value counts as selected unless it is
    one of the three empty sentinels (boolean false / absent / empty text)."""
    return not (value == val_false()
                or value == val_absent()
                or value == val_empty_text())


# --- @ContractOnly callees bridged to the REAL language primitives -----------

def mapping_with(base, key, flag):
    """The real dict-display merge the axiom models (mapping.md section 3.1)."""
    return {**base, key: flag}


def mapping_copy(base):
    """The real dict copy the axiom models (mapping.md section 3.2)."""
    return {**base}


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def prepare_attrs(value, attrs):
    if counts_as_selected(value):
        # Fresh mapping: every caller attribute, with the selection flag forced
        # on. The caller's mapping is read, never written.
        return mapping_with(attrs, attr_selected(), True)
    # Pass-through: a fresh copy of exactly the caller's attributes.
    return mapping_copy(attrs)


# --- type bridge: model carrier <-> runtime values ----------------------------

def key_to_real(k):
    return "checked" if k == 0 else "k%d" % k


def key_to_model(name):
    if name == "checked":
        return 0
    assert name.startswith("k"), "unexpected attribute name %r" % name
    return int(name[1:])


# Selected runtime values: every entry satisfies the repo's default selection
# predicate (none of them is the boolean false / absent / empty-text value).
SELECTED_POOL = [True, 1, 0, "x", "on", "0", 2.5, "hello", [1]]

SENTINEL_TO_REAL = {-1: False, -2: None, -3: ""}


def value_to_real(code):
    if code in SENTINEL_TO_REAL:
        return SENTINEL_TO_REAL[code]
    return SELECTED_POOL[code % len(SELECTED_POOL)]


def attrs_to_real(attrs):
    return {key_to_real(k): v for k, v in attrs.items()}


def attrs_to_model(real_attrs):
    return {key_to_model(name): v for name, v in real_attrs.items()}


# --- observations -------------------------------------------------------------

def shadow_observe(code, attrs):
    """(received-mapping contents, caller-mapping contents after the call),
    in model-carrier space."""
    work = dict(attrs)
    result = prepare_attrs(code, work)
    return (dict(result), dict(work))


def real_observe(widget_cls, code, attrs, use_none):
    """Same observation from the real repo function. `use_none` exercises the
    absent-mapping call for the empty model mapping (the repo coalesces it to
    empty, mapping.md section 2)."""
    widget = widget_cls()  # widget-level attrs empty: the rendering step's
    # attrs entry is then a contents-identical copy of the mapping handed to it
    real_value = value_to_real(code)
    caller = None if use_none else attrs_to_real(attrs)
    ctx = widget.get_context("field", real_value, caller)
    received = attrs_to_model(ctx["widget"]["attrs"])
    after = {} if caller is None else attrs_to_model(caller)
    return (received, after)


def check_case(widget_cls, code, attrs, use_none=False):
    s = shadow_observe(code, attrs)
    r = real_observe(widget_cls, code, attrs, use_none)
    if s != r:
        return ("DISAGREEMENT\n"
                "  value code=%r (real value %r)\n"
                "  attrs=%r (real %s)\n"
                "  shadow (received, caller-after)=%r\n"
                "  real   (received, caller-after)=%r"
                % (code, value_to_real(code), attrs,
                   "None" if use_none else repr(attrs_to_real(attrs)), s, r))
    return None


# --- input generation ----------------------------------------------------------

def boundary_cases():
    codes = [-3, -2, -1, 0, 1, 2, 5, 100, -4, -100]
    mappings = [
        {},
        {0: False},              # selection key already present, off
        {0: True},               # selection key already present, on
        {1: True},
        {1: True, 2: False},
        {0: False, 3: True},
        {0: True, 1: False, 2: True, 7: False},
        {-5: True, 12: False},
    ]
    for code in codes:
        for m in mappings:
            yield (code, m, False)
        # absent-mapping variant of the empty model mapping
        yield (code, {}, True)


def rand_case(rng):
    if rng.random() < 0.4:
        code = rng.choice([-1, -2, -3])
    else:
        code = rng.randint(-6, 12)
    n = rng.randint(0, 6)
    attrs = {rng.randint(-4, 9): bool(rng.getrandbits(1)) for _ in range(n)}
    use_none = (not attrs) and rng.random() < 0.3
    return (code, attrs, use_none)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=False)
        try:
            django.setup()
        except Exception:
            pass
    # The REAL patched repo function's class (mapping.md section 1).
    from django.forms.widgets import CheckboxInput

    checked = 0
    n_boundary = 0
    for code, attrs, use_none in boundary_cases():
        err = check_case(CheckboxInput, code, attrs, use_none)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        code, attrs, use_none = rand_case(rng)
        err = check_case(CheckboxInput, code, attrs, use_none)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real widget context construction on "
          "%d inputs (%d boundary + %d fuzz, seed %d); caller mapping "
          "contents diffed after every call."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
