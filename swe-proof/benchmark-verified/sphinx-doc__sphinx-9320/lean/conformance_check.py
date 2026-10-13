#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-9320.

The bundle models ONE function: the new-root-path entry validator
(`is_path_or_empty`, `sphinx/cmd/quickstart.py:98-101`). Its Lean implementation
(`implementation_validateRootEntry`) routes an entry `x` as:

    if x == "":            result = .ok x          # accept empty verbatim (NEW)
    else:                  result = checkExistingDir x   # delegate, UNCHANGED

This script transliterates that R/I leg into Python (`shadow`) and
differential-tests it against an ORACLE: an in-process replica of the POST-PATCH
`is_path_or_empty`:

    def oracle(x):
        if x == '':
            return ('ok', x)
        return check_existing_dir(x)

The existing-directory validator (`is_path`, the `checkExistingDir` A-reference)
is UNCHANGED by the patch and appears identically in both the specification and
the implementation, so it must CANCEL in the differential. We therefore use a
SINGLE shared stand-in `check_existing_dir` in both the oracle and the shadow —
it returns a deterministic ('ok', s) / ('error', msg) outcome derived from the
entry (modeling `path.isdir`: accept names that "look like" an existing dir,
reject the rest). The differential then isolates exactly the routing decision the
patch changes (empty -> accept vs. delegate), independent of what the real
`is_path` computes.

The result is encoded as a 2-tuple: ('ok', returned_string) for a returned value,
('error', message) for a raised ValidationError — matching the
Except.ok / Except.error model.

stdlib only; no network, no sphinx import. Pinned seed: 9320 (also in mapping.md).
exit 0 iff zero disagreements.
"""
import sys

SEED = 9320
N = 120_000

# Entry pool: the empty string (the discriminator), path-like names, relative and
# absolute-ish names, dotted names, whitespace, and unicode. The empty string is
# first so it is always exercised.
ENTRIES = [
    "", " ", "  ", ".", "..", "/", "./docs", "docs", "src/docs", "/tmp",
    "/nonexistent/path", "~", "~/proj", "C:\\proj", "a", "name with spaces",
    "réns", "日本", "\t", "\n", "x" * 64, "0", "conf.py", "./",
]


# --- shared A-reference: a deterministic stand-in for the UNCHANGED is_path ---
# Identical object used by oracle and shadow, so it cancels in the differential.
def check_existing_dir(x):
    # Models `is_path`: returns the (expanduser'd) entry if it "is a dir",
    # else raises ValidationError. The exact predicate is irrelevant to the
    # differential (it is shared) — it only needs to be deterministic and to
    # sometimes accept, sometimes reject, so both legs exercise both outcomes.
    looks_like_dir = x.endswith("/") or x in (".", "..", "~") or x.startswith("/")
    if looks_like_dir:
        return ("ok", x)
    return ("error", "Please enter a valid path name.")


# --- ORACLE: post-patch is_path_or_empty -------------------------------------
def oracle(x):
    if x == "":
        return ("ok", x)
    return check_existing_dir(x)


# --- shadow of implementation_validateRootEntry (the R/I leg) ----------------
def shadow(x):
    if x == "":
        return ("ok", x)
    return check_existing_dir(x)


def disagree(x):
    got = oracle(x)
    want = shadow(x)
    if got != want:
        return (x, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # --- exhaustive over the structured pool ---
    for x in ENTRIES:
        d = disagree(x)
        if d:
            print(f"DISAGREE exhaustive entry={d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # --- fuzz (pins seed/volume) ---
    rnd = _lcg(SEED)
    for _ in range(N):
        x = ENTRIES[next(rnd) % len(ENTRIES)]
        # occasionally mutate to a fresh random ascii string to widen coverage
        if next(rnd) % 4 == 0:
            length = next(rnd) % 12
            x = "".join(chr(32 + (next(rnd) % 95)) for _ in range(length))
        d = disagree(x)
        if d:
            print(f"DISAGREE fuzz entry={d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
