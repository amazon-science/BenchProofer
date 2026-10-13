#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11880 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The model IS Python: ``Field``
becomes a plain class whose ``__init__`` keeps its impl statements, and
``deep_duplicate`` keeps its two copy loops byte-for-byte. There are no
@Pure helpers, no PSeq usage, and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md §1 —
``django.forms.fields.Field.__deepcopy__`` — invoked the way client code
invokes it, via ``copy.deepcopy(field)``. The gate applies patch.diff to
/testbed before this script runs and sets PYTHONPATH=/testbed, so the
imported Django is the patched one.

Type bridge (mapping.md §2): the field's per-code message-override mapping
(a dict from override code to override value) is carried in the model by two
index-aligned ``List[int]`` — ``msg_codes[k]`` bound to ``msg_values[k]`` —
with code/value strings as opaque int identity tokens; the validator list is
a ``List[int]`` of validator identity tokens. The bridge lifts int token t
to the string "c%d" (codes) / "m%d" (values) / the int itself (validator
tokens; the real list is copied element-wise regardless of element type),
and generates only distinct codes per field (a mapping binds each code
once), which is exactly the carrier's image of a dict. Lowering back reads
``list(dup.error_messages.items())`` so entry ORDER is compared too (the
real mapping preserves insertion order, matching the model's index order).

Per observation the shadow's postconditions are diffed against the real
duplicate:
  * the duplicate's override mapping has the same entries, in order, as the
    shadow's index-aligned output lists, and is a DISTINCT object from the
    original's (the shadow's freshly built lists ARE distinct; the real side
    must agree, observed via ``is not`` and by mutating the duplicate and
    checking the original is unreached);
  * the duplicate's validator list likewise: same tokens in order, distinct
    object;
  * the original field is left exactly as it was on both sides.

Input domain: the only functional precondition is
``len(msg_codes) == len(msg_values)`` — satisfied by construction (a mapping
has exactly one value per code). Boundary cases (empty mapping, singleton,
several entries, empty/singleton validators, real-looking override-code
names) + fuzz over random sizes and tokens.

>= 1e5 Requires-satisfying inputs: boundary battery + 100000 fuzz fields.
Pinned fuzz seed: 118801 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random for fuzz; no f-strings for old
container Pythons).
"""
import copy
import random
import sys

SEED = 118801
N_FUZZ = 100000


# --- SHADOW: model.py impl region, contracts stripped ------------------------

class Field(object):
    def __init__(self):
        self.msg_codes = []
        self.msg_values = []
        self.validators = []


def deep_duplicate(self):
    # impl region of model.py, verbatim (Invariant(...) calls stripped)
    result = Field()

    a = 0
    while a < len(self.msg_codes):
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1

    b = 0
    while b < len(self.validators):
        result.validators.append(self.validators[b])
        b = b + 1
    return result


# --- oracle plumbing ----------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            USE_I18N=False,
            DATABASES={},
        )
    django.setup()


def _lift_code(t):
    return "c%d" % t


def _lift_value(t):
    return "m%d" % t


def _fail(msg, codes, values, validators, shadow_out, real_msgs, real_vals):
    print("DISAGREEMENT: %s" % msg)
    print("  input msg_codes   = %r" % (codes,))
    print("  input msg_values  = %r" % (values,))
    print("  input validators  = %r" % (validators,))
    print("  shadow msg_codes  = %r" % (shadow_out.msg_codes,))
    print("  shadow msg_values = %r" % (shadow_out.msg_values,))
    print("  shadow validators = %r" % (shadow_out.validators,))
    print("  real error_messages (dup) = %r" % (real_msgs,))
    print("  real validators (dup)     = %r" % (real_vals,))
    sys.exit(1)


def main():
    try:
        _configure_django()
        from django import forms
    except Exception as exc:
        print("ERROR: cannot import/configure Django in this environment: %r"
              % (exc,))
        return 2

    checked = 0

    def observe(codes, values, validators, code_strs=None, value_strs=None):
        """codes/values/validators: the model-level input (int tokens,
        distinct codes). code_strs/value_strs optionally override the lifted
        string carriers (used to exercise real-looking override names)."""
        nonlocal checked
        assert len(codes) == len(values)  # the functional Requires

        # -- shadow run over the model carrier --
        f = Field()
        f.msg_codes = list(codes)
        f.msg_values = list(values)
        f.validators = list(validators)
        out = deep_duplicate(f)

        # -- real run over the lifted carrier --
        if code_strs is None:
            code_strs = [_lift_code(t) for t in codes]
        if value_strs is None:
            value_strs = [_lift_value(t) for t in values]
        field = forms.Field()
        field.error_messages = dict(zip(code_strs, value_strs))
        field.validators = list(validators)
        orig_msgs_snapshot = list(field.error_messages.items())
        orig_vals_snapshot = list(field.validators)

        dup = copy.deepcopy(field)
        real_msgs = list(dup.error_messages.items())
        real_vals = list(dup.validators)

        # bridge the shadow output up to the real carrier: lift each output
        # token through the (bijective on this input) token->string maps
        tok2code = dict(zip(codes, code_strs))
        tok2value = dict(zip(values, value_strs))
        lifted_pairs = [(tok2code.get(ct, ct), tok2value.get(vt, vt))
                        for ct, vt in zip(out.msg_codes, out.msg_values)]

        # (1) same override entries, in order
        if real_msgs != lifted_pairs:
            _fail("duplicate's override mapping differs from shadow output",
                  codes, values, validators, out, real_msgs, real_vals)
        # (2) same validator tokens, in order
        if real_vals != list(out.validators):
            _fail("duplicate's validator list differs from shadow output",
                  codes, values, validators, out, real_msgs, real_vals)
        # (3) distinct container objects — the shadow's outputs are freshly
        # built lists (distinct by construction, asserted for symmetry); the
        # real side must agree.
        if not (out.msg_codes is not f.msg_codes
                and out.msg_values is not f.msg_values
                and out.validators is not f.validators):
            _fail("shadow output aliases its input collection",
                  codes, values, validators, out, real_msgs, real_vals)
        if dup.error_messages is field.error_messages:
            _fail("duplicate SHARES the override mapping object with the "
                  "original (shadow's is distinct)",
                  codes, values, validators, out, real_msgs, real_vals)
        if dup.validators is field.validators:
            _fail("duplicate SHARES the validator list object with the "
                  "original (shadow's is distinct)",
                  codes, values, validators, out, real_msgs, real_vals)
        # (4) mutating the duplicate must not reach the original (the
        # observable consequence of distinctness the model's `is not`
        # clauses carry)
        dup.error_messages["__mut_probe__"] = "z"
        dup.validators.append(object())
        if ("__mut_probe__" in field.error_messages
                or len(field.validators) != len(orig_vals_snapshot)):
            _fail("mutating the duplicate reached the original",
                  codes, values, validators, out, real_msgs, real_vals)
        # (5) the original is left exactly as it was, on both sides
        if (list(field.error_messages.items()) != orig_msgs_snapshot
                or list(field.validators) != orig_vals_snapshot):
            _fail("original field was mutated by the duplication",
                  codes, values, validators, out, real_msgs, real_vals)
        if (f.msg_codes != list(codes) or f.msg_values != list(values)
                or f.validators != list(validators)):
            _fail("shadow mutated its input field",
                  codes, values, validators, out, real_msgs, real_vals)

        checked += 1

    # ---- boundary battery ----
    observe([], [], [])                          # empty mapping, no validators
    observe([], [], [7])                         # empty mapping, one validator
    observe([0], [0], [])                        # singleton mapping
    observe([1], [2], [3])
    observe([1, 2, 3], [4, 4, 4], [5, 6])        # repeated values (keys distinct)
    observe([-5, 0, 5], [0, -1, 1], [0])
    observe(list(range(20)), list(range(100, 120)), list(range(10)))
    # real-looking override-code names (the strings client code actually uses)
    observe([0, 1], [10, 11], [1, 2],
            code_strs=["required", "invalid"],
            value_strs=["value A", "value B"])
    observe([0, 1, 2, 3], [9, 8, 7, 6], [],
            code_strs=["required", "invalid", "max_length", "min_length"],
            value_strs=["r", "i", "x", "n"])

    # ---- fuzz (pinned seed) ----
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        codes = rng.sample(range(-1000, 1000), n)   # distinct codes
        values = [rng.randint(-1000, 1000) for _ in range(n)]
        m = rng.randint(0, 6)
        validators = [rng.randint(-1000, 1000) for _ in range(m)]
        observe(codes, values, validators)

    print("G-CONF OK: shadow of the model impl agrees with the real patched "
          "field-duplication function over %d Requires-satisfying inputs "
          "(entries+order, validator list, container distinctness, "
          "original untouched); seed=%d" % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
