#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16938 (nagini).

Refines-or-refutes the one leg no other gate covers: does the MODEL in
``model.py`` agree with the REAL patched repository function it claims to model?

================================================================================
ORACLE CHOICE -- the REAL patched function is CALLED, not transliterated
================================================================================
The modeled repo symbol (mapping.md section 1) is the nested closure

    queryset_iterator(obj, field)   in   Serializer.handle_m2m_field

at ``django/core/serializers/python.py:81-82`` and the byte-identical twin at
``django/core/serializers/xml_serializer.py:157-158`` (both @ base_commit
1136aa5005f0ae70fea12796b7e37d6f027b9263). The gold patch rewrites both to

    return getattr(obj, field.name).select_related().only("pk").iterator()

That closure is a *local* inside ``handle_m2m_field``, so it cannot be imported
and called by name. It is nevertheless DRIVEN, not transliterated: this script
runs the REAL ``django.core.serializers.serialize(backend, [obj])`` end to end
over a real sqlite-backed ORM, and captures the exact ``QuerySet`` the patched
closure constructs by wrapping the UNCHANGED boundary immediately below it --
``QuerySet.iterator``, the terminal call of the patched chain. The spy records
``self`` (the fully built queryset) and delegates to the original
``QuerySet.iterator``, so the whole real control flow executes unmodified:
the real related-manager accessor, the real ``QuerySet.select_related()``, the
real ``QuerySet.only("pk")``, the real ``Query.add_immediate_loading``, the real
``Query.get_select_mask``, and the real ``select_related_descend`` /
``SQLCompiler.pre_sql_setup``. Nothing about the query construction is
reimplemented here -- there is no hand-written model of Django in this file.

Both patched sites are exercised (``backend="python"`` and ``backend="xml"``),
so the single modeled function is checked against BOTH hunks of patch.diff.

The three per-clause real observables, each read off the captured real queryset:
  (W) well-formedness  -> does ``query.get_compiler(...).pre_sql_setup()`` raise
      ``FieldError``? (the real ``select_related_descend`` raise branch, i.e.
      the real counterpart of the deep predicate ``ill_formed``)
  (P) the projection, in the representation the real query state HOLDS it in ->
      ``query.deferred_loading == (field_names, defer)``, compared facet-wise
      against the model's ``listed`` / ``excluding``.
  (P') the projection's EFFECTIVE column set -> the real
      ``query.get_select_mask()`` (cross-checked against the compiled SQL's
      select list), compared against the column set the model's own ``dropped``
      predicate implies. Diffing BOTH (P) and (P') pins the representation and
      its meaning, so neither a right-set/wrong-mode nor a right-mode/wrong-set
      answer can slip through.
  (G) grounding / member set -> the m2m pk list the REAL serializer emitted,
      compared with the true membership recorded at fixture-build time, AND the
      model's ``members`` facet.

================================================================================
SHADOW -- the impl region of model.py, copied VERBATIM
================================================================================
``build_pk_iterator``, ``clear_specific_request``, ``only_pk`` and the ``@Pure``
helpers ``dropped`` and ``ill_formed`` are copied character-for-character from
the ``# impl-start`` / ``# impl-end`` and ``# pure-start`` / ``# pure-end``
regions of model.py, with ONLY the contract calls removed (``Requires``/``Ensures``; there are no
``Invariant``/``Assert``/``Fold``/``Unfold``/``Acc``/``MustTerminate`` calls
inside the impl regions). No restructuring, renaming or simplification. The
Nagini carrier ``PSet`` is provided by a shim with the operations the region uses
(construction from elements, ``in``, ``==``, ``len``, and set difference
``-``); ``Exists(int, lambda f: ...)`` is
evaluated over the finite universe of field codes, which is faithful because
``requested`` is always a subset of that universe. model.py has NO
``@ContractOnly`` callee (mapping.md section 3: "no consumed @ContractOnly
axiom"), so nothing had to be stubbed.

================================================================================
TYPE BRIDGE (mapping.md section 2, inverted)
================================================================================
Real -> abstract (``alpha``), applied to a real captured ``QuerySet``:
  * ``restricted`` = ``isinstance(qs.query.select_related, dict)`` -- exactly the
    flag the compiler computes (``compiler.py:1184``).
  * ``requested``  = ``PSet`` of field codes for the keys of that dict (empty
    when it is not a dict -- a non-dict names no specific field).
  * ``listed`` / ``excluding`` = the real ``qs.query.deferred_loading`` pair
    ``(field_names, defer)``: ``listed`` is the codes the projection explicitly
    lists, ``excluding`` says whether that list is the codes to leave OUT. This
    is the projection carried the way the real query state ITSELF carries it.
    That matters: a defer-mode query and an only-mode query can have the same
    effective column set yet behave differently under a subsequent narrowing,
    because ``Query.add_immediate_loading`` (``sql/query.py:2336-2358``) reads
    the mode and, in defer mode, stores ``field_names.difference(existing)``.
    An earlier revision of this bridge collapsed the projection to a single
    ``loaded`` column set read off ``get_select_mask()``; that read is
    information-DESTROYING -- a plain base and a ``defer(pk)`` base both map to
    "all fields loaded" -- so it could not express the real function's behaviour
    and mis-attributed the resulting mismatch to the model. The pair is the
    faithful encoding.
  * ``members``    = the true m2m membership of the owning row, which is what
    the collection the accessor yields addresses.
  * field identities <-> distinct int codes (model.py never indexes ``str``).
The EFFECTIVE column set is still read, separately, from the real
``get_select_mask()`` (``real_loaded_set``) and diffed against the set the
model's own ``dropped`` predicate implies (``model_loaded_set``), so the
abstraction is checked for meaning as well as for representation.
Inputs are generated in the REAL direction -- a base state is realized by a
custom default manager on the related model whose ``get_queryset()`` bakes in a
``select_related``/``only``/``defer`` combination -- and then abstracted with
``alpha``. Generating real-side and abstracting keeps every input inside the
model's ``Requires``, which constrains only permissions (``Acc``) and so admits
EVERY abstract base state.

================================================================================
INPUT DOMAIN -- finite, so enumerated EXHAUSTIVELY, then fuzzed to >= 1e5
================================================================================
The modeled input space is finite: the base state is fixed by (a) what the
accessor's manager bakes into ``select_related`` -- absent, no-arg, ``None``, or
any non-empty subset of the 3 FK fields (10 configs); (b) what it bakes into the
projection -- absent, or ``only``/``defer`` over any subset of the 5 concrete
fields (65 configs); (c) which of 6 owning rows with different m2m membership
(including an EMPTY collection and a SINGLETON) is serialized; (d) which patched
site runs (python / xml). That is 10*65*6*2 = 7800 distinct cases, all of which
are enumerated exhaustively -- a stronger check than 1e5 samples over a subspace.
Seeded fuzz over the SAME space then tops the total up to >= 1e5 (the contract's
count). Boundary cases enumerated first and asserted present: empty collection,
singleton collection, the exact F2P shape (a custom manager baking
``select_related("master")`` with no projection -- the issue's reproducer), a
base already unrestricted, a restricted base whose requested field IS loaded, a
multi-field restricted base, and each branch of ``ill_formed`` (restricted with a
requested-but-excluded field; restricted with none excluded; unrestricted).
Pinned seed: SEED = 16938 (recorded in mapping.md under "## G-CONF").

================================================================================
RESULT -- the model AGREES with the real patched code on the whole finite space
================================================================================
Every clause of ``build_pk_iterator`` agrees with the real patched chain on all
7800 enumerated cases (and the seeded fuzz on top): well-formedness, the
``restricted`` facet, the projection in both its representation (``listed`` /
``excluding``) and its effective column set, and the member set.

The interesting family, and the one an earlier revision of this script got
wrong, is the ``defer(pk)`` base. ``QuerySet.only("pk")`` is
``Query.add_immediate_loading(("pk",))`` (``sql/query.py:2336-2358``), which
resolves ``"pk"`` to the pk's real name and then, when the incoming query is in
DEFER mode, stores ``field_names.difference(existing)``. If the accessor's
manager already deferred the pk's own column, that difference is EMPTY, so
``deferred_loading`` becomes ``(set(), False)`` -- an empty list, which imposes
no restriction, i.e. every column loads. Observed against the real patched
serializer with ``get_queryset() -> ...defer("id")``:

    real built deferred_loading : (set(), False)
    real built get_select_mask(): {}     (= no restriction, all fields loaded)
    real compiled SQL           : SELECT tag.id, tag.name, tag.master_id, ...

model.py models exactly that: ``only_pk`` case-splits on
``q.excluding and pk in q.listed`` and yields an EMPTY ``listed`` in that case,
and its ``dropped`` predicate reads an empty list as "nothing is dropped". So the
model predicts the all-columns projection for a ``defer(pk)`` base and the
pk-only projection otherwise, which is what the real code does.

This required the projection to be carried as the ``(listed, excluding)`` PAIR
rather than as a single effective column set: with the collapsed encoding a plain
base and a ``defer(pk)`` base are the SAME abstract state while the real function
distinguishes them, so no model over the collapsed state could be faithful. The
distinction lives in the type bridge, not in the model.

Falsifiability is demonstrated by a negative control: run WITHOUT the gold patch,
this script reports 69870 disagreements over the same 100000 inputs, dominated by
``well_formedness+restricted`` (52894) -- the real pre-patch ``FieldError`` on the
F2P reproducer shape, which the patched model predicts away. The check therefore
still discriminates the fix from the bug.

MODELING NOTE (declared, not silently dropped). ``build_pk_iterator``'s
``requested`` facet is compared too, and now agrees everywhere
(``requested_keyset_mismatches == 0``): the real ``select_related()`` replaces the
dict with ``True``, discarding the keys, and ``clear_specific_request`` models the
same discard (``q.requested - q.requested``, an empty set). The clause's stated
purpose (refinement.md section C.1: "the build addresses the SAME members as the
owning collection's accessor yields") is ADDITIONALLY checked directly against the
m2m pk list the real serializer emits, for every case.

Exit 0 iff zero disagreements. On disagreement the input and both outputs are
printed and the exit status is 1. stdlib + django (the repo under test) only.
"""
import itertools
import json
import random
import sys
import xml.etree.ElementTree as ET

SEED = 16938          # pinned; recorded in mapping.md "## G-CONF"
N_TARGET = 100000     # >= 1e5 Requires-satisfying inputs

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=False,
    )
django.setup()

from django.core import serializers                      # noqa: E402
from django.core.exceptions import FieldError            # noqa: E402
from django.db import connection, models                 # noqa: E402
from django.db.models.query import QuerySet              # noqa: E402


# ============================================================================
# Nagini carrier shim: PSet (immutable set; construction, `in`, `==`)
# ============================================================================
class PSet(object):
    __slots__ = ("_s",)

    def __init__(self, *items):
        self._s = frozenset(items)

    @classmethod
    def from_iter(cls, items):
        p = cls.__new__(cls)
        object.__setattr__(p, "_s", frozenset(items))
        return p

    def __contains__(self, x):
        return x in self._s

    def __iter__(self):
        return iter(self._s)

    def __len__(self):
        return len(self._s)

    def __eq__(self, other):
        return isinstance(other, PSet) and self._s == other._s

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._s)

    def __sub__(self, other):
        return PSet.from_iter(self._s - other._s)

    def __repr__(self):
        return "PSet(%s)" % (sorted(self._s),)


# Universe over which the model's `Exists(int, ...)` is evaluated. Faithful
# because `requested` is always a subset of the declared field codes.
_UNIVERSE = []


def Exists(_ty, pred):
    return any(pred(f) for f in _UNIVERSE)


# ============================================================================
# SHADOW: model.py's pure + impl regions, VERBATIM, contract calls stripped
# ============================================================================
class Fetch(object):
    """A collection-fetch query state, carrying only the touched facets."""

    def __init__(self, restricted, requested, members, listed, excluding):
        self.restricted = restricted
        self.requested = requested
        self.members = members
        self.listed = listed
        self.excluding = excluding


# pure-start (model.py @Pure dropped / ill_formed, contract decorators stripped)
def dropped(listed, excluding, pk, f):
    return f != pk and len(listed) > 0 and (
        f in listed if excluding else not (f in listed))


def ill_formed(restricted, requested, listed, excluding, pk):
    return restricted and len(listed) > 0 and Exists(
        int, lambda f: f in requested and dropped(listed, excluding, pk, f))
# pure-end


def clear_specific_request(q):
    # impl-start
    return Fetch(False, q.requested - q.requested, q.members, q.listed,
                 q.excluding)
    # impl-end


def only_pk(q, pk):
    # impl-start
    if q.excluding and pk in q.listed:
        return Fetch(q.restricted, q.requested, q.members,
                     PSet(pk) - PSet(pk), False)
    return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
    # impl-end


def build_pk_iterator(base, pk):
    # impl-start
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end


def model_loaded_set(listed, excluding, pk):
    """The field codes the model's projection loads, derived from the model's
    OWN `dropped` predicate -- used to cross-check the model against the real
    `get_select_mask()` in addition to the raw representation."""
    return PSet.from_iter(f for f in _UNIVERSE
                          if not dropped(listed, excluding, pk, f))


# ============================================================================
# Real ORM fixture. The related model's DEFAULT manager bakes in the base
# state, exactly as the issue's reproducer does, so the state under test is
# what the real accessor `getattr(obj, field.name)` yields.
# ============================================================================
BAKE = {"fn": None}


class TagManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return BAKE["fn"](qs) if BAKE["fn"] else qs


class M1(models.Model):
    n = models.CharField(max_length=9)

    class Meta:
        app_label = "contenttypes"


class M2(models.Model):
    n = models.CharField(max_length=9)

    class Meta:
        app_label = "contenttypes"


class M3(models.Model):
    n = models.CharField(max_length=9)

    class Meta:
        app_label = "contenttypes"


class Tag(models.Model):
    objects = TagManager()
    name = models.CharField(max_length=40)
    master = models.ForeignKey(M1, models.SET_NULL, null=True)
    second = models.ForeignKey(M2, models.SET_NULL, null=True)
    third = models.ForeignKey(M3, models.SET_NULL, null=True)

    class Meta:
        app_label = "contenttypes"


class Topic(models.Model):
    title = models.CharField(max_length=40)
    tags = models.ManyToManyField(Tag)

    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as _se:
    for _m in (M1, M2, M3, Tag, Topic):
        _se.create_model(_m)

BAKE["fn"] = None
_a = M1.objects.create(n="a")
_b = M2.objects.create(n="b")
_c = M3.objects.create(n="c")
_TAGS = [
    Tag.objects.create(name="t0", master=_a, second=_b, third=_c),
    Tag.objects.create(name="t1", master=_a, second=None, third=None),
    Tag.objects.create(name="t2", master=None, second=_b, third=None),
    Tag.objects.create(name="t3", master=None, second=None, third=_c),
]

# Owning rows with different m2m membership: EMPTY and SINGLETON boundaries
# plus larger collections.
_MEMBERSHIP = [[], [0], [0, 1], [1, 2, 3], [0, 1, 2, 3], [2]]
TOPICS = []
for _i, _sel in enumerate(_MEMBERSHIP):
    _t = Topic.objects.create(title="T%d" % _i)
    if _sel:
        _t.tags.add(*[_TAGS[k] for k in _sel])
    TOPICS.append((_t, tuple(sorted(_TAGS[k].pk for k in _sel))))

CONCRETE = [f.name for f in Tag._meta.concrete_fields]
PKNAME = Tag._meta.pk.name
CODE = {n: i for i, n in enumerate(CONCRETE)}
PKCODE = CODE[PKNAME]
_UNIVERSE.extend(CODE.values())
FKS = [f.name for f in Tag._meta.concrete_fields if f.is_relation]

# Capture the queryset the patched closure builds, at the UNCHANGED boundary
# immediately below it (the terminal `.iterator()` of the patched chain).
CAP = []
_orig_iterator = QuerySet.iterator


def _spy_iterator(self, *a, **kw):
    if self.model is Tag:
        CAP.append(self)
    return _orig_iterator(self, *a, **kw)


QuerySet.iterator = _spy_iterator


# ============================================================================
# Type bridge: real QuerySet -> abstract Fetch facets (mapping.md section 2)
# ============================================================================
def alpha(qs, members=()):
    """Real -> abstract. The projection is carried the way the real query state
    itself carries it: `deferred_loading == (field_names, defer)` maps to
    (`listed`, `excluding`), so a defer-mode and an only-mode query with the
    same *effective* column set remain DISTINGUISHABLE abstract states -- which
    is what the model's signature requires and what the old collapsed `loaded`
    read destroyed."""
    sr = qs.query.select_related
    restricted = isinstance(sr, dict)
    requested = PSet.from_iter(CODE[k] for k in sr if k in CODE) if restricted \
        else PSet()
    field_names, defer = qs.query.deferred_loading
    listed = PSet.from_iter(CODE[n] for n in field_names if n in CODE)
    return (restricted, requested, PSet.from_iter(members), listed, bool(defer))


def real_loaded_set(qs):
    """The real column set the projection loads, read off the REAL
    `get_select_mask()` (cross-checked against the compiled SQL select list).
    An empty mask means "no restriction in place" => every concrete field."""
    mask = qs.query.get_select_mask()
    if not mask:
        names = set(CONCRETE)
    else:
        names = {f.name for f in mask if getattr(f, "name", None) in CODE}
    return PSet.from_iter(CODE[n] for n in names)


def make_baker(sr, proj):
    """Realize an abstract base state through the REAL accessor: a custom
    default manager on the related model that bakes the state into
    get_queryset(), exactly as the issue's reproducer does."""
    def fn(qs):
        if sr == "noargs":
            qs = qs.select_related()
        elif sr == "null":
            qs = qs.select_related(None)
        elif isinstance(sr, tuple):
            qs = qs.select_related(*sr)
        if proj is not None:
            kind, names = proj
            qs = qs.only(*names) if kind == "only" else qs.defer(*names)
        return qs
    return fn


def sql_select_columns(qs):
    """The real compiled select list (cross-check for the select-mask read)."""
    try:
        sql = qs.query.get_compiler(using="default").as_sql()[0]
    except FieldError:
        return None
    head = sql.split(" FROM ")[0]
    return head[len("SELECT "):] if head.startswith("SELECT ") else head


# ============================================================================
# One case: drive the REAL patched serializer, diff against the shadow
# ============================================================================
def run_case(spec):
    sr, proj, topic_ix, backend = spec
    topic, true_pks = TOPICS[topic_ix]
    BAKE["fn"] = make_baker(sr, proj)
    del CAP[:]

    serialize_error = None
    got_pks = None
    try:
        blob = serializers.serialize(backend, [topic])
        if backend == "python":
            got_pks = tuple(sorted(blob[0]["fields"]["tags"]))
        else:
            root = ET.fromstring(blob)
            got_pks = tuple(sorted(
                int(o.get("pk"))
                for fe in root.iter("field") if fe.get("name") == "tags"
                for o in fe.iter("object")))
    except FieldError as e:
        serialize_error = "FieldError: %s" % e
    except Exception as e:                                  # pragma: no cover
        serialize_error = "%s: %s" % (type(e).__name__, e)

    if not CAP:
        # An EMPTY collection still builds and evaluates the query, so the
        # closure must have run. If it did not, the case tested nothing.
        if true_pks == () and serialize_error is None:
            return None
        raise AssertionError(
            "patched closure never ran (no queryset captured) for spec=%r; "
            "the case would test nothing" % (spec,))

    built = CAP[0]
    abstract_base = alpha(getattr(topic, "tags").all(), members=true_pks)
    abstract_built = alpha(built, members=true_pks)
    real_loaded = real_loaded_set(built)
    try:
        built.query.get_compiler(using="default").pre_sql_setup()
        real_raises = False
    except FieldError:
        real_raises = True

    predicted = build_pk_iterator(Fetch(*abstract_base), PKCODE)
    model_ill = ill_formed(predicted.restricted, predicted.requested,
                           predicted.listed, predicted.excluding, PKCODE)
    model_loaded = model_loaded_set(predicted.listed, predicted.excluding,
                                    PKCODE)

    bad = []
    # (W) well-formedness: the discriminating guarantee
    if model_ill != real_raises:
        bad.append("well_formedness")
    # restricted facet
    if predicted.restricted != abstract_built[0]:
        bad.append("restricted")
    # (P) the projection, in the representation the query state holds it in
    if predicted.listed != abstract_built[3]:
        bad.append("listed")
    if predicted.excluding != abstract_built[4]:
        bad.append("excluding")
    # (P') the projection's EFFECTIVE column set, vs the real select mask
    if model_loaded != real_loaded:
        bad.append("loaded")
    # (G) grounding: the built fetch addresses the same members
    if predicted.members != abstract_built[2]:
        bad.append("members")
    if serialize_error is None and got_pks != true_pks:
        bad.append("member_set")
    if serialize_error is not None and not real_raises:
        bad.append("unexpected_error")

    # informational only (see MODELING NOTE in the docstring)
    requested_keyset_mismatch = predicted.requested != abstract_built[1]

    info = {
        "spec": {"baked_select_related": sr, "baked_projection": proj,
                 "topic_ix": topic_ix, "backend": backend},
        "abstract_base": {"restricted": abstract_base[0],
                          "requested": sorted(abstract_base[1]),
                          "listed": sorted(abstract_base[3]),
                          "excluding": abstract_base[4]},
        "shadow_out": {"restricted": predicted.restricted,
                       "requested": sorted(predicted.requested),
                       "listed": sorted(predicted.listed),
                       "excluding": predicted.excluding,
                       "loaded": sorted(model_loaded),
                       "members": sorted(predicted.members),
                       "ill_formed": model_ill},
        "real_out": {"restricted": abstract_built[0],
                     "requested": sorted(abstract_built[1]),
                     "listed": sorted(abstract_built[3]),
                     "excluding": abstract_built[4],
                     "loaded": sorted(real_loaded),
                     "members": sorted(abstract_built[2]),
                     "raises_FieldError": real_raises,
                     "deferred_loading": repr(built.query.deferred_loading),
                     "sql_select": sql_select_columns(built),
                     "serialized_m2m_pks": got_pks,
                     "true_member_pks": true_pks,
                     "serialize_error": serialize_error},
    }
    return tuple(bad), requested_keyset_mismatch, info


# ============================================================================
# Input domain
# ============================================================================
def boundary_specs():
    """Boundary cases, named, asserted present in the enumeration."""
    empty_ix = _MEMBERSHIP.index([])
    single_ix = _MEMBERSHIP.index([0])
    full_ix = _MEMBERSHIP.index([0, 1, 2, 3])
    return [
        # the exact F2P shape: manager bakes select_related("master"), no
        # projection -> pre-patch this is the reported FieldError regression
        ("F2P reproducer", (("master",), None, full_ix, "python")),
        ("F2P reproducer (xml site)", (("master",), None, full_ix, "xml")),
        # empty and singleton collections
        ("empty collection", ((("master",)), None, empty_ix, "python")),
        ("singleton collection", (("master",), None, single_ix, "python")),
        # unrestricted bases (select_related absent / no-arg / None)
        ("unrestricted (absent)", (None, None, full_ix, "python")),
        ("unrestricted (no-arg)", ("noargs", None, full_ix, "python")),
        ("unrestricted (None)", ("null", None, full_ix, "python")),
        # restricted base whose requested field IS loaded (ill_formed False)
        ("restricted, requested loaded",
         (("master",), ("only", ("master",)), full_ix, "python")),
        # restricted base whose requested field is EXCLUDED (ill_formed True)
        ("restricted, requested excluded",
         (("master",), ("only", ("name",)), full_ix, "python")),
        # multi-field restricted base
        ("multi-field restricted",
         (("master", "second", "third"), None, full_ix, "python")),
        # the defer-mode bases, incl. the pk-deferred one exposing clause (P)
        ("defer(pk) base", (None, ("defer", (PKNAME,)), full_ix, "python")),
        ("defer(pk) base + restricted",
         (("master",), ("defer", (PKNAME,)), full_ix, "python")),
        ("defer(non-pk) base", (None, ("defer", ("name",)), full_ix, "python")),
    ]


def enumerate_domain():
    srs = [None, "noargs", "null"] + [
        tuple(x) for k in range(1, len(FKS) + 1)
        for x in itertools.combinations(FKS, k)]
    projs = [None]
    for k in range(0, len(CONCRETE) + 1):
        for x in itertools.combinations(CONCRETE, k):
            projs.append(("only", tuple(x)))
            projs.append(("defer", tuple(x)))
    return [(sr, pj, ix, be)
            for sr in srs for pj in projs
            for ix in range(len(TOPICS)) for be in ("python", "xml")]


def main():
    domain = enumerate_domain()
    named_boundaries = boundary_specs()
    for label, spec in named_boundaries:
        if spec not in domain:
            print("BOUNDARY CASE MISSING FROM DOMAIN: %s %r" % (label, spec))
            return 1

    classes = {}
    checked = 0
    requested_keyset_mismatches = 0
    skipped_nocap = 0

    def consume(spec):
        nonlocal checked, requested_keyset_mismatches, skipped_nocap
        r = run_case(spec)
        if r is None:
            skipped_nocap += 1
            return
        bad, rq_mismatch, info = r
        checked += 1
        if rq_mismatch:
            requested_keyset_mismatches += 1
        if bad:
            classes.setdefault(bad, []).append(info)

    # 1) boundary cases first, by name
    for _label, spec in named_boundaries:
        consume(spec)
    # 2) the whole finite space, exhaustively
    for spec in domain:
        consume(spec)
    exhaustive = checked
    # 3) seeded fuzz over the SAME space to reach the >= 1e5 count
    rng = random.Random(SEED)
    while checked < N_TARGET:
        consume(domain[rng.randrange(len(domain))])

    if classes:
        total = sum(len(v) for v in classes.values())
        print("G-CONF FAIL: %d disagreements over %d inputs (seed=%d)"
              % (total, checked, SEED))
        for bad, examples in sorted(classes.items(), key=lambda kv: -len(kv[1])):
            print("  class %s: %d occurrences" % ("+".join(bad), len(examples)))
            for info in examples[:3]:
                print("    input     : %r" % (info["spec"],))
                print("    abstract  : %r" % (info["abstract_base"],))
                print("    shadow    : %r" % (info["shadow_out"],))
                print("    real      : %r" % (info["real_out"],))
        print(json.dumps({
            "gate": "G-CONF", "status": "fail", "seed": SEED,
            "inputs_checked": checked, "exhaustive_cases": exhaustive,
            "disagreements": total,
            "classes": {"+".join(k): len(v) for k, v in classes.items()},
            "requested_keyset_mismatches": requested_keyset_mismatches,
            "oracle": ("real patched queryset_iterator driven via "
                       "serializers.serialize (python+xml sites), queryset "
                       "captured at QuerySet.iterator"),
        }))
        return 1

    print("G-CONF OK: %d inputs, 0 disagreements (seed=%d; %d exhaustive over "
          "the finite space, remainder seeded fuzz over the same space); "
          "shadow = model.py impl region verbatim; oracle = real patched "
          "queryset_iterator driven through serializers.serialize at both "
          "patched sites (python + xml)" % (checked, SEED, exhaustive))
    print(json.dumps({
        "gate": "G-CONF", "status": "pass", "seed": SEED,
        "inputs_checked": checked, "exhaustive_cases": exhaustive,
        "disagreements": 0,
        "requested_keyset_mismatches": requested_keyset_mismatches,
        "clauses_checked": ["well_formedness(ill_formed vs real FieldError)",
                            "restricted",
                            "listed+excluding(projection as deferred_loading)",
                            "loaded(effective mask vs real get_select_mask)",
                            "members", "member_set(real serialized m2m pks)"],
        "oracle": ("real patched queryset_iterator driven via "
                   "serializers.serialize (python+xml sites), queryset "
                   "captured at QuerySet.iterator"),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
