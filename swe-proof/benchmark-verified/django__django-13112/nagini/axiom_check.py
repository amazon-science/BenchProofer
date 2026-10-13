#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13112.

There is NO consumed @ContractOnly axiom in this bundle: the whole reference
normalization is modelled DEEPLY (spelled-out pure folds `lower_cp` / `normfold`
/ `first_dot` / `keep_count` / `normalized` in model.py). This script validates
that deep model against the REAL Python behaviour it stands in for (the
A-reference): the post-fix transformation of a model reference string,

    if '.' in model:
        app_label, model_name = model.split('.')
        ref = '%s.%s' % (app_label, model_name.lower())   # label case kept
    else:
        ref = model.lower()

built from the stdlib `str.split('.')`, `str.lower()` and `%`-formatting — the
exact operations the gold patch performs. The deep model must reproduce this
function on every in-domain input.

Domain: a model reference is either a bare model name (no dot) or a qualified
name `app_label.model_name` with EXACTLY ONE dot (these are the only shapes
Django ever produces and the only ones the gold transformation accepts — two
or more dots make the gold's tuple-unpack raise ValueError). Identifiers are
ASCII (letters/digits/underscore), which is precisely where the model's ASCII
`lower_cp` agrees with `str.lower()`.

Imports nothing repo-specific — only the inputs are exercised against the
reference transformation expressed in pure Python. Exit 0 iff every observation
matches the deep model.
"""
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def lower_cp(c):
    """model.py `lower_cp`: ASCII lower-casing of one code point."""
    if 65 <= c <= 90:
        return c + 32
    return c


def first_dot(s):
    """model.py `first_dot`: index of first '.' (46) or len(s)."""
    for k, c in enumerate(s):
        if c == 46:
            return k
    return len(s)


def normfold(s, keep):
    """model.py `normfold`: keep first `keep` verbatim, lower-case the rest."""
    return [s[k] if k < keep else lower_cp(s[k]) for k in range(len(s))]


def keep_count(s):
    """model.py `keep_count`."""
    p = first_dot(s)
    return p if p < len(s) else 0


def normalized_model(s):
    """model.py `normalized`, on a list of code points -> list of code points."""
    return normfold(s, keep_count(s))


# --- the REAL transformation the gold patch performs (the A-reference) -------

def gold_transform(model):
    """The post-fix reference normalization, using only stdlib str operations."""
    if '.' in model:
        app_label, model_name = model.split('.')      # exactly one dot in-domain
        return '%s.%s' % (app_label, model_name.lower())
    return model.lower()


def check(model):
    """Assert deep model == real gold transformation on `model` (a str)."""
    observed = [ord(ch) for ch in gold_transform(model)]      # real behaviour
    expected = normalized_model([ord(ch) for ch in model])    # deep model
    assert observed == expected, (
        "deep model unsound on %r: gold transform gave %r, deep model gives %r"
        % (model, observed, expected))


def main():
    # ASCII identifier alphabet (the in-domain character set) + a few extras.
    letters_upper = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    letters_lower = [chr(c) for c in range(ord('a'), ord('z') + 1)]
    digits = [chr(c) for c in range(ord('0'), ord('9') + 1)]
    ident_chars = letters_upper + letters_lower + digits + ['_']

    # --- boundary cases ---------------------------------------------------
    boundary = [
        "",                       # empty
        "a", "Z", "_", "0",       # single chars
        "Author", "AUTHOR", "author",
        "MiXedCase_migrations",   # the F2P app label, bare
        "MiXedCase_migrations.author",
        "MiXedCase_migrations.Author",
        "MiXedCase_migrations.AUTHOR",
        "MiXedCase_migrations.book",
        "MiXedCase_migrations.magazine",
        "DJ_RegLogin.Category",   # the issue's reference
        "DJ_RegLogin.Content",
        "app.MyModel",
        "App.model",
        "MyApp.MyModel",
        ".",                      # dot only -> '' + '.' + ''
        "A.",                     # empty model name
        ".B",                     # empty app label
        "lowerapp.UPPERMODEL",
        "UPPERAPP.lowermodel",
        "auth.User",
        "contenttypes.ContentType",
    ]
    for m in boundary:
        check(m)

    # --- randomized fuzz: bare names (no dot) -----------------------------
    rng = random.Random(13112)
    for _ in range(20000):
        n = rng.randint(0, 18)
        name = "".join(rng.choice(ident_chars) for _ in range(n))
        check(name)

    # --- randomized fuzz: exactly one dot (app_label.model_name) ----------
    for _ in range(20000):
        a = rng.randint(0, 12)
        b = rng.randint(0, 12)
        app = "".join(rng.choice(ident_chars) for _ in range(a))
        mod = "".join(rng.choice(ident_chars) for _ in range(b))
        check(app + "." + mod)

    print("G-AX OK: deep model (normalized) == real gold reference transform "
          "on %d boundary + 40000 fuzz inputs (bare + single-dot, ASCII "
          "identifiers); app-label case preserved, model name lower-cased."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
