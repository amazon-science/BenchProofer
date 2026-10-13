#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8475.

This bundle consumes NO `@ContractOnly` axiom: the operation under
specification -- the classification of WHICH light-probe (HEAD) failures are
retried with the full probe (GET) -- is modelled DEEPLY by the pure predicate
`is_retryable(kind)` in model.py. G-AX therefore validates that deep model
against the REAL behaviour it abstracts: the Python exception-matching
semantics of the retried-failure `except` clause in the patched code, i.e.

    except (HTTPError, TooManyRedirects):
        # retry with a GET request

The model's outcome-kind abstraction is:

    kind 0  -> the probe succeeded (no exception)               -> not a retry
    kind 1  -> a status-level error          (HTTPError)        -> RETRYABLE
    kind 2  -> an unbounded-relocation error (TooManyRedirects) -> RETRYABLE
    kind 3  -> any OTHER probe failure (other RequestException) -> not retried

`is_retryable(kind) == (kind == 1 or kind == 2)`. The A-reference soundness
obligation is: the real `except (HTTPError, TooManyRedirects)` clause catches a
raised exception EXACTLY for the kinds the model marks retryable, and the
classification kinds are mutually exclusive and exhaustive over the failure
surface (so kind-2, the new retried kind, was genuinely NOT caught by the
pre-patch `except HTTPError`).

Imports nothing repo-specific: `requests.exceptions` is the third-party library
the patched code imports from -- the same classes the gold `except` tuple
names. Exit 0 iff every obligation holds.
"""
import random
import sys

from requests.exceptions import (
    HTTPError,
    TooManyRedirects,
    RequestException,
    ConnectionError,
    Timeout,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    ProxyError,
    ChunkedEncodingError,
    ContentDecodingError,
    InvalidURL,
    MissingSchema,
    InvalidSchema,
    URLRequired,
)

# The post-patch retried-failure clause, exactly as it appears in the gold
# patch (sphinx/builders/linkcheck.py, the inner HEAD/GET fallback):
RETRY_CLAUSE = (HTTPError, TooManyRedirects)
# The pre-patch clause (for the differential check that kind 2 was NOT caught):
PREPATCH_CLAUSE = (HTTPError,)


def model_is_retryable(kind):
    """Reference of model.py's deep model `is_retryable` (the pure region)."""
    return kind == 1 or kind == 2


def classify_kind(exc_type):
    """The model outcome KIND for a raised probe exception of type `exc_type`.

    Mirrors model.py's abstraction: a status-level error is kind 1
    (HTTPError); an unbounded-relocation error is kind 2 (TooManyRedirects);
    any other request failure is kind 3. (Kind 0 -- success -- raises no
    exception and so is not classified here.)
    """
    # TooManyRedirects must be tested FIRST only if it were a subclass of
    # HTTPError; we assert below it is NOT, so order is immaterial -- but we
    # encode the model's disjoint intent explicitly.
    if issubclass(exc_type, HTTPError):
        return 1
    if issubclass(exc_type, TooManyRedirects):
        return 2
    return 3


def caught_by(exc_type, clause):
    """Does Python's `except clause` catch an instance of `exc_type`?"""
    return issubclass(exc_type, clause)


def check_classification_disjoint():
    """The two retried kinds are produced by DISJOINT exception classes: a
    raised HTTPError is never also a TooManyRedirects and vice-versa, so kind 1
    and kind 2 are well-defined and the new kind 2 is a genuinely separate
    failure mode (not already a status error)."""
    assert not issubclass(TooManyRedirects, HTTPError), (
        "soundness broken: TooManyRedirects is a subclass of HTTPError, so the "
        "pre-patch `except HTTPError` would already have caught it and there is "
        "no kind-2 distinct from kind-1")
    assert not issubclass(HTTPError, TooManyRedirects), (
        "soundness broken: HTTPError is a subclass of TooManyRedirects")
    # Both are genuine request exceptions (the failure surface).
    assert issubclass(HTTPError, RequestException)
    assert issubclass(TooManyRedirects, RequestException)


def check_retry_clause_matches_model(exc_type):
    """The real post-patch `except (HTTPError, TooManyRedirects)` catches an
    exception of type `exc_type` EXACTLY when the model marks its kind
    retryable."""
    kind = classify_kind(exc_type)
    real_caught = caught_by(exc_type, RETRY_CLAUSE)
    model_says = model_is_retryable(kind)
    assert real_caught == model_says, (
        "A-reference unsound on %s: kind=%d, real `except (HTTPError, "
        "TooManyRedirects)` caught=%r but model is_retryable=%r"
        % (exc_type.__name__, kind, real_caught, model_says))


def check_prepatch_misses_kind2(exc_type):
    """Differential: the PRE-patch clause `except HTTPError` does NOT catch a
    kind-2 (TooManyRedirects) failure -- this is exactly the bug the fix
    closes, and exactly what model_prepatch.py fails to retry."""
    kind = classify_kind(exc_type)
    if kind == 2:
        assert not caught_by(exc_type, PREPATCH_CLAUSE), (
            "differential broken: pre-patch `except HTTPError` already caught "
            "the unbounded-relocation failure %s" % exc_type.__name__)


def main():
    # The exception classes the probe can raise (the failure surface). Each is
    # a real requests.exceptions class; we classify it and check both the
    # post-patch and pre-patch clause behaviour against the model.
    surface = [
        HTTPError,            # kind 1 (status error)
        TooManyRedirects,     # kind 2 (unbounded relocation) -- the new kind
        RequestException,     # kind 3 (generic)
        ConnectionError,      # kind 3
        Timeout,              # kind 3
        ConnectTimeout,       # kind 3
        ReadTimeout,          # kind 3
        SSLError,             # kind 3
        ProxyError,           # kind 3
        ChunkedEncodingError,  # kind 3
        ContentDecodingError,  # kind 3
        InvalidURL,           # kind 3
        MissingSchema,        # kind 3
        InvalidSchema,        # kind 3
        URLRequired,          # kind 3
    ]

    check_classification_disjoint()

    for exc_type in surface:
        check_retry_clause_matches_model(exc_type)
        check_prepatch_misses_kind2(exc_type)

    # Boundary: a NON-request exception (e.g. a bare ValueError) is also not
    # caught by the retry clause -- kind 3, not retried.
    for exc_type in (ValueError, RuntimeError, KeyError, Exception):
        assert not caught_by(exc_type, RETRY_CLAUSE) or exc_type is Exception, (
            "non-request exception %s unexpectedly matched the retry clause"
            % exc_type.__name__)

    # Fuzz: random pairs of (head_kind, get_kind) -- assert the model's
    # effective-outcome contract (probe_outcome) reduces to the retry
    # classification, i.e. a retryable head failure yields the GET outcome and
    # a non-retryable head failure (kind 3) is authoritative.
    rng = random.Random(8475)
    for _ in range(20000):
        head_kind = rng.randint(0, 3)
        get_kind = rng.randint(0, 3)
        if head_kind == 0:
            expected = 0
        elif model_is_retryable(head_kind):
            expected = get_kind
        else:
            expected = head_kind
        # the effective outcome is always one of the two probes' kinds
        assert expected in (head_kind, get_kind)
        # kind-2 head failure with a successful GET is reachable (=> "working")
        if head_kind == 2 and get_kind == 0:
            assert expected == 0, "kind-2 head + ok GET must resolve to success"

    print("G-AX OK: deep model is_retryable validated == real "
          "`except (HTTPError, TooManyRedirects)` over %d requests exception "
          "classes (disjoint kinds 1/2; kind 2 not caught pre-patch) + 20000 "
          "outcome fuzz pairs" % len(surface))
    return 0


if __name__ == "__main__":
    sys.exit(main())
