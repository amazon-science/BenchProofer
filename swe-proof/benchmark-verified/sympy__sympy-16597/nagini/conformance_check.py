#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16597 (nagini).

SHADOW: the impl regions of model.py (`deduce_even` / `deduce_infinite`),
copied VERBATIM below with the contract calls stripped (the `Ensures` blocks
live outside the impl regions; the impl bodies carry no contract calls, so
they copy over unchanged). The `KB` record class copies over with its
`Ensures` lines removed, and the @Pure helper `consistent_theory` copies over
as a plain function with its `Requires` lines removed and `Implies` realized
as a plain boolean helper. All carriers are plain Optional[bool] fields; no
PSeq shim is needed and there are no @ContractOnly callees.

ORACLE: the REAL patched repo behaviour the model models per mapping.md --
the fact-deduction engine's closure of a seed assumption set, observed
through the three-valued `is_<fact>` properties of a real object built from
that seed. The gate applies patch.diff to /testbed before this script runs
(PYTHONPATH=/testbed; this script never applies any diff itself).

Type bridge (mapping.md section 2): identity on the trit values -- the
object's `is_<fact>` property (True / False / None) maps to the KB field of
the same name, field for field over the 14 carried facts.

Input domain mirrors the preconditions exactly: both modeled functions are
NULLARY (empty pre-conditions region, no parameters), so each has a
single abstract input -- its fixed seed. The >=1e5 budget therefore goes
into independent concrete REALIZATIONS of each seed, every one an
observation of the real engine that must reproduce the shadow's full
14-field record:
  * fresh symbolic carriers (Symbol / Dummy, randomized fresh names) built
    from the seed assumption set -- `even=True` for the first deducer,
    `infinite=True, real=True` (an unbounded real quantity) for the second;
  * the numeric singleton witnesses of the unbounded-real seed (the
    positive and negative unbounded quantities);
  * a randomized read order over the 14 properties on every realization
    (property reads drive the lazy deduction, so order permutes the
    engine-internal deduction path), plus a second read of each property to
    confirm the deduced value is stable.

>= 1e5 Requires-satisfying inputs: boundary battery + 50000 fuzz rounds x 2
seeds = 100000+ fuzz observations. Pinned fuzz seed: 16597.

Exit 0 iff zero disagreements; on disagreement prints the input (seed +
realization + read order) and both records and exits 1. stdlib + the repo
under test only (plain random; hypothesis not needed).
"""
import json
import random
import sys
from typing import Optional

SEED = 16597
N_FUZZ_ROUNDS = 50_000   # x2 seeds = 100000 fuzz observations

# the 14 carried facts, in KB field order (must match model.py KB fields)
PROPS = [
    "integer", "rational", "real", "finite", "even", "odd",
    "algebraic", "transcendental", "irrational", "infinite",
    "complex", "noninteger", "prime", "composite",
]


# --- contract shims -----------------------------------------------------------

def Implies(a, b):
    return (not a) or b


# --- KB record from model.py, Ensures lines stripped ---------------------------

class KB:
    """Three-valued status of each relevant numeric property.

    Each field is True (the property holds), False (it does not), or None
    (unknown). Only the properties touched by the witnessed queries are carried.
    """

    def __init__(self) -> None:
        self.integer = None        # type: Optional[bool]
        self.rational = None       # type: Optional[bool]
        self.real = None           # type: Optional[bool]
        self.finite = None         # type: Optional[bool]
        self.even = None           # type: Optional[bool]
        self.odd = None            # type: Optional[bool]
        self.algebraic = None      # type: Optional[bool]
        self.transcendental = None  # type: Optional[bool]
        self.irrational = None     # type: Optional[bool]
        self.infinite = None       # type: Optional[bool]
        self.complex = None        # type: Optional[bool]
        self.noninteger = None     # type: Optional[bool]
        self.prime = None          # type: Optional[bool]
        self.composite = None      # type: Optional[bool]


# --- pure helper from model.py, Requires lines stripped ------------------------

def consistent_theory(k):
    """The record is closed under the intended set-containment relations."""
    return (
        # integer -> rational ; !rational -> !integer
        Implies(k.integer is True, k.rational is True)
        and Implies(k.rational is False, k.integer is False)
        # rational -> real ; rational -> algebraic ; rational -> finite
        and Implies(k.rational is True, k.real is True)
        and Implies(k.rational is True, k.algebraic is True)
        and Implies(k.rational is True, k.finite is True)
        # real -> complex (a real quantity is complex)
        and Implies(k.real is True, k.complex is True)
        # algebraic -> complex ; algebraic -> finite
        and Implies(k.algebraic is True, k.complex is True)
        and Implies(k.algebraic is True, k.finite is True)
        # even -> integer ; odd -> integer ; !integer -> !even ; !integer -> !odd
        and Implies(k.even is True, k.integer is True)
        and Implies(k.odd is True, k.integer is True)
        and Implies(k.integer is False, k.even is False)
        and Implies(k.integer is False, k.odd is False)
        # even == integer & !odd : an even quantity is not odd (the !odd direction)
        and Implies(k.even is True, k.odd is False)
        # prime -> integer ; composite -> integer ; !integer -> !prime ; -> !composite
        and Implies(k.prime is True, k.integer is True)
        and Implies(k.composite is True, k.integer is True)
        and Implies(k.integer is False, k.prime is False)
        and Implies(k.integer is False, k.composite is False)
        # irrational -> real ; irrational -> !rational ; irrational -> finite
        and Implies(k.irrational is True, k.real is True)
        and Implies(k.irrational is True, k.rational is False)
        and Implies(k.irrational is True, k.finite is True)
        # transcendental -> complex ; -> !algebraic ; -> finite
        and Implies(k.transcendental is True, k.complex is True)
        and Implies(k.transcendental is True, k.algebraic is False)
        and Implies(k.transcendental is True, k.finite is True)
        # infinite -> !finite
        and Implies(k.infinite is True, k.finite is False)
        # contrapositives of the four boundedness-forcing containments:
        # !finite -> !rational, !algebraic, !irrational, !transcendental
        and Implies(k.finite is False, k.rational is False)
        and Implies(k.finite is False, k.algebraic is False)
        and Implies(k.finite is False, k.irrational is False)
        and Implies(k.finite is False, k.transcendental is False)
        # noninteger == real & !integer : the True direction we witness, plus
        # the reverse-direction exclusion (an integer is NOT a noninteger)
        and Implies(k.real is True and k.integer is False, k.noninteger is True)
        and Implies(k.integer is True, k.noninteger is False)
    )


# --- the impl regions of model.py, verbatim (contracts stripped) ---------------

def deduce_even():
    # impl-start
    k = KB()
    k.even = True
    # even -> integer
    k.integer = True
    # integer -> rational
    k.rational = True
    # rational -> real, algebraic, finite
    k.real = True
    k.algebraic = True
    k.finite = True
    # real / algebraic -> complex
    k.complex = True
    # even -> !odd ; integer -> !noninteger
    k.odd = False
    k.noninteger = False
    # rational -> !irrational ; algebraic -> !transcendental ; finite -> !infinite
    k.irrational = False
    k.transcendental = False
    k.infinite = False
    # prime / composite stay Unknown: parity does not decide primality
    return k
    # impl-end


def deduce_infinite():
    # impl-start
    k = KB()
    k.infinite = True
    k.real = True
    # real -> complex
    k.complex = True
    # infinite -> !finite
    k.finite = False
    # !finite -> !rational, !algebraic, !irrational, !transcendental
    k.rational = False
    k.algebraic = False
    k.irrational = False
    k.transcendental = False
    # !rational -> !integer
    k.integer = False
    # !integer -> !even, !odd, !prime, !composite
    k.even = False
    k.odd = False
    k.prime = False
    k.composite = False
    # real & !integer -> noninteger
    k.noninteger = True
    return k
    # impl-end


# --- shadow records (each deducer is a nullary pure computation) ----------------

def kb_to_dict(k):
    return {p: getattr(k, p) for p in PROPS}


SHADOW_EVEN = kb_to_dict(deduce_even())
SHADOW_INF = kb_to_dict(deduce_infinite())
# sanity: the shadow records satisfy the copied closure predicate
assert consistent_theory(deduce_even())
assert consistent_theory(deduce_infinite())


# --- oracle: the real patched engine's deduced fact table -----------------------

def trit(v):
    assert v is True or v is False or v is None, "unexpected fact value %r" % (v,)
    return v


def read_table(obj, order):
    """Read the 14 relevant is_* properties in the given order (order permutes
    the lazy deduction path), reading each twice to confirm stability."""
    out = {}
    for p in order:
        first = trit(getattr(obj, "is_%s" % p))
        second = trit(getattr(obj, "is_%s" % p))
        if first is not second:
            raise AssertionError(
                "unstable deduced fact is_%s: %r then %r" % (p, first, second))
        out[p] = first
    return out


def check_one(label, shadow, obj, order):
    """Diff the shadow record against the real engine's deduced table for one
    realization; return an error string on disagreement, else None."""
    real = read_table(obj, order)
    if real != shadow:
        diffs = {p: (shadow[p], real[p]) for p in PROPS if shadow[p] is not real[p]}
        return ("DISAGREEMENT\n"
                "  input: %s (read order %s)\n"
                "  shadow=%s\n  real=%s\n  differing fields (shadow, real)=%s"
                % (label, list(order), shadow, real, diffs))
    return None


def main():
    from sympy import Symbol, Dummy, S

    checked = 0
    disagreement = None

    # --- boundary battery -----------------------------------------------------
    # every carrier kind for each seed, plus the numeric singleton witnesses of
    # the unbounded-real seed, each read in field order and reversed field order
    boundary = []
    for order in (tuple(PROPS), tuple(reversed(PROPS))):
        boundary.append(("Symbol(even=True)", SHADOW_EVEN,
                         lambda: Symbol("be", even=True), order))
        boundary.append(("Dummy(even=True)", SHADOW_EVEN,
                         lambda: Dummy(even=True), order))
        boundary.append(("Symbol(infinite=True, real=True)", SHADOW_INF,
                         lambda: Symbol("bi", infinite=True, real=True), order))
        boundary.append(("Dummy(infinite=True, real=True)", SHADOW_INF,
                         lambda: Dummy(infinite=True, real=True), order))
        boundary.append(("positive unbounded singleton", SHADOW_INF,
                         lambda: S.Infinity, order))
        boundary.append(("negative unbounded singleton", SHADOW_INF,
                         lambda: S.NegativeInfinity, order))
    n_boundary = 0
    for label, shadow, make, order in boundary:
        err = check_one(label, shadow, make(), order)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # --- fuzz: fresh realizations x randomized read order ----------------------
    rng = random.Random(SEED)  # pinned seed
    n_fuzz = 0
    for i in range(N_FUZZ_ROUNDS):
        order = PROPS[:]
        rng.shuffle(order)

        # even seed: fresh symbolic carrier (fresh name defeats object caching)
        name = "e%d_%d" % (i, rng.randrange(10 ** 9))
        if rng.random() < 0.5:
            obj = Symbol(name, even=True)
        else:
            obj = Dummy(name, even=True)
        err = check_one("even seed carrier %r" % name, SHADOW_EVEN, obj, order)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

        # unbounded-real seed: fresh symbolic carrier, or a singleton witness
        rng.shuffle(order)
        r = rng.random()
        if r < 0.45:
            name = "i%d_%d" % (i, rng.randrange(10 ** 9))
            obj = Symbol(name, infinite=True, real=True)
            label = "unbounded-real seed carrier %r" % name
        elif r < 0.90:
            name = "j%d_%d" % (i, rng.randrange(10 ** 9))
            obj = Dummy(name, infinite=True, real=True)
            label = "unbounded-real seed carrier %r" % name
        elif r < 0.95:
            obj = S.Infinity
            label = "positive unbounded singleton"
        else:
            obj = S.NegativeInfinity
            label = "negative unbounded singleton"
        err = check_one(label, SHADOW_INF, obj, order)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow impl == real deduced fact table on %d "
          "observations (%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
