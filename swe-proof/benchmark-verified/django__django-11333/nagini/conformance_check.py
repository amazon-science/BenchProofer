#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11333 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers ``default_selector`` /
``resolve_selector`` copy over as plain functions. There are no @ContractOnly
callees and no PSeq usage, so no shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.urls.resolvers.get_resolver``. The gate applies patch.diff to
/testbed before this script runs.

Type bridge (mapping.md section 2):
  * ``urlconf`` (Optional[str]) <-> ``selector`` (Optional[int]): a per-trial
    bijection from urlconf strings to int tokens, with the trial's configured
    default urlconf mapped to 0 (== default_selector()) and ``None`` <-> ``None``.
  * routing-table object IDENTITY <-> int token: each distinct real object is
    assigned the ``fresh`` token of the call that first produced it; identity
    (``is``) on objects becomes equality on tokens.
  * the unbounded memo behind the lookup <-> the shadow ``Dict[int, int]``.
  * the entry-state scalars ``cached`` / ``existing`` / ``fresh`` are computed
    per call from the shadow cache's genuine entry state (so every generated
    call is Requires-satisfying by construction), with ``fresh`` drawn from a
    never-reused counter (hence ``existing != fresh`` always holds).

Per real call the shadow's returned token must equal the real returned
object's token, and the shadow cache size must equal the real memo's live
entry count (no eviction, one slot per resolved selector). Each trial resets
the real memo through the repo's own public cache-reset entry point and
asserts the reset actually empties the memo the lookup populates (the
companion change site of mapping.md section 1).

Input plan (>= 1e5 Requires-satisfying calls): boundary request sequences
(omitted-then-explicit-default and the reverse, repeats, multiple distinct
selectors, empty-string selector, long reuse chains) plus randomized fuzz
trials over small selector pools with omitted requests mixed in.
Pinned fuzz seed: 11333.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import itertools
import json
import random
import sys

SEED = 11333
N_FUZZ_TRIALS = 8000


# --- @Pure helpers from model.py, contracts stripped ---------------------------

def default_selector():
    return 0


def resolve_selector(selector):
    if selector is None:
        return default_selector()
    return selector


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def get_resolver_shadow(cache, selector, cached, existing, fresh):
    key = resolve_selector(selector)
    if key in cache:
        return cache[key]
    cache[key] = fresh
    return fresh


# --- one differential trial -----------------------------------------------------

def run_trial(env, root, requests):
    """Replay one request sequence against both the shadow and the real
    patched lookup, from an empty memo, with the default selector set to
    ``root``. Returns (n_calls, err) where err is None or a message."""
    settings, real_get_resolver, memo_info, reset = env
    reset()
    if memo_info().currsize != 0:
        return 0, ("RESET FAILURE: the public cache-reset entry point left "
                   "%d live entries in the memo the lookup populates"
                   % memo_info().currsize)
    settings.ROOT_URLCONF = root

    shadow_cache = {}
    sel_token = {root: 0}          # bridge: urlconf str -> selector token
    next_sel = itertools.count(1)
    obj_token = {}                 # bridge: id(real object) -> identity token
    refs = []                      # keep objects alive so ids stay unique
    fresh_counter = itertools.count(10 ** 6)

    n = 0
    for u in requests:
        if u is None:
            sel = None
        else:
            if u not in sel_token:
                sel_token[u] = next(next_sel)
            sel = sel_token[u]

        # entry-state scalars, computed from the shadow cache's genuine entry
        # state so the model's preconditions hold by construction
        key = resolve_selector(sel)
        cached = key in shadow_cache
        existing = shadow_cache[key] if cached else -1
        fresh = next(fresh_counter)

        shadow_res = get_resolver_shadow(shadow_cache, sel, cached, existing,
                                         fresh)

        real_obj = real_get_resolver() if u is None else real_get_resolver(u)
        refs.append(real_obj)
        oid = id(real_obj)
        if oid not in obj_token:
            # a never-seen object: by the bridge it carries this call's fresh
            # identity token
            obj_token[oid] = fresh
        real_res = obj_token[oid]
        n += 1

        if shadow_res != real_res:
            return n, (
                "DISAGREEMENT on request %r (selector token %r) in trial\n"
                "  root=%r requests=%r (call #%d)\n"
                "  shadow (impl region) returned token %r\n"
                "  real patched lookup returned the object with token %r\n"
                "  shadow cache: %r"
                % (u, sel, root, requests, n, shadow_res, real_res,
                   shadow_cache))

        real_size = memo_info().currsize
        if len(shadow_cache) != real_size:
            return n, (
                "MEMO-SIZE DISAGREEMENT after request %r in trial\n"
                "  root=%r requests=%r (call #%d)\n"
                "  shadow cache has %d slots: %r\n"
                "  real memo holds %d live entries"
                % (u, root, requests, n, len(shadow_cache), shadow_cache,
                   real_size))
    return n, None


# --- input generation ------------------------------------------------------------

ROOTS = ["pkg_a.routes", "pkg_b.routes", "top", "", "x.y.z.w"]
OTHERS = ["pkg_a.other", "alt.routes", "third.routes", "", "pkg_b.routes"]


def boundary_trials():
    """Explicit sequences stressing the omitted/explicit-default identity,
    slot distinctness, reuse chains, and the empty-string selector."""
    r, o, o2 = "pkg_a.routes", "alt.routes", "third.routes"
    seqs = [
        [None, r],                       # omitted, then explicit default
        [r, None],                       # explicit default, then omitted
        [None, None],
        [r, r],
        [None, o],
        [o, None],
        [None, r, o, None, r, o],
        [o, o2, None, r, o, o2, None],
        [o, None, r, None, o2, r, o],
        ["", None, r, ""],               # empty string is a valid selector
        [None] * 12,
        [r] * 12,
        [o, o, o2, o2, None, None, r, r],
        [None, r, None, r, None, r],
        [o2, o, r, None, r, o, o2],
    ]
    out = []
    for root in ROOTS:
        for seq in seqs:
            out.append((root, list(seq)))
    # the default selector equal to a pool selector (explicit root everywhere)
    out.append(("alt.routes", [None, "alt.routes", "pkg_a.routes", None]))
    out.append(("", [None, "", "alt.routes", None, ""]))
    return out


def fuzz_trials(rng):
    for _ in range(N_FUZZ_TRIALS):
        root = rng.choice(ROOTS)
        pool_size = rng.randint(1, 4)
        pool = rng.sample(OTHERS, pool_size) + [root]
        length = rng.randint(8, 20)
        requests = []
        for _ in range(length):
            if rng.random() < 0.35:
                requests.append(None)
            else:
                requests.append(rng.choice(pool))
        yield root, requests


# --- driver ------------------------------------------------------------------------

def main():
    from django.conf import settings
    if not settings.configured:
        settings.configure(ROOT_URLCONF="conf_check.initial")
    from django.urls.base import clear_url_caches
    from django.urls.resolvers import _get_cached_resolver, get_resolver

    env = (settings, get_resolver, _get_cached_resolver.cache_info,
           clear_url_caches)

    checked = 0
    n_trials = 0
    for root, requests in boundary_trials():
        n, err = run_trial(env, root, requests)
        checked += n
        n_trials += 1
        if err:
            print(err)
            return 1
    n_boundary = n_trials

    rng = random.Random(SEED)
    for root, requests in fuzz_trials(rng):
        n, err = run_trial(env, root, requests)
        checked += n
        n_trials += 1
        if err:
            print(err)
            return 1

    if checked < 100000:
        print("INPUT BUDGET NOT MET: only %d Requires-satisfying calls"
              % checked)
        return 1

    print("G-CONF OK: shadow impl == real patched lookup on %d "
          "Requires-satisfying calls across %d trials (%d boundary + %d "
          "fuzz, seed %d); result-token and memo-size agreement on every "
          "call; 0 disagreements."
          % (checked, n_trials, n_boundary, n_trials - n_boundary, SEED))
    print(json.dumps({"checked": checked, "trials": n_trials,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
