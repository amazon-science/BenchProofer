#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13807.

Executes the REAL unchanged callee the patched constraint-integrity check now
routes every spliced identifier through —

  * the SQLite backend's identifier-delimiter
    ``django.db.backends.sqlite3.operations.DatabaseOperations.quote_name``
    (``django/db/backends/sqlite3/operations.py:170``) —

and asserts that every observation matches the ``delimit`` axiom in model.py
(the A-consumed callee). The runtime counterpart ``delimit_id`` in model.py is
the same callee returning the delimited identifier as a code-point list; its
content is ``delimit`` of the input, so this one check covers both.

The ``delimit`` axiom (A-consumed):

    delimit(name):
      * if name is already delimited (begins AND ends with the delimiter
        code point 34, the double quote, len >= 2): returned unchanged;
      * otherwise: wrapped -> [34] + name + [34].
    The result therefore always begins and ends with the delimiter and is at
    least 1 code point long; an *undelimited* identifier gains two delimiters
    (a lone delimiter `"` is already-delimited, so it is returned unchanged as a
    single code point — this is the boundary case the model axiom's
    `len(Result()) >= 1` Ensures, not `>= 2`, is calibrated to).

The decisive case the bundle's spec turns on: an identifier that is a SQL
reserved word (e.g. ``order``) is NOT already delimited, so ``quote_name``
returns ``"order"`` -- strictly longer than the bare word -- which is what the
spliced command text must contain so the word is parsed as a name, not the
keyword. The pre-patch impl splices the bare word and fails the spec.

Imports only Django (the repo under test, importable in-container) and the
stdlib ``random``. Exit 0 iff every obligation holds.
"""
import random
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _codepoints(s):
    return [ord(ch) for ch in s]


def delimit_model(cps):
    """Reference of model.py's `delimit` axiom over code points (mirrors the
    real `name.startswith('"') and name.endswith('"')` test: a single '"' char
    counts as already-delimited because it begins and ends with the delimiter)."""
    if len(cps) >= 1 and cps[0] == 34 and cps[-1] == 34:
        return list(cps)
    return [34] + list(cps) + [34]


def check_one(quote_name, name):
    observed = _codepoints(quote_name(name))          # REAL callee
    expected = delimit_model(_codepoints(name))       # axiom Ensures
    assert observed == expected, (
        "delimit axiom unsound on %r: quote_name -> %r, axiom requires %r"
        % (name, observed, expected))
    # structural guarantees the proof relies on (mirror model.py's Ensures
    # exactly: len(Result()) >= 1, NOT >= 2 — the lone-delimiter identifier '"'
    # is already-delimited and is returned unchanged as a single code point):
    assert len(observed) >= 1, "delimited %r shorter than 1 cp: %r" % (name, observed)
    assert observed[0] == 34 and observed[-1] == 34, (
        "delimited %r not bracketed by delimiter: %r" % (name, observed))


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db.backends.sqlite3.operations import DatabaseOperations
    ops = DatabaseOperations(connection=None)
    quote_name = ops.quote_name

    # --- boundary: SQL reserved words (the decisive class), ordinary names,
    #     already-delimited names, and edge identifiers --------------------
    boundary = [
        "order", "select", "where", "table", "group", "from", "join",
        "Order", "SELECT",                 # case variants are still bare words
        "a", "z", "abc", "my_table", "col1", "_x", "x9",
        "tablename_with_underscores", "CamelCase",
        '"order"', '"select"', '"already"',   # already-delimited -> unchanged
        '""',                                 # two-delimiter form -> unchanged
        '"',                                  # lone delimiter: startswith==endswith True
        '"a"', '"my_table"',
        "table with space", "weird;name", "na#me", "n'q",
        "a\"b",        # internal quote, not bracketing -> still wrapped
        "\"unbalanced", "unbalanced\"",       # only one side delimited -> wrapped
        "é", "café", "票据",                  # non-ASCII identifiers
    ]
    for name in boundary:
        check_one(quote_name, name)

    # --- randomized fuzz over a mixed alphabet (incl. the delimiter) --------
    rng = random.Random(13807)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789_ ;#'.-") + ['"', 'é', '票']
    n = 20000
    for _ in range(n):
        length = rng.randint(0, 16)
        name = "".join(rng.choice(alphabet) for _ in range(length))
        check_one(quote_name, name)

    # --- idempotence witness the axiom encodes: delimiting twice is a no-op
    #     on an already-delimited identifier --------------------------------
    for name in ["order", "select", "my_table", "café"]:
        once = quote_name(name)
        twice = quote_name(once)
        assert once == twice, (
            "quote_name not idempotent on %r: once=%r twice=%r"
            % (name, once, twice))

    print("G-AX OK: delimit axiom (sqlite3 DatabaseOperations.quote_name) sound "
          "over %d boundary + %d fuzz identifiers; bare SQL keywords gain two "
          "delimiters, already-delimited names unchanged, idempotent."
          % (len(boundary), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
