"""Twin-artifact model for sphinx-doc__sphinx-8638.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed documentation field renders one entry as a paragraph consisting of a
  *name* token followed by a parenthesised *type* token. Each token is turned
  into an interlinking cross-reference node IF AND ONLY IF the role configured
  for that token slot is present; with no configured role the token is emitted
  as a plain inline text node that links nowhere, and when it does link it
  carries the role it is RENDERED under as its reference kind.

  A configured role is normalised against the token's own target before the
  token links: a slot configured with the type-reference role whose target
  names the null value renders under the fallback object-reference role
  instead, the null value not being a type. Normalisation is the identity in
  every other case — in particular on an absent role, for every target.

  Rendering an entry is a bounded step of the field transformation: the entry
  is always delivered, so every guarantee below is owed on every entry rather
  than only on the ones an implementation gets round to producing.

  The field type used to document attributes / instance variables configures NO
  role for its name token. Therefore the rendered name token of such an entry
  must be a PLAIN inline node (it must NOT become a cross-reference), while its
  type token — whose type-role is present — must be a cross-reference whose
  reference kind equals that type-role NORMALISED against the type target.

A configured role is modelled as an ``int`` role code: ``0`` denotes "no role
configured" (an absent / empty role); any non-zero value denotes a present role
identified by that code. Two role identities are named (``TYPE_ROLE``,
``NULL_ROLE``) because normalisation is defined in terms of them. The only
properties of a role the behaviour depends on are its presence (zero vs
non-zero) and, when present, its identity — both captured by the code. A
rendered token is a minimal node carrying only the two touched fields: whether
it is a cross-reference (``is_xref``) and, when it is, the reference kind it
carries (``reftype``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FieldNode:
    def __init__(self, xref: bool, ref: int) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_xref) and self.is_xref == xref)    # type: ignore
        Ensures(Acc(self.reftype) and self.reftype == ref)     # type: ignore
        self.is_xref = xref
        self.reftype = ref


# axioms-start
# (no unchanged opaque callee is consumed; the token-emission decision, the
#  role normalisation and the field-entry construction are modelled deeply.)
# axioms-end


# pure-start
# Role identities the rendering distinguishes. Code ``0`` is an absent role; a
# non-zero code identifies a present role. Two identities are named because the
# role normalisation below is defined in terms of them.
TYPE_ROLE = 1   # the type-reference role a typed slot is configured with
NULL_ROLE = 2   # the role a token falls back to when its target names the null
                # value (which is not a type)


@Pure
def rendered_role(role: int, target_is_null: bool) -> int:
    """The role a token is actually rendered under.

    A token configured with the type-reference role whose target names the null
    value renders under the fallback role instead; every other configuration —
    an absent role included — renders under exactly its configured role.
    """
    if role == TYPE_ROLE and target_is_null:
        return NULL_ROLE
    return role
# pure-end


def make_xref(role: int) -> FieldNode:
    """Emit the node for one token under the *role* code it renders under.

    With a present role (non-zero code) the token becomes a cross-reference
    carrying that role as its reference kind; with no role (code ``0``) the
    token is a plain inline node that links nowhere. The presence of the role is
    the sole determinant of whether the token links.
    """
    # pre-conditions-start
    # emitting one token is a bounded step of the rendering: the node is always
    # delivered, so the guarantees below are owed on every role.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_xref) and Acc(Result().reftype))
    # a token cross-references exactly when the role it renders under is present
    Ensures(Result().is_xref == (role != 0))
    # the rendered token carries exactly that role as the reference kind: the
    # present role when it links, and the "no role" sentinel (0) otherwise (a
    # plain inline node has no reference kind).
    Ensures(Result().reftype == role)
    # post-conditions-end
    # impl-start
    if role != 0:
        return FieldNode(True, role)
    return FieldNode(False, 0)
    # impl-end


def build_variable_field_entry(type_role: int,
                               type_target_is_null: bool) -> List[FieldNode]:
    # pre-conditions-start
    # the type slot of this field carries a present (type-reference) role
    Requires(type_role != 0)
    # rendering one entry is a bounded step of the transformation: the entry is
    # always delivered, so the guarantees below are owed on every admissible
    # input rather than only on the inputs an implementation chooses to answer.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # the entry has exactly two rendered tokens: the name then the type
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].is_xref) and Acc(Result()[0].reftype))
    Ensures(Acc(Result()[1].is_xref) and Acc(Result()[1].reftype))
    # the NAME token must be a plain inline node — never a cross-reference,
    # and a plain node carries no reference kind (the "no role" sentinel 0)
    Ensures(Result()[0].is_xref is False)
    Ensures(Result()[0].reftype == 0)
    # the TYPE token must be a cross-reference carrying its type-role as
    # NORMALISED against the type target
    Ensures(Result()[1].is_xref is True)
    Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
    # post-conditions-end
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
