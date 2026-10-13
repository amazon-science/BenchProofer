#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23299 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/MustTerminate) stripped. The @Pure helpers of the pure
region (``key_resolved`` / ``key_other``) copy over unchanged — they are plain
integer constants. There is no @ContractOnly callee in this bundle (the impl
composes only dict primitives), so the shadow runs stand-alone.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``matplotlib.rc_context``, exercised as a genuine context manager
over the live module-global ``matplotlib.rcParams``. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH so the
import resolves to the patched module.

Type bridge (mapping.md section 2): the repo mapping is ``rcParams`` (string
key -> validated value); the model carrier is ``Dict[int, int]``.
  * key tokens: 0 <-> the distinguished key ``'backend'``; 1 <-> a
    representative ordinary key (``'lines.linewidth'``, float-validated);
    tokens 2.. <-> further float-validated ordinary keys, exercising the
    frame clause over pre-existing keys the body does not touch.
  * value tokens: for the distinguished key, n <-> the string
    ``'module://_sbu_tok_<n>'`` (accepted verbatim by the key's validator, so
    the mapping stores it unchanged — an exact bijection); for ordinary keys,
    n <-> ``float(n)`` (the float validator is the identity on numeric input
    up to the int->float embedding, exact for |n| < 2**53).

The body run inside the context is abstracted by the model to its writes on
the two observed keys (the ``new_resolved`` / ``other_override`` parameters);
the driver realises that body concretely in three ways the repo supports:
passing the overrides as the context's mapping argument, assigning inside the
context body, and assigning only the distinguished key (the ordinary key's
pre-exit value then being its entry value). After the context exits, the
post-state of every tracked key is read at the raw-dict level (bypassing the
resolving getter, which is downstream machinery outside the modeled
behaviour) and compared token-for-token against the shadow's post-state.

>= 1e5 Requires-satisfying inputs: enumerated boundary cases + 100000 fuzz
trials. Pinned fuzz seed: 23299 (the instance number; recorded in mapping.md).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 23299
N_FUZZ = 100000


# --- pure region of model.py, contracts stripped -------------------------------

def key_resolved():
    # The distinguished key whose body-set value must survive the context exit.
    return 0


def key_other():
    # A representative ordinary key whose body-set value is reverted on exit.
    return 1


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def restore_after_temporary_overrides(params,
                                      entry_resolved,
                                      entry_other,
                                      new_resolved,
                                      other_override):
    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
    # distinguished key from the snapshot. The net data flow — a snapshot that
    # excludes the distinguished key — is realised here by recording into the
    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
    # key, but NOT the distinguished key.
    saved = {}  # type: Dict[int, int]
    saved[key_other()] = params[key_other()]
    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
    params[key_resolved()] = new_resolved
    params[key_other()] = other_override
    # Restore (dict.update over the snapshot's keys): the snapshot covers only
    # the ordinary key, so only it is reverted; the distinguished key, absent
    # from the snapshot, keeps the body-set value.
    if key_other() in saved:
        params[key_other()] = saved[key_other()]


# --- bridge: Dict[int,int] tokens <-> real rcParams keys/values ----------------

# token -> real rc key name. Token 0 is the distinguished key; token 1 is the
# observed ordinary key; tokens 2.. are further float-validated pre-existing
# keys used to exercise the frame clause (untouched by the body, reverted by
# the real exit path, left alone by the shadow — same net effect).
KEY_NAMES = {
    0: "backend",
    1: "lines.linewidth",
    2: "lines.markersize",
    3: "hatch.linewidth",
    4: "font.size",
    5: "grid.linewidth",
    6: "axes.linewidth",
    7: "xtick.major.size",
    8: "ytick.major.size",
}
EXTRA_TOKENS = sorted(t for t in KEY_NAMES if t >= 2)

_BK_PREFIX = "module://_sbu_tok_"


def backend_of_token(n):
    # value-token bijection for the distinguished key: the validator accepts
    # this form verbatim, so the stored value round-trips exactly.
    return _BK_PREFIX + str(n)


def token_of_backend(v):
    if not isinstance(v, str) or not v.startswith(_BK_PREFIX):
        return ("<unbridgeable backend value %r>" % (v,))
    try:
        return int(v[len(_BK_PREFIX):])
    except ValueError:
        return ("<unbridgeable backend value %r>" % (v,))


def token_of_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ("<unbridgeable float value %r>" % (v,))
    if f != int(f):
        return ("<unbridgeable float value %r>" % (v,))
    return int(f)


# --- oracle: the real patched repo context manager -----------------------------

def get_oracle():
    import matplotlib
    return matplotlib


def raw_get(rcp, name):
    # Raw stored value: bypass the resolving getter (downstream machinery,
    # not part of the modeled mapping-state behaviour).
    return dict.__getitem__(rcp, name)


def run_real(mpl, entry_resolved, entry_other, new_resolved, other_override,
             extras, mode):
    """Set the tracked entry state on the live rcParams, run the real context
    manager with a body writing the observed keys per `mode`, and return the
    abstracted post-state Dict[int,int] over the tracked tokens (or an error
    string)."""
    rcp = mpl.rcParams
    # entry state, through the public validated path
    rcp[KEY_NAMES[0]] = backend_of_token(entry_resolved)
    rcp[KEY_NAMES[1]] = float(entry_other)
    for t, v in extras.items():
        rcp[KEY_NAMES[t]] = float(v)
    pre_keys = len(rcp)

    if mode == "rc_arg":
        # overrides passed as the context's mapping argument
        with mpl.rc_context(rc={KEY_NAMES[0]: backend_of_token(new_resolved),
                                KEY_NAMES[1]: float(other_override)}):
            pass
    elif mode == "assign":
        # overrides assigned inside the context body
        with mpl.rc_context():
            rcp[KEY_NAMES[0]] = backend_of_token(new_resolved)
            rcp[KEY_NAMES[1]] = float(other_override)
    elif mode == "distinguished_only":
        # body writes only the distinguished key; the ordinary key's pre-exit
        # value is then its entry value (other_override == entry_other)
        assert other_override == entry_other
        with mpl.rc_context():
            rcp[KEY_NAMES[0]] = backend_of_token(new_resolved)
    else:
        raise AssertionError("unknown mode %r" % (mode,))

    if len(rcp) != pre_keys:
        return "<key-set size changed across the context: %d -> %d>" % (
            pre_keys, len(rcp))

    post = {}
    tok = token_of_backend(raw_get(rcp, KEY_NAMES[0]))
    if isinstance(tok, str):
        return tok
    post[0] = tok
    for t in sorted(KEY_NAMES):
        if t == 0:
            continue
        if t == 1 or t in extras:
            tok = token_of_float(raw_get(rcp, KEY_NAMES[t]))
            if isinstance(tok, str):
                return tok
            post[t] = tok
    return post


# --- differential driver --------------------------------------------------------

def check(mpl, entry_resolved, entry_other, new_resolved, other_override,
          extras, mode):
    """Run shadow and oracle on one Requires-satisfying input; return an error
    string on disagreement, else None."""
    # shadow side: the abstract mapping, tracked tokens at entry values
    params = {key_resolved(): entry_resolved, key_other(): entry_other}
    params.update(extras)
    restore_after_temporary_overrides(params, entry_resolved, entry_other,
                                      new_resolved, other_override)
    # oracle side
    real_post = run_real(mpl, entry_resolved, entry_other, new_resolved,
                         other_override, extras, mode)
    if params != real_post:
        return ("DISAGREEMENT on input entry_resolved=%r entry_other=%r "
                "new_resolved=%r other_override=%r extras=%r mode=%r:\n"
                "  shadow (impl region)          = %r\n"
                "  real (patched repo rc_context) = %r"
                % (entry_resolved, entry_other, new_resolved, other_override,
                   extras, mode, params, real_post))
    return None


def boundary_cases():
    """Enumerated boundary inputs (all satisfy the precondition: both observed
    keys present with pinned entry values, distinct key tokens)."""
    cases = []
    vals = [0, 1, -1, 7, 23299]
    # small cross-product on the two-key core, both body realisations
    for er in vals[:3]:
        for eo in vals[:3]:
            for nr in vals[:3]:
                for oo in vals[:3]:
                    for mode in ("rc_arg", "assign"):
                        cases.append((er, eo, nr, oo, {}, mode))
    # body re-establishes the entry values (override == entry)
    cases.append((5, 6, 5, 6, {}, "rc_arg"))
    cases.append((5, 6, 5, 6, {}, "assign"))
    # body writes only the distinguished key
    for er, eo, nr in [(100, 5, 200), (0, 0, 0), (-3, 9, -3), (7, -2, 23299)]:
        cases.append((er, eo, nr, eo, {}, "distinguished_only"))
    # extra pre-existing ordinary keys the body never touches (frame clause)
    all_extras = {t: 10 * t + 1 for t in EXTRA_TOKENS}
    cases.append((100, 5, 200, 7, all_extras, "rc_arg"))
    cases.append((100, 5, 200, 7, all_extras, "assign"))
    cases.append((100, 5, 200, 5, all_extras, "distinguished_only"))
    cases.append((0, 0, 0, 0, {2: 0, 3: -1}, "assign"))
    # large-magnitude tokens (still exact under the int<->float embedding)
    big = 2 ** 40
    cases.append((big, -big, big - 1, -big + 1, {4: big}, "rc_arg"))
    cases.append((-big, big, -big, big, {}, "assign"))
    return cases


def main():
    mpl = get_oracle()

    checked = 0
    boundary = boundary_cases()
    for er, eo, nr, oo, extras, mode in boundary:
        err = check(mpl, er, eo, nr, oo, extras, mode)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over the bridged domain (pinned seed)
    rng = random.Random(SEED)
    modes = ("rc_arg", "assign", "distinguished_only")
    lo, hi = -10 ** 6, 10 ** 6
    for _ in range(N_FUZZ):
        er = rng.randint(lo, hi)
        eo = rng.randint(lo, hi)
        nr = rng.randint(lo, hi)
        mode = modes[rng.randrange(3)]
        oo = eo if mode == "distinguished_only" else rng.randint(lo, hi)
        extras = {}
        for t in rng.sample(EXTRA_TOKENS, rng.randint(0, 3)):
            extras[t] = rng.randint(lo, hi)
        err = check(mpl, er, eo, nr, oo, extras, mode)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched rc_context on %d inputs "
          "(%d boundary + %d fuzz, seed %d); distinguished key survives, "
          "ordinary keys reverted, key set unchanged; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
