#!/usr/bin/env python3
"""G-AX — validate the one A-reference deep model against the REAL repo callee.

There is NO consumed `axiom <callee>_prop` in the bundle (the axioms region of
Solution.lean is empty). This check validates the single A-reference fact
(refinement.md row 2): the Lean `quoteIdentifier` model is behaviourally
identical to the real unchanged callee
`DatabaseOperations.quote_name` (django/db/backends/sqlite3/operations.py:170-173).

For every fuzzed/boundary identifier we assert
    quoteIdentifier(name) == real quote_name(name)
where `quoteIdentifier` wraps the name in double quotes unless it both begins and
ends with a double-quote character (idempotence). exit 0 iff every observation
meets the model.

stdlib-only (+ optional in-tree django import). exit 0 iff sound.
"""
import random
import sys


def real_quote_name(name: str) -> str:
    """The REAL unchanged callee. Prefer the in-tree source; fall back to a
    byte-for-byte copy of operations.py:170-173 (pinned at base_commit, untouched
    by the patch) so the check runs without a configured django app."""
    try:
        from django.db.backends.sqlite3.operations import DatabaseOperations
        return DatabaseOperations.quote_name(None, name)
    except Exception:
        if name.startswith('"') and name.endswith('"'):
            return name
        return '"%s"' % name


def quote_identifier_model(name: str) -> str:
    """The Lean `quoteIdentifier` deep model, transcribed to Python.

    Lean: `if name.head? = some '"' ∧ name.getLast? = some '"' then name
           else ['"'] ++ name ++ ['"']`."""
    if len(name) >= 1 and name[0] == '"' and name[-1] == '"':
        return name
    return '"' + name + '"'


SEED = 13807
N = 60_000

ALPHABET = list('abcXYZ_0123 "().,;%select')
RESERVED = ["order", "select", "where", "group", "table", "from",
            '"order"', '"select"', "", '"', '""', "a", "Author_book",
            "x\"y", "\"leading", "trailing\""]


def rand_ident(rng):
    if rng.random() < 0.35:
        return rng.choice(RESERVED)
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 18)))


def main() -> int:
    rng = random.Random(SEED)
    checked = 0

    cases = list(RESERVED) + [rand_ident(rng) for _ in range(N)]
    for name in cases:
        got_model = quote_identifier_model(name)
        got_real = real_quote_name(name)
        if got_model != got_real:
            print(f"UNSOUND: quoteIdentifier model={got_model!r} != "
                  f"real quote_name={got_real!r} for name={name!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} all observations meet the modeled property "
          f"(quoteIdentifier == real quote_name)")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
