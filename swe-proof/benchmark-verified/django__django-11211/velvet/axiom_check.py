#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11211.

Executes the REAL unchanged callees the modeled `preparedValue` relies on and
asserts every observation meets the axioms' contracts (Solution.lean axioms
region), as bound in mapping.md §3.

The two A-consumed axioms:

  (A-consumed) `preCoerce` ↔ base `Field.get_prep_value`
      (django/db/models/fields/__init__.py:771). On the modeled value domain
      (None / a concrete UUID / its str transcription / its int transcription —
      none a lazy Promise) it is the IDENTITY: `preCoerce v = v`.

  (A-consumed) `canonicalize` ↔ `UUIDField.to_python`
      (django/db/models/fields/__init__.py:2338). Its load-bearing property is
      idempotence on well-formed input: `canonicalize (canonicalize v) =
      canonicalize v`. We also assert the property the prepared key actually
      relies on: a non-canonical transcription (str/int) is brought to the SAME
      canonical object as the concrete value it denotes — i.e. the conversion
      collapses interchangeable transcriptions to one stored form. (`WellFormed`
      domain: only values to_python accepts.)

Imports only the repo's own field module (`django.db.models`) and stdlib `uuid`
— the same code the gold patch calls, in-container. Exit 0 iff every obligation
holds.
"""
import os
import random
import sys
import uuid


def _setup_django():
    """Field instantiation is import-time-only; no DB needed, but importing the
    fields module pulls in app settings. Configure a minimal settings module."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    "django.contrib.contenttypes",
                    "django.contrib.auth",
                ],
                DATABASES={},
            )
        import django
        django.setup()
    except Exception:
        # Field construction below does not strictly require setup(); proceed.
        pass


def main():
    _setup_django()
    from django.db.models import UUIDField, Field

    field = UUIDField()
    base_get_prep = Field.get_prep_value          # the UNCHANGED base callee
    to_python = field.to_python                   # the UNCHANGED conversion

    rng = random.Random(11211)

    def well_formed_values():
        """A corpus of values UUIDField.to_python accepts (WellFormed domain)."""
        vals = [None]
        # boundary identifiers
        boundary = [
            uuid.UUID(int=0),
            uuid.UUID("ffffffffffffffffffffffffffffffff"),
            uuid.UUID("12345678123456781234567812345678"),
        ]
        # fuzzed identifiers (deterministic)
        fuzz = [uuid.UUID(int=rng.getrandbits(128)) for _ in range(2000)]
        for u in boundary + fuzz:
            vals.append(u)                  # concrete object  (Val.concrete)
            vals.append(str(u))             # hyphenated str    (Val.textual)
            vals.append(u.hex)              # 32-char hex str   (Val.textual)
            vals.append(u.int)             # int transcription (Val.numeric)
        return vals

    n = 0
    for v in well_formed_values():
        n += 1

        # (A-consumed) preCoerce_id: base get_prep_value is the identity here.
        prepped = base_get_prep(field, v)
        assert prepped is v or prepped == v, (
            "preCoerce_id unsound: base Field.get_prep_value(%r) -> %r "
            "(expected identity)" % (v, prepped))

        # (A-consumed) canonicalize is total on this domain (does not raise).
        canon = to_python(v)

        # canonicalize_idem: its output is a fixed point.
        canon2 = to_python(canon)
        assert canon2 == canon, (
            "canonicalize_idem unsound: to_python(to_python(%r))=%r != "
            "to_python(%r)=%r" % (v, canon2, v, canon))

        # the key-matching property: a transcription canonicalizes to the SAME
        # object as the concrete value it denotes (collapses interchangeable
        # transcriptions). None stays None.
        if v is None:
            assert canon is None
        else:
            assert isinstance(canon, uuid.UUID), (
                "to_python(%r) -> %r is not the canonical object" % (v, canon))
            if isinstance(v, uuid.UUID):
                assert canon == v
            else:
                # str/int transcription must denote the same canonical object
                # (constructed independently to avoid round-tripping via canon).
                if isinstance(v, int):
                    denoted = uuid.UUID(int=v)
                else:
                    denoted = uuid.UUID(hex=v)
                assert canon == denoted, (
                    "transcription %r canonicalized to %r, expected %r"
                    % (v, canon, denoted))

    print("G-AX OK: preCoerce (base Field.get_prep_value) identity and "
          "canonicalize (UUIDField.to_python) idempotent + transcription-"
          "collapsing on %d well-formed values (seed=11211)." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
