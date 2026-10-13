#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6938 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert/MustTerminate) stripped. The model
has no @Pure helpers and no @ContractOnly callees; the one contract-side
construct the impl region touches (`ToSeq`) copies over on a small immutable
PSeq shim.

ORACLE: the REAL patched repo functions the model models per mapping.md
section 1 — `xarray.core.variable.IndexVariable.to_index_variable`
(model `as_coordinate`), `IndexVariable.copy` (model `independent_clone`),
and `Variable.to_base_variable` (model `as_plain`). The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so `import xarray` resolves to the patched module.

Type bridge (mapping.md section 2): the repo carries `dims` as a tuple of
Hashable dimension names; the model carries a `List[int]` of name codes under
any injective name<->int coding. Here code c <-> name "d<c>"; comparison is
done in name space by lifting the shadow's code lists through the same
coding. The model's dims setter maps to the repo's `dims` property setter
(both rebind the receiver's stored dimension-name sequence), so the
observables compared per input are:

    (1) the returned object is / is not the receiver (distinctness);
    (2) the returned object's initial dimension names;
    (3) the receiver's dimension names after the call;
    (4) both objects' dimension names after reassigning the RESULT's dims
        (mutation independence: the receiver must be unaffected).

Storage identity (`Result().dims is not self.dims`) is checked internally on
the shadow only: the repo carries dims as an immutable tuple, so storage
identity is not an observable there — mutation independence (4) is the
observable that clause underpins (mapping.md section 2, refinement.md).

Input domain: the model precondition demands only a readable list of name
codes. The realizable receiver domain is: exactly one dimension name for the
coordinate-variable operations (a 1-D coordinate variable), any finite name
tuple for the plain re-presentation. Generation covers boundary name codes
and data lengths plus randomized fuzz.

>= 1e5 Requires-satisfying inputs: 104 boundary checks + 34000 fuzz
iterations x 3 operation checks each = 102104 differential inputs.
Pinned fuzz seed: 6938 (the instance number; recorded in mapping.md).

Exit 0 iff zero disagreements; on disagreement prints the input and both
observations and exits 1. stdlib only (plus the in-container xarray oracle).
"""
import json
import random
import sys

SEED = 6938
N_FUZZ = 34000  # x3 operation checks per iteration


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq(object):
    __slots__ = ("_t",)

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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

class CoordVar:
    """A one-dimensional coordinate variable. The only field the studied
    behaviour touches is `dims`, the tuple of dimension names (modelled as a
    `List[int]` of name codes)."""

    def __init__(self, dims):
        self.dims = dims  # type: List[int]


def independent_clone(self):
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        new_dims.append(self.dims[i])
        i = i + 1
    res = CoordVar(new_dims)
    return res


def as_coordinate(self):
    return independent_clone(self)


def as_plain(self):
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        base_dims.append(self.dims[j])
        j = j + 1
    return CoordVar(base_dims)


# --- bridge: name code <-> dimension name (injective) ------------------------

def to_name(code):
    return "d%d" % code


def lift(codes):
    """List[int] of name codes -> tuple of dimension names."""
    return tuple(to_name(c) for c in codes)


# --- observation harnesses ----------------------------------------------------

OBS_KEYS = ("distinct", "result_dims", "receiver_dims_after_call",
            "result_dims_after_mut", "receiver_dims_after_mut")


def shadow_observe(op, codes, mut_codes):
    """Run a shadow operation and record the four bridged observables (in
    name space). Also returns the shadow-internal storage-independence bit."""
    cv = CoordVar(list(codes))
    res = op(cv)
    obs = {
        "distinct": res is not cv,
        "result_dims": lift(res.dims),
        "receiver_dims_after_call": lift(cv.dims),
    }
    storage_independent = res.dims is not cv.dims
    # the modelled dims setter: rebinding the stored name sequence
    res.dims = list(mut_codes)
    obs["result_dims_after_mut"] = lift(res.dims)
    obs["receiver_dims_after_mut"] = lift(cv.dims)
    return obs, storage_independent


def real_observe(recv, call, mut_codes):
    """Run the real repo re-presentation and record the same observables."""
    res = call(recv)
    obs = {
        "distinct": res is not recv,
        "result_dims": tuple(res.dims),
        "receiver_dims_after_call": tuple(recv.dims),
    }
    # the real dims property setter: rebinding the stored name tuple
    res.dims = lift(mut_codes)
    obs["result_dims_after_mut"] = tuple(res.dims)
    obs["receiver_dims_after_mut"] = tuple(recv.dims)
    return obs


def compare(op_name, codes, data_repr, s_obs, r_obs, storage_independent):
    if not storage_independent:
        return ("INTERNAL: shadow %s did not allocate fresh dims storage "
                "on input codes %r" % (op_name, codes))
    if s_obs != r_obs:
        lines = ["DISAGREEMENT on %s, input dims codes %r (names %r), "
                 "data %s:" % (op_name, codes, lift(codes), data_repr)]
        for k in OBS_KEYS:
            lines.append("  %-24s shadow=%r  real=%r"
                         % (k + ":", s_obs[k], r_obs[k]))
        return "\n".join(lines)
    return None


# --- differential driver --------------------------------------------------------

def unit_data(ndim):
    """A nested-list payload of shape (1,)*ndim for a plain Variable."""
    d = 0.0
    for _ in range(ndim):
        d = [d]
    return d


def make_checks(IndexVariable, Variable):
    def check_coord(codes, data):
        """as_coordinate  vs  IndexVariable.to_index_variable (1-D receiver)."""
        mut = [c + 10000000 for c in codes]
        s_obs, sind = shadow_observe(as_coordinate, codes, mut)
        iv = IndexVariable(lift(codes), data)
        r_obs = real_observe(iv, lambda r: r.to_index_variable(), mut)
        return compare("as_coordinate/IndexVariable.to_index_variable",
                       codes, "len %d" % len(data), s_obs, r_obs, sind)

    def check_clone(codes, data):
        """independent_clone  vs  IndexVariable.copy (1-D receiver)."""
        mut = [c + 10000000 for c in codes]
        s_obs, sind = shadow_observe(independent_clone, codes, mut)
        iv = IndexVariable(lift(codes), data)
        r_obs = real_observe(iv, lambda r: r.copy(), mut)
        return compare("independent_clone/IndexVariable.copy",
                       codes, "len %d" % len(data), s_obs, r_obs, sind)

    def check_plain(codes):
        """as_plain  vs  Variable.to_base_variable (n-D receiver)."""
        mut = [c + 10000000 for c in codes]
        s_obs, sind = shadow_observe(as_plain, codes, mut)
        v = Variable(lift(codes), unit_data(len(codes)))
        r_obs = real_observe(v, lambda r: r.to_base_variable(), mut)
        return compare("as_plain/Variable.to_base_variable",
                       codes, "shape %r" % ((1,) * len(codes),),
                       s_obs, r_obs, sind)

    return check_coord, check_clone, check_plain


def main():
    from xarray import IndexVariable, Variable  # the patched module
    check_coord, check_clone, check_plain = make_checks(IndexVariable, Variable)

    checked = 0

    # --- boundary: name-code extremes x data lengths/dtypes (1-D receivers) --
    boundary_codes = (0, 1, -1, 7, 120, 999999, -424242)
    boundary_data = ([], [0], list(range(2)), list(range(100)),
                     ["a"], ["a", "b", "c"], [1.5, 2.5])
    n_boundary = 0
    for code in boundary_codes:
        for data in boundary_data:
            for chk in (check_coord, check_clone):
                err = chk([code], list(data))
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1

    # --- boundary: plain re-presentation over 0..4 dimension names ----------
    for codes in ([], [5], [3, 4], [10, 20, 30], [0, 1, 2, 3], [-1, 999999]):
        err = check_plain(codes)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # --- randomized fuzz (pinned seed) ---------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        code = rng.randint(-10 ** 6, 10 ** 6)
        n = rng.randint(0, 8)
        data = list(range(n))
        for chk in (check_coord, check_clone):
            err = chk([code], list(data))
            if err:
                print(err)
                return 1
            checked += 1
        ndim = rng.randint(0, 4)
        codes = rng.sample(range(0, 2 * 10 ** 6), ndim)
        err = check_plain(codes)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched re-presentations "
          "(IndexVariable.to_index_variable / IndexVariable.copy / "
          "Variable.to_base_variable) on %d inputs (%d boundary + %d fuzz "
          "iterations x 3, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
