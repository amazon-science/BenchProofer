#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15987.

This bundle consumes NO `@ContractOnly` axiom: the presence test is modelled
deeply over the two per-entry booleans `value_matches` / `is_path_object` and
the front-recursive fold `any_match` (model.py).  What G-AX must validate is the
A-reference — that the per-entry abstraction faithfully reflects the REAL Python
path machinery the gold patch relies on:

  (R1) The corrected presence test
            app_dir in [str(d) for d in fixture_dirs]
       equals the model's `any_match` over the per-entry value matches, where
       a configured entry's value match is  str(entry) == app_dir.  Equivalently
       the default directory is detected exactly when SOME entry's path string
       equals the default one's, regardless of the entry's Python type.

  (R2) The discriminator `is_path_object` correctly captures the raw-vs-string
       divergence the bug turned on:
         * a rich pathlib.Path whose string form equals app_dir satisfies the
           string comparison  str(d) == app_dir  (value match True) but NOT the
           raw object comparison  d == app_dir  (a PurePath is never == to a
           str) — so the pre-patch raw membership misses it;
         * a plain str entry equal to app_dir matches under BOTH comparisons.

  (R3) Hence the modelled outcomes coincide with the real outcomes:
         model post-patch result  ==  (app_dir in [str(d) for d in dirs])
         model pre-patch  result  ==  (app_dir in dirs)
       on every generated configuration.

Imports only the Python standard library (`os.path`, `pathlib` — the exact
machinery `os.path.join(...)` / `str(d)` exercise in the gold patch).  Exit 0
iff every obligation holds.
"""
import os
import pathlib
import random
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def any_match(value_matches):
    """Reference of model.py's `any_match`: the disjunction of per-entry value
    matches (post-patch semantics)."""
    return any(value_matches)


def model_prepatch(value_matches, is_path_object):
    """Reference of model_prepatch.py's buggy loop: an entry counts only when
    its value matches AND it is a plain string (raw object comparison)."""
    return any(v and not p for v, p in zip(value_matches, is_path_object))


# --- the per-entry abstraction computed from REAL Python values --------------

def abstract_entry(entry, app_dir):
    """Reduce a real configured entry (a str or a pathlib.Path) to the two
    model booleans, using the REAL path machinery."""
    value_matches = (str(entry) == app_dir)          # str(d) == app_dir
    is_path_object = isinstance(entry, pathlib.PurePath)
    return value_matches, is_path_object


def real_postpatch(app_dir, fixture_dirs):
    """The corrected real expression from the gold patch."""
    return app_dir in [str(d) for d in fixture_dirs]


def real_prepatch(app_dir, fixture_dirs):
    """The original buggy real expression."""
    return app_dir in fixture_dirs


# --- the checks --------------------------------------------------------------

def check_config(app_dir, fixture_dirs):
    value_matches = []
    is_path_object = []
    for entry in fixture_dirs:
        v, p = abstract_entry(entry, app_dir)
        value_matches.append(v)
        is_path_object.append(p)

    # R3: modelled post-patch == real corrected membership
    assert any_match(value_matches) == real_postpatch(app_dir, fixture_dirs), (
        "post-patch model disagrees with real membership on app_dir=%r dirs=%r"
        % (app_dir, fixture_dirs))
    # R3: modelled pre-patch == real buggy membership
    assert model_prepatch(value_matches, is_path_object) == \
        real_prepatch(app_dir, fixture_dirs), (
        "pre-patch model disagrees with real membership on app_dir=%r dirs=%r"
        % (app_dir, fixture_dirs))

    # R2: a Path equal-by-string is detected post-patch but missed pre-patch
    for entry, v, p in zip(fixture_dirs, value_matches, is_path_object):
        if isinstance(entry, pathlib.PurePath) and str(entry) == app_dir:
            assert v is True and p is True
            assert (entry == app_dir) is False, (
                "PurePath unexpectedly == str on %r" % (entry,))


def main():
    rng = random.Random(15987)

    # Path fragments to assemble realistic directory paths.
    parts = ["app", "fixtures", "data", "my-app", "x.y", "sub", "tests",
             "fixtures_1", "fixtures_2", ""]

    # --- the F2P scenario, explicitly: a single Path entry equal to the
    #     application's default fixtures directory ---------------------------
    cur = os.path.join("home", "proj", "tests", "fixtures_regress")
    app_dir = os.path.join(cur, "fixtures")
    f2p_dirs = [pathlib.Path(cur) / "fixtures"]   # Path(_cur_dir) / "fixtures"
    assert str(f2p_dirs[0]) == app_dir, (str(f2p_dirs[0]), app_dir)
    check_config(app_dir, f2p_dirs)
    # the discriminating fact the test asserts: detected only with the fix
    assert real_postpatch(app_dir, f2p_dirs) is True
    assert real_prepatch(app_dir, f2p_dirs) is False

    # --- boundary configurations ------------------------------------------
    boundary = [
        (app_dir, []),                                   # empty list
        (app_dir, [app_dir]),                            # plain-str match
        (app_dir, [pathlib.Path(app_dir)]),              # Path match
        (app_dir, ["unrelated"]),                        # plain-str no match
        (app_dir, [pathlib.Path("unrelated")]),          # Path no match
        (app_dir, [app_dir, pathlib.Path(app_dir)]),     # both kinds match
        (app_dir, ["unrelated", pathlib.Path(app_dir)]),  # only the Path matches
        (app_dir, [pathlib.PurePosixPath(app_dir)]),     # PurePath subclass
    ]
    for ad, dirs in boundary:
        check_config(ad, dirs)

    # --- randomized fuzz ---------------------------------------------------
    for _ in range(20000):
        depth = rng.randint(1, 4)
        app_dir = os.path.join(*[rng.choice(parts) for _ in range(depth)])
        n = rng.randint(0, 6)
        dirs = []
        for _ in range(n):
            d_depth = rng.randint(1, 4)
            s = os.path.join(*[rng.choice(parts) for _ in range(d_depth)])
            # occasionally force the entry to equal app_dir, as a str or a Path
            if rng.random() < 0.35:
                s = app_dir
            dirs.append(pathlib.Path(s) if rng.random() < 0.5 else s)
        check_config(app_dir, dirs)

    print("G-AX OK: per-entry abstraction (value_matches/is_path_object) and "
          "any_match fold validated against real os.path/pathlib on %d boundary "
          "+ 20000 fuzz configurations; post-patch model == "
          "`app_dir in [str(d) for d in dirs]`, pre-patch model == "
          "`app_dir in dirs`." % (len(boundary) + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
