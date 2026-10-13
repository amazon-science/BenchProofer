#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_m2mPkQuery
against the patch.diff behaviour (the post-patch `queryset_iterator` query-state
construction: `getattr(obj, field.name).select_related().only("pk")`).

The impl region is R/I (rows 1-4) plus a deeply-modeled, executable A-reference
(`raisesFieldError`, the `select_related_descend` rejection condition).
conf_skip=false: this runs a real fuzz.

  shadow (op-for-op transliteration of implementation_m2mPkQuery):
    q = dict(qs)                              # input queryset (projected)
    q["select_rel"] = ("unrestricted", None)  # .select_related()  [the fix]
    q["immediate"] = ["pk"]                    # .only("pk")
    return q                                    # the constructed query

The OBSERVABLE we diff is the triple the spec pins:
    (relation, immediate, raises_field_error(q))
We diff against an INDEPENDENT reconstruction of the patched query state
(`patched_query`) that follows `QuerySet.select_related()` / `.only("pk")` and
then evaluates `select_related_descend`'s rejection condition directly — written
from the Python semantics, NOT by reusing `shadow`, so a divergence would surface.

exit 0 iff zero disagreements over >=10^5 fuzzed inputs. stdlib-only.
"""
import random
import sys

SEED = 16938          # pinned in mapping.md
N = 120_000           # >= 10^5

FIELDS = ["master", "category", "author", "owner", "parent", "pk", "name"]


def raises_field_error(select_rel, immediate):
    """Deep model of `select_related_descend`'s deferred-vs-traversed rejection.

    Mirrors Lean `raisesFieldError`: only a RESTRICTED traversal (a specific
    field set, i.e. `query.select_related` is a dict / `restricted=True`) can
    conflict; a requested field absent from the immediate-loading mask is the
    conflict. `unrestricted` traversal (select_related True OR False — the
    projection collapses them, neither can conflict) never conflicts."""
    kind, fields = select_rel
    if kind == "fields" and immediate is not None:
        return any(f not in immediate for f in fields)
    return False


def shadow(qs):
    """R/I shadow of implementation_m2mPkQuery.

    `qs` = {"relation": str, "select_rel": (kind, fields|None),
            "immediate": list|None}. Returns the observed triple."""
    q = dict(qs)
    q["select_rel"] = ("unrestricted", None)  # .select_related() (the fix, op #2)
    q["immediate"] = ["pk"]                 # .only("pk")          (op #3)
    return (q["relation"], q["immediate"], q["select_rel"], raises_field_error(
        q["select_rel"], q["immediate"]))


def patched_query(qs):
    """Independent reconstruction of the POST-patch query state.

    QuerySet.select_related() with no args sets query.select_related = True
    (restricted=False); .only("pk") sets the immediate mask to {"pk"}. Then the
    SQL compiler runs select_related_descend over the related fields: with
    select_related True (not a dict) restricted is False, so no field can be
    'both deferred and traversed'."""
    relation = qs["relation"]
    # .select_related()  -> select_related = True  (unrestricted boolean)
    select_related = True
    # .only("pk")        -> deferred_loading immediate mask = {"pk"}
    immediate = ["pk"]
    # observed traversal config, projected to the SelectRel bijection:
    # non-dict (True OR False) -> unrestricted; dict -> fields (requested keys)
    select_rel = ("fields", list(select_related)) if isinstance(
        select_related, dict) else ("unrestricted", None)
    # select_related_descend rejection: restricted = isinstance(select_related, dict)
    restricted = isinstance(select_related, dict)
    raises = False
    if restricted:
        requested = select_related  # the dict of requested related fields
        for f in requested:
            if f not in immediate:   # deferred (not in immediate mask) yet traversed
                raises = True
                break
    return (relation, immediate, select_rel, raises)


def random_select_rel(rng):
    r = rng.random()
    if r < 0.5:
        return ("unrestricted", None)
    k = rng.randint(1, 3)
    return ("fields", rng.sample(FIELDS, k))


def random_case(rng):
    relation = rng.choice(["tags", "categories", "meta_data", "topics", "groups"])
    select_rel = random_select_rel(rng)
    if rng.random() < 0.4:
        immediate = None
    else:
        k = rng.randint(0, 3)
        immediate = rng.sample(FIELDS, k)
    return {"relation": relation, "select_rel": select_rel, "immediate": immediate}


def fixed_cases():
    """Boundary cases, incl. the F2P custom-manager scenario: the related
    manager applied select_related('master') (restricted dict), and the field is
    deferred by only('pk')."""
    return [
        # F2P: custom manager select_related("master") + only("pk") -> bug if unfixed
        {"relation": "tags", "select_rel": ("fields", ["master"]),
         "immediate": None},
        {"relation": "tags", "select_rel": ("fields", ["master"]),
         "immediate": ["name"]},
        # plain m2m, no custom manager / already-unrestricted traversal
        # (select_related False and True both project to "unrestricted")
        {"relation": "categories", "select_rel": ("unrestricted", None),
         "immediate": None},
        {"relation": "meta_data", "select_rel": ("unrestricted", None),
         "immediate": None},
        # restricted traversal of a field that IS in the mask
        {"relation": "topics", "select_rel": ("fields", ["pk"]), "immediate": ["pk"]},
        # multi-field restricted traversal
        {"relation": "groups", "select_rel": ("fields", ["author", "owner"]),
         "immediate": ["pk"]},
    ]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    cases = fixed_cases() + [random_case(rng) for _ in range(N)]
    for qs in cases:
        got = shadow(qs)
        want = patched_query(qs)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((qs, got, want))
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for qs, g, w in examples:
            print(f"  qs={qs!r} shadow={g!r} patched={w!r}")
        return 1
    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
