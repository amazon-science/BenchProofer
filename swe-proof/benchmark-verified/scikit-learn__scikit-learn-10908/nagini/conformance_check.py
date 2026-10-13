#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-10908 (nagini).

Refutes (does not prove) the refinement leg: does model.py's impl region agree
with the REAL patched repo function it claims to model?

SHADOW
  The `# impl-start` / `# impl-end` region of `model.py`'s `get_feature_names`,
  copied VERBATIM below with only the contract calls removed (`Requires`,
  `Ensures`, `Invariant`, `Assert`, `MustTerminate`, `Acc`, and the
  `# invariants-start`/`-end` markers). No restructuring, no renaming: the
  branch order, the `usable_terms` screen on the supplied list, the `result`/`j`
  copy loop, the `self.supplied = False` write before the unfitted-object raise,
  and the comments are the model's own text. `Vectoriser`'s constructor body
  (six field writes) is copied the same way.

  model.py's module-level `@Pure` helper `usable_terms` is copied over as well.
  Its `Requires` line is stripped like any other contract, and its
  quantifier pair is spelled as the equivalent Python comprehension over the same
  index range -- the file's ONLY transliteration, called out here because a
  `Forall` term is a static Viper construct and cannot be executed. The predicate
  it computes is the same: non-empty, and no two positions carry the same term.

  model.py's other two `@Pure` helpers, `places` and `numbered_by_place`, are
  spec-only vocabulary: they occur in model.py exclusively inside contracts and
  never in an impl region, so they are not part of the shadow. Their executable
  counterpart appears here only as `_is_numbered_by_place` -- used as a domain
  screen and to observe the REAL numbering -- never as shadow behaviour.

  model.py declares no `@ContractOnly` axiom (its `# axioms-start` region is
  empty), so there is nothing else to copy over. The impl region never evaluates
  a `PSeq`/`ToSeq` term either -- every `ToSeq` occurrence in model.py sits
  inside a contract (Ensures/Invariant/Assert) and is stripped -- so no PSeq shim
  is needed here; the executable carrier is a plain `List[int]`.

ORACLE
  The real patched `CountVectorizer.get_feature_names`
  (`sklearn/feature_extraction/text.py:994` at base_commit, per mapping.md §1),
  CALLED, not transliterated. The gate applies patch.diff to /testbed before
  this script runs and PYTHONPATH=/testbed makes the patched module importable;
  the script asserts the patch is actually in place (`_patch_is_applied`) so a
  silent pre-patch run cannot masquerade as a pass.

  BOTH modelled failures are observed and DISTINGUISHED, so reporting one where
  the real function reports the other is a disagreement:
    * model `NotFittedError` <-> the real `sklearn.exceptions.NotFittedError`
      (`_check_vocabulary` -> `check_is_fitted`, `text.py:304`);
    * model `UnusableTermsError` -- the materialise step's rejection of a
      supplied list it cannot turn into a mapping -- <-> the real `ValueError`
      that `_validate_vocabulary` raises for a repeated term
      (`text.py:282`) or an empty list (`text.py:294`).

  The one callee the impl region invokes, `materialise_from_param`, is modelled
  DEEPLY in model.py but mapping.md §3.1 records it as an A-reference for
  `VectorizerMixin._validate_vocabulary` (`text.py:273`, the unchanged routine
  the patch adds a guarded call to). Following both sibling bundles
  (velvet/lean `conformance_check.py`), the shadow realises that callee with the
  REAL repo routine rather than with the model's own body, so the axiom is
  exercised instead of assumed -- and the shadow reads `fitted`/`supplied` back
  off the real object instead of hardcoding them, so a routine that failed to
  set `vocabulary_` / `fixed_vocabulary_` would show up as a disagreement.
  Independently, `materialise_verbatim` (the helper's impl region, copied
  verbatim) is diffed against that same real routine on every input where the
  helper's own precondition holds, so the deep body is checked here too rather
  than deferred wholly to G-AX.

TYPE BRIDGE (mapping.md §2, inverted)
  Terms are opaque to the query, so model.py carries them as `int` ids; the real
  routine wants `str`. `_TERMS[i]` is the concrete term for id `i` and
  `_TERM_ID` inverts it. A model state
  `(fitted, has_param, supplied, param, names, idx)` becomes a real
  `CountVectorizer` by: `vocabulary=[_TERMS[t] for t in param]` when `has_param`
  else `None` (`self.vocabulary is not None` <-> `has_param`); when `fitted`,
  `vocabulary_ = {_TERMS[names[j]]: idx[j]}` -- the model's mapping carried as
  the parallel pair `names` (its terms in ascending index order) and `idx` (the
  index each of those terms holds), so BOTH halves of the mapping cross the
  bridge (`hasattr(self, 'vocabulary_')` <-> `fitted`) -- and
  `fixed_vocabulary_ = supplied`.

  The observed output is compared as
  `(outcome, fixed_vocabulary_, names-in-index-order, indices-in-that-order)`
  with terms mapped back to ids. The fourth component is what makes a
  RENUMBERING visible: `names-in-index-order` alone is the same list for
  `{a:0, b:1}` and for `{a:0, b:7}`, so a shadow that reported the right names
  while moving them to other columns would agree on a triple and disagree here.
  So the returned list, the recorded supplied-at-construction flag, the
  resulting index ORDER and the actual index each name carries all have to
  agree -- not just the return value.

INPUT DOMAIN
  Every generated state satisfies `get_feature_names`'s `Requires` -- asserted
  per input by `_requires_holds`, which enforces the model's two representation
  clauses, `fitted -> usable_terms(names)` and
  `fitted -> numbered_by_place(idx, names)`, and nothing else. In particular a
  fitted, supplied-at-construction object whose materialised mapping does NOT
  match its constructor list is generated and checked: model.py imposes no
  such relation, so neither does this gate.

  `param` is NOT restricted. The constructor vocabulary is an arbitrary
  caller-supplied list, so an EMPTY list and a list with a REPEATED term are
  generated and checked like any other -- these are exactly the inputs on which
  the real function reports `_validate_vocabulary`'s ValueError instead of
  returning, and the model's `UnusableTermsError` exit is diffed against it.

  Two documented restrictions, from the frozen artifacts rather than from
  convenience:

  (1) When `fitted`, `names` is a NON-EMPTY list of DISTINCT ids -- exactly
      `Implies(self.fitted, usable_terms(self.names))`, the model's stated
      representation invariant for a materialised mapping. Distinctness is
      structural: `vocabulary_` is a dict KEYED by term, so no term can occur
      twice among its keys, and the bridge builds it from `names` by that same
      keying. Non-emptiness is a repo invariant: `vocabulary_ == {}` is not a
      state the repository can produce, because all three sites that assign
      `vocabulary_` guard against it -- `text.py:294-297` raises "empty
      vocabulary passed to fit" before assigning, and `text.py:928`'s value
      comes from `_count_vocab`, which raises "empty vocabulary; perhaps the
      documents only contain stop words" (`text.py:834`), with `_limit_features`
      raising "After pruning, no terms remain" as well. That premise is CHECKED,
      not assumed: `_check_nonempty_invariant` executes both guards
      in-container and fails the gate if either one stops rejecting.

  (2) When `fitted`, the mapping is NUMBERED BY PLACE: read in ascending index
      order, its indices are exactly 0, 1, ..., n-1 -- exactly
      `Implies(self.fitted, numbered_by_place(self.idx, self.names))`, the other
      half of the same representation invariant. This is not a convenience: it
      is the invariant the REPOSITORY validates and maintains, at every site
      that can put a `vocabulary_` on the object.
        * A Mapping passed as `vocabulary` is accepted only if its index set has
          no repeat (`text.py:287-288`) and contains every i in
          `range(len(vocabulary))` (`text.py:289-293`) -- i.e. only if it is a
          bijection onto 0..n-1, which read in index order IS 0..n-1.
        * A list/set passed as `vocabulary` is numbered by `enumerate`
          (`text.py:280-283`).
        * A learned mapping comes from `_count_vocab`'s `defaultdict(...,
          vocabulary.__len__)` (`text.py:804-805`), is renumbered by
          `_sort_features` with `enumerate` (`text.py:749-751`) and renumbered
          again by `_limit_features`'s `cumsum` of the keep-mask
          (`text.py:783-789`); all three produce a contiguous 0-based
          numbering.
      That premise is CHECKED, not assumed, the same way as (1):
      `_check_positional_invariant` executes the two Mapping guards (a gapped
      and a repeated-index dict must both still be rejected), confirms an
      accepted permutation dict is positional, and confirms a real
      `fit_transform` -- plain, and again under `max_features` so
      `_limit_features` runs -- yields a `vocabulary_` whose values are exactly
      `range(n)`. If any of those stops holding, the gate fails.

  Consequence, stated rather than buried: the only impl path the in-domain
  corpus does not reach is the zero-trip copy loop (`len(self.names) == 0`),
  which is reachable only from the excluded state (1). It is exercised anyway
  as a LABELLED out-of-domain probe (`_out_of_domain_probe`) whose result is
  reported in the JSON summary instead of being scored: there the model returns
  `[]` while the real `_check_vocabulary` raises ValueError("Vocabulary is
  empty"), a divergence model.py's precondition excludes and that no repo path
  can witness.

  Restriction (2) costs no impl path at all -- both `fitted` branches are reached
  by positionally numbered states -- but because the interesting question about a
  precondition is what it HIDES, four non-positionally numbered states (a gapped
  numbering, an all-shifted one, a doubled one and a singleton at index 7) are
  run anyway as labelled probes (`_numbering_probes`) and reported in the JSON
  summary. They AGREE: the query only reads the mapping it reports, so the model
  and the real patched function observe the same thing on a wrongly numbered
  object too. Restriction (2) is therefore a statement about which objects the
  repository can build -- executed by `_check_positional_invariant` -- and not
  cover for a divergence.

  One bridge exclusion, on the MODEL side rather than the repo side:
  `supplied is None` realises the model's always-present `supplied` field as an
  ABSENT real `fixed_vocabulary_`, which is admissible only where the impl WRITES
  the flag before it can be observed. That holds on the unfitted-raise path (the
  impl writes `self.supplied = False` there without ever reading it), but NOT on
  the unusable-supplied-list path: the modelled step writes nothing there, and
  the real routine likewise validates the list BEFORE its first write, so the
  flag's entry value is observable and an absent attribute has no model carrier.
  Nor on a fitted object, where the real function returns without touching the
  attribute. Both combinations are excluded by `_requires_holds` rather than left
  to chance.

INPUT COUNT
  The domain is infinite (ordered sequences over the term pool), so: boundary
  states first -- all FOUR impl branches (unfitted-raise / unusable-list-reject /
  materialise / already-fitted), the exact F2P vocabulary (the nine food terms of
  `test_feature_names`), singleton and full-pool vocabularies, reverse and
  shuffled index orders, the `fixed_vocabulary_`-absent fresh object, stale-`names`
  states, states taken from a REAL `fit_transform`, empty and repeated-term
  supplied lists in every flag combination, and an EXHAUSTIVE sweep of every list
  up to length 3 over a 3-term pool -- then 100000 seeded fuzz states whose
  supplied lists are drawn WITH replacement, so empty and repeating lists occur
  throughout rather than being generated away. Branch hit counts are reported in
  the JSON summary. Pinned seed: 10908 (recorded in mapping.md under `## G-CONF`).

  The check was mutation-tested to confirm it is capable of failing: fourteen
  deliberately wrong shadows -- among them dropping the on-demand materialisation
  entirely (i.e. reverting the gold patch's effect), dropping the usable-list
  screen so an empty or repeating list is copied through instead of rejected,
  reporting the unfitted-object failure for an unusable supplied list, writing the
  supplied flag on the rejection path, omitting the `self.supplied = False` write
  before the unfitted raise, an off-by-one copy loop, reversed output order,
  `supplied=False` instead of `True`, sorting the supplied terms instead of
  preserving their order, a swapped branch guard, and a sorting verbatim helper
  body -- are each caught and reported. Three of the fourteen target the
  NUMBERING half specifically, and are the reason the observation carries it:
  a verbatim helper that numbers the terms it materialises `2*k` instead of `k`,
  one that numbers them from 1, and an already-fitted path that renumbers the
  mapping it reports while leaving the reported names alone. All three agree with
  the real function on every component of the OLD observation
  `(outcome, fixed_vocabulary_, names-in-index-order)` and on the old
  `(names, fitted, supplied)` helper diff; each is caught only because the
  numbering is now observed -- by the fourth component of the observation for the
  third, and by the helper diff's `idx` comparison for the first two.

Exit 0 iff zero disagreements; on a disagreement the state and both observed
outputs are printed and the exit status is 1. stdlib + sklearn only.
"""
import itertools
import json
import random
import sys
from operator import itemgetter
from typing import List

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.exceptions import NotFittedError as RealNotFittedError

SEED = 10908
N_FUZZ = 100_000

# --- type bridge: opaque term ids <-> concrete repo terms (mapping.md §2) ----
# The first nine are the F2P vocabulary of test_feature_names.
_TERMS = ["beer", "burger", "celeri", "coke", "pizza", "salad", "sparkling",
          "tomato", "water", "and", "document", "first", "is", "one", "second",
          "the", "third", "this", "alpha", "zeta", "x", "q9", "m", "0"]
_TERM_ID = {t: i for i, t in enumerate(_TERMS)}
_UNSET = "<unset>"


# =============================================================================
# SHADOW -- model.py's impl regions, copied verbatim, contracts stripped
# =============================================================================

class NotFittedError(Exception):
    """model.py's user-defined stand-in for the unfitted-object failure."""
    pass


class UnusableTermsError(Exception):
    """model.py's user-defined stand-in for the materialise step's rejection of
    a supplied list it cannot turn into a mapping."""
    pass


class Vectoriser:
    """model.py's Vectoriser; constructor body copied verbatim."""

    def __init__(self, fitted: bool, has_param: bool, supplied: bool,
                 param: List[int], names: List[int], idx: List[int]) -> None:
        self.fitted = fitted
        self.has_param = has_param
        self.supplied = supplied
        self.param = param
        self.names = names
        self.idx = idx


def usable_terms(xs: List[int]) -> bool:
    """model.py's `@Pure usable_terms`, contract stripped. The nested `Forall`
    pair over `0 <= i < j < len(xs)` is spelled as the equivalent comprehension
    over that same index range (a `Forall` term is not executable); the
    predicate -- non-empty and no term listed twice -- is unchanged."""
    return len(xs) > 0 and all(
        xs[i] != xs[j]
        for i in range(len(xs)) for j in range(i + 1, len(xs)))


def _is_numbered_by_place(idx, names) -> bool:
    """model.py's `@Pure numbered_by_place`, as an executable predicate. NOT part
    of the shadow: `numbered_by_place` is spec-only vocabulary in model.py (it
    occurs there exclusively inside contracts). It is used here as the domain
    screen for restriction (2) and to observe the REAL numbering."""
    return len(idx) == len(names) and list(idx) == list(range(len(names)))


def materialise_verbatim(self: Vectoriser) -> None:
    """The impl region of model.py's `materialise_from_param`, VERBATIM with
    contracts stripped. Diffed against the real `_validate_vocabulary` on every
    input satisfying that helper's precondition by `_check_pair`; not used by the
    shadow query itself, which calls the real routine (see module docstring,
    ORACLE)."""
    # impl-start
    new_names = []  # type: List[int]
    new_idx = []  # type: List[int]
    k = 0
    while k < len(self.param):
        new_names.append(self.param[k])
        new_idx.append(k)
        k = k + 1
    self.names = new_names
    self.idx = new_idx
    self.fitted = True
    self.supplied = True
    # impl-end


def materialise_from_param(self: Vectoriser) -> None:
    """The A-reference callee, realised by the REAL unchanged repo routine
    `VectorizerMixin._validate_vocabulary` (`text.py:273`) rather than by
    model.py's own body, so the axiom is exercised rather than assumed.

    `fitted` and `supplied` are read BACK off the real object instead of being
    hardcoded to True, so a routine that did not materialise the mapping or did
    not record the supplied-at-construction vocabulary would surface here as a
    disagreement. So is the NUMBERING half (`idx`): the indices come off the real
    `vocabulary_` rather than being assumed to be 0..n-1, so a routine that
    numbered the supplied terms any other way would surface here too."""
    cv = CountVectorizer(vocabulary=[_TERMS[t] for t in self.param])
    cv._validate_vocabulary()                       # the REAL repo routine
    pairs = sorted(cv.vocabulary_.items(), key=itemgetter(1))
    self.names = [_TERM_ID[t] for t, i in pairs]
    self.idx = [i for t, i in pairs]
    self.fitted = hasattr(cv, "vocabulary_")
    self.supplied = cv.fixed_vocabulary_


def get_feature_names(self: Vectoriser) -> List[int]:
    """The impl region of model.py's `get_feature_names`, VERBATIM with the
    contract calls and the invariants block stripped."""
    # impl-start
    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # A supplied list that cannot become a mapping: the materialise
                # step reports its rejection and writes nothing at all.
                raise UnusableTermsError()
        else:
            # The on-demand materialise step runs on the unfitted object; with
            # no construction-supplied list it builds nothing but records that
            # the vocabulary was not supplied at construction, and the failure
            # then surfaces.
            self.supplied = False
            raise NotFittedError()
    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        result.append(self.names[j])
        j = j + 1
    return result
    # impl-end


# =============================================================================
# Bridge + observation
# =============================================================================

def _build_real(state):
    """Model state -> the real CountVectorizer it denotes (mapping.md §2)."""
    fitted, has_param, supplied, param, names, idx = state
    vocab = [_TERMS[t] for t in param] if has_param else None
    cv = CountVectorizer(vocabulary=vocab)
    if fitted:
        # BOTH halves of the model's mapping cross the bridge: `names` supplies
        # the keys, `idx` the index each key carries. (A dict built from a
        # positional `idx` is the same dict `enumerate` would give, but reading
        # `idx` rather than assuming it is what lets a renumbering be observed.)
        cv.vocabulary_ = {_TERMS[t]: idx[j] for j, t in enumerate(names)}
    if supplied is not None:
        # `supplied is None` models a fresh object, on which the real
        # `fixed_vocabulary_` attribute is genuinely absent. Admissible only
        # where the impl writes the field before it can be observed; see the
        # module docstring (INPUT DOMAIN) and `_requires_holds`.
        cv.fixed_vocabulary_ = supplied
    return cv


def _observe_real(cv):
    """(outcome, fixed_vocabulary_, names-in-index-order, those names' indices)
    for the real object. The fourth component is the NUMBERING half: without it
    `{a:0, b:1}` and `{a:0, b:7}` are indistinguishable observations."""
    try:
        names = cv.get_feature_names()              # the REAL patched function
        outcome = ("ok", [_TERM_ID[t] for t in names])
    except RealNotFittedError:
        outcome = ("raise", "NotFittedError")
    except ValueError:
        # `_validate_vocabulary`'s rejection of a list it cannot turn into a
        # mapping: "Duplicate term in vocabulary" (text.py:282) / "empty
        # vocabulary passed to fit" (text.py:294). NOTE: RealNotFittedError is
        # a ValueError subclass in sklearn, so it MUST be caught first (above)
        # for the two failures to stay distinguishable.
        outcome = ("raise", "UnusableTermsError")
    except Exception as exc:
        outcome = ("raise-other", type(exc).__name__)
    flag = getattr(cv, "fixed_vocabulary_", _UNSET)
    if hasattr(cv, "vocabulary_"):
        pairs = sorted(cv.vocabulary_.items(), key=itemgetter(1))
        index = [_TERM_ID[t] for t, i in pairs]
        numbering = [i for t, i in pairs]
    else:
        index = _UNSET
        numbering = _UNSET
    return (outcome, flag, index, numbering)


def _observe_shadow(state):
    """The same observation for the shadow, over the model carrier."""
    fitted, has_param, supplied, param, names, idx = state
    v = Vectoriser(fitted, has_param,
                   False if supplied is None else supplied,
                   list(param), list(names), list(idx))
    try:
        outcome = ("ok", list(get_feature_names(v)))
    except NotFittedError:
        # bridge: model NotFittedError <-> sklearn.exceptions.NotFittedError
        outcome = ("raise", "NotFittedError")
    except UnusableTermsError:
        # bridge: model UnusableTermsError <-> _validate_vocabulary's ValueError
        outcome = ("raise", "UnusableTermsError")
    except Exception as exc:
        # The model declares exactly those two failures, so anything else is a
        # divergence. Tagged "shadow-crash" -- a tag no real observation can
        # produce -- so it is always REPORTED as a disagreement (with the state
        # and both outputs, per the G-CONF contract) and can never
        # coincidentally match the real side's outcome.
        outcome = ("shadow-crash", type(exc).__name__, str(exc))
    index = list(v.names) if v.fitted else _UNSET
    numbering = list(v.idx) if v.fitted else _UNSET
    return (outcome, v.supplied, index, numbering)


def _state(fitted, has_param, supplied, param, names, idx=None):
    """Complete a `(fitted, has_param, supplied, param, names)` tuple with the
    mapping's NUMBERING half.

    In-domain the numbering is not a free dimension: restriction (2) pins it to
    0..n-1 on a fitted object -- that is exactly what `numbered_by_place` says --
    so the canonical value is derived here rather than sampled, since sampling it
    would only ever produce states `_requires_holds` rejects. `idx` can be passed
    explicitly, and IS passed by `_numbering_probes`, so the screen is shown to
    be doing work rather than merely asserted."""
    if idx is None:
        idx = list(range(len(names)))
    return (fitted, has_param, supplied, list(param), list(names), list(idx))


def _requires_holds(state):
    """get_feature_names's Requires, plus the two exclusions the module
    docstring records (INPUT DOMAIN). NOTE: no constraint on `param` -- the
    constructor vocabulary is an arbitrary caller-supplied list."""
    fitted, has_param, supplied, param, names, idx = state
    if fitted:
        # Requires(Implies(self.fitted, usable_terms(self.names)))
        if not usable_terms(list(names)):
            return False
        # Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))
        if not _is_numbered_by_place(idx, names):
            return False
        if supplied is None:
            # An absent real `fixed_vocabulary_` has no carrier on a fitted
            # object: the real get_feature_names returns without touching the
            # attribute, so absence is observationally distinct from the
            # model's always-present field.
            return False
    if supplied is None and (not fitted) and has_param and \
            not usable_terms(list(param)):
        # Likewise on the unusable-supplied-list path: the modelled step writes
        # nothing and the real routine validates before its first write, so the
        # flag's entry value is observable there.
        return False
    if not fitted and len(list(idx)) != len(list(names)):
        # An unfitted object carries no mapping, so neither half is meaningful;
        # keeping the two carriers the same length is a bridge hygiene condition
        # (mapping.md §2), not a behavioural restriction.
        return False
    return all(0 <= t < len(_TERMS) for t in list(param) + list(names))


def _branch_of(state):
    """Which impl branch a state exercises (reported in the JSON summary)."""
    fitted, has_param, _, param, _, _ = state
    if fitted:
        return "already-fitted"
    if not has_param:
        return "unfitted-raise"
    return "materialise" if usable_terms(list(param)) else "unusable-reject"


# =============================================================================
# The differential check
# =============================================================================

def _check_pair(state):
    """Diff shadow vs the real patched function on one state. Returns an error
    string on disagreement, else None."""
    assert _requires_holds(state), "generated a state outside Requires: %r" % (state,)

    got = _observe_shadow(state)
    want = _observe_real(_build_real(state))
    if got != want:
        return ("DISAGREEMENT (shadow query vs real patched get_feature_names)\n"
                "  state (fitted, has_param, supplied, param, names, idx) = %r\n"
                "  shadow = %r\n"
                "  real   = %r" % (state, got, want))

    # Also diff the VERBATIM copy of the deep helper's impl region against the
    # real `_validate_vocabulary`, on every input where the helper's own
    # precondition (has_param and a usable supplied list) holds. BOTH halves of
    # the mapping the helper builds are diffed: the names it lists in index
    # order AND the index each of them is given.
    _, has_param, _, param, _, _ = state
    if has_param and usable_terms(list(param)):
        a = Vectoriser(False, True, False, list(param), [], [])
        materialise_verbatim(a)
        b = Vectoriser(False, True, False, list(param), [], [])
        materialise_from_param(b)                   # the real routine
        if (a.names, a.idx, a.fitted, a.supplied) != \
                (b.names, b.idx, b.fitted, b.supplied):
            return ("DISAGREEMENT (verbatim materialise_from_param vs real "
                    "_validate_vocabulary)\n"
                    "  param  = %r\n"
                    "  model  = names=%r idx=%r fitted=%r supplied=%r\n"
                    "  real   = names=%r idx=%r fitted=%r supplied=%r"
                    % (list(param), a.names, a.idx, a.fitted, a.supplied,
                       b.names, b.idx, b.fitted, b.supplied))
    return None


def _check_nonempty_invariant():
    """Verify the reachability premise behind domain restriction (1): no repo
    path yields a present-but-empty `vocabulary_`. Executes both guards."""
    cv = CountVectorizer(vocabulary=[])
    try:
        cv._validate_vocabulary()
    except ValueError:
        pass
    else:
        return ("repo invariant BROKEN: _validate_vocabulary accepted an empty "
                "vocabulary, so vocabulary_ == {} is reachable and domain "
                "restriction (1) is unsound")
    cv = CountVectorizer()
    try:
        cv.fit_transform(["", ""])
    except ValueError:
        pass
    else:
        return ("repo invariant BROKEN: fit_transform produced a vocabulary "
                "from stop-word-only documents, so vocabulary_ == {} is "
                "reachable and domain restriction (1) is unsound")
    return None


def _check_positional_invariant():
    """Verify the reachability premise behind domain restriction (2): every
    `vocabulary_` the repository can put on an object is NUMBERED BY PLACE --
    read in ascending index order, its indices are exactly 0..n-1. Executes the
    guards rather than asserting them."""
    # (a) A Mapping vocabulary with a GAP must be rejected (text.py:289-293).
    cv = CountVectorizer(vocabulary={"beer": 0, "burger": 2})
    try:
        cv._validate_vocabulary()
    except ValueError:
        pass
    else:
        return ("repo invariant BROKEN: _validate_vocabulary accepted a mapping "
                "whose indices skip 1, so a non-positional vocabulary_ is "
                "reachable and domain restriction (2) is unsound")
    # (b) A Mapping vocabulary with a REPEATED index must be rejected
    #     (text.py:287-288).
    cv = CountVectorizer(vocabulary={"beer": 0, "burger": 0})
    try:
        cv._validate_vocabulary()
    except ValueError:
        pass
    else:
        return ("repo invariant BROKEN: _validate_vocabulary accepted a mapping "
                "with a repeated index, so a non-injective vocabulary_ is "
                "reachable and domain restriction (2) is unsound")
    # (c) An ACCEPTED mapping vocabulary (any permutation of 0..n-1) is
    #     positional when read in index order -- the fitted states the bridge
    #     builds are exactly these.
    cv = CountVectorizer(vocabulary={"beer": 2, "burger": 0, "celeri": 1})
    cv._validate_vocabulary()
    if not _is_numbered_by_place(
            [i for t, i in sorted(cv.vocabulary_.items(), key=itemgetter(1))],
            sorted(cv.vocabulary_, key=cv.vocabulary_.get)):
        return ("repo invariant BROKEN: an accepted mapping vocabulary is not "
                "numbered by place: %r" % (cv.vocabulary_,))
    # (d) A list vocabulary is numbered by enumerate (text.py:280-283).
    cv = CountVectorizer(vocabulary=["water", "beer", "coke"])
    cv._validate_vocabulary()
    if sorted(cv.vocabulary_.values()) != list(range(3)):
        return ("repo invariant BROKEN: a list vocabulary was not numbered "
                "0..n-1: %r" % (cv.vocabulary_,))
    # (e) A LEARNED vocabulary_ is positional -- plain fit_transform
    #     (_count_vocab + _sort_features), and again under max_features so
    #     _limit_features' renumbering runs too.
    docs = ["the pizza and beer", "salad water tomato beer",
            "coke coke burger celeri"]
    for kwargs in ({}, {"max_features": 3}, {"min_df": 2}, {"max_df": 2}):
        cv = CountVectorizer(**kwargs)
        cv.fit_transform(docs)
        n = len(cv.vocabulary_)
        if sorted(cv.vocabulary_.values()) != list(range(n)):
            return ("repo invariant BROKEN: a learned vocabulary_ (%r) is not "
                    "numbered 0..n-1: %r" % (kwargs, cv.vocabulary_))
    return None


def _check_failures_distinguishable():
    """The two modelled failures must stay distinguishable on the real side.
    `sklearn.exceptions.NotFittedError` IS a ValueError subclass, so if
    `_observe_real` ever caught ValueError first, every unfitted-object failure
    would silently read as the materialise step's rejection and the
    unfitted-raise branch would be checked against the wrong exception."""
    if not issubclass(RealNotFittedError, ValueError):
        return None                                 # nothing to confuse
    got = _observe_real(_build_real(_state(False, False, False, [], [])))[0]
    if got != ("raise", "NotFittedError"):
        return ("failure bridge BROKEN: the genuinely-unfitted object observed "
                "as %r, not the unfitted-object failure -- the ValueError "
                "handler is shadowing NotFittedError" % (got,))
    got = _observe_real(_build_real(_state(False, True, False, [], [])))[0]
    if got != ("raise", "UnusableTermsError"):
        return ("failure bridge BROKEN: the empty-supplied-list object observed "
                "as %r, not the materialise step's rejection" % (got,))
    return None


def _patch_is_applied():
    """The oracle must be the PATCHED function; a pre-patch run must not pass."""
    cv = CountVectorizer(vocabulary=["beer", "burger"])
    try:
        return cv.get_feature_names() == ["beer", "burger"]
    except Exception:
        return False


def _out_of_domain_probe():
    """The labelled probe for the one impl path the in-domain corpus cannot
    reach (module docstring, INPUT DOMAIN). Reported, not scored."""
    state = _state(True, False, False, [], [])
    try:
        shadow = _observe_shadow(state)
    except Exception as exc:
        shadow = ("raise", type(exc).__name__)
    cv = CountVectorizer()
    cv.vocabulary_ = {}
    cv.fixed_vocabulary_ = False
    real = _observe_real(cv)
    return {"state": "fitted with an empty vocabulary_ (no repo path builds it)",
            "shadow": repr(shadow), "real": repr(real),
            "agree": shadow == real}


def _numbering_probes():
    """Labelled probes for domain restriction (2): states whose mapping is NOT
    numbered by place. Reported, not scored -- `_requires_holds` excludes them,
    so `_check_pair`'s in-domain assertion would fire on them.

    They are run and reported because the interesting question about a
    precondition is what it HIDES. Each probe's `agree` field answers it: the
    query only READS the mapping it reports, so shadow and real observe the same
    thing on a non-positionally numbered object too. Restriction (2) therefore
    excludes no state on which the model and the real patched function disagree
    -- it is a faithfulness statement about which objects the repository can
    build (checked by `_check_positional_invariant`), not cover for a
    divergence."""
    probes = []
    for label, names, idx in (
            ("gapped numbering {beer:0, burger:2}", [0, 1], [0, 2]),
            ("all indices shifted by one", [0, 1, 2], [1, 2, 3]),
            ("F2P names numbered 0,2,4,...", F2P_PARAM,
             [2 * i for i in range(9)]),
            ("singleton numbered 7", [4], [7])):
        state = _state(True, False, False, [], names, idx)
        assert not _requires_holds(state), \
            "a non-positional state passed the domain screen: %r" % (state,)
        try:
            shadow = _observe_shadow(state)
        except Exception as exc:                     # pragma: no cover
            shadow = ("raise", type(exc).__name__)
        real = _observe_real(_build_real(state))
        probes.append({"state": label, "shadow": repr(shadow),
                       "real": repr(real), "agree": shadow == real})
    return probes


# =============================================================================
# Input generation
# =============================================================================

F2P_PARAM = list(range(9))          # the nine food terms of test_feature_names
_ALL = list(range(len(_TERMS)))


def _learned_state_from_real_fit(docs):
    """A fitted/not-supplied state taken from a REAL fit_transform, so the
    boundary corpus contains index orders the repository itself produced. BOTH
    halves are read off the real object -- the numbering too -- so these states
    carry a repository-produced numbering rather than a derived one."""
    cv = CountVectorizer()
    cv.fit_transform(docs)
    pairs = sorted(cv.vocabulary_.items(), key=itemgetter(1))
    names = [_TERM_ID[t] for t, i in pairs if t in _TERM_ID]
    idx = [i for t, i in pairs if t in _TERM_ID]
    if len(names) != len(cv.vocabulary_) or not names:
        return None                                  # a term outside the pool
    return (True, False, False, [], names, idx)


def boundary_states():
    """Boundary cases first: every impl branch at least once, the F2P shape, the
    extremes of each dimension, and the whole unusable-supplied-list class."""
    s = [
        # -- not fitted, no construction-supplied list: the raise branch, with
        #    fixed_vocabulary_ absent (a genuinely fresh object), then present.
        (False, False, None, [], []),
        (False, False, False, [], []),
        (False, False, True, [], []),
        # -- not fitted, USABLE construction-supplied list: materialise branch.
        (False, True, None, F2P_PARAM, []),          # the exact F2P shape
        (False, True, False, F2P_PARAM, []),
        (False, True, True, F2P_PARAM, []),
        (False, True, None, [0], []),                # singleton
        (False, True, None, [4], []),
        (False, True, None, [0, 1], []),
        (False, True, None, list(reversed(F2P_PARAM)), []),   # reverse order
        (False, True, None, _ALL, []),                        # full pool
        (False, True, None, list(reversed(_ALL)), []),
        (False, True, None, [9, 10, 11, 12, 13, 14, 15, 16, 17], []),
        (False, True, None, [23], []),               # the "0" term
        # -- not fitted, usable list, stale `names` present in the state (the
        #    impl must overwrite it, never return the stale value).
        (False, True, None, [0, 1, 2], [5, 6, 7]),
        (False, True, False, F2P_PARAM, [20, 21]),
        # -- already fitted, supplied-at-construction (Requires: names == param).
        (True, True, True, F2P_PARAM, F2P_PARAM),
        (True, True, True, [0], [0]),
        (True, True, True, _ALL, _ALL),
        (True, True, True, list(reversed(F2P_PARAM)), list(reversed(F2P_PARAM))),
        # -- already fitted, learned from data (supplied False): names need not
        #    relate to param at all.
        (True, False, False, [], [0]),
        (True, False, False, [], F2P_PARAM),
        (True, False, False, [], list(reversed(F2P_PARAM))),
        (True, False, False, [], [15, 3, 8, 0]),     # arbitrary index order
        (True, False, False, [], _ALL),
        (True, False, False, [], list(reversed(_ALL))),
        (True, True, False, [0, 1], [8, 7, 6]),      # supplied list ignored
        (True, True, False, F2P_PARAM, [20]),
        (True, True, False, [5], F2P_PARAM),
        # -- already fitted, supplied True, single/full (Requires: names==param)
        (True, True, True, [23], [23]),
        (True, True, True, [20, 21, 22], [20, 21, 22]),
    ]
    # -- not fitted, UNUSABLE construction-supplied list: the reject branch.
    #    Empty and repeated-term lists, every flag value, with and without a
    #    stale `names`. This is the class the real routine rejects with
    #    ValueError rather than materialising.
    for param in ([], [0, 0], [20, 20], [0, 1, 0], [3, 3, 3], [0, 1, 2, 1],
                  [5, 5], F2P_PARAM + [0], [23, 23], _ALL + _ALL):
        for supplied in (None, True, False):
            for stale in ([], [7, 8]):
                s.append((False, True, supplied, list(param), list(stale)))
    # -- already fitted WITH an unusable ctor list: the list must be ignored
    #    entirely (the real function never validates it once fitted).
    for param in ([], [0, 0], [5, 5, 5]):
        for names in ([0], F2P_PARAM, [15, 3, 8]):
            s.append((True, True, False, list(param), list(names)))
    # -- EXHAUSTIVE sweep: every supplied list up to length 3 over a 3-term
    #    pool, so the usable/unusable boundary is covered without sampling.
    for length in range(0, 4):
        for param in itertools.product([0, 1, 2], repeat=length):
            for supplied in (None, True, False):
                s.append((False, True, supplied, list(param), []))
    for docs in (["the pizza beer", "salad water tomato"],
                 ["beer beer beer"],
                 ["this is the first document", "and this is the second one"],
                 ["coke and salad", "burger celeri sparkling", "water"],
                 ["alpha zeta", "alpha", "zeta"]):
        st = _learned_state_from_real_fit(docs)
        if st is not None:
            s.append(st)
    return [c for c in (_state(*st) for st in s) if _requires_holds(c)]


def _rand_param(rng):
    """A supplied list drawn WITH replacement (so repeated terms occur) and of
    a length that may be zero (so the empty list occurs) -- the constructor
    vocabulary is an arbitrary caller-supplied list, not a validated one."""
    k = rng.randint(0, 8)
    return [rng.randrange(len(_TERMS)) for _ in range(k)]


def _rand_names(rng):
    """A materialised mapping's index-ordered names: non-empty and distinct
    (domain restriction (1))."""
    k = rng.randint(1, len(_TERMS))
    return rng.sample(_ALL, k)


def fuzz_state(rng):
    """A uniformly-drawn state (filtered against _requires_holds by the caller)."""
    kind = rng.randint(0, 4)
    if kind == 0:                                   # unfitted, no ctor list
        supplied = rng.choice([None, True, False])
        return (False, False, supplied, [], [])
    if kind in (1, 2):                              # unfitted WITH a ctor list:
        supplied = rng.choice([None, True, False])   # usable or not, at random
        param = _rand_param(rng)
        stale = _rand_names(rng) if rng.random() < 0.3 else []
        return (False, True, supplied, param, stale)
    if kind == 3:                                   # fitted, supplied at ctor
        names = _rand_names(rng)
        return (True, True, True, list(names), list(names))
    if rng.random() < 0.5:                          # fitted, learned from data
        return (True, False, False, [], _rand_names(rng))
    return (True, True, False, _rand_param(rng), _rand_names(rng))


def main():
    if not _patch_is_applied():
        print("G-CONF ERROR: the gold patch is NOT applied -- "
              "CountVectorizer.get_feature_names does not materialise a "
              "construction-supplied vocabulary, so the oracle is pre-patch.")
        return 1

    for check in (_check_nonempty_invariant, _check_positional_invariant,
                  _check_failures_distinguishable):
        err = check()
        if err:
            print("G-CONF FAIL: " + err)
            return 1

    hits = {"unfitted-raise": 0, "unusable-reject": 0,
            "materialise": 0, "already-fitted": 0}
    boundary = boundary_states()
    checked = 0
    for state in boundary:
        err = _check_pair(state)
        if err:
            print(err)
            return 1
        hits[_branch_of(state)] += 1
        checked += 1

    rng = random.Random(SEED)
    fuzzed = 0
    while fuzzed < N_FUZZ:
        state = _state(*fuzz_state(rng))
        if not _requires_holds(state):
            continue
        err = _check_pair(state)
        if err:
            print(err)
            return 1
        hits[_branch_of(state)] += 1
        checked += 1
        fuzzed += 1

    missing = [b for b, n in hits.items() if n == 0]
    if missing:
        print("G-CONF FAIL: impl branch(es) never exercised: %r" % (missing,))
        return 1

    probe = _out_of_domain_probe()
    numbering = _numbering_probes()
    print("G-CONF OK: verbatim shadow of model.py's get_feature_names impl "
          "region == real patched CountVectorizer.get_feature_names on %d "
          "Requires-satisfying states (%d boundary + %d fuzz, seed %d), "
          "including the empty / repeated-term supplied lists the real "
          "_validate_vocabulary rejects; outcome (both failures distinguished), "
          "fixed_vocabulary_, vocabulary_ index order AND the index each "
          "reported name carries all agree, and the verbatim "
          "materialise_from_param body == the real _validate_vocabulary on "
          "every usable-supplied-list input (both halves of the mapping it "
          "builds); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked,
        "boundary": len(boundary),
        "fuzz": N_FUZZ,
        "disagreements": 0,
        "seed": SEED,
        "branch_hits": hits,
        "shadow": "direct (contract-stripped impl region of model.py, verbatim; "
                  "the @Pure usable_terms quantifier pair spelled as the "
                  "equivalent comprehension)",
        "oracle": "called: CountVectorizer.get_feature_names "
                  "(sklearn/feature_extraction/text.py:994, gold-patched)",
        "failures_observed": {
            "NotFittedError": "sklearn.exceptions.NotFittedError "
                              "(_check_vocabulary, text.py:304)",
            "UnusableTermsError": "ValueError from _validate_vocabulary "
                                  "(text.py:282 duplicate / text.py:294 empty)",
        },
        "a_reference_callee": "realised by the real "
                             "VectorizerMixin._validate_vocabulary; the "
                             "verbatim model body diffed against it too",
        "repo_invariant_checked": [
            "vocabulary_ is never present-but-empty (both assignment guards "
            "executed)",
            "vocabulary_ is always numbered by place: the two Mapping guards "
            "(gap / repeated index) executed and still rejecting, an accepted "
            "permutation mapping and a list vocabulary observed positional, and "
            "a learned vocabulary_ observed positional plain and under "
            "max_features / min_df / max_df so _limit_features renumbers",
        ],
        "out_of_domain_probe": probe,
        "numbering_probes": numbering,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
