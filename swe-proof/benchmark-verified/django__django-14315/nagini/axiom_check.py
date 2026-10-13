#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14315.

Executes the REAL Python operations the model relies on and asserts that every
observation matches the model (as encoded in model.py). Two kinds:

  (A-consumed) the `env_merge` axiom (model.py axioms region) over-approximates
      the real mapping merge ``{**base, **overlay}``:
        * the result is a fresh, non-empty mapping (when either input is
          non-empty);
        * every key of `overlay` is present with `overlay`'s value;
        * every key of `base` not overridden by `overlay` keeps `base`'s value;
        * the result holds no key outside `base` ∪ `overlay`;
        * `base` and `overlay` are unchanged (lengths preserved).

  (A-reference) the two deep models (spelled out in model.py's impl regions)
      computed against the real Python expressions they mirror:
        * `normalized_environment(env)`  ==  `env or None`
        * `effective_environment(env, base)`  ==
              `{**base, **env} if env else None`
      i.e. an empty / None command mapping normalises to None (so the launched
      subprocess inherits os.environ), and a non-empty one becomes the merge.

Imports nothing repo-specific: only the standard library. Exit 0 iff every
obligation holds.
"""
import os
import random
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def normalized_environment(env):
    """Deep model of model.py `normalized_environment` (`env or None`)."""
    if len(env) == 0:
        return None
    return env


def effective_environment(env, base):
    """Deep model of model.py `effective_environment`
    (`{**base, **env} if env else None`)."""
    if env is None:
        return None
    if len(env) == 0:
        return None
    return {**base, **env}            # the env_merge callee, spelled out


# --- the checks --------------------------------------------------------------

def check_env_merge_axiom(base, overlay):
    """Assert the real merge {**base, **overlay} meets the env_merge Ensures."""
    base_len, overlay_len = len(base), len(overlay)
    result = {**base, **overlay}                       # real callee
    # non-empty result whenever an input is non-empty
    if base_len > 0 or overlay_len > 0:
        assert result, "env_merge axiom unsound: empty merge of %r,%r" % (base, overlay)
    assert result is not None
    # overlay wins
    for k, v in overlay.items():
        assert k in result and result[k] == v, (
            "env_merge axiom unsound: overlay key %r -> %r missing in %r"
            % (k, v, result))
    # base carried through when not overridden
    for k, v in base.items():
        if k not in overlay:
            assert k in result and result[k] == v, (
                "env_merge axiom unsound: base key %r -> %r missing in %r"
                % (k, v, result))
    # no spurious keys
    for k in result:
        assert k in base or k in overlay, (
            "env_merge axiom unsound: spurious key %r in %r" % (k, result))
    # inputs unchanged (lengths preserved)
    assert len(base) == base_len and len(overlay) == overlay_len, (
        "env_merge axiom unsound: input mapping mutated")


def check_normalized_reference(env):
    """Assert deep model == real `env or None`."""
    observed = (env or None)                            # real Python expression
    expected = normalized_environment(dict(env))        # deep model
    assert observed == expected, (
        "normalized_environment deep model unsound on %r: real=%r model=%r"
        % (env, observed, expected))
    # the discriminating clause: empty mapping -> None
    if len(env) == 0:
        assert observed is None and expected is None, (
            "empty mapping must normalise to None, got real=%r model=%r"
            % (observed, expected))


def check_effective_reference(env, base):
    """Assert deep model == real `{**base, **env} if env else None`."""
    observed = ({**base, **env} if env else None)       # real Python expression
    expected = effective_environment(None if env is None else dict(env), dict(base))
    assert observed == expected, (
        "effective_environment deep model unsound on env=%r base=%r: "
        "real=%r model=%r" % (env, base, observed, expected))
    # the discriminating clause: None/empty command mapping -> None (inherit
    # os.environ), never an empty mapping
    if env is None or len(env) == 0:
        assert observed is None and expected is None, (
            "None/empty command mapping must yield None, got real=%r model=%r"
            % (observed, expected))


def _rand_map(rng, max_keys=6, key_space=12):
    n = rng.randint(0, max_keys)
    return {rng.randrange(key_space): rng.randrange(100) for _ in range(n)}


def main():
    # --- boundary cases ----------------------------------------------------
    empties = [{}, dict()]
    smalls = [{1: 10}, {1: 10, 2: 20}, {5: 0}, {0: 0}]
    overlaps_base = {1: 100, 2: 200, 3: 300}

    # env_merge axiom: boundary
    boundary_pairs = [
        ({}, {}), ({}, {1: 1}), ({1: 1}, {}),
        ({1: 1}, {1: 2}),                       # overlay wins on shared key
        (overlaps_base, {2: 999}),              # partial override
        (overlaps_base, {4: 4, 5: 5}),          # disjoint
        ({1: 1, 2: 2}, {1: 1, 2: 2}),           # identical
    ]
    for base, overlay in boundary_pairs:
        check_env_merge_axiom(base, overlay)

    # normalized_environment (A-reference): boundary
    for env in empties + smalls + [overlaps_base]:
        check_normalized_reference(env)

    # effective_environment (A-reference): boundary, incl. the tested env in
    # {None, {}} -> None case (F2P test_runshell_use_environ).
    real_environ = dict(os.environ)             # the real process environment
    base_samples = [{}, {1: 1}, {1: 1, 2: 2}, overlaps_base]
    env_samples = [None, {}, {1: 10}, {2: 20, 3: 30}, {1: 999}]
    for base in base_samples:
        for env in env_samples:
            check_effective_reference(env, base)
    # also against the real os.environ as the base mapping
    osenv = {ord(k[0]) if k else 0: len(v) for k, v in list(real_environ.items())[:8]}
    for env in env_samples:
        check_effective_reference(env, osenv)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(14315)
    for _ in range(20000):
        base = _rand_map(rng)
        overlay = _rand_map(rng)
        check_env_merge_axiom(base, overlay)
        check_normalized_reference(dict(overlay))
        env = None if rng.random() < 0.25 else _rand_map(rng)
        check_effective_reference(env, base)

    print("G-AX OK: env_merge axiom (A-consumed) sound on %d boundary + 20000 "
          "fuzz pairs; normalized_environment / effective_environment deep "
          "models (A-reference) == real Python on boundary + 20000 fuzz inputs "
          "(incl. None/{} -> None)." % len(boundary_pairs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
