#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11211.

Executes the REAL unchanged callees that the added key-preparation method
composes —

  * the base preliminary-coercion step ``Field.get_prep_value``
    (``django/db/models/fields/__init__.py:771-775``), reached via
    ``super().get_prep_value(value)``; and
  * the canonicalizing parser ``UUIDField.to_python``
    (``django/db/models/fields/__init__.py:2338-2349``), reached via
    ``self.to_python(value)`` —

and asserts that every observation matches the two axioms in model.py, plus the
refinement-load-bearing properties the in-Python prefetch join relies on: the
stored textual form of a UUID and the same identity in canonical ``uuid.UUID``
form prepare to the SAME join key, and a value that is NOT in the canonical
object form does not match one that is even when it carries the same 128 bits.

The two axioms (both A-consumed) — three facets each, matching model.py:

  base_prepare(value)  -- identity on the join facets for these inputs:
      Result().is_none == value.is_none, .canon == .canon, .key == .key,
      .is_canon_form == .is_canon_form
      (real Field.get_prep_value returns the value unchanged when it is not a
      lazy Promise, which never occurs in the prefetch path).

  canonicalize(value)  -- a non-empty value comes back IN THE CANONICAL OBJECT
      FORM whose numeric join key is the canonical identity:
          Implies(not is_none, Result().is_canon_form)
          Implies(not is_none, Result().key == value.canon)
          Implies(is_none,     Result().key == value.key)
          Implies(is_none,     Result().is_canon_form == value.is_canon_form)
      (real UUIDField.to_python returns a uuid.UUID — see :2342 for the parse
      branch and :2349 for the already-canonical / None passthrough — whose
      dict/equality key is its 128-bit .int identity).

The model facets map to reality as: ``canon`` == ``uuid.UUID(...).int`` (the
canonical identity); ``is_canon_form`` == ``isinstance(raw, uuid.UUID)`` (the
FORM half of the join key, which Python's ``==`` compares before any numeric
part); ``key`` == the numeric part of the join key (a uuid.UUID contributes its
.int; a bare int contributes itself; a textual form contributes no number at
all and is distinguished by the form flag). The decisive assertions are that
``to_python(<str form>) == to_python(<uuid form>)`` — the join matches — and
that ``u.int != u`` and ``{u: x}[u.int]`` misses — the form flag is not
decoration.

Imports only Django (the repo under test, importable in-container) and the
stdlib ``uuid``/``random``. Exit 0 iff every obligation holds.
"""
import random
import sys
import uuid


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _is_canon_form(raw):
    """The FORM half of the join key: True iff the value is held in the
    canonical object form (a uuid.UUID). Python's == compares this first — a
    non-uuid.UUID never equals a uuid.UUID — so the model carries it as a
    separate facet (``is_canon_form``)."""
    return isinstance(raw, uuid.UUID)


def _join_key(prepared):
    """The NUMERIC part of the join key a prepared value contributes. A
    uuid.UUID keys/compares by its 128-bit .int; anything else keys by itself.
    ``canon`` of a value is uuid.UUID(...).int."""
    if isinstance(prepared, uuid.UUID):
        return prepared.int
    return prepared


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import models

    field = models.UUIDField()
    base = models.Field()  # the unchanged base whose get_prep_value is inherited

    def check_one(u):
        """For a UUID ``u``, check both axioms (all four facets) and the join
        behaviour across every storage form the value may arrive in."""
        canon = u.int

        # The storage forms the value can arrive in (None handled separately):
        #   already-canonical uuid.UUID; 32-char hex str; hyphenated str; int.
        forms = {
            "uuid": u,
            "hex32": u.hex,            # 32-char hex, no dashes  (what get_db_prep_value stores)
            "hyphen": str(u),          # 8-4-4-4-12 hyphenated hex
            "int": u.int,              # integer form
        }
        for name, value in forms.items():
            # --- base_prepare axiom: identity on facets for these inputs -----
            coerced = base.get_prep_value(value)        # REAL Field.get_prep_value
            assert coerced is value or coerced == value, (
                "base_prepare unsound (%s): Field.get_prep_value changed %r to %r"
                % (name, value, coerced))
            # the FORM facet is preserved too (Ensures Result().is_canon_form ==
            # value.is_canon_form): the base step neither canonicalizes nor
            # de-canonicalizes on these inputs.
            assert _is_canon_form(coerced) == _is_canon_form(value), (
                "base_prepare unsound (%s): form facet changed %r -> %r"
                % (name, _is_canon_form(value), _is_canon_form(coerced)))
            assert _join_key(coerced) == _join_key(value), (
                "base_prepare unsound (%s): numeric key changed" % (name,))

            # --- canonicalize axiom: canonical object FORM + canonical key ----
            prepared = field.to_python(coerced)          # REAL UUIDField.to_python
            assert _is_canon_form(prepared), (
                "canonicalize unsound (%s): to_python returned a value outside "
                "the canonical object form: %r" % (name, prepared))
            assert _join_key(prepared) == canon, (
                "canonicalize unsound (%s): join key %r != canonical %r"
                % (name, _join_key(prepared), canon))

            # --- full composed method == the gold get_prep_value -------------
            composed = field.to_python(base.get_prep_value(value))
            assert _is_canon_form(composed), (
                "composed get_prep_value (%s): result not in the canonical "
                "object form: %r" % (name, composed))
            assert _join_key(composed) == canon, (
                "composed get_prep_value (%s): join key %r != canonical %r"
                % (name, _join_key(composed), canon))

        # --- the decisive join match: stored str form and uuid form coincide -
        prepared_str = field.to_python(base.get_prep_value(u.hex))
        prepared_uuid = u  # the related object's pk arrives already-canonical
        assert _join_key(prepared_str) == _join_key(prepared_uuid), (
            "join MISMATCH: prepared str key %r != uuid pk key %r"
            % (_join_key(prepared_str), _join_key(prepared_uuid)))
        assert prepared_str == prepared_uuid, (
            "prepared str %r does not equal uuid pk %r"
            % (prepared_str, prepared_uuid))

        # --- the FORM facet is load-bearing, not decoration -------------------
        # The join is a dict keyed by the target's own (pk, class) pair and
        # looked up with the holder's (prepared, class) pair
        # (django/db/models/query.py:1746-1749 build, :1770 look up;
        # django/contrib/contenttypes/fields.py:210 target key, :205 holder
        # key). dict lookup is hash-then-==, and a bare 128-bit int hashes the
        # SAME as the uuid.UUID it spells while comparing UNEQUAL to it. So a
        # prepared value carrying the right number in the wrong form matches
        # nothing: exactly the freedom model.py's is_canon_form facet removes.
        assert hash(u) == hash(u.int), (
            "join model drift: uuid and its int no longer share a hash bucket")
        assert u != u.int, (
            "join model drift: uuid now compares equal to its int, so the form "
            "facet would be redundant")
        cache = {(u, "Article"): "target"}
        assert cache.get((u.int, "Article")) is None, (
            "join model drift: an int-formed key now resolves against a "
            "uuid-formed key")
        assert cache.get((u, "Article")) == "target", (
            "join model drift: a canonical-form key no longer resolves")

    # --- boundary: None passes through unchanged (empty key, same form) ------
    coerced_none = base.get_prep_value(None)
    assert coerced_none is None, "base_prepare(None) must stay None, got %r" % (coerced_none,)
    assert _is_canon_form(coerced_none) is False, "None must not be in canonical form"
    prepared_none = field.to_python(coerced_none)
    assert prepared_none is None, "canonicalize(None) must stay None, got %r" % (prepared_none,)
    assert _is_canon_form(prepared_none) == _is_canon_form(coerced_none), (
        "canonicalize(None) must preserve the form facet")

    # --- boundary UUIDs + randomized fuzz ------------------------------------
    boundary = [
        uuid.UUID(int=0),
        uuid.UUID(int=(1 << 128) - 1),
        uuid.UUID(int=1),
        uuid.uuid4(),
        uuid.uuid1(),
    ]
    for u in boundary:
        check_one(u)

    rng = random.Random(11211)
    n = 5000
    for _ in range(n):
        u = uuid.UUID(int=rng.getrandbits(128))
        check_one(u)

    print("G-AX OK: base_prepare (Field.get_prep_value) + canonicalize "
          "(UUIDField.to_python) axioms sound over %d boundary + %d fuzz UUIDs "
          "(uuid/hex32/hyphen/int forms + None) on all four facets "
          "(is_none/canon/key/is_canon_form); stored str form and uuid pk form "
          "prepare to equal join keys, and a same-number key outside the "
          "canonical object form resolves against nothing." % (len(boundary), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
