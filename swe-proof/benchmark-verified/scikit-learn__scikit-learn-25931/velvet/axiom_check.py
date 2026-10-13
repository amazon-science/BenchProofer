#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25931.

Executes the REAL scikit-learn callees that Solution.lean abstracts as
A-reference value legs, on a real fitted ``IsolationForest``, over boundary +
fuzzed inputs (both ``np.ndarray`` and ``pd.DataFrame`` carriers), and asserts
that every observation matches the model. No CONSUMED axiom exists in this
bundle; both checks are A-reference (value/contract identities the proof's
function symbols stand for).

IMPORTANT — this gate runs against the UNPATCHED base commit (G-AX does not
apply the gold patch). Therefore it may only touch callees that already exist
at ``base_commit``. The genuinely UNCHANGED callee the scoring paths sit on top
of is

    ``-self._compute_chunked_score_samples(X)``     (_iforest.py:442, base commit)

— the screening-independent ensemble scorer modeled by ``anomalyScores``
(mapping.md §3.1). The patch's private ``_score_samples`` is, by definition,
exactly ``check_is_fitted(self); return -self._compute_chunked_score_samples(X)``
(no ``_validate_data``). We therefore EMULATE that screen-free scoring path with
the unchanged callee, and assert the A-reference facts against the real
base-commit code. We never call ``_score_samples`` (it does not exist until the
patch is applied) and never axiomatize the function under change.

The kind-A checks (all A-reference — see refinement.md / mapping.md §3):

  (A-reference §3.1, value equality / screening-independence)
      score_samples(X)  ==  screen_free_scores(X_prepared)  element-wise.
      ``score_samples`` validates the raw input (one screen) and then scores
      with the unchanged callee; the screen-free path scores the already-prepared
      matrix with the SAME unchanged callee. Their equality is exactly the fact
      that ``_validate_data`` is value-neutral, which is why ``offset_`` is
      numerically identical before and after the patch. Modeled by
      ``anomalyScores`` — the sequence the public entry point serves the numbers
      of, and the sequence the fitting tail's order statistic is taken of. The
      public result being EXACTLY those numbers is also what grounds
      ``scoreValues`` as a reading and not a computation: in the repository a
      produced sequence IS its numbers, so the reading is the identity there. What
      that reading hands out is fenced in its own right, by the ELEMENT type — see
      the score-position leg below.

  (A-reference §3.1, screening is an ACTION with exactly one spelling)
      ``score_samples`` performs EXACTLY ONE ``_validate_data`` call (the public
      screen), while the screen-free building block
      ``_compute_chunked_score_samples`` performs ZERO. This is the asymmetry the
      modeled surface stands on: the public entry point screens its argument and
      then scores what the screen hands back, while the fitting tail derives its
      order statistic from the screen-free value alone — the Lean image of
      ``_score_samples`` having no ``_validate_data`` call at all. No counter
      models it any more (a counter is a freely-written value, and every pin over
      one was measured defeatable — properties.py records the history); the claim
      is carried structurally instead (mapping.md §6). The COUNTS are still the
      repository fact that structure rests on, so they are measured here, by
      patching the instance's ``_validate_data`` with a wrapper that tallies
      invocations.

  (A-reference §3.2)
      percentileAt(scores, q)  ==  numpy.percentile(scores, q).

  (A-reference §3.1, ONE SCORE PER SAMPLE — ``check_score_sequence_provenance``)
      The sequence produced for a prepared matrix holds exactly as many real
      numbers as the matrix holds samples, and the same matrix scored twice reads
      back bit-identically. Those two facts are what let Solution.lean carry a
      produced sequence as an opaque ``Scores`` carrier read by ``scoreValues``:
      the sequences that exist are per-matrix ones, non-empty wherever the fitting
      tail's sample fence admits the matrix, and reading them is not an action.

  (A-reference, WHY A MATRIX IS MODELED AS AN OBJECT — ``check_object_properties``)
      Solution.lean models a matrix as an opaque TYPE (three of them: as a caller
      supplies it, as a screen hands it back, and as presented to a screen) rather
      than as the sequence of numbers it holds. That is forced by the repository,
      not chosen for convenience, and this is where it is measured: two matrices
      holding BIT-IDENTICAL numbers disagree on every property a screen decides.

        * LABELLING -> the advisory. The same numbers presented with the
          per-column labelling the model recorded, and presented bare, differ on
          whether a screen reports a labelling discrepancy about them.
        * WIDTH -> the refusal. The same numbers arranged as two different widths
          differ on whether a screen turns them away at all.
        * LAYOUT -> readability. The same numbers in a dense arrangement and in a
          compressed-column one differ on whether the screen-free scorer can read
          them as they stand.

      A reference over a bare sequence of numbers would therefore have to return
      two different answers for one argument — i.e. it could not exist, which is
      what makes an earlier revision of this bundle's contents-carrier modeling
      unsound rather than merely coarse. The same function also measures the
      VALUE side of the first leg: those two matrices score to bit-identical
      values, which is what licenses the public entry point's value clause being
      unconditional in the labelling.

  (non-vacuity / the bug is real) for a model FITTED WITH feature names (a
      DataFrame), the PUBLIC ``score_samples`` called on the prepared array
      raises the spurious ``UserWarning: X does not have valid feature names,
      but IsolationForest was fitted with feature names`` (its internal screen
      validates a nameless array), whereas the screen-free path raises NO such
      warning — confirming the modeled difference (re-screen vs not) is the
      behavioural defect, not vacuous.

  (A-reference, the handle-property DOMAIN — ``screenAdvises`` / ``screenRefuses``)
      The screen reaches TWO distinct verdicts on a handle, and Solution.lean
      models them as two separate properties because the repository treats them
      differently:

        * ``screenAdvises X`` — the screen REPORTS a labelling discrepancy and
          scores the handle anyway. Measured: it is drawn exactly when the handle
          presents no column labelling while the model recorded one (or the
          converse); it is a ``UserWarning``, i.e. an ambient effect with no
          returned value a caller could drop; and the handle is still scored, to
          BIT-IDENTICAL values (leg (iv) below). Hence no clause of Solution.lean
          lets a labelling condition a score VALUE, and the advisory is carried as
          the public entry point's ARGUMENT RESTRICTION rather than as an outcome.
        * ``screenRefuses X`` — the screen RAISES, and no scores exist for that
          handle at all. Measured (``check_screen_refusals``): a width that
          disagrees with the recorded one (``ValueError: X has 2 features, but
          IsolationForest is expecting 3 features as input``), a handle holding no
          samples (``Found array with 0 sample(s) ... while a minimum of 1 is
          required``), a magnitude the recorded working precision cannot
          represent (``Input X contains infinity or a value too large for
          dtype('float32')`` at 1e300 — so the boundary is REPRESENTABILITY, not
          finiteness), and a labelling that DISAGREES with the recorded one
          (permuted: "must be in the same order as they were in fit"; disjoint:
          "unseen at fit time"). This is the verdict ``scorePublic`` reports by
          serving nothing.

      ``check_label_agreement`` measures the labelling legs on real labelled
      models; ``check_screen_refusals`` measures the shape/precision legs and the
      negative control that an ordinary handle is not refused.

  (A-reference, BOTH SCREEN PROPERTIES ARE DECIDED BY INSPECTION —
   ``check_inspection_decides``)
      Solution.lean lets ``screenRefuses`` and ``screenAdvises`` be named
      ANYWHERE, the fitting tail included, on the ground that reading either is an
      inspection of the matrix and not a screen of it. That liberty is load-bearing
      (the fitting tail's admissible re-screen BRANCHES on the advisory) and would
      be unsound if deciding one required performing a screen — the branch would
      then be the ambient report it is meant to avoid. Measured: an inspector
      reading only the matrix — its presented labelling, its width, its sample
      count, its element kind and its magnitudes, against what the model recorded
      — agrees with the real screen's OUTCOME on both properties over every
      fixture, with two negative controls (a finiteness inspector and a
      labelling-blind inspector are each measured to disagree somewhere, so the
      agreement is not obtainable by inspecting less). Note the direction this
      does NOT extend to: a screen's prepared OUTPUT is not decided by inspection,
      it is what the screen produces, which is why Solution.lean confines it to a
      reference on the CALLER'S handle instead of one on a matrix as presented.

  (WHY THE MODELED DOMAIN IS STILL NARROWER THAN THE CALLEE — and by exactly how
   much, which is the point of leg (iv))
      ``scorePublic``'s ``require screenAdvises samples = false`` excludes the
      handles the screen has something to advise about, and the repository DOES
      score those (leg (iv)). That exclusion is deliberate and it is the whole
      discriminator of this cell: drawing that advisory on the already-prepared
      training matrix IS the defect under repair, so a call site that would draw
      it is inadmissible rather than promised an outcome. What the domain now
      covers, and an earlier revision did not, is every handle the graded scoring
      surface actually uses: the unlabelled handle of an unlabelled model and the
      agreeing handle of a labelled one both satisfy ``screenAdvises = false``, so
      the value clause is unconditional in the labelling there. The earlier
      revision keyed the public value clause on the labelling itself (a
      handle-labelling reference), which left the ordinary ndarray carriers of
      ``sklearn/ensemble/tests/test_iforest.py`` outside the promise entirely;
      leg (iv) is the measurement that established it, and it is retained here as
      the standing control on the repair.

  (the ``hasSamples`` fence — ``check_empty_handle_fences``)
      The fitting tail's obligation requires a prepared matrix holding at least
      one sample. Measured:
      the screen-free scorer does not return an empty score sequence for an empty
      prepared handle, it RAISES
      (``InvalidParameterError: The 'n' parameter of gen_batches must be an int in
      the range [1, inf). Got 0 instead.``), and the order statistic of an empty
      score sequence raises as well (``IndexError``). So promising a value there
      would be promising something the repository never produces; the fence
      excludes it. The second leg is also why the score sequence is a CARRIER type
      in the spec rather than a sequence of numbers a text can write down: a
      reference total over such a type would promise the order statistic of the
      empty sequence, and a fence on the method's PARAMETER does not reach the
      other places that reference can be named at (see the point carrier, next).

  (the PERCENTILE POINT, A CARRIER — ``check_percentile_point_fences`` and
   ``check_point_provenance``)
      The order-statistic callee is PARTIAL in the requested point as well as in
      the sequence: asked for a point outside the range a percentage occupies it
      reports no order statistic at all but refuses the request (``ValueError:
      Percentiles must be in the range [0, 100]``). ``check_percentile_point_
      fences`` measures that partiality — outside the range on both sides and just
      past each endpoint, with the two ENDPOINTS plus the interior as the control
      that no more than the divergence is excluded.

      An earlier revision of Solution.lean fenced it with a precondition
      (``0 <= q <= 100``) and was refuted: a precondition fences the argument the
      method is CALLED WITH, while a total reference may be NAMED at any term of
      its argument type anywhere inside a body, so rivals that named the order
      statistic at a refused point in a value-neutral position verified while
      their faithful counterparts raise. The point is an opaque CARRIER now, so
      such a term cannot be written at all — and what that shifts onto this gate
      is a provenance obligation, ``check_point_provenance``: every point that
      does reach the fitting tail must lie inside the range the callee is defined
      at. Measured in two legs: the point the tail requests is ``100.0 *
      contamination`` (the offset a real fit records is bit-identical to the order
      statistic of that model's own screen-free scores at that point — the fitting
      tail's obligation itself, observed on the repository), and the estimator
      REFUSES a contamination level whose point would fall outside the range, with
      the admissible interval accepted as the control. So the carrier promises a
      value exactly where the repository derives one.

  (the WIDTH leg of ``scorableAsGiven`` — ``check_handle_properties`` leg (c))
      ``scorableAsGiven`` is the reference that fences whatever the screen-free
      scorer cannot consume AS IT STANDS, and that is not decided by the
      arrangement of the numbers alone: a prepared matrix NARROWER than the width
      the model was fitted on is a perfectly ordinary dense arrangement, and the
      scorer still raises on it (it indexes a feature the matrix does not have).
      Leg (c) measures all three: the dense matrix of the recorded width is
      consumed, the compressed-column one is refused, and the narrower one is
      refused. So the reference is read as consumability and not as layout alone,
      which is what keeps the offset tail from promising an offset for a matrix
      the scorer turns away.

  (the CONTAINER leg of ``scorableAsGiven`` — ``check_sparse_container_fence``)
      The same reference is what the PUBLIC entry point's own domain fence is built
      from (``require scorableAsGiven (preparedOf handle) = true``), and this leg is
      why that fence has to be there at all: the screen and the scorer disagree
      about one family of matrices. A handle in the newer sparse container is
      ACCEPTED by the public screen -- which hands back a prepared matrix of the
      same numbers, compressed by row, in the working precision -- and the scorer
      then refuses that matrix, as does the public entry point itself. So a clause
      unconditional over every accepted handle would promise scores where the
      repository reports none. Measured with the controls that bound the fence: the
      dense matrix and the older sparse containers of those same numbers are all
      consumed and all served, and ``fit`` refuses the newer container outright, so
      the offset tail never holds one either.

  (the SCORE POSITION, i.e. the reading's ELEMENT carrier —
   ``check_score_index_fences``)
      Reading a produced score sequence is PARTIAL in the position read, the same
      way the order statistic is partial in its point: asked for the score at a
      position the sequence does not have, the repository reports nothing and
      refuses the read (``IndexError: index 1000 is out of bounds for axis 0 with
      size 8``). Measured across sample counts at a position far past the end, at
      the length itself and at the mirror position before the start, on the
      screen-free sequence and on the public entry point's own result, and measured
      once more with the value read then cancelled away — the refusal happens at
      the READ, so a value-neutral use of it does not avoid it.

      That is why ``scoreValues`` hands back a sequence over an opaque ELEMENT
      type. A sequence whose elements a text can write down admits an UNGUARDED
      read at any position, needing only a default element to fall back on where
      the position is absent, so a text could name a score in a region where the
      repository derives none — and, as with the point, a precondition would fence
      only the argument a method is called with and not the other places the
      reading can be named at. With the element a carrier there is no default to
      fall back on. The controls bound the fence: every position a sequence HAS is
      readable, the public entry point's served sequence is bit-identical to that
      reading of the screen-free one, and the order statistic of the whole sequence
      is defined — so what is excluded is exactly the read the repository refuses.

  (the RECORDED OFFSET, i.e. the reported value's own carrier —
   ``check_offset_arithmetic_fences``)
      ARITHMETIC on the number a fitting tail records is partial too, and that is
      the last place a value the repository has no counterpart for could be
      written down. Divided by zero — by a literal zero, or by its own difference
      with itself — a recorded offset yields NO number: it refuses outright as a
      plain real (``ZeroDivisionError: float division by zero``) and reports a
      non-finite value together with a ``RuntimeWarning`` in the working precision
      the scorer produces. The reference language disagrees: division there is
      TOTAL and ``x / 0`` is the rational 0. So a reported offset whose TYPE
      admits division would let a text derive a value the repository does not
      have, and — as with the point and the position — a precondition cannot
      fence it, since the arithmetic may be named anywhere inside a body and a
      discarded quotient is invisible to any postcondition. Hence the reported
      offset is the opaque carrier ``Offset``, whose only terms are the order
      statistic the fitting tail reports and ``defaultOffset``, the constant the
      requestless fitting path records (measured: -0.5 on every model, and never
      the order statistic a requested contamination level determines). The
      controls bound the fence: negation, division by one and by two, the order
      statistic taken again and the count of the scores are all finite and warn
      about nothing. The leg also grounds the R-ARITH reading rule (mapping.md
      §2): the reference language's rational arithmetic is EXACT and the
      repository's on these numbers is not, so a rational term in the reference
      file denotes no repository quantity at all.

Imports only numpy / pandas / scikit-learn — the real packages the bug lives in.
Runs in-container against the UNPATCHED base commit. Exit 0 iff every obligation
holds.
"""
import sys
import types
import warnings

import numpy as np


def _fit_model(rng, n=40, n_features=3, contamination=0.05, as_dataframe=False):
    """Fit a real IsolationForest. If ``as_dataframe`` the training matrix is a
    pandas DataFrame (so ``feature_names_in_`` is recorded — needed to exhibit
    the feature-name warning on the public scoring path)."""
    from sklearn.ensemble import IsolationForest
    data = rng.randn(n, n_features)
    if as_dataframe:
        import pandas as pd
        X = pd.DataFrame(data, columns=["f%d" % i for i in range(n_features)])
    else:
        X = data
    clf = IsolationForest(random_state=0, contamination=contamination,
                          n_estimators=20)
    clf.fit(X)
    return clf


def _prepare(clf, X):
    """The single public screen: validate raw input into the prepared float32
    matrix exactly as ``score_samples`` does (``_iforest.py:436``)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return clf._validate_data(X, accept_sparse="csr", dtype=np.float32,
                                  reset=False)


def screen_free_scores(clf, Xp):
    """Faithful emulation of the patch's private ``_score_samples`` on an
    already-prepared matrix ``Xp``: ``check_is_fitted; return
    -_compute_chunked_score_samples(Xp)`` — built ONLY from base-commit callees,
    and performing NO ``_validate_data`` screen."""
    from sklearn.utils.validation import check_is_fitted
    check_is_fitted(clf)
    return -np.asarray(clf._compute_chunked_score_samples(Xp))


def _count_validate(fn):
    """Run ``fn(clf)`` with the instance's ``_validate_data`` wrapped to tally
    invocations; return the count. Restores the class method afterward."""
    def runner(clf):
        counts = {"n": 0}
        orig = clf._validate_data.__func__  # unbound
        def counting(self, *args, **kwargs):
            counts["n"] += 1
            return orig(self, *args, **kwargs)
        clf._validate_data = types.MethodType(counting, clf)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fn(clf)
        finally:
            del clf._validate_data  # restore the class method
        return counts["n"]
    return runner


def check_value_equality(clf, X_raw, label):
    """A-reference §3.1: score_samples(X) == screen-free scoring of the prepared
    matrix, element-wise (screening-independence of the score value)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")             # public path may warn
        pub = np.asarray(clf.score_samples(X_raw))
    Xp = _prepare(clf, X_raw)
    prv = screen_free_scores(clf, Xp)
    assert pub.shape == prv.shape, (
        "public / screen-free shape mismatch on %s: %r vs %r"
        % (label, pub.shape, prv.shape))
    assert np.allclose(pub, prv, rtol=0, atol=0), (
        "A-reference unsound on %s: score_samples != screen-free scoring "
        "(max abs diff %r)" % (label, float(np.max(np.abs(pub - prv)))))


def check_screen_counts(clf, X_raw, label):
    """A-reference §3.1: the PUBLIC ``score_samples`` screens exactly once; the
    screen-free building block ``_compute_chunked_score_samples`` screens zero
    (so the emulated private path screens zero too — it adds only
    ``check_is_fitted`` and a negation, neither of which validates)."""
    pub_calls = _count_validate(lambda clf: clf.score_samples(X_raw))(clf)
    Xp = _prepare(clf, X_raw)
    chunk_calls = _count_validate(
        lambda clf: clf._compute_chunked_score_samples(Xp))(clf)
    assert pub_calls == 1, (
        "screening contract unsound on %s: score_samples did %d "
        "_validate_data calls, expected exactly 1" % (label, pub_calls))
    assert chunk_calls == 0, (
        "screening contract unsound on %s: _compute_chunked_score_samples did "
        "%d _validate_data calls, expected 0 (the screen-free path performs no "
        "validation)" % (label, chunk_calls))


def check_percentile(scores, q):
    """A-reference §3.2: percentileAt == numpy.percentile."""
    observed = float(np.percentile(scores, q))
    expected = float(np.percentile(np.asarray(scores), q))   # the modeled value
    assert observed == expected, (
        "percentileAt axiom unsound at q=%r: %r vs %r" % (q, observed, expected))


def check_bug_is_real(clf_df):
    """Non-vacuity: a model fitted WITH feature names (a DataFrame), scored via
    the PUBLIC path on the prepared (nameless) array, raises the spurious
    feature-name UserWarning; the screen-free path does not."""
    n_features = clf_df.n_features_in_
    rng = np.random.RandomState(123)
    import pandas as pd
    Xdf = pd.DataFrame(rng.randn(5, n_features),
                       columns=["f%d" % i for i in range(n_features)])
    Xnd = Xdf.to_numpy()   # the validated, nameless array fit feeds internally

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        clf_df.score_samples(Xnd)
    pub_warned = any("valid feature names" in str(x.message) for x in w)

    Xp = _prepare(clf_df, Xnd)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        screen_free_scores(clf_df, Xp)
    prv_warned = any("valid feature names" in str(x.message) for x in w)

    assert pub_warned, (
        "non-vacuity failed: public score_samples did NOT raise the "
        "feature-name warning on a nameless array (model fitted with names) — "
        "the modeled bug is not present")
    assert not prv_warned, (
        "non-vacuity failed: the screen-free path DID raise the feature-name "
        "warning — the fix path is not screen-free")


def check_label_agreement(clf_df, label):
    """Grounding for the LABELLING legs of the two screen verdicts (mapping.md §1,
    §5 and the axiom comment in Solution.lean).

    Returns the number of observations made, so main() can report the count.

    Four legs, all against the real base-commit ``score_samples``:
      (i)   an AGREEING labelling — ``screenAdvises = false``,
            ``screenRefuses = false``: scores normally and draws no feature-name
            advisory, so the modeled entry point promises scores there.
      (ii)  a PERMUTED labelling (same labels, different order) —
            ``screenRefuses = true``: the real entry point RAISES rather than
            scoring, which is the verdict the modeled entry point reports by
            serving nothing.
      (iii) a DISJOINT labelling — ``screenRefuses = true``: refused likewise.
      (iv)  an UNLABELLED handle of a LABELLED model's own numbers —
            ``screenAdvises = true``: the real entry point draws the advisory and
            SCORES it anyway, to bit-identical values. This is the leg that fixes
            the reading of the two properties: a labelling governs the advisory and
            the refusal of a DISAGREEING labelling, never a score VALUE.
    Leg (ii) needs at least two columns; at one column only (i)/(iii)/(iv) exist.

    Unrelated warnings (e.g. pandas ``is_sparse is deprecated``) are ignored on
    leg (i): the claim is about the FEATURE-NAME advisory, not about silence.
    """
    from sklearn.utils.validation import _get_feature_names
    import pandas as pd
    rng = np.random.RandomState(9317)
    recorded = list(clf_df.feature_names_in_)
    n_features = len(recorded)
    data = rng.randn(6, n_features)
    observations = 0

    # (i) the agreeing handle: labelling present AND equal to the recorded one.
    Xok = pd.DataFrame(data, columns=recorded)
    names = _get_feature_names(Xok)
    assert names is not None and list(names) == recorded, (
        "labelling grounding failed on %s: the caller's DataFrame does not "
        "present the recorded labelling in order (%r vs %r)"
        % (label, None if names is None else list(names), recorded))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        got = np.asarray(clf_df.score_samples(Xok))
    assert got.shape == (6,), (
        "labelling grounding failed on %s: the agreeing handle did not score "
        "to one value per row (%r)" % (label, got.shape))
    assert not any("feature names" in str(x.message).lower() for x in w), (
        "labelling grounding failed on %s: an AGREEING labelling still drew "
        "a feature-name advisory %r, so `screenAdvises = false` is not the quiet "
        "domain the modeled entry point promises scores on"
        % (label, [str(x.message) for x in w]))
    observations += 1

    # (ii)/(iii) disagreeing labellings: the SAME numbers, labels the model did
    # not record in that order. The real entry point RAISES rather than scoring
    # them, which is `screenRefuses = true` — the verdict the modeled entry point
    # reports by serving nothing.
    disagreeing = []
    if n_features >= 2:
        disagreeing.append(("permuted", list(reversed(recorded))))
    disagreeing.append(("disjoint", ["z%d" % i for i in range(n_features)]))
    for kind, cols in disagreeing:
        Xbad = pd.DataFrame(data, columns=cols)
        assert list(_get_feature_names(Xbad)) != recorded, (
            "labelling grounding on %s: the %s labelling %r was meant to "
            "DISAGREE with %r" % (label, kind, cols, recorded))
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                clf_df.score_samples(Xbad)
        except ValueError as e:
            assert "feature names" in str(e).lower(), (
                "screenRefuses grounding on %s: the %s labelling raised an "
                "unexpected ValueError %r" % (label, kind, str(e)))
        else:
            raise AssertionError(
                "screenRefuses grounding failed on %s: the real entry point "
                "SCORED the %s labelling %r, so a DISAGREEING labelling is not "
                "a refusal and the modeled entry point may not report it as "
                "one" % (label, kind, cols))
        observations += 1

    # (iv) the UNLABELLED handle of a LABELLED model: the same numbers with no
    # labelling at all. The real entry point draws the ADVISORY
    # (`screenAdvises = true`) and SCORES it anyway, to bit-identical values. So
    # the advisory is not a refusal, and a labelling may not condition a score
    # VALUE — the standing control on this repair, since an earlier revision
    # conditioned the public value clause on the labelling and thereby said
    # nothing about the ordinary unlabelled carriers. See the module docstring.
    Xnd = np.asarray(data)
    assert _get_feature_names(Xnd) is None, (
        "advisory leg (iv) on %s: a bare ndarray was expected to present no "
        "labelling" % (label,))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got_nd = np.asarray(clf_df.score_samples(Xnd))
    assert got_nd.shape == got.shape and np.allclose(got_nd, got,
                                                    rtol=0, atol=0), (
        "advisory leg (iv) on %s: the unlabelled handle scored DIFFERENTLY from "
        "the agreeing one (%r vs %r) — the labelling would then be part of the "
        "value, and conditioning a value clause on it would be faithful after "
        "all" % (label, got_nd, got))
    observations += 1
    return observations


def check_handle_properties(clf_df):
    """Grounding for the HANDLE references `screenAdvises` and `scorableAsGiven`
    (mapping.md §1, §5). All three handle properties are properties of the matrix
    HANDLE rather than of the numbers it holds, which is what lets them separate
    a caller-supplied matrix from one an earlier screen already returned — a
    distinction no clause over the numbers can make.

    Measured here, all from base-commit callees:
      (a) the caller's own DataFrame carries a column labelling; the object the
          screen returns does NOT — which is exactly why screening that object
          again DRAWS THE ADVISORY (`screenAdvises = true`) for a model that
          recorded a labelling. Which labellings are ADVISED about and which are
          REFUSED is grounded in `check_label_agreement`;
      (b) screening is idempotent on the NUMBERS while consuming the labelling,
          so the two handles are numerically indistinguishable;
      (c) `scorableAsGiven`: what the screen-free scoring path — which inserts
          no conversion of its own — can CONSUME as it stands. `fit`'s own
          validation (`accept_sparse=["csc"]`) yields a CSC handle for sparse
          input, which that path cannot read, whereas it reads the dense handle
          of the recorded width fine; and a dense handle NARROWER than the width
          the model was fitted on is refused as well, though its arrangement is
          the ordinary one. Returns the number of WIDTH-leg observations it was
          able to make (a one-column model has no narrower handle to offer), so
          that main() can assert the leg was exercised somewhere.
    """
    from sklearn.utils.validation import _get_feature_names
    rng = np.random.RandomState(4242)
    import pandas as pd
    n_features = clf_df.n_features_in_
    Xdf = pd.DataFrame(rng.randn(6, n_features),
                       columns=["f%d" % i for i in range(n_features)])

    # (a) screenAdvises: the caller's handle presents a labelling, a screened
    # one does not — so screening the screened one again has something to report.
    assert _get_feature_names(Xdf) is not None, (
        "screenAdvises grounding failed: the caller's DataFrame carries no "
        "column labelling")
    Xp = _prepare(clf_df, Xdf)
    assert _get_feature_names(Xp) is None and not hasattr(Xp, "columns"), (
        "screenAdvises grounding failed: the screened handle still carries a "
        "column labelling — re-screening it could not draw the advisory")

    # (b) the two handles are numerically identical: only the handle differs.
    assert np.array_equal(np.asarray(Xdf, dtype=np.float32), np.asarray(Xp)), (
        "handle grounding failed: screening changed the NUMBERS, so a handle "
        "property is not the only difference")

    # (c) scorableAsGiven: dense reads; the CSC handle fit produces does not.
    from scipy import sparse as sp
    dense = np.asarray(Xp)
    screen_free_scores(clf_df, dense)          # readable as it stands
    csc = clf_df._validate_data(sp.csc_matrix(dense), accept_sparse=["csc"],
                                dtype=np.float32, reset=False)
    assert sp.isspmatrix_csc(csc), "expected fit's validation to yield CSC"
    try:
        screen_free_scores(clf_df, csc)
    except ValueError as e:
        assert "csr" in str(e).lower(), (
            "scorableAsGiven grounding: unexpected ValueError %r" % (str(e),))
    else:
        raise AssertionError(
            "scorableAsGiven grounding failed: the screen-free path READ the "
            "CSC handle, so the layout restriction is not real")

    # (c, width leg) a dense handle narrower than the recorded width holds its
    # numbers in the arrangement the scorer reads and is still not consumable:
    # the scorer indexes a feature it does not have. So `scorableAsGiven` is
    # false there too, and the reference fences it.
    width_obs = 0
    if n_features >= 2:
        narrow = np.ascontiguousarray(dense[:, :n_features - 1])
        try:
            screen_free_scores(clf_df, narrow)
        except Exception:
            width_obs += 1
        else:
            raise AssertionError(
                "scorableAsGiven grounding failed: the screen-free path "
                "CONSUMED a prepared handle narrower than the recorded width, "
                "so the width leg of the reference is not real")
        # control: at the recorded width the same numbers ARE consumed, so the
        # leg is about the width and not about the arrangement.
        got = screen_free_scores(clf_df, dense)
        assert np.asarray(got).shape == (dense.shape[0],), (
            "scorableAsGiven width control failed: the recorded-width dense "
            "handle did not yield one score per sample (%r)"
            % (np.asarray(got).shape,))
        width_obs += 1
    return width_obs


def check_object_properties(clf_df, label):
    """Grounding for modeling a matrix as an OBJECT (mapping.md §1, §2, §6).

    Solution.lean's screen properties are properties of opaque matrix TYPES. This
    function measures why they have to be: three times over, two matrices holding
    BIT-IDENTICAL numbers disagree about what a screen decides.

      (a) LABELLING -> the advisory. The recorded labelling presented, versus the
          same numbers presented bare: a screen reports a labelling discrepancy
          about the second and not about the first.
      (b) WIDTH -> the refusal. The same numbers arranged as the recorded width,
          versus arranged as another width: a screen turns the second away
          outright and scores the first.
      (c) LAYOUT -> readability. The same numbers dense, versus in the
          compressed-column arrangement ``fit``'s own validation produces for
          sparse input: the screen-free scorer reads the first as it stands and
          cannot read the second.

    So no reference over a sequence of numbers can decide any of them — it would
    have to answer twice for one argument. The matrices are objects, and only a
    score sequence, which genuinely is a sequence of numbers, is modeled as one.

    Leg (a) also measures the VALUE side: the two matrices there score to
    bit-identical values. That is the licence for the public entry point's value
    clause being unconditional in the labelling — the labelling governs the
    report and the refusal of a DISAGREEING labelling, never the score. (Leg (iv)
    of ``check_label_agreement`` measures the same identity from the advisory
    side; here it is stated as the object's own property.)

    Returns the number of observations made.
    """
    from sklearn.utils.validation import _get_feature_names
    import pandas as pd
    from scipy import sparse as sp
    rng = np.random.RandomState(6710)
    recorded = list(clf_df.feature_names_in_)
    width = len(recorded)
    data = rng.randn(6, width)
    labelled = pd.DataFrame(data, columns=recorded)
    bare = np.asarray(data)
    observations = 0

    # (a) same numbers, different labelling -> different advisory.
    assert _get_feature_names(labelled) is not None, (
        "object grounding failed on %s: the labelled matrix presents no "
        "labelling" % (label,))
    assert _get_feature_names(bare) is None, (
        "object grounding failed on %s: the bare numbers present a labelling"
        % (label,))
    assert np.array_equal(np.asarray(labelled, dtype=np.float64), bare), (
        "object grounding failed on %s: the two matrices do not hold the same "
        "numbers, so they are not two objects over one set of numbers"
        % (label,))
    with warnings.catch_warnings(record=True) as caught_lbl:
        warnings.simplefilter("always")
        got_lbl = np.asarray(clf_df.score_samples(labelled))
    with warnings.catch_warnings(record=True) as caught_bare:
        warnings.simplefilter("always")
        got_bare = np.asarray(clf_df.score_samples(bare))
    advised_lbl = [w for w in caught_lbl
                   if "feature names" in str(w.message)]
    advised_bare = [w for w in caught_bare
                    if "feature names" in str(w.message)]
    assert not advised_lbl and advised_bare, (
        "object grounding failed on %s: the advisory did not separate the two "
        "matrices (labelled drew %r, bare drew %r), so the labelling report is "
        "not a property of the object" % (label, [str(w.message) for w in
                                                 advised_lbl],
                                          [str(w.message) for w in
                                           advised_bare]))
    observations += 1

    # (a, value side) ... and yet they score to bit-identical values.
    assert got_lbl.shape == got_bare.shape and np.allclose(
            got_lbl, got_bare, rtol=0, atol=0), (
        "object grounding failed on %s: the two matrices over one set of "
        "numbers scored differently (%r vs %r), so the score is not a function "
        "of the numbers alone and the value clause could not be unconditional "
        "in the labelling" % (label, got_lbl, got_bare))
    observations += 1

    # (b) same numbers, different width -> different verdict. The alternative
    # width always divides the count: 2 for a one-column model (6 rows -> 3x2),
    # 1 otherwise.
    alt_width = 2 if width == 1 else 1
    reshaped = bare.reshape(bare.size // alt_width, alt_width)
    assert np.array_equal(np.sort(reshaped, axis=None),
                          np.sort(bare, axis=None)), (
        "object grounding failed on %s: the rearranged matrix does not hold the "
        "same numbers" % (label,))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            clf_df.score_samples(reshaped)
        except ValueError:
            observations += 1
        else:
            raise AssertionError(
                "object grounding failed on %s: the same numbers arranged as "
                "width %d were scored, so the refusal is not a property of the "
                "object" % (label, alt_width))
        # the negative control: the recorded width IS scored.
        assert np.asarray(clf_df.score_samples(bare)).shape == (6,), (
            "object grounding failed on %s: the recorded width was not scored"
            % (label,))
    observations += 1

    # (c) same numbers, different layout -> different readability.
    prepared = np.asarray(_prepare(clf_df, bare))
    screen_free_scores(clf_df, prepared)              # readable as it stands
    csc = clf_df._validate_data(sp.csc_matrix(prepared), accept_sparse=["csc"],
                                dtype=np.float32, reset=False)
    assert sp.isspmatrix_csc(csc) and np.array_equal(
            np.asarray(csc.todense()), prepared), (
        "object grounding failed on %s: the compressed arrangement does not "
        "hold the same numbers" % (label,))
    try:
        screen_free_scores(clf_df, csc)
    except ValueError:
        observations += 1
    else:
        raise AssertionError(
            "object grounding failed on %s: the screen-free scorer READ the "
            "compressed arrangement, so readability is not a property of the "
            "object" % (label,))
    return observations


def check_screen_refusals(clf, label):
    """Grounding for `screenRefuses` (mapping.md §1, §5): the handles a screen of
    the PUBLIC entry point turns away outright, instead of handing back scores.

    The modeled entry point reports that verdict by serving nothing, so every
    region named below has to be one where the real entry point genuinely
    produces no score sequence — otherwise the model would promise a refusal the
    repository does not perform. Measured on the real entry point, from the
    handle side only (no exception TYPE is modeled — only that no scores come
    back):

      (a) a width that disagrees with the width recorded at fit time;
      (b) a handle holding no samples at all;
      (c) a magnitude the recorded working precision cannot represent. Note the
          boundary: it is REPRESENTABILITY in that precision, not finiteness —
          ``1e300`` is a perfectly finite double and is still turned away, so a
          "finite" reading of this reference would promise scores where the
          repository refuses;
      (d) a value that is not a number at all.

    And the NEGATIVE CONTROL, which is what keeps the reference from collapsing
    into "refuses everything": the ordinary handle of the right width, holding
    samples and ordinary magnitudes, is NOT refused — it scores. Without this
    leg, a rival that reports a refusal for every handle would be grounded.
    """
    n_features = clf.n_features_in_
    observations = 0

    refused = [
        ("wider-than-recorded", np.zeros((5, n_features + 1))),
        ("no-samples", np.zeros((0, n_features))),
        ("magnitude-beyond-working-precision",
         np.full((5, n_features), 1e300)),
        ("not-a-number", np.full((5, n_features), np.nan)),
    ]
    if n_features > 1:
        refused.append(
            ("narrower-than-recorded", np.zeros((5, n_features - 1))))
    for why, X in refused:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                clf.score_samples(X)
        except Exception:
            observations += 1
        else:
            raise AssertionError(
                "screenRefuses grounding failed on %s: the real entry point "
                "handed back scores for the %s handle, so the model may not "
                "report a refusal there" % (label, why))

    # negative control: the ordinary handle is NOT refused.
    Xok = np.zeros((5, n_features))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = clf.score_samples(Xok)
    except Exception as e:
        raise AssertionError(
            "screenRefuses negative control failed on %s: the ordinary handle "
            "was turned away too (%r), so the verdict would be a refusal of "
            "everything" % (label, e))
    assert np.asarray(got).shape == (5,), (
        "screenRefuses negative control failed on %s: the ordinary handle did "
        "not yield one score per sample (%r)" % (label, np.asarray(got).shape))
    observations += 1

    # For a model that recorded a labelling, the same two boundaries have to be
    # refusals even when the handle's labelling AGREES: a labelling that agrees
    # does not rescue a handle holding no samples, nor one holding a magnitude
    # beyond the working precision. These are the two regions a model with no
    # refusal reference would have promised scores for.
    names = getattr(clf, "feature_names_in_", None)
    if names is not None:
        import pandas as pd
        cols = list(names)
        agreeing_refused = [
            ("agreeing-labelling/no-samples",
             pd.DataFrame(np.zeros((0, n_features)), columns=cols)),
            ("agreeing-labelling/magnitude-beyond-working-precision",
             pd.DataFrame(np.full((5, n_features), 1e300), columns=cols)),
        ]
        for why, X in agreeing_refused:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    clf.score_samples(X)
            except Exception:
                observations += 1
            else:
                raise AssertionError(
                    "screenRefuses grounding failed on %s: the real entry point "
                    "handed back scores for the %s handle, so an agreeing "
                    "labelling would rescue it and the model may not report a "
                    "refusal there" % (label, why))
        # and the control on that side too: agreeing + ordinary is scored.
        Xdf_ok = pd.DataFrame(np.zeros((5, n_features)), columns=cols)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got_df = clf.score_samples(Xdf_ok)
        advisories = [w for w in caught
                      if "feature names" in str(w.message)]
        assert not advisories, (
            "screenAdvises negative control failed on %s: the agreeing "
            "labelling still drew %r" % (label, str(advisories[0].message)))
        assert np.asarray(got_df).shape == (5,), (
            "screenRefuses negative control failed on %s: the agreeing "
            "labelling was not scored (%r)"
            % (label, np.asarray(got_df).shape))
        observations += 1
    return observations


def check_empty_handle_fences(clf, label):
    """Grounding for the ``hasSamples`` fence on the fitting tail's obligation,
    and for the ``Scores`` CARRIER (mapping.md §5).

    An empty prepared handle is not a region where the repository returns an
    empty score sequence — both callees on that path raise:

      (a) the screen-free chunked scorer refuses a handle with no samples;
      (b) the order statistic of an empty score sequence has no value to report.

    So the fence excludes a region the model would otherwise promise a value
    for. The negative control is the one-sample handle: the smallest handle the
    fence DOES admit still yields a score and an order statistic, so the fence is
    not wider than the divergence it excludes.

    Leg (b) is also what makes the score sequence a CARRIER TYPE rather than a
    sequence of numbers a text can write down: a reference total over such a type
    would promise an order statistic for the empty sequence, and a fence on the
    METHOD'S parameter would not reach the other places that reference can be
    named at (the fifth measured lesson — see the axiom block of Solution.lean and
    ``check_percentile_point_fences``). The reading's ELEMENT type is fenced for
    the same kind of reason, one step further in — ``check_score_index_fences``.
    """
    observations = 0
    n_features = clf.n_features_in_
    empty = np.zeros((0, n_features), dtype=np.float32)
    try:
        screen_free_scores(clf, empty)
    except Exception:
        observations += 1
    else:
        raise AssertionError(
            "empty-handle fence grounding failed on %s: the screen-free scorer "
            "accepted a handle with no samples, so the fence excludes a region "
            "the repository serves" % (label,))

    try:
        np.percentile(np.zeros(0, dtype=np.float64), 5.0)
    except Exception:
        observations += 1
    else:
        raise AssertionError(
            "empty-handle fence grounding failed on %s: the order statistic of "
            "an empty score sequence returned a value" % (label,))

    # negative control: one sample is enough for both callees.
    one = np.zeros((1, n_features), dtype=np.float32)
    scores = screen_free_scores(clf, one)
    assert np.asarray(scores).shape == (1,), (
        "empty-handle fence control failed on %s: a one-sample prepared handle "
        "did not yield one score (%r)" % (label, np.asarray(scores).shape))
    float(np.percentile(np.asarray(scores, dtype=np.float64), 5.0))
    observations += 1
    return observations


def check_percentile_point_fences(scores, label):
    """Grounding for the ``Point`` CARRIER on the fitting tail's obligation
    (mapping.md §5).

    What is measured is the PARTIALITY that makes a fence necessary at all: the
    order-statistic callee is partial in the percentile point exactly as it is
    partial in the score sequence — asked for a point outside the range a
    percentage occupies it reports no value but refuses the request. Measured on
    the REAL score sequence at the fit point, on both sides of the range and just
    outside each endpoint, with the two endpoints and the interior as the control
    that the excluded region is no wider than the divergence.

    An earlier revision of the spec carried this as a precondition
    ``0 ≤ q ∧ q ≤ 100``. The measurement is unchanged and what it grounds is not:
    a precondition fences the argument the method is CALLED WITH, while a total
    reference may be NAMED at any term of its argument type anywhere inside a
    body, so rivals naming the order statistic at a refused point in a
    value-neutral position verified while resolving nothing. The fence is
    therefore the argument TYPE now (the fifth measured lesson), and the two legs
    that make the type faithful — where the reachable points come from, and that
    none of them is refused — are ``check_point_provenance``.
    """
    observations = 0
    seq = np.asarray(scores, dtype=np.float64)
    assert seq.size > 0, (
        "percentile-point fence grounding needs a nonempty score sequence on %s"
        % (label,))
    for q in (-1000.0, -1.0, -0.5, -1e-9, 100.0 + 1e-7, 101.0, 200.0, 1000.0):
        try:
            np.percentile(seq, q)
        except Exception:
            observations += 1
        else:
            raise AssertionError(
                "percentile-point fence grounding failed on %s: the order "
                "statistic at the point %r (outside the range a percentage "
                "occupies) returned a value, so the fence excludes a region the "
                "repository serves" % (label, q))

    # control: inside the range — the two endpoints included — every point
    # yields a value, so the excluded region is no wider than the repository's.
    for q in (0.0, 1.0, 5.0, 50.0, 99.5, 100.0):
        float(np.percentile(seq, q))
        observations += 1
    return observations


def check_point_provenance(rng, label):
    """The other half of the ``Point`` carrier's grounding (mapping.md §5).

    The spec's percentile point is an opaque carrier, so no text in it can name a
    point of its own. What has to be measured, then, is not a restriction but a
    repository fact: every point that DOES reach the fitting tail lies inside the
    range the order statistic is defined at. Two legs, both on real fits:

      (a) PROVENANCE. The point the tail requests is ``100.0 * contamination``
          and nothing else. Measured, not assumed: the offset a real fit records
          is bit-identical to the order statistic of that model's own screen-free
          scores AT THAT POINT — which is the fitting tail's obligation itself,
          observed on the repository. And that point is inside ``[0, 100]``.
      (b) NO OTHER POINT CAN GET THERE. The estimator refuses a contamination
          level whose point would fall outside the range, so leg (a) is not an
          observation about the values that happen to be tried here: the region
          where the order statistic reports nothing is unreachable through this
          call site. The control is the admissible interval, whose endpoints are
          accepted and whose points yield a value.
    """
    from sklearn.ensemble import IsolationForest
    observations = 0

    for c in (0.01, 0.05, 0.25, 0.4, 0.5):
        X = rng.randn(48, 3)
        clf = IsolationForest(random_state=0, contamination=c, n_estimators=20)
        clf.fit(X)
        point = 100.0 * c
        assert 0.0 <= point <= 100.0, (
            "point provenance failed on %s: the point 100*%r=%r this call site "
            "requests is outside the range a percentage occupies"
            % (label, c, point))
        seq = np.asarray(screen_free_scores(clf, _prepare(clf, X)),
                         dtype=np.float64)
        expected = float(np.percentile(seq, point))
        assert float(clf.offset_) == expected, (
            "point provenance failed on %s at contamination %r: the recorded "
            "offset %r is not the order statistic of the model's own screen-free "
            "scores at the point %r (%r)"
            % (label, c, float(clf.offset_), point, expected))
        observations += 1

    # (b) a contamination whose point would leave the range is refused outright.
    Xr = rng.randn(32, 3)
    for c in (-100.0, -1.0, -0.5, 1.5, 2.0, 100.0):
        try:
            IsolationForest(random_state=0, contamination=c,
                            n_estimators=5).fit(Xr)
        except Exception:
            observations += 1
        else:
            raise AssertionError(
                "point provenance failed on %s: contamination %r was accepted, "
                "and the point 100*%r=%r it would request lies outside the range "
                "the order statistic is defined at"
                % (label, c, c, 100.0 * c))

    # control: the admissible interval is accepted, and its points yield values.
    for c in (1e-6, 0.5):
        clf = IsolationForest(random_state=0, contamination=c,
                              n_estimators=5).fit(Xr)
        seq = np.asarray(screen_free_scores(clf, _prepare(clf, Xr)),
                         dtype=np.float64)
        float(np.percentile(seq, 100.0 * c))
        observations += 1
    return observations


def check_score_sequence_provenance(clf, label):
    """Grounding for the ``Scores`` carrier and for ``scoreValues`` as a READING
    (mapping.md §3.1).

    A score sequence exists in one way only in the spec — the scorer applied to a
    prepared matrix — and its numbers are read with ``scoreValues``. Two
    repository facts make that faithful, measured here across sample counts:

      (a) ONE SCORE PER SAMPLE. The sequence produced for a prepared matrix holds
          exactly as many real numbers as that matrix holds samples. So a produced
          sequence IS its numbers (the reading is the identity — the other half of
          it is ``check_value_equality``, where the public entry point's own
          result is that reading), and it is NON-EMPTY wherever the fitting tail's
          sample fence admits the matrix, which is what lets the fence carry the
          empty case on its own.
      (b) THE READING IS NOT AN ACTION. The same prepared matrix scored twice
          reads back bit-identically, so the numbers are a function of the matrix
          and of nothing else, and naming them twice is not a second behaviour
          (the R-VALUE rule, mapping.md §2).
    """
    observations = 0
    n_features = clf.n_features_in_
    seq_rng = np.random.RandomState(4931)
    for n in (1, 2, 5, 17, 40):
        Xp = np.asarray(seq_rng.randn(n, n_features), dtype=np.float32)
        seq = np.asarray(screen_free_scores(clf, Xp))
        assert seq.shape == (n,), (
            "score-sequence grounding failed on %s: a prepared matrix of %d "
            "samples produced %r scores, not one per sample"
            % (label, n, seq.shape))
        assert seq.size > 0 and np.all(np.isfinite(seq)), (
            "score-sequence grounding failed on %s: the sequence produced for "
            "%d samples is empty or holds a non-number (%r)" % (label, n, seq))
        again = np.asarray(screen_free_scores(clf, Xp))
        assert np.array_equal(seq, again), (
            "score-sequence grounding failed on %s: scoring the same prepared "
            "matrix twice read back different numbers" % (label,))
        observations += 1
    return observations


def check_score_index_fences(clf, label):
    """Grounding for the reading's ELEMENT carrier — ``scoreValues : Scores →
    List Score`` (mapping.md §5).

    What is measured is the PARTIALITY that makes the element type a carrier:
    reading a produced score sequence is partial in the POSITION read, exactly as
    the order statistic is partial in its point.

      (a) A POSITION THE SEQUENCE DOES NOT HAVE IS REFUSED — nothing is reported
          for it. Measured across sample counts at a position far past the end, at
          the length itself, and at the mirror position before the start.
      (b) THE REFUSAL HAPPENS AT THE READ, so cancelling the value read away does
          not avoid it: a value-neutral use of an absent position refuses just the
          same. This is the leg that matters, because a value-neutral position is
          exactly where a postcondition cannot see the read.
      (c) CONTROL — THE FENCE EXCLUDES NO MORE THAN THAT. Every position the
          sequence HAS is readable and yields a real number, the public entry
          point's own served sequence is bit-identical to this reading of the
          screen-free one and refuses an absent position in the same way, and the
          order statistic of the whole sequence is defined.

    So a sequence whose elements a text can write down would let it name a score
    where the repository derives none (an unguarded read needs only a default
    element to fall back on), while an opaque element leaves no default to fall
    back on and no such term to write — the fifth lesson's shape, one step further
    in: the ARGUMENT TYPE, here the RESULT type of the reading, is what covers
    every place the reference can be named at.
    """
    observations = 0
    n_features = clf.n_features_in_
    idx_rng = np.random.RandomState(25931 + 7)
    for n in (1, 3, 9, 21):
        Xp = np.asarray(idx_rng.randn(n, n_features), dtype=np.float32)
        seq = np.asarray(screen_free_scores(clf, Xp))
        assert seq.shape == (n,), (
            "score-position fence grounding failed on %s: a prepared matrix of %d "
            "samples produced %r scores" % (label, n, seq.shape))

        # (a) positions the sequence does not have
        for pos in (1000, n, -n - 1):
            try:
                seq[pos]
            except IndexError:
                observations += 1
            else:
                raise AssertionError(
                    "score-position fence grounding failed on %s: the score at "
                    "position %r of a sequence of %d was reported, so the fence "
                    "excludes a region the repository serves"
                    % (label, pos, n))

        # (b) the refusal is at the READ, not at the use of what was read
        try:
            seq[1000] - seq[1000]
        except IndexError:
            observations += 1
        else:
            raise AssertionError(
                "score-position fence grounding failed on %s: reading position "
                "1000 of a sequence of %d and cancelling the value away reported "
                "no refusal" % (label, n))

        # (c) control: every position the sequence HAS is readable
        vals = [float(seq[i]) for i in range(n)]
        assert len(vals) == n and all(np.isfinite(v) for v in vals), (
            "score-position control failed on %s: not every position of a "
            "sequence of %d is readable as a real number (%r)"
            % (label, n, vals))
        float(np.percentile(np.asarray(seq, dtype=np.float64), 5.0))
        observations += 1

        # control, on the PUBLIC entry point's own served sequence: it is that
        # reading, and it refuses an absent position in the same way.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pub = np.asarray(clf.score_samples(Xp))
        assert np.array_equal(pub, seq), (
            "score-position control failed on %s: the served sequence is not the "
            "reading of the screen-free one at %d samples" % (label, n))
        observations += 1
        try:
            pub[len(pub)]
        except IndexError:
            observations += 1
        else:
            raise AssertionError(
                "score-position fence grounding failed on %s: the served sequence "
                "reported a score at position %d of %d" % (label, n, n))
    return observations


def check_offset_arithmetic_fences(clf, label):
    """Grounding for the RECORDED-OFFSET carrier — ``percentileAt : Scores →
    Point → Offset``, ``defaultOffset : Offset`` — and for the R-ARITH reading
    rule (mapping.md §2, §5).

    What is measured is the PARTIALITY OF ARITHMETIC on the number a fitting tail
    records, which is the reason the recorded offset is a carrier and not a
    rational:

      (a) WHICH VALUE EACH FITTING PATH RECORDS. A fit that requests a
          contamination level records the order statistic of its own screen-free
          scores at the point that level determines; a fit that requests none
          records the constant -0.5, and that constant is not the order statistic
          any requested level determines (measured on the same training data).
          So ``defaultOffset`` names a value the repository really records, at a
          different fitting path, and it is a value the tail modeled here must
          not report.
      (b) ARITHMETIC ON A RECORDED OFFSET IS PARTIAL. Divided by zero — by a
          literal zero or by the difference of the offset with itself — a
          recorded offset yields NO number: as a plain real it refuses outright,
          and in the working precision the scorer produces it reports a
          non-finite value together with a runtime warning.
      (c) THE DIVERGENCE IS AT THE ARITHMETIC, not at the use of its result, so
          cancelling the quotient away does not avoid it: the difference of that
          quotient with itself is not a number either.
      (d) CONTROL — THE FENCE EXCLUDES NO MORE THAN THAT. The arithmetic the
          repository does perform on these numbers is untouched: negation,
          division by one and by two, the order statistic taken again, and the
          count of the scores all yield finite values and warn about nothing.
      (e) R-ARITH GROUNDING. The reference language's arithmetic on rationals is
          EXACT and the repository's on these numbers is not: three tenths added
          together is exactly three tenths as a rational and is not 0.3 as the
          repository computes it, and the mean the repository reports for a real
          score sequence is not the exact rational mean of those same numbers.
          A rational term in the reference file therefore denotes no repository
          quantity, which is what the R-ARITH reading rule says.

    So a recorded offset whose TYPE admits division promises a value in a region
    where the repository derives none — the same shape as the point and the score
    position, one step further out: the fence has to be the TYPE, because a text
    may name the arithmetic anywhere inside a body and a postcondition cannot see
    a quotient that is discarded.
    """
    from fractions import Fraction

    from sklearn.ensemble import IsolationForest

    observations = 0
    n_features = clf.n_features_in_
    ar_rng = np.random.RandomState(25931 + 11)
    Xtr = ar_rng.randn(24, n_features)
    Xp = np.asarray(ar_rng.randn(16, n_features), dtype=np.float32)
    seq = np.asarray(screen_free_scores(clf, Xp), dtype=np.float64)

    # (a) which value each fitting path records
    auto = IsolationForest(random_state=0, contamination="auto",
                           n_estimators=20).fit(Xtr)
    assert float(auto.offset_) == -0.5, (
        "recorded-offset grounding failed on %s: the fit that requests no "
        "contamination level recorded %r and not the constant -0.5"
        % (label, float(auto.offset_)))
    observations += 1
    off = None
    for cont in (0.05, 0.25, 0.4):
        req = IsolationForest(random_state=0, contamination=cont,
                              n_estimators=20).fit(Xtr)
        own = np.asarray(screen_free_scores(req, _prepare(req, Xtr)),
                         dtype=np.float64)
        want = float(np.percentile(own, 100.0 * cont))
        assert np.isfinite(req.offset_) and float(req.offset_) == want, (
            "recorded-offset grounding failed on %s: a fit requesting "
            "contamination %r recorded %r, not the order statistic %r of its "
            "own screen-free scores"
            % (label, cont, float(req.offset_), want))
        assert float(req.offset_) != float(auto.offset_), (
            "recorded-offset grounding failed on %s: a fit requesting "
            "contamination %r recorded exactly the constant the requestless "
            "path records, so the two values could not be told apart"
            % (label, cont))
        off = float(req.offset_)
        observations += 1

    # (b) arithmetic on a recorded offset is partial
    for tag, thunk in (("offset / 0", lambda: off / 0.0),
                       ("offset / (offset - offset)", lambda: off / (off - off)),
                       ("1 / (offset - offset)", lambda: 1.0 / (off - off))):
        try:
            thunk()
        except ZeroDivisionError:
            observations += 1
        else:
            raise AssertionError(
                "recorded-offset arithmetic grounding failed on %s: %s reported "
                "a number" % (label, tag))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        quotient = np.float64(off) / np.float64(0.0)
    assert not np.isfinite(quotient), (
        "recorded-offset arithmetic grounding failed on %s: dividing a recorded "
        "offset by zero in the working precision reported the finite value %r"
        % (label, float(quotient)))
    assert any(issubclass(w.category, RuntimeWarning) for w in caught), (
        "recorded-offset arithmetic grounding failed on %s: dividing a recorded "
        "offset by zero in the working precision warned about nothing" % (label,))
    observations += 1

    # (c) the divergence is at the arithmetic, not at the use of its result
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cancelled = (np.float64(off) / np.float64(0.0)) - (np.float64(off) / np.float64(0.0))
    assert not np.isfinite(cancelled), (
        "recorded-offset arithmetic grounding failed on %s: cancelling the "
        "quotient away recovered the finite value %r"
        % (label, float(cancelled)))
    observations += 1

    # (d) control: the arithmetic the repository DOES perform is untouched
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        kept = [-off, off / 1.0, off / 2.0,
                float(np.percentile(seq, 25.0)), float(len(seq))]
    assert all(np.isfinite(v) for v in kept), (
        "recorded-offset arithmetic control failed on %s: the arithmetic the "
        "repository performs on these numbers reported %r" % (label, kept))
    assert not caught, (
        "recorded-offset arithmetic control failed on %s: the arithmetic the "
        "repository performs on these numbers warned about %r"
        % (label, [w.category.__name__ for w in caught]))
    observations += 1

    # (e) R-ARITH: the repository's arithmetic on these numbers is not the
    # reference language's exact rational arithmetic
    inexact = 0
    tenth = 0.1
    if (tenth + tenth + tenth) != 0.3:
        assert Fraction(1, 10) * 3 == Fraction(3, 10)
        inexact += 1
    exact_mean = sum((Fraction(float(v)) for v in seq), Fraction(0)) / len(seq)
    if Fraction(float(np.mean(seq))) != exact_mean:
        inexact += 1
    assert inexact >= 1, (
        "R-ARITH grounding failed on %s: the repository's arithmetic on these "
        "numbers was indistinguishable from exact rational arithmetic" % (label,))
    observations += 1
    return observations


def check_sparse_container_fence(clf, label):
    """Grounding for the LAYOUT fence the PUBLIC entry point carries on the
    prepared form of its own handle (``require scorableAsGiven (preparedOf handle)
    = true``; mapping.md §1, §5).

    The screen and the scorer disagree about one family of matrices, and that is a
    repository fact rather than a modeling choice. A screen converts the working
    precision and consumes the labelling; it does NOT rearrange every matrix it
    accepts. Measured here from base-commit callees, on three legs:

      (a) THE SCREEN ACCEPTS, THE SCORER DOES NOT. A handle held in the newer
          sparse container is accepted by the public screen -- it hands back a
          prepared matrix of the same numbers, in the working precision, with its
          numbers compressed BY ROW -- and both the screen-free scorer and the
          public entry point itself then refuse that matrix and report nothing for
          it. So ``scorableAsGiven`` is false there, the public clause has no value
          to serve there, and the fence is what keeps the clause from promising
          one.
      (b) CONTROL: THE FENCE EXCLUDES NO MORE THAN THAT. The SAME numbers in the
          dense arrangement and in the older sparse containers are all accepted by
          the screen AND consumed by the scorer, one score per sample, and the
          public entry point serves exactly those numbers. Every arrangement the
          graded scoring surface uses is one of these.
      (c) THE FITTING TAIL NEVER HOLDS THE EXCLUDED MATRIX EITHER, so the same
          fence on the offset tail excludes nothing reachable in fitting: ``fit``
          itself refuses a training matrix in the newer container outright, while
          the older container of the same numbers is fitted.

    Returns the number of observations made.
    """
    from scipy import sparse as sp
    fence_rng = np.random.RandomState(7717)
    n_features = clf.n_features_in_
    nums = fence_rng.randn(6, n_features)
    observations = 0

    # (a) accepted by the screen, refused by the scorer.
    newer = []
    for name in ("csr_array", "csc_array", "coo_array"):
        ctor = getattr(sp, name, None)
        if ctor is not None:
            newer.append((name, ctor))
    for name, ctor in newer:
        handle = ctor(nums)
        prepared = _prepare(clf, handle)          # no refusal: it hands data back
        assert sp.issparse(prepared) and prepared.shape == nums.shape, (
            "sparse-container grounding failed on %s/%s: the screen did not hand "
            "back a sparse prepared matrix of the same shape (%r)"
            % (label, name, prepared))
        try:
            screen_free_scores(clf, prepared)
        except ValueError as e:
            assert "csr_matrix" in str(e), (
                "sparse-container grounding on %s/%s: unexpected ValueError %r"
                % (label, name, str(e)))
        else:
            raise AssertionError(
                "sparse-container grounding failed on %s/%s: the screen-free "
                "scorer CONSUMED the prepared form of a handle in the newer "
                "container, so the public path's layout fence is not real"
                % (label, name))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")       # a labelled model may advise
            try:
                clf.score_samples(handle)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "sparse-container grounding failed on %s/%s: the PUBLIC "
                    "entry point served scores for a handle in the newer "
                    "container, so there is a value the fence excludes"
                    % (label, name))
        observations += 1

    # (b) control: dense and the older containers are consumed, and the public
    # entry point serves exactly the numbers the scorer produces for them.
    for name, ctor in (("dense", np.ascontiguousarray),
                       ("csr_matrix", sp.csr_matrix),
                       ("csc_matrix", sp.csc_matrix),
                       ("coo_matrix", sp.coo_matrix)):
        handle = ctor(nums)
        prepared = _prepare(clf, handle)
        got = np.asarray(screen_free_scores(clf, prepared))
        assert got.shape == (nums.shape[0],), (
            "sparse-container control failed on %s/%s: the scorer did not yield "
            "one score per sample (%r)" % (label, name, got.shape))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pub = np.asarray(clf.score_samples(handle))
        assert np.array_equal(pub, got), (
            "sparse-container control failed on %s/%s: the public entry point "
            "did not serve the numbers the scorer produces" % (label, name))
        observations += 1

    # (c) the fitting side: the newer container is refused by fit itself.
    if newer:
        from sklearn.ensemble import IsolationForest
        train = fence_rng.randn(24, n_features)
        try:
            IsolationForest(random_state=0, n_estimators=4,
                            contamination=0.1).fit(newer[0][1](train))
        except ValueError:
            pass
        else:
            raise AssertionError(
                "sparse-container grounding failed on %s: fit ACCEPTED a "
                "training matrix in the newer container, so the offset tail "
                "could hold one" % (label,))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            IsolationForest(random_state=0, n_estimators=4,
                            contamination=0.1).fit(sp.csc_matrix(train))
        observations += 1
    return observations


def _presented_labelling(X):
    """The per-column labelling a matrix PRESENTS, read off the object alone
    (``sklearn/base.py::_get_feature_names`` reads exactly this): the column
    labels of a frame whose labels are all strings, and nothing otherwise."""
    cols = getattr(X, "columns", None)
    if cols is None:
        return None
    cols = list(cols)
    if cols and all(isinstance(c, str) for c in cols):
        return [str(c) for c in cols]
    return None


def _inspect_refuses(clf, X, representability=True):
    """Decide whether a screen would turn this matrix away BY INSPECTING IT — its
    presented labelling, its width, its sample count, its element kind and its
    magnitudes, against what the model recorded when it was fitted. No screen is
    performed. ``representability=False`` is the deliberately weakened variant
    used as the negative control (it reads FINITENESS where the screen reads
    representability in the recorded working precision)."""
    recorded = getattr(clf, "feature_names_in_", None)
    presented = _presented_labelling(X)
    if presented is not None and recorded is not None:
        if presented != [str(c) for c in recorded]:
            return True                      # a labelling that DISAGREES
    try:
        a = np.asarray(X, dtype=np.float64)
    except Exception:
        return True                          # not numbers at all
    if a.ndim != 2 or a.shape[1] != clf.n_features_in_:
        return True                          # a width that disagrees
    if a.shape[0] < 1:
        return True                          # no samples
    if not np.all(np.isfinite(a)):
        return True                          # not a number
    if representability and np.any(
            np.abs(a) > float(np.finfo(np.float32).max)):
        return True                          # beyond the working precision
    return False


def _inspect_advises(clf, X, read_labelling=True):
    """Decide whether a screen of this matrix would draw the labelling ADVISORY,
    again BY INSPECTION: exactly when the matrix presents no labelling while the
    model recorded one, or presents one while the model recorded none.
    ``read_labelling=False`` is the negative control (an inspector that does not
    look at the labelling at all)."""
    if not read_labelling:
        return False
    recorded = getattr(clf, "feature_names_in_", None)
    presented = _presented_labelling(X)
    return (presented is not None) != (recorded is not None)


def _screened_outcome(clf, X):
    """Perform the real screen through the public entry point and report what it
    did: whether it turned the matrix away, and whether it drew the labelling
    advisory. The advisory is collected even when the screen raises, because the
    labelling is read before the numbers are."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            clf.score_samples(X)
            refused = False
        except Exception:
            refused = True
    advised = any("feature names" in str(w.message) for w in caught)
    return refused, advised


def check_inspection_decides(clf, label):
    """Grounding for the claim Solution.lean rests the SCREEN PROPERTIES on: both
    ``screenRefuses`` and ``screenAdvises`` are DECIDED BY INSPECTION of the
    matrix, so naming either carries no screening effect and a text that BRANCHES
    on one has proved something about its data rather than done something to it.

    Why this has to be measured rather than assumed: the two references may be
    named anywhere in the spec, including inside the fitting tail, whose whole
    obligation is that it performs no screen. If deciding one of them required
    performing a screen, that liberty would be unsound — a branch on the advisory
    would BE the ambient report it is meant to avoid. (The measured counterpart of
    the same rule in the other direction: a screen's prepared OUTPUT is not
    decidable by inspection at all, it is what the screen produces, which is why
    it is confined to the caller's side of this spec and reachable only where a
    caller's handle is.)

    Measured: an inspector reading only the matrix (its presented labelling, its
    width, its sample count, its element kind, its magnitudes) against what the
    model recorded agrees with the OUTCOME of the real screen on every fixture,
    for the refusal and for the advisory alike.

    Two negative controls keep that agreement from being vacuous:

      (a) an inspector reading FINITENESS where the screen reads representability
          in the recorded working precision must DISAGREE somewhere (it does, at
          ``1e300``) — so the fixtures do discriminate what is inspected;
      (b) an inspector that does not read the labelling at all must DISAGREE on
          the advisory somewhere (it does, on the unlabelled handle of a labelled
          model) — so the advisory leg is not decided by ignoring the labelling.
    """
    n_features = clf.n_features_in_
    recorded = getattr(clf, "feature_names_in_", None)
    fixtures = [
        ("ordinary-ndarray", np.zeros((5, n_features))),
        ("wider-than-recorded", np.zeros((5, n_features + 1))),
        ("no-samples", np.zeros((0, n_features))),
        ("magnitude-beyond-working-precision",
         np.full((5, n_features), 1e300)),
        ("not-a-number", np.full((5, n_features), np.nan)),
    ]
    if n_features > 1:
        fixtures.append(
            ("narrower-than-recorded", np.zeros((5, n_features - 1))))
    import pandas as pd
    cols = ([str(c) for c in recorded] if recorded is not None
            else ["f%d" % i for i in range(n_features)])
    fixtures += [
        ("labelled-frame", pd.DataFrame(np.zeros((5, n_features)),
                                        columns=cols)),
        ("labelled-frame/no-samples",
         pd.DataFrame(np.zeros((0, n_features)), columns=cols)),
        ("labelled-frame/magnitude-beyond-working-precision",
         pd.DataFrame(np.full((5, n_features), 1e300), columns=cols)),
        ("renamed-labelling",
         pd.DataFrame(np.zeros((5, n_features)),
                      columns=["z%d" % i for i in range(n_features)])),
    ]
    if n_features > 1:
        fixtures.append(
            ("permuted-labelling",
             pd.DataFrame(np.zeros((5, n_features)),
                          columns=list(reversed(cols)))))

    observations = 0
    finiteness_disagreed = False
    labelling_blind_disagreed = False
    for why, X in fixtures:
        refused, advised = _screened_outcome(clf, X)
        i_refused = _inspect_refuses(clf, X)
        i_advised = _inspect_advises(clf, X)
        assert i_refused == refused, (
            "screenRefuses is not decided by inspection on %s at the %s matrix: "
            "inspection says %r, the real screen did %r"
            % (label, why, i_refused, refused))
        assert i_advised == advised, (
            "screenAdvises is not decided by inspection on %s at the %s matrix: "
            "inspection says %r, the real screen did %r"
            % (label, why, i_advised, advised))
        observations += 1
        if _inspect_refuses(clf, X, representability=False) != refused:
            finiteness_disagreed = True
        if _inspect_advises(clf, X, read_labelling=False) != advised:
            labelling_blind_disagreed = True

    assert finiteness_disagreed, (
        "inspection control failed on %s: an inspector reading finiteness "
        "instead of representability in the recorded working precision agreed "
        "with the screen everywhere, so these fixtures do not discriminate what "
        "is inspected" % (label,))
    assert labelling_blind_disagreed, (
        "inspection control failed on %s: an inspector that never reads the "
        "labelling agreed with the screen's advisory everywhere, so the advisory "
        "leg is satisfied by ignoring the labelling" % (label,))
    return observations


def main():
    try:
        import pandas as pd
    except Exception as e:
        print("G-AX SKIP: pandas unavailable (%r)" % (e,))
        return 0

    rng = np.random.RandomState(25931)

    # --- boundary fitted models over contamination values -----------------
    n_value_checks = 0
    n_screen_checks = 0
    n_point_obs = 0
    for contamination in (0.05, 0.1, 0.25, 0.4, "auto"):
        clf = _fit_model(rng, n=40, n_features=3, contamination=contamination)

        # ndarray and DataFrame carriers (boundary + the issue's repro shape)
        Xnd = rng.randn(40, 3)
        Xdf = pd.DataFrame(Xnd, columns=["a", "b", "c"])
        for X, label in ((Xnd, "ndarray/c=%s" % contamination),
                         (Xdf, "DataFrame/c=%s" % contamination)):
            check_value_equality(clf, X, label)
            check_screen_counts(clf, X, label)
            n_value_checks += 1
            n_screen_checks += 1

        # percentileAt vs np.percentile on the real scores at the fit point
        scores = screen_free_scores(clf, _prepare(clf, Xnd))
        for q in (5.0, 10.0, 25.0, 40.0):
            check_percentile(scores, q)
        # and the POINT carrier's partiality leg, on that same real sequence
        n_point_obs += check_percentile_point_fences(
            scores, "point/c=%s" % contamination)

    # where the reachable points come from, and that none of them is refused —
    # the other leg of the POINT carrier's grounding.
    n_prov_obs = check_point_provenance(rng, "provenance")
    assert n_prov_obs >= 5, (
        "point provenance was never exercised (%d observations)" % (n_prov_obs,))

    # --- the issue's exact reproduction (single-column DataFrame) ----------
    clf = _fit_model(rng, n=8, n_features=1, contamination=0.05)
    Xdf1 = pd.DataFrame(data=rng.randn(8, 1), columns=["a"])
    check_value_equality(clf, Xdf1, "repro-1col")
    check_screen_counts(clf, Xdf1, "repro-1col")

    # the bug exhibition needs a model fitted WITH feature names
    clf_df = _fit_model(rng, n=8, n_features=1, contamination=0.05,
                        as_dataframe=True)
    check_bug_is_real(clf_df)
    n_width_obs = check_handle_properties(clf_df)
    n_seq_obs = check_score_sequence_provenance(clf_df, "seq/repro-1col")
    n_index_obs = check_score_index_fences(clf_df, "position/repro-1col")
    n_arith_obs = check_offset_arithmetic_fences(clf_df, "arith/repro-1col")

    # The layout and width legs of `scorableAsGiven` are legs of the SAME
    # reference, and a one-column model has no narrower prepared handle to
    # offer, so leg (c) is measured on a wider labelled model as well.
    clf_df4 = _fit_model(rng, n=24, n_features=4, contamination=0.1,
                         as_dataframe=True)
    n_width_obs += check_handle_properties(clf_df4)
    n_seq_obs += check_score_sequence_provenance(clf_df4, "seq/4col")
    n_index_obs += check_score_index_fences(clf_df4, "position/4col")
    n_arith_obs += check_offset_arithmetic_fences(clf_df4, "arith/4col")
    assert n_width_obs >= 2, (
        "scorableAsGiven width leg was never exercised (%d observations)"
        % (n_width_obs,))

    # --- why a matrix is an OBJECT: three screen decisions that the numbers
    # --- alone cannot decide, plus the value equality on the first ------------
    n_obj_obs = check_object_properties(clf_df, "object/repro-1col")

    # --- the screen's VERDICT: which handles it turns away, and which it does
    # --- not (the negative control) ------------------------------------------
    n_refuse_obs = 0
    n_refuse_models = 0
    n_fence_obs = 0
    n_inspect_obs = 0
    n_layout_obs = 0
    for d, contamination in ((1, 0.05), (3, 0.25), (5, "auto")):
        clf_v = _fit_model(rng, n=32, n_features=d, contamination=contamination)
        n_refuse_obs += check_screen_refusals(
            clf_v, "verdict/d=%d/c=%s" % (d, contamination))
        n_fence_obs += check_empty_handle_fences(
            clf_v, "fence/d=%d/c=%s" % (d, contamination))
        n_inspect_obs += check_inspection_decides(
            clf_v, "inspect/d=%d/c=%s" % (d, contamination))
        n_seq_obs += check_score_sequence_provenance(
            clf_v, "seq/d=%d/c=%s" % (d, contamination))
        n_index_obs += check_score_index_fences(
            clf_v, "position/d=%d/c=%s" % (d, contamination))
        n_arith_obs += check_offset_arithmetic_fences(
            clf_v, "arith/d=%d/c=%s" % (d, contamination))
        n_layout_obs += check_sparse_container_fence(
            clf_v, "layout/d=%d/c=%s" % (d, contamination))
        n_refuse_models += 1

    # --- the labelling as AGREEMENT IN ORDER, on real labelled models --------
    n_agree_obs = 0
    n_agree_models = 0
    for d, contamination in ((1, 0.05), (2, 0.1), (3, 0.25), (4, 0.4),
                             (5, "auto")):
        clf_lbl = _fit_model(rng, n=24, n_features=d,
                             contamination=contamination, as_dataframe=True)
        n_agree_obs += check_label_agreement(
            clf_lbl, "labels/d=%d/c=%s" % (d, contamination))
        n_obj_obs += check_object_properties(
            clf_lbl, "object/d=%d/c=%s" % (d, contamination))
        # the verdict legs on a LABELLED model too: an agreeing labelling does
        # not rescue an empty or unrepresentable handle.
        n_refuse_obs += check_screen_refusals(
            clf_lbl, "verdict-labelled/d=%d/c=%s" % (d, contamination))
        n_inspect_obs += check_inspection_decides(
            clf_lbl, "inspect-labelled/d=%d/c=%s" % (d, contamination))
        n_layout_obs += check_sparse_container_fence(
            clf_lbl, "layout-labelled/d=%d/c=%s" % (d, contamination))
        n_refuse_models += 1
        n_agree_models += 1

    # --- randomized fuzz over shapes ---------------------------------------
    n_fuzz = 0
    for _ in range(60):
        n = int(rng.randint(4, 64))
        d = int(rng.randint(1, 6))
        clf = _fit_model(rng, n=n, n_features=d,
                         contamination=float(rng.uniform(0.01, 0.49)))
        Xnd = rng.randn(n, d)
        cols = ["f%d" % i for i in range(d)]
        Xdf = pd.DataFrame(Xnd, columns=cols)
        check_value_equality(clf, Xdf, "fuzz")
        check_screen_counts(clf, Xdf, "fuzz")
        n_fuzz += 1

    assert n_seq_obs >= 4, (
        "score-sequence provenance was never exercised (%d observations)"
        % (n_seq_obs,))
    assert n_layout_obs >= 8, (
        "the public path's layout fence was never exercised (%d observations)"
        % (n_layout_obs,))
    assert n_index_obs >= 12, (
        "the score-position fence was never exercised (%d observations)"
        % (n_index_obs,))
    assert n_arith_obs >= 30, (
        "the recorded-offset arithmetic fence was never exercised (%d "
        "observations)" % (n_arith_obs,))

    print("G-AX OK: score_samples == screen-free scoring via the unchanged "
          "callee -_compute_chunked_score_samples (A-reference) over "
          "%d value-equality + %d screen-count boundary checks + %d fuzz "
          "models; public screens once / chunked scorer zero; feature-name "
          "advisory drawn only on the public path; screenAdvises/screenRefuses "
          "grounded over %d labelling observations on %d labelled models (an "
          "agreeing labelling scores quietly; an unlabelled handle draws the "
          "advisory and still scores to bit-identical values, so no labelling "
          "conditions a score value; permuted and disjoint labellings are "
          "turned away) plus %d verdict observations on %d models (disagreeing "
          "width, no samples, a magnitude beyond the working precision and a "
          "non-number are turned away; the ordinary handle is NOT) and %d "
          "empty-handle fence observations and %d percentile-point observations "
          "(the order statistic refuses a point outside the range a "
          "percentage occupies, on both sides and just past each endpoint, while "
          "the endpoints themselves and the interior all yield a value) — that "
          "partiality is fenced by the argument TYPE rather than by a "
          "precondition, and the two legs that make the type faithful are %d "
          "point-provenance observations (the point a fitting tail requests is "
          "100 * the requested contamination: the offset a real fit records is "
          "bit-identical to the order statistic of that model's own screen-free "
          "scores at that point, and a contamination whose point would leave the "
          "range is refused outright while the admissible interval is accepted) "
          "and %d score-sequence observations (a prepared matrix of n samples "
          "produces exactly n real scores and the same matrix read twice reads "
          "back bit-identically, so a produced sequence is its numbers and is "
          "non-empty wherever the sample fence admits the matrix) and %d "
          "score-position observations (reading a produced sequence at a position "
          "it does not have is refused — far past the end, at the length, at the "
          "mirror position before the start, and refused just the same where the "
          "value read is cancelled away — while every position a sequence HAS is "
          "readable, the served sequence is bit-identical to that reading, and the "
          "order statistic of the whole sequence is defined, so the reading's "
          "element type is a carrier for the same measured reason the point is) "
          "and %d recorded-offset observations (a fit requesting a contamination "
          "level records the order statistic of its own screen-free scores at the "
          "point that level determines, a fit requesting none records the "
          "constant -0.5 and never that order statistic, dividing a recorded "
          "offset by zero or by its own difference derives NO number — it refuses "
          "outright as a plain real and reports a non-finite value with a runtime "
          "warning in the working precision, and cancelling that quotient away "
          "recovers no number either — while negation, division by one and by "
          "two, the order statistic taken again and the count of the scores are "
          "all finite and warn about nothing, and the repository's arithmetic on "
          "these numbers is not the reference language's exact rational "
          "arithmetic, which is what the R-ARITH reading rule records); "
          "scorableAsGiven is CONSUMABILITY and not arrangement alone, over %d "
          "width observations (a dense handle narrower than the recorded width is "
          "refused by the screen-free scorer, the recorded-width one is "
          "consumed) and %d container observations (a handle in the newer sparse "
          "container is ACCEPTED by the public screen and the scorer then refuses "
          "the prepared matrix it hands back, as does the public entry point "
          "itself, while the dense matrix and the older sparse containers of the "
          "same numbers are consumed and served — and fit refuses the newer "
          "container outright, so no fitting tail holds one); both screen "
          "properties are DECIDED "
          "BY INSPECTION of the matrix — width, sample count, element kind, "
          "magnitudes and presented labelling against what the model recorded — "
          "agreeing with the real screen's outcome over %d observations, with a "
          "finiteness inspector and a labelling-blind inspector both measured to "
          "disagree; a matrix is an OBJECT and not its "
          "numbers, grounded over %d observations (matrices holding "
          "bit-identical numbers disagree about the advisory when their "
          "labelling differs, about the refusal when their width differs and "
          "about readability when their arrangement differs — while the first "
          "pair still scores to bit-identical values); percentileAt == "
          "np.percentile."
          % (n_value_checks, n_screen_checks, n_fuzz, n_agree_obs,
             n_agree_models, n_refuse_obs, n_refuse_models, n_fence_obs,
             n_point_obs, n_prov_obs, n_seq_obs, n_index_obs, n_arith_obs,
             n_width_obs, n_layout_obs, n_inspect_obs, n_obj_obs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
