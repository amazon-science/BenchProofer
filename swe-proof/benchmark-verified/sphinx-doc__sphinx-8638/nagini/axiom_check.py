#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8638.

This bundle consumes NO @ContractOnly axiom: the token-emission decision, the
role normalisation and the field-entry construction are modelled DEEPLY
(model.py: ``make_xref``, ``rendered_role`` and ``build_variable_field_entry``).
This check therefore validates the A-REFERENCE deep models against the REAL repo
callees, exactly as G-AX/G-EQ require:

  (1) ``make_xref(role)`` (model) == ``Field.make_xref(rolename, ...)`` (real):
      the rendered token is a cross-reference (a ``pending_xref`` node) IF AND
      ONLY IF the configured role is present (a truthy ``rolename``), and when it
      is, the cross-reference's ``reftype`` equals that role. With a falsy
      ``rolename`` the token is a plain inline node (NOT a ``pending_xref``).

  (2) ``rendered_role(role, target_is_null)`` (model) == the role the REAL
      ``PyTypedField.make_xref`` actually renders a token under: the
      type-reference role ``'class'`` on the target ``'None'`` gives way to the
      fallback object role ``'obj'``; every other (role, target) pair renders
      under the configured role unchanged — including the near-miss targets
      ``'NoneType'`` / ``'none'`` / ``'None_'`` and including an absent role on
      the target ``'None'``.

  (3) ``build_variable_field_entry(type_role, type_target_is_null)`` (model) ==
      the real rendering of a typed variable field (``:var int attr:`` and
      ``:vartype: None``) under the POST-PATCH configuration of
      ``PyObject.doc_field_types`` (the ``'variable'`` ``PyTypedField`` with NO
      ``rolename``): the NAME token is a plain ``literal_strong`` (no
      ``pending_xref``) while the TYPE token is a ``pending_xref`` carrying the
      type-role as NORMALISED against the type target.

Run inside the official SWE-bench container for the instance (post-patch tree),
where ``sphinx`` is importable. Layer (1) pins the core node-kind decision via
the real ``Field.make_xref``; layer (2) pins the normalisation via the real
``PyTypedField.make_xref``; layer (3) drives the real ``TypedField.make_field``
over the ``'variable'`` field configuration built by the REAL ``PyTypedField``
class (post-patch, no ``rolename``; and pre-patch ``rolename='obj'`` to confirm
the model discriminates), so the normalisation override is in the call path
rather than bypassed. No layer needs a full Sphinx app.

Imports are limited to the standard library plus the repo's own ``sphinx`` (the
very package whose behaviour the deep model abstracts). Exit 0 iff every
observation matches the model.
"""
import sys

# The model's named role identities, in their repo spellings (mapping.md §2).
TYPE_ROLE_STR = "class"   # model TYPE_ROLE — the configured type-reference role
NULL_ROLE_STR = "obj"     # model NULL_ROLE — the fallback role
NULL_TARGET = "None"      # the target text the model's `..._is_null` bool means


def model_rendered_role(role, target_is_null):
    """model.py's `rendered_role`, transliterated on the repo's role spellings
    (code 0 <-> a falsy role). This is the claim under test in layer (2)."""
    if role == TYPE_ROLE_STR and target_is_null:
        return NULL_ROLE_STR
    return role


def check_make_xref():
    """Layer (1): real Field.make_xref vs the model's make_xref decision."""
    from sphinx import addnodes
    from sphinx.util.docfields import Field

    fld = Field(name="variable")
    domain = "py"

    # Role inputs spanning the truthiness boundary the model's `role != 0` codes:
    #   falsy rolenames  -> code 0   -> NOT a cross-reference (plain inline)
    #   truthy rolenames -> code !=0 -> a cross-reference with reftype == role
    falsy_roles = [None, ""]
    truthy_roles = ["obj", "class", "data", "func", "meth", "attr", "exc",
                    "x", "a-very-long-role-name", "Obj", "0", "False"]

    n_obs = 0
    for role in falsy_roles:
        # No env => make_xref does not call process_field_xref; this isolates the
        # node-kind decision exactly as the model abstracts it.
        node = fld.make_xref(role, domain, "attr", innernode=addnodes.literal_strong)
        is_xref = isinstance(node, addnodes.pending_xref)
        assert not is_xref, (
            "REAL Field.make_xref(%r) produced a cross-reference; the model "
            "requires a plain inline node for an absent role" % (role,))
        n_obs += 1

    for role in truthy_roles:
        node = fld.make_xref(role, domain, "attr", innernode=addnodes.literal_strong)
        is_xref = isinstance(node, addnodes.pending_xref)
        assert is_xref, (
            "REAL Field.make_xref(%r) produced a plain node; the model requires "
            "a cross-reference for a present role" % (role,))
        # the cross-reference carries exactly the configured role as its reftype
        assert node["reftype"] == role, (
            "REAL Field.make_xref(%r) cross-reference reftype=%r != role"
            % (role, node.get("reftype")))
        n_obs += 1

    print("G-AX OK [1/3]: make_xref deep model == real Field.make_xref over %d "
          "role observations (links iff role present; reftype == role)." % n_obs)
    return n_obs


class _StubDomain:
    """Stands in for PythonDomain only where it is a no-op: the py domain does
    not override Domain.process_field_xref, whose body is `pass`."""

    def process_field_xref(self, refnode):
        pass


class _StubEnv:
    """Supplies exactly what PyXrefMixin.make_xref reads: env.ref_context and
    env.get_domain. Neither touches the node kind or reftype."""

    def __init__(self):
        self.ref_context = {}

    def get_domain(self, domain):
        return _StubDomain()


def _variable_field(rolename, typerolename="class"):
    """The 'variable' field built by the REAL PyTypedField class, so the real
    PyTypedField.make_xref override is in the call path. Post-patch passes NO
    rolename; pre-patch passes rolename='obj'."""
    from sphinx.domains.python import PyTypedField

    kwargs = dict(label="Variables", names=("var", "ivar", "cvar"),
                  typerolename=typerolename, typenames=("vartype",),
                  can_collapse=True)
    if rolename is not None:
        kwargs["rolename"] = rolename
    return PyTypedField("variable", **kwargs)


def check_rendered_role():
    """Layer (2): real PyTypedField.make_xref vs the model's rendered_role.

    The observation is the role the token is RENDERED under, read back off the
    node: a cross-reference's `reftype`, or "no role" for a plain inline node.
    """
    from sphinx import addnodes

    fld = _variable_field(rolename=None)
    env = _StubEnv()

    roles = [None, "", "class", "obj", "func", "meth", "attr", "exc", "data",
             "mod", "x", "Obj", "0", "False"]
    # 'None' is the null target; the rest are ordinary targets, three of them
    # deliberate near misses so the model's exact-match test cannot be loosened.
    targets = [NULL_TARGET, "NoneType", "none", "None_", "int", "T", "Foo",
               "bool", "MyClass", "attr"]

    n_obs = 0
    n_normalised = 0
    for role in roles:
        for target in targets:
            node = fld.make_xref(role, "py", target,
                                 innernode=addnodes.literal_strong, env=env)
            if isinstance(node, addnodes.pending_xref):
                real_role = node.get("reftype")
            else:
                real_role = None if not role else "<plain>"
            want = model_rendered_role(role, target == NULL_TARGET)
            if not role:
                # an absent role renders no reference kind at all; the model
                # says normalisation is the identity here, for every target
                assert not isinstance(node, addnodes.pending_xref), (
                    "REAL PyTypedField.make_xref(%r, target=%r) linked on an "
                    "absent role; the model requires a plain inline node"
                    % (role, target))
                assert want == role, (
                    "model normalises an absent role %r on target %r to %r; the "
                    "real callee has nothing to normalise" % (role, target, want))
            else:
                assert real_role == want, (
                    "REAL PyTypedField.make_xref(role=%r, target=%r) rendered "
                    "under %r but the model's rendered_role says %r"
                    % (role, target, real_role, want))
                if want != role:
                    n_normalised += 1
            n_obs += 1

    assert n_normalised == 1, (
        "expected exactly one normalising (role, target) pair among the probes "
        "(the type-reference role on the null target); saw %d" % (n_normalised,))

    print("G-AX OK [2/3]: rendered_role deep model == real "
          "PyTypedField.make_xref over %d (role, target) observations — the "
          "type-reference role %r on target %r renders under %r, every other "
          "pair (near-miss targets and an absent role included) renders "
          "unchanged." % (n_obs, TYPE_ROLE_STR, NULL_TARGET, NULL_ROLE_STR))
    return n_obs


def _render_variable_field(rolename, type_target="int"):
    """Drive the REAL TypedField.make_field for the 'variable' field config with
    the given name *rolename* and type target, returning (name_node,
    type_xrefs)."""
    from docutils import nodes
    from sphinx import addnodes

    fld = _variable_field(rolename)
    out = fld.make_field({"attr": [nodes.Text(type_target)]}, "py",
                         [("attr", [nodes.Text("blah blah")])],
                         env=_StubEnv())
    para = out[1][0]  # field_body -> (collapsed single) paragraph
    name_node = list(para.children)[0]
    type_xrefs = list(para.traverse(addnodes.pending_xref))
    return name_node, type_xrefs


def check_variable_field_end_to_end():
    """Layer (3): real TypedField.make_field for the 'variable' field config."""
    try:
        from sphinx import addnodes
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP [3/3]: sphinx not importable: %r" % (exc,))
        return True

    # (3a) POST-PATCH config (no rolename), ordinary type target — the behaviour
    #      build_variable_field_entry models with type_target_is_null False:
    #      NAME plain literal_strong, TYPE a pending_xref under the type-role.
    name_node, type_xrefs = _render_variable_field(rolename=None)
    assert isinstance(name_node, addnodes.literal_strong), (
        "post-patch variable NAME token is %r, expected a plain literal_strong"
        % (type(name_node).__name__,))
    assert not isinstance(name_node, addnodes.pending_xref), (
        "post-patch variable NAME token became a cross-reference (the bug)")
    assert name_node.astext() == "attr"
    assert type_xrefs, "variable TYPE token did not become a cross-reference"
    assert type_xrefs[0].get("reftype") == model_rendered_role(
        TYPE_ROLE_STR, False), (
        "variable TYPE cross-reference reftype=%r != the normalised type-role %r"
        % (type_xrefs[0].get("reftype"),
           model_rendered_role(TYPE_ROLE_STR, False)))
    assert type_xrefs[0].astext() == "int"

    # (3b) POST-PATCH config, NULL type target (`:vartype: None`) — the model's
    #      type_target_is_null True. The NAME token must still be plain, and the
    #      TYPE token must link under the NORMALISED role, not the configured
    #      one. This is the input on which a postcondition pinning the configured
    #      type-role unconditionally would contradict the real callee.
    null_name, null_type_xrefs = _render_variable_field(
        rolename=None, type_target=NULL_TARGET)
    assert not isinstance(null_name, addnodes.pending_xref), (
        "post-patch variable NAME token linked on the null type target")
    assert null_type_xrefs, (
        "variable TYPE token did not cross-reference on the null target")
    want_null = model_rendered_role(TYPE_ROLE_STR, True)
    assert null_type_xrefs[0].get("reftype") == want_null, (
        "on the null type target the real TYPE cross-reference reftype=%r, but "
        "the model's normalised type-role is %r"
        % (null_type_xrefs[0].get("reftype"), want_null))
    assert want_null != TYPE_ROLE_STR, (
        "the null target must NOT render under the configured type-role; the "
        "model's normalisation has become the identity there")

    # (3c) PRE-PATCH config (rolename='obj') — confirms the model DISCRIMINATES:
    #      the name token then becomes a pending_xref (model_prepatch's failure).
    pre_name, _ = _render_variable_field(rolename="obj")
    assert isinstance(pre_name, addnodes.pending_xref) and \
        pre_name.get("reftype") == "obj", (
        "pre-patch rolename='obj' must make the NAME token a cross-reference; "
        "got %r" % (type(pre_name).__name__,))

    print("G-AX OK [3/3]: real TypedField.make_field on the real PyTypedField — "
          "post-patch 'variable' config (no rolename) renders NAME as a plain "
          "literal_strong and TYPE as a pending_xref under the NORMALISED "
          "type-role (%r on an ordinary target, %r on the null target), "
          "matching build_variable_field_entry; pre-patch rolename='obj' makes "
          "NAME a cross-reference (the bug)."
          % (model_rendered_role(TYPE_ROLE_STR, False), want_null))
    return True


def main():
    try:
        check_make_xref()
    except ImportError as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: sphinx not importable in this environment: %r" % (exc,))
        return 0
    check_rendered_role()
    check_variable_field_end_to_end()
    print("G-AX OK: deep models (make_xref, rendered_role, "
          "build_variable_field_entry) sound against the real sphinx docfields "
          "/ python-domain rendering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
