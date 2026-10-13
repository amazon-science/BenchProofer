#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15380.

This bundle consumes NO `@ContractOnly` axiom. The behaviour under change — the
choice of registry key for the LATER model descriptor — is modelled deeply in
model.py (`prior_name` + the two guarded subscriptions of
`resolve_field_states`). The only out-of-band obligation is an **A-reference**:
that the model's lookup discipline matches real Python `dict` semantics on the
exact configuration the regression concerns.

We reproduce, in plain stdlib Python (`dict`), the two state registries and the
name-correspondence map of the migration autodetector, and assert that every
observation matches model.py:

  (1) `prior_name(renamed, later)` == `renamed.get(later, later)` (the deep model
      of `self.renamed_models.get((app_label, model_name), model_name)`).

  (2) The discriminating fact the patch fixes: for a RENAMED model, the model's
      prior name is ABSENT from the later-state registry — so the pre-patch key
      `to_state[prior_name]` raises `KeyError` — while the later name is PRESENT,
      so the post-patch key `to_state[later]` succeeds. For an UNCHANGED name
      the two keys coincide and both succeed.

  (3) The selected descriptors equal `from_state[prior_name]` (prior, unchanged)
      and `to_state[later]` (later, corrected) — model.py's two `Ensures`.

Imports nothing repo-specific: only `random`/`sys`. Exit 0 iff every obligation
holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def prior_name(renamed, later):
    """Reference for model.py's `prior_name`: the correspondence map applied to
    the later name, falling back to the later name when not recorded."""
    if later in renamed:
        return renamed[later]
    return later


def resolve_field_states(from_state, to_state, renamed, later):
    """Reference for model.py's `resolve_field_states` (the post-patch / gold
    behaviour): prior descriptor by prior name, later descriptor by later name.
    Precondition (mirrors model.py's Requires): `later in to_state` and
    `prior_name(...) in from_state`."""
    old_name = prior_name(renamed, later)
    return (from_state[old_name], to_state[later])


def prepatch_resolve(from_state, to_state, renamed, later):
    """The pre-patch (buggy) behaviour: later descriptor keyed by the PRIOR
    name. Raises KeyError exactly when the prior name is absent from the
    later-state registry (i.e. when the model was renamed)."""
    old_name = prior_name(renamed, later)
    return (from_state[old_name], to_state[old_name])


# --- the checks --------------------------------------------------------------

def check_config(from_state, to_state, renamed, later):
    """Assert (1)-(3) for one well-formed configuration.

    Well-formed (the autodetector invariants, mapping.md §2):
      * `later in to_state`              (field enumerated from later state)
      * `prior_name(later) in from_state` (prior state holds the model under
                                           its prior name)
    """
    old_name = prior_name(renamed, later)

    # (1) prior_name == dict.get with fallback
    assert old_name == renamed.get(later, later), (
        "prior_name model unsound: prior_name=%r dict.get=%r"
        % (old_name, renamed.get(later, later)))

    # (3) the model's two Ensures (post-patch behaviour) hold and never raise
    res = resolve_field_states(from_state, to_state, renamed, later)
    assert res[0] == from_state[old_name], "prior descriptor mismatch"
    assert res[1] == to_state[later], "later descriptor mismatch"

    renamed_here = (old_name != later)
    if renamed_here:
        # (2a) renamed: prior name MUST be absent from the later registry, so
        # the pre-patch lookup raises KeyError — the bug.
        assert old_name not in to_state, (
            "expected prior name %r absent from later registry on a rename, "
            "but it is present" % (old_name,))
        raised = False
        try:
            prepatch_resolve(from_state, to_state, renamed, later)
        except KeyError:
            raised = True
        assert raised, (
            "pre-patch lookup should raise KeyError on a renamed model %r" % later)
    else:
        # (2b) unchanged name: both keys coincide, pre-patch == post-patch.
        assert old_name == later and (later in to_state)
        assert prepatch_resolve(from_state, to_state, renamed, later) == res, (
            "with an unchanged name the two lookups must agree")


def main():
    # --- boundary configurations ---------------------------------------------
    # A renamed model: later name 2 corresponds to prior name 1.
    check_config(from_state={1: 100}, to_state={2: 200}, renamed={2: 1}, later=2)
    # An unchanged model: name 5 in both states, no rename entry.
    check_config(from_state={5: 500}, to_state={5: 555}, renamed={}, later=5)
    # Mixed registry: a renamed model alongside unchanged ones.
    check_config(
        from_state={1: 100, 3: 300, 7: 700},
        to_state={2: 200, 3: 300, 7: 700},
        renamed={2: 1},
        later=2,
    )
    # Unchanged model in a registry that also records other renames.
    check_config(
        from_state={1: 100, 3: 300},
        to_state={2: 200, 3: 300},
        renamed={2: 1},
        later=3,
    )

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(15380)
    for _ in range(50000):
        # Build a consistent later registry and a rename map pointing at distinct
        # prior names; then a prior registry that holds every model under its
        # prior name (the autodetector invariant).
        n_later = rng.randint(1, 6)
        later_names = rng.sample(range(0, 40), n_later)
        to_state = {nm: rng.randint(0, 9999) for nm in later_names}

        renamed = {}
        used_prior = set(later_names)
        for nm in later_names:
            if rng.random() < 0.5:
                # assign a fresh prior name distinct from all later/used names
                candidates = [c for c in range(40, 90) if c not in used_prior]
                pn = rng.choice(candidates)
                used_prior.add(pn)
                renamed[nm] = pn

        # prior registry: every model under its prior name (renamed.get(nm, nm))
        from_state = {prior_name(renamed, nm): rng.randint(0, 9999)
                      for nm in later_names}

        later = rng.choice(later_names)
        check_config(from_state, to_state, renamed, later)

    print("G-AX OK: prior_name == dict.get fallback; renamed models -> prior "
          "name absent from later registry (pre-patch KeyError) while later "
          "name present (post-patch succeeds); descriptors match model.py "
          "Ensures over 4 boundary + 50000 fuzz configurations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
