"""Twin-artifact model for django__django-14752.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An autocomplete endpoint answers a query by turning each matched record into
  one entry of an answer sequence. Two behaviours are pinned:

  (1) The per-record conversion is performed through a single, replaceable
      conversion step that belongs to the responder: every entry of the answer
      sequence is exactly the value that conversion step produces for the
      corresponding record, IN ORDER. Because the responder DEFERS to its own
      conversion step rather than settling the entry contents itself, a
      responder that supplies a different conversion step changes every entry
      accordingly -- the conversion step is the extension point, and the answer
      entries are bound to it, not to any predetermined entry shape.

  (2) The default conversion step turns a record into an entry exposing two
      fields: an identifier field carrying the textual form of the record's
      designated lookup attribute, and a display field carrying the textual form
      of the record itself.

The responder is modelled as a minimal object (`View`); a matched record as a
minimal object (`Record`) carrying the two textual values the default
conversion reads. An entry of the answer sequence is a minimal object (`Entry`).
The designated lookup attribute name is carried as an `int` token. The textual
values are `PSeq[int]` of code points (Nagini bans `str` indexing).

The replaceable conversion step (the responder's own, possibly-supplied
conversion) is the late-bound callee, axiomatized as `record_entry`: an
opaque per-(responder, record) entry producer. The default conversion step is
modelled deeply as `default_record_entry`; its agreement with the late-bound
step for a responder that supplies no replacement is validated out-of-band by
axiom_check.py (G-AX), not consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class View:
    """The responder. Modelled as a bare identity-bearing object: the late-bound
    conversion step is selected by WHICH responder this is (its dynamic type),
    captured here by the receiver argument to `record_entry`."""

    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(True)


class Record:
    """A matched record. Carries only the two textual values the default
    conversion step reads: the textual form of its designated lookup attribute
    (`id_text`) and the textual form of the record itself (`display_text`)."""

    def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_text) and Acc(self.display_text))
        Ensures(self.id_text == id_text)
        Ensures(self.display_text == display_text)
        # post-conditions-end
        # impl-start
        self.id_text = id_text            # type: PSeq[int]
        self.display_text = display_text  # type: PSeq[int]
        # impl-end


class Entry:
    """One entry of the answer sequence: an identifier field and a display field
    (the entry may carry further fields supplied by a replacement conversion
    step; only these two are observed for the default step)."""

    def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_val) and Acc(self.text_val))
        Ensures(self.id_val == id_val)
        Ensures(self.text_val == text_val)
        # post-conditions-end
        # impl-start
        self.id_val = id_val      # type: PSeq[int]
        self.text_val = text_val  # type: PSeq[int]
        # impl-end


# axioms-start
@Pure
@ContractOnly
def lookup_text(rec: Record, to_field_name: int) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record's designated
    lookup attribute (`str(getattr(obj, to_field_name))`). A pure, deterministic
    function of the record and the attribute token; for the modelled record it
    yields the record's stored `id_text`. Provenance + soundness: mapping.md /
    axiom_check.py (an unchanged callee). The conversion of an attribute to its
    textual form is the same wherever it is performed."""
    Requires(Acc(rec.id_text, 1 / 8))
    Ensures(Result() == rec.id_text)


@Pure
@ContractOnly
def display(rec: Record) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record itself
    (`str(obj)`). A pure, deterministic function of the record; for the modelled
    record it yields the record's stored `display_text`. Provenance + soundness:
    mapping.md / axiom_check.py (an unchanged callee). The conversion of a record
    to its textual form is the same wherever it is performed."""
    Requires(Acc(rec.display_text, 1 / 8))
    Ensures(Result() == rec.display_text)


@Pure
@ContractOnly
def record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    """The responder's OWN, replaceable conversion step (the extension point),
    late-bound on the responder `view`. Opaque: the produced entry is whatever
    this responder's conversion step yields for the record -- a responder that
    supplies a different conversion step yields a different entry. The default
    responder's conversion step agrees with `default_record_entry`; that
    agreement is validated against the real callee out-of-band by axiom_check.py
    (G-AX), NOT consumed here. Provenance: mapping.md."""
    Requires(Acc(rec.id_text, 1 / 8) and Acc(rec.display_text, 1 / 8))
    Ensures(True)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    # pre-conditions-start
    Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    Ensures(Acc(Result().id_val) and Acc(Result().text_val))
    # The default entry exposes two fields: the identifier field carries the
    # textual form of the record's designated lookup attribute, and the display
    # field carries the textual form of the record itself.
    Ensures(Result().id_val == lookup_text(rec, to_field_name))
    Ensures(Result().text_val == display(rec))
    # post-conditions-end
    # impl-start
    return Entry(lookup_text(rec, to_field_name), display(rec))
    # impl-end


def build_results(view: View, recs: List[Record], to_field_name: int) -> List[Entry]:
    # pre-conditions-start
    Requires(Acc(list_pred(recs), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
             Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recs), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    Ensures(Acc(list_pred(Result())))
    # The answer sequence is aligned, one entry per record, IN ORDER ...
    Ensures(len(Result()) == len(recs))
    # ... and every entry is exactly what the responder's OWN replaceable
    # conversion step produces for the corresponding record. The responder
    # defers to its conversion step: it does not settle the entry contents
    # itself, so a responder supplying a different step changes every entry.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Result()[k] is record_entry(view, recs[k], to_field_name)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Entry]
    i = 0
    while i < len(recs):
        # invariants-start
        Invariant(Acc(list_pred(recs), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recs))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  result[k] is record_entry(view, recs[k], to_field_name)))))
        Invariant(MustTerminate(len(recs) - i + 1))
        # invariants-end
        # PRE-CHANGE skeleton: the responder settles the entry contents itself,
        # constructing the default entry inline instead of deferring to its own
        # replaceable conversion step. A responder that supplies a different
        # conversion step is therefore IGNORED -- this is the absent extension
        # point the change introduces.
        result.append(Entry(lookup_text(recs[i], to_field_name), display(recs[i])))
        i = i + 1
    return result
    # impl-end
