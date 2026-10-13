#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8459 (nagini).

SHADOW: the impl region of model.py's `record_annotations`, copied verbatim
below with the contract calls stripped (the single `Requires` line inside the
@Pure helper `resolve` is dropped; the impl region itself contains no contract
calls). The @Pure helpers `KEY_RETURN`, `expand`, `resolve` copy over as plain
functions. There are no @ContractOnly callees in this bundle (no consumed
axioms; `resolve`/`expand` are the deep model, validated separately by G-AX).

ORACLE: the REAL repo function the model models per mapping.md section 1 —
`sphinx.ext.autodoc.typehints.record_typehints`. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the module
importable. The function is driven directly with a minimal app object carrying
the configured alias map and a fresh per-object store; the oracle output is
the per-object annotation mapping it populates for the documented callable.

Type bridge (mapping.md section 2): parameter names and annotation strings are
interned as int tokens. Per trial each distinct annotation source string s
gets a token tok(s); the shadow's `expand(tok) == tok + 1000` slot decodes to
the rendered underlying expansion of s (known by construction of the test
module: an alias name defined as a builtin renders to that builtin's name; a
bare builtin source is its own expansion). Name tokens: param0 -> 1,
param1 -> 2, the reserved return slot -> KEY_RETURN() == -1 <-> the literal
'return' key. The shadow's token dict is decoded back to a str->str mapping
and compared for equality against the oracle's recorded mapping.

Input domain (the Requires + mapping.md scoping): callables with exactly two
distinctly named parameters (each optionally annotated) and an optional return
annotation, PEP 563 string annotations, sources drawn from module-level alias
names and builtin type names; the alias map holds name-preserving (self-alias)
entries only — the scope mapping.md section 3.1 documents for the
`aliases[tok] == recorded` carrier — plus decoy entries governing no source.
Both resolution branches are exercised: map governs the source (alias
preserved) and map does not (underlying expansion recorded).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials over a
pool of generated callables x random alias maps. Pinned fuzz seed: 8459.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib-only imports (plus the repo under test).
"""
import json
import keyword
import random
import sys
import types

SEED = 8459
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ---------------------------

def KEY_RETURN():
    # The reserved name slot under which the return annotation is recorded.
    return -1


def expand(tok):
    # The underlying expansion of an annotation source token when NO alias
    # governs it.
    return tok + 1000


def resolve(tok, aliases):
    # The recorded annotation token for one source token under the alias map:
    # the alias's target when the map governs the token, otherwise the token's
    # own underlying expansion.
    if tok in aliases:
        return aliases[tok]
    return expand(tok)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def record_annotations(name0, raw0, has0,
                       name1, raw1, has1,
                       aliases,
                       ret_raw, ret_has):
    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation


# --- oracle plumbing -----------------------------------------------------------

class _NS:
    pass


BUILTINS = ["int", "str", "float", "bool", "list", "dict", "bytes",
            "tuple", "complex", "frozenset", "set"]


def build_fn(alias_defs, params, ret_src):
    """Build a module with PEP 563 string annotations, module-level alias
    definitions `<name> = <builtin>`, and a function with exactly the given
    two parameters (annotated or not) and optional return annotation."""
    lines = ["from __future__ import annotations"]
    for a, u in alias_defs:
        lines.append("%s = %s" % (a, u))
    sig = ", ".join(p if s is None else "%s: %s" % (p, s) for p, s in params)
    ret = "" if ret_src is None else " -> %s" % ret_src
    lines.append("def fn(%s)%s:" % (sig, ret))
    lines.append("    return None")
    mod = types.ModuleType("conf_target")
    exec(compile("\n".join(lines), "conf_target", "exec"), mod.__dict__)
    return mod.__dict__["fn"]


def real_recorded(record_typehints, fn, alias_map):
    """Drive the REAL function with a minimal app carrying the configured
    alias map and a fresh per-object store; return the recorded mapping."""
    app = _NS()
    app.config = _NS()
    app.config.autodoc_type_aliases = alias_map
    app.env = _NS()
    app.env.temp_data = {}
    record_typehints(app, "function", "t.fn", fn, {}, None, None)
    rec = app.env.temp_data.get("annotations", {}).get("t.fn", {})
    return dict(rec)


class Config:
    """One callable configuration: alias definitions, two parameter slots,
    optional return source, plus the prebuilt function object."""

    def __init__(self, alias_defs, params, ret_src):
        self.alias_defs = alias_defs          # [(alias_name, builtin_src)]
        self.params = params                  # [(pname, src_or_None)] * 2
        self.ret_src = ret_src                # src or None
        self.fn = build_fn(alias_defs, params, ret_src)
        # rendered underlying expansion of each usable source string
        self.expansion = {u: u for u in BUILTINS}
        for a, u in alias_defs:
            self.expansion[a] = u

    def sources(self):
        srcs = [s for _, s in self.params if s is not None]
        if self.ret_src is not None:
            srcs.append(self.ret_src)
        return srcs


def check_config(record_typehints, cfg, alias_names, decoys, tier):
    """Diff shadow vs real on one (callable, alias map) trial. `alias_names`
    are the self-aliased map keys; `decoys` are map keys governing no source.
    Returns an error string on disagreement, else None."""
    alias_map = {a: a for a in alias_names}
    for d in decoys:
        alias_map[d] = d

    # --- token interning (the mapping.md section 2 bridge) -------------------
    (n0, src0), (n1, src1) = cfg.params
    tok = {}
    rev = {}
    next_tok = [10]

    def intern(s):
        if s not in tok:
            t = next_tok[0]
            next_tok[0] += 1
            tok[s] = t
            rev[t] = s
            rev[t + 1000] = cfg.expansion.get(s, s)
        return tok[s]

    for s in cfg.sources():
        intern(s)
    aliases_tok = {}
    for k, v in alias_map.items():
        aliases_tok[intern(k)] = intern(v)

    # Requires: distinct name tokens, none equal to the reserved return slot.
    name_tok = {n0: 1, n1: 2}
    has0 = src0 is not None
    has1 = src1 is not None
    ret_has = cfg.ret_src is not None
    raw0 = tok[src0] if has0 else 0
    raw1 = tok[src1] if has1 else 0
    ret_raw = tok[cfg.ret_src] if ret_has else 0

    # --- shadow, decoded back to strings --------------------------------------
    shadow_tok = record_annotations(1, raw0, has0, 2, raw1, has1,
                                    aliases_tok, ret_raw, ret_has)
    name_str = {1: n0, 2: n1, KEY_RETURN(): "return"}
    shadow = {name_str[k]: rev[v] for k, v in shadow_tok.items()}

    # --- real ------------------------------------------------------------------
    real = real_recorded(record_typehints, cfg.fn, alias_map)

    if shadow != real:
        return ("DISAGREEMENT (%s)\n"
                "  callable: aliases_defined=%r params=%r ret=%r\n"
                "  alias_map=%r\n"
                "  shadow=%r\n"
                "  real  =%r"
                % (tier, cfg.alias_defs, cfg.params, cfg.ret_src,
                   alias_map, shadow, real))
    return None


def boundary_trials():
    """(config, self-aliased names, decoys) triples: the documented shapes
    plus branch/absence corners."""
    trials = []

    # the tested callable's exact shape: both branches
    c = Config([("myint", "int")], [("x", "myint"), ("y", "myint")], "myint")
    trials.append((c, ["myint"], []))
    trials.append((c, [], []))

    # the issue reproducer's alias-name shape
    c = Config([("JSONObject", "dict")], [("data", "JSONObject"), ("k", "str")],
               "JSONObject")
    trials.append((c, ["JSONObject"], []))
    trials.append((c, [], []))

    # unannotated slots: one, the other, both; return absent
    c = Config([("A", "float")], [("p", "A"), ("q", None)], "str")
    trials.append((c, ["A"], []))
    trials.append((c, [], []))
    c = Config([("A", "list")], [("p", None), ("q", "A")], None)
    trials.append((c, ["A"], []))
    c = Config([], [("p", None), ("q", None)], None)
    trials.append((c, [], []))
    c = Config([], [("p", None), ("q", None)], "int")
    trials.append((c, [], []))

    # map governs only some sources; two aliases, one governed
    c = Config([("A", "float"), ("B", "list")], [("p", "B"), ("q", "A")], "B")
    trials.append((c, ["A"], []))
    trials.append((c, ["B"], []))
    trials.append((c, ["A", "B"], []))

    # a builtin source self-aliased (source is its own underlying form)
    c = Config([], [("p", "int"), ("q", "str")], "int")
    trials.append((c, ["int"], []))
    trials.append((c, [], []))

    # decoy map entries governing no source
    c = Config([("A", "dict")], [("p", "A"), ("q", "int")], None)
    trials.append((c, [], ["Unused", "AlsoUnused"]))
    trials.append((c, ["A"], ["Unused"]))

    # both params share one annotation source
    c = Config([("Sh", "bytes")], [("p", "Sh"), ("q", "Sh")], None)
    trials.append((c, ["Sh"], []))
    trials.append((c, [], []))

    return trials


def make_pool(rng, n):
    """Prebuild n random callable configurations."""
    letters = "abcdefghijklmnopqrstuvwxyz"

    def fresh_name(prefix, seen):
        while True:
            s = prefix + "".join(rng.choice(letters)
                                 for _ in range(rng.randint(2, 8)))
            if s not in seen and not keyword.iskeyword(s):
                seen.add(s)
                return s

    pool = []
    for _ in range(n):
        seen = set(BUILTINS) | {"return", "fn"}
        alias_defs = [(fresh_name("Al", seen), rng.choice(BUILTINS))
                      for _ in range(rng.randint(1, 3))]
        alias_names = [a for a, _ in alias_defs]

        def pick_src():
            r = rng.random()
            if r < 0.15:
                return None                       # unannotated slot
            if r < 0.75:
                return rng.choice(alias_names)    # aliasable source
            return rng.choice(BUILTINS)           # bare builtin source

        p0 = fresh_name("p", seen)
        p1 = fresh_name("q", seen)
        params = [(p0, pick_src()), (p1, pick_src())]
        ret_src = pick_src()
        pool.append(Config(alias_defs, params, ret_src))
    return pool


def fuzz_trial(rng, cfg):
    """A random name-preserving alias map for cfg: any subset of its alias
    names + occasionally a builtin self-alias or a decoy."""
    alias_names = [a for a, _ in cfg.alias_defs
                   if rng.random() < 0.5]
    if rng.random() < 0.15:
        alias_names.append(rng.choice(BUILTINS))
    decoys = []
    if rng.random() < 0.2:
        decoys.append("Decoy" + str(rng.randint(0, 999)))
    return alias_names, decoys


def main():
    from sphinx.ext.autodoc.typehints import record_typehints  # REAL patched

    checked = 0
    n_boundary = 0
    for cfg, alias_names, decoys in boundary_trials():
        err = check_config(record_typehints, cfg, alias_names, decoys,
                           "boundary")
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    pool = make_pool(rng, 400)
    for _ in range(N_FUZZ):
        cfg = rng.choice(pool)
        alias_names, decoys = fuzz_trial(rng, cfg)
        err = check_config(record_typehints, cfg, alias_names, decoys, "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real recorded annotation mapping on "
          "%d inputs (%d boundary + %d fuzz over a 400-callable pool, "
          "seed %d)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
