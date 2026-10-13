#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13012 (nagini).

SHADOW: the impl regions of model.py — ``base_group_by_cols`` and
``wrapper_group_by_cols`` — copied VERBATIM below with only the contract
calls (Requires / Ensures / MustTerminate) stripped, plus the
``WrappingNode`` carrier with its contract lines stripped. The @Pure helper
``base_group_cols_seq`` copies over on a small immutable-tuple PSeq shim and
serves as an internal cross-check of the executable shadow. There are no
@ContractOnly callees (mapping.md section 3: the wrapped node's rule is a
deep model, not a consumed axiom), so the deep-model shadow is additionally
checked against the REAL wrapped node's own grouping-column answer.

ORACLE: the REAL patched repo function per mapping.md section 1 —
``django.db.models.expressions.ExpressionWrapper.get_group_by_cols``. The
gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the import resolves to the patched module. Each
probe builds a real wrapped node of the modelled family (a constant node
for ``inner_is_constant=True``, a column-like node otherwise), wraps it in
a real ExpressionWrapper, and calls ``get_group_by_cols(alias=...)``.

TYPE BRIDGE (mapping.md section 2): expression nodes <-> int identities.
For each probe the wrapped real node stands for ``inner_id`` and the real
composite stands for ``node_id`` (distinct objects, matching the class
invariant ``inner_id != node_id``); the oracle's returned node list lowers
to ``List[int]`` by that per-probe bijection (an unexpected node lowers to
an unmappable sentinel, forcing a printed disagreement). Grouping lists on
the modelled family have length 0 or 1. The optional grouping request
``request: Optional[int]`` raises to the repo's ``alias`` keyword as None
or an injectively derived string; on the modelled family the answer is
request-independent (mapping.md section 2), which the differential run
exercises across several requests including non-trivial ones.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): a boundary grid of id pairs
x grouping requests x all pooled real node shapes (both constant-ness arms),
plus 100000 random fuzz tuples (random distinct ids, random constant-ness,
random request, random matching node shape). Pinned fuzz seed: 13012 (the
instance number; recorded in mapping.md section 4). Every generated tuple
satisfies the precondition (the only functional requirement is
``inner_id != node_id``). Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib + the repo under test
only.
"""
import json
import random
import sys

SEED = 13012
N_FUZZ = 100000


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- carrier class of model.py, contract lines stripped -----------------------

class WrappingNode:
    def __init__(self, inner_id, inner_is_constant, node_id):
        self.inner_id = inner_id
        self.inner_is_constant = inner_is_constant
        self.node_id = node_id


# --- pure region of model.py, copied as a plain function ----------------------

def base_group_cols_seq(node_id, is_constant):
    if is_constant:
        return PSeq(0).take(0)
    return PSeq(node_id)


# --- impl regions of model.py, verbatim with contract calls stripped ----------

def base_group_by_cols(node_id, is_constant, request):
    if is_constant:
        empty = []  # type: List[int]
        return empty
    one = [node_id]  # type: List[int]
    return one


def wrapper_group_by_cols(node, request):
    cols = base_group_by_cols(node.inner_id, node.inner_is_constant, request)
    return cols


# --- oracle: the real patched repo function -----------------------------------

def configure_django():
    """Configure Django just enough to import the ORM expression classes and
    resolve one column reference. Building expressions and asking for their
    grouping columns runs only Python; no database connection is opened."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes',
                            'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    import django
    django.setup()


def build_node_pools():
    """Real wrapped-node shapes of the modelled family (mapping.md section 2):
    constant nodes for ``inner_is_constant=True`` and non-aggregate
    column-like nodes for ``inner_is_constant=False``. Alias-dependent /
    non-dichotomy node kinds are outside the modelled family (mapping.md
    section 3.1) and are never generated — the model never wraps them."""
    from django.db.models import IntegerField, Value, F
    from django.db.models.expressions import RawSQL
    from django.db.models.functions import Lower, Upper, Length, Coalesce
    from django.contrib.auth.models import User

    col = F('id').resolve_expression(User.objects.all().query)
    constants = [
        Value(3),
        Value(None),
        Value('f'),
        Value(42, output_field=IntegerField()),
    ]
    column_likes = [
        Lower(Value('f')),
        Upper(Value('abc')),
        Length(Value('hello')),
        Lower(Lower(Value('x'))),
        RawSQL('1', []),
        Coalesce(Value(1), Value(2)),
        col,
    ]
    return constants, column_likes


def raise_request(request):
    """Bridge: the model's optional int grouping request -> the repo's alias
    keyword (None stays None; an int raises to an injectively derived,
    non-trivial alias string)."""
    if request is None:
        return None
    return "a%d" % request


def lower_nodes(nodes, inner, inner_id, wrapper, node_id):
    """Bridge: the oracle's node list -> List[int] via the per-probe identity
    bijection. Any node outside the bijection lowers to an unmappable
    sentinel so a comparison against the shadow's ints must fail loudly."""
    out = []
    for e in nodes:
        if e is inner:
            out.append(inner_id)
        elif e is wrapper:
            out.append(node_id)
        else:
            out.append(("<unmapped node>", repr(e)))
    return out


def main():
    configure_django()
    from django.db.models import IntegerField
    from django.db.models.expressions import ExpressionWrapper

    constants, column_likes = build_node_pools()
    checked = 0

    def check(inner, inner_id, is_constant, node_id, request):
        nonlocal checked
        checked += 1
        # SHADOW: the contract-stripped impl regions.
        node = WrappingNode(inner_id, is_constant, node_id)
        shadow = wrapper_group_by_cols(node, request)
        # internal cross-check: the executable impl agrees with the pure
        # sequence value the spec is stated over.
        if ToSeq(shadow) != base_group_cols_seq(inner_id, is_constant):
            return ("INTERNAL: impl region and pure helper disagree at "
                    "inner_id=%r is_constant=%r" % (inner_id, is_constant))
        # ORACLE: the real patched composite.
        alias = raise_request(request)
        wrapper = ExpressionWrapper(inner, output_field=IntegerField())
        real = wrapper.get_group_by_cols(alias=alias)
        mapped = lower_nodes(real, inner, inner_id, wrapper, node_id)
        if shadow != mapped:
            return ("DISAGREEMENT (composite) at inner=%r inner_id=%r "
                    "is_constant=%r node_id=%r request=%r:\n"
                    "  shadow (impl region)         = %r\n"
                    "  real (patched repo, lowered) = %r\n"
                    "  real (raw node list)         = %r"
                    % (inner, inner_id, is_constant, node_id, request,
                       shadow, mapped, real))
        # Deep-model helper vs the REAL wrapped node's own answer (there is
        # no consumed axiom; the helper is a deep model of this real callee).
        shadow_inner = base_group_by_cols(inner_id, is_constant, request)
        real_inner = inner.get_group_by_cols(alias=alias)
        mapped_inner = lower_nodes(real_inner, inner, inner_id,
                                   wrapper, node_id)
        if shadow_inner != mapped_inner:
            return ("DISAGREEMENT (wrapped node's own rule) at inner=%r "
                    "inner_id=%r is_constant=%r request=%r:\n"
                    "  shadow (impl region)         = %r\n"
                    "  real (repo callee, lowered)  = %r\n"
                    "  real (raw node list)         = %r"
                    % (inner, inner_id, is_constant, request,
                       shadow_inner, mapped_inner, real_inner))
        return None

    # --- boundary grid: id pairs x requests x every pooled node shape --------
    id_pairs = [
        (0, 1), (1, 0), (-1, 0), (0, -1), (1, 2), (2, 1),
        (-2**31, 2**31 - 1), (2**63 - 1, -2**63),
        (13012, 13013), (999999999, -999999999),
    ]
    requests = [None, 0, 1, -1, 7, 13012]
    n_boundary = 0
    for inner_id, node_id in id_pairs:
        for request in requests:
            for inner in constants:
                err = check(inner, inner_id, True, node_id, request)
                if err:
                    print(err)
                    return 1
                n_boundary += 1
            for inner in column_likes:
                err = check(inner, inner_id, False, node_id, request)
                if err:
                    print(err)
                    return 1
                n_boundary += 1

    # --- randomized fuzz over the whole Requires-satisfying domain (pinned) --
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        inner_id = rng.randint(-10**9, 10**9)
        node_id = rng.randint(-10**9, 10**9)
        while node_id == inner_id:  # class invariant: distinct identities
            node_id = rng.randint(-10**9, 10**9)
        is_constant = rng.random() < 0.5
        request = None if rng.random() < 0.4 else rng.randint(-10**6, 10**6)
        inner = rng.choice(constants if is_constant else column_likes)
        err = check(inner, inner_id, is_constant, node_id, request)
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real patched composite (and the deep-"
          "model helper == the real wrapped-node callee) on %d inputs "
          "(%d boundary grid + %d fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
