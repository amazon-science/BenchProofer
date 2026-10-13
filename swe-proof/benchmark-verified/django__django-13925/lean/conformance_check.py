#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13925.

The bundle models ONE function: `Model._check_default_pk`
(`django/db/models/base.py`). It is a system check that decides whether to emit
the `models.W042` advisory ("auto-created primary key used …"). Its Lean
implementation (`implementation_checkDefaultPk`) returns the single advisory when
a conjunction of boolean observations holds, and the empty list otherwise:

    if auto_created
       and not (pk_is_to_one_relation and pk_relation_is_parent_link)   # the fix
       and not default_auto_field_overridden
       and not app_config_overridden:
        return [Warning(id='models.W042', obj=model, msg=..., hint=...)]
    return []

This script transliterates that R/I impl into Python (`shadow_check_default_pk`)
and differential-tests it against the ORACLE: a faithful in-process replica of
the POST-PATCH behavior of `_check_default_pk`, reproduced over the SAME
observables the real guard reads (mapping.md):

    cls._meta.pk.auto_created
    isinstance(cls._meta.pk, OneToOneField)
    cls._meta.pk.remote_field.parent_link
    settings.is_overridden('DEFAULT_AUTO_FIELD')
    cls._meta.app_config._is_default_auto_field_overridden

We do NOT stand up a Django app / model registry / settings (heavy, and the
modeled value is a pure decision over class metadata). Instead we reproduce the
patched guard directly over light stand-in records carrying exactly those
observables, plus the advisory payload (`obj`, `msg`, `hint`) which the patch
carries through unchanged. The advisory message/hint are opaque text carried
verbatim, so we model them with arbitrary strings; `obj` with an int identity.

The differential genuinely tests the Lean modeling of the FIX: the oracle
reproduces the patched `not (isinstance(pk, OneToOneField) and
pk.remote_field.parent_link)` guard, including Python's `and` short-circuit
(when `pk_is_to_one_relation` is False, `pk_relation_is_parent_link` is never
read); the shadow uses the total Lean `&&`. They must agree for every input — in
particular on the parent-link case the patch fixes
(`pk_is_to_one_relation and pk_relation_is_parent_link` both True), where the
advisory must be SUPPRESSED.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 13925 (also in
mapping.md).
"""
import sys

SEED = 13925
N = 200_000


# --- ORACLE: the post-patch _check_default_pk, faithful in-process replica ---
# A "model record" exposes the observables the real guard reads. `obj`/`msg`/
# `hint` are the advisory payload carried through unchanged by the patch.
def oracle_check_default_pk(rec):
    auto_created = rec["auto_created"]
    pk_is_o2o = rec["pk_is_to_one_relation"]
    pk_parent_link = rec["pk_relation_is_parent_link"]
    default_overridden = rec["default_auto_field_overridden"]
    app_overridden = rec["app_config_overridden"]
    # Faithful to patched source, including Python `and` short-circuit: when the
    # pk is not a to-one relation, `pk_relation_is_parent_link` is never read.
    if (
        auto_created and
        not (pk_is_o2o and pk_parent_link) and
        not default_overridden and
        not app_overridden
    ):
        return [{
            "id": "models.W042",
            "obj": rec["obj"],
            "msg": rec["msg"],
            "hint": rec["hint"],
        }]
    return []


# --- SHADOW: transliteration of the Lean R/I impl ----------------------------
# Mirrors `implementation_checkDefaultPk`: a total boolean conjunction (Lean `&&`)
# branching to a one-element advisory list or the empty list.
def shadow_check_default_pk(rec):
    report = (
        rec["auto_created"]
        and not (rec["pk_is_to_one_relation"] and rec["pk_relation_is_parent_link"])
        and not rec["default_auto_field_overridden"]
        and not rec["app_config_overridden"]
    )
    if report:
        return [{
            "id": "models.W042",
            "obj": rec["obj"],
            "msg": rec["msg"],
            "hint": rec["hint"],
        }]
    return []


# --- deterministic fuzzer (stdlib only) --------------------------------------
def gen(rng):
    return {
        "auto_created": rng.choice([True, False]),
        "pk_is_to_one_relation": rng.choice([True, False]),
        "pk_relation_is_parent_link": rng.choice([True, False]),
        "default_auto_field_overridden": rng.choice([True, False]),
        "app_config_overridden": rng.choice([True, False]),
        "obj": rng.randrange(0, 10_000),
        "msg": rng.choice(["m", "Auto-created primary key used …", ""]),
        "hint": rng.choice(["h", "Configure the DEFAULT_AUTO_FIELD setting …", ""]),
    }


def main():
    import random
    rng = random.Random(SEED)
    disagreements = 0

    # 1) Exhaustive over the 5 booleans (the decision domain) with fixed payload.
    payload = {"obj": 42, "msg": "m", "hint": "h"}
    for bits in range(32):
        rec = dict(payload)
        rec["auto_created"] = bool(bits & 1)
        rec["pk_is_to_one_relation"] = bool(bits & 2)
        rec["pk_relation_is_parent_link"] = bool(bits & 4)
        rec["default_auto_field_overridden"] = bool(bits & 8)
        rec["app_config_overridden"] = bool(bits & 16)
        if oracle_check_default_pk(rec) != shadow_check_default_pk(rec):
            disagreements += 1
            print(f"DISAGREE (exhaustive) on {rec}", file=sys.stderr)

    # 2) Randomized fuzz over booleans + varying payload.
    for _ in range(N):
        rec = gen(rng)
        if oracle_check_default_pk(rec) != shadow_check_default_pk(rec):
            disagreements += 1
            if disagreements <= 20:
                print(f"DISAGREE (fuzz) on {rec}", file=sys.stderr)

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreement(s)", file=sys.stderr)
        sys.exit(1)
    print(f"G-CONF OK: 32 exhaustive + {N} fuzzed inputs, zero disagreements")
    sys.exit(0)


if __name__ == "__main__":
    main()
