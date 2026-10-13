#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15499 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model's minimal `CreateModel` carrier
class copies over as a plain attribute holder (constructor contracts dropped).
There are no @Pure helpers and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.db.migrations.operations.models.CreateModel.reduce`, called with a
real creation operation and a real follow-up operation of one of the two
modeled facet-altering kinds. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2, refinement.md rows A1-A4):
  * each facet object (field list, option dict, bases tuple, manager
    collection) is abstracted to an integer identity token, with equal-content
    facets sharing ONE token ("two facet values are the same iff their tokens
    are equal") — tokenization is content-based per case, so e.g. two empty
    collections on the two steps carry the same token on both sides of the
    diff;
  * the display name and its lower-cased comparison key are DISTINCT tokens in
    general — the bridge interns the exact display string and the lower-cased
    string as separate keys, so a result that carried the lower-cased key
    where the case-preserved display name belongs maps to the WRONG token and
    is reported as a disagreement (except for all-lowercase names, where the
    two strings — and hence the observables — genuinely coincide);
  * the follow-up step kind maps to the integer tag by the operation's runtime
    class (the precondition-restricted two-kind domain);
  * the option facet installed by an option-altering step denotes, per
    mapping.md, the post-merge/key-filter option dict (a pre-existing,
    unchanged computation abstracted into the single token); the bridge
    computes that denotation with the real class's own key list so the
    token's concrete value is exact;
  * `Optional[CreateModel]` vs the repo's return: a one-element list holding a
    creation operation maps to the non-null folded carrier; any other return
    (the un-collapsed fall-through) maps to the null token.

Input domain: the precondition demands only the two modeled kind tags plus
readable facets, so every generated case is Requires-satisfying. Generation
stresses the decision boundary: same-name (exact case, differing case,
all-lowercase names where the two name observables coincide) vs different-name
targets, both kinds, empty and overlapping option dicts, empty/multi manager
collections.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 15499.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the repo under test) only.
"""
import json
import random
import string
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={},
    )
django.setup()

from django.db import models
from django.db.migrations.operations.models import (
    AlterModelManagers,
    AlterModelOptions,
)
from django.db.migrations.operations.models import CreateModel as RealCreateModel

SEED = 15499
N_FUZZ = 100_000
APP_LABEL = "testapp"


# --- the model's minimal carrier class, contracts stripped ---------------------

class CreateModel:
    """A model-creation step exposing only the touched facets, each an integer
    token: `name` (the display name, case preserved), `name_lower` (the
    lower-cased comparison key derived from it), `fields` (field list),
    `options` (option set), `bases` (inheritance bases), `managers` (manager
    collection)."""

    def __init__(self, name, name_lower, fields, options, bases, managers):
        self.name = name
        self.name_lower = name_lower
        self.fields = fields
        self.options = options
        self.bases = bases
        self.managers = managers


# Follow-up step KIND tags (model.py module constants)
KIND_ALTER_OPTIONS = 0
KIND_ALTER_MANAGERS = 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reduce_create(model, op_kind, op_name, op_options, op_managers):
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None


# --- bridge helpers ------------------------------------------------------------

def _values_equal(a, b):
    if a is b:
        return True
    if type(a) is not type(b):
        return False
    try:
        return bool(a == b)
    except Exception:
        return False


class TokenSpace:
    """Content-based value -> int token map (identity-token abstraction):
    equal-content values share one token; a value matching nothing previously
    seen gets a fresh token. Per-case (a token space never crosses cases)."""

    def __init__(self):
        self._pairs = []  # [(concrete value, token)]

    def tok(self, value):
        for concrete, t in self._pairs:
            if _values_equal(value, concrete):
                return t
        t = len(self._pairs) + 1
        self._pairs.append((value, t))
        return t

    def lookup(self, value):
        """Token of an equal-content known value, or -1 (an unknown facet in a
        result slot can never equal any shadow token)."""
        for concrete, t in self._pairs:
            if _values_equal(value, concrete):
                return t
        return -1


def merged_options_denotation(create_options, op_options):
    """The concrete option dict the installed-options token denotes for an
    option-altering fold, per mapping.md: the union favouring the alter step,
    with the class-listed alterable keys absent from the alter step dropped.
    Uses the real class's own key list so the denotation tracks the repo."""
    merged = dict(create_options)
    merged.update(op_options)
    for key in AlterModelOptions.ALTER_OPTION_KEYS:
        if key not in op_options:
            merged.pop(key, None)
    return merged


def run_case(create_name, op_is_managers, op_target_name,
             fields, create_options, bases, create_managers,
             op_options, op_managers):
    """Build the real operations and the token-level shadow inputs for one
    case, run both sides, map the real result back to tokens, and compare.
    Returns an error string on disagreement, else None."""
    real_create = RealCreateModel(
        create_name,
        fields=list(fields),
        options=dict(create_options),
        bases=tuple(bases),
        managers=list(create_managers),
    )
    if op_is_managers:
        real_op = AlterModelManagers(name=op_target_name,
                                     managers=list(op_managers))
        op_kind = KIND_ALTER_MANAGERS
    else:
        real_op = AlterModelOptions(name=op_target_name,
                                    options=dict(op_options))
        op_kind = KIND_ALTER_OPTIONS

    # --- token assignment (fresh spaces per case) -----------------------------
    # Names: strings interned with a family prefix so the display name and the
    # lower-cased key stay distinct observables whenever the strings differ.
    names = TokenSpace()
    t_name = names.tok("display:" + real_create.name)
    t_name_lower = names.tok("key:" + real_create.name_lower)
    t_op_name = names.tok("key:" + real_op.name_lower)

    facets = TokenSpace()
    t_fields = facets.tok(real_create.fields)
    t_options = facets.tok(real_create.options)
    t_bases = facets.tok(real_create.bases)
    t_managers = facets.tok(real_create.managers)
    if op_is_managers:
        t_op_managers = facets.tok(real_op.managers)
        t_op_options = facets.tok(_Fresh())   # unused by this kind's fold
    else:
        t_op_options = facets.tok(
            merged_options_denotation(real_create.options, real_op.options))
        t_op_managers = facets.tok(_Fresh())  # unused by this kind's fold

    shadow_model = CreateModel(t_name, t_name_lower, t_fields, t_options,
                               t_bases, t_managers)
    shadow_res = reduce_create(shadow_model, op_kind, t_op_name,
                               t_op_options, t_op_managers)

    real_res = real_create.reduce(real_op, APP_LABEL)
    real_folded = None
    if (isinstance(real_res, list) and len(real_res) == 1
            and isinstance(real_res[0], RealCreateModel)):
        real_folded = real_res[0]

    def describe():
        return ("  create: name=%r fields=%r options=%r bases=%r managers=%r\n"
                "  follow-up: kind=%s target=%r options=%r managers=%r"
                % (create_name, [n for n, _ in fields], create_options,
                   bases, [n for n, _ in create_managers],
                   "managers-alter" if op_is_managers else "options-alter",
                   op_target_name, op_options, [n for n, _ in op_managers]))

    if (shadow_res is None) != (real_folded is None):
        return ("DISAGREEMENT (fold decision)\n%s\n  shadow=%r\n  real=%r"
                % (describe(),
                   "folded" if shadow_res is not None else "not-folded",
                   real_res))
    if shadow_res is None:
        return None

    # --- map the real folded op's slots back to tokens and compare -----------
    real_tokens = {
        "name": names.lookup("display:" + real_folded.name),
        "name_lower": names.lookup("key:" + real_folded.name_lower),
        "fields": facets.lookup(real_folded.fields),
        "options": facets.lookup(real_folded.options),
        "bases": facets.lookup(real_folded.bases),
        "managers": facets.lookup(real_folded.managers),
    }
    shadow_tokens = {
        "name": shadow_res.name,
        "name_lower": shadow_res.name_lower,
        "fields": shadow_res.fields,
        "options": shadow_res.options,
        "bases": shadow_res.bases,
        "managers": shadow_res.managers,
    }
    for slot in ("name", "name_lower", "fields", "options", "bases", "managers"):
        if shadow_tokens[slot] != real_tokens[slot]:
            return ("DISAGREEMENT (slot %r)\n%s\n"
                    "  shadow token=%r  real token=%r\n"
                    "  real folded slot value=%r"
                    % (slot, describe(), shadow_tokens[slot],
                       real_tokens[slot], getattr(real_folded, slot)))
    return None


class _Fresh:
    """A per-use sentinel equal only to itself: a facet the current step kind
    never installs, tokenized so the shadow still receives an int argument."""


# --- input generation ------------------------------------------------------------

# Reusable instance pools (reduce only forwards these objects; content
# equality per case is what the tokenization observes).
_FIELD_POOL = [models.CharField(max_length=10) for _ in range(4)]
_MANAGER_POOL = [models.Manager() for _ in range(6)]


def make_fields(n):
    return [("f%d" % i, _FIELD_POOL[i]) for i in range(n)]


def make_managers(names, offset=0):
    return [(nm, _MANAGER_POOL[(offset + i) % len(_MANAGER_POOL)])
            for i, nm in enumerate(names)]


OPTION_KEY_POOL = list(AlterModelOptions.ALTER_OPTION_KEYS) + [
    "db_table", "custom_a", "custom_b",
]


def rand_name(rng):
    first = rng.choice(string.ascii_letters)
    rest = "".join(rng.choice(string.ascii_letters + string.digits)
                   for _ in range(rng.randint(0, 7)))
    return first + rest


def rand_options(rng):
    ks = rng.sample(OPTION_KEY_POOL, rng.randint(0, 4))
    return {k: rng.randint(0, 9) for k in ks}


def rand_case(rng):
    create_name = rand_name(rng)
    op_is_managers = rng.random() < 0.5
    roll = rng.random()
    if roll < 0.45:
        op_target_name = create_name                       # exact-case match
    elif roll < 0.75:
        # differing-case spelling of the same name: keys still match
        op_target_name = "".join(
            c.upper() if rng.random() < 0.5 else c.lower() for c in create_name)
    else:
        op_target_name = rand_name(rng)                    # usually a mismatch
        if op_target_name.lower() == create_name.lower():
            op_target_name = op_target_name + "x"
    fields = make_fields(rng.randint(0, 3))
    create_options = rand_options(rng)
    bases = (models.Model,) if rng.random() < 0.7 else ("%s.parent" % APP_LABEL,)
    create_managers = make_managers(
        ["m%d" % i for i in range(rng.randint(0, 2))])
    op_options = rand_options(rng)
    op_managers = make_managers(
        ["om%d" % i for i in range(rng.randint(0, 3))], offset=3)
    return (create_name, op_is_managers, op_target_name, fields,
            create_options, bases, create_managers, op_options, op_managers)


def boundary_cases():
    """Decision-boundary cases: both kinds x {exact-case match, cross-case
    match, all-lowercase name (the two name observables coincide), mismatch},
    empty/overlapping option dicts, empty/multi manager collections."""
    cases = []
    f1 = make_fields(1)
    base = (models.Model,)
    for op_is_managers in (False, True):
        for create_name, target in [
            ("Foo", "Foo"),        # exact-case key match
            ("Foo", "foo"),        # lower-cased target, same key
            ("Foo", "FOO"),        # upper-cased target, same key
            ("foo", "foo"),        # all-lowercase: display == key
            ("Foo", "Bar"),        # key mismatch: no fold via these rules
            ("Foo", "fooo"),       # near-miss key
        ]:
            cases.append((create_name, op_is_managers, target, f1,
                          {"verbose_name": "v"}, base,
                          make_managers(["objects"]),
                          {"verbose_name": "w"},
                          make_managers(["objects", "things"], offset=3)))
    # empty facets on both sides (equal-content collections share a token)
    cases.append(("Foo", True, "Foo", [], {}, base, [], {}, []))
    cases.append(("Foo", False, "Foo", [], {}, base, [], {}, []))
    # identical option dicts on both steps (merged denotation == creation-side
    # options: equal content, one token)
    cases.append(("Foo", False, "Foo", f1, {"verbose_name": "v"}, base,
                  make_managers(["objects"]), {"verbose_name": "v"}, []))
    # identical manager collections on both steps
    same_mgrs = make_managers(["objects"])
    cases.append(("Foo", True, "Foo", f1, {}, base,
                  list(same_mgrs), {}, list(same_mgrs)))
    # option dicts exercising the merge/key-filter denotation: alterable keys
    # present on the creation side only, plus a non-alterable creation-side key
    cases.append(("Foo", False, "Foo", f1,
                  {"ordering": ["a"], "verbose_name": "x", "db_table": "t"},
                  base, make_managers(["objects"]),
                  {"verbose_name": "y"}, []))
    cases.append(("Foo", True, "Foo", f1,
                  {"ordering": ["a"], "db_table": "t"},
                  base, make_managers(["objects"]),
                  {"verbose_name": "y"}, make_managers(["only"], offset=3)))
    return cases


def main():
    checked = 0
    boundary = boundary_cases()
    for case in boundary:
        err = run_case(*case)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = run_case(*rand_case(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real reduce on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
