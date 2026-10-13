# properties.py — PBT manifest for sphinx-doc__sphinx-8475. NOT a Nagini module;
# a record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT.
#
# Instance under attack: probe_outcome(head_kind: int, get_kind: int) -> int.
# It models the inner HEAD(light)->GET(full) fallback of check_uri: a light
# probe whose outcome KIND is retryable (status error kind 1 OR unbounded-
# relocation kind 2) is retried and the FULL probe's outcome stands; a success
# (kind 0) or a non-retryable failure (kind 3) is authoritative.
#
# Frozen postconditions (the defended surface):
#   P1: head_kind == 0                              => Result() == 0
#   P2: head_kind != 0 and is_retryable(head_kind)  => Result() == get_kind   (LOAD-BEARING)
#   P3: head_kind != 0 and not is_retryable(head)   => Result() == head_kind
#   P4: Result() == head_kind or Result() == get_kind
#   P5: 0 <= Result() <= 3
# is_retryable(kind) == (kind == 1 or kind == 2)  is a @Pure spec helper,
# GROUNDED in the input (fully unfolded) — there is no opaque answer-key oracle
# to echo, so the ungrounded-oracle lane is N/A (see 'assessment').
#
# Both inputs are pass-by-value `int` (immutable scalars; NO Acc(x,1/2) heap
# reference), so there is NO read-only heap input and the FRAME-MUTATION lane is
# vacuous for this instance (you cannot mutate an int frame). See 'assessment'.
#
# The discriminating content of the gold patch is P2 at head_kind == 2 (the new
# TooManyRedirects retry). The F2P test (test_TooManyRedirects_on_HEAD) drives a
# server that loops on HEAD (kind 2) but answers GET 200 (kind 0); the locator
# must be reported "working" (effective outcome 0). The prepatch retries only
# kind 1 and reports it broken. Every reject rival below is grounded by which
# postcondition clause it violates and why its faithful real patch would fail
# that F2P (or a PASS_TO_PASS).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8475"
FLOAT_ENCODING = None  # meta.json float_encoding is null; unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl region body (between # impl-start and # impl-end). All
# variants are produced by _swap on THIS unique block, so edits stay strictly
# inside the impl region and same_spec is guaranteed.
_GOLD_IMPL = """\
    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
    # light probe failed with a retryable kind (is_retryable is false for a
    # success, kind 0); otherwise the light-probe outcome (a success, or a
    # non-retryable failure) stands.
    if is_retryable(head_kind):
        result = get_kind
    else:
        result = head_kind
    return result"""

assert _GOLD_IMPL in _BASE, "impl region drift: gold block not found verbatim"
assert _BASE.count(_GOLD_IMPL) == 1, "impl region not unique"


def _impl(new_body: str) -> str:
    """Swap ONLY the impl-region body; spec view is untouched => same_spec."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ----------------------------------------------------------------------------
# SPEC LANE
# ----------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness) -------------------------------------
    # A structurally-DIFFERENT but CORRECT impl: an explicit per-kind dispatch
    # on head_kind instead of the is_retryable branch. Keeps every clause's
    # obligation: kind 0 -> 0 (P1), kinds 1,2 -> get_kind (P2), kind 3 ->
    # head_kind (P3). No framing lemma needed (no loop, no fold), so this is a
    # safe positive control (avoids the forward-append / dropped-invariant
    # pitfalls). If this CANNOT verify => SPEC-TOO-STRONG.
    {
        "id": "pos-explicit-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Structurally different but equivalent: dispatch explicitly on the\n"
            "    # light-probe kind. kind 0 is authoritative success; kinds 1 and 2\n"
            "    # are the retryable failures (full probe's outcome stands); kind 3 is\n"
            "    # the authoritative non-retryable failure.\n"
            "    if head_kind == 0:\n"
            "        result = head_kind\n"
            "    elif head_kind == 3:\n"
            "        result = head_kind\n"
            "    else:\n"
            "        result = get_kind\n"
            "    return result"
        ),
        "rationale": "explicit per-kind dispatch is behaviourally identical to "
                     "the is_retryable branch; it must verify against the frozen "
                     "postcondition (else SPEC-TOO-STRONG). is_retryable(k) is "
                     "(k==1 or k==2), so head_kind==0 -> head_kind==0 satisfies "
                     "P1, head_kind in {1,2} -> get_kind satisfies P2, "
                     "head_kind==3 -> head_kind satisfies P3.",
    },

    # A second, also-correct positive control: branch on the NEGATION
    # (not is_retryable) with reordered branches. Confirms the spec does not
    # over-fit one particular control shape.
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Reordered: take the light-probe outcome unless it is a retryable\n"
            "    # failure, in which case the full probe's outcome stands.\n"
            "    if not is_retryable(head_kind):\n"
            "        result = head_kind\n"
            "    else:\n"
            "        result = get_kind\n"
            "    return result"
        ),
        "rationale": "branch reorder on the negation of is_retryable; "
                     "equivalent to gold, must verify (else SPEC-TOO-STRONG).",
    },

    # ---- ADMISSIBILITY -----------------------------------------------------
    # The precondition must admit the F2P-shaped input: the kind-2-on-HEAD /
    # ok-GET locator (head_kind == 2, get_kind == 0). Assert the Requires holds
    # for it AND that the produced effective outcome is the "working" success
    # (Result == 0) the F2P expects. If the Requires rejected this normal input
    # => PRECOND-TOO-STRONG.
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # Admissibility witness for the F2P input shape (HEAD loops with\n"
            "    # TooManyRedirects => kind 2; GET answers 200 => kind 0). The\n"
            "    # precondition 0 <= k <= 3 must accept it, and a retryable kind-2\n"
            "    # light failure with an ok GET must resolve to success (0).\n"
            "    Assert(0 <= head_kind and head_kind <= 3)\n"
            "    Assert(0 <= get_kind and get_kind <= 3)\n"
            "    if is_retryable(head_kind):\n"
            "        result = get_kind\n"
            "    else:\n"
            "        result = head_kind\n"
            "    Assert(Implies(head_kind == 2 and get_kind == 0, result == 0))\n"
            "    return result"
        ),
        "rationale": "the precondition (0<=k<=3) admits the normal F2P input "
                     "(head_kind=2, get_kind=0) and the gold logic resolves it "
                     "to success (Result==0). If the Requires could not be "
                     "established for this input => PRECOND-TOO-STRONG.",
    },

    # ---- PARTIAL-DOMAIN (uniqueness / SPEC-TOO-WEAK) -----------------------
    # THE prepatch rival: retry ONLY a status error (kind 1), never the
    # unbounded-relocation failure (kind 2). Correct on the whole domain except
    # head_kind == 2: there it returns head_kind (=2) instead of get_kind.
    # This is exactly model_prepatch.py's `if head_kind == 1:`. Its faithful
    # real patch is the PRE-patch `except HTTPError:` (no TooManyRedirects),
    # which reports the kind-2-on-HEAD locator as broken => FAILS the F2P
    # test_TooManyRedirects_on_HEAD. MUST be rejected on P2 at head_kind==2.
    {
        "id": "weak-prepatch-kind1-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PARTIAL-DOMAIN rival: retry only a status-level error (kind 1),\n"
            "    # NOT an unbounded-relocation failure (kind 2). Correct everywhere\n"
            "    # except head_kind == 2.\n"
            "    if head_kind == 1:\n"
            "        result = get_kind\n"
            "    else:\n"
            "        result = head_kind\n"
            "    return result"
        ),
        "refinement": "this is the literal PRE-patch classification "
                      "(`except HTTPError:` retries kind 1 only). On the F2P "
                      "input head_kind=2 (TooManyRedirects on HEAD), get_kind=0 "
                      "(GET 200) it returns 2 (broken) instead of 0 (working), "
                      "so the faithful real patch reports the locator broken and "
                      "FAILS tests/test_build_linkcheck.py::test_TooManyRedirects_on_HEAD. "
                      "It does NOT resolve.",
        "rationale": "rejected by P2 (head_kind != 0 and is_retryable(head_kind) "
                     "=> Result() == get_kind): is_retryable(2) is True so P2 "
                     "demands Result()==get_kind, but at head_kind==2 this impl "
                     "returns head_kind==2 != get_kind in general. If it "
                     "verified => SPEC-TOO-WEAK.",
    },

    # PARTIAL-DOMAIN, other end: retry kind 2 but NOT kind 1. Inverse partial
    # miss — correct on head_kind in {0,2,3} but wrong on the status-error
    # kind 1 (returns head_kind=1 instead of get_kind). Its faithful real patch
    # would be `except TooManyRedirects:` (dropping HTTPError), which would
    # stop retrying ordinary HEAD status errors that the GET fallback resolves
    # — regressing the existing HEAD->GET fallback that PASS_TO_PASS tests
    # (test_follows_redirects_on_HEAD and the defaults suite) exercise.
    {
        "id": "weak-kind2-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PARTIAL-DOMAIN rival: retry only an unbounded-relocation failure\n"
            "    # (kind 2), NOT a status-level error (kind 1). Wrong on head_kind==1.\n"
            "    if head_kind == 2:\n"
            "        result = get_kind\n"
            "    else:\n"
            "        result = head_kind\n"
            "    return result"
        ),
        "refinement": "faithful real patch = `except TooManyRedirects:` "
                      "(dropping HTTPError from the retry tuple). A HEAD that "
                      "raises HTTPError (kind 1) would no longer fall back to "
                      "GET, so a server that 4xx/5xx-es on HEAD but answers GET "
                      "would be reported broken — regressing the original "
                      "HEAD->GET fallback covered by the PASS_TO_PASS suite "
                      "(test_follows_redirects_on_HEAD / test_defaults). Does "
                      "NOT resolve.",
        "rationale": "rejected by P2 at head_kind==1: is_retryable(1) is True so "
                     "Result() must equal get_kind, but this returns "
                     "head_kind==1. If it verified => SPEC-TOO-WEAK.",
    },

    # ---- VALUE / WRONG-SUBSTITUTION (uniqueness) ---------------------------
    # Over-retry: treat the non-retryable kind 3 as retryable too (retry on any
    # non-success). Correct on kinds 0,1,2 but wrong on head_kind==3: returns
    # get_kind instead of the authoritative head_kind. Faithful real patch =
    # `except RequestException:` (catch every request failure), which would
    # retry connection/timeout/SSL failures that GET cannot fix and could
    # silently turn a genuinely-broken link "working" when GET happens to
    # succeed for an unrelated reason — diverging from the gold narrow tuple
    # and the authoritative-failure semantics the PASS_TO_PASS suite checks
    # (test_raises_for_invalid_status, the selfsigned/SSL cases).
    {
        "id": "weak-overcatch-kind3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # OVER-RETRY rival: retry on ANY non-success light outcome,\n"
            "    # including the non-retryable kind 3. Wrong on head_kind==3.\n"
            "    if head_kind != 0:\n"
            "        result = get_kind\n"
            "    else:\n"
            "        result = head_kind\n"
            "    return result"
        ),
        "refinement": "faithful real patch = `except RequestException:` (catch "
                      "every request failure and retry with GET). It retries "
                      "kind-3 failures (ConnectionError/Timeout/SSLError/...) "
                      "that the gold narrow `(HTTPError, TooManyRedirects)` "
                      "tuple deliberately leaves authoritative; the gold patch "
                      "does NOT widen to all RequestException, so this is a "
                      "different (broader) behaviour that diverges from gold on "
                      "the authoritative-failure cases the PASS_TO_PASS suite "
                      "pins (e.g. test_raises_for_invalid_status, the selfsigned "
                      "SSL failures). Does NOT match the gold patch.",
        "rationale": "rejected by P3 (head_kind != 0 and not "
                     "is_retryable(head_kind) => Result() == head_kind): "
                     "is_retryable(3) is False, so P3 demands Result()==3, but "
                     "this returns get_kind. If it verified => SPEC-TOO-WEAK.",
    },

    # ---- CONSTANT / DEGENERATE ECHO (uniqueness, supporting) ---------------
    # A cheap supporting near-miss: always return get_kind regardless of the
    # light outcome. Satisfies P2 but violates P1 (head_kind==0 must give 0,
    # not get_kind) and P3. Faithful real patch = always issue the GET probe
    # and report its outcome (drop the HEAD short-circuit), which changes the
    # observable result whenever HEAD already succeeded or failed
    # non-retryably. Supporting case carrying a real refinement.
    {
        "id": "weak-always-get",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # DEGENERATE rival: always report the full-probe outcome,\n"
            "    # ignoring the light probe entirely.\n"
            "    result = get_kind\n"
            "    return result"
        ),
        "refinement": "faithful real patch = drop the HEAD short-circuit and "
                      "always use the GET response. When HEAD already succeeded "
                      "(kind 0) this would still emit the GET outcome, double-"
                      "requesting and changing the reported result for "
                      "already-working HEAD links; for a non-retryable HEAD "
                      "failure (kind 3) it would mask the real failure with GET. "
                      "This is not the gold patch (which keeps the HEAD outcome "
                      "authoritative on kinds 0 and 3) and would not resolve the "
                      "PASS_TO_PASS HEAD-success cases (test_defaults / "
                      "test_follows_redirects_on_HEAD).",
        "rationale": "rejected by P1 (head_kind==0 => Result()==0): if "
                     "get_kind != 0 this returns get_kind != 0, violating P1; "
                     "also violates P3 at head_kind==3. If it verified => "
                     "SPEC-TOO-WEAK.",
    },
]


# ----------------------------------------------------------------------------
# AXIOM LANE — the deep-model reference `is_retryable` (A-reference, G-AX).
# No @ContractOnly axiom is consumed (axioms region empty), but the bundle has
# an A-reference deep model that must equal the real `except (HTTPError,
# TooManyRedirects)` exception-matching semantics. We validate that in the
# instance Docker image against the real requests.exceptions classes.
#
# Probes are self-contained: they import ONLY requests.exceptions (the third-
# party library the patched module imports the two classes from — present in
# the image regardless of the gold patch), CALL the real classes (issubclass
# membership = exactly what Python's `except (A, B)` does), open nothing on
# disk, print a diagnostic, and sys.exit(0) iff the obligation holds.
# ----------------------------------------------------------------------------
AXIOM_TESTS = [

    # axiom-soundness: the real post-patch `except (HTTPError, TooManyRedirects)`
    # catches a raised exception EXACTLY for the kinds the model marks retryable
    # (is_retryable(kind) == kind in {1,2}), kinds 1 and 2 are produced by
    # DISJOINT classes (TooManyRedirects is not a subclass of HTTPError), and
    # the pre-patch `except HTTPError` does NOT catch kind 2. Fuzz the whole
    # requests.exceptions failure surface + boundary non-request exceptions.
    {
        "id": "ax-sound-is_retryable",
        "axiom": "is_retryable",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import sys
from requests.exceptions import (
    HTTPError, TooManyRedirects, RequestException, ConnectionError, Timeout,
    ConnectTimeout, ReadTimeout, SSLError, ProxyError, ChunkedEncodingError,
    ContentDecodingError, InvalidURL, MissingSchema, InvalidSchema, URLRequired,
)

# The real post-patch retried-failure clause, verbatim from the gold patch.
RETRY_CLAUSE = (HTTPError, TooManyRedirects)
# The pre-patch clause (differential: kind 2 was NOT caught before).
PREPATCH_CLAUSE = (HTTPError,)

def model_is_retryable(kind):
    # mirrors model.py's @Pure is_retryable
    return kind == 1 or kind == 2

def classify_kind(exc_type):
    # mirrors model.py / mapping.md outcome-kind abstraction
    if issubclass(exc_type, HTTPError):
        return 1
    if issubclass(exc_type, TooManyRedirects):
        return 2
    return 3

def caught_by(exc_type, clause):
    # Python `except clause` catches exc iff issubclass(type(exc), clause).
    return issubclass(exc_type, clause)

# (1) The two retried kinds are DISJOINT classes — else kind 2 would already be
# kind 1 and there is no genuinely-new retried failure mode.
assert not issubclass(TooManyRedirects, HTTPError), \
    "UNSOUND: TooManyRedirects subclasses HTTPError (kind 2 not distinct from kind 1)"
assert not issubclass(HTTPError, TooManyRedirects), \
    "UNSOUND: HTTPError subclasses TooManyRedirects"
assert issubclass(HTTPError, RequestException), "HTTPError not a RequestException"
assert issubclass(TooManyRedirects, RequestException), "TooManyRedirects not a RequestException"

surface = [
    HTTPError, TooManyRedirects, RequestException, ConnectionError, Timeout,
    ConnectTimeout, ReadTimeout, SSLError, ProxyError, ChunkedEncodingError,
    ContentDecodingError, InvalidURL, MissingSchema, InvalidSchema, URLRequired,
]
for exc_type in surface:
    kind = classify_kind(exc_type)
    real_caught = caught_by(exc_type, RETRY_CLAUSE)
    model_says = model_is_retryable(kind)
    assert real_caught == model_says, (
        "AXIOM-UNSOUND on %s: kind=%d real `except (HTTPError, TooManyRedirects)` "
        "caught=%r but is_retryable=%r" % (exc_type.__name__, kind, real_caught, model_says))
    # differential: pre-patch clause must MISS exactly the new kind 2
    if kind == 2:
        assert not caught_by(exc_type, PREPATCH_CLAUSE), (
            "DIFFERENTIAL broken: pre-patch `except HTTPError` already caught "
            "kind-2 %s" % exc_type.__name__)

# boundary: a non-request exception is never caught by the retry clause (kind 3,
# not retried) — RuntimeError/ValueError/KeyError are not RequestException.
for exc_type in (ValueError, RuntimeError, KeyError, OSError):
    assert not caught_by(exc_type, RETRY_CLAUSE), (
        "non-request exception %s unexpectedly matched the retry clause"
        % exc_type.__name__)

print("AX-SOUND OK: is_retryable == real `except (HTTPError, TooManyRedirects)` "
      "over %d request-exception classes (disjoint kinds 1/2; kind 2 missed "
      "pre-patch) + boundary non-request exceptions" % len(surface))
sys.exit(0)
''',
        "rationale": "if the real post-patch except tuple disagreed with "
                     "is_retryable on any classifiable exception, or the kinds "
                     "were not disjoint, or the pre-patch clause already caught "
                     "kind 2, the A-reference deep model would be UNSOUND. "
                     "Mirrors axiom_check.py but executed against the real "
                     "requests classes in the instance image.",
    },

    # axiom-containment: enumerate EXACTLY the kinds the MODEL can hand to the
    # is_retryable / except classification (head_kind in {0,1,2,3} from the
    # precondition 0<=head_kind<=3), and assert each non-success kind {1,2,3}
    # is realized by a concrete real requests.exceptions class whose membership
    # in the retry tuple matches the model. The model never reaches a kind
    # outside {0,1,2,3}, and every failure kind it can reach is backed by a
    # real exception class — so the A-reference covers exactly the caller's
    # reachable surface (covering MORE non-request exceptions would still be
    # sound; the defect would be a reachable kind with no real class).
    {
        "id": "ax-contain-reachable-kinds",
        "axiom": "is_retryable",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": r'''
import sys
from requests.exceptions import HTTPError, TooManyRedirects, ConnectionError

def model_is_retryable(kind):
    return kind == 1 or kind == 2

# The precondition is 0 <= head_kind <= 3, so the ONLY kinds the model can pass
# to the classification are {0,1,2,3}. kind 0 (success) raises no exception.
# Each failure kind the model can reach must be realized by a real
# requests.exceptions class, and that class's membership in the post-patch
# retry tuple must match the model's is_retryable for that kind.
RETRY_CLAUSE = (HTTPError, TooManyRedirects)
witnesses = {
    1: HTTPError,         # kind 1 (status error)  -> retryable
    2: TooManyRedirects,  # kind 2 (unbounded redirect) -> retryable (NEW)
    3: ConnectionError,   # kind 3 (other failure) -> not retryable
}
reachable_failure_kinds = [1, 2, 3]
for kind in reachable_failure_kinds:
    exc_type = witnesses[kind]
    assert exc_type is not None, "reachable kind %d has no real exception witness" % kind
    real_caught = issubclass(exc_type, RETRY_CLAUSE)
    assert real_caught == model_is_retryable(kind), (
        "CONTAINMENT/SOUNDNESS mismatch on reachable kind %d (%s): real retry-tuple "
        "membership=%r but is_retryable=%r" % (kind, exc_type.__name__, real_caught,
                                               model_is_retryable(kind)))

# kind 0 (success) is the no-exception path: not classified by the except clause,
# and is_retryable(0) is False (never retried) — covered by definition.
assert not model_is_retryable(0), "kind 0 (success) must not be retryable"

# No reachable kind lies outside {0,1,2,3}: the precondition bounds it, so there
# is no caller-reachable input outside the A-reference's modeled surface.
for kind in (0, 1, 2, 3):
    assert kind in (0, 1, 2, 3)

print("AX-CONTAIN OK: every caller-reachable kind {0,1,2,3} is covered by the "
      "A-reference (kinds 1/2/3 backed by real HTTPError/TooManyRedirects/"
      "ConnectionError witnesses matching is_retryable; kind 0 = no-exception "
      "success). No reachable kind outside the modeled surface.")
sys.exit(0)
''',
        "rationale": "the model's precondition (0<=head_kind<=3) bounds the "
                     "kinds it can pass to the exception classification to "
                     "{0,1,2,3}; each reachable failure kind is realized by a "
                     "concrete requests.exceptions class whose retry-tuple "
                     "membership equals is_retryable. A reachable kind with no "
                     "real class / wrong membership => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
