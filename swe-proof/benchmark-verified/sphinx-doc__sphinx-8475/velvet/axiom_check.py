#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8475.

Executes the REAL `requests` exception hierarchy and `isinstance`/`except`
dispatch (the callees the patch leaves UNCHANGED — it only widens the inner
`except` clause) and asserts that every observation matches the deep models in
Solution.lean's pure region:

  * (A-reference) `RequestFailure` + `retriable` faithfully model the inner
        catch-set membership:
          - `TooManyRedirects` is NOT caught by `except HTTPError` (pre-patch
            set), but IS caught by `except (HTTPError, TooManyRedirects)`
            (post-patch set) — the single soundness-critical class-topology fact;
          - `HTTPError` is caught by both inner sets;
          - an unrelated `Exception` is caught by neither inner set.
  * (A-reference) `classifyUnhandled` faithfully models the top-level handler's
        status reading: `HTTPError` 401 -> working, 503 -> ignored, else broken;
        `TooManyRedirects` and any other `Exception` -> broken (they are not
        `HTTPError`, so they fall to `except Exception`).

The check uses real `raise ... except` control flow (not just `issubclass`) so
it actually exercises the dispatch the patched code relies on. Imports stdlib +
`requests` (present in the instance image). Exit 0 iff every obligation holds.
"""
import random
import sys

from requests.exceptions import HTTPError, TooManyRedirects, RequestException


# --- Solution.lean deep models, transliterated -------------------------------
# RequestFailure: ("status", code) | ("redirect",) | ("other",)
# retriable e := match e: .statusError _ -> True | .redirectLoop -> True | .otherFailure -> False
# classifyUnhandled e := .statusError 401 -> working | 503 -> ignored | _ -> broken
#                        | .redirectLoop -> broken | .otherFailure -> broken
def model_retriable(e):
    kind = e[0]
    if kind == "status":
        return True
    if kind == "redirect":
        return True
    return False


def model_classify_unhandled(e):
    kind = e[0]
    if kind == "status":
        code = e[1]
        if code == 401:
            return "working"
        if code == 503:
            return "ignored"
        return "broken"
    # redirect / other
    return "broken"


# --- real-dispatch helpers ----------------------------------------------------
def make_real_exception(e):
    """Build the real `requests` exception object for an abstract RequestFailure."""
    kind = e[0]
    if kind == "status":
        err = HTTPError("status %d" % e[1])
        # The top-level handler reads err.response.status_code.
        err.response = _FakeResponse(e[1])
        return err
    if kind == "redirect":
        return TooManyRedirects("Exceeded redirects")
    return ValueError("some other failure")  # an unrelated Exception


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def caught_by(exc, catch_tuple):
    """Return True iff `except catch_tuple` catches a freshly-raised `exc` —
    real `raise ... except` dispatch, not a static issubclass query."""
    try:
        raise exc
    except catch_tuple:
        return True
    except BaseException:
        return False


def real_top_level_status(exc):
    """The top-level handler of check_uri, transliterated VERBATIM from the repo
    (linkcheck.py:181-191), executed against the real exception object:

        except HTTPError as err:
            if err.response.status_code == 401:  return 'working'
            elif err.response.status_code == 503: return 'ignored'
            else: return 'broken'
        except Exception as err:
            return 'broken'
    """
    try:
        raise exc
    except HTTPError as err:
        if err.response.status_code == 401:
            return "working"
        elif err.response.status_code == 503:
            return "ignored"
        else:
            return "broken"
    except Exception:  # noqa: BLE001 - mirrors the repo's broad handler
        return "broken"


PRE_PATCH_INNER = (HTTPError,)                      # `except HTTPError`
POST_PATCH_INNER = (HTTPError, TooManyRedirects)    # `except (HTTPError, TooManyRedirects)`


def check_failure(e):
    exc = make_real_exception(e)

    # (1) class-topology / inner catch-set faithfulness.
    real_caught_post = caught_by(exc, POST_PATCH_INNER)
    assert real_caught_post == model_retriable(e), (
        "retriable model unsound for %r: real `except (HTTPError, TooManyRedirects)` "
        "caught=%r, model retriable=%r" % (e, real_caught_post, model_retriable(e)))

    # (2) the discriminating fact: TooManyRedirects escapes the PRE-patch inner
    #     clause but is caught by the POST-patch one (and HTTPError by both).
    real_caught_pre = caught_by(make_real_exception(e), PRE_PATCH_INNER)
    if e[0] == "redirect":
        assert real_caught_pre is False, (
            "soundness anchor broken: TooManyRedirects WAS caught by `except "
            "HTTPError` — the bug premise (it is not an HTTPError subclass) fails")
        assert real_caught_post is True, (
            "TooManyRedirects not caught by the widened inner clause")
    elif e[0] == "status":
        assert real_caught_pre is True and real_caught_post is True, (
            "HTTPError must be caught by both inner clauses, got pre=%r post=%r"
            % (real_caught_pre, real_caught_post))
    else:  # other
        assert real_caught_pre is False and real_caught_post is False, (
            "an unrelated Exception must be caught by neither inner clause")

    # (3) classifyUnhandled faithfulness against the real top-level handler.
    real_status = real_top_level_status(make_real_exception(e))
    assert real_status == model_classify_unhandled(e), (
        "classifyUnhandled model unsound for %r: real top-level handler -> %r, "
        "model -> %r" % (e, real_status, model_classify_unhandled(e)))


def main():
    # --- static topology anchors (the class relationships the model rests on) -
    assert not issubclass(TooManyRedirects, HTTPError), (
        "TooManyRedirects is unexpectedly a subclass of HTTPError")
    assert not issubclass(HTTPError, TooManyRedirects)
    assert issubclass(TooManyRedirects, RequestException)
    assert issubclass(HTTPError, RequestException)

    # --- boundary failures ----------------------------------------------------
    boundary = [
        ("status", 401), ("status", 503), ("status", 200), ("status", 0),
        ("status", 301), ("status", 400), ("status", 403), ("status", 404),
        ("status", 500), ("status", 502), ("status", 504),
        ("redirect",), ("other",),
    ]
    for e in boundary:
        check_failure(e)

    # --- randomized fuzz over status codes + the three failure kinds ----------
    rng = random.Random(8475)
    for _ in range(20000):
        choice = rng.randint(0, 2)
        if choice == 0:
            e = ("status", rng.randint(0, 599))
        elif choice == 1:
            e = ("redirect",)
        else:
            e = ("other",)
        check_failure(e)

    print("G-AX OK: RequestFailure/retriable/classifyUnhandled deep models sound "
          "against the real requests exception hierarchy on %d boundary + 20000 "
          "fuzz failures. Anchor confirmed: TooManyRedirects is NOT caught by "
          "`except HTTPError` but IS caught by `except (HTTPError, "
          "TooManyRedirects)`; HTTPError 401->working/503->ignored/else->broken; "
          "other -> broken." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
