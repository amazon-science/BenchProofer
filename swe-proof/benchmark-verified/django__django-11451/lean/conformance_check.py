#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_credentialAuth
against the patch.diff behaviour (post-patch ModelBackend.authenticate).

The impl region is all R/I: the four callees (lookupUser, passwordMatches,
userAllowed, checkHashCount) are referenced IDENTICALLY in spec and impl
(I-tagged, not consumed axioms), so this runs a real fuzz. For each fuzzed
input we instantiate the SAME random oracles for the callees and observe the
modeled outcome (user, queries, hasherCalls) two ways:

  * shadow()  — reproduces implementation_credentialAuth op-for-op:
                resolve the login name, then the patched guard
                `if login is None or secret is None: return`, else one store
                query; on a miss one hasher run (set_password); on a hit the
                check's inherent hashing cost checkHashCount (0 when the stored
                password is unusable — hashers.check_password short-circuits
                before hasher.verify — else 1 encode() from verify; MD5's
                must_update is False so harden_runtime never runs).
  * patched() — an independent reconstruction of the patched Python control flow
                of ModelBackend.authenticate, counting the same two side effects
                (hasher = CountingMD5PasswordHasher.calls, i.e. encode()
                invocations: one from set_password's make_password on a miss;
                on a hit, check_password returns False with no hash when the
                stored password is unusable, else exactly one from verify).

Zero disagreements required over >=10^5 fuzzed inputs. stdlib-only; exit 0 iff
zero disagreements.
"""
import random
import sys

SEED = 11451          # pinned in mapping.md
N = 120_000           # >= 10^5

NAME_ALPHABET = list("abcUSER_0123")


def rand_opt_name(rng):
    """An Option (List Char): None ~1/3 of the time, else a short identifier."""
    if rng.random() < 0.34:
        return None
    return "".join(rng.choice(NAME_ALPHABET) for _ in range(rng.randint(0, 6)))


def make_oracles(rng):
    """A random instantiation of the UNCHANGED callees, shared by both legs."""
    # lookupUser: some login names map to a user uid, others miss.
    known = {}
    for _ in range(rng.randint(0, 5)):
        known["".join(rng.choice(NAME_ALPHABET) for _ in range(rng.randint(0, 6)))] = rng.randint(0, 99)
    usable = rng.random() < 0.8       # stored password usable (not set_unusable)
    # passwordMatches u pw: an unusable stored password can never match.
    matches = usable and rng.random() < 0.5
    allowed = rng.random() < 0.5      # userAllowed u
    # checkHashCount u pw: check_password short-circuits (0 hashes) on an
    # unusable stored password, else hasher.verify encodes once.
    check_hashes = 1 if usable else 0
    return known, matches, allowed, check_hashes


def resolve(name, fallback):
    return fallback if name is None else name


def shadow(name, fallback, secret, oracles):
    """R/I shadow of implementation_credentialAuth."""
    known, matches, allowed, check_hashes = oracles
    login = name
    if login is None:
        login = fallback
    if login is None or secret is None:
        return (None, 0, 0)
    if login not in known:
        return (None, 1, 1)
    u = known[login]
    if matches and allowed:
        return (u, 1, check_hashes)
    return (None, 1, check_hashes)


def patched(name, fallback, secret, oracles):
    """Independent reconstruction of the PATCHED authenticate() control flow.
    queries counts get_by_natural_key calls; hasher counts set_password calls."""
    known, matches, allowed, check_hashes = oracles
    queries = 0
    hasher = 0
    username = name
    if username is None:
        username = fallback
    # patched guard: short-circuit before any DB query / hasher run
    if username is None or secret is None:
        return (None, queries, hasher)
    queries += 1                       # get_by_natural_key(username)
    if username not in known:          # DoesNotExist
        hasher += 1                    # set_password(password) -> encode()
        return (None, queries, hasher)
    u = known[username]
    # check_password: 0 encodes when the stored password is unusable
    # (short-circuit before hasher.verify), else 1 from verify -> encode().
    hasher += check_hashes
    if matches and allowed:            # check_password and user_can_authenticate
        return (u, queries, hasher)
    return (None, queries, hasher)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first: the three F2P credential shapes
    # ({}, {username}, {password}) plus both-present.
    o0 = ({"abc": 7}, True, True, 1)   # usable stored password: verify hashes once
    o1 = ({"abc": 7}, False, True, 0)  # unusable stored password: check short-circuits
    fixed = [
        (None, None, None, o0),        # {} : nothing supplied
        ("abc", None, None, o0),       # {username} : no password
        (None, None, "pw", o0),        # {password} : no username (no fallback)
        ("abc", None, "pw", o0),       # both present, user known, ok
        ("zzz", None, "pw", o0),       # both present, user unknown -> hasher
        (None, "abc", "pw", o0),       # fallback supplies the name
        (None, "abc", None, o0),       # fallback name but no password
        ("abc", None, "pw", o1),       # hit on a user with an unusable password
    ]
    cases = fixed + [
        (rand_opt_name(rng), rand_opt_name(rng), rand_opt_name(rng), make_oracles(rng))
        for _ in range(N)
    ]

    for name, fallback, secret, oracles in cases:
        got = shadow(name, fallback, secret, oracles)
        want = patched(name, fallback, secret, oracles)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((name, fallback, secret), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
