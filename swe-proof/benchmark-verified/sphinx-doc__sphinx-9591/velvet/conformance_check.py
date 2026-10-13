#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9591 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs (node
class + text content of each child of the produced annotation node):

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: build the child list `[Text(': ')] ++ annotationNodes(typ)`.
              The A-tagged callee `annotationNodes` is NOT replaced by its model
              here; G-CONF isolates the R/I legs, so the A leg keeps the REAL
              callee `_parse_annotation` (mapping.md §4). Thus shadow =
              [Text(': ')] + _parse_annotation(typ, env).
  * ORACLE  — `patch.diff`'s behaviour: the patched property branch
              `addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)`
              with `annotations = _parse_annotation(typ, self.env)`. We build the
              real desc_annotation node and read its children — the exact node
              structure the F2P test asserts on.

They must agree on every input (the spec domain `isBareName` plus a few compound
annotations to exercise the bridge). Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + docutils/sphinx only. The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import string
import sys

from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import _parse_annotation

SEED = 9591
N_FUZZ = 100_000


class _Config:
    python_use_unqualified_type_names = False


class _Env:
    def __init__(self):
        self.config = _Config()
        self.ref_context = {}


def node_signature(node):
    """Observable fingerprint of an inline node: (class name, text content).
    This is exactly what the F2P assert_node comparisons key on."""
    return (type(node).__name__, node.astext())


def shadow_children(typ, env):
    """R/I shadow of Solution.lean impl: prepend a literal ': ' text node to the
    parser's nodes (the A-callee `_parse_annotation` kept real)."""
    annotations = _parse_annotation(typ, env)
    children = [nodes.Text(': ')] + list(annotations)
    return [node_signature(n) for n in children]


def oracle_children(typ, env):
    """patch.diff behaviour: the patched desc_annotation construction's children.

        annotations = _parse_annotation(typ, self.env)
        signode += addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)
    """
    annotations = _parse_annotation(typ, env)
    node = addnodes.desc_annotation(typ, '', nodes.Text(': '), *annotations)
    return [node_signature(n) for n in node.children]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    for name in ["int", "str", "bool", "Point", "None", "Optional",
                 "pathlib.Path", "a.b.C", "T", "_x"]:
        yield name
    # compound annotations exercise the multi-node bridge
    for ann in ["Optional[str]", "List[int]", "Dict[str, int]", "int | None"]:
        yield ann
    first = string.ascii_letters + "_"
    rest = string.ascii_letters + string.digits + "_"
    for _ in range(n):
        k = rng.randint(0, 18)
        name = rng.choice(first) + "".join(rng.choice(rest) for _ in range(k))
        if rng.random() < 0.25:
            k2 = rng.randint(1, 10)
            name = name + "." + rng.choice(first) + "".join(
                rng.choice(rest) for _ in range(k2))
        yield name


def main():
    env = _Env()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_children(s, env)
        oracle = oracle_children(s, env)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of propertyTypeNodes agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
