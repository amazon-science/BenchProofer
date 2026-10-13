"""Twin-artifact model for scikit-learn__scikit-learn-25973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A greedy feature-selection procedure scores candidates in a preset number of
  scoring steps. Each step scores ONE candidate by drawing a family of
  cross-validation train/test splits from the caller-supplied split source and
  keeping one aggregate score built from exactly that draw, so a step can only
  complete when its OWN draw yields at least one split.

  The desired observable behaviour is that every scoring step draws a non-empty
  split family — the same positive number of splits the configured source
  carries — so the procedure completes for any number of steps, however many
  times the source has to present its family.

  This is stated of a configured source the securing step MATERIALISES: one that
  carries its split family for that step to build a re-presenting source FROM,
  or one that already re-presents its family on every draw. Nothing is claimed
  of a source that presents its family ITSELF and only once — the securing step
  hands such a source straight back, so its later draws present nothing and the
  behaviour above does not hold of it at all.

  The specified quantity is the per-step record of how many splits each step
  drew, together with the source those steps drew. The contract requires that
  the record holds one entry per step, that entry ``k`` is the count the drawn
  source presented on its ``k``-th draw, and that the reported source handed out
  exactly one draw per step and kept exactly one score per draw IN STEP — so no
  entry can be a remembered number, and no draw may be taken outside a step.

  The CONFIGURED source is specified the same way, through its own ledgers, for
  the case where a draw after its first presents nothing (a ONE-SHOT source —
  the case in which the behaviour above is not automatic, and the case the
  MATERIALISES condition above is stated of): such a source hands out EXACTLY
  ONE draw over the whole procedure, the one the securing step takes, and no
  kept score is built from a draw of it. So a scoring step may not draw the
  one-shot configured source, and the securing step may not be repeated. Nothing
  is claimed about a configured source that already presents its family on every
  draw, because securing such a source is permitted to hand back the source
  itself, in which case its ledgers are the reported source's.

The split source is modelled as a minimal record carrying only its touched
facets: the size of the split family it carries (``size``) and a boolean facet
(``reusable``) of its per-draw semantics. The number of splits a single draw
yields is modelled deeply as a pure function of those facets and of how many
draws preceded it. Whether the securing step MATERIALISES a given source is not
a function of those facets, so it is carried separately, as a domain token
(``materialisable``) the caller supplies together with the source and the
securing step consumes; it is demanded only of a source whose draws after the
first present nothing, since a source that re-presents its family on every draw
is secured correctly however the securing step treats it. The control-flow
property that the steps drew a source whose every draw presents the configured
source's full positive family has no value-level witness (the family size alone
does not record it), so for the proof it is pinned by an unforgeable capability
predicate (``presents_family``) that names BOTH the drawn source and the
configured one; this keeps the contract from being discharged either by echoing
the input's family size or by securing some unrelated family of the same size.

Drawing a split family is an EFFECT on the source, not a computation over its
facets, so a draw is modelled as an operation (``draw_splits``) rather than as a
readable value: it consumes the source's draw ledger at some tally and returns
it advanced by one, reporting the count that draw presented. Aggregating that
draw into the one score the step keeps is a second effect (``keep_score``) on a
second ledger. Both ledgers (``draws_taken`` / ``scores_kept``) are abstract, so
neither can be fabricated or advanced by hand: the ONLY way to reach a tally of
``n`` is to perform ``n`` operations. And because a score can be kept only while
its own draw is the single outstanding one (``draws_taken == scores_kept + 1``),
the two ledgers pin the ORDER as well as the totals: draw, keep, draw, keep, …
A total-tally obligation alone would not — a routine could take every draw up
front and then report remembered numbers — which is why the contract states the
alternation as the callee's own precondition and requires each reported entry to
be the journal entry that step's own draw produced. The two ledgers are carried
by EVERY source that has them, the configured one included, and they are separate
per source, so the configured source's own tallies say where the procedure did
NOT draw.

Termination (total correctness): the procedure must ANSWER — hand the record back
to its caller. Nagini is a partial-correctness verifier by default, so without an
explicit obligation a routine that never returns discharges every postcondition
vacuously while producing nothing; the obligation is carried as ``MustTerminate``
in the precondition, with a strictly smaller measure on each modelled operation
(each is a single bounded step on a source) and a decreasing loop measure, so a
routine may perform the operations but may not diverge. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class SplitSource:
    """A cross-validation split source. Only the touched facets are modelled:
    the size of the split family it carries (``size``), and a boolean facet
    (``reusable``) of how many splits a draw presents (see ``draw_count``)."""
    def __init__(self, size: int, reusable: bool) -> None:
        Requires(size >= 0)
        Requires(MustTerminate(1))                                # two field stores
        Ensures(Acc(self.size) and Acc(self.reusable))            # type: ignore[name-defined]
        Ensures(self.size == size and self.reusable == reusable)  # type: ignore[name-defined]
        self.size = size          # type: int
        self.reusable = reusable  # type: bool


class SelectionResult:
    """What the procedure reports: the per-step split counts it recorded and
    the split source those steps actually drew."""
    def __init__(self, counts: List[int], cv: SplitSource) -> None:
        Requires(Acc(list_pred(counts)))
        Requires(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Requires(MustTerminate(1))                                  # two field stores
        Ensures(Acc(self.counts) and Acc(self.cv))                  # type: ignore[name-defined]
        Ensures(Acc(list_pred(self.counts)) and self.counts is counts)  # type: ignore[name-defined]
        # the recorded counts are carried through unchanged in length and value
        Ensures(len(self.counts) == Old(len(counts)))               # type: ignore[name-defined]
        Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(self.counts),  # type: ignore[name-defined]
                                              self.counts[k] == Old(counts[k]))))  # type: ignore[name-defined]
        Ensures(Acc(self.cv.size, 1 / 2) and Acc(self.cv.reusable, 1 / 2))  # type: ignore[name-defined]
        Ensures(self.cv is cv)                                      # type: ignore[name-defined]
        self.counts = counts  # type: List[int]
        self.cv = cv          # type: SplitSource


# axioms-start
# Proof-only capability predicate that the modelled per-step draw of `cv` yields
# the full positive split family CARRIED BY `src`. It is abstract (no body), so
# no implementation can fabricate it by hand or Fold it into existence; it can be
# obtained ONLY from the Ensures of the modelled callee `secure_reusable_source`
# below, and only for the pair (its result, its argument). The result the
# procedure reports must carry this token against the CONFIGURED source, so the
# contract can be discharged neither by a routine that merely echoes the input's
# family size, nor by one that secures some unrelated family that happens to have
# the same size. Provenance + executable soundness check: mapping.md /
# axiom_check.py (G-AX).
@ContractOnly
@Predicate
def presents_family(cv: SplitSource, src: SplitSource) -> bool:
    pass


# Proof-only token that a source keeps its two ledgers at all. Abstract (no
# body), so no implementation can Fold it into existence; it is granted only by
# `secure_reusable_source` and is what makes the source's tallies readable.
@ContractOnly
@Predicate
def has_ledger(cv: SplitSource) -> bool:
    pass


# Proof-only token that the securing step MATERIALISES this source: the source
# carries its split family as a family for the securing step to build a
# re-presenting source FROM, rather than carrying its own single-use
# presentation of it. Abstract (no body), so no implementation can Fold it into
# existence; like `has_ledger` it is a DOMAIN token — held by the source the
# caller supplies and consumed by the one securing step. It is required only
# where the securing step's guarantee is not automatic, i.e. of a source that
# does NOT present its family on every draw: such a source, if it presents its
# family ITSELF and only once, is handed back by the securing step unchanged, so
# its later draws present nothing and the behaviour under specification does not
# hold of it. Provenance + executable soundness check: mapping.md /
# axiom_check.py (G-AX).
@ContractOnly
@Predicate
def materialisable(cv: SplitSource) -> bool:
    pass


# LEDGER 1: how many draws `cv` has handed out so far. Readable only while the
# source carries `has_ledger`, it starts at 0 on a freshly secured source, and
# `draw_splits` is the ONLY operation that advances it — by exactly one per call.
# No implementation can set it, so the ONLY way a source's tally reaches `n` is
# that `n` draws were actually performed on it. Every source that carries
# `has_ledger` keeps its OWN tally — the configured source included, and its
# ledger is a separate resource from the secured source's — so the configured
# source's tally records how many draws were taken from IT and no other.
# Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
@Pure
@ContractOnly
def draws_taken(cv: SplitSource) -> int:
    Requires(has_ledger(cv))
    Ensures(Result() >= 0)


# LEDGER 2: how many scores have been kept from `cv`'s draws so far — one per
# completed scoring step. `keep_score` is the ONLY operation that advances it,
# and it may run only while exactly ONE draw is outstanding, so the pair of
# tallies records the ORDER the two effects were interleaved in and not merely
# their totals. This is what gives "every step drew for itself" a value-level
# witness: the count a draw reports is the same on every draw (a source
# presenting its full family never depletes), so neither the counts nor a total
# tally can distinguish one draw per step from all the draws taken up front and a
# remembered number reported per step. Provenance + soundness check: mapping.md /
# axiom_check.py (G-AX).
@Pure
@ContractOnly
def scores_kept(cv: SplitSource) -> int:
    Requires(has_ledger(cv))
    Ensures(Result() >= 0)


# The JOURNAL the kept scores form: entry `k` is the split count that `cv`'s
# `k`-th draw presented and that the `k`-th kept score was built from. Readable
# only while the source carries `has_ledger`; no implementation can write it
# (`keep_score` is the only writer), so a reported record required to equal this
# journal cannot be assembled out of remembered numbers. Provenance + soundness
# check: mapping.md / axiom_check.py (G-AX).
@Pure
@ContractOnly
def score_from_draw(cv: SplitSource, k: int) -> int:
    Requires(has_ledger(cv))
    Ensures(Result() >= 0)


# An unchanged library helper the procedure CALLS (but does not change),
# modelled as a @ContractOnly callee (A-consumed). Its Ensures is the WEAKEST
# sufficient contract for the proof: the source it returns carries the SAME
# family size as its input, has `reusable == True`, and it is the UNIQUE grantor
# of the `presents_family` capability on the (result, argument) PAIR. That
# capability has no value-level witness (the family size alone is forgeable by
# echo, and a same-size family is forgeable by construction), so for the proof
# it — not the size value — is what pins whose family the steps draw. The
# returned source starts both ledgers at zero. Securing is ITSELF a draw on the
# configured source when that source is one-shot: it takes exactly one, keeps no
# score from it, and the family it hands the secured source is that one draw's.
# For a source that already presents its family on every draw the count it takes
# is not pinned (nothing observable depends on it), so the contract states the
# draw only where it is exact. The contract is validated == the real callee by
# axiom_check.py / G-AX. Provenance: mapping.md.
@ContractOnly
def secure_reusable_source(src: 'SplitSource') -> 'SplitSource':
    Requires(Acc(src.size, 1 / 4) and Acc(src.reusable, 1 / 4))
    Requires(src.size >= 0)
    # a source that does not already present its family on every draw is one
    # this step MATERIALISES: it is the securing step that builds the
    # re-presenting source, so the guarantees below are exact only for such a
    # source. A source presenting its family on every draw needs no token —
    # handing that very source back already satisfies them.
    Requires(Implies(src.reusable == False, materialisable(src)))
    # the configured source's own ledgers, with no draw of it outstanding.
    Requires(has_ledger(src))
    Requires(draws_taken(src) == scores_kept(src))
    # a single bounded step: it always answers (measure 1, strictly below the
    # procedure's, so a routine may consume it but cannot discharge its own
    # obligation by re-invoking itself).
    Requires(MustTerminate(1))
    Ensures(Acc(src.size, 1 / 4) and Acc(src.reusable, 1 / 4))
    Ensures(Acc(Result().size) and Acc(Result().reusable))
    Ensures(Result().size == src.size)
    Ensures(Result().reusable == True)
    Ensures(presents_family(Result(), src))
    # a freshly secured source keeps its ledgers and has handed out no draws and
    # kept no scores yet.
    Ensures(has_ledger(Result()))
    Ensures(draws_taken(Result()) == 0)
    Ensures(scores_kept(Result()) == 0)
    # the configured source keeps its ledger too: securing takes ONE draw of a
    # one-shot source and keeps no score from any draw of it.
    Ensures(has_ledger(src))
    Ensures(scores_kept(src) == Old(scores_kept(src)))
    Ensures(Implies(src.reusable == False,
                    draws_taken(src) == Old(draws_taken(src)) + 1))


# ONE draw from a source. Drawing is an EFFECT (it advances the source's draw
# ledger), so it is an operation rather than a computation over the source's
# facets: it advances `draws_taken` by exactly one, leaves the kept-score ledger
# alone, and reports the number of splits THAT draw presented -- the
# deeply-modelled `draw_count` of the source's facets and of the draws that
# preceded this one. A caller cannot advance the ledger without performing the
# draw, and cannot perform the draw without reporting exactly the count that draw
# presented. A draw may be taken only while NO draw is outstanding —
# `draws_taken(cv) == scores_kept(cv)` — because a step's draw is aggregated into
# that step's one kept score before the next step's draw begins; together with
# `keep_score`'s converse precondition this makes the two effects strictly
# alternate. A draw leaves the source's facets and the journal it has already
# written unchanged. Validated == one real `.split()` draw by axiom_check.py /
# G-AX. Provenance: mapping.md.
@ContractOnly
def draw_splits(cv: 'SplitSource') -> int:
    Requires(Acc(cv.size, 1 / 4) and Acc(cv.reusable, 1 / 4))
    Requires(cv.size >= 0)
    Requires(has_ledger(cv))
    Requires(draws_taken(cv) == scores_kept(cv))
    Requires(MustTerminate(1))
    Ensures(Acc(cv.size, 1 / 4) and Acc(cv.reusable, 1 / 4))
    Ensures(cv.size == Old(cv.size) and cv.reusable == Old(cv.reusable))
    Ensures(has_ledger(cv))
    Ensures(draws_taken(cv) == Old(draws_taken(cv)) + 1)
    Ensures(scores_kept(cv) == Old(scores_kept(cv)))
    Ensures(Result() == draw_count(cv.reusable, cv.size, Old(draws_taken(cv))))
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
            score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))


# ONE scoring step's aggregation: keep the score built from the draw that step
# just took. This too is an EFFECT (it advances the kept-score ledger and writes
# the journal), and it may run ONLY while exactly one draw is outstanding —
# `draws_taken(cv) == scores_kept(cv) + 1` — because the score a step keeps is
# aggregated from the splits of its OWN draw: a step cannot keep a score without
# drawing for itself, and cannot draw twice before keeping. The count it commits
# must be exactly the count that outstanding draw presented. Validated == the
# real per-candidate aggregation by axiom_check.py / G-AX. Provenance: mapping.md.
@ContractOnly
def keep_score(cv: 'SplitSource', c: int) -> None:
    Requires(Acc(cv.size, 1 / 4) and Acc(cv.reusable, 1 / 4))
    Requires(cv.size >= 0)
    Requires(has_ledger(cv))
    Requires(draws_taken(cv) == scores_kept(cv) + 1)
    Requires(c == draw_count(cv.reusable, cv.size, draws_taken(cv) - 1))
    Requires(MustTerminate(1))
    Ensures(Acc(cv.size, 1 / 4) and Acc(cv.reusable, 1 / 4))
    Ensures(cv.size == Old(cv.size) and cv.reusable == Old(cv.reusable))
    Ensures(has_ledger(cv))
    Ensures(draws_taken(cv) == Old(draws_taken(cv)))
    Ensures(scores_kept(cv) == Old(scores_kept(cv)) + 1)
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
            score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
# axioms-end


# pure-start
@Pure
def draw_count(reusable: bool, size: int, prior_draws: int) -> int:
    """Number of splits a single draw yields from a source, as a pure function
    of the source's facets and of how many draws preceded it. When ``reusable``
    holds the draw yields the full ``size`` on every draw; otherwise it yields
    ``size`` only when no draw preceded it and ``0`` once a draw has. Modelled
    for a non-negative family size and a non-negative count of prior draws."""
    Requires(size >= 0 and prior_draws >= 0)
    if reusable:
        return size
    if prior_draws == 0:
        return size
    return 0


@Pure
def step_completes(reusable: bool, size: int, prior_draws: int) -> bool:
    """A scoring step completes exactly when its own draw is non-empty (an empty
    draw leaves nothing to aggregate, so no score can be kept)."""
    Requires(size >= 0 and prior_draws >= 0)
    return draw_count(reusable, size, prior_draws) > 0
# pure-end


# ---------------------------------------------------------------------------
# The scoring procedure. It runs `n_scorings` scoring steps, each drawing a
# source that presents the configured source's full positive split family and
# keeping the score its own draw produced, and reports the per-step draw counts
# together with the source those steps drew.
# ---------------------------------------------------------------------------
def select_features(src: SplitSource, n_scorings: int) -> SelectionResult:
    # pre-conditions-start
    Requires(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
    # A non-empty split family (the cross-validator yields at least one split),
    # and at least one scoring step.
    Requires(src.size > 0)
    Requires(n_scorings >= 1)
    # The configured source arrives with its ledgers untouched: nothing has been
    # drawn from it and no score has been kept from it yet.
    Requires(has_ledger(src))
    Requires(draws_taken(src) == 0)
    Requires(scores_kept(src) == 0)
    # A source that does not already present its family on every draw is one the
    # securing step MATERIALISES — it carries its split family for that step to
    # build the re-presenting source FROM. Nothing below is claimed of a source
    # that presents its family ITSELF and only once: the securing step hands
    # such a source back unchanged, so its later draws present nothing.
    Requires(Implies(src.reusable == False, materialisable(src)))
    # TERMINATION: the procedure must ANSWER — hand the record back. Without the
    # obligation a routine that never returns discharges every postcondition
    # below vacuously while producing no record at all.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
    Ensures(Acc(Result().counts) and Acc(Result().cv))
    Ensures(Acc(list_pred(Result().counts)))
    Ensures(Acc(Result().cv.size, 1 / 2) and Acc(Result().cv.reusable, 1 / 2))
    # The source the steps drew carries the unforgeable capability that its every
    # draw presents THE CONFIGURED SOURCE's full positive family, and carries
    # that family's full positive size. The capability cannot be produced by
    # echoing the input, nor by securing a same-size family built from scratch.
    Ensures(presents_family(Result().cv, src))
    Ensures(Result().cv.size == src.size)
    Ensures(Result().cv.reusable == True)
    Ensures(Result().cv.size > 0)
    # One recorded draw per scoring step.
    Ensures(len(Result().counts) == n_scorings)
    # Each step's recorded count is EXACTLY the number of splits the witnessed
    # source yields on that step's draw (step `k` after `k` prior draws) — so
    # the count must be PRODUCED BY drawing that witnessed source, not echoed off
    # the input. Because that source presents its full family on every draw,
    # every step records the full positive family.
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
            Result().counts[k] == draw_count(Result().cv.reusable,
                                             Result().cv.size, k))))
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
                                          Result().counts[k] == src.size)))
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
                                          Result().counts[k] >= 1)))
    # The reported source has handed out exactly ONE draw PER STEP and kept
    # exactly ONE score PER DRAW: both ledgers stand at `n_scorings`. Neither is
    # implied by the counts above — a source presenting its full family reports
    # the same number on every draw, so the recorded counts are identical whether
    # each step drew or a single remembered number was reused — and neither
    # ledger can be advanced except by performing its own operation.
    Ensures(has_ledger(Result().cv))
    Ensures(draws_taken(Result().cv) == n_scorings)
    Ensures(scores_kept(Result().cv) == n_scorings)
    # And the reported record IS the journal those kept scores wrote: entry `k`
    # is the count the source's `k`-th draw presented. Since a score may be kept
    # only while its own draw is the single outstanding one, this forces the two
    # effects to alternate — draw, keep, draw, keep — so the `n_scorings` draws
    # cannot be taken up front and then reported from memory: every entry is the
    # journal entry its own step produced.
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < n_scorings,
            Result().counts[k] == score_from_draw(Result().cv, k))))
    # The CONFIGURED source's own ledgers say where the procedure did NOT draw.
    # When that source is ONE-SHOT it handed out EXACTLY ONE draw over the whole
    # procedure — the securing step's — and no score was kept from any draw of
    # it. So no scoring step drew it and the securing step ran exactly once.
    # Neither is implied by anything above: the clauses above constrain only the
    # source the steps report, and a routine that leaves some scoring step
    # drawing the configured source, or that secures it again per step,
    # satisfies every one of them.
    #
    # Both are stated for the one-shot case only, because that is where the
    # abstraction is exact: securing a source that ALREADY presents its family
    # on every draw may legitimately hand back that very source, and then its
    # ledgers are the reported source's and stand at `n_scorings`. That case
    # needs no clause here — a source whose every draw re-presents its family
    # cannot be depleted by being drawn per step, so drawing it directly is
    # already correct. Claiming zero kept scores there would be claiming
    # something FALSE of the intended behaviour, not something stronger.
    Ensures(has_ledger(src))
    Ensures(Implies(src.reusable == False, scores_kept(src) == 0))
    Ensures(Implies(src.reusable == False, draws_taken(src) == 1))
    # post-conditions-end
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    Assert(cv.size == src.size)
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # invariants-start
        Invariant(Acc(src.size, 1 / 2) and Acc(src.reusable, 1 / 2))
        Invariant(Acc(cv.size, 1 / 2) and Acc(cv.reusable, 1 / 2))
        Invariant(cv.size == src.size and cv.size > 0 and cv.reusable == True)
        Invariant(presents_family(cv, src))
        Invariant(has_ledger(cv))
        Invariant(draws_taken(cv) == i)
        Invariant(scores_kept(cv) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < scores_kept(cv),
                score_from_draw(cv, k) == draw_count(cv.reusable, cv.size, k))))
        # the configured source is untouched by the steps: when it is one-shot,
        # its ledger still shows only the securing step's draw and no score kept
        # from any draw of it.
        Invariant(has_ledger(src))
        Invariant(Implies(src.reusable == False, scores_kept(src) == 0))
        Invariant(Implies(src.reusable == False, draws_taken(src) == 1))
        Invariant(0 <= i and i <= n_scorings)
        Invariant(Acc(list_pred(used)))
        Invariant(len(used) == i)
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                used[k] == draw_count(cv.reusable, cv.size, k))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                used[k] == src.size)))
        # the measure: `n_scorings - i` steps remain, strictly fewer each pass;
        # `+ 1` keeps it positive on the final pass (0 remaining).
        Invariant(MustTerminate(n_scorings - i + 1))
        # invariants-end
        # step i draws the secured source (`i` draws preceded it) and keeps the
        # score built from that draw before the next step draws.
        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end
