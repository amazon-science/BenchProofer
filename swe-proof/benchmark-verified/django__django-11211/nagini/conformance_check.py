#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11211 (nagini).

SHADOW: the impl region of model.py's ``prepare_key``, copied VERBATIM below
with only the contract calls (Requires / Ensures) stripped, together with the
``Value`` carrier class (its ``__init__`` body, contracts stripped, extended
with a ``raw`` slot so the real callees can act on the underlying repo value).
Both callees of the impl region are @ContractOnly axioms, so — per the G-CONF
shadow rules — each delegates to the REAL repo function it is bound to in
mapping.md section 1:

  * ``base_prepare``  -> the real ``Field.get_prep_value`` (the unchanged base
    coercion step, invoked unbound on the field instance exactly as a
    ``super()`` dispatch resolves it);
  * ``canonicalize``  -> the real ``UUIDField.to_python`` (the unchanged
    canonicalizing parser).

There are no @Pure helpers (the pure region is empty), so no PSeq shim is
needed.

ORACLE: the real patched repo method the model models per mapping.md
section 1 — ``UUIDField.get_prep_value``. The gate applies patch.diff to
/testbed and sets PYTHONPATH=/testbed before this script runs, so
``django.db.models`` resolves to the patched module and the method exists on
the field.

TYPE BRIDGE (mapping.md section 2): the repo value is one of ``None``, a
``uuid.UUID``, a textual storage form (32-char hex or hyphenated ``str``), or
an ``int``; the model carrier is a ``Value`` with facets ``is_none: bool``,
``canon: int`` (the 128-bit canonical identity the value denotes),
``key`` (the numeric part of the join key the current storage form yields: a
``uuid.UUID`` keys by its ``.int``, a raw ``str``/``int`` keys as-stored) and
``is_canon_form: bool`` (the FORM half of the join key —
``isinstance(raw, uuid.UUID)`` — which the join's ``==`` compares before any
numeric part, so a same-numbered key in another form matches nothing).
Lowering a repo value computes all four facets; the shadow's resulting
``Value`` is compared against the oracle's return lowered the same way, plus a
direct equality / type check on the underlying repo values. Malformed
strings/ints that denote no identity have no ``Value`` representation
(mapping.md sections 2 and 3.2) and are outside the Requires-satisfying input
domain.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary identities (the
all-zero and all-one 128-bit values, small/large ints, version-1 and
version-4 identities) each in every accepted storage form (uuid.UUID, 32-char
hex, hyphenated, uppercase, braced, URN, int), plus ``None``, plus 20000
random 128-bit fuzz identities x 5 storage forms = >= 100000 checks total.
Pinned fuzz seed: 11211 (recorded in mapping.md). Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits 1.
stdlib + Django (the repo under test) only.
"""
import json
import random
import sys
import uuid

SEED = 11211
N_FUZZ = 20000

_EMPTY_KEY = 0  # the key facet a bare None carries (any fixed int works: the
                # is_none flag discriminates it; both sides lower identically)


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


# --- Value carrier (model.py class, contracts stripped, + raw slot) ----------

class Value(object):
    __slots__ = ("is_none", "canon", "key", "is_canon_form", "raw")

    def __init__(self, is_none, canon, key, is_canon_form, raw=None):
        self.is_none = is_none
        self.canon = canon
        self.key = key
        self.is_canon_form = is_canon_form
        self.raw = raw


# --- bridge: repo value <-> Value facets --------------------------------------

def join_key(raw):
    """The NUMERIC part of the key this value yields in the in-Python join
    dict: a uuid.UUID keys by its 128-bit .int identity; any other value keys
    as-stored."""
    if isinstance(raw, uuid.UUID):
        return raw.int
    return raw


def is_canon_form(raw):
    """The FORM half of the join key: True iff the value is held in the
    canonical object form. Python's ``==`` on keys compares form first, so a
    non-uuid.UUID never matches a uuid.UUID however its number reads."""
    return isinstance(raw, uuid.UUID)


def canonical_int(raw):
    """The 128-bit canonical identity a (well-formed) storage form denotes."""
    if isinstance(raw, uuid.UUID):
        return raw.int
    if isinstance(raw, int):
        return uuid.UUID(int=raw).int
    return uuid.UUID(hex=raw).int


def lower(raw):
    """Lower a repo value to its Value facets (mapping.md section 2)."""
    if raw is None:
        return Value(True, 0, _EMPTY_KEY, False, raw)
    return Value(False, canonical_int(raw), join_key(raw), is_canon_form(raw),
                 raw)


# --- @ContractOnly callees: delegated to the REAL repo functions -------------
# (bound in main() once the Django field instances exist)

_field = None        # the real UUIDField instance
_base_field_cls = None  # the real base Field class (unbound dispatch target)


def base_prepare(value):
    """Axiomatized base coercion step -> real ``Field.get_prep_value``,
    invoked unbound on the field instance, exactly the callee a ``super()``
    dispatch inside the field's own method resolves to."""
    out = _base_field_cls.get_prep_value(_field, value.raw)
    return lower(out)


def canonicalize(value):
    """Axiomatized canonicalizing parser -> real ``UUIDField.to_python``."""
    out = _field.to_python(value.raw)
    return lower(out)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def prepare_key(value):
    coerced = base_prepare(value)  # type: Value
    return canonicalize(coerced)


# --- differential driver ------------------------------------------------------

def describe(raw):
    return "%r (%s)" % (raw, type(raw).__name__)


def check(oracle, raw):
    """Run shadow and oracle on one repo value; return an error string on
    disagreement, else None."""
    v = lower(raw)
    shadow = prepare_key(v)
    real = oracle(raw)
    real_v = lower(real)
    # raw-level agreement (value and type)
    if not (shadow.raw == real and type(shadow.raw) is type(real)):
        return ("DISAGREEMENT on input %s:\n"
                "  shadow (impl region over real callees) = %s\n"
                "  real (patched repo method)             = %s"
                % (describe(raw), describe(shadow.raw), describe(real)))
    # facet-level agreement through the bridge (all four facets)
    if ((shadow.is_none, shadow.canon, shadow.key, shadow.is_canon_form)
            != (real_v.is_none, real_v.canon, real_v.key, real_v.is_canon_form)):
        return ("FACET DISAGREEMENT on input %s:\n"
                "  shadow facets = %r\n"
                "  real facets   = %r"
                % (describe(raw),
                   (shadow.is_none, shadow.canon, shadow.key,
                    shadow.is_canon_form),
                   (real_v.is_none, real_v.canon, real_v.key,
                    real_v.is_canon_form)))
    # postcondition spot-checks (both sides, already known equal): the
    # prepared key of a non-empty value is its canonical identity AND is held
    # in the canonical object form; emptiness and canonical identity are
    # preserved; an empty value keeps its key and its form
    if not v.is_none:
        if shadow.key != v.canon:
            return ("POSTCONDITION on input %s: prepared key %r != canonical %r"
                    % (describe(raw), shadow.key, v.canon))
        if not shadow.is_canon_form:
            return ("POSTCONDITION on input %s: prepared key %s is not held in "
                    "the canonical object form, so it matches no target key"
                    % (describe(raw), describe(shadow.raw)))
        if shadow.is_none or shadow.canon != v.canon:
            return ("POSTCONDITION on input %s: facets not preserved: %r"
                    % (describe(raw), (shadow.is_none, shadow.canon)))
        # the join predicate itself (model.py's matches_target_key): the
        # prepared key must compare EQUAL to the key a target record with this
        # canonical identity contributes, which is that identity in canonical
        # object form. Checked on the real objects, not just the facets.
        target_key = uuid.UUID(int=v.canon)
        if not (shadow.raw == target_key and
                {(target_key, "T"): 1}.get((shadow.raw, "T")) == 1):
            return ("JOIN MISMATCH on input %s: prepared %s does not resolve "
                    "against target key %r"
                    % (describe(raw), describe(shadow.raw), target_key))
    else:
        if not shadow.is_none or shadow.key != v.key:
            return ("POSTCONDITION on None: prepared %s" % describe(shadow.raw))
        if shadow.is_canon_form != v.is_canon_form:
            return ("POSTCONDITION on None: form facet changed %r -> %r"
                    % (v.is_canon_form, shadow.is_canon_form))
    return None


def storage_forms(u):
    """Every accepted storage form of one identity ``u`` (uuid.UUID)."""
    return [
        u,                       # already-canonical object form
        u.hex,                   # 32-char lowercase hex (the stored form)
        str(u),                  # hyphenated 8-4-4-4-12
        u.hex.upper(),           # uppercase hex (parser accepts it)
        "{%s}" % u,              # braced form
        "urn:uuid:%s" % u,       # URN form
        u.int,                   # integer form
    ]


def boundary_identities():
    return [
        uuid.UUID(int=0),
        uuid.UUID(int=1),
        uuid.UUID(int=(1 << 128) - 1),
        uuid.UUID(int=(1 << 127)),
        uuid.UUID(int=0x00000000000000000000000000000010),
        uuid.UUID("12345678-1234-5678-1234-567812345678"),
        uuid.uuid1(),
        uuid.uuid4(),
        uuid.uuid5(uuid.NAMESPACE_DNS, "example.org"),
        uuid.uuid3(uuid.NAMESPACE_URL, "http://example.org/x"),
    ]


def main():
    global _field, _base_field_cls
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not configurable: %r" % (exc,))
        return 1

    from django.db import models

    _field = models.UUIDField()
    _base_field_cls = models.Field
    if "get_prep_value" not in vars(models.UUIDField):
        print("G-CONF ERROR: oracle method absent on UUIDField — patched repo "
              "not on the path")
        return 1
    oracle = _field.get_prep_value  # the real patched repo method

    checked = 0

    # boundary: None (the empty value) --------------------------------------
    err = check(oracle, None)
    if err:
        print(err)
        return 1
    checked += 1

    # boundary identities x every storage form ------------------------------
    n_boundary = 1
    for u in boundary_identities():
        for raw in storage_forms(u):
            err = check(oracle, raw)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # randomized fuzz: 128-bit identities in the five main forms (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        u = uuid.UUID(int=rng.getrandbits(128))
        for raw in (u, u.hex, str(u), u.hex.upper(), u.int):
            err = check(oracle, raw)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl (over the real axiomatized callees) == real "
          "patched key-preparation method on %d inputs (%d boundary + %d fuzz "
          "identities x 5 forms, seed %d) on all four facets "
          "(is_none/canon/key/is_canon_form), and every non-empty prepared key "
          "resolves against its target key in a real dict join; "
          "0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees -> real repo functions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
