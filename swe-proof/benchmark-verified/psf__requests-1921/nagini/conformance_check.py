#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1921 (nagini).

SHADOW — the impl region of `model.py`'s `effective_collection` copied VERBATIM
         below (the model IS Python, so there is no transliteration step): only
         the contract statements (`Requires`/`Ensures`/`Invariant`/`Assert`) and
         the `# invariants-start`/`-end` markers were deleted; the loop, the
         `old_result` bookkeeping, and the two branch tests are byte-for-byte
         the model's. The `@Pure` helpers the region depends on (`absent`,
         `none_val`, `effective`, `combined`) copy over as plain functions with
         `@Pure` stripped. There is no `@ContractOnly` callee in this bundle
         (mapping.md §3: the combine-and-drop is modelled DEEPLY, A-reference
         only), so nothing is axiomatised away and nothing has to be stubbed;
         the whole modelled computation is under test here. No `PSeq`/`ToSeq`
         shim is needed — the carrier is `List[int]`.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
         `requests.sessions.merge_setting(request_setting, session_setting,
         dict_class=OrderedDict)` at `requests/sessions.py:34` (dict-merge
         branch, body lines 54-62; mapping.md §1). The gate git-applies the gold
         patch to /testbed before this script runs and sets PYTHONPATH, so the
         `merge_setting` imported here is the FIXED code, including the line the
         patch adds:

             merged_setting = dict((k, v) for (k, v) in merged_setting.items()
                                  if v is not None)

         Driving it needs no context beyond two mappings, so no transliteration
         is warranted (contrast the velvet sibling, which transliterates the
         Lean impl for its shadow but likewise CALLS the real `merge_setting`
         for its oracle). Consequently the real `to_key_val_list`
         (`requests/utils.py:144`) and `OrderedDict.update` used by the
         precedence merge are exercised too, so the R-refinements mapping.md §2
         claims about them are tested rather than assumed. We always pass two
         real dicts, so the early-return branches (`session_setting is None`,
         `request_setting is None`, non-Mapping bypass) are never taken: the
         dict-merge tail is the only branch the gold patch touches and the only
         branch the model models.

BRIDGE — mapping.md §2 inverted. Model side: the key universe is the index set
         `0 .. n-1`, position `k` holding the value for key `k`, with
         `absent()` == 0 meaning "this side does not carry key k" and
         `none_val()` == -1 meaning "key k is explicitly set to the unset
         value". Repo side: `to_repo` turns each list into an `OrderedDict`,
         OMITTING positions equal to `absent()` (key genuinely not in the dict)
         and storing the Python value `None` for `none_val()`; any other integer
         is stored as itself (identity on per-key value-identity). `from_repo`
         inverts it: a key missing from the merged dict reads back as
         `absent()`, a key still mapping to `None` reads back as `none_val()`
         (that is exactly the pre-patch bug shape, so it is reported as a
         disagreement rather than normalised away), any other value as itself.
         Result ordering is not modelled and not compared (mapping.md §2:
         `dict_class` ordering is unobserved by the behaviour under test); the
         per-key value mapping over `0 .. n-1` is.

INPUTS — every input satisfies the model's Requires (`0 <= n <= len(session)`,
         `n <= len(request)`; the permission conjuncts are vacuous outside
         Nagini). Because both the model and the real function decide each key
         INDEPENDENTLY of the others, the modelled decision space is the per-key
         class grid, and it is enumerated EXHAUSTIVELY: all (session, request)
         pairs of every length 0..4 over the 4-class value alphabet
         {absent, unset, real 1, real 7} — 1 + 16 + 256 + 4096 + 65536 = 69905
         inputs, so every reachable combination of the impl's two branch tests
         (`rv != absent()`, `ev == none_val()`) across up to four keys is
         covered, not sampled. That is a stronger check than 1e5 random samples
         over the same space, not a weaker one. On top of it: explicit boundary
         cases (empty; the exact F2P shape — a session-only key set to the unset
         value, which `test_headers_on_session_with_None_are_not_sent` pins and
         which the pre-patch per-request-only drop leaves in place; `n` strictly
         smaller than the list lengths, so positions outside the key universe
         are never read) and seeded fuzz over longer inputs (length <= 12, wider
         real-value alphabet, `n <= len`) to bring the total past 1e5.

Pinned seed: 1921 (recorded in mapping.md §G-CONF). Exit 0 iff zero
disagreements; on a disagreement the input and both outputs are printed and the
exit status is 1. stdlib + the `requests` package under evaluation only.
"""
import itertools
import random
import sys
from collections import OrderedDict
from typing import List  # noqa: F401  (used by the verbatim `# type:` comment)

from requests.sessions import merge_setting

SEED = 1921
N_FUZZ = 40_000
MAX_ENUM_LEN = 4
ENUM_ALPHABET = (0, -1, 1, 7)          # absent(), none_val(), two real values
FUZZ_ALPHABET = (0, -1, 1, 2, 7, 42, 99)
MAX_FUZZ_LEN = 12


# ---------------------------------------------------------------------------
# SHADOW: model.py's `pure` region, @Pure stripped, otherwise verbatim.
# ---------------------------------------------------------------------------
def absent():
    # The distinguished value meaning "key not carried by this collection" (an
    # input position) / "key dropped from the combined collection" (an output
    # position): a lookup finds the key absent.
    return 0


def none_val():
    # The distinguished explicit "unset" value a caller may store under a key.
    # A key whose effective value is this must be dropped from the result.
    return -1


def effective(sv, rv):
    # The effective value for a key before the unset-drop: the per-request value
    # wins where the per-request collection carries the key (rv != absent()),
    # otherwise the standing per-session value is used.
    if rv != absent():
        return rv
    return sv


def combined(sv, rv):
    # The value the combined collection holds for a key: the effective value,
    # except that an effective value equal to the unset value drops the key
    # (it becomes absent). This is the per-key behaviour the result must realise.
    if effective(sv, rv) == none_val():
        return absent()
    return effective(sv, rv)


# ---------------------------------------------------------------------------
# SHADOW: model.py's `effective_collection` impl region, contracts stripped.
# (Everything between `# impl-start` and `# impl-end`, minus Invariant/Assert.)
# ---------------------------------------------------------------------------
def effective_collection(session, request, n):
    result = []  # type: List[int]
    i = 0
    while i < n:
        sv = session[i]
        rv = request[i]
        # Precedence: the per-request value wins where the per-request
        # collection carries the key, else the per-session value.
        if rv != absent():
            ev = rv
        else:
            ev = sv
        # Drop the key (absent) when its effective value is the unset value,
        # regardless of which side contributed it; otherwise carry it through.
        if ev == none_val():
            val = absent()
        else:
            val = ev
        old_result = result
        result = result + [val]
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# BRIDGE (mapping.md §2, inverted).
# ---------------------------------------------------------------------------
def to_repo(session, request, n):
    """Model carrier -> the real repo types: two dicts over the key universe
    0..n-1. absent() means the key is simply not in that dict; none_val()
    becomes the Python value None; any other integer stays itself."""
    ses = OrderedDict()
    req = OrderedDict()
    for k in range(n):
        sv = session[k]
        rv = request[k]
        if sv != absent():
            ses[str(k)] = None if sv == none_val() else sv
        if rv != absent():
            req[str(k)] = None if rv == none_val() else rv
    return ses, req


def from_repo(merged, n):
    """The real merged mapping -> the model carrier: a length-n list of per-key
    values. A key missing from the result reads back as absent(); a key still
    mapping to None reads back as none_val() (the pre-patch bug shape, reported
    as a disagreement, never normalised away)."""
    out = [absent()] * n
    for key, v in merged.items():
        idx = int(key)
        out[idx] = none_val() if v is None else v
    return out


def oracle(session, request, n):
    """Call the REAL patched merge_setting. Note the argument order:
    merge_setting(request_setting, session_setting) -- the per-request side
    wins, matching the model's `effective`."""
    ses, req = to_repo(session, request, n)
    merged = merge_setting(req, ses, dict_class=OrderedDict)
    return from_repo(merged, n)


# ---------------------------------------------------------------------------
# Inputs: every triple satisfies the model's Requires 0 <= n <= len(session)
# and n <= len(request).
# ---------------------------------------------------------------------------
def boundary_inputs():
    A, U = absent(), none_val()
    return [
        ([], [], 0),                       # empty key universe
        ([U], [A], 1),                     # F2P shape: session-only unset -> drop
        ([A], [U], 1),                     # request-only unset -> drop
        ([U], [U], 1),                     # both unset -> drop
        ([5], [U], 1),                     # request unsets a real session value
        ([U], [5], 1),                     # request overrides an unset session value
        ([5], [A], 1),                     # session-only real value survives
        ([A], [5], 1),                     # request-only real value survives
        ([5], [7], 1),                     # both real -> request wins
        ([A], [A], 1),                     # neither side carries the key
        ([U, U, U], [A, A, A], 3),         # all session-side unset -> all dropped
        ([1, U, 3], [A, A, A], 3),
        ([U, 1], [1, U], 2),
        ([U, 1, 2], [A, U, 3], 0),         # n == 0 with non-empty lists
        ([U, 1, 2], [A, U, 3], 1),         # n < len: tail positions unread
        ([U, 1, 2, 9], [A, U, 3], 2),      # n < both lens, unequal lens
    ]


def enum_inputs():
    """Exhaustive: all (session, request) pairs of each length 0..MAX_ENUM_LEN
    over the 4-class value alphabet, with n == the length (the full key
    universe). Per-key independence makes this the whole modelled decision
    space up to that arity."""
    for length in range(MAX_ENUM_LEN + 1):
        for s in itertools.product(ENUM_ALPHABET, repeat=length):
            for r in itertools.product(ENUM_ALPHABET, repeat=length):
                yield (list(s), list(r), length)


def fuzz_inputs(count, rng):
    """Seeded fuzz over the same space, with longer inputs, a wider real-value
    alphabet, and n sometimes strictly below both list lengths."""
    for _ in range(count):
        n = rng.randint(0, MAX_FUZZ_LEN)
        slack_s = rng.randint(0, 3)
        slack_r = rng.randint(0, 3)
        s = [rng.choice(FUZZ_ALPHABET) for _ in range(n + slack_s)]
        r = [rng.choice(FUZZ_ALPHABET) for _ in range(n + slack_r)]
        yield (s, r, n)


def main():
    rng = random.Random(SEED)
    disagreements = []
    checked = 0
    n_boundary = 0
    n_enum = 0
    n_fuzz = 0

    streams = (("boundary", boundary_inputs()),
               ("exhaustive", enum_inputs()),
               ("fuzz", fuzz_inputs(N_FUZZ, rng)))

    for kind, stream in streams:
        for session, request, n in stream:
            # Requires guard: never feed the shadow an input outside its domain.
            assert 0 <= n <= len(session) and n <= len(request)
            checked += 1
            if kind == "boundary":
                n_boundary += 1
            elif kind == "exhaustive":
                n_enum += 1
            else:
                n_fuzz += 1
            shadow_out = effective_collection(session, request, n)
            try:
                real_out = oracle(session, request, n)
            except Exception as exc:              # noqa: BLE001
                disagreements.append((kind, session, request, n, shadow_out,
                                      "raised %r" % (exc,)))
                if len(disagreements) >= 5:
                    break
                continue
            if shadow_out != real_out:
                disagreements.append((kind, session, request, n, shadow_out,
                                      real_out))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for kind, session, request, n, sh, orc in disagreements:
            print("  [%s] session=%r request=%r n=%d\n    shadow=%r\n    oracle=%r"
                  % (kind, session, request, n, sh, orc))
        return 1

    print("G-CONF OK: model.py impl shadow (effective_collection, contracts "
          "stripped) agrees with the REAL patched "
          "requests.sessions.merge_setting on %d inputs "
          "(%d boundary + %d exhaustive length<=%d + %d fuzz, seed=%d), "
          "0 disagreements."
          % (checked, n_boundary, n_enum, MAX_ENUM_LEN, n_fuzz, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"boundary": %d, "exhaustive": %d, "fuzz": %d, '
          '"shadow": "direct (contract-stripped impl region of model.py)", '
          '"oracle": "called: requests.sessions.merge_setting (patched)"}'
          % (checked, SEED, n_boundary, n_enum, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
