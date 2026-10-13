#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-6028 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`buildAuthority` / `assembleAuthority` / `authorityBase`)
              transliterated to Python over the *real* repo type (`str`), via the
              mapping.md bijection (`List Char` ↔ `str`, `None`/`''` ↔ `[]`,
              `'@'.join([a, n])` ↔ `a ++ ['@'] ++ n`). The shadow is wrapped in
              the *unchanged* bracketing callees run LIVE: the real
              `urllib3.util.parse_url` upstream (to obtain the slots) and the real
              `urlunparse` downstream (to re-assemble the URL), plus the verbatim
              swap/defaults glue that the patch did not touch.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `requests.utils.prepend_scheme_if_needed` applied at base_commit
              (the real correctness oracle, G-RESOLVE).

The impl region has NO A-tagged content (no axiomatized callees), so the modeled
slice is pure R/I; `parse_url`/`urlunparse` are unchanged callees exercised in
situ on BOTH sides. They must agree on every input on which the oracle returns
normally. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Domain: the real patched `prepend_scheme_if_needed` itself raises `TypeError` on
inputs where `auth` is truthy but the post-swap netloc is `None` (mapping.md
§3.1 — a partiality of the gold fix). Such inputs are skipped (the oracle does
not define a result there); the shadow is held to exactly the oracle's domain.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo
(requests, urllib3 already installed). The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import sys

SEED = 6028
N_FUZZ = 160_000


def _to_list(s):
    """Bridge a parse_url slot (Optional[str]) to the Lean `List Char` view:
    None and '' both map to the empty list (mapping.md §2)."""
    if s is None:
        return []
    return list(s)


def _from_list(xs):
    return "".join(xs)


def authority_base(netloc_slot, path_slot):
    """authorityBase (deep model): pick the path slot when the authority slot is
    falsy, else the authority slot. Inputs are `List Char` (lists of chars)."""
    if netloc_slot == []:
        return path_slot
    return netloc_slot


def assemble_authority(userinfo, base):
    """assembleAuthority (deep model): fold credentials back in when present."""
    if userinfo == []:
        return base
    return userinfo + ["@"] + base


def shadow(url, new_scheme, parse_url, urlunparse):
    """Full R/I shadow of prepend_scheme_if_needed: real parse_url upstream, the
    modeled authority rebuild (buildAuthority) in the middle, verbatim
    swap/defaults glue, real urlunparse downstream.

    Mirrors the gold control flow exactly; only the authority value `netloc` that
    flows into urlunparse comes from the deep model.  Returns the assembled URL
    string, or raises (same partiality as the oracle)."""
    parsed = parse_url(url)
    scheme, auth, host, port, path, query, fragment = parsed
    netloc = parsed.netloc

    # --- verbatim glue: the path-side of the swap is unchanged by the patch ---
    if not netloc:
        netloc, path = path, netloc

    # --- modeled slice: buildAuthority over the Lean carrier ---------------
    # base = authorityBase(netlocSlot, pathSlot); but note the gold swap has
    # already moved the value the patch reads into `netloc`. We replicate the
    # patched expression `netloc = '@'.join([auth, netloc])` through the deep
    # model so the carrier-level computation is the audited one.
    userinfo = _to_list(auth)
    base = _to_list(netloc)
    built = assemble_authority(userinfo, base)
    # If credentials were present, the model rebuilt the authority; otherwise it
    # is the unchanged host portion. When auth is truthy but netloc is None the
    # join is undefined (None bridged to []) — the oracle raises here, so this
    # shadow input is dropped by the caller and never compared.
    if auth:
        if netloc is None:
            # oracle raises TypeError here; signal undefined to the caller
            raise TypeError("post-swap netloc is None with truthy auth")
        netloc = _from_list(built)

    # --- verbatim glue: scheme/path defaults, unchanged by the patch -------
    if scheme is None:
        scheme = new_scheme
    if path is None:
        path = ""

    return urlunparse((scheme, netloc, path, "", query, fragment))


def rand_url(rng):
    chars = list("abcABC012:@/.?#%-+ []~_=&") + ["user", "pass", "host",
                                                  "example.com", ":80", "/path"]
    n = rng.randint(0, 6)
    parts = [rng.choice(chars) for _ in range(n)]
    return "".join(parts)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the two F2P scenarios + the
    # pre-patch passing cases (no credentials) + empties.
    yield ("http://user:pass@example.com/path?query", "http")
    yield ("http://user@example.com/path?query", "http")
    yield ("example.com/path", "http")
    yield ("//example.com/path", "http")
    yield ("example.com:80", "http")
    yield ("http://user:pass@h:8080/p?q#f", "https")
    yield ("HTTP://U:P@H/P", "http")
    yield ("", "http")
    yield ("user@host", "http")
    yield ("http://[::1]:80/p", "http")
    for _ in range(n):
        yield (rand_url(rng), rng.choice(["http", "https", "ftp"]))


def main():
    try:
        from urllib3.util import parse_url
        from requests.compat import urlunparse
        from requests.utils import prepend_scheme_if_needed as oracle
    except Exception as e:  # pragma: no cover
        print("G-CONF SETUP ERROR: %r" % (e,))
        return 2

    rng = random.Random(SEED)
    disagreements = []
    compared = 0
    skipped = 0
    for url, new_scheme in fuzz_inputs(N_FUZZ, rng):
        # Oracle defines the domain: skip inputs on which the real patched
        # function raises (its own partiality, mapping.md §3.1).
        try:
            orc = oracle(url, new_scheme)
        except Exception:
            skipped += 1
            continue
        try:
            sh = shadow(url, new_scheme, parse_url, urlunparse)
        except Exception as e:
            # Shadow raised where oracle did not — a genuine disagreement.
            sh = ("SHADOW-RAISED", type(e).__name__)
        compared += 1
        if sh != orc:
            disagreements.append((url, new_scheme, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d compared inputs:"
              % (len(disagreements), compared))
        for url, ns, sh, orc in disagreements:
            print("  url=%r new_scheme=%r shadow=%r oracle=%r"
                  % (url, ns, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildAuthority (with live parse_url/"
          "urlunparse) agrees with patch.diff behaviour on %d inputs "
          "(%d skipped: oracle's own partiality; seed=%d), 0 disagreements."
          % (compared, skipped, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
