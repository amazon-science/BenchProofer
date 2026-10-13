#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3677 (nagini).

SHADOW — the impl regions of `model.py`, copied VERBATIM with only the contract
calls stripped: the `@Pure` helper `is_array_shaped`, the deep model
`as_mapping` (its whole impl region, including the signalling path for the
operand class on which the normalisation is undefined),
and `merge_method`'s impl region (`second = other` / `if is_array_shaped(other):
second = as_mapping(other)` / `result = [receiver, second]`). The `Operand`
carrier class is copied too, minus its `Ensures`. No transliteration and no
restructuring: on nagini the model IS Python. This bundle consumes NO
`@ContractOnly` axiom (mapping.md §4), so there is no axiomatized callee to
redirect; the one A-reference callee (`DataArray.to_dataset()`) is nevertheless
exercised for real on both legs — see ORACLE and the deep-model cross-check.

ORACLE CHOICE — the REAL patched repo function is CALLED, not transliterated.
mapping.md §1 binds `merge_method` to the body of `Dataset.merge`
(`xarray/core/dataset.py:3548`, the operand construction at `dataset.py:3606-3615`
that the gold hunk feeds). The modeled OUTPUT is the two-operand sequence handed
to the core combination routine, which in the real code is the `(dataset, other)`
pair `Dataset.merge` passes to `dataset_merge_method` (which then builds
`objs = [dataset, other]`, `xarray/core/merge.py:817-819`, for the default
`overwrite_vars=frozenset()` this script always uses). So the oracle runs the
patched `Dataset.merge` with `xarray.core.dataset.dataset_merge_method` wrapped
by a spy that records the operand pair it actually receives and then delegates to
the real callee. Nothing is reimplemented: the branch decision
(`isinstance(other, xr.DataArray)`) and the conversion (`other.to_dataset()`,
i.e. the A-reference callee) are executed by the real patched module, and the
real merge is allowed to run to completion afterwards so the bug's own symptom
(`AttributeError: 'DataArray' object has no attribute 'items'` from
`coerce_pandas_values`, `merge.py:394`) is observable if it ever reappears.
The gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before this
script runs; `_assert_oracle_is_patched()` refuses to run against unpatched
source, so a green result cannot come from an unpatched oracle.

TYPE BRIDGE (mapping.md §2, inverted) — abstract `Operand(is_mapping, name,
value)` <-> a real merge operand. Concrete -> abstract: `is_mapping =
hasattr(obj, "items")` (the named-entry interface the core routine requires of
every operand — the real property the bijection names, deliberately NOT an
`isinstance` re-test of the patched branch condition, so a divergence between
"is a DataArray" and "lacks .items()" would show up as a disagreement), `name` =
the single/first data variable's `Hashable` name through the fixed name<->code
bijection `_NAME_BY_CODE` (`-1` = no name, per mapping.md §2), `value` = that
variable's scalar `int` data. Abstract -> concrete: a code/value pair becomes
either `xr.DataArray(data=value, name=_NAME_BY_CODE[name])` (array-shaped) or
`xr.Dataset({name: value, ...})` (mapping-shaped). Inputs are generated
concretely and abstracted, so every generated input lands inside the model's
`Requires` by construction: the receiver is always a `Dataset` (mapping-shaped,
it is the method receiver), receiver and argument are always distinct objects,
and an array-shaped argument is always NAMED (`name >= 0`) — an unnamed
`DataArray` is outside the modeled domain because the conversion is undefined
there (`_to_dataset_whole` raises, `dataarray.py:467-471`; mapping.md §3.1).
`name_is_own_label` is read off the real object as `name in obj.coords`: the
conversion is ALSO undefined when the array's name is one of its own coordinate
names (`_to_dataset_whole` raises a second ValueError, `dataarray.py:472-476`),
and unlike the unnamed case that class is INSIDE the modeled domain (it is a
named array-shaped operand), so it is generated systematically and in fuzz and
its outcome is diffed like any other.

WHAT IS DIFFED, per postcondition of `merge_method`:
  * WHICH OUTCOME occurred          — the real merge built an operand sequence
                                         iff the shadow returned one; a shadow
                                         that returns where the real conversion
                                         is undefined, or signals where it is
                                         defined, is a disagreement;
  * `len(...) == 2`                    — the real operand pair has two operands;
  * `Result()[0] is receiver`          — real operand 0 is the receiver OBJECT;
  * `Result()[i].is_mapping`           — BOTH real operands expose `.items()`
                                         (the clause the pre-patch violates);
  * `Result()[1].name/.value == other.name/.value` — the real second operand
                                         still carries the argument's single
                                         named value, name and value;
  * `Implies(not is_array_shaped(other), Result()[1] is other)` — a
                                         mapping-shaped argument reaches the core
                                         as the SAME object (no lossy rebuild).
Every clause is compared field-by-field against the shadow's output, so a
disagreement in either direction fails. Additionally, on each array-shaped input
the deep model is cross-checked against the real A-reference callee:
`as_mapping(abstract(da))` must equal `abstract(da.to_dataset())`.

INPUT DOMAIN — the branch-relevant part of the modeled space is enumerated
exhaustively, then fuzzed to the count. The systematic grid crosses: receiver
size 0..3 variables x argument shape (named DataArray / Dataset with 0..3
variables) x name choice (disjoint from the receiver / colliding with a receiver
name) x value relation (equal to the colliding variable / different, i.e. the
merge-conflict regime, which is inside the model's `Requires` — the model
constrains nothing about name disjointness) — plus the exact F2P shape
(`xr.Dataset({"a": 0}).merge(xr.DataArray(data=1, name="b"))`), the empty
receiver, the empty-Dataset argument, and a multi-variable argument (the
lossy-rebuild witness). Both impl branches and both postcondition arms are taken
many times. Seeded fuzz over the same space then fills the count.
>= 1e5 Requires-satisfying inputs; pinned seed 3677 (mapping.md §G-CONF).

Exit 0 iff zero disagreements; a disagreement prints the input and both sides and
exits 1. Last stdout line is a JSON report. stdlib + xarray only.
"""
import json
import random
import sys

import xarray as xr
import xarray.core.dataset as _dataset_mod

SEED = 3677
N_FUZZ = 100_000

# name <-> code bijection (mapping.md §2: variable NAME (Hashable) <-> int code;
# the F2P test's name="b" is code 1).
_NAME_BY_CODE = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "x", 6: "y", 7: "z"}
_CODE_BY_NAME = {v: k for k, v in _NAME_BY_CODE.items()}
NO_NAME = -1          # model.py: name == -1 means unnamed
NO_VALUE = 0          # abstraction sentinel for an operand with no entry


# ============================================================================
# SHADOW — model.py, verbatim, contract calls stripped
# ============================================================================

class NormalisationUndefined(Exception):
    # Signalled when an array-shaped operand has no one-entry mapping-shaped
    # form: its single entry's name is also one of its own axis-label names.
    pass


class Operand:
    # An operand to the combination routine.
    #   is_mapping        : exposes the named-entry interface the core needs
    #   name              : the single entry's name (-1 == unnamed)
    #   value             : the single entry's value
    #   name_is_own_label : `name` is also one of this operand's own axis-label
    #                       names, so it has no one-entry mapping-shaped form
    def __init__(self, is_mapping, name, value, name_is_own_label):
        self.is_mapping = is_mapping  # type: bool
        self.name = name              # type: int
        self.value = value            # type: int
        self.name_is_own_label = name_is_own_label  # type: bool


# --- pure region ------------------------------------------------------------
def is_array_shaped(o):
    # An operand lacks the named-entry interface exactly when it is not
    # mapping-shaped.
    return not o.is_mapping


# --- as_mapping: impl region (deep model of the conversion callee) ----------
def as_mapping(o):
    if o.name_is_own_label:
        raise NormalisationUndefined()
    res = Operand(True, o.name, o.value, False)
    return res


# --- merge_method: impl region ---------------------------------------------
def merge_method(receiver, other):
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result


# ============================================================================
# TYPE BRIDGE (mapping.md §2)
# ============================================================================

def to_operand(obj):
    """Concrete merge operand -> abstract Operand.

    is_mapping is read off the REAL named-entry interface (`.items()`), which is
    what `coerce_pandas_values` requires of every operand; name/value abstract
    the single (first) data variable through the name<->code bijection.
    """
    is_mapping = hasattr(obj, "items")
    if is_mapping:
        items = list(obj.data_vars.items())
        if not items:
            return Operand(True, NO_NAME, NO_VALUE, False)
        key, var = items[0]
        return Operand(True, _CODE_BY_NAME.get(key, NO_NAME), int(var.values),
                       False)
    name = obj.name
    # name_is_own_label is read off the REAL object: the entry's own name is also
    # one of the axis-label names the operand itself carries.
    return Operand(False,
                   NO_NAME if name is None else _CODE_BY_NAME.get(name, NO_NAME),
                   int(obj.values[()]) if obj.ndim == 0 else int(obj.values[0]),
                   name is not None and name in obj.coords)


def make_receiver(codes_values):
    """Abstract -> concrete: the mapping-shaped receiver Dataset."""
    return xr.Dataset({_NAME_BY_CODE[c]: v for c, v in codes_values})


def make_array_operand(code, value, own_label=False):
    """Abstract -> concrete: a NAMED array-shaped operand (code >= 0).

    own_label=True builds the operand class on which the normalisation is
    UNDEFINED: the entry name is also one of the operand's own axis-label names
    (name_is_own_label). This class satisfies merge_method's Requires (it is a
    NAMED array-shaped operand), so it is inside the modeled domain and must be
    generated, not skipped.
    """
    name = _NAME_BY_CODE[code]
    if own_label:
        return xr.DataArray(data=value, name=name, coords={name: value})
    return xr.DataArray(data=value, name=name)


def make_mapping_operand(codes_values):
    """Abstract -> concrete: a mapping-shaped operand Dataset."""
    return xr.Dataset({_NAME_BY_CODE[c]: v for c, v in codes_values})


def fields(op):
    return (bool(op.is_mapping), int(op.name), int(op.value),
            bool(op.name_is_own_label))


# ============================================================================
# ORACLE — the real patched Dataset.merge, with the operand pair it hands to
# the core combination routine recorded by a spy over the real callee.
# ============================================================================

_captured = []
_real_dataset_merge_method = _dataset_mod.dataset_merge_method


def _spy(dataset, other, *args, **kwargs):
    _captured.append((dataset, other))
    return _real_dataset_merge_method(dataset, other, *args, **kwargs)


def _install_spy():
    _dataset_mod.dataset_merge_method = _spy


def _assert_oracle_is_patched():
    """Refuse to certify anything against unpatched source."""
    import inspect
    src = inspect.getsource(_dataset_mod.Dataset.merge)
    if "to_dataset()" not in src or "isinstance" not in src:
        print("G-CONF ERROR: oracle Dataset.merge is NOT the patched function "
              "(no operand normalisation found in its source); refusing to run.")
        sys.exit(2)
    # the pre-patch behaviour must really be gone: an unconverted array-shaped
    # operand used to reach coerce_pandas_values and raise AttributeError.
    probe = xr.Dataset({"a": 0}).merge(xr.DataArray(data=1, name="b"))
    if sorted(str(k) for k in probe.data_vars) != ["a", "b"]:
        print("G-CONF ERROR: patched merge produced %r, expected vars a,b"
              % (sorted(str(k) for k in probe.data_vars),))
        sys.exit(2)


def oracle(receiver_obj, other_obj):
    """Run the REAL patched Dataset.merge; return the operand pair it built,
    plus how the full merge ended (informational)."""
    del _captured[:]
    outcome = "ok"
    try:
        receiver_obj.merge(other_obj)
    except Exception as exc:                     # noqa: BLE001 - informational
        outcome = type(exc).__name__
    if len(_captured) != 1:
        return None, outcome
    return _captured[0], outcome


# ============================================================================
# DIFFERENTIAL COMPARISON
# ============================================================================

def check_one(receiver_obj, other_obj):
    """Diff the shadow against the real patched function on one input.
    Returns None on agreement, else an explanatory string."""
    receiver_abs = to_operand(receiver_obj)
    other_abs = to_operand(other_obj)

    # The modeled operation is PARTIAL: on an array-shaped operand whose entry
    # name is also one of its own axis-label names there is no one-entry
    # mapping-shaped form, so the shadow signals instead of returning a
    # sequence. Record which outcome the shadow took.
    shadow = None
    shadow_undefined = False
    try:
        shadow = merge_method(receiver_abs, other_abs)
    except NormalisationUndefined:
        shadow_undefined = True
    real_pair, outcome = oracle(receiver_obj, other_obj)

    def describe(extra):
        return ("DISAGREEMENT\n"
                "  receiver = %r\n"
                "  other    = %r\n"
                "  shadow   = %s\n"
                "  real     = %s (merge outcome: %s)\n"
                "  %s"
                % (receiver_obj, other_obj,
                   "NormalisationUndefined (no sequence produced)"
                   if shadow_undefined else
                   ("len=%d ops=%r  ids=(receiver:%s, other:%s)"
                    % (len(shadow), [fields(o) for o in shadow],
                       shadow[0] is receiver_abs, shadow[1] is other_abs)),
                   ("len=2 ops=%r ids=(receiver:%s, other:%s)"
                    % ([fields(to_operand(o)) for o in real_pair],
                       real_pair[0] is receiver_obj,
                       real_pair[1] is other_obj)) if real_pair else "NO OPERANDS",
                   outcome,
                   extra))

    # BOTH OUTCOMES ARE DIFFED. The real operation produced an operand pair iff
    # the shadow returned one: an over-claimed no-raise model (shadow returns,
    # real raises) and an over-broad raise (shadow raises, real returns) are both
    # disagreements. The real side "produced no sequence" is exactly real_pair is
    # None -- the core combination routine was never reached.
    if shadow_undefined:
        if real_pair is not None:
            return describe("the shadow signalled that no one-entry "
                            "mapping-shaped form exists, but the real merge DID "
                            "build an operand sequence and reached the core")
        # Agreement on the undefined outcome. Confirm the real conversion is
        # undefined for the same reason the model says it is -- the entry name
        # colliding with one of the operand's own axis-label names -- rather than
        # for some unrelated reason the model does not represent.
        if not is_array_shaped(other_abs):
            return describe("the shadow signalled on a mapping-shaped operand; "
                            "only array-shaped operands can be undefined")
        try:
            other_obj.to_dataset()
        except Exception as exc:                 # noqa: BLE001 - expected
            if type(exc).__name__ != "ValueError":
                return describe("the real conversion failed with %s, not the "
                                "ValueError the model represents"
                                % type(exc).__name__)
            return None
        return describe("the shadow signalled that no one-entry mapping-shaped "
                        "form exists, but the real conversion produced one")
    if real_pair is None:
        return describe("the real patched merge never reached the core "
                        "combination routine, so no operand sequence was built; "
                        "the model claims a 2-operand sequence")
    if len(shadow) != 2:
        return describe("shadow produced %d operands, not 2" % len(shadow))

    # Result()[0] is receiver -- the receiver passes through as the same object
    if not (shadow[0] is receiver_abs) == (real_pair[0] is receiver_obj):
        return describe("receiver pass-through identity differs")
    if real_pair[0] is not receiver_obj:
        return describe("real operand 0 is not the receiver object")

    # field-by-field: is_mapping (both operands), and name/value of operand 1
    for i in (0, 1):
        if fields(shadow[i]) != fields(to_operand(real_pair[i])):
            return describe("operand %d differs: shadow %r vs real %r"
                            % (i, fields(shadow[i]),
                               fields(to_operand(real_pair[i]))))

    # EVERY operand reaching the core exposes the named-entry interface
    for i in (0, 1):
        if not hasattr(real_pair[i], "items"):
            return describe("real operand %d lacks the .items() named-entry "
                            "interface (the pre-patch failure mode)" % i)

    # Result()[1].name/.value == other.name/.value (the argument's single value)
    if (shadow[1].name, shadow[1].value) != (other_abs.name, other_abs.value):
        return describe("shadow lost the argument's single named value")
    real_second = to_operand(real_pair[1])
    if (real_second.name, real_second.value) != (other_abs.name, other_abs.value):
        return describe("real second operand carries %r, argument carried %r"
                        % ((real_second.name, real_second.value),
                           (other_abs.name, other_abs.value)))

    # Implies(not is_array_shaped(other), Result()[1] is other)
    if not is_array_shaped(other_abs):
        if not (shadow[1] is other_abs) == (real_pair[1] is other_obj):
            return describe("mapping-shaped pass-through identity differs "
                            "(shadow %s, real %s)"
                            % (shadow[1] is other_abs, real_pair[1] is other_obj))
        if real_pair[1] is not other_obj:
            return describe("a mapping-shaped argument was REBUILT rather than "
                            "passed through (lossy-rebuild hole, refinement.md B)")
    else:
        # array-shaped arm: cross-check the deep model against the REAL
        # A-reference callee it models (DataArray.to_dataset()).
        # (reached only when the shadow returned, i.e. the normalisation is
        # defined for this operand; the undefined class was handled above)
        real_converted = to_operand(other_obj.to_dataset())
        if fields(as_mapping(other_abs)) != fields(real_converted):
            return describe("deep model as_mapping %r != real to_dataset() %r"
                            % (fields(as_mapping(other_abs)),
                               fields(real_converted)))
        # and the real merge must not have hit the missing-.items() symptom
        if outcome == "AttributeError":
            return describe("the real patched merge raised AttributeError "
                            "(the unconverted-operand symptom)")
    return None


# ============================================================================
# INPUT GENERATION
# ============================================================================

def systematic_inputs():
    """Exhaustive grid over the branch-relevant structure of the modeled space
    (receiver size x argument shape x name collision x value relation), plus the
    F2P shape and the empty/multi boundaries. Every yielded input satisfies
    merge_method's Requires: the receiver is a Dataset (mapping-shaped), the two
    operands are distinct objects, and every array-shaped argument is named."""
    # the exact F2P case first
    yield (make_receiver([(0, 0)]), make_array_operand(1, 1))

    all_codes = sorted(_NAME_BY_CODE)
    for r_size in (0, 1, 2, 3):
        recv_codes = all_codes[:r_size]
        recv_vals = [(c, 10 + c) for c in recv_codes]
        free = [c for c in all_codes if c not in recv_codes]

        # --- array-shaped argument (both name regimes, both value relations)
        cand = []
        if free:
            cand.append((free[0], 7))                              # disjoint name
        if recv_codes:
            cand.append((recv_codes[0], 10 + recv_codes[0]))       # collide, equal
            cand.append((recv_codes[0], 999))                      # collide, differ
        for code, val in cand:
            yield (make_receiver(recv_vals), make_array_operand(code, val))
            # the SAME abstract operand but with its entry name also one of its
            # own axis-label names: the class on which the normalisation is
            # undefined. Inside the Requires (still a NAMED array-shaped
            # operand), so it must be exercised.
            yield (make_receiver(recv_vals),
                   make_array_operand(code, val, own_label=True))

        # --- mapping-shaped argument, 0..3 variables, same three name regimes
        for o_size in (0, 1, 2, 3):
            if o_size == 0:
                yield (make_receiver(recv_vals), make_mapping_operand([]))
                continue
            if len(free) >= o_size:
                yield (make_receiver(recv_vals),
                       make_mapping_operand([(c, 20 + c) for c in free[:o_size]]))
            if recv_codes:
                # collide on the first name, equal value then differing value
                tail = [c for c in free[:o_size - 1]]
                yield (make_receiver(recv_vals),
                       make_mapping_operand([(recv_codes[0], 10 + recv_codes[0])]
                                            + [(c, 20 + c) for c in tail]))
                yield (make_receiver(recv_vals),
                       make_mapping_operand([(recv_codes[0], 999)]
                                            + [(c, 20 + c) for c in tail]))

    # extra boundaries: empty receiver with each argument shape; extreme values
    yield (make_receiver([]), make_array_operand(1, 0))
    yield (make_receiver([]), make_mapping_operand([]))
    yield (make_receiver([(0, 0)]), make_array_operand(1, -(2 ** 31)))
    yield (make_receiver([(0, 0)]), make_array_operand(1, 2 ** 31))
    yield (make_receiver([(0, 0)]),
           make_mapping_operand([(1, 1), (2, 2), (3, 3)]))   # multi-var argument
    # the F2P shape's undefined-normalisation counterpart (the exact witness:
    # name "b" carrying an axis-label "b"), and it with an empty receiver
    yield (make_receiver([(0, 0)]), make_array_operand(1, 1, own_label=True))
    yield (make_receiver([]), make_array_operand(1, 1, own_label=True))


def fuzz_inputs(n, rng):
    all_codes = sorted(_NAME_BY_CODE)
    for _ in range(n):
        r_size = rng.randint(0, 3)
        recv_codes = rng.sample(all_codes, r_size)
        recv_vals = [(c, rng.randint(-1000, 1000)) for c in recv_codes]
        receiver = make_receiver(recv_vals)
        if rng.random() < 0.5:
            # array-shaped argument: always NAMED (inside the Requires)
            code = rng.choice(all_codes)
            # sample BOTH the defined and the undefined normalisation classes
            yield (receiver, make_array_operand(code, rng.randint(-1000, 1000),
                                                own_label=rng.random() < 0.5))
        else:
            o_size = rng.randint(0, 3)
            o_codes = rng.sample(all_codes, o_size)
            yield (receiver,
                   make_mapping_operand([(c, rng.randint(-1000, 1000))
                                         for c in o_codes]))


# ============================================================================
# DRIVER
# ============================================================================

def main():
    _assert_oracle_is_patched()
    _install_spy()

    checked = 0
    branch_array = 0
    branch_mapping = 0
    branch_undefined = 0
    n_systematic = 0

    rng = random.Random(SEED)
    for phase, source in (("systematic", systematic_inputs()),
                          ("fuzz", fuzz_inputs(N_FUZZ, rng))):
        for receiver_obj, other_obj in source:
            err = check_one(receiver_obj, other_obj)
            if err is not None:
                print("G-CONF FAIL (%s input #%d): %s" % (phase, checked + 1, err))
                return 1
            checked += 1
            if phase == "systematic":
                n_systematic += 1
            if isinstance(other_obj, xr.DataArray):
                branch_array += 1
                if other_obj.name is not None and other_obj.name in other_obj.coords:
                    branch_undefined += 1
            else:
                branch_mapping += 1

    if branch_array == 0 or branch_mapping == 0 or branch_undefined == 0:
        print("G-CONF FAIL: an impl branch or outcome was never exercised "
              "(array-shaped=%d, mapping-shaped=%d, undefined-normalisation=%d)"
              % (branch_array, branch_mapping, branch_undefined))
        return 1

    print("G-CONF OK: shadow (model.py impl region, verbatim) == real patched "
          "Dataset.merge operand construction on %d inputs "
          "(%d systematic + %d fuzz, seed %d); array-shaped branch %d, "
          "mapping-shaped branch %d, undefined-normalisation outcome %d; "
          "0 disagreements."
          % (checked, n_systematic, N_FUZZ, SEED, branch_array, branch_mapping,
             branch_undefined))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "systematic": n_systematic, "fuzz": N_FUZZ,
                      "branch_array_shaped": branch_array,
                      "branch_mapping_shaped": branch_mapping,
                      "branch_undefined_normalisation": branch_undefined,
                      "oracle": "xarray.core.dataset.Dataset.merge (patched), "
                                "called; operand pair recorded at the real "
                                "dataset_merge_method callee",
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
