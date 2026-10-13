#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16560 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Exsures) stripped. There are no @Pure helpers and no
@ContractOnly callees in this bundle (both regions are empty); no PSeq shim is
needed (all carriers are scalars). The five impl functions are:
  configured_code, surfaced_violation_code, validate_rule, constraints_equal,
  keyword_bundle_names_code.

ORACLE: the REAL patched repo surfaces the model models per mapping.md,
imported from /testbed (the gate applies patch.diff before this script runs):
  Site 1 (configuration)  -> BaseConstraint/CheckConstraint/UniqueConstraint
                             __init__ storing `violation_error_code`
  Site 2 (violation flow) -> CheckConstraint.validate, driven through the real
                             Q(...).check(...) verdict on a live model
                             instance (the boolean the model abstracts), with
                             the raised ValidationError's `code` observed
  Site 3 (identity)       -> CheckConstraint.__eq__ / UniqueConstraint.__eq__
  Site 4 (reconstruction) -> BaseConstraint.deconstruct kwargs membership

Type bridge (mapping.md section 2): the classifier's Optional[int] token
domain lifts through a FIXED pool -- the None token <-> None, and each
distinct non-null int token <-> a distinct concrete string classifier. The
shadow's `is` on tokens is realised by always passing the SAME int object per
token (pool indexing), so token identity coincides with token equality,
mirroring the interned-string reading documented in mapping.md. The opaque
`*_key` payload (every other equality facet) lifts to the constraint's `name`
(all other facets held constant across a compared pair). `violated: bool`
lifts to a model-instance field value that makes the constraint's real
underlying check report a violation (or not). The user-defined
ValidationFailure <-> the framework ValidationError; the classifier the
surfaced failure carries is the raised error's `.code`.

The neutral (None) classifier is realised BOTH ways at sites 1 and 4 --
omitting the keyword and passing it explicitly as None -- since both concrete
call shapes realise the model's neutral marker.

Input domain: every precondition is either trivially satisfied (plain scalar
inputs) or `Requires(violated)` on surfaced_violation_code, which the driver
honours by calling it only on the raising path.

>= 1e5 Requires-satisfying inputs: exhaustive boundary sweeps over the token
pool (codes x codes x key-agreement x subclasses, codes x verdicts, codes x
call shapes) + 100000 cheap-site fuzz tuples (sites 1/3/4) + 20000 validate
fuzz tuples (site 2, each executing the real in-container check). Pinned
fuzz seed: 165600.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random).
"""
import json
import random
import sys

SEED = 165600
N_FUZZ_CHEAP = 100000
N_FUZZ_VALIDATE = 20000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class ValidationFailure(Exception):
    pass


def configured_code(code):
    return code


def surfaced_violation_code(rule_code, violated):
    return rule_code


def validate_rule(rule_code, violated):
    if violated:
        raise ValidationFailure()
    return


def constraints_equal(a_key, a_code, b_key, b_code):
    return a_key == b_key and a_code is b_code


def keyword_bundle_names_code(rule_code):
    return rule_code is not None


# --- token pools (the bridge's fixed carriers) --------------------------------

# Canonical int-token objects: always index THIS list so the same token value
# is the same object (shadow `is` == token equality, per mapping.md).
CODE_TOKENS = [None, 1, 2, 3, 5, 8, 13, 100, 255]
CODE_STRINGS = {t: (None if t is None else "classifier_%d" % t)
                for t in CODE_TOKENS}
KEY_TOKENS = [0, 1, 2, 3, 7, 42]
KEY_NAMES = {k: "rule_name_%d" % k for k in KEY_TOKENS}


def lift_code(token):
    return CODE_STRINGS[token]


# --- oracle drivers ------------------------------------------------------------

_env = {}


def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=False,
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()
    from django.db import models
    from django.db.models import Q
    from django.db.models.constraints import (BaseConstraint, CheckConstraint,
                                              UniqueConstraint)
    from django.core.exceptions import ValidationError

    class Thing(models.Model):
        num = models.IntegerField()

        class Meta:
            app_label = "auth"  # registered app label; no table is created

    _env.update(Q=Q, BaseConstraint=BaseConstraint,
                CheckConstraint=CheckConstraint,
                UniqueConstraint=UniqueConstraint,
                ValidationError=ValidationError, Thing=Thing)
    # One reusable constraint per code token for the validate driver (the
    # check itself is held constant; only the classifier and verdict vary).
    _env["validators"] = {
        t: CheckConstraint(check=Q(num__gt=0), name="v",
                           violation_error_code=lift_code(t))
        for t in CODE_TOKENS
    }


def real_configured(code_token, omit_kwarg, cls_index):
    """Site 1: construct a real constraint; observe its stored classifier."""
    kw = {} if omit_kwarg else {"violation_error_code": lift_code(code_token)}
    if cls_index == 0:
        c = _env["BaseConstraint"](name="n", **kw)
    elif cls_index == 1:
        c = _env["CheckConstraint"](check=_env["Q"](num__gt=0), name="n", **kw)
    else:
        c = _env["UniqueConstraint"](fields=["num"], name="n", **kw)
    return c.violation_error_code


def real_validate(code_token, violated):
    """Site 2: run the real CheckConstraint.validate on a live instance whose
    field value makes the underlying check report `violated`; observe the
    outcome kind and the classifier the raised error carries."""
    c = _env["validators"][code_token]
    inst = _env["Thing"](num=0 if violated else 1)
    try:
        c.validate(_env["Thing"], inst)
        return ("ok", None)
    except _env["ValidationError"] as e:
        return ("raise", e.code)


def real_equal(a_key, a_code, b_key, b_code, cls_index):
    """Site 3: real __eq__ over a pair differing only in name (the lifted
    opaque key) and classifier; every other facet held constant."""
    if cls_index == 0:
        ca = _env["CheckConstraint"](check=_env["Q"](num__gt=0),
                                     name=KEY_NAMES[a_key],
                                     violation_error_code=lift_code(a_code))
        cb = _env["CheckConstraint"](check=_env["Q"](num__gt=0),
                                     name=KEY_NAMES[b_key],
                                     violation_error_code=lift_code(b_code))
    else:
        ca = _env["UniqueConstraint"](fields=["num"], name=KEY_NAMES[a_key],
                                      violation_error_code=lift_code(a_code))
        cb = _env["UniqueConstraint"](fields=["num"], name=KEY_NAMES[b_key],
                                      violation_error_code=lift_code(b_code))
    return ca == cb


def real_deconstruct_names(code_token, omit_kwarg):
    """Site 4: membership of the classifier keyword in the real
    reconstruction kwargs."""
    kw = {} if omit_kwarg else {"violation_error_code": lift_code(code_token)}
    c = _env["BaseConstraint"](name="n", **kw)
    return "violation_error_code" in c.deconstruct()[2]


# --- per-site differential checks ----------------------------------------------

def check_configured(code_token, omit_kwarg, cls_index):
    s = configured_code(code_token)
    r = real_configured(code_token, omit_kwarg, cls_index)
    if lift_code(s) != r or ((s is None) != (r is None)):
        return ("DISAGREEMENT site=configuration\n"
                "  code_token=%r omit_kwarg=%r cls=%d\n"
                "  shadow=%r (lifts to %r)\n  real=%r"
                % (code_token, omit_kwarg, cls_index, s, lift_code(s), r))
    return None


def check_validate(code_token, violated):
    try:
        validate_rule(code_token, violated)
        shadow = ("ok", None)
    except ValidationFailure:
        shadow = ("raise", surfaced_violation_code(code_token, True))
    real = real_validate(code_token, violated)
    ok = (shadow[0] == real[0]
          and lift_code(shadow[1]) == real[1]
          and (shadow[1] is None) == (real[1] is None))
    if not ok:
        return ("DISAGREEMENT site=violation-flow\n"
                "  code_token=%r violated=%r\n"
                "  shadow=%r (code lifts to %r)\n  real=%r"
                % (code_token, violated, shadow, lift_code(shadow[1]), real))
    return None


def check_equal(a_key, a_code, b_key, b_code, cls_index):
    s = constraints_equal(a_key, a_code, b_key, b_code)
    r = real_equal(a_key, a_code, b_key, b_code, cls_index)
    if bool(s) != bool(r):
        return ("DISAGREEMENT site=identity\n"
                "  a_key=%r a_code=%r b_key=%r b_code=%r cls=%d\n"
                "  shadow=%r\n  real=%r"
                % (a_key, a_code, b_key, b_code, cls_index, s, r))
    return None


def check_deconstruct(code_token, omit_kwarg):
    s = keyword_bundle_names_code(code_token)
    r = real_deconstruct_names(code_token, omit_kwarg)
    if bool(s) != bool(r):
        return ("DISAGREEMENT site=reconstruction\n"
                "  code_token=%r omit_kwarg=%r\n  shadow=%r\n  real=%r"
                % (code_token, omit_kwarg, s, r))
    return None


# --- drivers --------------------------------------------------------------------

def run_boundary():
    """Exhaustive sweeps over the token pools."""
    checked = 0
    for i, code in enumerate(CODE_TOKENS):
        for omit in ((True, False) if code is None else (False,)):
            for cls_index in (0, 1, 2):
                err = check_configured(code, omit, cls_index)
                if err:
                    return checked, err
                checked += 1
            err = check_deconstruct(code, omit)
            if err:
                return checked, err
            checked += 1
        for violated in (False, True):
            err = check_validate(code, violated)
            if err:
                return checked, err
            checked += 1
        for j, other in enumerate(CODE_TOKENS):
            for a_key in KEY_TOKENS[:3]:
                for b_key in KEY_TOKENS[:3]:
                    for cls_index in (0, 1):
                        err = check_equal(a_key, CODE_TOKENS[i],
                                          b_key, CODE_TOKENS[j], cls_index)
                        if err:
                            return checked, err
                        checked += 1
    return checked, None


def run_fuzz(rng):
    checked = 0
    for _ in range(N_FUZZ_CHEAP):
        pick = rng.random()
        if pick < 0.34:
            code = CODE_TOKENS[rng.randrange(len(CODE_TOKENS))]
            omit = code is None and rng.random() < 0.5
            err = check_configured(code, omit, rng.randrange(3))
        elif pick < 0.67:
            err = check_equal(KEY_TOKENS[rng.randrange(len(KEY_TOKENS))],
                              CODE_TOKENS[rng.randrange(len(CODE_TOKENS))],
                              KEY_TOKENS[rng.randrange(len(KEY_TOKENS))],
                              CODE_TOKENS[rng.randrange(len(CODE_TOKENS))],
                              rng.randrange(2))
        else:
            code = CODE_TOKENS[rng.randrange(len(CODE_TOKENS))]
            omit = code is None and rng.random() < 0.5
            err = check_deconstruct(code, omit)
        if err:
            return checked, err
        checked += 1
    for _ in range(N_FUZZ_VALIDATE):
        err = check_validate(CODE_TOKENS[rng.randrange(len(CODE_TOKENS))],
                             rng.random() < 0.5)
        if err:
            return checked, err
        checked += 1
    return checked, None


def main():
    _setup()
    n_boundary, err = run_boundary()
    if err:
        print(err)
        return 1
    rng = random.Random(SEED)
    n_fuzz, err = run_fuzz(rng)
    if err:
        print(err)
        return 1
    total = n_boundary + n_fuzz
    print("G-CONF OK: shadow impl == real patched constraint surfaces on %d "
          "inputs (%d boundary + %d fuzz, seed %d) across configuration / "
          "violation-flow / identity / reconstruction."
          % (total, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": total, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
