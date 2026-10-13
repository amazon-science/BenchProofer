#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5840 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The single @ContractOnly impl callee `make_key(loc, True)`
(the deduplication-key constructor under the recognised convention) is
realized by the REAL repo constructor per mapping.md section 3.1 —
`Path(str(conftestpath)).resolve()` — with the produced key's location string
re-encoded as the model's List[int] carrier. (`canonical` is the same
constructor's string view, per mapping.md section 3.2: both conventions carry
the identical canonical string, so the recognised constructor realizes both.)

ORACLE: the REAL patched repo function per mapping.md section 1 — the
dedup-key computation inside `PytestPluginManager._importconftest`
(src/_pytest/config/__init__.py), driven on real conftest files. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
resolves the patched package (the script also prepends /testbed/src, the
package's source root in this repo layout).

Type bridge (mapping.md section 2): a location string maps to List[int] of
code points (ord per char). The shadow's output key is a location-string
carrier PLUS the abstract recognition token; the real observables it maps to
are (i) the string of the key under which `_importconftest` cached the module
and (ii) the membership-recognition effect — an INDEPENDENTLY-recomputed key
for the shadow's canonical string must be found by the real cache's
membership test and must map to the very module object the call returned
(the token's real meaning: recomputed-lookup HIT). A second request through
any variant spelling of the same physical file must reuse the cached entry
(same module object, no new cache entry).

Input domain: Requires demands only a read-only location list; the real
callee's operating domain is a location naming an existing conftest file
(callers guard with an existence check before invoking it), so inputs are
generated as real conftest files in a scratch tree: 400 physical files across
nested dirs (some under package dirs with __init__.py), plus symlinked
directory aliases and symlinked file aliases, then >=1e5 lookups through
variant spellings (direct, via dir-symlink, via file-symlink, with redundant
self-collapsing infix segments). Boundary cases cover the first-import path,
the repeat-import path, symlink chains, and package-dir conftests.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz lookups.
Pinned fuzz seed: 5840.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + py (the repo's own path library) only.
"""
import json
import os
import random
import shutil
import sys
from pathlib import Path

SEED = 5840
N_FUZZ = 100_000
N_FILES = 400


def _codes(s):
    return [ord(c) for c in s]


def _str(codes):
    return "".join(chr(c) for c in codes)


# --- @ContractOnly callee bridged to the REAL recognised-key constructor ------

def make_key(loc, recognised_convention):
    assert recognised_convention is True  # the impl region only uses True
    key_obj = Path(_str(loc)).resolve()   # REAL constructor (recognised)
    return _codes(str(key_obj))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def conftest_dedup_key(loc):
    # Build the deduplication key under the recognised convention, so an
    # independently-recomputed key for the same location finds the stored entry.
    result = make_key(loc, True)
    return result


def main():
    sys.path.insert(0, "/testbed/src")
    import py
    from _pytest.config import PytestPluginManager

    root = "/tmp/conf_pool_5840"
    links = os.path.join(root, "links")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(links)

    rng = random.Random(SEED)
    pm = PytestPluginManager()

    # --- build the physical scratch tree ---------------------------------------
    files = []          # absolute str paths of physical conftest files
    dir_alias = {}      # physical dir -> list of symlink alias dirs
    file_alias = {}     # physical file -> list of symlink alias files
    n_links = 0
    for i in range(N_FILES):
        depth = rng.randint(1, 3)
        d = os.path.join(root, *("lvl%d_%d" % (j, i) for j in range(depth)))
        os.makedirs(d)
        if i % 7 == 0:
            # a package dir (module import goes through the package path)
            with open(os.path.join(d, "__init__.py"), "w") as fh:
                fh.write("")
        fpath = os.path.join(d, "conftest.py")
        with open(fpath, "w") as fh:
            fh.write("value = %d\n" % i)
        files.append(fpath)
        aliases = []
        for a in range(rng.randint(0, 2)):
            alias = os.path.join(links, "dl_%d_%d" % (i, a))
            os.symlink(d, alias)
            aliases.append(alias)
            n_links += 1
        dir_alias[fpath] = aliases
        faliases = []
        if i % 5 == 0:
            fl = os.path.join(links, "fl_%d.py" % i)
            os.symlink(fpath, fl)
            faliases.append(fl)
            n_links += 1
            if i % 10 == 0:
                fl2 = os.path.join(links, "fl2_%d.py" % i)
                os.symlink(fl, fl2)  # symlink chain
                faliases.append(fl2)
                n_links += 1
        file_alias[fpath] = faliases

    checked = [0]
    canonical_mod = {}  # canonical str -> module returned on first import

    def check_lookup(loc_str, phys):
        """One input: the location `loc_str` (a spelling of physical file
        `phys`). Diff the shadow key against the real cached-key observables."""
        loc = _codes(loc_str)
        shadow_key = conftest_dedup_key(loc)
        shadow_str = _str(shadow_key)

        before = len(pm._conftestpath2mod)
        mod = pm._importconftest(py.path.local(loc_str))
        after = len(pm._conftestpath2mod)

        first = shadow_str not in canonical_mod
        if first:
            canonical_mod[shadow_str] = mod
            if after != before + 1:
                return ("DISAGREEMENT loc=%r\n  first request for canonical "
                        "%r changed cache size %d -> %d (expected one new "
                        "entry)" % (loc_str, shadow_str, before, after))
        else:
            if mod is not canonical_mod[shadow_str]:
                return ("DISAGREEMENT loc=%r\n  repeat request for canonical "
                        "%r returned a DIFFERENT module (cache not reused)"
                        % (loc_str, shadow_str))
            if after != before:
                return ("DISAGREEMENT loc=%r\n  repeat request for canonical "
                        "%r grew the cache %d -> %d (shadow key predicts a "
                        "hit)" % (loc_str, shadow_str, before, after))

        # Recognition effect: an INDEPENDENTLY-recomputed key for the shadow's
        # canonical string must be found by the real membership test and map
        # to the returned module.
        recomputed = Path(shadow_str)
        if recomputed not in pm._conftestpath2mod:
            return ("DISAGREEMENT loc=%r\n  shadow key %r holds the "
                    "recognition token but the real cache membership test "
                    "MISSES the recomputed key" % (loc_str, shadow_str))
        if pm._conftestpath2mod[recomputed] is not mod:
            return ("DISAGREEMENT loc=%r\n  recomputed key %r maps to a "
                    "different module than the call returned"
                    % (loc_str, shadow_str))
        # String view: the canonical string names the physical file.
        if shadow_str != str(Path(phys).resolve()):
            return ("DISAGREEMENT loc=%r\n  shadow canonical %r != physical "
                    "resolution %r" % (loc_str, shadow_str,
                                       str(Path(phys).resolve())))
        checked[0] += 1
        return None

    def run(loc_str, phys):
        err = check_lookup(loc_str, phys)
        if err:
            print(err)
            sys.exit(1)

    def spellings(phys):
        """Variant spellings of one physical conftest file."""
        out = [phys]
        d = os.path.dirname(phys)
        base = os.path.basename(d)
        # redundant self-collapsing infix (lexically collapsed by the path
        # object at construction; same location)
        out.append(os.path.join(d, "..", base, "conftest.py"))
        out.append(os.path.join(d, ".", "conftest.py"))
        for alias in dir_alias[phys]:
            out.append(os.path.join(alias, "conftest.py"))
        out.extend(file_alias[phys])
        return out

    # --- boundary: first import + every variant spelling once ------------------
    n_boundary = 0
    for phys in files:
        for s in spellings(phys):
            run(s, phys)
            n_boundary += 1

    # --- fuzz: randomized repeat lookups through random spellings --------------
    for _ in range(N_FUZZ):
        phys = files[rng.randrange(len(files))]
        opts = spellings(phys)
        run(opts[rng.randrange(len(opts))], phys)

    shutil.rmtree(root, ignore_errors=True)
    print("G-CONF OK: shadow dedup key == real conftest cache key on %d "
          "inputs (%d boundary + %d fuzz over %d physical files / %d "
          "symlinks, seed %d)."
          % (checked[0], n_boundary, N_FUZZ, N_FILES, n_links, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
