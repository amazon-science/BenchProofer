#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8551.

The bundle models ONE step: the construction of the cross-reference node for a
type name appearing in an object's info field (`PyXrefMixin.make_xref`,
`sphinx/domains/python.py:269-284`). Its Lean implementation
(`implementation_makeXref`) builds, for a surrounding namespace context
(`module`, `class`) and an annotation `target`, a node whose attributes are:

    result.refspecific = True
    result.reftarget   = strippedTarget(target)   # target[1:] iff a .|~ sigil
    result.py:module   = ctx.module                # the CHANGED writes (R/I)
    result.py:class    = ctx.cls

This script transliterates that R/I leg into Python (`shadow_make_xref`) and
differential-tests it against an ORACLE: an in-process replica of the POST-PATCH
`make_xref` attribute writes, driven through a real dict-backed `ref_context` so
the `.get('py:module')`/`.get('py:class')` ↔ Option bijection is exercised
against actual dict semantics:

    result = {}
    result['reftarget'] = target              # what super().make_xref sets
    result['refspecific'] = True
    result['py:module'] = ref_context.get('py:module')   # + patch
    result['py:class']  = ref_context.get('py:class')     # + patch
    if target.startswith(('.', '~')):
        result['reftarget'] = target[1:]

The node is encoded as a 4-tuple (refspecific, reftarget, py:module, py:class)
with None for an absent Option, matching the Lean model. We compare the oracle's
node against the shadow's node.

stdlib only; no network, no sphinx import. Pinned seed: 8551 (also in mapping.md).
exit 0 iff zero disagreements.
"""
import sys

SEED = 8551
N = 120_000

# Option String pools (None == Lean `none`). "" included to probe the empty
# string (a present-but-empty key, distinct from a missing key / None).
MODULES = [None, "example", "mod", "mod.submod", "Class", ""]
CLASSES = [None, "Class", "Inner", "example", ""]
# target pool: plain names, dotted names, and .|~-sigil-prefixed names.
TARGETS = [
    "str", "int", "A", "mod.A", "mod.submod.A", "name", "age",
    ".A", "~A", ".mod.A", "~mod.submod.A", ".", "~", "..A", "~~x", "",
]


# --- ORACLE: post-patch make_xref attribute writes, via a real ref_context ---
def oracle_make_xref(module, cls, target):
    ref_context = {}
    if module is not None:
        ref_context['py:module'] = module
    if cls is not None:
        ref_context['py:class'] = cls

    result = {}
    # super().make_xref(...) constructs the pending_xref with reftarget=target
    result['reftarget'] = target
    result['refspecific'] = True
    # the two patched lines:
    result['py:module'] = ref_context.get('py:module')
    result['py:class'] = ref_context.get('py:class')
    if target.startswith(('.', '~')):
        # prefix, result['reftarget'] = target[0], target[1:]
        result['reftarget'] = target[1:]
    return (result['refspecific'], result['reftarget'],
            result['py:module'], result['py:class'])


# --- shadow of implementation_makeXref (the R/I leg) -------------------------
def shadow_make_xref(module, cls, target):
    def has_sigil(t):
        return t.startswith(".") or t.startswith("~")
    def stripped(t):
        return t[1:] if has_sigil(t) else t
    refspecific = True
    reftarget = target
    py_module = module
    py_class = cls
    if has_sigil(target):
        reftarget = stripped(target)
    return (refspecific, reftarget, py_module, py_class)


def disagree(module, cls, target):
    got = oracle_make_xref(module, cls, target)
    want = shadow_make_xref(module, cls, target)
    if got != want:
        return (module, cls, target, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # --- exhaustive over the structured pools ---
    for module in MODULES:
        for cls in CLASSES:
            for target in TARGETS:
                d = disagree(module, cls, target)
                if d:
                    print(f"DISAGREE exhaustive module={d[0]!r} class={d[1]!r} "
                          f"target={d[2]!r}: oracle={d[3]} shadow={d[4]}")
                    print("status=fail")
                    return 1
                checked += 1

    # --- fuzz (pins seed/volume) ---
    rnd = _lcg(SEED)
    for _ in range(N):
        module = MODULES[next(rnd) % len(MODULES)]
        cls = CLASSES[next(rnd) % len(CLASSES)]
        target = TARGETS[next(rnd) % len(TARGETS)]
        d = disagree(module, cls, target)
        if d:
            print(f"DISAGREE fuzz module={d[0]!r} class={d[1]!r} "
                  f"target={d[2]!r}: oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
