#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14238 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped.  The @Pure helper ``is_subtype`` copies
over as a plain function; the ``Cls`` carrier copies over with its constructor
contract stripped (the model's PSet[int] field is a plain frozenset of ints —
membership is the only operation used).  There are no @ContractOnly callees
in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md — the
metaclass membership test ``AutoFieldMeta.__subclasscheck__`` in
``django/db/models/fields/__init__.py``.  The gate applies patch.diff to
/testbed before this script runs, so the method under test is the patched
one.  The oracle is invoked unbound as ``type(owner).__subclasscheck__(owner,
candidate)`` — exactly the modeled callee, for every generated (owner,
candidate) pair whose owner carries the metaclass.

Type bridge (mapping.md section 2): a Python class ``C`` lifts to a carrier
with ``cid = id(C)`` and ``anc = {id(A) for A in C.__mro__}``; the
constructor precondition (``cid in anc``) holds because a class is always in
its own MRO, so every lifted class is a Requires-satisfying input.  The
registered-base parameters ``base_one``/``base_two`` are the two entries of
the owner's registered family (its ``_subclasses`` tuple), read off the real
owner at check time.

Input domain: 4-tuples of classes.  Generation builds a large pool of
dynamically created classes with random inheritance drawn from the real
field-class family (member bases, their user subclasses, grandchildren, the
attached owner type and its subclasses) plus unrelated classes and builtins,
then checks every boundary pair and >= 1e5 fuzz pairs.  Class creations that
raise (metaclass conflict / inconsistent MRO) are skipped — they are not
inputs of the real function either.

Pinned fuzz seed: 142380.  Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1.  stdlib only.
"""
import json
import random
import sys
import types

SEED = 142380
N_FUZZ = 100000


# --- model.py carrier, contract calls stripped --------------------------------

class Cls(object):
    """A class abstracted by its identity `cid` and the set `anc` of
    identities of all classes it derives from (its ancestry)."""

    def __init__(self, cid, anc):
        self.cid = cid
        self.anc = anc


# --- pure helper from model.py, contracts stripped -----------------------------

def is_subtype(sub, base):
    """The ordinary structural-subtype query: `sub` is a subtype of `base` iff
    `base`'s identity lies in `sub`'s ancestry."""
    return base.cid in sub.anc


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def subclass_check(owner, base_one, base_two, candidate):
    if is_subtype(candidate, base_one):
        return True
    if is_subtype(candidate, base_two):
        return True
    return is_subtype(candidate, owner)


# --- bridge: real Python class -> model carrier --------------------------------

_LIFT_CACHE = {}


def lift(cls):
    """Lift a class per mapping.md section 2: cid = id(class), anc = the set
    of identities of the class's MRO.  Reflexivity (cid in anc) holds by
    construction, so the carrier satisfies the constructor precondition."""
    c = _LIFT_CACHE.get(cls)
    if c is None:
        c = Cls(id(cls), frozenset(id(a) for a in cls.__mro__))
        _LIFT_CACHE[cls] = c
    return c


# --- differential driver --------------------------------------------------------

def check(owner, candidate):
    """Run shadow and oracle on one (owner, candidate) pair; return an error
    string on disagreement, else None.  `owner` must carry the metaclass under
    test (so the oracle call is the real modeled method)."""
    b1, b2 = owner._subclasses          # the owner's registered base family
    real = bool(type(owner).__subclasscheck__(owner, candidate))
    shadow = bool(subclass_check(lift(owner), lift(b1), lift(b2),
                                 lift(candidate)))
    if shadow != real:
        return ("DISAGREEMENT on owner=%s candidate=%s "
                "(candidate MRO %r):\n"
                "  shadow (impl region) = %r\n"
                "  real (patched metaclass membership test) = %r"
                % (owner.__name__, candidate.__name__,
                   [a.__name__ for a in candidate.__mro__], shadow, real))
    return None


def make_class(rng, name, base_pool):
    """Create a class from 1-3 random bases; None if the combination is not
    constructible (metaclass conflict / inconsistent MRO) — such combinations
    are not inputs of the real function either."""
    k = rng.randint(1, 3)
    bases = []
    for b in rng.sample(base_pool, min(k, len(base_pool))):
        if b not in bases:
            bases.append(b)
    try:
        return types.new_class(name, tuple(bases))
    except TypeError:
        return None


def main():
    import django  # noqa: F401
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.models.fields import (
        AutoField, BigAutoField, SmallAutoField,
        Field, IntegerField, BigIntegerField, SmallIntegerField,
        CharField,
    )

    meta = type(AutoField)

    # --- curated seed classes: user subclasses of the registered bases (the
    #     discriminating scenario), grandchildren, owner subclasses, siblings
    #     of the family, and unrelated classes ---------------------------------
    class UserBig(BigAutoField):
        pass

    class UserSmall(SmallAutoField):
        pass

    class UserBigGrandchild(UserBig):
        pass

    class UserBigGreatGrandchild(UserBigGrandchild):
        pass

    class OwnerChild(AutoField):
        pass

    class OwnerGrandchild(OwnerChild):
        pass

    class Unrelated(object):
        pass

    class UnrelatedChild(Unrelated):
        pass

    class PlainIntField(IntegerField):
        pass

    curated = [
        AutoField, BigAutoField, SmallAutoField,
        Field, IntegerField, BigIntegerField, SmallIntegerField, CharField,
        UserBig, UserSmall, UserBigGrandchild, UserBigGreatGrandchild,
        OwnerChild, OwnerGrandchild,
        Unrelated, UnrelatedChild, PlainIntField,
        object, int, type, dict,
    ]

    checked = 0

    # --- boundary grid: every curated candidate against every curated owner
    #     that carries the metaclass under test --------------------------------
    curated_owners = [c for c in curated if isinstance(c, meta)]
    assert AutoField in curated_owners
    for owner in curated_owners:
        for candidate in curated:
            err = check(owner, candidate)
            if err:
                print(err)
                return 1
            checked += 1
    n_boundary = checked

    # --- grow a random class pool by repeated inheritance over the curated
    #     seeds (pinned seed), keeping owner-metaclass classes identified -----
    rng = random.Random(SEED)
    pool = list(curated)
    for i in range(4000):
        cls = make_class(rng, "Gen%d" % i, pool)
        if cls is not None:
            pool.append(cls)
    owners = [c for c in pool if isinstance(c, meta)]

    # --- fuzz: >= 1e5 random (owner, candidate) pairs ------------------------
    for _ in range(N_FUZZ):
        owner = rng.choice(owners)
        candidate = rng.choice(pool)
        err = check(owner, candidate)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched membership test on %d "
          "inputs (%d boundary pairs + %d fuzz over a %d-class pool, %d "
          "owner-metaclass classes, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, len(pool), len(owners), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
