"""Twin-artifact model for django__django-11815.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single enumeration member, used as a default value, is rendered into a
  fragment of importable source code that — when later evaluated — must recover
  the SAME member. The member carries four pieces of text: the dotted module
  path it lives in, the simple class name of its enumeration, its STABLE
  declared identifier (the attribute name under which the member is defined on
  the class), and a renderable form of the mutable payload it currently holds.

  The rendered fragment must reconstruct the member by its STABLE identifier:
  it is the module path, a dot, the class name, then the identifier — quoted as
  a single-quoted string literal — enclosed in subscription brackets. Reading
  the texts as Unicode code-point sequences, the result is

        module ++ "." ++ class_name ++ "[" ++ "'" ++ identifier ++ "'" ++ "]".

  It must NOT be built from the member's mutable payload, because that payload
  may be re-rendered differently later (for example after human-language
  translation of a deferred string) and would then no longer identify any
  member. The single accompanying import statement is the import of the
  member's module, and ONLY that — no further imports derived from rendering
  the payload.

  Rendering is a bounded, straight-line computation: the operation MUST
  terminate and return its two texts (a total-correctness obligation, carried
  as MustTerminate in the precondition).

  Domain: the stable identifier is REQUIRED to be drawn from the simple
  identifier alphabet (ASCII letters, ASCII digits, underscore). Attribute
  names declared in a class body always satisfy this, and on this alphabet
  the single-quote wrap below is exactly the token's canonical rendered form
  (no escaping, no delimiter switch). The specification makes no claim for
  names outside this alphabet (e.g. a name carrying a quote or a backslash,
  constructible only through dynamic construction APIs), whose canonical
  rendering may switch quote style or insert escapes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
quoting of a stable identifier into a single-quoted string literal is the
unchanged repr of a simple identifier token and is modelled deeply as a wrap in
U+0027 quotes, validated == the real callee out-of-band by axiom_check.py
(G-AX); it is not consumed as an axiom. The modeled input domain is scoped to
match: a precondition states that every code point of the stable identifier is
an ASCII letter, digit, or underscore — the shape an attribute name always has,
and exactly the domain on which the single-quote wrap IS the real rendering
(no escaping, no delimiter switch). Texts outside that domain are outside the
modeled slice.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged stdlib operation the
# fragment relies on — wrapping a stable identifier in a single-quoted string
# literal, i.e. repr of a simple identifier token — is modelled DEEPLY by
# `quoted` below and validated == the real callee by axiom_check.py / G-AX as
# an A-reference; it is not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def plain_token_char(c: int) -> bool:
    """Code point of a plain attribute-name token: an ASCII letter, digit, or
    underscore. On tokens made only of these code points, the single-quote
    wrap `quoted` below is exactly the rendered string-literal form of the
    token (no character needs escaping and no delimiter switch occurs)."""
    return (c == 95                                # '_'
            or (48 <= c and c <= 57)               # '0'..'9'
            or (65 <= c and c <= 90)               # 'A'..'Z'
            or (97 <= c and c <= 122))             # 'a'..'z'


@Pure
def quoted(tok: PSeq[int]) -> PSeq[int]:
    """A simple identifier token rendered as a single-quoted string literal:
    a U+0027 quote, the token code points, a closing U+0027 quote. Deep model
    of repr applied to a plain identifier (no quote/backslash/control chars)."""
    return PSeq(39) + tok + PSeq(39)


@Pure
def rendered(module: PSeq[int], class_name: PSeq[int],
             identifier: PSeq[int]) -> PSeq[int]:
    """The reference fragment, keyed by the stable identifier:
    module ++ '.' ++ class_name ++ '[' ++ "'identifier'" ++ ']'."""
    return (module + PSeq(46) + class_name + PSeq(91)
            + quoted(identifier) + PSeq(93))


@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end


def serialize_member(module: List[int], class_name: List[int],
                     identifier: List[int], payload: List[int]
                     ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four texts are read-only inputs (fractional permission). `payload` is
    # the renderable mutable-payload form; it is supplied but MUST NOT shape
    # either output (the point: key by the stable identifier, not the payload).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(class_name), 1 / 2))
    Requires(Acc(list_pred(identifier), 1 / 2))
    Requires(Acc(list_pred(payload), 1 / 2))
    # Domain scoping: the stable identifier is a plain attribute-name token —
    # every code point an ASCII letter, digit, or underscore. That is the only
    # shape a declared attribute name can take, and it is exactly the domain
    # on which the single-quote wrap `quoted` equals the real rendering of the
    # token as a string literal. Texts with a quote, backslash, or control
    # character are outside the modeled slice.
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(identifier),
        plain_token_char(identifier[k])))))
    # The rendering is a bounded amount of straight-line work and MUST
    # terminate (a total-correctness obligation). An implementation that
    # diverges before returning would satisfy the value postconditions only
    # vacuously and would never deliver the rendered fragment to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(class_name), 1 / 2))
    Ensures(Acc(list_pred(identifier), 1 / 2))
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The fragment reconstructs the member by its STABLE identifier, grounded in
    # the module / class_name / identifier carriers (not the payload).
    Ensures(ToSeq(Result()[0]) ==
            rendered(ToSeq(module), ToSeq(class_name), ToSeq(identifier)))
    # The accompanying import statement is exactly the import of the module.
    Ensures(ToSeq(Result()[1]) == import_line(ToSeq(module)))
    # post-conditions-end
    # impl-start
    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)
    # impl-end
