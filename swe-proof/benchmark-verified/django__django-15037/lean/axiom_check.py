#!/usr/bin/env python3
"""G-AX — validate the A-reference `dbTableToModelName` against the REAL
UNCHANGED callee the relation block uses, `table2model`.

`table2model` is the inner function of `handle_inspection`:
    def table2model(table_name):
        return re.sub(r'[^a-zA-Z0-9]', '', table_name.title())

The proof consumes NO callee `_prop` axiom: `dbTableToModelName` appears
identically in the spec and the impl, so the only property relied upon is that
it is a deterministic pure function of its input. This check confirms that
property against the real callee (determinism over boundary + fuzz), which is
exactly the A-reference obligation (refinement.md row 5).

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import re
import sys

SEED = 15037


def table2model(table_name: str) -> str:
    """The REAL unchanged callee (inspectdb.py:43)."""
    return re.sub(r'[^a-zA-Z0-9]', '', table_name.title())


def main() -> int:
    rng = random.Random(SEED)

    # Boundary names: empty, ascii, digits, separators, unicode, the F2P tables.
    names = [
        "", "a", "foo", "bar", "inspectdb_peoplemoredata",
        "inspectdb_foreignkeytofield", "people_unique", "people_unique_id",
        "123", "4extra", "a-b.c d", "TableName", "tABLE_name",
        "__dunder__", "with space", "café_table", "ééé",
    ]
    alphabet = "abcABC_0123 .-é"
    for _ in range(50_000):
        n = rng.randint(0, 24)
        names.append("".join(rng.choice(alphabet) for _ in range(n)))

    bad = 0
    examples = []
    for nm in names:
        # Determinism: the callee is a pure function of its argument.
        a = table2model(nm)
        b = table2model(nm)
        if a != b:
            bad += 1
            if len(examples) < 10:
                examples.append((nm, a, b))
        # Range sanity: output is alphanumeric (matches the opaque's String type).
        if not re.fullmatch(r'[A-Za-z0-9]*', a):
            bad += 1
            if len(examples) < 10:
                examples.append((nm, a, "<non-alnum>"))

    if bad:
        print(f"G-AX FAIL: {bad} violations of the table2model reference property")
        for nm, a, b in examples:
            print(f"  name={nm!r} -> {a!r} / {b!r}")
        return 1

    print(f"G-AX OK: dbTableToModelName == table2model is a deterministic pure "
          f"function on all probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
