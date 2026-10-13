#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13033 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM with the contract
          calls (Requires/Ensures/Invariant/Assert and their Acc/list_pred
          arguments) stripped; the model IS Python, so no transliteration.
          PSeq is a thin tuple shim; the @Pure helpers copy over as plain
          functions. The shadow works over the model's carrier types
          (List[int] of name tokens / code points).

BRIDGE  — mapping.md §2's type abstraction: each column name is one token
          (its index into the concrete name list); a rendered token sequence
          is expanded back to the real string by substituting each encoded
          name token (>= 256) with its name and each punctuation/literal
          code point with its character. The bijection is exact on the
          documented domain (mapping.md "Domain note"): identifier-style
          names whose repr adds no escaping, which is the domain the repo
          callers actually supply. The fuzzer stays inside that domain.

ORACLE  — the REAL patched repo behaviour: BaseTimeSeries.
          _check_required_columns (PYTHONPATH=/testbed, gold patch applied
          by the gate before this script runs), driven via a minimal
          stand-in object exposing only the attributes the method reads;
          the raised ValueError message is the observable. This exercises
          both modeled functions at once: the per-run rendering (the nested
          helper) and the full report assembly.

The shadow and the oracle must agree on every input that drives the modeled
leading-run-disagreement branch. Exit 0 iff zero disagreements over the
boundary cases + 100000 fuzzed inputs. Pinned seed: 13033. stdlib only.
"""
import random
import sys

SEED = 13033
N_FUZZ = 100_000

# ---------------------------------------------------------------------------
# Contract shims: nagini_contracts symbols stripped to executable Python.
# ---------------------------------------------------------------------------


class PSeq:
    """Plain tuple shim for nagini's pure sequence type."""

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# model.py constants and pure region, copied over as plain functions
# (@Pure and the Ensures ghost lines stripped).
# ---------------------------------------------------------------------------

NAME_QUOTE = 39   # "'"
COMMA = 44        # ","
SPACE = 32        # " "
LBRACK = 91       # "["
RBRACK = 93       # "]"


def empty_seq():
    return PSeq(0).take(0)


def encode_name(t):
    return t + 256


def quoted(t):
    return PSeq(NAME_QUOTE) + PSeq(encode_name(t)) + PSeq(NAME_QUOTE)


def joined(run):
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return quoted(run[0])
    return quoted(run[0]) + PSeq(COMMA, SPACE) + joined(run.drop(1))


def render_run(run):
    if len(run) == 1:
        return quoted(run[0])
    return PSeq(LBRACK) + joined(run) + PSeq(RBRACK)


def report_seq(cls_name, demanded, found):
    seg1 = PSeq(32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
                118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
                116, 101, 100, 32)
    seg2 = PSeq(32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
                32, 99, 111, 108, 117, 109, 110)
    plural = PSeq(115) if len(demanded) > 1 else empty_seq()
    seg3 = PSeq(32, 98, 117, 116, 32, 102, 111, 117, 110, 100,
                32)
    return (cls_name + seg1 + render_run(demanded) + seg2 + plural + seg3
            + render_run(found))


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------


def render_name_run(run):
    run_s = ToSeq(run)
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]
        return out_single
    # any other length -> bracketed textual list form
    inner = []
    i = len(run)
    while i > 0:
        elt = run[i - 1]
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]
    return result


def compose_leading_run_report(cls_name, demanded, found):
    expected_field = render_name_run(demanded)
    found_field = render_name_run(found)
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]
    if len(demanded) > 1:
        plural = [115]
    else:
        plural = []
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)
    return result


# ---------------------------------------------------------------------------
# Bridge: real strings -> tokens, shadow output tokens -> real string
# (mapping.md §2; same expansion axiom_check.py validates for G-AX).
# ---------------------------------------------------------------------------


def expand(model_seq, names):
    out = []
    for code in model_seq:
        if code >= 256:
            out.append(names[code - 256])
        else:
            out.append(chr(code))
    return "".join(out)


def shadow_message(class_name, demanded_names, found_names):
    dem_tokens = list(range(len(demanded_names)))
    fnd_tokens = list(range(len(demanded_names),
                            len(demanded_names) + len(found_names)))
    all_names = demanded_names + found_names
    cls_points = [ord(c) for c in class_name]  # ASCII class names only
    out = compose_leading_run_report(cls_points, dem_tokens, fnd_tokens)
    return expand(out, all_names)


# ---------------------------------------------------------------------------
# Oracle: the REAL patched method, driven via a stand-in exposing only the
# attributes it reads; the ValueError message is the observable.
# ---------------------------------------------------------------------------

class _StandIn:
    pass


_CLASS_CACHE = {}


def oracle_message(class_name, required, present):
    from astropy.timeseries.core import BaseTimeSeries
    obj = _StandIn()
    cls = _CLASS_CACHE.get(class_name)
    if cls is None:
        cls = type(class_name, (_StandIn,), {})
        _CLASS_CACHE[class_name] = cls
    obj.__class__ = cls
    obj._required_columns_enabled = True
    obj._required_columns_relax = False
    obj._required_columns = list(required)
    obj.colnames = list(present)
    try:
        BaseTimeSeries._check_required_columns(obj)
        return None
    except ValueError as e:
        return e.args[0]


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying inputs that drive the modeled branch
# (required non-empty, present non-empty, leading run disagrees). Names stay
# inside the documented token-bijection domain: identifier characters only.
# ---------------------------------------------------------------------------

IDENT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"


def gen_case(rng):
    def name():
        return "".join(rng.choice(IDENT) for _ in range(rng.randint(1, 8)))
    class_name = rng.choice(
        ["TimeSeries", "BinnedTimeSeries", "SampledTimeSeries", "Foo", "Bar"])
    nreq = rng.randint(1, 5)
    required = [name() for _ in range(nreq)]
    npres = rng.randint(1, 6)
    present = [name() for _ in range(npres)]
    if present[:len(required)] == required:
        present[0] = present[0] + "X"
    return class_name, required, present


def boundary_cases():
    # the issue scenario (two demanded names) and neighbours
    yield ("TimeSeries", ["time", "a"], ["time", "b"])
    yield ("TimeSeries", ["time", "a"], ["time"])        # found run shorter
    yield ("TimeSeries", ["time"], ["a"])                # single demanded name
    yield ("TimeSeries", ["time"], ["banana"])
    yield ("TimeSeries", ["time", "a", "c"], ["time", "x", "y"])
    yield ("TimeSeries", ["time", "flux"], ["time"])
    yield ("BinnedTimeSeries", ["time_bin_start", "a"], ["time_bin_start"])
    yield ("Foo", ["a", "b"], ["c", "d", "e"])
    yield ("Bar", ["x"], ["y", "z"])
    yield ("TimeSeries", ["t"], ["q", "r", "s", "u", "v"])
    yield ("TimeSeries", ["a", "a"], ["a", "b"])         # repeated name
    yield ("TimeSeries", ["w", "x", "y", "z"], ["w"])    # long demanded run


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [gen_case(rng) for _ in range(N_FUZZ)]

    for class_name, required, present in cases:
        # only the leading-run-disagreement branch is modeled
        if not required or not present:
            continue
        if present[:len(required)] == required:
            continue
        count += 1
        found = present[:len(required)]  # the repo-side slice (mapping.md B3)
        shadow = shadow_message(class_name, required, found)
        oracle = oracle_message(class_name, required, present)
        if shadow != oracle:
            disagreements.append((class_name, required, present, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for cn, req, pres, sh, orc in disagreements:
            print("  class=%r required=%r present=%r\n    shadow=%r\n    oracle=%r"
                  % (cn, req, pres, sh, orc))
        return 1
    print("G-CONF OK: model.py impl shadow (token carrier, expanded via the "
          "mapping.md bijection) agrees with the real patched "
          "_check_required_columns message on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
