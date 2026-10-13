#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8551 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped — the `RefNode` constructor and the
`make_field_ref` body. The @Pure helpers (`suffix_eq`, `member`,
`count_suffix`, `has_ctx_candidate`, `resolve_count`, `first_suffix`,
`resolve_name`) copy over as plain functions on top of a tuple-backed PSeq
shim (len/index/drop/+/==). There are no @ContractOnly callees in this bundle
(the axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md —
`sphinx.domains.python.PyXrefMixin.make_xref`, imported from /testbed (the
gate applies the diff before this script runs; this script never applies any
diff itself). It is driven through `PyField`, which inherits the mixin's
`make_xref` unmodified. The env argument is the one upstream input the
modelled call site threads through (mapping.md site B): a minimal stand-in
carrying only the two things the method reads from it — the current
namespace context mapping and the domain lookup (which returns a REAL
`PythonDomain`, so the field-xref post-processing hook that runs on the node
is the real, unmodified one). The end-to-end resolution observable is also
diffed: the node's recorded attributes are fed to the REAL, unchanged
`PythonDomain.find_obj` in prefer-specific mode (exactly as the resolver
entry point reads them off the node) and compared against the shadow's
`resolve_count` / `resolve_name` on the shadow node's fields.

Type bridge (mapping.md section 2):
  - dotted qualified name str <-> PSeq[int] of segment tokens: each case
    interns its (dot-free) segment strings injectively into ints; a dotted
    name is the join of its segments, so string equality / suffix tests map
    exactly to segment-sequence equality / suffix tests;
  - namespace context Optional[str] <-> Optional[PSeq[int]]: None <-> None,
    a present context string <-> its segment sequence;
  - the registered-objects mapping <-> PSeq[PSeq[int]] of its keys, in the
    same insertion order (the fallback scan iterates that order);
  - the produced node <-> RefNode: its target attribute <-> node.target, the
    prefer-specific marker (present and true) <-> node.specific, the two
    recorded context attributes <-> node.ctx_mod / node.ctx_cls.

Input domain = the model's Requires: a non-None module context whose
module-qualified candidate is registered, the bare target NOT registered, no
class-nested candidate registered when a class context is present, and at
least two registered names ending with the target (so the fallback alone
would be ambiguous). Targets are plain dotted identifiers (no leading
relative-reference punctuation — outside the modelled domain).

>= 1e5 Requires-satisfying inputs: structured boundary cases (the issue
scenario, class context present/absent, multi-segment targets and modules,
many-way ambiguous fallback sets, permuted registry orders) plus 100000 fuzz
cases. Pinned fuzz seed: 85510.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random; no hypothesis needed).
"""
import json
import random
import sys

SEED = 85510
N_FUZZ = 100_000


# --- PSeq shim: pure Viper sequences as plain tuples --------------------------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def drop(self, n):
        return PSeq(*tuple.__getitem__(self, slice(n, None)))

    def take(self, n):
        return PSeq(*tuple.__getitem__(self, slice(None, n)))

    def __add__(self, other):
        return PSeq(*(tuple.__add__(self, tuple(other))))


# --- pure region of model.py, contracts stripped ------------------------------

def suffix_eq(obj, name):
    if len(name) > len(obj):
        return False
    return obj.drop(len(obj) - len(name)) == name


def member(objs, q):
    if len(objs) == 0:
        return False
    if objs[0] == q:
        return True
    return member(objs.drop(1), q)


def count_suffix(objs, name):
    if len(objs) == 0:
        return 0
    rest = count_suffix(objs.drop(1), name)
    if suffix_eq(objs[0], name):
        return 1 + rest
    return rest


def has_ctx_candidate(mod, cls, name, objs):
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return True
    if mod is not None and member(objs, mod + name):
        return True
    return member(objs, name)


def resolve_count(mod, cls, name, objs):
    if has_ctx_candidate(mod, cls, name, objs):
        return 1
    return count_suffix(objs, name)


def first_suffix(objs, name):
    if len(objs) == 0:
        return name
    if suffix_eq(objs[0], name):
        return objs[0]
    return first_suffix(objs.drop(1), name)


def resolve_name(mod, cls, name, objs):
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return mod + cls + name
    if mod is not None and member(objs, mod + name):
        return mod + name
    if member(objs, name):
        return name
    return first_suffix(objs, name)


# --- impl region of model.py, verbatim, contract calls stripped ---------------

class RefNode:
    def __init__(self, target, specific, ctx_mod, ctx_cls):
        self.target = target
        self.specific = specific
        self.ctx_mod = ctx_mod
        self.ctx_cls = ctx_cls


def make_field_ref(target, cur_module, cur_class, objs):
    node = RefNode(target, True, cur_module, cur_class)
    return node


# --- bridge helpers ------------------------------------------------------------

def dotted(segs):
    return ".".join(segs)


def to_pseq(segs, table):
    """Segment strings -> PSeq of interned ints (injective per case)."""
    ids = []
    for s in segs:
        if s not in table:
            table[s] = len(table)
        ids.append(table[s])
    return PSeq(*ids)


class EnvShim:
    """Minimal stand-in for the environment handle the method under test
    reads: the current namespace context mapping plus the domain lookup
    (returning a REAL domain instance, so the node post-processing hook that
    runs during construction is the real one)."""

    def __init__(self, domain_obj, ref_context):
        self.ref_context = ref_context
        self._domain = domain_obj

    def get_domain(self, name):
        return self._domain


def make_domain(PythonDomain, ObjectEntry, object_fullnames):
    """A REAL PythonDomain populated with just what find_obj reads
    (same construction axiom_check.py validated against the resolver)."""
    dom = object.__new__(PythonDomain)
    dom.data = {"objects": {fn: ObjectEntry("index", fn, "class")
                            for fn in object_fullnames}}
    role2type = {}
    for name, ot in PythonDomain.object_types.items():
        for role in ot.roles:
            role2type.setdefault(role, []).append(name)
    dom._role2type = role2type
    dom.objtypes_for_role = role2type.get
    return dom


def requires_hold(target, mod, cls, objs):
    """Mirror of the model's Requires over segment tuples (guards the
    generated input domain)."""
    if mod is None:
        return False
    t = tuple(target)
    if (tuple(mod) + t) not in [tuple(o) for o in objs]:
        return False
    if cls is not None and (tuple(mod) + tuple(cls) + t) in [tuple(o) for o in objs]:
        return False
    if t in [tuple(o) for o in objs]:
        return False
    n_suffix = sum(1 for o in objs
                   if len(o) >= len(t) and tuple(o)[len(o) - len(t):] == t)
    return n_suffix >= 2


# --- one differential probe -----------------------------------------------------

def check_one(sphinx_syms, target, mod, cls, objs):
    """target/mod: tuples of segment strings; cls: tuple or None; objs: list
    of tuples (registry insertion order)."""
    PyField, PythonDomain, ObjectEntry = sphinx_syms

    # --- shadow on the interned-int carrier
    table = {}
    t_ids = to_pseq(target, table)
    m_ids = to_pseq(mod, table)
    c_ids = to_pseq(cls, table) if cls is not None else None
    objs_ids = PSeq(*[to_pseq(o, table) for o in objs])
    node = make_field_ref(t_ids, m_ids, c_ids, objs_ids)
    shadow_count = resolve_count(node.ctx_mod, node.ctx_cls, node.target, objs_ids)
    shadow_name = resolve_name(node.ctx_mod, node.ctx_cls, node.target, objs_ids)

    # --- real: build the node via the patched method under test
    dom = make_domain(PythonDomain, ObjectEntry, [dotted(o) for o in objs])
    env = EnvShim(dom, {"py:module": dotted(mod),
                        "py:class": dotted(cls) if cls is not None else None})
    field = PyField("field")
    result = field.make_xref("class", "py", dotted(target), env=env)

    real_target = result.get("reftarget")
    real_specific = bool(result.hasattr("refspecific") and result["refspecific"])
    real_mod = result.get("py:module")
    real_cls = result.get("py:class")

    # --- end-to-end: feed the node's recorded attributes to the REAL resolver
    # exactly as the resolver entry point reads them off the node
    searchmode = 1 if result.hasattr("refspecific") else 0
    matches = dom.find_obj(None, real_mod, real_cls, real_target,
                           "class", searchmode)
    real_names = sorted(n for n, _ in matches)

    # --- bridge the shadow node back to strings and diff
    inv = {v: k for k, v in table.items()}

    def ids_to_str(seq):
        if seq is None:
            return None
        return dotted([inv[i] for i in seq])

    problems = []
    if ids_to_str(node.target) != real_target:
        problems.append("target: shadow=%r real=%r"
                        % (ids_to_str(node.target), real_target))
    if bool(node.specific) != real_specific:
        problems.append("prefer-specific flag: shadow=%r real=%r"
                        % (node.specific, real_specific))
    if ids_to_str(node.ctx_mod) != real_mod:
        problems.append("module context: shadow=%r real=%r"
                        % (ids_to_str(node.ctx_mod), real_mod))
    if ids_to_str(node.ctx_cls) != real_cls:
        problems.append("class context: shadow=%r real=%r"
                        % (ids_to_str(node.ctx_cls), real_cls))
    if shadow_count != len(real_names):
        problems.append("resolution count: shadow=%d real=%d (%r)"
                        % (shadow_count, len(real_names), real_names))
    elif shadow_count == 1 and real_names != [ids_to_str(shadow_name)]:
        problems.append("resolved name: shadow=%r real=%r"
                        % (ids_to_str(shadow_name), real_names))
    if problems:
        return ("DISAGREEMENT\n  target=%r module=%r class=%r\n  objects=%r\n  %s"
                % (dotted(target), dotted(mod),
                   dotted(cls) if cls is not None else None,
                   [dotted(o) for o in objs], "\n  ".join(problems)))
    return None


# --- input generation -------------------------------------------------------------

def boundary_cases():
    """Structured Requires-satisfying cases."""
    cases = []
    # the issue scenario: same simple name under two sub-namespaces, resolved
    # from the deeper one
    cases.append((("A",), ("mod", "submod"), None,
                  [("mod", "A"), ("mod", "submod", "A")]))
    # same, registry order reversed (fallback scan order differs)
    cases.append((("A",), ("mod", "submod"), None,
                  [("mod", "submod", "A"), ("mod", "A")]))
    # shallow module context
    cases.append((("A",), ("mod",), None,
                  [("mod", "A"), ("pkg", "A")]))
    # class context present, no class-nested candidate registered
    cases.append((("A",), ("mod",), ("C",),
                  [("mod", "A"), ("pkg", "A")]))
    cases.append((("A",), ("mod", "submod"), ("Outer",),
                  [("mod", "submod", "A"), ("mod", "A"), ("x", "A")]))
    # multi-segment target
    cases.append((("sub", "A"), ("mod",), None,
                  [("mod", "sub", "A"), ("pkg", "sub", "A")]))
    cases.append((("sub", "A"), ("mod",), ("C",),
                  [("mod", "sub", "A"), ("pkg", "other", "sub", "A")]))
    # many-way ambiguous fallback set
    cases.append((("A",), ("m1",), None,
                  [("m1", "A"), ("m2", "A"), ("m3", "A"), ("m4", "A")]))
    # noise objects that are not suffix matches
    cases.append((("A",), ("mod",), None,
                  [("mod", "B"), ("mod", "A"), ("pkg", "A"), ("C",)]))
    # deep module path
    cases.append((("A",), ("p", "q", "r"), None,
                  [("p", "q", "r", "A"), ("p", "A")]))
    # class context with a same-named module-level sibling elsewhere
    cases.append((("Name",), ("pkg", "core"), ("Holder",),
                  [("pkg", "core", "Name"), ("pkg", "util", "Name"),
                   ("other", "Name")]))
    # target segment reused inside object prefixes (suffix test must not
    # match mid-name)
    cases.append((("A",), ("A", "mod"), None,
                  [("A", "mod", "A"), ("A", "A")]))
    return cases


def gen_fuzz_case(rng, pool):
    """One random Requires-satisfying case."""
    target = tuple(rng.choice(pool) for _ in range(rng.randint(1, 2)))
    mod = tuple(rng.choice(pool) for _ in range(rng.randint(1, 3)))
    cls = (rng.choice(pool),) if rng.random() < 0.4 else None
    objs = [mod + target]
    # a second, distinct suffix match so the bare fallback is ambiguous
    for _ in range(100):
        prefix = tuple(rng.choice(pool) for _ in range(rng.randint(1, 2)))
        cand = prefix + target
        if cand != mod + target and \
                (cls is None or cand != mod + cls + target):
            objs.append(cand)
            break
    # noise objects (must not violate the Requires)
    for _ in range(rng.randint(0, 4)):
        depth = rng.randint(1, 4)
        cand = tuple(rng.choice(pool) for _ in range(depth))
        if cand == target:
            continue
        if cls is not None and cand == mod + cls + target:
            continue
        objs.append(cand)
    rng.shuffle(objs)
    objs = list(dict.fromkeys(objs))
    return target, mod, cls, objs


def main():
    # REAL repo symbols (the module the model models, per mapping.md)
    from sphinx.domains.python import PyField, PythonDomain, ObjectEntry
    syms = (PyField, PythonDomain, ObjectEntry)

    checked = 0
    n_boundary = 0
    for target, mod, cls, objs in boundary_cases():
        if not requires_hold(target, mod, cls, objs):
            print("INTERNAL: boundary case violates Requires: %r"
                  % ((target, mod, cls, objs),))
            return 2
        err = check_one(syms, target, mod, cls, objs)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    pool = ["mod", "submod", "pkg", "sub", "core", "util",
            "A", "B", "C", "Name", "x", "y"]
    n_fuzz = 0
    while n_fuzz < N_FUZZ:
        target, mod, cls, objs = gen_fuzz_case(rng, pool)
        if not requires_hold(target, mod, cls, objs):
            continue  # rare collision; regenerate
        err = check_one(syms, target, mod, cls, objs)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow impl == real patched field-xref construction "
          "(+ end-to-end prefer-specific resolution) on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
