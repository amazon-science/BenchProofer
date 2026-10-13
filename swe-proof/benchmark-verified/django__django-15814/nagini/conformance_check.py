#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15814 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region contains none — contracts live only in the
pre/post regions) and the @Pure helper `canonical_of` copied over as a plain
function. There are no @ContractOnly callees and no PSeq usage in this
bundle; the carriers are plain ints and dicts, so no shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.sql.query.Query.deferred_to_data`, restricted to the
single-related-model `.only("rel__attr")` scenario the model abstracts. The
gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so importing Django resolves the patched code. For each
input the script builds a fresh queryset restricting the related object to
one chosen attribute, calls `deferred_to_data` on its Query, and reads the
per-model attname mapping it reports.

TYPE BRIDGE (mapping.md section 2): model classes <-> int tokens, field
attnames <-> int tokens, per-model attname sets <-> the inner Dict[int,int]
used as a self-keyed set, and the `canonical` map <-> the class-level
canonical/storage-representative relation (an alias class collapses to the
class whose storage it shares; a storage-backing class is its own
representative). The model's Result() covers the RELATED model's
contribution to the reported mapping; the root model's bucket (present in
the real output, concrete in both pre/post worlds and carrying no
discriminating content per refinement.md A6) is excluded from the
comparison. Everything else — which keys exist on the related side (the
canonical-keying / anti-scatter observable), and the exact attname set in
each bucket — is compared under the token bijection.

INPUT DOMAIN (Requires of related_reported_fields):
  * `related_pk != chosen_attr` (distinct attname tokens);
  * `canonical` idempotent at `related` (canonical_of(canonical_of(related))
    == canonical_of(related)).
Up to the token bijection the realizable structures are: the related model
is an alias of another model (related != canonical_of(related), realized as
an alias class — including an alias-of-alias, which the class machinery
collapses to the same representative), or it backs its own storage
(related == canonical_of(related), realized as an ordinary class, with the
self-entry either absent from the map or explicit). The fuzz varies the
structure, the token values (mixed sign/magnitude; model tokens may collide
with attname tokens — different sorts), the explicit self-entry, and inert
extra map entries at keys the shadow never reads (kept off {related,
canonical} so idempotence at `related` is preserved).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz values, the
real callee invoked afresh for every input. Pinned fuzz seed: 15814.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys

SEED = 15814
N_FUZZ = 100_000

CHOSEN_ATTR_NAME = "status"   # the restricted attribute on the related model
PK_ATTR_NAME = "id"           # the related model's pk attname


# --- pure helper from model.py (pure region), decorator/contract stripped ---

def canonical_of(canonical, model):
    if model in canonical:
        return canonical[model]
    return model


# --- the impl region of model.py, verbatim (no contracts appear in it) ------

def related_reported_fields(canonical, related, related_pk, chosen_attr):
    # Canonical identity under which the related model's fields are reported.
    rel_key = canonical_of(canonical, related)  # type: int

    # `must_include`: the passthrough requirements (the primary key) keyed by
    # the related model's canonical identity (the fix normalizes the traversed
    # model to its canonical form before keying).
    must_include = {}  # type: Dict[int, Dict[int, int]]
    cur_model = related  # type: int
    cur_model = canonical_of(canonical, cur_model)
    pk_set = {}  # type: Dict[int, int]
    pk_set[related_pk] = related_pk
    must_include[cur_model] = pk_set

    # `seen`: the restricted requirement (the chosen attribute) keyed by the
    # related model's canonical identity.
    seen = {}  # type: Dict[int, Dict[int, int]]
    leaf_set = {}  # type: Dict[int, int]
    leaf_set[chosen_attr] = chosen_attr
    seen[rel_key] = leaf_set

    # Merge the passthrough requirements into the reported (`seen`) accumulator,
    # per model key: a model recorded in `must_include` folds its required
    # attributes into the model's reported set under the same key.
    if cur_model in seen:
        target_set = seen[cur_model]  # type: Dict[int, int]
        source_set = must_include[cur_model]  # type: Dict[int, int]
        if related_pk in source_set:
            target_set[related_pk] = source_set[related_pk]
        seen[cur_model] = target_set
    else:
        seen[cur_model] = must_include[cur_model]

    # The reported per-model mapping (keyed by canonical model identity).
    return seen


# --- Django scaffolding for the oracle ---------------------------------------

def configure_django():
    """Configure Django just enough to define and introspect model classes.
    `deferred_to_data` only walks field/model metadata; an in-memory sqlite
    config is more than sufficient (no DB connection is ever opened). A
    throwaway app is written to a temp directory so the app registry loads."""
    import os
    import tempfile

    app_dir = tempfile.mkdtemp(prefix="conf_check_15814_")
    pkg_dir = os.path.join(app_dir, "conf_check_app")
    os.makedirs(pkg_dir, exist_ok=True)
    open(os.path.join(pkg_dir, "__init__.py"), "w").close()
    open(os.path.join(pkg_dir, "models.py"), "w").close()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "conf_check_app",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=False,
        )

    import django
    django.setup()


def build_scenarios():
    """One related-model class family (a storage-backing class, an alias of
    it, and an alias-of-alias) plus a root model with an FK to each variant.
    Returns the three concrete scenarios keyed by structure:
      'alias'        related is an alias  (related != canonical)
      'alias2'       related is an alias-of-alias (still != canonical)
      'self'         related backs its own storage (related == canonical)
    Each scenario: (root_class, related_raw_class, related_canonical_class,
    extra_related_side_classes) — the extra classes are the other members of
    the related family, mapped to fresh tokens so an unexpected key in the
    real output is detected rather than crashing the bridge."""
    from django.db import models

    class ConfUser(models.Model):
        status = models.CharField(max_length=50)

        class Meta:
            app_label = "conf_check_app"

    class ConfAliasUser(ConfUser):
        class Meta:
            app_label = "conf_check_app"
            proxy = True

    class ConfAliasAliasUser(ConfAliasUser):
        class Meta:
            app_label = "conf_check_app"
            proxy = True

    class ConfItemSelf(models.Model):
        assignee = models.ForeignKey(ConfUser, models.CASCADE)

        class Meta:
            app_label = "conf_check_app"

    class ConfItemAlias(models.Model):
        assignee = models.ForeignKey(ConfAliasUser, models.CASCADE)

        class Meta:
            app_label = "conf_check_app"

    class ConfItemAlias2(models.Model):
        assignee = models.ForeignKey(ConfAliasAliasUser, models.CASCADE)

        class Meta:
            app_label = "conf_check_app"

    return {
        "alias": (ConfItemAlias, ConfAliasUser, ConfUser,
                  [ConfAliasAliasUser]),
        "alias2": (ConfItemAlias2, ConfAliasAliasUser, ConfUser,
                   [ConfAliasUser]),
        "self": (ConfItemSelf, ConfUser, ConfUser,
                 [ConfAliasUser, ConfAliasAliasUser]),
    }


def real_related_view(root_class):
    """Call the REAL patched function on a fresh query restricting the
    related object to the chosen attribute; return the reported per-model
    attname mapping with the root model's bucket removed (the model's
    Result() covers the related model's contribution; the root bucket is
    outside the modeled slice — refinement.md A6)."""
    target = {}
    q = root_class.objects.only("assignee__%s" % CHOSEN_ATTR_NAME).query
    q.deferred_to_data(target)
    return {m: set(attrs) for m, attrs in target.items() if m is not root_class}


# --- differential -------------------------------------------------------------

def check_case(scenarios, structure, canonical_map, r_tok, pk_tok, attr_tok):
    """Run shadow and oracle on one abstract input (realized by `structure`);
    return an error string on disagreement, else None."""
    c_tok = canonical_of(canonical_map, r_tok)
    shadow = related_reported_fields(dict(canonical_map), r_tok,
                                     pk_tok, attr_tok)

    # Representation sanity: inner dicts are self-keyed sets.
    for m_tok, bucket in shadow.items():
        for a_tok, v in bucket.items():
            if v != a_tok:
                return ("DISAGREEMENT (shadow set representation broken)\n"
                        "  input: structure=%s canonical=%r related=%r "
                        "pk=%r attr=%r\n  shadow=%r"
                        % (structure, canonical_map, r_tok, pk_tok,
                           attr_tok, shadow))
    shadow_sets = {k: set(v.keys()) for k, v in shadow.items()}

    root_class, raw_class, canon_class, extras = scenarios[structure]
    real_view = real_related_view(root_class)

    # Token bijection for this input: the raw related class carries r_tok,
    # its canonical/storage class carries c_tok (they coincide in the 'self'
    # structure), the other family members carry fresh unused tokens so a
    # stray key in the real output surfaces as a mismatch, not a KeyError.
    fresh = min([r_tok, c_tok, pk_tok, attr_tok, 0]) - 1
    tok_model = {}
    for extra in extras:
        tok_model[extra] = fresh
        fresh -= 1
    tok_model[canon_class] = c_tok
    tok_model[raw_class] = r_tok
    tok_attr = {PK_ATTR_NAME: pk_tok, CHOSEN_ATTR_NAME: attr_tok}

    mapped = {}
    for m, attrs in real_view.items():
        if m not in tok_model:
            return ("DISAGREEMENT (real output keyed by a class outside the "
                    "modeled related family)\n"
                    "  input: structure=%s canonical=%r related=%r pk=%r "
                    "attr=%r\n  real=%r\n  shadow=%r"
                    % (structure, canonical_map, r_tok, pk_tok, attr_tok,
                       real_view, shadow_sets))
        mapped_attrs = set()
        for a in attrs:
            if a not in tok_attr:
                # An attname with no abstract counterpart: over-fetch on the
                # real side relative to the model — a genuine mismatch.
                mapped_attrs.add(("<unmapped>", a))
            else:
                mapped_attrs.add(tok_attr[a])
        mapped[tok_model[m]] = mapped_attrs

    if mapped != shadow_sets:
        return ("DISAGREEMENT\n"
                "  input: structure=%s canonical=%r related=%r pk=%r attr=%r\n"
                "  real (tokenized)=%r  raw real=%r\n"
                "  shadow=%r"
                % (structure, canonical_map, r_tok, pk_tok, attr_tok,
                   mapped, real_view, shadow_sets))
    return None


def boundary_cases():
    """Explicit (structure, canonical_map, related, pk, attr) tuples."""
    cases = []
    # alias, minimal tokens
    cases.append(("alias", {2: 1}, 2, 3, 4))
    # alias with explicit idempotent self-entry for the canonical token
    cases.append(("alias", {2: 1, 1: 1}, 2, 3, 4))
    # alias-of-alias (map still collapses straight to the canonical token)
    cases.append(("alias2", {5: 1}, 5, 3, 4))
    # self-backing, token absent from the map
    cases.append(("self", {}, 1, 3, 4))
    # self-backing with explicit self-entry
    cases.append(("self", {1: 1}, 1, 3, 4))
    # zero / negative / huge tokens
    cases.append(("alias", {0: -1}, 0, 1, 2))
    cases.append(("alias", {-5: -9}, -5, 0, -1))
    cases.append(("alias", {2 ** 62: 7}, 2 ** 62, -2 ** 62, 2 ** 40))
    cases.append(("self", {}, 0, -1, 1))
    cases.append(("self", {-(2 ** 40): -(2 ** 40)}, -(2 ** 40), 2 ** 40, 0))
    # model token colliding with an attname token (different sorts)
    cases.append(("alias", {7: 3}, 7, 3, 4))
    cases.append(("self", {}, 4, 3, 4))
    # inert extra entries at keys the shadow never reads
    cases.append(("alias", {2: 1, 9: 8, 8: 8, 100: 1}, 2, 3, 4))
    cases.append(("self", {9: 8, 100: 100}, 1, 3, 4))
    return cases


def rand_case(rng):
    structure = rng.choice(["alias", "alias", "alias2", "self", "self"])

    def tok():
        k = rng.random()
        if k < 0.5:
            return rng.randint(-20, 20)
        if k < 0.85:
            return rng.randint(-10 ** 6, 10 ** 6)
        return rng.randint(-2 ** 62, 2 ** 62)

    if structure in ("alias", "alias2"):
        r = tok()
        c = tok()
        while c == r:
            c = tok()
        canonical = {r: c}
        if rng.random() < 0.5:
            canonical[c] = c  # explicit idempotent self-entry
    else:
        r = tok()
        c = r
        canonical = {}
        if rng.random() < 0.5:
            canonical[r] = r
    # inert extra entries (never read by the shadow); keys stay off
    # {related, canonical} so idempotence at `related` is preserved
    for _ in range(rng.randint(0, 3)):
        k = tok()
        if k in (r, c):
            continue
        canonical[k] = tok()
    pk = tok()
    attr = tok()
    while attr == pk:
        attr = tok()
    return structure, canonical, r, pk, attr


def main():
    configure_django()
    scenarios = build_scenarios()

    checked = 0
    n_boundary = 0
    for structure, canonical, r, pk, attr in boundary_cases():
        err = check_case(scenarios, structure, canonical, r, pk, attr)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        structure, canonical, r, pk, attr = rand_case(rng)
        err = check_case(scenarios, structure, canonical, r, pk, attr)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched per-model reported mapping "
          "(related-model slice) on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
