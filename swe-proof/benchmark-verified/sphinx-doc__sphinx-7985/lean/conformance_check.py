#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-7985.

Differential test of the R/I shadow of `implementation_checkLink` against the
behavior of the patched `check()` classifier (gold patch.diff) over >=1e5 fuzzed
inputs. Exit 0 iff zero disagreements.

Modeled function: the network-free classification prefix of the nested `check()`
in CheckExternalLinksBuilder.check_thread (sphinx/builders/linkcheck.py).

Bridged observations (mapping.md): the source-relative path presence
(`path.exists(path.join(srcdir, uri))`), the skip-pattern match
(`any(rex.match(uri) for rex in self.to_ignore)`), and the web-resolution stage
outcome are each provided as fuzzed inputs (localFileExists / ignoreMatch /
httpResult). The patched scheme test uses the REAL regex. stdlib-only.
"""
import random
import re
import string
import sys

URI_RE = re.compile('[a-z]+://')

STATUSES = ["unchecked", "working", "broken", "ignored", "localLink", "redirected"]


def gold_check(uri, local_file_exists, ignore_match, http_result):
    """Faithful transcription of the PATCHED `check()` classification prefix.

    `self.good`/`self.broken`/`self.redirected`/`check_uri()` (the http branch)
    are the unchanged subtree: its observed outcome is `http_result`.
    """
    if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
        return 'unchecked'
    elif not uri.startswith(('http:', 'https:')):
        if URI_RE.match(uri):
            return 'unchecked'
        else:
            if local_file_exists:
                return 'working'
            else:
                if ignore_match:
                    return 'ignored'
                else:
                    return 'broken'
    else:
        return http_result


# Lean status name -> gold status string
LEAN_TO_GOLD = {
    "unchecked": "unchecked", "working": "working", "broken": "broken",
    "ignored": "ignored", "localLink": "local", "redirected": "redirected",
}


def lean_shadow(uri, local_file_exists, ignore_match, http_result):
    """R/I shadow of implementation_checkLink (Lean), with deep models inlined."""
    def starts_with_hash_mailto(u):
        return u.startswith('#') or u.startswith('mailto:')

    def starts_with_http(u):
        return u.startswith('http:') or u.startswith('https:')

    def has_uri_scheme(u):
        i = 0
        while i < len(u) and 'a' <= u[i] <= 'z':
            i += 1
        return i > 0 and u[i:].startswith('://')

    if len(uri) == 0 or starts_with_hash_mailto(uri):
        out = "unchecked"
    elif not starts_with_http(uri):
        if has_uri_scheme(uri):
            out = "unchecked"
        elif local_file_exists:
            out = "working"
        elif ignore_match:
            out = "ignored"
        else:
            out = "broken"
    else:
        out = http_result  # passthrough; http_result is a Lean LinkStatus name
    return LEAN_TO_GOLD[out]


def run_case(uri, lfe, im, hr):
    g = gold_check(uri, lfe, im, hr)
    # the http branch passes through hr (a Lean status name) -> normalize to gold
    g_norm = LEAN_TO_GOLD.get(hr, hr) if (
        not (len(uri) == 0 or uri.startswith(('#', 'mailto:')))
        and uri.startswith(('http:', 'https:'))
    ) else g
    s = lean_shadow(uri, lfe, im, hr)
    if s != g_norm:
        print(f"DISAGREE uri={uri!r} lfe={lfe} im={im} hr={hr}: lean={s} gold={g_norm}")
        sys.exit(1)


def main():
    rng = random.Random(20240630)
    # deterministic boundary cases
    fixed = [
        "", "#a", "mailto:x@y", "ftp://h/p", "ftp:legacy", "conf.py",
        "path/to/notfound", "http://a.b", "https://a.b", "HTTP://a",
        "a://x", "abc://y", "://z", "weird:thing", "rel/path", "../up",
    ]
    for uri in fixed:
        for lfe in (False, True):
            for im in (False, True):
                for hr in STATUSES:
                    run_case(uri, lfe, im, hr)

    alphabet = string.ascii_letters + string.digits + ":/.#-_ @~"
    n = 0
    target = 200_000
    while n < target:
        ln = rng.randint(0, 14)
        uri = "".join(rng.choice(alphabet) for _ in range(ln))
        # also build scheme/prefix-biased variants
        variants = [uri]
        pre = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(0, 5)))
        variants.append(pre + rng.choice(["", "://", ":", "/", "//"]) + uri)
        variants.append(rng.choice(["#", "mailto:", "http:", "https:", "ftp:"]) + uri)
        for v in variants:
            run_case(v, rng.choice([False, True]), rng.choice([False, True]),
                     rng.choice(STATUSES))
            n += 1

    print(f"G-CONF OK: {n} fuzzed cases, zero disagreements")
    sys.exit(0)


if __name__ == "__main__":
    main()
