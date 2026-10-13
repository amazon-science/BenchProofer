#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8475.

The bundle models ONE fragment: the HEAD-probe → GET-fallback block of
`check_uri`. Its Lean implementation (`implementation_probeUri`) decides, for a
lightweight (HEAD) probe outcome `light` and a fallback (GET) outcome `full`:

    response = light
    if retryWithFull(light):     # the CHANGED decision (R/I)
        response = full
    return response

where `retryWithFull(light)` is `true` iff `light in {statusError, redirectLoop}`.

This script transliterates that R/I leg into Python (`shadow_probe`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of the changed lines (`sphinx/builders/linkcheck.py:166-179`),
driven with the REAL `requests.exceptions` classes so the exception-type ↔
ReqOutcome bijection is exercised against the actual library:

    try:
        <HEAD probe>            # raises per `light`
    except (HTTPError, TooManyRedirects):
        <GET fallback>          # outcome per `full`
    # surviving response flows downstream

The surviving outcome is encoded as a `ReqOutcome` string ("ok", "statusError",
"redirectLoop", "otherFailure"), matching the Lean enum. We compare the surviving
outcome the post-patch block would carry downstream against the shadow's result.

stdlib + the in-repo `requests` library only; no network. Pinned seed: 8475
(also in mapping.md). exit 0 iff zero disagreements.
"""
import sys

SEED = 8475
N = 120_000

OUTCOMES = ["ok", "statusError", "redirectLoop", "otherFailure"]

# --- bijection: ReqOutcome <-> a real requests exception (or success) --------
# mapping.md: ok <-> no exception; statusError <-> HTTPError;
# redirectLoop <-> TooManyRedirects; otherFailure <-> any other exception.
try:
    from requests.exceptions import HTTPError, TooManyRedirects
except Exception as e:  # pragma: no cover
    print(f"status=fail could not import real requests.exceptions: {e!r}")
    sys.exit(1)


class _OtherError(Exception):
    """Stand-in for any non-HTTPError/non-TooManyRedirects failure (connection,
    TLS, the anchor-not-found Exception, ...)."""


def _raise_for(outcome):
    """Reproduce, with the REAL classes, what a probe with `outcome` does."""
    if outcome == "ok":
        return  # usable response, no exception
    if outcome == "statusError":
        raise HTTPError("error status")
    if outcome == "redirectLoop":
        raise TooManyRedirects("exceeded 30 redirects")
    if outcome == "otherFailure":
        raise _OtherError("connection failed")
    raise AssertionError(outcome)


# --- ORACLE: the post-patch try/except, run with real exception classes ------
def oracle_probe(light: str, full: str) -> str:
    """The surviving ReqOutcome that the POST-PATCH block carries downstream."""
    try:
        _raise_for(light)            # HEAD probe + raise_for_status()
        return "ok"                  # HEAD succeeded
    except (HTTPError, TooManyRedirects):
        # retry with GET request (post-patch: HTTPError OR TooManyRedirects)
        try:
            _raise_for(full)         # GET fallback + raise_for_status()
            return "ok"
        except HTTPError:
            return "statusError"
        except TooManyRedirects:
            return "redirectLoop"
        except _OtherError:
            return "otherFailure"
    except _OtherError:
        # not caught by the retry clause -> propagates (reported broken downstream)
        return "otherFailure"


# --- shadow of implementation_probeUri (the R/I leg) -------------------------
def shadow_probe(light: str, full: str) -> str:
    def retry_with_full(o):
        # Lean: statusError => true | redirectLoop => true | _ => false
        return o in ("statusError", "redirectLoop")
    response = light
    if retry_with_full(light):
        response = full
    return response


def disagree(light: str, full: str):
    got = oracle_probe(light, full)
    want = shadow_probe(light, full)
    if got != want:
        return (light, full, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # --- exhaustive: every (light, full) pair over the 4x4 enum ---
    for light in OUTCOMES:
        for full in OUTCOMES:
            d = disagree(light, full)
            if d:
                print(f"DISAGREE exhaustive light={d[0]} full={d[1]}: "
                      f"oracle={d[2]} shadow={d[3]}")
                print("status=fail")
                return 1
            checked += 1

    # --- fuzz (redundant over the finite domain, but pins the seed/volume) ---
    rnd = _lcg(SEED)
    for _ in range(N):
        light = OUTCOMES[next(rnd) % 4]
        full = OUTCOMES[next(rnd) % 4]
        d = disagree(light, full)
        if d:
            print(f"DISAGREE fuzz light={d[0]} full={d[1]}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
