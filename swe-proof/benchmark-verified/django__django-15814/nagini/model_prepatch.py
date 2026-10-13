"""Twin-artifact model for django__django-15814.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader works out which database columns to fetch for an optimized
  query that pulls a related object alongside the primary one and restricts the
  related object to a chosen subset of its stored attributes, it accumulates,
  per participating model, the set of attribute names that must be fetched.
  The mapping it reports is consumed WHOLE by the step that turns it into
  columns: every bucket it reports is read, not only the related model's.

  Two models participate in the slice modelled here: the query's own PRIMARY
  model, and the RELATED model reached from it through one reference attribute
  the primary model stores.

  Three kinds of attribute name are recorded while the related model is
  traversed:

    (1) the *passthrough* requirements on the primary side — the primary
        model's own primary-key attribute and the reference attribute it stores
        for the traversed relation. Even though the caller restricted only the
        related object, the primary object still has to be identifiable and the
        reference it is reached through still has to be fetched;

    (2) a *passthrough* requirement on the related side — the related model's
        own primary-key attribute, which must always be fetched so a fetched
        related object can be identified, and

    (3) the *restricted* requirement — the chosen attribute on the related
        model (the one the caller asked to keep).

  Each model participates in the accumulation under ONE canonical identity. A
  model that is a lightweight alias of another shares that other model's
  storage, hence its canonical identity: both must be recorded under the same
  canonical key. The restricted attribute (3) is recorded under the related
  model's canonical identity. The reported result is the per-model mapping of
  canonical model identity to the set of attribute names recorded for it.

  The contract pins the OBSERVABLES that the downstream identification step
  relies on:

    * the canonical-identity bucket for the related model exists and holds
      EXACTLY its primary key and the chosen attribute — nothing else (no
      spurious over-fetch);

    * the canonical-identity bucket for the primary model exists and holds
      EXACTLY its own primary key and the reference attribute — nothing else.
      A reported mapping that omits either of those from the primary model's
      bucket, or that reports some other attribute set there, is rejected: the
      primary object would then not be identifiable, or the reference the
      related object is reached through would not be fetched, even though the
      caller restricted only the related object; and

    * each primary key is recorded under its model's canonical identity, NOT
      scattered under that model's raw (non-canonical) identity. A reported
      mapping that lodges a primary key under a raw alias identity (leaving the
      canonical bucket — or some other bucket — to carry it) is rejected: a
      passthrough primary key must be accumulated under the same canonical key
      the restricted attribute and the final read-out use.

  Scope of the modelled slice: exactly one relation hop, over a reference the
  primary model itself stores; the primary and the related model keep separate
  storage, so their canonical identities differ; the caller's restriction keeps
  exactly one attribute and that attribute belongs to the related object, so
  nothing beyond the passthrough requirements is asked of the primary model;
  and that chosen attribute is stored by the related model itself rather than
  by a model whose storage it extends. Outside that slice the reported mapping
  has further participants, or further attributes for these ones, and this
  contract says nothing about it.

Modelling choices (Nagini fragment):
  * Models are `int` tokens; attribute names are `int` tokens.
  * The canonical identity of a model (its storage representative; an alias
    collapses to the model it aliases, a non-alias is its own canonical) is the
    map ``canonical`` from a model token to its canonical model token. It is
    idempotent (a canonical model is its own canonical). This is an unchanged
    attribute read, validated against real Python semantics out-of-band by
    axiom_check.py (G-AX) as an A-reference, not consumed as an axiom.
  * The storage owner of an attribute name (which model's storage holds it) is
    the map ``attr_owner`` from an attribute-name token to a canonical model
    token. Both maps are read-only.
  * The per-model accumulators are `Dict[int, Dict[int, int]]`: a model token
    maps to its recorded attribute-name set (a set carried as a `Dict[int,int]`
    keyed by attribute-name token). The result is the full per-model mapping;
    membership of an attribute name in a model's reported set is the observable
    the downstream identification step relies on.

No string indexing is used (Nagini bans it). Dict access is guarded by an
explicit membership test before subscription. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The per-model field accumulation and the canonical-key
# selection are the behaviour under specification and are modelled deeply (the
# `canonical_of` helper and the impl). The map subscriptions / set membership it
# composes are ordinary mapping operations, validated against their real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end


# pure-start
@Pure
def canonical_of(canonical: Dict[int, int], model: int) -> int:
    """The canonical (storage) identity of `model`: the `canonical` map applied
    to `model`, falling back to `model` itself when the model is absent from the
    map (a model that backs its own storage is its own canonical identity)."""
    Requires(Acc(dict_pred(canonical), 1 / 4))
    if model in canonical:
        return canonical[model]
    return model
# pure-end


def related_reported_fields(canonical: Dict[int, int],
                            attr_owner: Dict[int, int],
                            primary: int,
                            primary_pk: int,
                            ref_attr: int,
                            related: int,
                            related_pk: int,
                            chosen_attr: int) -> Dict[int, Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(canonical), 1 / 2))
    Requires(Acc(dict_pred(attr_owner), 1 / 2))
    # The passthrough key and the restricted key are distinct attribute names
    # (the primary key is not the chosen attribute), so set membership of one is
    # independent of the other.
    Requires(related_pk != chosen_attr)
    # The canonical map is a fixed-point of itself at both participants: a
    # canonical identity is its own canonical (idempotence). This is the real
    # attribute's property (`_meta.concrete_model` of a concrete model is
    # itself; validated by G-AX), constraining the input to the attribute's true
    # domain so that normalizing a model that is already canonical is a no-op.
    Requires(canonical_of(canonical, canonical_of(canonical, related))
             == canonical_of(canonical, related))
    Requires(canonical_of(canonical, canonical_of(canonical, primary))
             == canonical_of(canonical, primary))
    # Modelled slice: the related object is stored separately from the primary
    # one, so the two participants report under different canonical identities.
    Requires(canonical_of(canonical, primary)
             != canonical_of(canonical, related))
    # Modelled slice: the chosen attribute is one the related model's own
    # storage holds (it is not inherited from a model whose storage the related
    # model extends, which would report it under that other model's identity).
    # Stated on the storage identity of the declaring model, so the declaring
    # model token itself is NOT pinned to the related model's canonical identity
    # (it is only known to share it).
    Requires(chosen_attr in attr_owner
             and canonical_of(canonical, attr_owner[chosen_attr])
             == canonical_of(canonical, related))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(canonical), 1 / 2))
    Ensures(Acc(dict_pred(attr_owner), 1 / 2))
    # The result is the per-model reported mapping; permission to it and to the
    # two canonical-identity buckets whose contents the contract constrains.
    Ensures(Acc(dict_pred(Result())))
    Ensures(canonical_of(canonical, related) in Result())
    Ensures(canonical_of(canonical, primary) in Result())
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, related)])))
    Ensures(Acc(dict_pred(Result()[canonical_of(canonical, primary)])))
    # The reported set for the related model lives under its CANONICAL identity.
    # Within that bucket the chosen restricted attribute is present (the caller's
    # kept attribute), self-keyed.
    Ensures(chosen_attr in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][chosen_attr]
            == chosen_attr)
    # Discriminating clause (presence): the related model's primary key is
    # present in that SAME canonical-identity bucket, self-keyed.
    Ensures(related_pk in Result()[canonical_of(canonical, related)]
            and Result()[canonical_of(canonical, related)][related_pk]
            == related_pk)
    # Closure: the canonical bucket holds NOTHING beyond the primary key and the
    # chosen attribute — no spurious over-fetch.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, related)],
        a == related_pk or a == chosen_attr))))
    # Passthrough clause (presence): restricting the related object does not
    # excuse the primary side. Under the primary model's CANONICAL identity the
    # reported set carries its own primary key, so a fetched primary object can
    # be identified, AND the reference attribute the related object is reached
    # through, so the relation can still be traversed — both self-keyed.
    Ensures(primary_pk in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][primary_pk]
            == primary_pk)
    Ensures(ref_attr in Result()[canonical_of(canonical, primary)]
            and Result()[canonical_of(canonical, primary)][ref_attr]
            == ref_attr)
    # Closure: the primary model's bucket holds NOTHING beyond those two — the
    # caller restricted the related object, not the primary one, so no other
    # attribute of the primary model is reported as required.
    Ensures(Forall(int, lambda a: (Implies(
        a in Result()[canonical_of(canonical, primary)],
        a == primary_pk or a == ref_attr))))
    # Provenance clauses: the reported mapping is keyed SOLELY by canonical
    # identity. When a participating model is a non-canonical alias, its raw
    # identity is not a key of the result at all; everything recorded for it
    # lives under its canonical identity. (When a participant is already its own
    # canonical, the raw and canonical identities coincide and the clause is
    # vacuous.) Together with the presence clauses above, this requires each
    # primary key to reside under the canonical identity rather than under the
    # alias identity.
    Ensures(Implies(related != canonical_of(canonical, related),
                    not (related in Result())))
    Ensures(Implies(primary != canonical_of(canonical, primary),
                    not (primary in Result())))
    # post-conditions-end
    # impl-start
    # Canonical identities under which the two participating models report.
    prim_key = canonical_of(canonical, primary)  # type: int
    rel_key = canonical_of(canonical, related)  # type: int

    # `must_include`: the passthrough requirements, keyed by canonical identity.
    # The primary model contributes its own primary key.
    must_include = {}  # type: Dict[int, Dict[int, int]]
    prim_set = {}  # type: Dict[int, int]
    prim_set[primary_pk] = primary_pk
    must_include[prim_key] = prim_set

    # The traversed model is taken as the relation hands it over.
    cur_model = related  # type: int

    # Passing through the relation records the reference attribute on the model
    # the traversal came from, and the traversed model's own primary key.
    if prim_key in must_include:
        from_set = must_include[prim_key]  # type: Dict[int, int]
        from_set[ref_attr] = ref_attr
        must_include[prim_key] = from_set
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
    if prim_key in seen:
        prim_target = seen[prim_key]  # type: Dict[int, int]
        prim_source = must_include[prim_key]  # type: Dict[int, int]
        if primary_pk in prim_source:
            prim_target[primary_pk] = prim_source[primary_pk]
        if ref_attr in prim_source:
            prim_target[ref_attr] = prim_source[ref_attr]
        seen[prim_key] = prim_target
    else:
        seen[prim_key] = must_include[prim_key]

    # The reported per-model mapping (keyed by canonical model identity).
    return seen
    # impl-end
