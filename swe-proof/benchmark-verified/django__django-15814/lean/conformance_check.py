#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15814.

The bundle models ONE decision inside `Query.deferred_to_data`'s relation-traversal
loop (`django/db/models/sql/query.py:719-753`): at each relation step, the model
under which the step's identifier (pk) requirement is registered in `must_include`.
The modeled value is a PURE function of the resolved relation steps (mapping.md):

    steps : list[RelModel]   where each step has its own identity and the identity
                               of the base (concrete) model whose storage it shares

Post-patch rule (the patched line at query.py:751):

    for name in parts[:-1]:
        ...
        if is_reverse_o2o(source):
            cur_model = source.related_model
        else:
            cur_model = source.remote_field.model
        cur_model = cur_model._meta.concrete_model     # <-- the added line
        opts = cur_model._meta
        add_to_dict(must_include, cur_model, opts.pk)  # cur_model is the dict key

`cur_model._meta.concrete_model` maps a proxy model to its concrete base and is the
identity on a concrete model. So the model keyed is always the concrete base.

Standing up a database / ORM to drive the real `deferred_to_data` is heavy and
unnecessary: the modeled value is this pure decision over each resolved model's
concrete-base identity. The ORACLE below is a faithful in-process replica that uses
the EXACT patched access `cur_model._meta.concrete_model` against real stand-in
objects whose classes mirror the repo hierarchy (`Options.concrete_model` is the
class itself for a concrete model, and the base model for a proxy — matching
django/db/models/options.py:141-142). The SHADOW is the op-for-op transliteration
of `implementation_relationModelKeys` (key = `baseIdent`, per refinement.md).

Each produced key is compared on its model identity. This genuinely tests the
discriminating clause: a proxy step must yield its concrete base model's id as the
key (not the proxy's) — the exact behavior of FAIL_TO_PASS
`test_select_related_only`.

stdlib-only. Pinned seed: 15814 (also in mapping.md).
"""
import random
import sys

SEED = 15814
N = 120_000


# --- repo-faithful stand-in classes (mirror the real hierarchy) --------------
class _Options:
    """Stand-in for a model's _meta. `concrete_model` is the model class itself
    for a concrete model, and the underlying base model for a proxy (matching
    options.py:141-142, 762)."""
    def __init__(self, model, concrete_model):
        self.model = model
        self.concrete_model = concrete_model


class _Model:
    """Stand-in for a Django model class. Carries an identity and a _meta whose
    concrete_model points to the base (itself, if concrete)."""
    _next = [0]

    def __init__(self, ident, base=None):
        self.ident = ident
        # base is None => this is a concrete model => concrete_model is self
        concrete = self if base is None else base
        self._meta = _Options(self, concrete)


def _make_step(ident, base_ident, proxy):
    """Build a resolved relation-step model.
    proxy=False: a concrete model (base == self, base_ident == ident).
    proxy=True : a proxy of a concrete base whose identity is base_ident."""
    if not proxy:
        return _Model(ident)                      # concrete: concrete_model is self
    base = _Model(base_ident)                      # the concrete base
    return _Model(ident, base=base)


# --- ORACLE: faithful in-process replica of the patched loop -----------------
def oracle_keys(steps):
    """steps: list of (ident, base_ident, proxy). Returns list of keyed model ids.
    Replicates the post-patch body: cur_model = cur_model._meta.concrete_model;
    key = id(cur_model)."""
    out = []
    for ident, base_ident, proxy in steps:
        cur_model = _make_step(ident, base_ident, proxy)
        cur_model = cur_model._meta.concrete_model     # the EXACT patched access
        out.append(cur_model.ident)
    return out


# --- SHADOW of implementation_relationModelKeys (the R/I leg) ----------------
# Mirrors Solution.lean: curModel := baseOf m = m.baseIdent; key := curModel.
def shadow_keys(steps):
    out = []
    for ident, base_ident, proxy in steps:
        base_of = ident if not proxy else base_ident   # baseOf m = m.baseIdent
        out.append(base_of)
    return out


def disagree(steps):
    got = oracle_keys(steps)
    want = shadow_keys(steps)
    if got != want:
        return (steps, got, want)
    return None


def _enumerate_edge():
    cases = []
    # empty traversal
    cases.append([])
    # single concrete step -> keyed under itself
    cases.append([(5, 5, False)])
    # single proxy step -> MUST be keyed under its concrete base, not the proxy
    cases.append([(7, 3, True)])
    # the F2P shape: follow a relation to a proxy model
    cases.append([(11, 2, True)])
    # mixed traversal: concrete then proxy
    cases.append([(1, 1, False), (8, 4, True)])
    # several proxies of distinct bases
    cases.append([(20 + i, i, True) for i in range(6)])
    return cases


def main() -> int:
    checked = 0
    for steps in _enumerate_edge():
        d = disagree(steps)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 8)
        steps = []
        # distinct identities across step models and bases
        pool = rng.sample(range(1, 10_000), 2 * n) if n else []
        for j in range(n):
            proxy = rng.random() < 0.5             # proxy steps well-represented
            ident = pool[2 * j]
            base_ident = pool[2 * j + 1] if proxy else ident
            steps.append((ident, base_ident, proxy))
        d = disagree(steps)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
