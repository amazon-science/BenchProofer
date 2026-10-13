#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_validateToken
against the patch.diff behaviour (post-patch session-token verification decision
inside get_user).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: compute `token_verified` (false if no stored token,
else stored == current), and if not verified, scan the alternates for a match;
classify the input as REJECTED / ACCEPTED-CURRENT / ACCEPTED-ALTERNATE. We diff
that against an independent reconstruction of the post-patch Python control flow
(constant_time_compare modeled as value equality), mapping which branch of the
patched block executes to the same three-way decision. Zero disagreements
required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16631          # pinned in mapping.md
N = 120_000           # >= 10^5

TOKEN_ALPHABET = list("0123456789abcdef")  # hex digests; plus we use "" for absent

REJECTED = "rejected"
ACCEPTED_CURRENT = "acceptedCurrent"
ACCEPTED_ALTERNATE = "acceptedAlternate"


def shadow(stored, current, alternates):
    """R/I shadow of implementation_validateToken.

    Returns the VerifyDecision as one of the three code strings.
    Empty string `stored == ""` models the absent/falsy session hash ([] in Lean).
    """
    if stored == "":
        token_verified = False
    else:
        token_verified = (stored == current)
    if not token_verified:
        alternate_matched = False
        for t in alternates:
            if t == stored:
                alternate_matched = True
        if stored != "" and alternate_matched:
            return ACCEPTED_ALTERNATE
        else:
            return REJECTED
    return ACCEPTED_CURRENT


def patched(stored, current, alternates):
    """Independent reconstruction of the post-patch get_user verification block,
    classifying which branch executes:
      - the flush-and-drop branch (`request.session.flush(); user = None`)
        -> REJECTED
      - verified against the current-secret hash (block falls through, no state
        change) -> ACCEPTED_CURRENT
      - the fallback-acceptance branch (`if session_hash and any(...)`) ->
        ACCEPTED_ALTERNATE
    constant_time_compare(a, b) is value equality of the two strings.
    `session_hash` falsy is modeled as the empty string.
    """
    session_hash = stored

    if not session_hash:
        session_hash_verified = False
    else:
        session_auth_hash = current
        session_hash_verified = (session_hash == session_auth_hash)

    if not session_hash_verified:
        if session_hash and any(session_hash == fb for fb in alternates):
            return ACCEPTED_ALTERNATE
        return REJECTED
    return ACCEPTED_CURRENT


def rand_token(rng):
    return "".join(rng.choice(TOKEN_ALPHABET) for _ in range(rng.randint(1, 8)))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ("", "cur", []),                         # no stored token -> reject
        ("cur", "cur", []),                      # verified -> accepted-current
        ("cur", "cur", ["cur"]),                 # verified even with alternates
        ("old", "cur", ["old"]),                 # fallback match -> accepted-alternate
        ("old", "cur", ["x", "old", "y"]),       # fallback match later in list
        ("bad", "cur", ["old"]),                 # mismatch, no alternate -> reject
        ("bad", "cur", []),                      # mismatch, empty alternates -> reject
        ("", "cur", ["old"]),                    # absent stored, even with alternates
        ("old", "old", ["old"]),                 # stored==current==alternate -> current wins
    ]
    cases = list(fixed)
    for _ in range(N):
        # bias toward overlapping token pools so matches actually occur
        pool = [rand_token(rng) for _ in range(rng.randint(0, 4))]
        stored = rng.choice([""] + pool) if pool else rng.choice(["", rand_token(rng)])
        current = rng.choice(pool) if pool and rng.random() < 0.5 else rand_token(rng)
        alternates = [rng.choice(pool) for _ in range(rng.randint(0, 4))] if pool else []
        cases.append((stored, current, alternates))

    for stored, current, alternates in cases:
        got = shadow(stored, current, alternates)
        want = patched(stored, current, alternates)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((stored, current, alternates), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
