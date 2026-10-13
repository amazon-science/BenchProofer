#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14404.

This bundle consumes NO @ContractOnly axiom: the one string operation that
changed -- building the slash-redirect target from the request's FULL path
rather than its prefix-stripped path -- is modelled DEEPLY in model.py
(`with_trailing_slash`, the `result.append(47)` impl). There is therefore no
axiom Ensures to validate against a callee.

What G-AX validates here is the single load-bearing DEEP-MODELLING premise the
refinement rests on (mapping.md §2.1 / §3, refinement.md §A5/§D):

  the request's full path `request.path` carries any deployment path prefix
  (SCRIPT_NAME / FORCE_SCRIPT_NAME), while `request.path_info` does NOT.

Hence building the redirect target from `request.path` ("%s/" % request.path)
restores the prefix, while the pre-patch "%s/" % request.path_info drops it,
and the two coincide exactly when no prefix is present. We reproduce the REAL
path construction from django/core/handlers/wsgi.py:65-76 (WSGIRequest.__init__,
unchanged by this instance) and assert:

  (1) model `with_trailing_slash(request.path)` == the GOLD target "%s/" % request.path
  (2) when a non-empty prefix is present, the GOLD target includes the prefix
      and the BUG target ("%s/" % request.path_info) does NOT  (they differ)
  (3) when no prefix is present, GOLD and BUG targets coincide  (no regression)

Imports nothing repo-specific: only the standard library. Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- model.py reference encoding (kept in lock-step with model.py) -----------

def with_trailing_slash(codepoints):
    """Reference of model.py's deep model `with_trailing_slash`, as a list of
    code points: the path followed by code point 47 ('/')."""
    return list(codepoints) + [47]


# --- the REAL request-path construction (django/core/handlers/wsgi.py:65-76) -
# Verbatim transcription of WSGIRequest.__init__'s path / path_info logic,
# which this instance does NOT change. get_script_name returns FORCE_SCRIPT_NAME
# when set, else the WSGI SCRIPT_NAME (wsgi.py:159-187); we feed the resulting
# script_name directly.

def build_path_info(raw_path_info):
    # path_info = get_path_info(environ) or '/'
    return raw_path_info or '/'


def build_path(script_name, path_info):
    # self.path = '%s/%s' % (script_name.rstrip('/'), path_info.replace('/', '', 1))
    return '%s/%s' % (script_name.rstrip('/'), path_info.replace('/', '', 1))


def gold_target(request_path):
    # '%s/' % request.path     (the FIX)
    return '%s/' % request_path


def bug_target(request_path_info):
    # '%s/' % request.path_info     (the pre-patch BUG)
    return '%s/' % request_path_info


# --- the checks --------------------------------------------------------------

def check_case(script_name, raw_path_info):
    path_info = build_path_info(raw_path_info)
    path = build_path(script_name, path_info)

    gold = gold_target(path)
    bug = bug_target(path_info)

    # (1) the model's deep model of "%s/" % request.path == the real gold target
    model_target = with_trailing_slash([ord(ch) for ch in path])
    assert model_target == [ord(ch) for ch in gold], (
        "deep model with_trailing_slash unsound: script_name=%r path_info=%r: "
        "model gave %r, gold '%%s/' %% request.path gave %r"
        % (script_name, path_info, model_target, [ord(ch) for ch in gold]))

    prefix = script_name.rstrip('/')
    if prefix:
        # (2) with a non-empty prefix the gold target carries it, and the gold
        #     and bug targets DIFFER (the bug, building from the prefix-stripped
        #     path, is observable). Note: the bug target may *coincidentally*
        #     also start with the prefix when path_info echoes it, so the
        #     load-bearing claim is `gold != bug`, not "bug lacks the prefix".
        assert gold.startswith(prefix + '/'), (
            "gold target %r does not carry prefix %r (script_name=%r)"
            % (gold, prefix, script_name))
        assert gold != bug, (
            "with prefix %r the gold and bug targets coincide (gold=%r bug=%r) "
            "-- the bug would be unobservable" % (prefix, gold, bug))
    else:
        # (3) no prefix => gold and bug coincide (the fix is a no-op there)
        assert gold == bug, (
            "without a prefix the gold and bug targets differ "
            "(script_name=%r gold=%r bug=%r)" % (script_name, gold, bug))


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        # (script_name, raw PATH_INFO)
        ('', '/admin/articles'),                 # no prefix
        ('', '/admin/articles/'),                # no prefix, trailing slash
        ('', ''),                                # empty path_info -> '/'
        ('/prefix/', '/admin/articles'),         # the F2P SCRIPT_NAME='/prefix/'
        ('/prefix', '/admin/articles'),          # prefix without trailing slash
        ('/prefix/', '/admin/admin_views/article'),  # the F2P changelist[:-1]
        ('/deep/nested/prefix/', '/admin/x'),    # multi-segment prefix
        ('/p', '/'),                             # minimal prefix, root path_info
        ('/prefix/', ''),                        # prefix + empty path_info
        ('/Prefix-With.Dots_123/', '/a/b/c'),    # punctuation in prefix
    ]
    for script_name, raw in boundary:
        check_case(script_name, raw)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(14404)
    seg_chars = "abcdefABCDEF0123456789-_.~"
    for _ in range(20000):
        # random script_name (often empty), random path_info
        if rng.random() < 0.35:
            script_name = ''
        else:
            n = rng.randint(1, 4)
            script_name = '/' + '/'.join(
                ''.join(rng.choice(seg_chars) for _ in range(rng.randint(1, 6)))
                for _ in range(n))
            if rng.random() < 0.5:
                script_name += '/'
        m = rng.randint(0, 5)
        raw = '/' + '/'.join(
            ''.join(rng.choice(seg_chars) for _ in range(rng.randint(0, 6)))
            for _ in range(m)) if m else rng.choice(['', '/'])
        check_case(script_name, raw)

    print("G-AX OK: deep model with_trailing_slash(request.path) == gold "
          "'%%s/' %% request.path on %d boundary + 20000 fuzz cases; "
          "request.path carries the SCRIPT_NAME/FORCE_SCRIPT_NAME prefix and "
          "request.path_info does not (prefix present => gold != bug; absent "
          "=> gold == bug)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
