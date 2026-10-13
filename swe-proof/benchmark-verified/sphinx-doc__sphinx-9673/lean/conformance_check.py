#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_augment
against the patch.diff behaviour of augment_descriptions_with_types.

The impl region is pure control flow over two abstract inputs: the parsed field
markers (each already split into whitespace-separated tokens by the caller's
`re.split(' +', …)`) and the ordered name->type-text table. Every op is I
(identical concrete control flow) modulo the type-only R refinement declared in
refinement.md (Python sets modeled as Lean lists queried by membership; the
appended `nodes.field` objects modeled as `(field_name, text)` pairs; the
`OrderedDict` modeled as an ordered assoc list). The shadow reproduces the
post-patch behaviour op-for-op; we assert zero disagreements vs an independent
reconstruction of the patched function over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 9673
N = 120_000           # >= 10^5


# ---- Lean model (the R/I shadow of implementation_augment) --------------

def join_sp(parts):
    return " ".join(parts)


def shadow_augment(fields, annotations):
    """R/I shadow of implementation_augment. `fields` is a list of token lists;
    `annotations` is an ordered list of (name, ann) pairs. has_desc/has_type are
    lists used as sets (membership only)."""
    has_desc = []
    has_type = []
    for parts in fields:
        p0 = parts[0] if parts else ""
        if p0 == "param":
            if len(parts) == 2:
                has_desc.append(parts[1])
            elif len(parts) > 2:
                name = join_sp(parts[2:])
                has_desc.append(name)
                has_type.append(name)
        elif p0 == "type":
            has_type.append(join_sp(parts[1:]))
        elif p0 == "return" or p0 == "returns":
            has_desc.append("return")
        elif p0 == "rtype":
            has_type.append("return")
    out = []
    for (name, ann) in annotations:
        if name == "return" or name == "returns":
            pass
        elif name in has_desc and name not in has_type:
            out.append(("type " + name, ann))
    # trailing rtype: List.lookup "return"
    ret = None
    for (name, ann) in annotations:
        if name == "return":
            ret = ann
            break
    if ret is not None:
        if "return" in has_desc and "return" not in has_type:
            out.append(("rtype", ret))
    return out


# ---- Independent reconstruction of the patched function -----------------

def patched_augment(fields, annotations):
    """Post-patch augment_descriptions_with_types, faithful to typehints.py.
    `fields` = list of token lists (the result of re.split(' +', field_name));
    `annotations` = OrderedDict modeled as ordered (name, ann) list. Returns the
    ordered list of (field_name, body_text) appended to the field list."""
    has_description = set()
    has_type = set()
    for parts in fields:
        p0 = parts[0] if parts else ""
        if p0 == "param":
            if len(parts) == 2:
                has_description.add(parts[1])
            elif len(parts) > 2:
                name = " ".join(parts[2:])
                has_description.add(name)
                has_type.add(name)
        elif p0 == "type":
            name = " ".join(parts[1:])
            has_type.add(name)
        elif p0 in ("return", "returns"):          # gold hunk 1
            has_description.add("return")
        elif p0 == "rtype":
            has_type.add("return")

    annos = dict(annotations)  # OrderedDict iteration order == insertion order
    out = []
    for name in [n for (n, _) in annotations]:
        if name in ("return", "returns"):          # gold hunk 2
            continue
        if name in has_description and name not in has_type:
            out.append(("type " + name, annos[name]))
    if "return" in annos:
        if "return" in has_description and "return" not in has_type:
            out.append(("rtype", annos["return"]))
    return out


# ---- Fuzz ---------------------------------------------------------------

NAMES = ["x", "y", "param1", "a b", "val", "n", "return", "returns", "self"]
TYPES = ["int", "str", "List[int]", "", "MyClass", "float"]


def rand_marker(rng):
    """A field marker as the caller would split it: a token list with no empty
    tokens (re.split(' +', s) on a stripped non-empty string)."""
    kind = rng.random()
    if kind < 0.30:
        # param forms
        form = rng.randint(1, 3)
        nm = rng.choice(["x", "y", "param1", "val", "n"])
        if form == 1:
            # bare 'param' (len 1) -> falls through both param sub-branches
            return ["param"]
        if form == 2:
            return ["param", nm]
        # len > 2: 'param name extra' -> name = join(parts[2:])
        extra = rng.choice(["t", "type", "x"])
        return ["param", nm, extra]
    if kind < 0.45:
        return ["type", rng.choice(["x", "y", "param1", "val", "n"])]
    if kind < 0.60:
        return ["return"]
    if kind < 0.75:
        return ["returns"]
    if kind < 0.88:
        return ["rtype"]
    # noise / unrecognized marker
    return [rng.choice(["meta", "vartype", "raises", "keyword", "foo"]),
            rng.choice(["a", "b"])]


def rand_annotations(rng):
    n = rng.randint(0, 4)
    seen = set()
    out = []
    for _ in range(n):
        nm = rng.choice(NAMES)
        if nm in seen:        # dict keys are unique
            continue
        seen.add(nm)
        out.append((nm, rng.choice(TYPES)))
    # often include a 'return' annotation (the interesting case)
    if rng.random() < 0.5 and "return" not in seen:
        out.append(("return", rng.choice(TYPES)))
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    for _ in range(N):
        nf = rng.randint(0, 5)
        fields = [rand_marker(rng) for _ in range(nf)]
        annotations = rand_annotations(rng)

        got = shadow_augment(fields, annotations)
        want = patched_augment(fields, annotations)

        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((fields, annotations, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for e in examples:
            print("  ", e)
        return 1

    print(f"G-CONF OK: {N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
