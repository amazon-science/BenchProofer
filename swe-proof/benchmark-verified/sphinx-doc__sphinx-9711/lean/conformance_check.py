#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-9711.

The bundle models ONE behavior: which (if any) of the configured minimum-version
requirements is the FIRST that a loaded extension fails to meet
(`verify_needs_extensions` in `sphinx/extension.py`). Its Lean implementation
(`implementation_verifyExtensionVersions`) iterates `(req, loaded?)` entries and
returns `some k` for the first unmet entry, else `none`.

This script transliterates that R/I impl into Python (`shadow`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH version-check block of `verify_needs_extensions` (the `fulfilled`
flag: `'unknown version'` ⇒ fail; else compare with `packaging.version.Version`,
falling back to string `>` on `InvalidVersion`; first failure raises). The raise
of `VersionRequirementError` for the k-th extension ↔ returning `some k`; no
raise ↔ `none`.

The version comparison is the A-reference leg (refinement.md ops 5/6): it is
left as the REAL repo callee `packaging.version.Version` in BOTH legs here (its
agreement with the Lean deep model `parseVersion`/`verGt`/`stringGt` is
validated separately by G-AX / axiom_check.py). So G-CONF tests the R/I
wiring — the loop, the first-unmet-index selection, the `unknown version`
sentinel, the not-loaded skip, and the fallback dispatch.

Every version string used below is ASCII, so every entry tested is admitted by
the spec's `problem_pre_verifyExtensionVersions`; the excluded class (non-ASCII
text) is out of scope here for the same reason it is out of scope in
axiom_check.py, and is documented there.

The discriminating case (the issue): req `"0.6"` vs loaded `"0.10"` is MET under
the numeric comparison (oracle returns no raise) — the pre-patch string compare
would have raised. Covered exhaustively and by fuzz.

stdlib-only except `packaging` (a real Sphinx dependency, imported by the gold
patch). Pinned seed: 9711 (also recorded in mapping.md).
"""
import sys

from packaging.version import InvalidVersion, Version

SEED = 9711
N = 200_000


# --- ORACLE: the post-patch version-check block, faithful in-process replica ----
def oracle(entries):
    """Replicate verify_needs_extensions's post-patch loop. `entries` is a list
    of (reqversion, loaded) where loaded is None (extension absent) or the
    extension's version string. Returns the 0-based index of the first entry
    that raises VersionRequirementError, or None if none does."""
    for idx, (reqversion, loaded) in enumerate(entries):
        if loaded is None:
            continue
        version = loaded
        fulfilled = True
        if version == 'unknown version':
            fulfilled = False
        else:
            try:
                if Version(reqversion) > Version(version):
                    fulfilled = False
            except InvalidVersion:
                if reqversion > version:
                    fulfilled = False
        if not fulfilled:
            return idx  # the raise point
    return None


# --- shadow of implementation_verifyExtensionVersions (R/I leg) -----------------
# Mirrors Solution.lean op-for-op; the A-reference comparison uses real Version.
def shadow(entries):
    idx = 0
    for (req, loaded) in entries:
        if loaded is None:
            pass
        else:
            ver = loaded
            fulfilled = True
            if ver == 'unknown version':
                fulfilled = False
            else:
                try:
                    if Version(req) > Version(ver):
                        fulfilled = False
                except InvalidVersion:
                    if req > ver:
                        fulfilled = False
            if not fulfilled:
                return idx
        idx = idx + 1
    return None


def disagree(entries):
    got = oracle(entries)
    want = shadow(entries)
    if got != want:
        return (list(entries), got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# representative version strings: numeric multi-component (the bug domain),
# the sentinel, and invalid (fallback) strings.
VER_POOL = ("0.6", "0.10", "0.6.0", "3.9", "3.10", "3.11", "1", "1.0",
            "1.0.0", "2", "10", "unknown version", "abc", "1.x", "v2", "")
REQ_POOL = VER_POOL


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over single-entry combos (req × loaded incl. absent)
    # — this directly covers the discriminating numeric-vs-string cases.
    for req in REQ_POOL:
        for loaded in (None,) + VER_POOL:
            entries = [(req, loaded)]
            d = disagree(entries)
            if d:
                print(f"DISAGREE single entry={d[0]}: oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
            checked += 1

    # Two-entry combos to exercise the first-unmet-index selection / ordering.
    for r1 in REQ_POOL[:8]:
        for l1 in (None,) + VER_POOL[:8]:
            for r2 in REQ_POOL[:4]:
                entries = [(r1, l1), (r2, "0.10")]
                d = disagree(entries)
                if d:
                    print(f"DISAGREE pair entry={d[0]}: oracle={d[1]} shadow={d[2]}")
                    print("status=fail")
                    return 1
                checked += 1

    # Random fuzz over variable-length entry lists.
    rnd = _lcg(SEED)
    for _ in range(N):
        n = next(rnd) % 5
        entries = []
        for _ in range(n):
            req = REQ_POOL[next(rnd) % len(REQ_POOL)]
            choice = next(rnd) % (len(VER_POOL) + 1)
            loaded = None if choice == len(VER_POOL) else VER_POOL[choice]
            entries.append((req, loaded))
        d = disagree(entries)
        if d:
            print(f"DISAGREE fuzz entry={d[0]}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
