#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13807.

The bundle declares **no consumed axioms**. The single routine the construction
leans on — the SQLite backend's SQL identifier quoter — is modeled DEEPLY by
`quoteIdent` (Solution.lean pure region), an **A-reference**: G-AX validates that
deep model against the REAL callee rather than trusting an axiom's `ensures`.

The A-reference claim:

  (A-reference) `quote_ident` (this file, the reference encoding of Solution.lean's
      `quoteIdent`) == the REAL SQLite backend quoter
      `DatabaseOperations.quote_name` for every identifier:
        * an identifier already wrapped in double quotes is returned unchanged
          (quoting once is enough);
        * any other identifier is wrapped in double quotes.

This is the per-identifier transform the gold patch applies at the three
positions where `check_constraints` embeds an identifier in a SQL statement
(mapping.md §3). Validating it == the real quoter is what makes the statement
builders' deep model sound.

Imports Django (present in the SWE-Bench instance image) + stdlib only. The
quoter is a pure string method that does not touch the live connection, so a
`DatabaseOperations` constructed with a dummy connection suffices. Exit 0 iff
every observation matches the deep model.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=False,
    )
    django.setup()

from django.db.backends.sqlite3.operations import DatabaseOperations


# --- Solution.lean reference encoding (kept in lock-step with quoteIdent) -----

def quote_ident(name):
    """Reference impl of Solution.lean's deep model `quoteIdent`:
       if name starts and ends with '"' -> unchanged; else wrap in '"'."""
    if name[:1] == '"' and name[-1:] == '"':
        return name
    return '"' + name + '"'


# --- the check ---------------------------------------------------------------

def check_quote_reference(ops, name):
    """Assert the deep model quote_ident(name) == the REAL quote_name(name)."""
    observed = ops.quote_name(name)        # real callee
    expected = quote_ident(name)           # deep model
    assert observed == expected, (
        "quoteIdent deep model unsound on %r: quote_name gave %r, "
        "deep model gives %r" % (name, observed, expected))


def main():
    ops = DatabaseOperations(connection=None)

    # --- boundary cases -------------------------------------------------------
    boundary = [
        "",                                  # empty identifier
        "order", "select", "where",          # SQL keywords (the F2P scenario)
        "table", "from", "group",            # more keywords
        "id", "name", "reporter_id",         # ordinary identifiers
        "a", "Z", "_x", "x9",
        '"order"',                           # already double-quoted -> unchanged
        '"select"', '"where"',
        '"', '""',                           # degenerate quote-only identifiers
        '"a',                                # leading quote only (NOT both ends)
        'a"',                                # trailing quote only
        "with space", "weird;name", "a.b",
        "MixedCase", "UPPER",
    ]
    for name in boundary:
        check_quote_reference(ops, name)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13807)
    alphabet = list('abcdefABCDEF_0123456789') + ['"', ' ', ';', '.', '-', "'"]
    for _ in range(20000):
        n = rng.randint(0, 16)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        check_quote_reference(ops, name)

    print("G-AX OK: quoteIdent deep model (== DatabaseOperations.quote_name) "
          "sound on %d boundary + 20000 fuzz identifiers" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
