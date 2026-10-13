#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8551 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildCrossRef`,
              routed through the deep model `scopedRef`/`normalizeTarget`)
              transliterated to Python over the real repo types, via the
              mapping.md bijection (`List Char` ↔ `str`, `ScopeName` ↔
              `Optional[str]`). There are NO A-tagged callees in the impl region
              (no axioms / no `:|` stubs), so the shadow is pure R/I.

  * ORACLE  — patch.diff's behaviour: the REAL patched
              `sphinx.domains.python.PyXrefMixin.make_xref` (resolved from the
              repo at base_commit with the gold patch applied — the harness
              applies patch.diff before this runs). We invoke it through a
              concrete `PyField` instance with a minimal `BuildEnvironment` stub
              that supplies `ref_context` (the current module / current class)
              and a no-op `process_field_xref` domain, then read the produced
              `pending_xref` node's attributes.

Observable of one built cross-reference, per the mapping.md §2 bijection:
  (refdomain, reftype, reftarget, refspecific, py:module, py:class)
matched against the Lean `CrossRef` record
  (refdomain, reftype, reftarget, refspecific, scopeModule, scopeClass).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sphinx
(sphinx is the repo under test). The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 8551
N_FUZZ = 100_000


# --- ORACLE driver: the REAL patched PyXrefMixin.make_xref -------------------

def _make_env(cur_module, cur_class):
    """Minimal BuildEnvironment stand-in. The patched make_xref only reads
    `env.ref_context.get('py:module' / 'py:class')` and, via super().make_xref,
    `env.get_domain(domain).process_field_xref(node)` (a no-op for the py
    domain). We supply exactly that surface."""
    class _StubDomain:
        def process_field_xref(self, pnode):
            return None

    class _StubEnv:
        def __init__(self):
            self.ref_context = {'py:module': cur_module, 'py:class': cur_class}

        def get_domain(self, domain):
            return _StubDomain()

    return _StubEnv()


def oracle_build(cur_module, cur_class, domain, reftype, target):
    """patch.diff's behaviour: build the cross-reference node with the real
    patched make_xref and read back the observable attributes."""
    from sphinx.domains.python import PyField
    field = PyField('param')          # any concrete PyXrefMixin subclass
    env = _make_env(cur_module, cur_class)
    node = field.make_xref(reftype, domain, target, contnode=None, env=env)
    return (
        node.get('refdomain'),
        node.get('reftype'),
        node.get('reftarget'),
        bool(node.get('refspecific')),
        node.get('py:module'),
        node.get('py:class'),
    )


# --- SHADOW: Solution.lean buildCrossRef / scopedRef / normalizeTarget --------

def shadow_normalize_target(target):
    """normalizeTarget (pure region) transliterated: strip a leading '.'/'~'."""
    if target and target[0] in ('.', '~'):
        return target[1:]
    return target


def shadow_normalize_kind(reftype, target):
    """normalizeKind (pure region) transliterated: `None` is not a type, so a
    class-kind reference to the literal target 'None' is built as an
    object-kind reference instead."""
    if reftype == 'class' and target == 'None':
        return 'obj'
    return reftype


def shadow_build(cur_module, cur_class, domain, reftype, target):
    """buildCrossRef -> scopedRef (pure region) transliterated. Returns the same
    6-tuple observable as the oracle."""
    return (
        domain,
        shadow_normalize_kind(reftype, target),
        shadow_normalize_target(target),
        True,
        cur_module,
        cur_class,
    )


# --- fuzzing ------------------------------------------------------------------

def fuzz_inputs(n, rng):
    modules = [None, "", "mod", "mod.submod", "example", "pkg.sub.deep"]
    classes = [None, "", "Class", "A", "Outer.Inner"]
    targets = [
        "", "A", "int", "str", "mod.A", "mod.submod.A",
        ".A", "~mod.A", ".mod.submod.A", "~A", "...", "~", ".",
        "list", "Dict", "a.b.c.D", "~pkg.mod.Cls", ".x",
        "None", ".None", "~None", "mod.None",
    ]
    domains = ["py"]
    reftypes = ["class", "obj", "exc", "func", "data"]

    # boundary: exhaustive cross product of the small carrier sets first
    for m in modules:
        for c in classes:
            for t in targets:
                yield (m, c, "py", "class", t)

    # then randomized re-sampling to exceed the fuzz floor deterministically
    for _ in range(n):
        yield (
            rng.choice(modules),
            rng.choice(classes),
            rng.choice(domains),
            rng.choice(reftypes),
            rng.choice(targets),
        )


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for m, c, domain, reftype, target in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_build(m, c, domain, reftype, target)
        oracle = oracle_build(m, c, domain, reftype, target)
        if shadow != oracle:
            disagreements.append((m, c, domain, reftype, target, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for m, c, dom, rt, t, sh, orc in disagreements:
            print("  module=%r class=%r domain=%r reftype=%r target=%r "
                  "shadow=%r oracle=%r" % (m, c, dom, rt, t, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildCrossRef agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
