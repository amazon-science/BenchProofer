#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-10908.

Executes the REAL package callee — the UNCHANGED `_validate_vocabulary` routine
on `CountVectorizer` — and asserts every observation matches the deep model in
model.py. There is NO consumed `@ContractOnly` axiom; the single A-reference is
the deep helper `materialise_from_param`, validated `==` the real
`_validate_vocabulary` on the list-vocabulary domain, plus the differential
witness that the change is observable.

The A-reference checks (model.py `materialise_from_param`):

  For a freshly-constructed `CountVectorizer(vocabulary=<usable list>)` — a
  non-empty list with no repeated term, i.e. `usable_terms` — on an object with a
  construction-supplied list and no materialised mapping:
    * before materialisation the mapping is absent: hasattr(cv,'vocabulary_')
      is False  (model: self.fitted == False);
    * after the UNCHANGED _validate_vocabulary runs, the mapping is present, the
      object reports a fixed vocabulary, and the index-ordered feature names
      equal the supplied list in order
        (model: self.fitted, self.supplied, ToSeq(self.names) == ToSeq(self.param));
    * term i of the supplied list carries INDEX i in the mapping that is built —
      asserted term by term against `vocabulary_[term]`, not merely as "the names
      come back in that order", because the order alone is the same observation
      for `{a: 0, b: 1}` and `{a: 0, b: 7}`
        (model: `Ensures(numbered_by_place(self.idx, self.names))`);
    * the helper's domain is exactly `usable_terms(self.param)` and that bound is
      honest: a list with a repeated term is rejected, and so is an empty one, so
      the helper is NOT claimed to materialise a list it cannot turn into a
      mapping;
    * on that rejection the routine writes NOTHING — it validates before its
      first assignment, so `vocabulary_` stays absent and `fixed_vocabulary_`
      keeps its entry value. This is the state the caller's rejection exit claims
      (`not self.fitted and self.supplied == Old(self.supplied)`), so it is
      observed here rather than assumed.

  The CALLER'S REPRESENTATION-INVARIANT PREMISE
  (`check_every_mapping_is_numbered_by_place`):
    `get_feature_names` requires an ALREADY-fitted object's mapping to be
    numbered by place, and claims the same of the mapping it hands back. That
    premise is about which fitted objects the package can produce — unchanged
    code — so it is executed here rather than argued in prose: the two
    Mapping-vocabulary guards still reject a gapped, a repeated, a 1-based and a
    trailing-gap numbering; an accepted permutation mapping, a list vocabulary,
    and a learned `vocabulary_` (plain and under `max_features` / `min_df` /
    `max_df`, so `_sort_features`' and `_limit_features`' renumberings run) are
    each observed positional. If any of that stopped holding, a non-positionally
    numbered `vocabulary_` would be reachable and the precondition would be
    excluding a real state instead of describing the representation.

  The DIFFERENTIAL WITNESS (the change is observable):
    * the PRE-PATCH code path — go straight to the unusable check
      (`_check_vocabulary`) WITHOUT first materialising — raises NotFittedError
      for an object that has a construction-supplied list but no materialised
      mapping;  while
    * the POST-PATCH behaviour — materialise on demand, then check — succeeds
      and returns the supplied list in order;  and
    * a genuinely-unfitted object (no `vocabulary` supplied) raises
      NotFittedError on BOTH paths (the failure is still raised when there is
      truly nothing to materialise).

Imports nothing beyond the package under test (`sklearn`). Runs at the
instance's base_commit: every assertion holds against the UNCHANGED
`_validate_vocabulary` / `_check_vocabulary` routines and reproduces the
pre-patch `get_feature_names` failure directly (it does NOT call the patched
method). Exit 0 iff every obligation holds.
"""
import sys

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.exceptions import NotFittedError


def _feature_names_from_vocabulary_(cv):
    """The index-ordered feature names — exactly the (unchanged) body of
    get_feature_names after the fitted check: vocabulary_ terms in index order."""
    from operator import itemgetter
    return [t for t, i in sorted(cv.vocabulary_.items(), key=itemgetter(1))]


def check_materialise_matches_helper(vocab):
    """A-reference: the UNCHANGED _validate_vocabulary materialises the mapping
    from a construction-supplied list exactly as the deep helper models it."""
    cv = CountVectorizer(vocabulary=vocab)

    # before materialisation: no mapping present  (model: not self.fitted)
    assert not hasattr(cv, "vocabulary_"), (
        "freshly-constructed vectoriser already reports a materialised mapping")

    # run the UNCHANGED materialise-from-supplied-list routine
    cv._validate_vocabulary()

    # the three Ensures of materialise_from_param:
    assert hasattr(cv, "vocabulary_"), (
        "_validate_vocabulary did not materialise the mapping")            # self.fitted
    assert cv.fixed_vocabulary_ is True, (
        "_validate_vocabulary did not mark a construction-supplied "
        "vocabulary as supplied-at-construction")                         # self.supplied
    names = _feature_names_from_vocabulary_(cv)
    assert names == list(vocab), (
        "index-ordered feature names do not equal the supplied list in order")
    # ToSeq(self.names) == ToSeq(self.param)

    # numbered_by_place(self.idx, self.names): term i of the supplied list is
    # given index i. Asserted TERM BY TERM against the mapping's own value, not
    # merely as "the names come out in that order" -- the order alone is the same
    # for {a: 0, b: 1} and {a: 0, b: 7}, and it is the actual index that names the
    # column every other entry point on the object addresses.
    for position, term in enumerate(vocab):
        assert cv.vocabulary_[term] == position, (
            "term %r at place %d of the supplied list was given index %r -- "
            "materialise_from_param's numbered_by_place Ensures would be "
            "unfaithful" % (term, position, cv.vocabulary_[term]))
    assert sorted(cv.vocabulary_.values()) == list(range(len(vocab))), (
        "the materialised mapping's indices are not exactly 0..n-1: %r"
        % (sorted(cv.vocabulary_.values()),))


def check_unusable_rejected_without_writing(vocab, what):
    """Domain honesty AND the rejection state: a list that cannot become a
    mapping — empty, or with a term listed twice — is rejected, and the routine
    writes nothing on the way out.

    `usable_terms` is exactly the helper's precondition, so this is the boundary
    of what the model claims the routine does. The no-write half is what the
    caller's rejection exit asserts (`not self.fitted` and the supplied flag
    unchanged), so it is observed on both halves of the class."""
    cv = CountVectorizer(vocabulary=vocab)
    sentinel = "<entry value>"
    cv.fixed_vocabulary_ = sentinel          # an observable entry value
    try:
        cv._validate_vocabulary()
    except ValueError:
        assert not hasattr(cv, "vocabulary_"), (
            "%s vocabulary was rejected but a mapping was materialised anyway "
            "-- the caller's `not self.fitted` rejection claim is unfaithful"
            % what)
        assert cv.fixed_vocabulary_ is sentinel, (
            "%s vocabulary was rejected but fixed_vocabulary_ was overwritten "
            "-- the caller's `self.supplied == Old(self.supplied)` rejection "
            "claim is unfaithful" % what)
        return
    raise AssertionError("%s vocabulary was not rejected" % what)


def check_every_mapping_is_numbered_by_place():
    """The caller's REPRESENTATION INVARIANT premise, executed against the
    UNCHANGED routines: every `vocabulary_` this package can put on an object is
    numbered by place -- read in ascending index order, its indices are exactly
    0..n-1.

    `get_feature_names` states this as
    `Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))` and
    claims the same of the mapping it leaves behind. A premise about which
    already-fitted objects EXIST is about unchanged code, so it belongs here, at
    base_commit, and is executed rather than asserted in prose."""
    # (a) a Mapping vocabulary is ACCEPTED only if its indices are a bijection
    #     onto 0..n-1 (the repeated-index and missing-index guards).
    for vocab, what in (({"beer": 0, "burger": 2}, "index 1 missing"),
                        ({"beer": 0, "burger": 0}, "repeated index"),
                        ({"a": 1, "b": 2}, "1-based numbering"),
                        ({"a": 0, "b": 1, "c": 3}, "gap at the end")):
        cv = CountVectorizer(vocabulary=vocab)
        try:
            cv._validate_vocabulary()
        except ValueError:
            pass
        else:
            raise AssertionError(
                "a mapping vocabulary with %s was ACCEPTED, so a non-positional "
                "vocabulary_ is reachable and get_feature_names's "
                "numbered_by_place premise is unfaithful" % what)
    # (b) an accepted permutation mapping is positional read in index order.
    cv = CountVectorizer(vocabulary={"beer": 2, "burger": 0, "celeri": 1})
    cv._validate_vocabulary()
    assert sorted(cv.vocabulary_.values()) == [0, 1, 2], cv.vocabulary_
    assert _feature_names_from_vocabulary_(cv) == ["burger", "celeri", "beer"]

    # (c) a LEARNED mapping is positional too -- plainly, and under each pruning
    #     parameter, so _sort_features' and _limit_features' renumberings run.
    docs = ["the pizza and beer", "salad water tomato beer",
            "coke coke burger celeri"]
    for kwargs in ({}, {"max_features": 3}, {"min_df": 2}, {"max_df": 2}):
        cv = CountVectorizer(**kwargs)
        cv.fit_transform(docs)
        n = len(cv.vocabulary_)
        assert sorted(cv.vocabulary_.values()) == list(range(n)), (
            "a learned vocabulary_ (%r) is not numbered 0..n-1: %r"
            % (kwargs, cv.vocabulary_))
        for position, term in enumerate(_feature_names_from_vocabulary_(cv)):
            assert cv.vocabulary_[term] == position, (
                "learned mapping (%r) is not numbered by place at %r"
                % (kwargs, term))


def _prepatch_get_feature_names(cv):
    """The PRE-PATCH get_feature_names: straight to the unusable check, NO
    on-demand materialisation."""
    cv._check_vocabulary()
    return _feature_names_from_vocabulary_(cv)


def check_differential_witness(vocab):
    """The change is observable: an object with a construction-supplied list but
    no materialised mapping raises on the PRE-PATCH path and succeeds on the
    POST-PATCH path; a genuinely-unfitted object raises on BOTH."""
    # (a) has a supplied list, not yet materialised
    cv = CountVectorizer(vocabulary=vocab)
    raised = False
    try:
        _prepatch_get_feature_names(cv)          # pre-patch path
    except NotFittedError:
        raised = True
    assert raised, (
        "pre-patch path did NOT raise on a vectoriser with a supplied "
        "vocabulary — the bug is not reproduced, so the change is not "
        "differential")

    # post-patch behaviour: materialise on demand, then return names
    cv2 = CountVectorizer(vocabulary=vocab)
    if not hasattr(cv2, "vocabulary_"):
        cv2._validate_vocabulary()
    cv2._check_vocabulary()
    names = _feature_names_from_vocabulary_(cv2)
    assert names == list(vocab), (
        "post-patch behaviour did not return the supplied list in order")
    assert cv2.fixed_vocabulary_ is True

    # (b) genuinely unfitted: no vocabulary supplied -> raises on BOTH paths
    cv3 = CountVectorizer()                       # vocabulary is None
    raised_pre = False
    try:
        _prepatch_get_feature_names(cv3)
    except NotFittedError:
        raised_pre = True
    assert raised_pre, "genuinely-unfitted object did not raise on pre-patch path"

    cv4 = CountVectorizer()
    raised_post = False
    try:
        if not hasattr(cv4, "vocabulary_"):
            cv4._validate_vocabulary()            # no-op: vocabulary is None
        cv4._check_vocabulary()                   # still raises
        _feature_names_from_vocabulary_(cv4)
    except NotFittedError:
        raised_post = True
    assert raised_post, (
        "genuinely-unfitted object did not raise on post-patch path — the "
        "failure must still be raised when there is nothing to materialise")


def main():
    vocabs = [
        ["beer", "burger", "celeri", "coke", "pizza",
         "salad", "sparkling", "tomato", "water"],
        ["a"],
        ["z", "y", "x", "w"],            # reverse order: index follows position
        ["and", "document", "first", "is", "one",
         "second", "the", "third", "this"],
        [str(i) for i in range(50)],     # larger, distinct
    ]
    for vocab in vocabs:
        check_materialise_matches_helper(vocab)
        check_differential_witness(vocab)

    check_every_mapping_is_numbered_by_place()

    for vocab in (["pizza", "beer", "pizza"], ["x", "x"],
                  ["a", "b", "c", "b"], ["q", "q", "q"]):
        check_unusable_rejected_without_writing(vocab, "duplicate-term")
    check_unusable_rejected_without_writing([], "empty")

    print("G-AX OK: deep helper materialise_from_param == real "
          "_validate_vocabulary on its whole domain: every usable supplied list "
          "(non-empty, no repeated term) materialises the mapping, sets "
          "fixed_vocabulary_, and yields index-ordered names == the supplied "
          "list with term i of that list at index i (checked term by term, so "
          "the NUMBERING and not merely the order is observed); every UNUSABLE "
          "list (empty, or a term listed twice) is rejected "
          "with no write at all, matching the caller's rejection exit; the "
          "caller's numbered-by-place premise holds of every mapping this "
          "package can build (the two Mapping-vocabulary guards reject a gapped "
          "and a repeated numbering; an accepted permutation, a list vocabulary "
          "and a learned vocabulary_ -- plain and under max_features / min_df / "
          "max_df -- are all positional); "
          "differential witness confirmed (pre-patch raises NotFittedError on a "
          "supplied-vocabulary object, post-patch returns the names; "
          "genuinely-unfitted raises on both).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
