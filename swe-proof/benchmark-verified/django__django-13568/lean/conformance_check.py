#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_checkUserModel against the patch.diff behaviour (post-patch
check_user_model).

The impl region is NOT all-A-tagged (it is all R/I, refinement.md), so this
runs a real fuzz. The five UNCHANGED sub-checks are R-refined to booleans
(reqFieldsBadShape, usernameInRequired, fieldUnique, usesDefaultBackend,
isAnonymousMethod, isAuthenticatedMethod); the changed op (the login-field
uniqueness guard, row 3) is modeled deeply as the constraint filter
`coveredByUnconditionalUniqueConstraint` over a list of (isUnique, isConditional,
fields) records. We assert zero disagreements vs an independent reconstruction
of the patched function over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13568          # pinned in mapping.md
N = 130_000           # >= 10^5

FIELD_NAMES = ["username", "email", "login", "user_name", "", "id", "uuid"]


def covered_by_unconditional_unique_constraint(constraints, field):
    """Deep model of the changed guard's added conjunct: some unconditional
    uniqueness constraint ranges over exactly the one login field.

    `constraints` is a list of (is_unique, is_conditional, fields) tuples,
    mirroring Lean's `ConstraintInfo`. This is the R/I shadow of
    `not cls._meta.get_field(...).unique and not any(c.fields == (field,)
    for c in total_unique_constraints)` — `total_unique_constraints` keeps only
    `is_unique and not is_conditional`.
    """
    return any(
        is_unique and (not is_conditional) and list(fields) == [field]
        for (is_unique, is_conditional, fields) in constraints
    )


def shadow(username_field, req_bad_shape, username_in_required, field_unique,
           uses_default_backend, is_anon_method, is_auth_method, constraints):
    """R/I shadow of implementation_checkUserModel — in-order accumulation."""
    errors = []
    if req_bad_shape:
        errors.append("auth.E001")
    if username_in_required:
        errors.append("auth.E002")
    if (not field_unique) and not covered_by_unconditional_unique_constraint(
            constraints, username_field):
        if uses_default_backend:
            errors.append("auth.E003")
        else:
            errors.append("auth.W004")
    if is_anon_method:
        errors.append("auth.C009")
    if is_auth_method:
        errors.append("auth.C010")
    return errors


def patched(username_field, req_bad_shape, username_in_required, field_unique,
            uses_default_backend, is_anon_method, is_auth_method, constraints):
    """Independent reconstruction of the post-patch django check_user_model.

    Mirrors the source: E001, E002, then the (now constraint-guarded) E003/W004
    uniqueness diagnostic, then C009 / C010. `total_unique_constraints` filters
    the declared constraints to UniqueConstraint with condition is None; the
    guard skips the diagnostic when the field is directly unique OR some such
    constraint has fields == (USERNAME_FIELD,)."""
    errors = []
    if req_bad_shape:
        errors.append("auth.E001")
    if username_in_required:
        errors.append("auth.E002")

    total_unique_constraints = [
        fields for (is_unique, is_conditional, fields) in constraints
        if is_unique and is_conditional is False
    ]
    guarded = any(tuple(fields) == (username_field,)
                  for fields in total_unique_constraints)
    if (not field_unique) and not guarded:
        if uses_default_backend:
            errors.append("auth.E003")
        else:
            errors.append("auth.W004")

    if is_anon_method:
        errors.append("auth.C009")
    if is_auth_method:
        errors.append("auth.C010")
    return errors


def rand_constraints(rng, username_field):
    n = rng.choice([0, 0, 1, 1, 1, 2, 3])
    out = []
    for _ in range(n):
        is_unique = rng.random() < 0.7
        is_conditional = rng.random() < 0.4
        r = rng.random()
        if r < 0.45:
            fields = [username_field]            # exactly the login field
        elif r < 0.65:
            fields = [username_field, rng.choice(FIELD_NAMES)]  # composite
        elif r < 0.8:
            fields = [rng.choice(FIELD_NAMES)]   # some other single field
        else:
            fields = []                          # empty tuple
        out.append((is_unique, is_conditional, fields))
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    cases = []

    # Deterministic boundary: every boolean combination with a constraint set
    # that exactly covers the login field unconditionally (the F2P scenario),
    # and one with a conditional (partial) constraint (the partial-unique W004
    # scenario), and the empty constraint set.
    for bits in range(64):
        flags = [(bits >> k) & 1 == 1 for k in range(6)]
        cases.append(("username", *flags,
                      [(True, False, ["username"])]))         # total unique → guarded
        cases.append(("username", *flags,
                      [(True, True, ["username"])]))          # partial → not guarded
        cases.append(("username", *flags, []))                # no constraints
        cases.append(("username", *flags,
                      [(False, False, ["username"])]))        # non-unique constraint
        cases.append(("username", *flags,
                      [(True, False, ["username", "email"])]))  # composite → not guarded

    # Fuzz.
    for _ in range(N):
        uf = rng.choice(FIELD_NAMES)
        # Oversample field_unique=False so the changed branch is hit hard.
        if rng.random() < 0.6:
            field_unique = False
        else:
            field_unique = rng.random() < 0.5
        flags = (
            rng.random() < 0.2,        # req_bad_shape
            rng.random() < 0.2,        # username_in_required
            field_unique,
            rng.random() < 0.5,        # uses_default_backend
            rng.random() < 0.2,        # is_anon_method
            rng.random() < 0.2,        # is_auth_method
        )
        cases.append((uf, *flags, rand_constraints(rng, uf)))

    for c in cases:
        got = shadow(*c)
        want = patched(*c)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, g, w in examples:
            print(f"  in={c!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
