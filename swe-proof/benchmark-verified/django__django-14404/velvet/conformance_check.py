#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14404 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`appendSlashRedirect` / `redirectTarget` / `fullPath`)
              transliterated to Python over the *real* repo types, via the
              mapping.md §2 bijection: the two carriers are produced from a real
              `HttpRequest` — `mountPrefix` ↔ `script_name.rstrip('/')` and
              `localPath` ↔ `request.path_info` (the R legs A1/A2) — then the
              concrete `prefix + local + "/"` assembly (the I legs A3/A4) is
              applied. This bundle consumes no axioms, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched redirect destination, i.e.
              `"%s/" % request.path` evaluated on a real `HttpRequest` carrying
              the same `script_name` + `path_info` (the real correctness oracle
              the gold patch installs at sites.py:430, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with the gold patch
applied by the harness). stdlib + django only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 14404
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ALLOWED_HOSTS=["*"],
            DEFAULT_CHARSET="utf-8",
            FORCE_SCRIPT_NAME=None,
            USE_X_FORWARDED_HOST=False,
        )
    django.setup()


def _make_request(script_name, path_info):
    from django.test import RequestFactory
    rf = RequestFactory()
    return rf.get(path_info, SCRIPT_NAME=script_name)


# --- the R/I shadow: Solution.lean redirectTarget, transliterated ------------
def shadow_redirect(script_name, path_info):
    """redirectTarget(fullPath(mountPrefix, localPath)) — the R/I shadow.
    R legs A1/A2: bridge via the real request's mount prefix + local path.
    I legs A3/A4: the concrete `prefix + local + "/"` assembly of the impl."""
    req = _make_request(script_name, path_info)
    mount_prefix = script_name.rstrip("/")     # R (A1): carrier from the request
    local_path = req.path_info                 # R (A2): carrier from the request
    full = mount_prefix + local_path           # I (A3): fullPath
    return full + "/"                          # I (A4): trailing slash


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_redirect(script_name, path_info):
    """patch.diff's behaviour: the patched redirect destination. The gold patch
    builds the destination as `"%s/" % request.path` (was `request.path_info`);
    we evaluate exactly that expression on a real request carrying the same
    script_name + path_info."""
    req = _make_request(script_name, path_info)
    return "%s/" % req.path


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    script_names = [
        "", "/prefix/", "/prefix", "/a/b/", "/a/b",
        "/deep/mount/point/", "/x", "/",
    ]
    path_infos = [
        "/", "/admin/auth/foo", "/admin/auth/article",
        "/admin/auth/article/", "/a-b/c", "/admin/auth/article/123/", "/x",
    ]
    for s in script_names:
        for p in path_infos:
            yield (s, p)
    seg_alphabet = list("abcXYZ0/9-_.~")
    for _ in range(n):
        ns = rng.randint(0, 12)
        np = rng.randint(0, 16)
        # script_name: sometimes empty (root mount), else a non-empty prefix
        script_name = "" if rng.random() < 0.25 else (
            "/" + "".join(rng.choice(seg_alphabet) for _ in range(ns)))
        # path_info always begins with '/' (the WSGI invariant the model uses)
        path_info = "/" + "".join(rng.choice(seg_alphabet) for _ in range(np))
        yield (script_name, path_info)


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for script_name, path_info in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_redirect(script_name, path_info)
        oracle = oracle_redirect(script_name, path_info)
        if shadow != oracle:
            disagreements.append((script_name, path_info, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sn, pi, sh, orc in disagreements:
            print("  script_name=%r path_info=%r shadow=%r oracle=%r"
                  % (sn, pi, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of appendSlashRedirect agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
