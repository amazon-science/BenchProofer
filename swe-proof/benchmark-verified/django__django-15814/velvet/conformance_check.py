#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15814 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`resolveKeys`) is the map-keying step inside
`Query.deferred_to_data` (django/db/models/sql/query.py, body lines 745-757):

    for name in parts[:-1]:
        ...
        if is_reverse_o2o(source):
            cur_model = source.related_model
        else:
            cur_model = source.remote_field.model
        cur_model = cur_model._meta.concrete_model      # <-- the fix
        opts = cur_model._meta
        ...
        add_to_dict(must_include, cur_model, opts.pk)    # cur_model is the key

The per-model key normalization (the `canonOf`/`keysOf` fold) is modeled deeply
and is I/R-tagged. But the operation it abstracts — walking a relation chain
through Django's model metadata graph (`opts.get_field(name)`,
`source.remote_field.model`, `source.related_model`) and recording, per reached
model, the key under which that model's field restrictions are collected — has
observable behavior ONLY against a live model registry and a relational backend:

  * the chain of models reached is produced by Django's metadata graph resolved
    against registered model classes; whether a reached model is a proxy (the
    case where the surface identity differs from the concrete/canonical
    identity, `ident != canon`) is a property of that registered class
    hierarchy, not a DB-free input we can fuzz.
  * reproducing the bug-triggering case — a relation chain whose target is a
    proxy model, optimized with `select_related().only(...)`, so the downstream
    related-populator (django/db/models/query.py:2243) looks up the concrete
    model's pk column and crashes with `'id' is not in list` — requires standing
    up the model graph (CustomModel/ProxyCustomModel/AnotherModel, or the F2P
    ProxyTrackerUser/Issue models), a DB connection, and an actual query
    execution; i.e. the F2P integration test `test_select_related_only` itself,
    not a pure R/I transliteration this gate can fuzz.

The abstraction the spec pins (`canon` -> the key every reached model
contributes, collapsing a proxy onto its concrete model, `keysOf` over the
COMPLETE chain) IS the modeled content; there is no DB-free oracle that produces
the metadata-graph model chain and proxy-ness to diff against. Per
SPEC_GUIDE §0 / WORKER_PROMPT, when the impl region's executable content is not
reproducible as a pure R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub. Soundness of the modeled keying step is instead carried by
G-VERIFY (the fold provably records the canonical identity `canonOf e = e.canon`
for every reached model, so the result is the per-model canonical-key sequence)
and G-DIFF (the prepatch, which records the surface identity `e.ident`, fails
exactly the `out = keysOf entities` clause on any input containing a proxy where
`ident != canon` -- the proxy-target crash). This mirrors the
django__django-13109, django__django-13315 and django__django-13089 precedents.
See mapping.md §4 and refinement.md §B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-15814 -- the modeled do-block is "
          "the map-keying step of Query.deferred_to_data, walking a relation "
          "chain through Django's model metadata graph and recording, per "
          "reached model, the key under which its field restrictions are "
          "collected. The fix normalizes each reached model to its concrete "
          "model before keying; whether a reached model is a proxy (surface vs. "
          "concrete identity) is a property of the live model registry and is "
          "only observable by executing a select_related().only() query against "
          "a real backend, not reproducible as a pure DB-free R/I shadow. "
          "conf_skip=true. Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
