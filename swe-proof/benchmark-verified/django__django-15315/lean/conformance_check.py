#!/usr/bin/env python3
"""G-CONF for django__django-15315.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_object_hash` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `Field.__hash__`
(django/db/models/fields/__init__.py) over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

The fix makes a field's hash depend ONLY on its construction-time identity token
(`creation_counter`); the owner identity (`app_label`, `model_name`, available
only once the field is attached to a model class) is no longer consulted, so the
hash is immutable across attachment.

We isolate `Field.__hash__` by instantiating a real `Field`, overwriting its
`creation_counter` with the chosen serial, and optionally attaching a fake
`model` object exposing `_meta.app_label` / `_meta.model_name`.

Type bijection (mapping.md):
  o.serial : Int                    <-> self.creation_counter
  o.owner : Option(label, name)     <-> (model._meta.app_label, model._meta.model_name)
                                        if hasattr(self,'model') else None
  implementation_object_hash o      <-> Field.__hash__(self)
  result = int_hash o.serial        <-> hash(self.creation_counter)

`creation_counter` ranges over ALL ints: ordinary fields get non-negative
serials, while auto-created fields draw from `Field.auto_creation_counter`,
which counts DOWN from -1 (so e.g. every model's auto pk has a negative
counter). The Lean model therefore mirrors CPython's int hash concretely
(`int_hash`): reduce the magnitude modulo the Mersenne prime
`M = sys.hash_info.modulus = 2**61 - 1`, re-apply the sign, then map the
reserved output -1 to -2. The shadow below is that transliteration; the fuzzer
draws serials from the full signed domain and probes every boundary
(0, +-1, +-(M-1), +-M, +-(M+1), multi-limb magnitudes).

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + django only.
"""
import random
import sys
import types

# --- configure Django settings before importing the model machinery ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, DATABASES={},
        INSTALLED_APPS=[], USE_I18N=False,
    )
    django.setup()

from django.db.models.fields import Field

M = sys.hash_info.modulus  # 2**61 - 1 on 64-bit CPython


# --- shadow: R/I transliteration of implementation_object_hash ---------------
def int_hash(n):
    """Transliteration of Lean `int_hash`: sign-preserving reduction of the
    magnitude modulo the Mersenne prime M, with the reserved output -1 mapped
    to -2."""
    r = n % M if n >= 0 else -((-n) % M)
    return -2 if r == -1 else r


def shadow(serial, owner):
    """Mirror of the Lean impl: owner is deliberately not consulted."""
    return int_hash(serial)


# --- oracle: drive the REAL patched Field.__hash__ ---------------------------
def make_owner_model(label, name):
    meta = types.SimpleNamespace(app_label=label, model_name=name)
    return types.SimpleNamespace(_meta=meta)


def oracle(serial, owner):
    """Run the REAL patched Field.__hash__ on a field with the chosen serial and
    optional owner attachment, and return its hash."""
    f = Field()
    f.creation_counter = serial
    if owner is not None:
        label, name = owner
        f.model = make_owner_model(label, name)
    else:
        if hasattr(f, "model"):
            del f.model
    return hash(f)


_LABELS = ["app", "auth", "myapp", "x", "really_long_app_label", "a", "blog"]
_NAMES = ["mymodel", "book", "m", "User", "really_long_model_name", "z", "post"]


def rand_owner(rng):
    if rng.random() < 0.5:
        return None
    return (rng.choice(_LABELS), rng.choice(_NAMES))


def main():
    rng = random.Random(15315)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    # Boundary cases first, each with and without an attached owner. Negative
    # serials are REAL inputs: auto-created fields (auto pk) use
    # auto_creation_counter, counting down from -1.
    boundary_serials = [
        0, 1, 7, -1, -2, -3, -100,
        M - 1, M, M + 1, -(M - 1), -M, -(M + 1),
        2 * M + 5, -(2 * M + 5), 10 ** 30 + 7, -(10 ** 30 + 7),
    ]
    cases = []
    for s in boundary_serials:
        cases.append((s, None))
        cases.append((s, ("auth", "user")))
    for serial, owner in cases:
        o = oracle(serial, owner)
        s = shadow(serial, owner)
        if o != s:
            disagreements += 1
            if first is None:
                first = (serial, owner, o, s)
    for i in range(N):
        # Mix realistic serials (small magnitudes, both signs) with full-range
        # and multi-limb magnitudes to stress the modular-reduction law.
        u = i % 4
        if u == 0:
            serial = rng.randint(-10_000_000, 10_000_000)
        elif u == 1:
            serial = rng.randint(-(2 ** 63), 2 ** 63)
        elif u == 2:
            serial = rng.randint(-(2 ** 200), 2 ** 200)
        else:
            # near the Mersenne modulus boundaries
            k = rng.randint(-3, 3)
            serial = k * M + rng.randint(-4, 4)
        owner = rand_owner(rng)

        o = oracle(serial, owner)
        s = shadow(serial, owner)
        if o != s:
            disagreements += 1
            if first is None:
                first = (serial, owner, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
