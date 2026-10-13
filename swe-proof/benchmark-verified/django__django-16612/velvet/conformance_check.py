#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16612 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`appendSlashRedirect` / `redirectTarget`) transliterated to
              Python over the *real* repo types, via the mapping.md §2
              bijection: the encoded-path/encoded-query carriers are produced by
              feeding the raw (path, query) through the REAL unchanged encoders
              `escape_uri_path` / `iri_to_uri` (the R legs A1/A2), then the
              concrete slash + query-suffix assembly (the I legs A3/A4/A5) is
              applied. There is no A-tagged callee left to substitute (this
              bundle consumes no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched redirect destination, i.e.
              `request.get_full_path(force_append_slash=True)` evaluated on a
              real `HttpRequest` with the same path + query string (the real
              correctness oracle the gold patch installs at sites.py:456,
              G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with the gold patch
applied by the harness). stdlib + django only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16612
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_X_FORWARDED_HOST=False,
            ALLOWED_HOSTS=["*"],
            DEFAULT_CHARSET="utf-8",
        )
    django.setup()


# --- the R/I shadow: Solution.lean redirectTarget, transliterated ------------
def shadow_redirect(path, qs):
    """redirectTarget(escape_uri_path(path), iri_to_uri(qs)) — the R/I shadow.
    R legs A1/A2: bridge via the real unchanged encoders. I legs A3-A5: the
    concrete slash + '?'-query assembly of the impl `do` block."""
    from django.utils.encoding import escape_uri_path, iri_to_uri
    encoded_path = escape_uri_path(path)                 # R (real encoder)
    encoded_query = iri_to_uri(qs) if qs else ""         # R (real encoder)
    slash = "" if encoded_path.endswith("/") else "/"    # I (A3)
    query = "" if encoded_query == "" else "?" + encoded_query  # I (A4)
    return encoded_path + slash + query                  # I (A5)


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_redirect(path, qs):
    """patch.diff's behaviour: the patched redirect destination. The gold patch
    replaces `"%s/" % request.path` with
    `request.get_full_path(force_append_slash=True)`; we evaluate exactly that
    callee on a real request carrying the same path + query string."""
    from django.http import HttpRequest
    req = HttpRequest()
    req.path = path
    req.META["QUERY_STRING"] = qs
    return req.get_full_path(force_append_slash=True)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    paths = [
        "", "/admin/auth/foo", "/admin/auth/foo/", "/admin/auth/article",
        "/prefix/admin/auth/article", "/a b/c", "/I ♥ Django/", "/x", "/x/", "/",
    ]
    queries = [
        "", "id=1", "id=123", "id=1&x=2", "q=a b", "q=I ♥ Django",
        "a=1&a=2&b=3", "next=/test_admin/admin/admin_views/article",
        "f=%3D&g=~", "empty=",
    ]
    for p in paths:
        for q in queries:
            yield (p, q)
    path_alphabet = list("abcXYZ0/9 -_.~!*'()&+$,:@é♥") + ["/"]
    qs_alphabet = list("abcXYZ0/9 -_.~=&?#%é♥+;")
    for _ in range(n):
        np = rng.randint(0, 20)
        nq = rng.randint(0, 20)
        path = "/" + "".join(rng.choice(path_alphabet) for _ in range(np))
        qs = "" if rng.random() < 0.2 else "".join(
            rng.choice(qs_alphabet) for _ in range(nq))
        yield (path, qs)


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for path, qs in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_redirect(path, qs)
        oracle = oracle_redirect(path, qs)
        if shadow != oracle:
            disagreements.append((path, qs, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for path, qs, sh, orc in disagreements:
            print("  path=%r qs=%r shadow=%r oracle=%r" % (path, qs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of appendSlashRedirect agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
