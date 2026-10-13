#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14369 (nagini).

SHADOW  — the impl region of `model.py` copied VERBATIM with the contract
          statement lines (Requires/Ensures/Invariant/Assert) stripped; the
          model IS Python, so no transliteration.  The @Pure helper
          `chain_power` copies over as a plain function.  Carrier: a division
          chain is a List[int] of the operands' own intrinsic exponents, one
          per position, plus the bool `leading` (the chain opens with the
          division operator); the result is the List[int] of resulting integer
          exponents, one per operand position.

ORACLE  — the REAL patched repo function (PYTHONPATH=/testbed; the gate
          applies the gold patch before this script runs): astropy's CDS
          unit-format parser, `astropy.units.Unit("<op0>/<op1>/...",
          format="cds")` — the parser whose division-chain reduction the
          model models (mapping.md §1).  The observable is the parsed
          composite unit's integer exponent per base.

BRIDGE  — mapping.md §2's type abstraction.  Model position i, carrying
          intrinsic exponent q(i), is realised as a concrete operand surface
          `<base><q(i)>` (a base name followed by its own exponent, e.g. an
          exponent of 2 on `kpc` is the single operand `kpc2`); `leading`
          prefixes the surface with the division operator.  Every constructed
          surface is CHECKED to parse back to exactly its intended (base,
          exponent), so the bridge is verified, not assumed.  Division of
          units adds exponent vectors with the divisor negated, so for each
          base the parsed unit's power must equal the SUM of the shadow's
          entries over the positions realised with that base.  On chains whose
          bases are all distinct (exercised exhaustively below) each such sum
          is a single position, i.e. the per-position exponent is observed
          directly — no masking.  Executable subdomain: chain lengths 1..12
          with at most 12 distinct bases per chain (the size of the concrete
          base alphabet) and intrinsic exponents in -6..12 (the range whose
          surfaces are verified to round-trip); the model's behaviour is
          uniform in the exponent's value, which the wide range samples.

Inputs: boundary cases + exhaustive distinct-base chains (lengths 1..4, both
leading settings, powered operands) + exhaustive repeated-base chains +
100000 fuzzed Requires-satisfying chains (len(powers) >= 1).  Pinned seed:
14369.
Exit 0 iff zero disagreements; on disagreement print the input and both
outputs and exit 1.  stdlib + astropy (the repo under test) only.
"""
import itertools
import random
import sys
import warnings

warnings.simplefilter("ignore")

SEED = 14369
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# model.py pure region, copied as a plain function (@Pure/Requires stripped).
# ---------------------------------------------------------------------------

def chain_power(i, power, leading):
    if i == 0 and not leading:
        return power
    return -power


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Invariant/Assert) stripped.
# ---------------------------------------------------------------------------

def reduce_division_chain(powers, leading):
    result = []  # type: list
    n = len(powers)
    i = n
    while i > 0:
        old = result  # noqa: F841  (kept: verbatim impl line)
        q = powers[i - 1]
        if i - 1 == 0 and not leading:
            result = [q] + result
        else:
            result = [-q] + result
        i = i - 1
    return result


# ---------------------------------------------------------------------------
# Oracle: the real patched CDS parser.  A chain of (base, intrinsic exponent)
# pairs is rendered to a CDS surface and parsed; the per-base integer powers of
# the parsed composite are the observable.
# ---------------------------------------------------------------------------

BASE_POOL = ["km", "s", "Mpc", "kpc", "m", "g", "J", "W", "pix", "nm", "cm", "K"]
Q_MIN, Q_MAX = -6, 12

_base_cache = {}


def _operand_surface(base_name, q):
    """The CDS surface for ONE operand: the base name, followed by its own
    exponent whenever that exponent is not 1."""
    return base_name if q == 1 else "%s%d" % (base_name, q)


def _check_operand_bridge(u, base_name, q):
    """VERIFY the bridge for one operand: the constructed surface must parse to
    exactly the intended base at exactly the intended exponent (or to nothing
    at all when the exponent is 0). Returns the base object, or raises."""
    key = (base_name, q)
    if key not in _base_cache:
        parsed = u.Unit(_operand_surface(base_name, q), format="cds")
        bases, powers = list(parsed.bases), [int(p) for p in parsed.powers]
        if q == 0:
            if bases:
                raise AssertionError("bridge: %r should be dimensionless, got %r"
                                     % (_operand_surface(base_name, q), bases))
            _base_cache[key] = None
        else:
            if len(bases) != 1 or powers[0] != q:
                raise AssertionError(
                    "bridge: %r parsed to %r^%r, intended exponent %r"
                    % (_operand_surface(base_name, q), bases, powers, q))
            _base_cache[key] = bases[0]
    return _base_cache[key]


def check_chain(u, powers, leading, base_names, disagreements):
    """Diff shadow vs parser on one chain.  `base_names[i]` is the base the
    model position i is realised with (positions may share a base).  Returns
    False once enough disagreements are collected to stop early."""
    n = len(powers)
    # bridge: verify + resolve each position's base object
    bases = [_check_operand_bridge(u, base_names[i], powers[i]) for i in range(n)]
    surface = ("/" if leading else "") + "/".join(
        _operand_surface(base_names[i], powers[i]) for i in range(n))

    parsed = u.Unit(surface, format="cds")
    real = {b: int(p) for b, p in zip(parsed.bases, parsed.powers)}

    shadow = reduce_division_chain(list(powers), leading)
    ok = True
    if len(shadow) != n:
        ok = False
    else:
        # per-base: parser power == SUM of shadow entries over that base's
        # positions (positions whose exponent is 0 contribute no base at all)
        seen = [b for b in dict.fromkeys(bases) if b is not None]
        for b in seen:
            want = sum(shadow[i] for i in range(n) if bases[i] is b)
            got = real.get(b, 0)
            if want != got:
                ok = False
                break
        # nothing the parser reports may come from outside the chain
        if ok:
            for b, p in real.items():
                if b not in seen and p != 0:
                    ok = False
                    break
        # per-position pure-function cross-check on distinct-base chains with
        # no zero exponents (each base occurs once: exponent observed directly)
        if ok and len(seen) == n and all(q != 0 for q in powers):
            for i in range(n):
                got_i = real.get(bases[i], 0)
                if (chain_power(i, powers[i], leading) != got_i
                        or shadow[i] != got_i):
                    ok = False
                    break
    if not ok:
        disagreements.append((list(powers), leading, surface, shadow,
                              {str(b): p for b, p in real.items()}))
    return len(disagreements) < 5


def main():
    import astropy.units as u

    rng = random.Random(SEED)
    disagreements = []
    checked = 0

    def distinct_names(n):
        return BASE_POOL[:n]

    # 1. Boundary cases: single operand, pairs, the issue/F2P chain shapes,
    #    powered operands, leading-operator forms, repeats, zero exponents,
    #    extreme exponents, max-length distinct chain.
    boundary = [
        ([1], False, ["s"]),                       # n == 1: head keeps +1
        ([1], True, ["s"]),                        # opens with the operator
        ([1, 1], False, ["km", "s"]),              # minimal true division
        ([1, 1], True, ["km", "s"]),
        ([1, 1], False, ["s", "s"]),               # divisor shares the dividend's base
        ([1, 1, 1], False, ["km", "s", "Mpc"]),    # the F2P shape
        ([1, 1, 1, 2], False, ["J", "m", "s", "kpc"]),   # the issue's shape
        ([1, 1, 2], False, ["J", "s", "kpc"]),
        ([2, 1], False, ["m", "s"]),               # powered HEAD
        ([1, 2], False, ["km", "s"]),              # powered trailing operand
        ([-2, 1], False, ["kpc", "s"]),            # negative intrinsic exponent
        ([12, 1], False, ["m", "s"]),              # large intrinsic exponent
        ([0, 1], False, ["m", "s"]),               # zero intrinsic exponent
        ([1, 0], False, ["km", "m"]),
        ([1, 1, 1], False, ["s", "s", "s"]),       # all-equal base, odd length
        ([1, 1, 1, 1], False, ["s", "s", "s", "s"]),
        ([1, 1, 1, 1], False, ["km", "s", "km", "s"]),   # alternating repeats
        ([1, 1, 1, 1], False, ["s", "km", "km", "Mpc"]), # repeat not at the head
        ([1] * 12, False, distinct_names(12)),     # longest all-distinct chain
        ([1] * 12, True, distinct_names(12)),
        ([3] * 12, False, ["W"] * 12),             # longest all-equal chain
        ([-6, 12, 1], True, ["km", "s", "Mpc"]),   # extreme exponents, leading
    ]
    for powers, lead, names in boundary:
        checked += 1
        if not check_chain(u, powers, lead, names, disagreements):
            break

    # 2. Exhaustive distinct-base chains, lengths 1..4 over POWERED operands,
    #    both leading settings: every position's exponent observed directly.
    if not disagreements:
        qs = [1, 2, -1, 3]
        for n in range(1, 5):
            names = distinct_names(n)
            for combo in itertools.product(qs, repeat=n):
                for lead in (False, True):
                    checked += 1
                    if not check_chain(u, list(combo), lead, names,
                                       disagreements):
                        break
                if disagreements:
                    break
            if disagreements:
                break

    # 3. Exhaustive repeated-base chains: all length-1..4 chains over a 2-base
    #    alphabet at exponents {1,2} (covers every duplication pattern here).
    if not disagreements:
        pairs = [("s", 1), ("s", 2), ("km", 1)]
        for n in range(1, 5):
            for combo in itertools.product(pairs, repeat=n):
                for lead in (False, True):
                    checked += 1
                    if not check_chain(u, [q for _b, q in combo], lead,
                                       [b for b, _q in combo], disagreements):
                        break
                if disagreements:
                    break
            if disagreements:
                break

    # 4. Fuzz: 100000 Requires-satisfying chains, lengths 1..12, wide-range
    #    intrinsic exponents, at most 12 distinct bases per chain (the
    #    executable subdomain), both leading settings.
    if not disagreements:
        for _ in range(N_FUZZ):
            n = rng.randint(1, 12)
            k = rng.randint(1, min(n, len(BASE_POOL)))
            vocab = BASE_POOL[:k]
            names = [rng.choice(vocab) for _ in range(n)]
            powers = [rng.randint(Q_MIN, Q_MAX) for _ in range(n)]
            lead = rng.random() < 0.5
            checked += 1
            if not check_chain(u, powers, lead, names, disagreements):
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for powers, lead, surface, shadow, real in disagreements:
            print("  powers=%r leading=%r bridged=%r\n"
                  "    shadow(per-position)=%r\n"
                  "    oracle(per-base powers)=%r"
                  % (powers, lead, surface, shadow, real))
        return 1
    print("G-CONF OK: model.py impl shadow agrees with the real patched CDS "
          "parser exponent behaviour on %d inputs (seed=%d), 0 disagreements."
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
