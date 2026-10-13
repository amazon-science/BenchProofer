#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5840.

The changed function `_importconftest` keys its module cache by turning a path
into a *key object*. `Solution.lean` models this DEEPLY (no consumed axiom): the
`Key`/`KeyRepr` type encodes that the two ways of turning ONE filesystem location
into a key object —

    primary   = Path(str(p)).resolve()    # post-patch / consumer probe key
    secondary = unique_path(p)            # pre-patch cache key (py.path.local)

— are DISTINCT dictionary keys, even though they compare ``==`` equal as path
values. That single fact is the A-reference (mapping.md §3.1, refinement.md §A3).
This script validates it against the REAL path objects, in the eval container,
on boundary + fuzz paths (including the #5819 mixed-case scenario).

`unique_path` is reconstructed VERBATIM from the pre-patch `src/_pytest/pathlib.py`
(the very helper the gold patch deletes), so we exercise the real pre-patch key
builder. Imports only stdlib + `py` (the same `py.path.local` the repo uses).

Concretely we assert, for every constructed location `p`:
  (1) primary == secondary            (same location: they ARE equal as values)
  (2) primary in {primary: m}         (post-patch: a probe finds its own entry)
  (3) primary NOT in {secondary: m}   (pre-patch: a primary probe misses the
                                        secondary-keyed entry)  <-- the bug
and symmetrically `secondary not in {primary: m}` is not required by the spec
(consumers only ever probe with `primary`), but we record hash inequality which
is what makes (3) hold. Exit 0 iff every obligation holds on every path.

The model maps (1)+(2)+(3) onto:
  ⟨loc, primary⟩ ≠ ⟨loc, secondary⟩  and
  regLookup [(⟨loc,secondary⟩, m)] (probeKey loc) = none  and
  regLookup [(⟨loc,primary⟩,   m)] (probeKey loc) = some m
which is exactly what `regLookup`/`Key`-equality compute in Solution.lean.
"""
import os
import random
import sys
import tempfile
from os.path import normcase
from pathlib import Path

import py


# --- pre-patch key builder, reconstructed verbatim from src/_pytest/pathlib.py
def unique_path(path):
    """Returns a unique path in case-insensitive (but case-preserving) file
    systems such as Windows.

    This is needed only for ``py.path.local``; ``pathlib.Path`` handles this
    natively with ``resolve()``."""
    return type(path)(normcase(str(path.realpath())))


def primary_key(local_path):
    """post-patch / consumer key: Path(str(conftestpath)).resolve()."""
    return Path(str(local_path)).resolve()


def secondary_key(local_path):
    """pre-patch cache key: unique_path(conftestpath)."""
    return unique_path(local_path)


def check_location(local_path):
    """Validate the A-reference distinct-dict-key fact on one real location."""
    prim = primary_key(local_path)
    sec = secondary_key(local_path)

    # (1) same location: equal as path values (the subtle part — they ARE ==)
    assert prim == sec, (
        "A-reference unsound: primary %r != secondary %r as values for %s"
        % (prim, sec, local_path))

    # (2) post-patch: a primary probe finds an entry keyed under primary
    assert prim in {prim: "mod"}, (
        "A-reference unsound: primary key not found under itself for %s"
        % local_path)

    # (3) THE BUG / the discriminator: a primary probe MISSES an entry keyed
    #     under the secondary representation, because they hash differently.
    missed = prim not in {sec: "mod"}
    assert missed, (
        "A-reference unsound: primary probe %r unexpectedly HIT a "
        "secondary-keyed entry %r (same hash) for %s — the model's "
        "⟨loc,primary⟩ ≠ ⟨loc,secondary⟩ would be false here"
        % (prim, sec, local_path))

    # what makes (3) hold: distinct hashes despite value equality
    assert hash(prim) != hash(sec), (
        "A-reference fragile: equal hashes for %r / %r on %s (then (3) "
        "would be platform-luck, not the modeled key-object distinction)"
        % (prim, sec, local_path))


def main():
    rng = random.Random(5840)
    root = tempfile.mkdtemp(prefix="gax5840_")

    # --- boundary locations: the scenarios the issue + F2P tests exercise ----
    boundary_names = [
        "test/conftest.py",            # F2P param 'test'
        "tests/conftest.py",           # F2P param 'tests'
        "Foo/conftest.py",             # #5819 uppercase package dir
        "JenkinsRoot/test/conftest.py",  # #5792 mixed case
        "MixedCase/SubDir/conftest.py",
        "lower/only/conftest.py",      # already-lowercase: still distinct objects
        "UPPER/CONFTEST.py",
        "a/conftest.py",
        "conftest.py",
        "Dir With Spaces/conftest.py",
    ]
    locations = []
    for rel in boundary_names:
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").close()
        locations.append(py.path.local(full))

    for lp in locations:
        check_location(lp)

    # --- fuzz: randomized mixed-case directory trees -------------------------
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    n_fuzz = 3000
    for _ in range(n_fuzz):
        depth = rng.randint(1, 4)
        parts = []
        for _ in range(depth):
            k = rng.randint(1, 8)
            parts.append("".join(rng.choice(letters) for _ in range(k)))
        rel = os.path.join(*parts, "conftest.py")
        full = os.path.join(root, rel)
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w").close()
        except (OSError, FileExistsError):
            continue
        check_location(py.path.local(full))

    print("G-AX OK: Key/KeyRepr deep model sound — primary "
          "(Path.resolve) and secondary (unique_path) key objects denote the "
          "same location yet are distinct dict keys (== but hash-distinct) on "
          "%d boundary + %d fuzz locations; a primary probe misses a "
          "secondary-keyed entry, exactly as ⟨loc,primary⟩ ≠ ⟨loc,secondary⟩."
          % (len(boundary_names), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
