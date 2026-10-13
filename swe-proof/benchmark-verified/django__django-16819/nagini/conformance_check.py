#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16819 (nagini).

SHADOW  — the impl region of model.py copied VERBATIM with the contract
          statement lines (Requires/Ensures) stripped; the model IS Python,
          so no transliteration.  The @Pure helpers (`names_equal`,
          `base_combine`) and the `Operand` carrier class copy over as plain
          Python; Nagini's `ToSeq` becomes a plain tuple shim.  The shadow
          works over the model's carrier types: an index name as a List[int]
          of Unicode code points, the counterpart as an Operand with three
          facets (is_remove_index / name / elidable), and the outcome as the
          4-tag integer encoding.

BRIDGE  — mapping.md §2's type abstraction, applied in both directions:
          * name List[int] <-> str: a Python str IS a sequence of code
            points, so "".join(chr(c)) / [ord(ch)] is a bijection and
            sequence equality of code points is exactly str equality.
          * operation.is_remove_index <-> the runtime class of the real
            counterpart (an index-removal operation vs any other operation).
          * mixed list-or-False return of the real method <-> tags:
            False -> 0, [] -> 1, [counterpart] -> 2, [receiver] -> 3
            (element matched by object identity — the real method returns
            the very same objects).
          * the counterpart's second positional argument of the real method
            (the application label) is never read on this code path
            (mapping.md §3) and is passed as a fixed dummy.
          * the model leaves the receiver's name and elidable flag free even
            where the real constructor restricts them (a name must be
            non-empty at construction; elidable is a class default), so the
            receiver is built once through the real constructor and the two
            free facets are then assigned per-case — the method under test
            only ever READS them.

ORACLE  — the REAL patched repo function (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs):
          `django.db.migrations.operations.models.AddIndex.reduce`, invoked
          on a genuine AddIndex receiver against genuine counterpart
          operations (a real RemoveIndex when is_remove_index, otherwise a
          real base Operation / a second AddIndex — two distinct
          non-removal classes, exercised alternately).

Exit 0 iff zero disagreements over the boundary grid + >=1e5 fuzzed
Requires-satisfying inputs.  Pinned seed: 16819.  stdlib + the repo under
test (django) only.
"""
import random
import sys

SEED = 16819
N_FUZZ = 110_000


# ---------------------------------------------------------------------------
# Nagini shims: ToSeq is sequence snapshot/equality — a plain tuple.
# ---------------------------------------------------------------------------

def ToSeq(x):
    return tuple(x)


# ---------------------------------------------------------------------------
# model.py carrier class, VERBATIM with Ensures lines stripped.
# ---------------------------------------------------------------------------

class Operand:
    """A counterpart operation considered for combination. Only the touched
    facets are modelled: whether it removes an index, the name it carries
    (consulted only when it is an index-removal), and its elidable flag."""

    def __init__(self, is_remove_index, name, elidable):
        self.is_remove_index = is_remove_index
        self.name = name
        self.elidable = elidable


# ---------------------------------------------------------------------------
# model.py pure region, copied as plain functions (@Pure/Requires stripped).
# ---------------------------------------------------------------------------

def names_equal(a, b):
    """Whether two index names denote the same string."""
    return ToSeq(a) == ToSeq(b)


def base_combine(self_elidable, op_elidable):
    """The generic combination rule shared by every operation: a self-elidable
    operation is replaced by the counterpart alone (2); otherwise an elidable
    counterpart replaces the operation by the operation alone (3); otherwise the
    operations cannot be combined (0)."""
    if self_elidable:
        return 2
    if op_elidable:
        return 3
    return 0


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM (contract statement lines stripped).
# ---------------------------------------------------------------------------

def reduce_add_index(index_name, self_elidable, operation):
    if operation.is_remove_index and names_equal(index_name, operation.name):
        return 1
    if self_elidable:
        return 2
    if operation.elidable:
        return 3
    return 0


# ---------------------------------------------------------------------------
# Bridges.
# ---------------------------------------------------------------------------

def cps_to_str(cps):
    """List[int] of code points -> str (bijective; mapping.md §2)."""
    return "".join(chr(c) for c in cps)


def str_to_cps(s):
    return [ord(ch) for ch in s]


def tag_of(result, receiver, counterpart):
    """Real mixed list-or-False return -> the model's 4-tag encoding.
    Anything outside the four documented shapes maps to None (a guaranteed
    disagreement, surfaced with the raw value)."""
    if result is False:
        return 0
    if isinstance(result, list):
        if len(result) == 0:
            return 1
        if len(result) == 1 and result[0] is counterpart:
            return 2
        if len(result) == 1 and result[0] is receiver:
            return 3
    return None


# ---------------------------------------------------------------------------
# Oracle: the genuine patched AddIndex.reduce on genuine operation objects.
# ---------------------------------------------------------------------------

def make_oracle():
    # Configure minimal settings defensively; the code path under test is
    # pure control flow over operation attributes and needs no database.
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure()
    except Exception:
        pass

    from django.db import models as db_models
    from django.db.migrations.operations.models import AddIndex, RemoveIndex
    from django.db.migrations.operations.base import Operation

    # One genuine receiver, built through the real constructor (which demands
    # a non-empty index name); the two facets the model leaves free
    # (index.name, elidable) are assigned per-case below — the method under
    # test only reads them.
    receiver = AddIndex(
        "Pony", db_models.Index(fields=["weight"], name="placeholder_name"))

    # Genuine counterparts: one index-removal, two non-removal classes
    # (the base operation class and a second add-index operation) so the
    # runtime type test is exercised against more than one negative class.
    remove_op = RemoveIndex("Pony", "placeholder_name")
    plain_op = Operation()
    other_add = AddIndex(
        "Pony", db_models.Index(fields=["pink"], name="placeholder_name"))

    def oracle(index_name_str, self_elidable, op_is_remove, op_name_str,
               op_elidable, alt):
        receiver.index.name = index_name_str
        receiver.elidable = self_elidable
        if op_is_remove:
            counterpart = remove_op
            counterpart.name = op_name_str
        else:
            counterpart = plain_op if alt == 0 else other_add
            # a non-removal counterpart may carry any name; the real code
            # path must never consult it (short-circuit), mirrored here by
            # assigning it anyway
            counterpart.name = op_name_str
        counterpart.elidable = op_elidable
        result = receiver.reduce(counterpart, "someapp")
        return tag_of(result, receiver, counterpart), result

    return oracle


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying (any code-point lists, any booleans).
# ---------------------------------------------------------------------------

NAME_POOL = [
    "",                             # empty (free in the model)
    "a",
    "idx",
    "idx_pony_weight_pink",
    "idx_pony_weight_pink ",        # trailing-space near-miss
    "IDX_PONY_WEIGHT_PINK",         # case near-miss
    "idx_pony_weight_pin",          # prefix near-miss
    "idx_pony_weight_pinkk",        # extension near-miss
    "other_name",
    "näme_ünicode",       # non-ASCII BMP
    "\U0001F40E_index",             # astral-plane code point
    "x" * 100,                      # long
]


def rand_name(rng):
    if rng.random() < 0.5:
        return rng.choice(NAME_POOL)
    n = rng.randint(0, 12)
    return "".join(
        chr(rng.choice((rng.randint(97, 122), rng.randint(0x20, 0x2FFF))))
        for _ in range(n))


def main():
    oracle = make_oracle()
    rng = random.Random(SEED)
    checked = 0
    disagreements = []

    def check(index_name_str, self_el, op_is_rm, op_name_str, op_el, alt, tag):
        nonlocal checked
        checked += 1
        cps = str_to_cps(index_name_str)
        operand = Operand(op_is_rm, str_to_cps(op_name_str), op_el)
        # round-trip sanity of the code-point bridge (bijectivity)
        assert cps_to_str(cps) == index_name_str
        shadow = reduce_add_index(cps, self_el, operand)
        real_tag, raw = oracle(index_name_str, self_el, op_is_rm,
                               op_name_str, op_el, alt)
        if shadow != real_tag:
            disagreements.append(
                (tag, index_name_str, self_el, op_is_rm, op_name_str, op_el,
                 alt, shadow, real_tag, raw))
        return len(disagreements) < 5

    # boundary grid: every pool name pair x all boolean combinations x both
    # non-removal counterpart classes
    done = False
    for idx_name in NAME_POOL:
        for op_name in NAME_POOL:
            for op_is_rm in (False, True):
                for se in (False, True):
                    for oe in (False, True):
                        for alt in ((0,) if op_is_rm else (0, 1)):
                            if not check(idx_name, se, op_is_rm, op_name,
                                         oe, alt, "boundary"):
                                done = True
                                break
                        if done:
                            break
                    if done:
                        break
                if done:
                    break
            if done:
                break
        if done:
            break

    # fuzz
    if not disagreements:
        for i in range(N_FUZZ):
            idx_name = rand_name(rng)
            # bias toward equal names so the discriminating branch is hot
            op_name = idx_name if rng.random() < 0.4 else rand_name(rng)
            op_is_rm = rng.random() < 0.5
            se = rng.random() < 0.5
            oe = rng.random() < 0.5
            alt = i % 2
            if not check(idx_name, se, op_is_rm, op_name, oe, alt, "fuzz"):
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for (tag, idx_name, se, op_is_rm, op_name, oe, alt, sh, rt,
             raw) in disagreements:
            print("  [%s] index_name=%r self_elidable=%r is_remove=%r "
                  "op_name=%r op_elidable=%r alt=%d\n"
                  "    shadow tag=%r\n    real   tag=%r (raw=%r)"
                  % (tag, idx_name, se, op_is_rm, op_name, oe, alt, sh, rt,
                     raw))
        return 1
    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "combination rule on %d inputs (boundary grid + fuzz, seed=%d), "
          "0 disagreements." % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
