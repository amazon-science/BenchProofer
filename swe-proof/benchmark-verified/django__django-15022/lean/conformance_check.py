#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15022.

The bundle models ONE behaviour: the multi-word search-term filtering loop in
`ModelAdmin.get_search_results` (`django/contrib/admin/options.py`). Its Lean
implementation (`implementation_searchFilter`) narrows a collection of records
to those for which a SINGLE related row matches EVERY search word:

    termQueries = []                          # accumulate per-word queries
    for t in terms: termQueries.append(t)
    return [p for p in parents
            if not terms                      # empty query -> keep all
            or any(all(t in r.matched for t in termQueries) for r in p.rows)]

This script stands up a REAL in-memory Django (sqlite) with `Parent`/`Child`
models (a reverse FK = the multi-valued relation), registers a `ModelAdmin` with
`search_fields=['child__name']`, and calls the REAL patched
`get_search_results` over fuzzed scenarios. It diffs the set of surviving parent
pks against the R/I shadow of `implementation_searchFilter`.

Bridging (mapping.md): each token-id ↦ a unique NATO word (chosen substring-free,
so word `t` matches a child iff `t` is one of the child's tokens, under
`icontains`). A `Row.matched` token-set ↦ a `Child` whose `name` is the
space-join of its tokens. The search term ↦ the space-join of the query tokens
(`smart_split` re-splits it into the same words). The surviving-parent set is the
membership observable the F2P tests assert (count==0 / count==1).

>=1e5 randomized draws plus enumerated edge cases. stdlib-only fuzzing (pinned
seed 15022, also recorded in mapping.md). Exit 0 iff zero disagreements.
"""
import os
import random
import sys
import tempfile

SEED = 15022
N_RANDOM = 120_000  # >= 1e5

# Substring-free token vocabulary (no word is a substring of another, so
# `icontains` of word w over a space-join of words matches iff w is in the set).
WORDS = [
    "alpha", "bravo", "delta", "foxtrot", "golf", "hotel", "india",
    "juliet", "kilo", "november", "oscar", "victor", "whiskey", "yankee",
]


def _assert_substring_free():
    for a in WORDS:
        for b in WORDS:
            if a != b and a in b:
                raise SystemExit(f"vocabulary not substring-free: {a!r} in {b!r}")


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "ccapp"))
    open(os.path.join(d, "ccapp", "__init__.py"), "w").close()
    models_py = (
        "from django.db import models\n"
        "class Parent(models.Model):\n"
        "    name = models.CharField(max_length=128)\n"
        "    class Meta: app_label = 'ccapp'\n"
        "class Child(models.Model):\n"
        "    parent = models.ForeignKey(Parent, models.SET_NULL, null=True)\n"
        "    name = models.CharField(max_length=128, blank=True)\n"
        "    class Meta: app_label = 'ccapp'\n"
    )
    open(os.path.join(d, "ccapp", "models.py"), "w").write(models_py)
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "ccapp"],
        USE_TZ=True,
    )
    django.setup()
    from django.db import connection
    from ccapp.models import Parent, Child
    with connection.schema_editor() as se:
        se.create_model(Parent)
        se.create_model(Child)
    return Parent, Child


# ---- shadow of implementation_searchFilter (the R/I leg) -------------------
# A scenario: parents = list of parents; each parent = list of children; each
# child = a frozenset of token-ids (its matched word set). The query = a list of
# token-ids. Returns the set of surviving parent indices.
def shadow_filter(parents, terms):
    survivors = set()
    for i, rows in enumerate(parents):
        if not terms:
            survivors.add(i)                       # combinedMatch [] = true
            continue
        # any related row matches every word?
        if any(all(t in row for t in terms) for row in rows):
            survivors.add(i)
    return survivors


def _scenario_to_db(Parent, Child, parents):
    """Materialize a scenario; return [parent_pk] in scenario order."""
    Child.objects.all().delete()
    Parent.objects.all().delete()
    pks = []
    for rows in parents:
        p = Parent.objects.create(name="p")
        pks.append(p.pk)
        for tokset in rows:
            cname = " ".join(WORDS[t] for t in sorted(tokset))
            Child.objects.create(parent=p, name=cname)
    return pks


def real_filter(admin_obj, Parent, pks, terms):
    """Run the REAL patched get_search_results; return surviving scenario idxs."""
    search_term = " ".join(WORDS[t] for t in terms)
    qs = Parent.objects.all()
    out_qs, _dup = admin_obj.get_search_results(None, qs, search_term)
    surviving_pks = set(out_qs.values_list("pk", flat=True))  # distinct membership
    return {i for i, pk in enumerate(pks) if pk in surviving_pks}


def _enumerate_edge(n_tokens):
    """Hand-picked scenarios exercising the quantifier-swap discriminator."""
    A, B, C = 0, 1, 2
    cases = []
    # the F2P discriminator: two words split across two rows, no single row both.
    # query [A,B]: row {A}, row {B}  -> pre-patch keeps, post-patch drops.
    cases.append(([[{A}, {B}]], [A, B]))
    # single row matches both -> kept
    cases.append(([[{A, B}, {C}]], [A, B]))
    # many identical words, one row contains it
    cases.append(([[{A}, {A, B}]], [A, A, A, A]))
    # empty query -> all parents kept (incl. childless)
    cases.append(([[], [{A}]], []))
    # childless parent with nonempty query -> dropped
    cases.append(([[]], [A]))
    # multiple parents mixed
    cases.append(([[{A, B}], [{A}, {B}], []], [A, B]))
    # single word, present / absent
    cases.append(([[{A}], [{B}]], [A]))
    return cases


def main() -> int:
    _assert_substring_free()
    Parent, Child = setup_django()
    from django.contrib.admin import ModelAdmin, AdminSite

    class ParentAdmin(ModelAdmin):
        search_fields = ["child__name"]

    admin_obj = ParentAdmin(Parent, AdminSite())

    checked = 0
    disagreements = 0

    def run_one(parents, terms):
        nonlocal checked, disagreements
        pks = _scenario_to_db(Parent, Child, parents)
        got = real_filter(admin_obj, Parent, pks, terms)
        exp = shadow_filter(parents, terms)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH parents={parents} terms={terms}: "
                      f"real={sorted(got)} shadow={sorted(exp)}")

    # edge cases
    for parents, terms in _enumerate_edge(len(WORDS)):
        run_one(parents, terms)

    # randomized fuzzing
    rng = random.Random(SEED)
    vocab_n = len(WORDS)
    for _ in range(N_RANDOM):
        n_parents = rng.randint(1, 3)
        parents = []
        for _p in range(n_parents):
            n_children = rng.randint(0, 3)
            rows = []
            for _c in range(n_children):
                k = rng.randint(0, 3)
                rows.append(set(rng.sample(range(vocab_n), k)))
            parents.append(rows)
        n_terms = rng.randint(0, 3)
        terms = [rng.randint(0, vocab_n - 1) for _ in range(n_terms)]
        run_one(parents, terms)

    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s) over {checked} checks")
    return 1


if __name__ == "__main__":
    sys.exit(main())
