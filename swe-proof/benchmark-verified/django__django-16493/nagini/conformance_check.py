#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16493 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The @Pure helpers ``default_store_id`` / ``reported_value``
copy over as plain functions. The field stand-in is a three-attribute shim
object (store_id, has_producer, producer_id). There are no @ContractOnly
callees in this bundle and no PSeq usage (no shim needed).

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.db.models.fields.files.FileField.deconstruct`` (its storage-kwarg
include/omit decision). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed resolves the patched source.

Type bridge (mapping.md section 2): object identity <-> integer identity
tags. A single registry maps each tag to one distinct live object; tag 0 is
the canonical default store singleton. ``has_producer`` <-> presence of the
held-callable attribute on the field; the result pair (included, value) <->
presence of the "storage" key in the deconstructed kwargs and the identity of
the object stored under it. Because the model's tag space is unified (equal
tags mean the SAME object, regardless of role), one registry serves both the
store and producer roles, so tag coincidences (producer tag == store tag,
producer tag == 0) map to genuine object-identity coincidences on the field.

Input domain: the model's only precondition is read-only access to the three
attributes, so EVERY (bool, int, int) triple is Requires-satisfying. The
field state for a triple is built by direct attribute assignment on a real
FileField (deconstruct is read-only, so states are independent); this covers
the whole total domain including the constructor-unreachable coincidence
corners. Additionally, reachable states are exercised through the REAL
constructor (concrete stores and deferred callables, including a callable
that evaluates to the default store), with tags derived from the resulting
live objects via the identity registry -- the reverse bridge.

>= 1e5 Requires-satisfying inputs: 18 exhaustive boundary triples + 7
constructor-path cases + 100000 fuzzed triples. Pinned fuzz seed: 16493.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 16493
N_FUZZ = 100000


# --- pure helpers from model.py, contracts stripped ---------------------------

def default_store_id():
    return 0


def reported_value(has_producer, producer_id, store_id):
    if has_producer:
        return producer_id
    return store_id


# --- the field stand-in shim ---------------------------------------------------

class FieldShim(object):
    __slots__ = ("store_id", "has_producer", "producer_id")

    def __init__(self, has_producer, producer_id, store_id):
        self.store_id = store_id
        self.has_producer = has_producer
        self.producer_id = producer_id


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def deconstruct_storage(self):
    # Compute the value to report first (producer if present, else store),
    # then decide inclusion from that same value.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)


# --- identity-tag registry (the bridge) ----------------------------------------

class TagRegistry(object):
    """Bijection between integer identity tags and live objects: equal tags
    <-> the same object. Tag 0 is the default-store singleton."""

    def __init__(self, default_obj, make_obj):
        self._by_tag = {0: default_obj}
        self._by_id = {id(default_obj): 0}
        self._make = make_obj
        self._next = 1

    def obj(self, tag):
        if tag not in self._by_tag:
            o = self._make(tag)
            self._by_tag[tag] = o
            self._by_id[id(o)] = tag
        return self._by_tag[tag]

    def tag(self, o):
        """Reverse bridge: tag of a live object, minting a fresh tag for
        objects not seen before."""
        k = id(o)
        if k not in self._by_id:
            while self._next in self._by_tag:
                self._next += 1
            self._by_tag[self._next] = o     # keep a reference: ids stay valid
            self._by_id[k] = self._next
            self._next += 1
        return self._by_id[k]


# --- differential driver --------------------------------------------------------

def real_decision(field):
    """Run the REAL patched deconstruct on a field and project out the
    storage decision: (included, stored_object_or_None)."""
    name, path, args, kwargs = field.deconstruct()
    if "storage" in kwargs:
        return (True, kwargs["storage"])
    return (False, None)


def check(reg, field, has_producer, producer_id, store_id):
    """Diff shadow vs real on one field state; return an error string on
    disagreement, else None."""
    shadow_inc, shadow_val = deconstruct_storage(
        FieldShim(has_producer, producer_id, store_id))
    real_inc, real_obj = real_decision(field)
    if shadow_inc != real_inc:
        return ("DISAGREEMENT on (has_producer=%r, producer_id=%r, "
                "store_id=%r):\n  shadow (impl region) inclusion = %r\n"
                "  real (patched deconstruct) inclusion = %r"
                % (has_producer, producer_id, store_id, shadow_inc, real_inc))
    if real_inc:
        expect = reg.obj(shadow_val)
        if real_obj is not expect:
            return ("DISAGREEMENT on (has_producer=%r, producer_id=%r, "
                    "store_id=%r):\n  shadow reported value tag = %r "
                    "(object %r)\n  real stored object = %r"
                    % (has_producer, producer_id, store_id, shadow_val,
                       expect, real_obj))
    else:
        # Consistency of the shadow pair: omission implies the reported
        # value is the default tag.
        if shadow_val != default_store_id():
            return ("INTERNAL: shadow omitted but reported non-default tag "
                    "%r on (has_producer=%r, producer_id=%r, store_id=%r)"
                    % (shadow_val, has_producer, producer_id, store_id))
    return None


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(MEDIA_ROOT="/tmp/sbu_conf_media", MEDIA_URL="/m/")
    from django.core.files.storage import FileSystemStorage, default_storage
    from django.db.models import FileField

    reg = TagRegistry(
        default_storage,
        lambda tag: FileSystemStorage(location="/tmp/sbu_conf_%d" % tag))

    def field_for(has_producer, producer_id, store_id):
        """Forward bridge: build a real field whose attribute state realizes
        the triple, by direct assignment (deconstruct is read-only)."""
        f = FileField(upload_to="up")
        f.storage = reg.obj(store_id)
        if has_producer:
            f._storage_callable = reg.obj(producer_id)
        return f

    checked = 0
    disagreements = 0

    # (a) exhaustive boundary triples over three tags (0 = default, two
    # distinct non-defaults), covering every equality pattern among
    # producer/store/default including the coincidence corners.
    boundary = 0
    for has_producer in (False, True):
        for producer_id in (0, 1, 2):
            for store_id in (0, 1, 2):
                f = field_for(has_producer, producer_id, store_id)
                err = check(reg, f, has_producer, producer_id, store_id)
                if err:
                    print(err)
                    return 1
                checked += 1
                boundary += 1

    # (b) constructor-path cases: states produced by the REAL constructor,
    # with tags recovered from the live objects (reverse bridge).
    custom_store = FileSystemStorage(location="/tmp/sbu_conf_custom")

    def returns_default():
        return default_storage

    def returns_custom():
        return custom_store

    def returns_fresh():
        return FileSystemStorage(location="/tmp/sbu_conf_fresh")

    class CallableStore(FileSystemStorage):
        def __call__(self):
            return default_storage

    ctor_cases = [
        FileField(upload_to="up"),                          # nothing supplied
        FileField(upload_to="up", storage=default_storage),  # explicit default
        FileField(upload_to="up", storage=custom_store),     # concrete custom
        FileField(upload_to="up", storage=returns_default),  # deferred -> default
        FileField(upload_to="up", storage=returns_custom),   # deferred -> custom
        FileField(upload_to="up", storage=returns_fresh),    # deferred -> fresh
        FileField(upload_to="up",                            # callable instance
                  storage=CallableStore(location="/tmp/sbu_conf_ci")),
    ]
    for f in ctor_cases:
        has_producer = hasattr(f, "_storage_callable")
        producer_id = reg.tag(f._storage_callable) if has_producer \
            else default_store_id()
        store_id = reg.tag(f.storage)
        err = check(reg, f, has_producer, producer_id, store_id)
        if err:
            print(err)
            return 1
        checked += 1

    # (c) randomized fuzz over the total domain (pinned seed): tags drawn
    # from a small band so identity coincidences occur often.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        has_producer = rng.random() < 0.5
        producer_id = rng.randint(0, 7)
        store_id = rng.randint(0, 7)
        f = field_for(has_producer, producer_id, store_id)
        err = check(reg, f, has_producer, producer_id, store_id)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched deconstruct storage "
          "decision on %d inputs (%d boundary + %d constructor-path + %d "
          "fuzz, seed %d); 0 disagreements."
          % (checked, boundary, len(ctor_cases), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
