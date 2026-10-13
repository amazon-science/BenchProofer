#!/usr/bin/env python3
"""G-CONF differential conformance for sphinx-doc__sphinx-8475 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`resolveLinkStatus`) is the HEAD-then-GET dispatch of
`check_uri()` (`sphinx/builders/linkcheck.py:168-204`):

    try:
        response = requests.head(req_url, allow_redirects=True, ...)
        response.raise_for_status()
    except (HTTPError, TooManyRedirects):        # <-- the fix widens this set
        # retry with GET request if that fails, some servers
        # don't like HEAD requests.
        response = requests.get(req_url, stream=True, ...)
        response.raise_for_status()
    except HTTPError as err:
        ... -> 'working' / 'ignored' / 'broken'
    except Exception as err:
        return 'broken', str(err), 0

The CHANGED behaviour the spec pins is *which `except` clause catches a HEAD
attempt that exhausts the redirect budget* (`TooManyRedirects`): post-patch the
inner clause catches it and a full GET fetch is retried; pre-patch it escapes the
inner clause (since `TooManyRedirects` is not an `HTTPError` subclass) and is
reported `broken` by the top-level handler.

This is not reproducible as a pure, network-free R/I shadow this gate can fuzz
over >=1e5 inputs:

  * The only observable the fix produces is the reported status of a link, which
    `check_uri` derives from the LIVE outcomes of `requests.head` / `requests.get`
    against a real HTTP endpoint. It materializes only after a server actually
    answers a HEAD with an infinite redirect loop and a GET with 200 — which is
    exactly what the F2P test stands up: an `InfiniteRedirectOnHeadHandler`
    `http.server` on localhost, driven through the whole `app.builder.build_all()`
    linkcheck pipeline (`tests/test_build_linkcheck.py::test_TooManyRedirects_on_HEAD`).
    Reproducing the observable requires the live request machinery, not a
    transliteration this gate can fuzz.
  * The dispatch's R/I content (`retried = isinstance(ex, (HTTPError,
    TooManyRedirects))`, then classify the retried/unretried outcome) has no
    input-dependent computation on value contents to differentially refute — the
    discriminating fact is the BRANCH taken (which `except` catches the HEAD
    failure), driven by the real exception hierarchy + `isinstance` dispatch,
    covered by axiom_check.py (G-AX).

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region's observable is a
live-network branch-dispatch side effect with no network-free, input-dependent
R/I shadow, set meta.json conf_skip=true and ship this status=skip stub.
Soundness of the modeled dispatch is carried instead by G-VERIFY (the spec
provably forces a redirect-budget exhaustion to be retried and a reached fallback
to be reported `working`), G-DIFF (the prepatch, whose inner set excludes the
redirect-budget exhaustion, fails exactly on a `.failed .redirectLoop` head probe
with a reachable fallback), G-MUT, and G-AX (the real `requests` hierarchy: the
inner `except HTTPError` does NOT catch `TooManyRedirects`, `except (HTTPError,
TooManyRedirects)` does, and the top-level handler routes statuses as
`classifyUnhandled` says). See mapping.md section 3/4 and refinement.md section A/C.
"""
import sys


def main():
    print("G-CONF status=skip: sphinx-doc__sphinx-8475 — the modeled do-block "
          "dispatches a link's reported status from the live outcomes of HEAD/GET "
          "requests; post-patch the inner `except (HTTPError, TooManyRedirects)` "
          "retries a redirect-budget exhaustion with a full GET fetch. The only "
          "observable is a live-network branch-dispatch side effect with no "
          "network-free, input-dependent R/I shadow. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF + G-MUT + G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
