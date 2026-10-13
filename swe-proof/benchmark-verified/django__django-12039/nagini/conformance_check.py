#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12039 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helper `sep`
copies over as a plain function. After stripping, the impl uses only plain
lists (PSeq appears solely inside contracts), so no PSeq shim is needed.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo logic the model models per mapping.md — the
per-column rendering performed inside
`django.db.backends.ddl_references.Columns.__str__` (site 1) and
`django.db.backends.ddl_references.IndexColumns.__str__` (site 2). The inner
helper is a closure, so the oracle drives it through the public `__str__` of a
single-column instance: with exactly one column, `', '.join(...)` degenerates
to that column's rendered text. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable
(the module has no settings dependency).

Type bridge (mapping.md section 2): repo `str` values map to List[int] of
Unicode code points (`[ord(ch) for ch in s]`; empty str <-> []). The model's
`base` input is the site's already-assembled base token, produced UPSTREAM of
the modeled operation:
  * site 1: the quoted column — realized by passing a quoting callable that
    returns an arbitrary generated string;
  * site 2: the quoted column combined with its operator-class keyword — the
    repo assembles it as `'{} {}'.format(quoted, opclass)`, so the bridge
    computes the model's `base` the same way from the generated (quoted,
    opclass) pair.
The model's `suffix` input is `col_suffixes[idx]`, supplied directly.

Input domain: the model's Requires demands only read access to the two lists,
so any (base, suffix) code-point pair is Requires-satisfying; generation draws
arbitrary strings (printable ASCII plus a slice of non-ASCII code points),
weighting the empty suffix heavily since it is one of the two behavioural
branches.

>= 1e5 Requires-satisfying inputs: boundary cases + 50000 fuzz pairs, each
pair exercised at BOTH sites (>= 100096 shadow-vs-oracle comparisons).
Pinned fuzz seed: 12039.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12039
N_FUZZ = 50_000


# --- pure helper from model.py, contracts stripped ----------------------------

def sep():
    return 32


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_column(base, suffix):
    result = []  # type: list
    # base token
    j = 0
    while j < len(base):
        result.append(base[j])
        j = j + 1
    # only append a separator + suffix when the suffix is non-empty
    if len(suffix) > 0:
        result.append(sep())
        k = 0
        while k < len(suffix):
            result.append(suffix[k])
            k = k + 1
    return result


def render_column_with_opclass(base, suffix):
    result = []  # type: list
    # base token
    j = 0
    while j < len(base):
        result.append(base[j])
        j = j + 1
    # only append a separator + suffix when the suffix is non-empty
    if len(suffix) > 0:
        result.append(sep())
        k = 0
        while k < len(suffix):
            result.append(suffix[k])
            k = k + 1
    return result


# --- bridge: str <-> List[int] code points ------------------------------------

def cp(s):
    return [ord(ch) for ch in s]


def from_cp(lst):
    return "".join(chr(c) for c in lst)


def real_site1(Columns, quoted, suffix):
    """Real rendered text of one column at site 1: a single-column Columns
    instance whose quoting callable yields the given base token."""
    obj = Columns("tbl", ["c0"], (lambda name: quoted), col_suffixes=[suffix])
    return str(obj)


def real_site2(IndexColumns, quoted, opclass, suffix):
    """Real rendered text of one column at site 2: a single-column
    IndexColumns instance; the repo itself combines the quoted column with the
    operator-class keyword to form the base token."""
    obj = IndexColumns("tbl", ["c0"], (lambda name: quoted),
                       col_suffixes=[suffix], opclasses=[opclass])
    return str(obj)


def check_pair(Columns, IndexColumns, quoted, opclass, suffix):
    """Compare shadow vs oracle at both sites for one generated input;
    return an error string on disagreement, else None."""
    # site 1: base = the quoted column alone
    shadow1 = render_column(cp(quoted), cp(suffix))
    real1 = real_site1(Columns, quoted, suffix)
    if from_cp(shadow1) != real1:
        return ("DISAGREEMENT site1\n  quoted=%r suffix=%r\n  shadow=%r\n  real=%r"
                % (quoted, suffix, from_cp(shadow1), real1))

    # site 2: base = the quoted column combined with the operator-class
    # keyword (assembled upstream of the modeled operation, mirrored here)
    base2 = "{} {}".format(quoted, opclass)
    shadow2 = render_column_with_opclass(cp(base2), cp(suffix))
    real2 = real_site2(IndexColumns, quoted, opclass, suffix)
    if from_cp(shadow2) != real2:
        return ("DISAGREEMENT site2\n  quoted=%r opclass=%r suffix=%r\n"
                "  shadow=%r\n  real=%r"
                % (quoted, opclass, suffix, from_cp(shadow2), real2))
    return None


def boundary_cases():
    quoteds = ['"headline"', '"name"', "", "x", '`a b`', '"weird""q"']
    opclasses = ["text_pattern_ops", "varchar_pattern_ops", "", "o p s"]
    suffixes = ["", "DESC", "ASC", "NULLS FIRST", " ", "D"]
    return [(q, o, s) for q in quoteds for o in opclasses for s in suffixes]


ALPHABET = [chr(c) for c in range(32, 127)] + [chr(c) for c in (160, 233, 955, 20013)]


def rand_str(rng, nmax):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, nmax)))


def main():
    sys.path.insert(0, "/testbed")
    from django.db.backends.ddl_references import Columns, IndexColumns  # REAL patched callees

    checked = 0
    for quoted, opclass, suffix in boundary_cases():
        err = check_pair(Columns, IndexColumns, quoted, opclass, suffix)
        if err:
            print(err)
            return 1
        checked += 2  # both sites

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        quoted = rand_str(rng, 24)
        opclass = rand_str(rng, 20)
        # weight the empty suffix heavily: it is one of the two branches
        suffix = "" if rng.random() < 0.4 else rand_str(rng, 12)
        err = check_pair(Columns, IndexColumns, quoted, opclass, suffix)
        if err:
            print(err)
            return 1
        checked += 2  # both sites

    print("G-CONF OK: shadow impl == real per-column rendering on %d "
          "comparisons (%d boundary + %d fuzz pairs, both sites, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
