#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14915 (nagini).

SHADOW: the impl region of model.py's ``ChoiceValue.membership_identity``,
copied VERBATIM below with only the contract calls (Requires / Ensures /
MustTerminate) stripped. The class carries the two modeled facets ``value``
and ``instance`` exactly as in model.py. The single @ContractOnly callee
``value_identity`` is delegated to the REAL callee the model maps it to
(mapping.md section 3.1): the built-in ``hash`` applied to the bare stored
value. There are no @Pure helpers in the pure region (mapping.md).

ORACLE: the REAL patched repo method per mapping.md section 1 —
``django.forms.models.ModelChoiceIteratorValue.__hash__``, exercised through
the built-in ``hash(...)`` on a real wrapper instance. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH so the
import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2): the wrapped value is modeled directly as
``int`` (the F2P keys are auto-increment integer pks); generation therefore
happens over ``int`` with no lowering needed. The ``instance`` facet is an
opaque integer standing for the identity of the derived domain object; it is
raised to a real Python object for the oracle via a fixed table of distinct
objects (including ``None``), since only the (non-)dependence of the result
on this facet is observable. The returned membership identity is an ``int``
on both sides — identical carrier.

INPUT PLAN (>= 1e5 Requires-satisfying inputs; the precondition demands only
readable fields, so every (int value, instance choice) pair qualifies):
boundary values (0, +/-1, -2, small auto-increment-style pks, values around
the 2**61-1 hash modulus, word-size boundaries, huge bignums) each crossed
with EVERY instance object in the table, plus 100000 random fuzz values over
mixed magnitude ranges, each crossed with a rotating instance object.
Determinism of both sides is probed by hashing twice on boundary inputs.
Pinned fuzz seed: 14915. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14915
N_FUZZ = 100000


# --- @ContractOnly callee: the REAL stdlib primitive (mapping.md 3.1) ---------

def value_identity(v):
    """The axiomatized membership-identity primitive on a bare stored value,
    delegated to the real callee it models: the built-in ``hash``."""
    return hash(v)


# --- impl region of model.py, verbatim with contract calls stripped ----------

class ChoiceValue:
    def __init__(self, value, instance):
        self.value = value
        self.instance = instance

    def membership_identity(self):
        return value_identity(self.value)


# --- oracle: the real patched repo wrapper class ------------------------------

def real_wrapper_class():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True)
    django.setup()
    from django.forms.models import ModelChoiceIteratorValue
    return ModelChoiceIteratorValue


class _Domain(object):
    """A stand-in domain object for the wrapper's derived-object slot."""

    def __init__(self, tag):
        self.tag = tag


# instance bridge: opaque model ints -> distinct real objects (incl. None)
INSTANCE_OBJECTS = [None, _Domain("a"), _Domain("b"), object(), "sentinel"]


# --- input generation ---------------------------------------------------------

_M = 2 ** 61 - 1  # CPython's hash modulus for ints

BOUNDARY_VALUES = [
    0, 1, 2, 3, -1, -2, -3,
    5, 6, 17,                      # small auto-increment-style keys
    255, 256, 65535, 65536,
    2 ** 31 - 1, 2 ** 31, -(2 ** 31),
    2 ** 63 - 1, 2 ** 63, -(2 ** 63),
    _M - 1, _M, _M + 1, 2 * _M, -_M, -(_M + 1),
    2 ** 64, 2 ** 100, -(2 ** 100),
    10 ** 100, -(10 ** 100),
]


def main():
    MCIV = real_wrapper_class()

    checked = 0
    disagreements = 0

    def check(value, inst_obj, inst_int):
        nonlocal checked, disagreements
        checked += 1
        shadow_obj = ChoiceValue(value, inst_int)
        shadow = shadow_obj.membership_identity()
        real = hash(MCIV(value, inst_obj))
        if shadow != real:
            disagreements += 1
            print("DISAGREEMENT at value=%r instance=%r:\n"
                  "  shadow (impl region)     = %r\n"
                  "  real (patched wrapper)   = %r"
                  % (value, inst_obj, shadow, real))
            return
        # the shadow's facets are untouched by the call (read-only frame)
        if shadow_obj.value != value or shadow_obj.instance != inst_int:
            disagreements += 1
            print("SHADOW FRAME VIOLATION at value=%r" % (value,))

    # boundary values x every instance object; determinism probed by a
    # second pass over the same pairs (both sides must repeat their answer)
    for _pass in range(2):
        for v in BOUNDARY_VALUES:
            for i, obj in enumerate(INSTANCE_OBJECTS):
                check(v, obj, i)

    # instance-independence, differentially: for each boundary value the
    # real wrapper's identity must be the same under every instance object
    # (it already equals the fixed shadow answer above; this is a direct
    # cross-object probe on the oracle side)
    for v in BOUNDARY_VALUES:
        reals = {hash(MCIV(v, obj)) for obj in INSTANCE_OBJECTS}
        if len(reals) != 1:
            disagreements += 1
            print("ORACLE INSTANCE-DEPENDENCE at value=%r: identities %r"
                  % (v, sorted(reals)))

    # randomized fuzz over mixed magnitudes (pinned seed)
    rng = random.Random(SEED)
    n_inst = len(INSTANCE_OBJECTS)
    for k in range(N_FUZZ):
        r = rng.random()
        if r < 0.4:
            v = rng.randint(-100, 10000)          # realistic key range
        elif r < 0.7:
            v = rng.randint(-(2 ** 63), 2 ** 63)  # word-size range
        elif r < 0.9:
            v = rng.randint(-4, 4) + rng.choice(
                [0, _M, -_M, 2 * _M, 2 ** 31, 2 ** 63])  # modulus neighborhoods
        else:
            v = rng.getrandbits(rng.randint(64, 512)) * rng.choice([1, -1])
        i = k % n_inst
        check(v, INSTANCE_OBJECTS[i], i)

    if disagreements:
        print("FAIL: %d disagreement(s) over %d inputs" % (disagreements, checked))
        return 1
    print("PASS: shadow impl == real patched wrapper identity on all %d "
          "inputs (%d boundary x %d instances x 2 passes + %d fuzz); "
          "oracle instance-independent on all boundary values; pinned seed %d"
          % (checked, len(BOUNDARY_VALUES), len(INSTANCE_OBJECTS),
             N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
