"""Twin-artifact model for sphinx-doc__sphinx-7590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A C++ numeric literal that is immediately followed by an identifier which is
  NOT one of the recognised numeric suffixes denotes a user-defined literal:
  the trailing identifier belongs to the literal token, and the literal's
  mangled id is the function-call style name-mangling

      clL_Zli<identifier-id>E<numeric-literal-id>E

  i.e. it is mangled as if it were the call `identifier(numeric-literal)`,
  embedding BOTH the mangled id of the trailing identifier and the mangled id
  of the numeric part. When the numeric literal instead carries a recognised
  numeric suffix (or has no trailing identifier at all), it is an ordinary
  numeric literal whose id is just the numeric-literal id.

The mangled id of an ordinary numeric literal is `L` + its text + `E`; the
mangled id of the (non-special) trailing identifier is the decimal length of
the identifier followed by the identifier text. The trivial numeric-literal
mangling is modelled directly; the (length-prefixed) identifier mangling is an
unchanged component supplied to the operation as the already-computed id string
of the trailing identifier, exactly as the real code obtains it, and is
axiomatized. The user-defined-literal mangling and the suffix-vs-identifier
decision are modelled deeply.

A second, simpler dialect parses the same numeric literals but has no
user-defined literals at all. There, a numeric literal is followed by a
recognised numeric suffix only when the trailing run of suffix characters is a
valid suffix terminated by a word boundary: such a suffix is part of the
literal's text (its id is the numeric-literal id of the literal-plus-suffix),
whereas a trailing run that is not a recognised suffix is NOT part of the
literal (its id is the numeric-literal id of the bare literal). This dialect
shares the same ordinary numeric-literal mangling.

Character data (literal text, identifier text, mangled ids) is modelled as
`List[int]` of code points (Nagini bans `str` indexing); the specification is
carried by `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def ident_mangle(ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a nonempty, ordinary trailing identifier — the UNCHANGED
    identifier id-generator. The contract is imposed over a RESTRICTED domain:
    the identifier is nonempty and is not the one reserved identifier whose id
    is a constant two-character abbreviation rather than the length-prefixed
    form (its code points are excluded by the precondition). On this domain the
    id is the decimal length of the identifier followed by the identifier text,
    so the identifier text is a (proper) suffix of its id, strictly longer than
    the identifier. Provenance + executable soundness check (the precondition
    must exclude every input on which the real generator deviates):
    mapping.md / axiom_check.py.
    """
    Requires(len(ident) > 0)
    # exclude the one reserved identifier the real generator maps to a constant
    # short abbreviation (code points 115, 116, 100) — outside the contracted
    # length-prefixed domain.
    Requires(ident != PSeq(115, 116, 100))
    Ensures(len(Result()) > len(ident))
    Ensures(Result().drop(len(Result()) - len(ident)) == ident)
# axioms-end


# pure-start
@Pure
def udl_prefix() -> PSeq[int]:
    # the function-call name-mangling prefix 'clL_Zli'
    return PSeq(99, 108, 76, 95, 90, 108, 105)


@Pure
def number_id_seq(lit: PSeq[int]) -> PSeq[int]:
    # mangled id of an ordinary numeric literal: 'L' + text + 'E'
    return PSeq(76) + lit + PSeq(69)


@Pure
def udl_id_seq(lit: PSeq[int], ident: PSeq[int]) -> PSeq[int]:
    """Mangled id of a user-defined literal: it is mangled as if it were the
    function call `ident(literal)` —
        clL_Zli + <identifier-id> + E + <numeric-literal-id> + E.
    Defined over the same restricted identifier domain as `ident_mangle`
    (nonempty, not the reserved short-abbreviation identifier).
    """
    Requires(len(ident) > 0)
    Requires(ident != PSeq(115, 116, 100))
    return udl_prefix() + ident_mangle(ident) + PSeq(69) \
        + number_id_seq(lit) + PSeq(69)
# pure-end


def number_literal_id(lit: List[int], ident: List[int], suffixed: bool,
                      ident_id: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(ident_id), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    # the trailing identifier (when present) is an ordinary identifier outside
    # the reserved short-abbreviation case the unchanged id-generator special-
    # cases (code points 115, 116, 100): the contract is imposed over this
    # domain so the identifier-mangling component is the length-prefixed form.
    Requires(ToSeq(ident) != PSeq(115, 116, 100))
    # the supplied identifier id is exactly the unchanged identifier mangling of
    # the trailing identifier (as the real code obtains it by calling the
    # identifier's id-generator), whenever a trailing identifier is present
    Requires(Implies(len(ToSeq(ident)) > 0,
                     ToSeq(ident_id) == ident_mangle(ToSeq(ident))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(ident_id), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # An unsuffixed numeric literal that is followed by an identifier is a
    # user-defined literal: its id is the function-call style mangling, which
    # embeds BOTH the trailing identifier and the numeric literal.
    # (the `ident != std` conjunct is always true by the precondition above —
    # it discharges udl_id_seq's domain restriction inside this guard and does
    # NOT weaken the contract on the contracted domain.)
    Ensures(Implies(not suffixed and len(ToSeq(ident)) > 0
                    and ToSeq(ident) != PSeq(115, 116, 100),
                    ToSeq(Result())
                    == udl_id_seq(ToSeq(lit), ToSeq(ident))))
    # Otherwise (a recognised numeric suffix, or no trailing identifier) it is
    # an ordinary numeric literal: its id is just the numeric-literal id.
    Ensures(Implies(suffixed or len(ToSeq(ident)) == 0,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): after matching the numeric literal only a fixed alpha
    # suffix run is consumed; a trailing user-defined-literal identifier is
    # never recognised, so the result is ALWAYS the ordinary numeric-literal id
    # regardless of any following identifier.
    out = [76] + lit + [69]  # type: List[int]
    return out
    # impl-end


def c_number_literal_id(lit: List[int], trail: List[int],
                        valid: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lit), 1 / 2))
    Requires(Acc(list_pred(trail), 1 / 2))
    # a numeric literal always has nonempty text
    Requires(len(lit) > 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lit), 1 / 2))
    Ensures(Acc(list_pred(trail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A recognised numeric suffix is part of the numeric literal's text: the
    # consumed suffix run is folded into the literal and the id is the ordinary
    # numeric-literal id of the literal-plus-suffix text.
    Ensures(Implies(valid,
                    ToSeq(Result())
                    == number_id_seq(ToSeq(lit) + ToSeq(trail))))
    # A trailing suffix-alphabet run that is NOT a recognised numeric suffix is
    # left unconsumed: only the bare numeric literal becomes the text, so the id
    # is just the numeric-literal id of the literal alone (the trailing run does
    # not belong to the number).
    Ensures(Implies(not valid,
                    ToSeq(Result()) == number_id_seq(ToSeq(lit))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): after matching the numeric literal, a MAXIMAL run of
    # suffix-alphabet characters is consumed unconditionally (the old
    # `while self.current_char in 'uUlLfF'` loop). The trailing run is therefore
    # ALWAYS folded into the literal text, even when it is not a recognised
    # numeric suffix, so the id is always the literal-plus-run id.
    out = [76] + lit + trail + [69]  # type: List[int]
    return out
    # impl-end
