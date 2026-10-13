#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-13439.

The bundle models ONE function: the post-patch `Pipeline.__len__`
(`sklearn/pipeline.py`). Its Lean implementation (`implementation_len`) reports
the size of a sequential composition observed through its ordered list of steps,
returning that count. The size is modeled in `Option Nat`: a defined size is
`some n`; the impl always produces `some (len steps)`.

    def __len__(self):
        return len(self.steps)

This script transliterates that R/I impl into Python (`shadow_len`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `Pipeline.__len__`, i.e. `len(self.steps)`.

We do NOT stand up scikit-learn's estimator machinery (heavy; the modeled value
is purely the length of the step list — `__len__` reads nothing else). Both legs
are total functions of the step-list length, so the edge set EXHAUSTIVELY covers
the boundary (empty list, singletons, and a dense run of lengths 0..256); the
fuzz loop additionally samples random step lists with varied names/components to
confirm the count never depends on a step's contents.

stdlib-only. Pinned seed: 13439 (also recorded in mapping.md).
"""
import sys

SEED = 13439
N = 120_000
MAX_LEN = 256


# --- ORACLE: the post-patch Pipeline.__len__, faithful in-process replica -----
def oracle_len(steps):
    # def __len__(self): return len(self.steps)
    return len(steps)


# --- shadow of implementation_len (the R/I leg) -------------------------------
# Mirrors Solution.lean op-for-op: result = some self.steps.length.
def shadow_len(steps):
    return len(steps)


def disagree(steps):
    got = oracle_len(steps)
    want = shadow_len(steps)
    if got != want:
        return (steps, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _mk_steps(n, rnd=None, names=None):
    out = []
    for i in range(n):
        if rnd is not None and names is not None:
            nm = names[next(rnd) % len(names)]
            comp = names[next(rnd) % len(names)]
        else:
            nm, comp = f"s{i}", f"c{i}"
        out.append((nm, comp))
    return out


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over the boundary: every length 0..MAX_LEN.
    for n in range(0, MAX_LEN + 1):
        steps = _mk_steps(n)
        d = disagree(steps)
        if d:
            print(f"DISAGREE boundary len={len(d[0])}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # Random fuzz: varied lengths AND varied step names/components — the count
    # must be independent of step contents.
    rnd = _lcg(SEED)
    names = ("anova", "svc", "Anova", "", "pca", "x" * 30, "name")
    for _ in range(N):
        n = next(rnd) % (MAX_LEN + 1)
        steps = _mk_steps(n, rnd, names)
        d = disagree(steps)
        if d:
            print(f"DISAGREE fuzz len={len(d[0])}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
