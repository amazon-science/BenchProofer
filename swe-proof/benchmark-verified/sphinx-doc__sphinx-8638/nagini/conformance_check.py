#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8638 (nagini).

SHADOW: the executable regions of `model.py`, copied VERBATIM below with only
the contract calls and the `@Pure` decorator removed. Concretely:
`FieldNode.__init__` (its two `Ensures` stripped), the `# pure-start` /
`# pure-end` region (the `TYPE_ROLE` / `NULL_ROLE` role identities and
`rendered_role`, the role normalisation the postcondition of
`build_variable_field_entry` is stated through), `make_xref`'s impl region
(`if role != 0: return FieldNode(True, role) / return FieldNode(False, 0)`), and
`build_variable_field_entry`'s impl region (`name_role = 0; name_node =
make_xref(name_role); type_node = make_xref(rendered_role(type_role,
type_target_is_null)); par = [name_node, type_node]; return par`). No statement
is renamed, reordered, or simplified. The model consumes no `@ContractOnly`
axiom (mapping.md §3: "There is **no consumed `@ContractOnly` axiom** in this
bundle"), and it uses no `PSeq`/`ToSeq` carrier — so no axiom shim and no
sequence shim are needed here; the only carrier bridges are the two in
mapping.md §2 (role code, rendered token).

`rendered_role` is part of the model's spec view, not of an impl region, and it
is diffed here on purpose: it is the leg on which the type token's reference
kind is claimed, so it is the leg that must be refutable against real code.

Note that `name_role = 0` is a LITERAL of the shadow, copied from the impl. It
is the model's claim about the PATCHED repo configuration, and the oracle below
reads that configuration LIVE from the repo rather than restating it — so if
the patch had not been applied (or had removed the wrong keyword), the name
token's real role would be `'obj'` (code != 0) and this check would report a
disagreement. That is the refinement leg G-CONF exists to refute.

ORACLE: the REAL patched repo functions, called — nothing is transliterated.
Per mapping.md §1 the modeled routine is the rendering of one typed
`'variable'` field entry: `sphinx.util.docfields.TypedField.make_field` / its
inner `handle_item` (`sphinx/util/docfields.py:172-204`) driven by the
`'variable'` `PyTypedField` of `PyObject.doc_field_types`
(`sphinx/domains/python.py:352-357` — the lines the gold patch edits). This
script imports `sphinx.domains.python.PyObject` from /testbed (the gate applies
the gold patch before the script runs; the script never applies a patch
itself), reads the live `'variable'` field object out of `doc_field_types`, and
calls its real `make_field`. Two oracle shapes are driven:

  (a) the live field object itself, unmodified — the exact F2P shape
      (`test_info_field_list_var`: `:var int attr:`), typerolename='class';
  (b) a real `PyTypedField('variable', ...)` built by the real class
      (`type(live_field)`), carrying the live field's OWN `rolename` (the
      patched value under test, read from the repo, never hardcoded here) with
      only `typerolename` varied, so the model's `type_role` parameter is
      exercised over many role identities instead of just `'class'`.

Because the field objects are built by the real `PyTypedField` class, the real
`PyTypedField.make_xref` override (`sphinx/domains/python.py:326-333`) is in
the call path on every probe, so the role normalisation the shadow's
`rendered_role` models is exercised by real code and not assumed.

The only stand-ins are the `env` object handed to `make_xref` (a `ref_context`
dict plus a `get_domain` returning a no-op `process_field_xref`). That is
faithful, not a reimplementation: `PythonDomain` does not override
`Domain.process_field_xref`, whose body at this commit is `pass`
(`sphinx/domains/__init__.py:311-315`), and `ref_context` supplies only the
`py:module`/`py:class` attributes `PyXrefMixin.make_xref` copies onto the node
— neither touches the node KIND or `reftype`, the only two observables in the
bridge. Everything under specification runs as unmodified repo code.

TYPE BRIDGE (mapping.md §2, inverted):
  * role: model `int` code -> repo `str`/`None`. Code `0` <-> an absent role
    (`None` / `''`); a non-zero code <-> the pool role string interned to that
    code (a bijection on the pool, so role IDENTITY round-trips). The two role
    identities the normalisation names are pinned to their repo spellings:
    `TYPE_ROLE` <-> `'class'` and `NULL_ROLE` <-> `'obj'` (asserted below, so
    the interning cannot drift out from under the normalisation leg).
    Inverting: the real node's `reftype` string is interned back to its code
    and compared against `FieldNode.reftype`.
  * target: model `bool` `..._is_null` -> repo target `str`. `True` <-> the
    target text is exactly `'None'`, the spelling of the null value;
    `False` <-> any other target. This is the ONLY property of a target the
    rendering observes, and the near-miss targets `'NoneType'`, `'none'`,
    `'None_'` are all probed on the `False` side to pin that.
  * rendered token: repo node -> `FieldNode`. `is_xref` <->
    `isinstance(node, addnodes.pending_xref)`; `reftype` <-> `node['reftype']`
    interned (and `0` for a plain inline node, which carries no reference
    kind).
  * field entry: repo paragraph -> `List[FieldNode]` of length 2. `handle_item`
    lays the paragraph out as [name token(s), Text ' (', type token(s), Text
    ')', Text ' -- ', content]; the check asserts that exact shape, so the
    slot extraction (`children[0]` = name, `children[2]` = type) cannot
    silently drift.

INPUT DOMAIN (kept inside the model's `Requires(type_role != 0)`): the type
role is always a non-empty role string, so its code is non-zero. Targets are
identifier-ish (letters/digits/underscore, non-empty) because `make_xrefs`
splits a target on `[](),`/`or` delimiters into MULTIPLE nodes, and the model's
entry is exactly two tokens. The literal target `'None'` is IN the domain, on
both the name and the type axis, and is probed at every role identity: it is
the target on which the role normalisation is observable, so excluding it would
leave the normalisation leg unrefuted. Both branches of the shadow's
`make_xref` are taken on EVERY entry input (the name token takes the
`role == 0` branch via the live patched `rolename`, the type token takes the
`role != 0` branch), and a third token-level layer diffs the shadow's
`rendered_role`-then-`make_xref` composition directly against the real
`PyTypedField.make_xref` of the live field over falsy (`None`, `''`) and truthy
roles crossed with null / near-miss / ordinary targets, so both the
`role == 0` branch and both sides of the normalisation are pinned against the
real callee independently of the configuration.

INPUT COUNT: 100000+ entry checks — boundary cases first (the F2P shape on the
live field, every pool role identity x every boundary target pair, single-char,
long, and null targets), then seeded fuzz over the same domain (which draws the
`'None'` target deliberately, not just by chance) to fill the count — plus the
token-level layer. Pinned seed: 86380 (recorded in mapping.md § G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + the repo's own sphinx/docutils only.
"""
import json
import random
import string
import sys

SEED = 86380
N_TOTAL = 100_000


# ============================================================================
# SHADOW — model.py's pure + impl regions, verbatim, contracts stripped
# ============================================================================

class FieldNode:
    def __init__(self, xref, ref):
        # (Ensures(Acc(self.is_xref) and self.is_xref == xref) stripped)
        # (Ensures(Acc(self.reftype) and self.reftype == ref) stripped)
        self.is_xref = xref
        self.reftype = ref


# pure-start (verbatim; the @Pure decorator is the only thing stripped)
TYPE_ROLE = 1   # the type-reference role a typed slot is configured with
NULL_ROLE = 2   # the role a token falls back to when its target names the null
                # value (which is not a type)


def rendered_role(role, target_is_null):
    if role == TYPE_ROLE and target_is_null:
        return NULL_ROLE
    return role
# pure-end


def make_xref(role):
    # impl-start
    if role != 0:
        return FieldNode(True, role)
    return FieldNode(False, 0)
    # impl-end


def build_variable_field_entry(type_role, type_target_is_null):
    # impl-start
    # The attribute / instance-variable field configures no role for its name
    # token, so the name slot is built under an absent role (code 0);
    # normalisation is the identity on an absent role, for every name target.
    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par
    # impl-end


# ============================================================================
# TYPE BRIDGE (mapping.md §2)
# ============================================================================

# Role pool: the roles that actually occur in this repo's field configurations
# plus shape variants. Interned to stable non-zero codes; an absent role
# (None / '') is code 0. The map is a bijection on the pool, so role identity
# round-trips through the bridge. The first two entries are pinned so that the
# two identities the normalisation is defined over land on their model codes:
# 'class' -> TYPE_ROLE, 'obj' -> NULL_ROLE.
ROLE_POOL = ["class", "obj", "func", "meth", "attr", "exc", "data", "mod",
             "x", "Obj", "a-very-long-role-name", "0", "False"]
_ROLE_CODE = {r: i + 1 for i, r in enumerate(ROLE_POOL)}

# The normalisation leg is stated over these two identities; if the interning
# ever drifts, the bridge would silently stop testing what the model claims.
assert _ROLE_CODE["class"] == TYPE_ROLE, "bridge drift: 'class' must intern to TYPE_ROLE"
assert _ROLE_CODE["obj"] == NULL_ROLE, "bridge drift: 'obj' must intern to NULL_ROLE"

# The repo spelling of the null value, i.e. the target on which the type role is
# normalised. This is the model's `..._is_null` bool, inverted.
NULL_TARGET = "None"


def role_to_code(role):
    """repo role (str | None)  ->  model int code."""
    if not role:            # None / '' — an absent role, per `if not rolename`
        return 0
    if role not in _ROLE_CODE:
        _ROLE_CODE[role] = len(_ROLE_CODE) + 1
    return _ROLE_CODE[role]


def target_is_null(target):
    """repo target (str) -> the model's `..._is_null` bool."""
    return target == NULL_TARGET


def observe(node, pending_xref):
    """repo rendered token node -> the FieldNode observables (is_xref, reftype)."""
    if isinstance(node, pending_xref):
        return (True, role_to_code(node.get("reftype")))
    return (False, 0)        # a plain inline node carries no reference kind


def shadow_observe(field_node):
    return (field_node.is_xref, field_node.reftype)


# ============================================================================
# ORACLE — the real patched repo functions
# ============================================================================

class _StubDomain:
    """Stands in for PythonDomain only where it is a no-op: the py domain does
    not override Domain.process_field_xref, whose body is `pass`."""

    def process_field_xref(self, refnode):
        pass


class _StubEnv:
    """Supplies exactly what PyXrefMixin.make_xref reads: env.ref_context (for
    the py:module / py:class node attributes) and env.get_domain."""

    def __init__(self):
        self.ref_context = {}

    def get_domain(self, domain):
        return _StubDomain()


def live_variable_field(PyObject):
    """The real 'variable' PyTypedField out of the live (patched) repo config —
    sphinx/domains/python.py:352-357, the lines the gold patch edits."""
    for f in PyObject.doc_field_types:
        if getattr(f, "name", None) == "variable":
            return f
    raise RuntimeError("no 'variable' doc field on PyObject.doc_field_types")


def field_with_type_role(live, type_role):
    """A real PyTypedField for the 'variable' field, built by the REAL class,
    carrying the live (patched) name `rolename` and the given typerolename."""
    kwargs = dict(label=live.label, names=live.names, typenames=live.typenames,
                  typerolename=type_role, can_collapse=live.can_collapse)
    if live.rolename is not None:
        kwargs["rolename"] = live.rolename
    return type(live)("variable", **kwargs)


def oracle_entry(field, env, nodes_mod, name_target, type_target, desc):
    """Call the REAL TypedField.make_field for one 'variable' entry and return
    the two observed tokens, per the mapping.md §2 paragraph bridge."""
    types = {name_target: [nodes_mod.Text(type_target)]}
    items = [(name_target, [nodes_mod.Text(desc)])]
    field_node = field.make_field(types, "py", items, env=env)
    para = field_node[1][0]          # field -> field_body -> collapsed paragraph
    kids = list(para.children)
    # handle_item's layout: name token(s), ' (', type token(s), ')', ' -- ',
    # content. Inside the modeled domain each slot is exactly one node; assert
    # it so the slot extraction cannot silently drift.
    if (len(kids) != 6 or kids[1].astext() != " (" or kids[3].astext() != ")"
            or kids[4].astext() != " -- "):
        raise AssertionError(
            "paragraph shape outside the modeled 2-token entry: %r"
            % ([type(k).__name__ + ":" + k.astext() for k in kids],))
    return kids[0], kids[2]


# ============================================================================
# differential checks
# ============================================================================

def check_entry(field, env, nodes_mod, pending_xref, type_role,
                name_target, type_target, desc, live_used):
    """One entry-level probe: shadow build_variable_field_entry(type_role,
    type_target_is_null) vs the real rendering of the same entry."""
    type_code = role_to_code(type_role)          # bridge: str -> model code
    is_null = target_is_null(type_target)        # bridge: str -> model bool
    shadow = build_variable_field_entry(type_code, is_null)
    real_name, real_type = oracle_entry(field, env, nodes_mod,
                                        name_target, type_target, desc)
    got = [observe(real_name, pending_xref), observe(real_type, pending_xref)]
    want = [shadow_observe(shadow[0]), shadow_observe(shadow[1])]
    if len(shadow) != 2 or got != want:
        return ("DISAGREEMENT (entry)\n"
                "  input: type_role=%r (code %d) name_target=%r "
                "type_target=%r (is_null=%r) desc=%r live_field=%r\n"
                "  shadow (model impl): len=%d %r\n"
                "  oracle (real patched TypedField.make_field): %r\n"
                "  real nodes: name=%s type=%s"
                % (type_role, type_code, name_target, type_target, is_null,
                   desc, live_used, len(shadow), want, got,
                   type(real_name).__name__, type(real_type).__name__))
    return None


def check_token(field, env, addnodes_mod, pending_xref, role, target):
    """One token-level probe: the shadow's rendered_role-then-make_xref
    composition vs the real make_xref of the live 'variable' PyTypedField.

    This pins BOTH the `role == 0` branch (an absent role must not link) and
    both sides of the role normalisation (the type-reference role gives way to
    the fallback role on the null target only) against real code, independently
    of the field configuration."""
    code = role_to_code(role)
    is_null = target_is_null(target)
    shadow = make_xref(rendered_role(code, is_null))
    real = field.make_xref(role, "py", target,
                           innernode=addnodes_mod.literal_strong, env=env)
    got = observe(real, pending_xref)
    want = shadow_observe(shadow)
    if got != want:
        return ("DISAGREEMENT (token)\n"
                "  input: role=%r (code %d) target=%r (is_null=%r)\n"
                "  shadow (model rendered_role + make_xref): %r\n"
                "  oracle (real PyTypedField.make_xref): %r (node %s)"
                % (role, code, target, is_null, want, got,
                   type(real).__name__))
    return None


BOUNDARY_NAMES = ["attr", "a", "somename", "value_2", "X", "None",
                  "a_very_long_attribute_name_indeed"]
# 'None' is the target the role normalisation is observable on and is IN the
# domain; 'NoneType', 'none' and 'None_' are the near misses that must NOT
# normalise, so the bridge's `target == 'None'` cannot be loosened.
BOUNDARY_TYPES = ["int", "T", "Foo", "bool", "MyClass", "None",
                  "NoneType", "none", "None_",
                  "a_very_long_type_name_indeed"]
BOUNDARY_DESCS = ["blah blah", "", "desc"]
TOKEN_TARGETS = BOUNDARY_NAMES + ["NoneType", "none", "None_"]
ALPHABET = string.ascii_letters + string.digits + "_"


def main():
    # REAL repo symbols (mapping.md §1), imported from the patched /testbed.
    from docutils import nodes as nodes_mod
    from sphinx import addnodes as addnodes_mod
    from sphinx.domains.python import PyObject

    pending_xref = addnodes_mod.pending_xref
    env = _StubEnv()
    live = live_variable_field(PyObject)

    # cache the real field objects (one per type role identity)
    fields = {}

    def field_for(type_role):
        if type_role not in fields:
            fields[type_role] = field_with_type_role(live, type_role)
        return fields[type_role]

    checked = 0
    n_boundary = 0

    # ---- token layer: the role == 0 branch and BOTH sides of the role
    #      normalisation, against the real PyTypedField.make_xref ------------
    n_token = 0
    for role in [None, ""] + ROLE_POOL:
        for target in TOKEN_TARGETS:
            err = check_token(live, env, addnodes_mod, pending_xref,
                              role, target)
            if err:
                print(err)
                return 1
            n_token += 1
            checked += 1

    # ---- boundary layer ----------------------------------------------------
    # (1) the exact F2P shape on the LIVE field object, unmodified.
    err = check_entry(live, env, nodes_mod, pending_xref, live.typerolename,
                      "attr", "int", "blah blah", True)
    if err:
        print(err)
        return 1
    checked += 1
    n_boundary += 1

    # (1b) the same LIVE field object on the null type target — the input on
    #      which the type role is normalised (`:vartype: None`).
    err = check_entry(live, env, nodes_mod, pending_xref, live.typerolename,
                      "attr", NULL_TARGET, "blah blah", True)
    if err:
        print(err)
        return 1
    checked += 1
    n_boundary += 1

    # (2) every pool role identity x every boundary target pair x descriptions.
    for type_role in ROLE_POOL:
        fld = field_for(type_role)
        for name_target in BOUNDARY_NAMES:
            for type_target in BOUNDARY_TYPES:
                for desc in BOUNDARY_DESCS:
                    err = check_entry(fld, env, nodes_mod, pending_xref,
                                      type_role, name_target, type_target,
                                      desc, False)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_boundary += 1

    # ---- seeded fuzz over the same domain, filling the count ---------------
    rng = random.Random(SEED)
    n_fuzz = 0
    n_fuzz_null = 0
    while checked < N_TOTAL:
        type_role = rng.choice(ROLE_POOL)
        # use the live field object itself when the role matches its own
        # (identical configuration; keeps the real object in the rotation)
        use_live = (type_role == live.typerolename and rng.random() < 0.5)
        fld = live if use_live else field_for(type_role)
        name_target = "".join(rng.choice(ALPHABET)
                              for _ in range(rng.randint(1, 16)))
        type_target = "".join(rng.choice(ALPHABET)
                              for _ in range(rng.randint(1, 16)))
        # Deliberately draw the null target and its near misses often enough
        # that the normalisation leg is fuzzed, not merely stumbled upon: a
        # random identifier is essentially never exactly 'None'.
        roll = rng.random()
        if roll < 0.10:
            type_target = NULL_TARGET
            n_fuzz_null += 1
        elif roll < 0.13:
            type_target = rng.choice(["NoneType", "none", "None_"])
        if rng.random() < 0.05:
            name_target = NULL_TARGET
        desc = rng.choice(BOUNDARY_DESCS + ["a b c", "x" * 40])
        err = check_entry(fld, env, nodes_mod, pending_xref, type_role,
                          name_target, type_target, desc, use_live)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow of model.py's pure + impl regions "
          "(rendered_role / build_variable_field_entry / make_xref, contracts "
          "stripped) == the REAL patched TypedField.make_field for the live "
          "'variable' PyTypedField (rolename=%r, read from the patched repo), "
          "role normalisation included, on %d inputs (%d boundary entries + "
          "%d fuzz entries of which %d on the null type target + %d make_xref "
          "tokens, seed %d); 0 disagreements."
          % (live.rolename, checked, n_boundary, n_fuzz, n_fuzz_null, n_token,
             SEED))
    print(json.dumps({"checked": checked, "boundary": n_boundary,
                      "fuzz": n_fuzz, "fuzz_null_target": n_fuzz_null,
                      "tokens": n_token,
                      "disagreements": 0, "seed": SEED,
                      "live_name_rolename": live.rolename,
                      "oracle": "real sphinx.util.docfields.TypedField."
                                "make_field via the live 'variable' "
                                "PyTypedField (called, not transliterated); "
                                "real PyTypedField.make_xref in the path, so "
                                "the role normalisation is exercised",
                      "shadow": "direct (contract-stripped pure + impl "
                                "regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
