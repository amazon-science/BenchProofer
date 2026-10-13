#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13033 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`str`, `list[str]`), via the
              mapping.md bijection (`List (List Char)` ↔ `list[str]`,
              `List Char` ↔ `str`), with the single opaque leaf `renderedName`
              bound to its declared real callee, `repr` of a `str` (that
              binding itself is validated by axiom_check.py / G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `BaseTimeSeries._check_required_columns` (the correctness oracle,
              G-RESOLVE), driven via a minimal stand-in object exposing only the
              attributes the method reads, with its raised `ValueError` message
              captured.

They must agree on every input that drives the modeled mismatch arm. Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
Because the opaque per-element rendering is bound to the real `repr`, the fuzz
alphabet includes ADVERSARIAL names (embedded quotes, backslashes, control
characters, non-ASCII) as well as simple identifiers — the bijection is exact
for every name (mapping.md §2).
"""
import random
import sys

SEED = 13033
N_FUZZ = 100_000
SIMPLE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
ADVERSARIAL = [
    "a'b", 'a"b', "a'b\"c", "'", '"', "\\", "a\\b", "a\\\\b",
    "a\tb", "a\nb", "\x00", "\x1b[31m", "\x7f", "\xa0",
    "écolønne", "列名", "it's", 'she said "hi"', "mix'ed\"and\\slash",
]


# --- the R/I shadow: Solution.lean errorMessage, transliterated --------------
def render_column_list(names):
    """renderColumnList: a 1-element collection -> the quoted scalar (verbatim,
    no escaping); any other size -> the bracketed list of canonically-rendered
    names (renderedName bound to repr). Transliteration of the pure-region
    model."""
    if len(names) == 1:
        return "'%s'" % names[0]          # quoted (plain interpolation)
    # bracketList xs = '[' ++ joinRendered xs ++ ']'  (', '-joined repr names)
    return "[" + ", ".join(repr(n) for n in names) + "]"


def shadow_message(class_name, required, present):
    """errorMessage className required present, transliterated to str."""
    found = present[:len(required)]                     # present.take required.length
    plural = "s" if len(required) > 1 else ""
    return ("%s object is invalid - expected %s as the first column%s but found %s"
            % (class_name, render_column_list(required), plural,
               render_column_list(found)))


# --- the oracle: the REAL patched method, driven via a stand-in --------------
class _StandIn:
    """Exposes only the attributes _check_required_columns reads (mapping.md §4)."""
    pass


def oracle_message(class_name, required, present):
    """Drive the patched BaseTimeSeries._check_required_columns and return the
    ValueError message it raises (None if it does not raise)."""
    from astropy.timeseries.core import BaseTimeSeries  # patched at base_commit
    obj = _StandIn()
    obj.__class__ = type(class_name, (_StandIn,), {})   # __class__.__name__ == class_name
    obj._required_columns_enabled = True
    obj._required_columns_relax = False
    obj._required_columns = list(required)
    obj.colnames = list(present)
    try:
        BaseTimeSeries._check_required_columns(obj)
        return None
    except ValueError as e:
        return e.args[0]


def gen_case(rng):
    """Generate (class_name, required, present) that drives the mismatch arm:
    required non-empty, present non-empty, and present[:len(required)] != required
    (so the `elif ... != required_columns` arm fires), relax False."""
    def name():
        if rng.random() < 0.25:
            return rng.choice(ADVERSARIAL)
        return "".join(rng.choice(SIMPLE) for _ in range(rng.randint(1, 6)))
    def simple_name():
        return "".join(rng.choice(SIMPLE) for _ in range(rng.randint(1, 6)))
    class_name = simple_name()   # a Python class name; always an identifier
    nreq = rng.randint(1, 4)
    required = [name() for _ in range(nreq)]
    # build present so its required-length prefix differs from `required`
    npres = rng.randint(1, 5)
    present = [name() for _ in range(npres)]
    if present[:len(required)] == required:
        # force a mismatch in the first position
        present[0] = present[0] + "X" if present else "X"
        if not present:
            present = ["X"]
    return class_name, required, present


def boundary_cases():
    # the F2P scenario and neighbours (mapping.md): 2 required columns
    yield ("TimeSeries", ["time", "a"], ["time", "b"])
    yield ("TimeSeries", ["time", "a"], ["time"])
    yield ("TimeSeries", ["time"], ["a"])
    yield ("TimeSeries", ["time"], ["banana"])
    yield ("TimeSeries", ["time", "a", "c"], ["time", "x", "y"])
    yield ("TimeSeries", ["time", "flux"], ["time"])
    yield ("Foo", ["a", "b"], ["c", "d", "e"])
    yield ("Bar", ["x"], ["y", "z"])
    # adversarial names exercising the opaque-leaf binding at the call site
    yield ("TimeSeries", ["a'b", "c"], ["x", "y"])
    yield ("TimeSeries", ["a\\b", "c"], ["x", "y"])
    yield ("TimeSeries", ["time", 'q"uote'], ["time", "a\tb"])
    yield ("TimeSeries", ["列名", "é"], ["x", "y"])


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [gen_case(rng) for _ in range(N_FUZZ)]

    for class_name, required, present in cases:
        # only the mismatch arm is modeled; skip degenerate inputs that would
        # take a different (unchanged) branch
        if not required or not present:
            continue
        if present[:len(required)] == required:
            continue
        count += 1
        shadow = shadow_message(class_name, required, present)
        oracle = oracle_message(class_name, required, present)
        if shadow != oracle:
            disagreements.append((class_name, required, present, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cn, req, pres, sh, orc in disagreements:
            print("  class=%r required=%r present=%r\n    shadow=%r\n    oracle=%r"
                  % (cn, req, pres, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of requiredColumnsError agrees with the real "
          "patched _check_required_columns on %d inputs (seed=%d, adversarial "
          "names included), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
