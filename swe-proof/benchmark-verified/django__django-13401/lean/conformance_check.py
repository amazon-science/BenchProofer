#!/usr/bin/env python3
"""G-CONF for django__django-13401.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of the three impls (`implementation_fieldEq`,
`implementation_fieldLt`, `implementation_fieldHashKey`, transliterated op-for-op
per refinement.md) against the REAL patched `Field.__eq__` / `__lt__` /
`__hash__`, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Type bijection (mapping.md):
  FieldId.creationCounter : Int           <-> field.creation_counter : int
  FieldId.model : Option (String×String)  <-> getattr(field,'model',None):
      none                <-> field has NO `model` attribute (hasattr == False)
      some (app, name)    <-> field.model._meta.(app_label, model_name) == (app,name)
  __eq__/__lt__ result : Bool             <-> bool
  __hash__ key (cc, app?, name?)          <-> the tuple the real __hash__ hashes;
      we compare hash(shadow_key) against the real hash(field) (same tuple => same
      hash, deterministically).

Real Field instances are built and given synthetic `model` stand-ins: a registry
maps each (app_label, model_name) pair to ONE sentinel object carrying a matching
`_meta`, so model-object identity/equality (`getattr(...) == getattr(...)`) tracks
pair equality exactly as a real model class would. stdlib-only.
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, DATABASES={}, INSTALLED_APPS=[], TEMPLATES=[],
    )
    django.setup()

from django.db.models.fields import Field

SEED = 13401
N = 120_000

# --- synthetic model stand-ins ------------------------------------------------
class _Meta:
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name

class _ModelStub:
    def __init__(self, app_label, model_name):
        self._meta = _Meta(app_label, model_name)

_REGISTRY = {}
def model_for(pair):
    """Return the unique sentinel object for a given (app, name) pair (so two
    distinct Field instances share the SAME model object for the same pair)."""
    if pair is None:
        return None
    if pair not in _REGISTRY:
        _REGISTRY[pair] = _ModelStub(*pair)
    return _REGISTRY[pair]

def make_field(cc, pair):
    f = Field()
    f.creation_counter = cc
    if pair is None:
        # ensure NO model attribute (hasattr(f,'model') == False)
        if hasattr(f, 'model'):
            del f.model
    else:
        f.model = model_for(pair)
    return f

# --- shadow (Lean impls, transliterated) -------------------------------------
def shadow_eq(cc_a, m_a, cc_b, m_b):
    return (cc_a == cc_b) and (m_a == m_b)

def key_lt(a, b):  # keyLt: app first, then model name (== Python tuple '<')
    return a < b

def shadow_lt(cc_a, m_a, cc_b, m_b):
    a_none = m_a is None
    b_none = m_b is None
    if cc_a != cc_b or (a_none and b_none):
        return cc_a < cc_b
    elif (not a_none) != (not b_none):   # isSome differs
        return a_none                    # no-model field first
    else:
        return key_lt(m_a, m_b)

def shadow_hash_key(cc, m):
    if m is None:
        return (cc, None, None)
    return (cc, m[0], m[1])

# --- fuzz ---------------------------------------------------------------------
APPS = ["app", "auth", "blog", "zoo"]
NAMES = ["field", "abstractmodel", "inheritmodel1", "inheritmodel2", "m"]

def rand_pair(rng):
    if rng.random() < 0.2:
        return None
    return (rng.choice(APPS), rng.choice(NAMES))

def rand_cc(rng):
    return rng.choice([1, 2, 5, 5, 5, 7])  # bias collisions on counter

def main():
    rng = random.Random(SEED)
    fails = 0
    for i in range(N):
        cc_a, m_a = rand_cc(rng), rand_pair(rng)
        cc_b, m_b = rand_cc(rng), rand_pair(rng)
        fa = make_field(cc_a, m_a)
        fb = make_field(cc_b, m_b)

        # __eq__
        real_eq = (fa == fb)
        if real_eq is NotImplemented:
            print(f"FAIL eq NotImplemented at {i}"); return 1
        if bool(real_eq) != shadow_eq(cc_a, m_a, cc_b, m_b):
            print(f"FAIL eq i={i} cc=({cc_a},{cc_b}) m=({m_a},{m_b}) "
                  f"real={real_eq} shadow={shadow_eq(cc_a,m_a,cc_b,m_b)}")
            fails += 1

        # __lt__
        real_lt = (fa < fb)
        if real_lt is NotImplemented:
            print(f"FAIL lt NotImplemented at {i}"); return 1
        if bool(real_lt) != shadow_lt(cc_a, m_a, cc_b, m_b):
            print(f"FAIL lt i={i} cc=({cc_a},{cc_b}) m=({m_a},{m_b}) "
                  f"real={real_lt} shadow={shadow_lt(cc_a,m_a,cc_b,m_b)}")
            fails += 1

        # __hash__ : real hash(field) must equal hash(shadow key tuple)
        if hash(fa) != hash(shadow_hash_key(cc_a, m_a)):
            print(f"FAIL hash i={i} cc={cc_a} m={m_a} "
                  f"real={hash(fa)} shadow_key={shadow_hash_key(cc_a,m_a)}")
            fails += 1

        if fails > 10:
            break

    if fails:
        print(f"G-CONF FAIL: {fails} disagreement(s)")
        return 1
    print(f"G-CONF OK: {N} inputs, 0 disagreements (seed={SEED})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
