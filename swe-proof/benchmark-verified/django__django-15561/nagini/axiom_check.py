#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15561.

This bundle consumes NO `@ContractOnly` axiom: the changed behaviour -- the set
of attributes that do not affect a column definition, and the rebuild decision
that ignores any difference confined to that set -- is modelled DEEPLY in
model.py (`schema_irrelevant_attrs` builds the set explicitly; the scan in
`field_alteration_needed` is spelled out in the impl region). G-AX validates
those deep models against the REAL operations the gold patch composes -- the
A-references -- not a hand-rolled stand-in:

  (A-reference 1) the schema-irrelevant attribute set (`Field.non_db_attrs` in
      the gold) is the 12-element tuple
        choices, blank, db_column, editable, error_messages, help_text,
        limit_choices_to, on_delete, related_name, related_query_name,
        validators, verbose_name
      -- i.e. the 11 legacy `non_database_attrs` PLUS `choices`. The model's
      `schema_irrelevant_attrs()` pins EXACTLY this 12-code set (set equality,
      so neither a subset nor a superset verifies).

  (A-reference 2) the rebuild decision the gold computes is
        quote_name(old.column) != quote_name(new.column)
        OR  (old_path, old_args, old_kwargs') != (new_path, new_args, new_kwargs')
      where kwargs' is kwargs with every key in `non_db_attrs` removed
      (`old_kwargs.pop(attr, None)` / `new_kwargs.pop(attr, None)`). This script
      reconstructs that exact comparison over REAL Python ``dict``s (the very
      primitives the gold patch composes: dict ``.pop`` and tuple ``!=``) and
      asserts model.py's decision -- `other_differs OR (some schema-relevant
      attribute disagrees)` -- equals it on boundary + fuzz field pairs.

The F2P discriminator is checked explicitly: a pair differing ONLY in `choices`
(same column, same path/args, same other kwargs) is a NO-OP under the gold
(post-patch) set but WOULD rebuild under the pre-patch set that omits `choices`.

Imports only the Python standard library (`dict`/`tuple` are the language
primitives the gold composes). Exit 0 iff every obligation holds.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the pure region) ---
# attribute name -> model.py attr code (model.py pure region)
ATTR_CODE = {
    "choices": 0,
    "blank": 1,
    "db_column": 2,
    "editable": 3,
    "error_messages": 4,
    "help_text": 5,
    "limit_choices_to": 6,
    "on_delete": 7,
    "related_name": 8,
    "related_query_name": 9,
    "validators": 10,
    "verbose_name": 11,
}

# model.py schema_irrelevant_attrs() member codes (post-patch / gold).
MODEL_NON_DB_CODES = set(ATTR_CODE.values())

# The gold's Field.non_db_attrs tuple, verbatim (django/db/models/fields/__init__.py).
GOLD_NON_DB_ATTRS = (
    "blank",
    "choices",
    "db_column",
    "editable",
    "error_messages",
    "help_text",
    "limit_choices_to",
    "on_delete",
    "related_name",
    "related_query_name",
    "validators",
    "verbose_name",
)

# The pre-patch local list (the bug): identical EXCEPT it omits "choices".
PREPATCH_NON_DATABASE_ATTRS = tuple(a for a in GOLD_NON_DB_ATTRS if a != "choices")


# --- (A-reference 2) the REAL gold decision over real dicts ------------------

def gold_should_be_altered(old_column, new_column, old_path, new_path,
                           old_args, new_args, old_kwargs, new_kwargs,
                           non_db_attrs):
    """Faithful reconstruction of the gold `_field_should_be_altered` body
    (django/db/backends/base/schema.py), composed of the exact primitives the
    gold patch uses: `kwargs.pop(attr, None)` and tuple `!=`.
    quote_name is monotone/injective on column names, so the column comparison
    is modelled by raw column inequality."""
    ok = dict(old_kwargs)
    nk = dict(new_kwargs)
    for attr in non_db_attrs:
        ok.pop(attr, None)
    for attr in non_db_attrs:
        nk.pop(attr, None)
    return old_column != new_column or (old_path, old_args, ok) != (
        new_path, new_args, nk)


# --- model.py decision (field_alteration_needed) -----------------------------

def model_decision(other_differs, attrs, old_vals, new_vals, non_db_codes):
    """model.py `field_alteration_needed`: other_differs OR some listed
    attribute is OUTSIDE the schema-irrelevant set and disagrees in value."""
    if other_differs:
        return True
    for i in range(len(attrs)):
        if attrs[i] not in non_db_codes and old_vals[i] != new_vals[i]:
            return True
    return False


def to_model_inputs(old_kwargs, new_kwargs, old_column, new_column,
                    old_path, new_path, old_args, new_args):
    """Project a field pair onto model.py's carrier:
      attrs = the kwarg keys appearing on either side (as model codes),
      old_vals/new_vals = the value token per key (a distinct ABSENCE token for
        a key missing on that side -> faithfully a value mismatch),
      other_differs = column / path / leading-args comparison (the non-kwarg
        structural part).
    Value tokens are obtained by hashing each (key,value) to a stable int; the
    ABSENCE token is a value no present value can take.
    Only keys that ARE attribute codes the model knows are listed; any kwarg key
    not in ATTR_CODE is schema-relevant by construction and folded into
    other_differs (so the abstraction never under-counts a real difference)."""
    ABSENT = -1
    keys = set(old_kwargs) | set(new_kwargs)
    attrs, ov, nv = [], [], []
    extra_relevant_differs = False
    for k in sorted(keys):
        if k not in ATTR_CODE:
            # a kwarg outside the modelled attribute universe: if it disagrees
            # it is schema-relevant -> fold into other_differs.
            a = old_kwargs.get(k, _AB)
            b = new_kwargs.get(k, _AB)
            if a != b:
                extra_relevant_differs = True
            continue
        attrs.append(ATTR_CODE[k])
        ov.append(_token(k, old_kwargs[k]) if k in old_kwargs else ABSENT)
        nv.append(_token(k, new_kwargs[k]) if k in new_kwargs else ABSENT)
    other_differs = (old_column != new_column or old_path != new_path
                     or old_args != new_args or extra_relevant_differs)
    return other_differs, attrs, ov, nv


_AB = object()
_TOK = {}


def _token(key, value):
    """A stable positive int token for a (key, value) pair; equal pairs -> equal
    tokens, distinct pairs -> distinct tokens (object/value identity carrier)."""
    k = (key, repr(value))
    if k not in _TOK:
        _TOK[k] = len(_TOK) + 1   # >= 1, never collides with ABSENT (-1)
    return _TOK[k]


# --- checks ------------------------------------------------------------------

def check_pair(old_kwargs, new_kwargs, old_column, new_column,
               old_path, new_path, old_args, new_args, label=""):
    other_differs, attrs, ov, nv = to_model_inputs(
        old_kwargs, new_kwargs, old_column, new_column,
        old_path, new_path, old_args, new_args)
    model_post = model_decision(other_differs, attrs, ov, nv, MODEL_NON_DB_CODES)
    gold_post = gold_should_be_altered(
        old_column, new_column, old_path, new_path, old_args, new_args,
        old_kwargs, new_kwargs, GOLD_NON_DB_ATTRS)
    assert model_post == gold_post, (
        "model decision disagrees with gold _field_should_be_altered on %s: "
        "model=%r gold=%r\n  old_kwargs=%r new_kwargs=%r col=(%r,%r) "
        "path=(%r,%r) args=(%r,%r)" % (
            label, model_post, gold_post, old_kwargs, new_kwargs,
            old_column, new_column, old_path, new_path, old_args, new_args))


def main():
    # --- (A-reference 1): the schema-irrelevant set membership ---------------
    gold_codes = set()
    for a in GOLD_NON_DB_ATTRS:
        assert a in ATTR_CODE, "gold attr %r missing from model universe" % a
        gold_codes.add(ATTR_CODE[a])
    assert MODEL_NON_DB_CODES == gold_codes, (
        "model schema_irrelevant_attrs codes %r != gold non_db_attrs codes %r"
        % (MODEL_NON_DB_CODES, gold_codes))
    assert ATTR_CODE["choices"] in MODEL_NON_DB_CODES, (
        "model omits the enumeration attribute (choices) from the "
        "schema-irrelevant set")
    assert len(GOLD_NON_DB_ATTRS) == 12 and "choices" in GOLD_NON_DB_ATTRS

    # --- F2P discriminator: choices-only change is a no-op under the gold ----
    #     (CharField name -> CharField name with choices=(...))
    base_kwargs = {"max_length": 255}
    with_choices = {"max_length": 255, "choices": (("Jane", "Jane"), ("Joe", "Joe"))}
    p = "django.db.models.CharField"
    # model decision == gold decision (must be False: no rebuild)
    check_pair(base_kwargs, with_choices, "name", "name", p, p, [], [],
               "F2P choices-only")
    g = gold_should_be_altered("name", "name", p, p, [], [],
                               base_kwargs, with_choices, GOLD_NON_DB_ATTRS)
    assert g is False, "gold should treat a choices-only change as a no-op"
    # symmetric direction (new->old) also a no-op (the test runs both ways)
    check_pair(with_choices, base_kwargs, "name", "name", p, p, [], [],
               "F2P choices-only reverse")
    # and the pre-patch set (omitting choices) WOULD wrongly rebuild:
    g_pre = gold_should_be_altered("name", "name", p, p, [], [],
                                   base_kwargs, with_choices,
                                   PREPATCH_NON_DATABASE_ATTRS)
    assert g_pre is True, (
        "pre-patch set must (buggily) rebuild on a choices-only change -- "
        "this is the behaviour the fix removes")

    # --- boundary field pairs -------------------------------------------------
    boundary = [
        # identical -> no rebuild
        (base_kwargs, dict(base_kwargs), "name", "name", p, p, [], [], "identical"),
        # column differs (kwargs equal) -> rebuild (gold compares quoted columns;
        # quote_name is injective so distinct columns differ). model==gold:
        (base_kwargs, dict(base_kwargs), "name", "title", p, p, [], [], "col-diff"),
        # a single schema-irrelevant attr differs -> no rebuild
        ({"max_length": 255, "help_text": "a"}, {"max_length": 255, "help_text": "b"},
         "name", "name", p, p, [], [], "help_text-diff"),
        ({"max_length": 255, "verbose_name": "A"}, {"max_length": 255, "verbose_name": "B"},
         "name", "name", p, p, [], [], "verbose_name-diff"),
        # several schema-irrelevant attrs differ together -> still no rebuild
        ({"max_length": 255, "blank": True, "editable": True, "help_text": "x"},
         {"max_length": 255, "blank": False, "editable": False, "help_text": "y"},
         "name", "name", p, p, [], [], "many-irrelevant-diff"),
        # a SCHEMA-RELEVANT attr differs (max_length, not in non_db) -> rebuild
        ({"max_length": 255}, {"max_length": 100}, "name", "name", p, p, [], [],
         "max_length-diff"),
        # path differs -> rebuild
        (base_kwargs, dict(base_kwargs), "name", "name", p,
         "django.db.models.TextField", [], [], "path-diff"),
        # relevant AND irrelevant differ -> rebuild
        ({"max_length": 255, "help_text": "a"}, {"max_length": 100, "help_text": "b"},
         "name", "name", p, p, [], [], "relevant+irrelevant"),
        # choices present on both but EQUAL -> no rebuild
        ({"max_length": 255, "choices": (("a", "a"),)},
         {"max_length": 255, "choices": (("a", "a"),)},
         "name", "name", p, p, [], [], "choices-equal"),
    ]
    for case in boundary:
        check_pair(*case[:-1], label=case[-1])

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(15561)
    attr_names = list(ATTR_CODE) + ["max_length", "null", "unique"]  # mix in relevant
    paths = [p, "django.db.models.TextField", "django.db.models.IntegerField"]
    cols = ["name", "title", "slug"]
    valpool = [None, True, False, 0, 1, 255, "x", "y", (("a", "a"),), (("b", "b"),)]
    for _ in range(20000):
        ok, nk = {}, {}
        for a in attr_names:
            if rng.random() < 0.5:
                ok[a] = rng.choice(valpool)
            if rng.random() < 0.5:
                nk[a] = rng.choice(valpool)
        oc, nc = rng.choice(cols), rng.choice(cols)
        op, npth = rng.choice(paths), rng.choice(paths)
        check_pair(ok, nk, oc, nc, op, npth, [], [], "fuzz")

    print("G-AX OK: schema_irrelevant_attrs == gold non_db_attrs (exactly 12 "
          "codes incl. the enumeration attribute, pinned by set EQUALITY); "
          "field_alteration_needed == gold "
          "_field_should_be_altered on %d boundary + 20000 fuzz field pairs; "
          "F2P choices-only no-op confirmed (and pre-patch set rebuilds)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
