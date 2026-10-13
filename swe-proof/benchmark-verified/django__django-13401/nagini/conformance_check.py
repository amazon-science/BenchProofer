#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13401 (nagini).

SHADOW: the impl regions of model.py (`attr_eq`, `attr_lt`, `attr_hash_key`),
copied VERBATIM below with the contract calls stripped, plus the two @Pure
helpers the impl calls (`same_owner`, `lex_lt`) copied over as plain
functions. `PSeq` is shimmed as a tuple subclass (variadic constructor,
`drop`, concatenation); `Attr` is the model's carrier class with the
contract lines removed. No @ContractOnly callees exist in this bundle.

ORACLE: the REAL patched repo methods the model models per mapping.md —
`django.db.models.fields.Field.__eq__`, `Field.__lt__`, `Field.__hash__` at
/testbed with the gate having applied patch.diff. Real `Field` instances are
built directly; their integer creation rank is assigned, and ownership is
bridged with interned stand-in owner objects exposing
`_meta.app_label` / `_meta.model_name`:

  * mapping.md's abstraction: an owning container is identified by its
    (label, name) pair, and the runtime enforces at most one container per
    pair — so the bridge interns ONE stand-in object per pair. Identity-based
    equality on the stand-ins then coincides with pair equality, which is
    exactly the equality the real methods observe on the owner attribute.
  * an ownerless attribute is a `Field` that never had the owner attribute
    set (absence, not None).

Output bridges:
  * equality / order: both sides return plain bools, compared with ==.
  * hash: the model's output is the identity KEY (a code-point sequence:
    rank, ownership flag, then when owned `label ++ [0] ++ name`; the
    separator 0 is below every identifier code point). The bridge decodes
    the shadow key back to its (rank, label-or-None, name-or-None) triple
    and requires `hash(triple) == the real method's hash` — the builtin
    `hash` on that triple is the unchanged callee (mapping.md §3.3), so a
    wrong shadow key decodes to a wrong triple and mismatches.

Input domain (the model's Requires): any int rank; owned flag with an
arbitrary identifier-alphabet (label, name) pair when owned. Boundary set:
the regression scenario shape (one shared rank, one label, several names),
bare attributes, mixed bare/owned at equal rank, and a label x name grid at
two ranks; fuzz draws ranks from a small band (to hit equal ranks often) and
25%-ownerless attributes. >= 1e5 Requires-satisfying inputs:
14884 boundary pairs + 100000 fuzz pairs (each pair exercises the equality,
the order both ways, and both hash keys). Pinned fuzz seed: 13401.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13401
N_FUZZ = 100_000
SEP = 0  # separator below every identifier code point (identifiers never NUL)


# --- PSeq shim: nagini's immutable sequence as a plain tuple ------------------

class PSeq(tuple):
    def __new__(cls, *args):
        return super().__new__(cls, args)

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, None)))

    def __add__(self, other):
        return PSeq(*(tuple(self) + tuple(other)))


# --- model.py carrier class, contract lines stripped --------------------------

class Attr:
    def __init__(self, rank, owned, okey):
        self.rank = rank
        self.owned = owned
        self.okey = okey


# --- @Pure helpers from model.py, decorators + contracts stripped -------------

def lex_lt(x, y):
    if len(x) == 0:
        return len(y) > 0
    if len(y) == 0:
        return False
    if x[0] != y[0]:
        return x[0] < y[0]
    return lex_lt(x.drop(1), y.drop(1))


def same_owner(a, b):
    return a.owned == b.owned and (not a.owned or a.okey == b.okey)


# --- the impl regions of model.py, verbatim -----------------------------------

def attr_eq(self_, other):
    return (
        self_.rank == other.rank and
        same_owner(self_, other)
    )


def attr_lt(self_, other):
    if (
        self_.rank != other.rank or
        not self_.owned and not other.owned
    ):
        return self_.rank < other.rank
    elif self_.owned != other.owned:
        return not self_.owned  # the owner-less attribute precedes
    else:
        return lex_lt(self_.okey, other.okey)


def attr_hash_key(self_):
    if self_.owned:
        return PSeq(self_.rank, 1) + self_.okey
    return PSeq(self_.rank, 0)


# --- bridges -------------------------------------------------------------------

def flat_key(label, name):
    """mapping.md's flattened identity key: label ++ [SEP] ++ name."""
    return PSeq(*([ord(c) for c in label] + [SEP] + [ord(c) for c in name]))


def attr_of(spec):
    """Build the model-side attribute from a (rank, label, name) spec;
    label is None => no owner."""
    rank, label, name = spec
    if label is None:
        return Attr(rank, False, PSeq())
    return Attr(rank, True, flat_key(label, name))


def decode_key(key):
    """Invert the shadow's hash KEY encoding back to the
    (rank, label-or-None, name-or-None) triple it denotes."""
    k = list(key)
    if len(k) == 2 and k[1] == 0:
        return (k[0], None, None)
    if len(k) >= 3 and k[1] == 1:
        rest = k[2:]
        i = rest.index(SEP)
        label = "".join(chr(c) for c in rest[:i])
        name = "".join(chr(c) for c in rest[i + 1:])
        return (k[0], label, name)
    raise ValueError("malformed shadow hash key: %r" % (k,))


class _OwnerMeta:
    __slots__ = ("app_label", "model_name")

    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name


class _Owner:
    """Stand-in owning container: identified by its (label, name) pair and
    interned so equal pairs are the same object (identity equality == pair
    equality, matching the runtime's one-container-per-pair invariant)."""
    __slots__ = ("_meta",)

    def __init__(self, app_label, model_name):
        self._meta = _OwnerMeta(app_label, model_name)


_OWNERS = {}


def owner_for(label, name):
    key = (label, name)
    if key not in _OWNERS:
        _OWNERS[key] = _Owner(label, name)
    return _OWNERS[key]


def field_of(Field, spec):
    """Build the real repo object for a (rank, label, name) spec."""
    rank, label, name = spec
    f = Field()
    f.creation_counter = rank
    if label is not None:
        f.model = owner_for(label, name)
    return f


# --- the differential check ----------------------------------------------------

def check_pair(Field, a_spec, b_spec):
    A, B = attr_of(a_spec), attr_of(b_spec)
    fa, fb = field_of(Field, a_spec), field_of(Field, b_spec)

    got_eq = attr_eq(A, B)
    want_eq = Field.__eq__(fa, fb)
    if got_eq != want_eq:
        return ("DISAGREEMENT (equality)\n  a=%r b=%r\n  shadow=%r\n  real=%r"
                % (a_spec, b_spec, got_eq, want_eq))

    for sa, sb, X, Y, fx, fy in ((a_spec, b_spec, A, B, fa, fb),
                                 (b_spec, a_spec, B, A, fb, fa)):
        got_lt = attr_lt(X, Y)
        want_lt = Field.__lt__(fx, fy)
        if got_lt != want_lt:
            return ("DISAGREEMENT (order)\n  a=%r b=%r\n  shadow=%r\n  real=%r"
                    % (sa, sb, got_lt, want_lt))

    for spec, X, f in ((a_spec, A, fa), (b_spec, B, fb)):
        try:
            triple = decode_key(attr_hash_key(X))
        except ValueError as e:
            return "DISAGREEMENT (hash key)\n  a=%r\n  %s" % (spec, e)
        got_h = hash(triple)
        want_h = Field.__hash__(f)
        if got_h != want_h:
            return ("DISAGREEMENT (hash)\n  a=%r\n  shadow key=%r -> %r\n"
                    "  real=%r" % (spec, tuple(attr_hash_key(X)), got_h,
                                   want_h))
    return None


def boundary_specs():
    APP = "model_fields"
    specs = [
        # one shared rank, one label, several names (the regression shape)
        (0, APP, "abstractmodel"),
        (0, APP, "inheritabstractmodel1"),
        (0, APP, "inheritabstractmodel2"),
        # bare attributes, distinct ranks (backward-compat ordering)
        (7, None, None), (-1, None, None), (3, None, None), (0, None, None),
        (100, None, None),
        # bare vs owned at the same rank
        (5, None, None), (5, APP, "thing"),
    ]
    labels = ["", "a", "app", "z", "app2", "model_fields", "auth"]
    names = ["", "a", "x", "model", "abstractmodel", "inheritabstractmodel1",
             "inheritabstractmodel10", "z"]
    for la in labels:
        for na in names:
            specs.append((0, la, na))
            specs.append((1, la, na))
    return specs


def rand_spec(rng, alphabet):
    rank = rng.randint(-3, 5)
    if rng.random() < 0.25:
        return (rank, None, None)
    n1 = rng.randint(0, 10)
    n2 = rng.randint(0, 10)
    label = "".join(rng.choice(alphabet) for _ in range(n1))
    name = "".join(rng.choice(alphabet) for _ in range(n2))
    return (rank, label, name)


def main():
    sys.setrecursionlimit(10000)
    from django.db.models.fields import Field

    checked = 0
    boundary = boundary_specs()
    for a in boundary:
        for b in boundary:
            err = check_pair(Field, a, b)
            if err:
                print(err)
                return 1
            checked += 1
    n_boundary = checked

    rng = random.Random(SEED)
    alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
    for _ in range(N_FUZZ):
        a = rand_spec(rng, alphabet)
        b = rand_spec(rng, alphabet)
        err = check_pair(Field, a, b)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (attr_eq/attr_lt/attr_hash_key) == real "
          "patched comparison/order/hash on %d input pairs (%d boundary + %d "
          "fuzz, seed %d)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
