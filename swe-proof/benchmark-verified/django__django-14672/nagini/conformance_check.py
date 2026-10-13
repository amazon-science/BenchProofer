#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14672 (nagini).

SHADOW: the impl region of `identity_name_component` from model.py, copied
verbatim below with the contract calls (Requires/Ensures) stripped. The pure
region copies over as plain code: the `Value` carrier becomes a plain class,
the kind constants stay as-is, and the `@Pure` helpers (`is_hashable`,
`canonical_names`, `canonical_items`) become plain functions. `PSeq[int]` /
`ToSeq` reduce to a plain immutable tuple shim (order-preserving sequence
theory over atoms). There are no @ContractOnly callees in this bundle (the
axioms region is empty).

ORACLE: the REAL repo behaviour the model models per mapping.md section 1 —
the value the intermediate-field-names collection contributes to the identity
of a reverse many-to-many relation (`ManyToManyRel.identity`, module
`django.db.models.fields.reverse_related`; the slot sits directly before the
trailing constraint flag in the returned tuple). The gate applies the diff to
/testbed before this script runs and sets PYTHONPATH; this script never
applies any diff itself. A relation object is constructed with opaque
stand-ins for every component the model omits (they are unchanged, already
hashable, and independent of the modeled slot per mapping.md section 2), and
the modeled slot is read out of the identity tuple.

Type bridge (mapping.md section 2): field names are modelled as opaque `int`
atoms; here they are real field-name strings (compared only for equality and
order, which the shadow never inspects beyond that). The runtime value maps
to the tagged carrier —
  None            -> kind KIND_ABSENT,    items ()
  a list of names -> kind KIND_MUTABLE,   items tuple(names)
  a tuple of names-> kind KIND_IMMUTABLE, items tuple(names)
and hashability of the real slot (hash() succeeds vs raises TypeError) must
match `is_hashable` of the shadow's carrier. The Requires (names is None or a
readable list) holds by construction of the generated inputs; the read-only
obligation (directive 5) is checked by snapshotting the input list.

>= 1e5 Requires-satisfying inputs: structured boundary cases (absent, empty,
the F2P two-name list, duplicates, empty-string names, long collections) plus
100000 fuzz collections of field-name-like strings. Pinned fuzz seed: 214672.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; no hypothesis needed).
"""
import json
import random
import string
import sys

SEED = 214672
N_FUZZ = 100_000


# --- pure region of model.py, contracts stripped -------------------------------
# Carrier kinds. A mutable sequence (KIND_MUTABLE) is the only one that is not
# hashable; an absent value and an immutable sequence are both hashable.
KIND_ABSENT = 0    # None
KIND_MUTABLE = 1   # a Python list
KIND_IMMUTABLE = 2  # a Python tuple


def ToSeq(xs):
    """PSeq shim: the pure sequence theory over atoms is a plain tuple."""
    return tuple(xs)


class Value:
    """A minimal model of a runtime value as it enters the identity: a kind tag
    (faithfully reflecting the value's runtime type) plus its element sequence
    (empty when absent)."""

    def __init__(self, kind, items):
        self.kind = kind
        self.items = items


def is_hashable(v):
    """Whether a value may participate in a hash. A mutable sequence is not
    hashable; an absent value and an immutable sequence are."""
    return v.kind != KIND_MUTABLE


def canonical_names(names):
    """The KIND the name collection contributes to the identity after
    canonicalisation: absent stays absent; any present sequence becomes the
    immutable form."""
    if names is None:
        return KIND_ABSENT
    return KIND_IMMUTABLE


def canonical_items(names):
    """The element sequence the name collection contributes after
    canonicalisation: order-preserving, identical to the input names (empty
    when absent)."""
    if names is None:
        return ToSeq([])
    return ToSeq(names)


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def identity_name_component(names):
    empty = []  # type: list
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names))


# --- bridge: real identity slot <-> the tagged model carrier -------------------

def observe_slot(slot):
    """Map the runtime value found in the identity slot to (kind, items,
    hashable). Returns None for a carrier kind outside the modeled domain
    (reported as a disagreement by the caller)."""
    try:
        hash(slot)
        hashable = True
    except TypeError:
        hashable = False
    if slot is None:
        return (KIND_ABSENT, (), hashable)
    if isinstance(slot, tuple):
        return (KIND_IMMUTABLE, tuple(slot), hashable)
    if isinstance(slot, list):
        return (KIND_MUTABLE, tuple(slot), hashable)
    return None


class _Opaque:
    """Stand-in for the identity components the model omits (unchanged by the
    patch and already hashable)."""
    def __repr__(self):
        return "<opaque>"


def real_identity_slot(ManyToManyRel, names):
    """Build a real reverse m2m relation carrying `names` as its intermediate
    field-name collection and read the modeled slot out of its identity tuple.
    The slot sits directly before the trailing constraint flag."""
    rel = ManyToManyRel(
        field=_Opaque(),
        to=_Opaque(),
        through=_Opaque(),          # required for a through-fields collection
        through_fields=names,
    )
    ident = rel.identity
    return ident[-2]


def check_one(ManyToManyRel, names):
    """Diff the shadow against the real identity slot on one input. Returns an
    error string on disagreement, else None."""
    snapshot = None if names is None else list(names)
    observed = observe_slot(real_identity_slot(ManyToManyRel, names))
    shadow = identity_name_component(names)
    shadow_view = (shadow.kind, tuple(shadow.items), is_hashable(shadow))
    if names is not None and names != snapshot:
        return ("DISAGREEMENT (input mutated)\n  names before=%r after=%r"
                % (snapshot, names))
    if observed is None or observed != shadow_view:
        return ("DISAGREEMENT\n  names=%r\n  shadow (kind, items, hashable)=%r"
                "\n  real   (kind, items, hashable)=%r"
                % (names, shadow_view, observed))
    return None


def boundary_cases():
    return [
        None,
        [],
        ['event', 'invitee'],          # the F2P through-fields collection
        ['invitee', 'event'],          # order matters
        ['parent', 'model'],
        ['a'],
        ['x', 'y', 'z', 'w'],
        ['dup', 'dup'],
        ['', ''],
        [''],
        ['name_with_underscores_and_1234567890'],
        ['n'] * 25,
        [string.ascii_lowercase],
    ]


def main():
    # REAL repo symbol (the relation whose identity the model models):
    import django  # noqa: F401  (presence check; no app setup needed)
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.models.fields.reverse_related import ManyToManyRel

    checked = 0
    n_boundary = 0
    for names in boundary_cases():
        err = check_one(ManyToManyRel, names)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    alphabet = string.ascii_lowercase + '_0123456789'
    for _ in range(N_FUZZ):
        if rng.random() < 0.05:
            names = None
        else:
            n = rng.randint(0, 6)
            names = [
                ''.join(rng.choice(alphabet)
                        for _ in range(rng.randint(0, 12)))
                for _ in range(n)
            ]
        err = check_one(ManyToManyRel, names)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real identity through-fields slot on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
