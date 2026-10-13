#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14404.

Validates the single kind-A construct of this bundle:

  (A-reference) the deep model `fullPath` (Solution.lean pure region) == the
      REAL unchanged framework attribute `request.path`. The redirect
      destination is modeled DEEPLY (no consumed axiom); G-AX validates that
      deep model against the real callee.

`fullPath(mountPrefix, localPath)` is the concatenation `mountPrefix ++
localPath` (Solution.lean pure region), where, per mapping.md §2:

  * `mountPrefix` ↔ the deployment mount-point prefix the framework prepends to
    every externally-visible URL, i.e. `script_name.rstrip('/')`
    (`django/core/handlers/wsgi.py:75`), and
  * `localPath`  ↔ the per-request local path `request.path_info`.

The real framework computes the full path as
`'%s/%s' % (script_name.rstrip('/'), path_info.replace('/', '', 1))`
(`WSGIRequest.__init__`, wsgi.py:75-76). Because `path_info` always begins with
a single '/', `path_info.replace('/', '', 1)` strips exactly that leading slash
and `'%s/%s' % (prefix, rest)` re-inserts it, so the result is exactly
`prefix + path_info`. We therefore assert, over boundary + fuzzed
(script_name, path_info) pairs, on a REAL request built by the test client:

    request.path            == fullPath(mountPrefix, localPath)
    redirect destination    == redirectTarget(mountPrefix, localPath)

where `redirectTarget(mp, lp) = mp ++ lp ++ ['/']` is the value the patched
`catch_all_view` hands to `HttpResponsePermanentRedirect` (`'%s/' %
request.path`). Imports only `django` (the repo under test) + stdlib.
Exit 0 iff every obligation holds.
"""
import random
import sys


def _configure_django():
    """Minimal settings so `django.test`/`django.http` import and run."""
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


# --- Solution.lean deep model, transliterated --------------------------------
def full_path(mount_prefix, local_path):
    """Reference implementation of Solution.lean `fullPath`, over the str
    carrier: the mount-point prefix followed by the local path."""
    return mount_prefix + local_path


def redirect_target(mount_prefix, local_path):
    """Reference implementation of Solution.lean `redirectTarget`: the full path
    with a single trailing slash appended."""
    return full_path(mount_prefix, local_path) + "/"


# --- the check ---------------------------------------------------------------
def make_request(script_name, path_info):
    from django.test import RequestFactory
    rf = RequestFactory()
    # RequestFactory builds a real WSGIRequest; SCRIPT_NAME is honoured exactly
    # as a deployed server would set it (and as FORCE_SCRIPT_NAME resolves to).
    return rf.get(path_info, SCRIPT_NAME=script_name)


def check_reference(script_name, path_info):
    """Assert the deep model == the REAL request.path, and the modeled redirect
    destination == the patched `'%s/' % request.path`."""
    req = make_request(script_name, path_info)
    mount_prefix = script_name.rstrip("/")          # the carrier (mapping.md §2)
    local_path = req.path_info                       # the carrier (mapping.md §2)

    # (A-reference) deep model fullPath == real request.path
    observed_path = req.path                         # real framework attribute
    expected_path = full_path(mount_prefix, local_path)   # deep model
    assert observed_path == expected_path, (
        "fullPath deep model unsound on script_name=%r path_info=%r: "
        "request.path gave %r, deep model gives %r"
        % (script_name, path_info, observed_path, expected_path))

    # the patched redirect destination is exactly '%s/' % request.path
    observed_dest = "%s/" % req.path                 # patched catch_all_view op
    expected_dest = redirect_target(mount_prefix, local_path)   # deep model
    assert observed_dest == expected_dest, (
        "redirectTarget deep model unsound on script_name=%r path_info=%r: "
        "'%%s/' %% request.path gave %r, deep model gives %r"
        % (script_name, path_info, observed_dest, expected_dest))


def main():
    _configure_django()

    # --- boundary cases ------------------------------------------------------
    script_names = [
        "",                # mounted at server root: empty prefix
        "/prefix/",        # the F2P FORCE_SCRIPT_NAME / SCRIPT_NAME value
        "/prefix",         # without trailing slash
        "/a/b/",
        "/a/b",
        "/deep/mount/point/",       # multi-segment prefix
        "/x",
        "/",               # bare slash: rstrip('/') -> ""
    ]
    path_infos = [
        "/",
        "/admin/auth/foo",
        "/admin/auth/article",
        "/admin/auth/article/",     # already ends in slash
        "/a-b/c",                   # punctuation in local path
        "/admin/auth/article/123/", # nested, trailing slash
        "/x",
    ]
    boundary = [(s, p) for s in script_names for p in path_infos]
    for s, p in boundary:
        check_reference(s, p)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(14404)
    seg_alphabet = list("abcXYZ0/9-_.~")
    for _ in range(20000):
        ns = rng.randint(0, 12)
        np = rng.randint(0, 16)
        # script_name: sometimes empty (root mount), else a non-empty prefix
        script_name = "" if rng.random() < 0.25 else (
            "/" + "".join(rng.choice(seg_alphabet) for _ in range(ns)))
        # path_info always begins with '/' (the WSGI invariant the model uses)
        path_info = "/" + "".join(rng.choice(seg_alphabet) for _ in range(np))
        check_reference(script_name, path_info)

    print("G-AX OK: fullPath deep model (== real request.path) and "
          "redirectTarget (== patched '%%s/' %% request.path) sound on %d "
          "boundary + 20000 fuzz (script_name, path_info) pairs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
