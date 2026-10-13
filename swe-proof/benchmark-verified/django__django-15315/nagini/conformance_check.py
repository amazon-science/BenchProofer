#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15315 (nagini).

SHADOW: the impl region of model.py's ``located_value``, copied VERBATIM
below with only the contract calls (Requires / Ensures) stripped, together
with the minimal ``Descriptor`` carrier class (its constructor body is the
plain field stores of model.py with the contract calls stripped). The single
@ContractOnly callee ``hash_int`` delegates to the REAL repo-relied callee it
axiomatizes per mapping.md section 3.1: the Python builtin ``hash`` applied
to one ``int`` (the primitive is unchanged by the patch; only the hashed
value changes). There are no other pure helpers (the pure region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.db.models.fields.Field.__hash__``. The gate applies
patch.diff to /testbed and sets PYTHONPATH=/testbed before this script runs,
so ``from django.db import models`` resolves to the patched module. Each
probe evaluates ``hash(field)`` on a real ``Field`` instance whose
``creation_counter`` carries the probe's order value, in three owner states:
unattached (no ``model`` attribute — mapping.md's has_owner=False) and
attached to each of two distinct model classes (has_owner=True with two
distinct owner-identity pairs). A separate attachment-transition pass builds
fresh fields, hashes them unattached, attaches them to a newly created model
class via the normal class-creation path, and re-hashes — the located-value
must be identical before and after attachment and equal to the shadow.

TYPE BRIDGE (mapping.md section 2): ``Descriptor.order`` <-> ``Field.
creation_counter`` is the identity on int; ``has_owner`` <-> presence of the
``model`` attribute; ``owner_label`` / ``owner_name`` are opaque int
identities standing for the owner-derived attributes (one distinct pair per
owning class); the returned hash is the identity on int. All bridges are
identities, so probes are generated directly as ints.

INPUT PLAN (>= 1e5 Requires-satisfying inputs; the precondition demands only
readable fields, so every (order, owner-state) combination qualifies):
boundary orders (0, +/-1, +/-2, powers of two around 2^31/2^61/2^63/2^64,
the hash modulus 2^61-1 and neighbours, huge magnitudes) plus 40000 fuzz
orders over mixed-width ranges, each probed in all 3 owner states
(>= 120000 checks), plus 300 attachment-transition probes (2 fields each).
Pinned fuzz seed: 15315. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15315
N_FUZZ = 40000
N_TRANSITION = 300


# --- @ContractOnly callee: the REAL relied-upon primitive (mapping.md 3.1) ---

def hash_int(value):
    return hash(value)


# --- Descriptor carrier + impl region of model.py, contracts stripped --------

class Descriptor(object):
    def __init__(self, order, has_owner, owner_label, owner_name):
        self.order = order
        self.has_owner = has_owner
        self.owner_label = owner_label
        self.owner_name = owner_name


def located_value(self):
    return hash_int(self.order)


# --- oracle: real patched Field instances -------------------------------------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
    django.setup()


def _make_model(class_name, app_label, field_map):
    """Create a model class through the normal class-creation path, which
    attaches every field via contribute_to_class (setting field.model)."""
    from django.db import models
    meta = type("Meta", (), {"app_label": app_label})
    attrs = {"__module__": "conf_probe_models", "Meta": meta}
    attrs.update(field_map)
    return type(class_name, (models.Model,), attrs)


def boundary_orders():
    vals = [0, 1, -1, 2, -2, 41, -41]
    for k in (8, 16, 31, 32, 60, 61, 62, 63, 64, 65, 100, 128, 256):
        p = 2 ** k
        vals += [p - 1, p, p + 1, -p + 1, -p, -p - 1]
    m = 2 ** 61 - 1  # the int-hash modulus
    vals += [m - 1, m, m + 1, 2 * m, 2 * m + 1, -m, -m - 1, -m + 1]
    vals += [10 ** 18, -(10 ** 18), 10 ** 30, -(10 ** 30)]
    seen = set()
    out = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def main():
    _setup_django()
    from django.db import models

    # Owner state A/B: two distinct owning classes (distinct label/name
    # identities). The opaque-int owner identities for the shadow bridge.
    model_a = _make_model("ConfOwnerA", "conf_app_a",
                          {"fa": models.IntegerField()})
    model_b = _make_model("ConfOwnerB", "conf_app_b",
                          {"fb": models.CharField(max_length=8)})
    attached_a = model_a._meta.get_field("fa")
    attached_b = model_b._meta.get_field("fb")
    unattached = models.IntegerField()
    assert hasattr(attached_a, "model") and hasattr(attached_b, "model")
    assert not hasattr(unattached, "model")

    # (real field, has_owner, owner_label id, owner_name id) probe states
    states = [
        (unattached, False, 0, 0),
        (attached_a, True, 1, 11),
        (attached_b, True, 2, 22),
    ]

    checked = 0
    disagreements = 0

    def check_order(order):
        nonlocal checked, disagreements
        real_vals = []
        for field, has_owner, olabel, oname in states:
            checked += 1
            shadow = located_value(
                Descriptor(order, has_owner, olabel, oname))
            field.creation_counter = order
            real = hash(field)  # dispatches to the patched Field.__hash__
            real_vals.append(real)
            if shadow != real:
                disagreements += 1
                print("DISAGREEMENT at order=%r has_owner=%r "
                      "owner=(%r,%r):\n  shadow=%r\n  real=%r"
                      % (order, has_owner, olabel, oname, shadow, real))
        # cross-state stability: the real located-value must not depend on
        # the owner state at all
        if len(set(real_vals)) != 1:
            disagreements += 1
            print("REAL-SIDE INSTABILITY at order=%r: per-state values %r"
                  % (order, real_vals))

    orders = boundary_orders()
    for order in orders:
        check_order(order)

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        width = rng.choice((8, 16, 32, 61, 64, 80, 128))
        v = rng.getrandbits(width)
        if rng.random() < 0.5:
            v = -v
        check_order(v)

    # attachment-transition probes: hash a FRESH field before attachment,
    # attach it through real class creation, hash again — the value must be
    # unchanged and equal to the shadow on the same order.
    for k in range(N_TRANSITION):
        f1 = models.IntegerField()
        f2 = models.CharField(max_length=4)
        o1, o2 = f1.creation_counter, f2.creation_counter
        pre1, pre2 = hash(f1), hash(f2)
        _make_model("ConfTrans%d" % k, "conf_trans_%d" % (k % 7),
                    {"g1": f1, "g2": f2})
        post1, post2 = hash(f1), hash(f2)
        for tag, order, pre, post, fld in (
                ("g1", o1, pre1, post1, f1), ("g2", o2, pre2, post2, f2)):
            checked += 1
            shadow_pre = located_value(Descriptor(order, False, 0, 0))
            shadow_post = located_value(Descriptor(order, True, 3, 33))
            if not (pre == post == shadow_pre == shadow_post):
                disagreements += 1
                print("TRANSITION DISAGREEMENT (%s, order=%r): "
                      "real pre=%r post=%r, shadow pre=%r post=%r"
                      % (tag, order, pre, post, shadow_pre, shadow_post))

    if disagreements:
        print("FAIL: %d disagreement(s) over %d checks" %
              (disagreements, checked))
        return 1
    print("PASS: shadow impl == real patched Field.__hash__ on %d checks "
          "(%d boundary + %d fuzz orders x 3 owner states, + %d attachment "
          "transitions x 2 fields); pinned seed %d"
          % (checked, len(orders), N_FUZZ, N_TRANSITION, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
