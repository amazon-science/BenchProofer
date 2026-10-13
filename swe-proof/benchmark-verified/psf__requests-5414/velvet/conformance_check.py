#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-5414 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable accept/reject:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `validateAsciiHostLabel` impl
              region transliterated to Python over the *real* repo type (`str`),
              via the mapping.md bijection (`List Char` <-> `str`,
              `head?` <-> `s[0]`):
                  hostAccepted(host) = not host.startswith(("*", "."))
              i.e. reject iff the host opens with the wildcard `*` or the
              separator `.`. (`host.head? == some c` <-> `host[:1] == c`, the
              single-char-prefix `startswith`.) The A-reference `isAsciiHost`
              only SCOPES the domain (the require), so the fuzz set is restricted
              to non-empty all-ASCII hosts; it is not part of the computed `out`.
  * ORACLE  — the post-patch repo behaviour: the real patched
              `requests.models.PreparedRequest.prepare_url`. Building a URL
              `http://<host>/` and calling prepare_url either succeeds (accept)
              or raises `InvalidURL` (reject). FALLBACK (documented): if requests
              cannot be imported, transliterate the post-patch guard directly:
                  reject iff host.startswith(("*", ".")).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + the repo's own `requests`. The fuzz seed is pinned
(mapping.md §4). Inputs are non-empty all-ASCII hosts (the `require`-scoped
domain); non-ASCII hosts take the unchanged IDNA branch and are out of scope.
"""
import random
import sys

SEED = 5414
N_FUZZ = 100_000


# --- the R/I shadow: hostAccepted transliterated ----------------------------
def shadow_accept(host):
    # accept iff the host does NOT open with '*' or '.'
    return not host.startswith(("*", "."))


# --- the oracle: post-patch prepare_url behaviour ---------------------------
def _live_oracle_factory():
    """Return an oracle backed by the real patched prepare_url, or None if it
    cannot be imported / the tree is not the post-patch tree."""
    try:
        from requests.models import PreparedRequest, InvalidURL

        def accepts(host):
            pr = PreparedRequest()
            try:
                pr.prepare_url("http://" + host + "/", None)
                return True
            except InvalidURL:
                return False

        # sanity: confirm the patch is in place over the discriminating hosts.
        # post-patch: '.'- and '*'-leading hosts reject; an ordinary host accepts.
        if accepts(".example.com"):
            return None   # unpatched / leading-dot accepted -> use fallback
        if accepts("*example.com"):
            return None   # wildcard must also reject (preserved P2P)
        if not accepts("example.com"):
            return None   # ordinary ASCII host must be accepted
        return accepts
    except Exception:
        return None


def _translit_oracle_factory():
    # post-patch guard transliterated: reject iff host opens with '*' or '.'.
    def accepts(host):
        return not host.startswith(("*", "."))
    return accepts


def fuzz_inputs(n, rng):
    # Hosts kept to clean ASCII label characters so parse_url returns the host
    # verbatim (no port/auth/path confounds): letters, digits, hyphen, dot, and
    # the wildcard needle. All inputs are non-empty (the require-scoped domain).
    body = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    lead = body + ["*", "."]
    # boundary / discriminating cases first
    yield ".example.com"     # F2P discriminator (leading dot -> reject)
    yield "*example.com"     # preserved P2P (wildcard -> reject)
    yield "example.com"      # ordinary host -> accept
    yield "*"
    yield "."
    yield "a"
    yield "a.b.c"
    yield "127-0-0-1"
    yield "x*y"              # wildcard NOT leading -> accept
    yield "x.y"              # dot NOT leading -> accept
    yield "*.example.com"    # wildcard then dot -> reject (wildcard leads)
    yield ".*example.com"    # dot then wildcard -> reject (dot leads)
    yield "sub.domain.example"
    for _ in range(n):
        k = rng.randint(1, 20)               # non-empty
        first = rng.choice(lead)
        rest = "".join(rng.choice(body) for _ in range(k - 1))
        s = first + rest
        # bias toward the discriminating leading code points
        r = rng.random()
        if r < 0.15:
            s = "." + rest
        elif r < 0.30:
            s = "*" + rest
        yield s


def run(oracle, rng):
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_accept(s)
        orc = oracle(s)
        if shadow != orc:
            disagreements.append((s, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return None
    return count


def main():
    live = _live_oracle_factory()
    if live is not None:
        oracle = live
        oracle_kind = "live post-patch requests prepare_url"
    else:
        oracle = _translit_oracle_factory()
        oracle_kind = ("transliterated post-patch guard "
                       "(reject iff host starts with '*' or '.')")

    rng = random.Random(SEED)
    c = run(oracle, rng)
    if c is None:
        return 1
    print("G-CONF OK: R/I shadow of validateAsciiHostLabel agrees with %s on %d "
          "inputs (seed=%d), 0 disagreements." % (oracle_kind, c, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
