#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1142 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types. The modeled changed
              operation is `contentLength` (`announcedSize`): the announced
              payload size as an `Option Nat` — `some n` (a content length of
              `n`) or `none` (no length announced). The size-obtaining mechanics
              for a present payload (`body.seek`/`body.tell` and `len(body)`) are
              UNCHANGED code and are transliterated faithfully as the I-bridge
              that produces the `Payload` shape from the raw `body` object
              (mapping.md §2). There are NO A-tagged callees in this impl region
              (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `requests.models.PreparedRequest.prepare_content_length` applied at
              base_commit (the real correctness oracle, G-RESOLVE), imported from
              the repo with the gold patch applied (the harness applies patch.diff
              before this runs).

The observable normal form is the state of `self.headers['Content-Length']`:
either the announced string value, or the sentinel `("__ABSENT__",)` when no
`Content-Length` header is present. They must agree on every input. Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo
under test only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. The method set instantiates the `carriesBody` bijection over BOTH 'GET'
and 'HEAD' (carriesBody = False) and body-carrying verbs (carriesBody = True),
so the F2P's HEAD half is exercised alongside the issue's GET.
"""
import io
import random
import sys

SEED = 1142
N_FUZZ = 100_000

ABSENT = ("__ABSENT__",)  # normal-form sentinel: no Content-Length header

# The methods 'prepare_content_length' treats as body-less (carriesBody=False);
# every other (already upper-cased) verb is body-carrying (carriesBody=True).
BODYLESS_METHODS = ("GET", "HEAD")


# --- the R/I shadow: Solution.lean announcedSize transliterated to Python ----

def shadow_content_length(body, method):
    """Full transliteration of `contentLength`/`announcedSize` over a real
    `body` object and an (already upper-cased) method string.

    The I-bridge classifies the raw `body` into the `Payload` shape exactly as
    the unchanged repo branch structure does, obtaining the size `n` via the
    unchanged seek/tell or len mechanics; the modeled changed op then decides
    the announcement."""
    carries_body = method not in BODYLESS_METHODS

    # I-bridge: raw body -> Payload shape (+ size for present payloads).
    if hasattr(body, "seek") and hasattr(body, "tell"):
        body.seek(0, 2)
        n = body.tell()
        body.seek(0, 0)
        payload = ("seekable", n)
    elif body is not None:
        payload = ("measurable", len(body))
    else:
        payload = ("absent",)

    # announcedSize payload carriesBody  : Option Nat
    if payload[0] == "seekable":
        announced = payload[1]
    elif payload[0] == "measurable":
        announced = payload[1]
    else:  # absent
        announced = 0 if carries_body else None

    # Option Nat -> observable header state (mapping.md §2): some n -> str(n);
    # none -> Content-Length absent.
    return str(announced) if announced is not None else ABSENT


def oracle_content_length(body, method):
    """patch.diff's behaviour: the patched prepare_content_length from the repo
    at base_commit with the gold patch applied. Observe the resulting
    Content-Length header (or its absence)."""
    from requests.models import PreparedRequest
    from requests.structures import CaseInsensitiveDict

    pr = PreparedRequest()
    pr.headers = CaseInsensitiveDict()
    pr.method = method
    pr.prepare_content_length(body)
    if "Content-Length" in pr.headers:
        return str(pr.headers["Content-Length"])
    return ABSENT


def make_body(kind, n, rng):
    """Materialize a real `body` object of the requested shape.
    * seekable    -> a file-like with seek+tell, of size n
    * measurable  -> an in-memory buffer (bytes) without seek/tell, of size n
    * absent      -> None
    """
    if kind == "seekable":
        return io.BytesIO(bytes(rng.randrange(256) for _ in range(n)))
    if kind == "measurable":
        return bytes(rng.randrange(256) for _ in range(n))
    return None


def fuzz_inputs(n, rng):
    methods = ["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    # --- boundary cases first (plan §4.1 step 4) -------------------------
    # The exact issue + F2P scenarios: a body-less GET and HEAD announce nothing.
    yield ("absent", 0, "GET")
    yield ("absent", 0, "HEAD")
    # A body-less body-carrying method still announces zero.
    yield ("absent", 0, "POST")
    yield ("absent", 0, "PUT")
    # An empty in-memory buffer announces 0 regardless of method.
    yield ("measurable", 0, "GET")
    yield ("measurable", 0, "POST")
    # A non-empty in-memory buffer announces its length regardless of method.
    yield ("measurable", 5, "GET")
    yield ("measurable", 5, "POST")
    # A seekable payload announces its size regardless of method (incl. empty).
    yield ("seekable", 0, "GET")
    yield ("seekable", 7, "HEAD")
    yield ("seekable", 7, "POST")

    kinds = ["seekable", "measurable", "absent"]
    for _ in range(n):
        kind = rng.choice(kinds)
        size = rng.randint(0, 64) if kind != "absent" else 0
        method = rng.choice(methods)
        yield (kind, size, method)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kind, size, method in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # Fresh body objects per side (the oracle's seek/tell mutates position).
        shadow = shadow_content_length(make_body(kind, size, rng), method)
        oracle = oracle_content_length(make_body(kind, size, rng), method)
        if shadow != oracle:
            disagreements.append((kind, size, method, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, size, method, sh, orc in disagreements:
            print("  body=%s(%d) method=%s shadow=%r oracle=%r"
                  % (kind, size, method, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of contentLength (+ unchanged size-obtaining "
          "I-bridge) agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
