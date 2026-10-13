"""properties.py — PBT falsification manifest for django__django-11333.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    get_resolver(cache: Dict[int,int], selector: Optional[int],
                 cached: bool, existing: int, fresh: int) -> int

i.e. the gold's "resolve the omitted urlconf to the default FIRST, then
memoize" routing-table lookup, collapsed into one contracted function. Its
defended surface (the load-bearing postcondition clauses):

  P1  Ensures(resolve_selector(selector) in cache)          # resolved slot present
  P2  Ensures(Result() == cache[resolve_selector(selector)])# return the slot's object
  P3  Ensures(Implies(cached,     Result() == existing))     # HIT reuses (memoization)
  P4  Ensures(Implies(not cached, Result() == fresh))        # MISS builds fresh
  P5  Ensures(Forall k != resolved: cache[k] == Old(cache[k]))    # distinctness
  P6  Ensures(Forall Old(k in cache): k in cache)            # cache only grows

and the precondition facts that anchor the memoization clause on the GENUINE
entry state (the django-12713 pattern, refinement.md §E):

  R1  Requires(dict_pred(cache))                             # FULL perm: cache is mutated
  R2  Requires(cached == (resolve_selector(selector) in cache))
  R3  Requires(Implies(cached, cache[resolve_selector(selector)] == existing))
  R4  Requires(Implies(cached, existing != fresh))

WHAT THIS SPEC DEFENDS, and the attacks it must survive:

  * The oracle is GROUNDED, not an answer-key. The output pin P2/P3/P4 is a
    function of the inputs: `resolve_selector` is a @Pure helper fully unfolded
    (`default_selector() if None else selector`), and the HIT/MISS object
    identity is pinned to the pre-state scalars `existing`/`fresh` fixed by the
    preconditions. There is NO opaque @ContractOnly marker to echo — no
    "return materialize(oracle(x))" shortcut exists. So the ungrounded-oracle
    echo class does NOT apply; instead the cheapest honest impl is included as a
    positive control (pos-control-merge-tail / pos-control-tmp-local).

  * The cache is held at FULL permission (R1 `dict_pred(cache)`, not
    `Acc(.,1/2)`) and is GENUINELY MUTATED by the gold (a slot is added on a
    miss). There is therefore NO read-only `Acc(x,1/2)` input to subvert: the
    mandatory FRAME-MUTATION class (overwrite a read-only input to satisfy the
    postcondition vacuously) does NOT apply to this instance — writing `cache`
    is the intended behaviour, not a vacuity exploit, and the OTHER scalars
    (selector/cached/existing/fresh) are pass-by-value immutables with no
    permission to subvert. The analogue here — over-CONSTRUCTING into an
    occupied slot to dodge memoization — IS attacked (adv-overwrite-on-hit),
    but it is rejected by P3 (the value clause), not by the permission system.

  * The change the gold makes (resolve BEFORE keying the memo) is sensed by P1:
    keying on the RAW argument leaves the resolved-default slot unpopulated.
    adv-raw-key reproduces model_prepatch.py and must be rejected by P1.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
GUARANTEED and a rejection comes from the POSTCONDITION (or precondition)
catching wrong behaviour, never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P. AXIOM_TESTS is empty: the bundle has NO @ContractOnly axiom and
NO A-reference deep model (meta.axioms == [], deep_model_references == []); the
lru_cache memo is modeled deeply as a Dict lookup-or-insert and the URLResolver
construction is abstracted as a fresh-token allocation (its contents are
unobserved by the F2P assertIs/assertIsNot). Nothing to falsify against a real
callee (G-AX is vacuous; axiom_check.py validates the two modeling assumptions
against the REAL functools.lru_cache out-of-band).
"""
from pathlib import Path

INSTANCE = "django__django-11333"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The whole gold impl body, between the markers (exclusive). Used as a single
# replaceable block; strictly INSIDE the impl region.
# ---------------------------------------------------------------------------
_GOLD_BODY = (
    "    key = resolve_selector(selector)\n"
    "    if key in cache:\n"
    "        return cache[key]\n"
    "    cache[key] = fresh\n"
    "    return fresh\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S1) Structurally-different but CORRECT: a single-return reshape. Compute the
# resolved key, populate the slot ONLY on a miss, then read the slot for BOTH
# branches (`return cache[key]`). Semantically identical to gold, different
# control shape (one return point, `not in` guard). On a HIT, cache[key]==existing
# (R3) so P3 holds; on a MISS the freshly-inserted slot holds `fresh` so P4 holds;
# P1/P2 hold because `key in cache` after either branch. Keeps every gold proof
# obligation it needs (no framing lemma is required: the only written key is the
# resolved one). If this fails to verify, the postcondition is over-fit to the
# two-return inline form => SPEC-TOO-STRONG.
_POS_MERGE_TAIL = _swap(_BASE, _GOLD_BODY,
    "    key = resolve_selector(selector)\n"
    "    if key not in cache:\n"
    "        cache[key] = fresh\n"
    "    return cache[key]\n"
)

# (S2) Structurally-different but CORRECT: same two-branch control flow, but the
# returned value is staged through typed LOCALS rather than returned inline
# (a local-variable reshape). Identical behaviour; confirms the spec admits a
# different local-binding shape, not just the gold spelling. If it fails to
# verify => SPEC-TOO-STRONG (over-fit to the inline-return form).
_POS_TMP_LOCAL = _swap(_BASE, _GOLD_BODY,
    "    key = resolve_selector(selector)\n"
    "    if key in cache:\n"
    "        hit = cache[key]  # type: int\n"
    "        return hit\n"
    "    cache[key] = fresh\n"
    "    miss = fresh  # type: int\n"
    "    return miss\n"
)

# (S3 / ADMISSIBILITY) A self-call on an F2P-shaped input — the omitted selector
# against an EMPTY cache (the very first get_resolver() before anything is
# cached). The fresh `{}` establishes full dict_pred; the precondition facts hold
# by construction: cached == (resolve_selector(None) in {}) == (0 in {}) == False;
# R3/R4 are vacuous (cached False). The discarded result is the freshly-built
# token. If this self-call cannot establish the Requires for a normal omitted-
# selector input => PRECOND-TOO-STRONG. The gold body then runs unchanged on the
# real `cache`, so the function is still correct.
_ADMISS = _swap(_BASE, _GOLD_BODY,
    "    probe_cache = {}  # type: Dict[int, int]\n"
    "    Assert(dict_pred(probe_cache))\n"
    "    Assert(False == (resolve_selector(None) in probe_cache))\n"
    "    Assert(Implies(False, probe_cache[resolve_selector(None)] == 0))\n"
    "    Assert(Implies(False, 0 != 1))\n"
    "    key = resolve_selector(selector)\n"
    "    if key in cache:\n"
    "        return cache[key]\n"
    "    cache[key] = fresh\n"
    "    return fresh\n"
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) OVER-CONSTRUCT / control-flow-effect — the django-12713 pattern the spec
# was specifically hardened against (refinement.md §E). On a HIT it does NOT reuse
# the cached object; it overwrites the resolved slot with a freshly-built `fresh`
# and returns it. Under the abstraction this is "rebuild the URLResolver on every
# call" — exactly the wasteful double-construction the optimization removes.
# Rejection source: P3 `Implies(cached, Result() == existing)`, gated on the
# pre-state scalar `cached`/`existing` (which the overwrite cannot perturb,
# because R4 fixes existing != fresh) — so Result()==fresh != existing.
_RIVAL_OVERWRITE = _swap(_BASE, _GOLD_BODY,
    "    key = resolve_selector(selector)\n"
    "    cache[key] = fresh\n"
    "    return fresh\n"
)

# (U2) RAW-KEY / partial-domain — the exact pre-gold bug (model_prepatch.py). Keys
# the memo on the RAW argument (an omitted selector lands in a separate -1
# "no-argument" slot, NOT the default selector's slot), so the resolved-default
# slot is never populated when the selector is omitted. Its faithful real patch
# is the pre-patch get_resolver (the @lru_cache on the raw arg) — which FAILS the
# F2P assertIs (get_resolver() builds a second URLResolver instead of reusing the
# one cached for ROOT_URLCONF), so it would NOT resolve. Rejection source: P1
# `resolve_selector(selector) in cache` (when selector is None, resolved == 0 is
# never inserted), hence also P2.
_RIVAL_RAW_KEY = _swap(_BASE, _GOLD_BODY,
    "    if selector is None:\n"
    "        raw = -1\n"
    "    else:\n"
    "        raw = selector\n"
    "    if raw in cache:\n"
    "        return cache[raw]\n"
    "    cache[raw] = fresh\n"
    "    return fresh\n"
)

# (U3) WRONG MISS VALUE / partial-domain — handles a HIT exactly like gold but on
# a MISS returns `existing` (the unconstrained 'already-cached object' scalar)
# instead of the freshly-built `fresh`. A faithful real patch of this shape would,
# on a cache miss, hand back some unrelated/stale object instead of the
# newly-constructed URLResolver — the returned object is not even the one stored,
# so a subsequent identical call returns a DIFFERENT object and the F2P assertIs
# breaks. Rejection source: P4 `Implies(not cached, Result() == fresh)` (on a
# miss `existing` is not pinned to `fresh`), and P2 (the returned `existing` need
# not be the cache's resolved-slot value).
_RIVAL_MISS_EXISTING = _swap(_BASE, _GOLD_BODY,
    "    key = resolve_selector(selector)\n"
    "    if key in cache:\n"
    "        return cache[key]\n"
    "    cache[key] = fresh\n"
    "    return existing\n"
)

# (U4) CORRUPT-OTHER-KEY / value-level distinctness — on a miss it inserts the
# resolved slot correctly AND clobbers a neighbouring slot (key+1) with `fresh`.
# A faithful real patch of this shape would, on building one resolver, stomp the
# cached resolver for a DIFFERENT urlconf — so the later get_resolver(other) hands
# back the wrong (overwritten) object and the F2P assertIsNot/identity contract
# breaks. Rejection source: P5 the distinctness Forall
# `k != resolved ⇒ cache[k] == Old(cache[k])`: the verifier cannot rule out that
# key+1 was already present with a different value, so the clause fails for
# k == key+1.
_RIVAL_CORRUPT_OTHER = _swap(_BASE, _GOLD_BODY,
    "    key = resolve_selector(selector)\n"
    "    if key in cache:\n"
    "        return cache[key]\n"
    "    cache[key] = fresh\n"
    "    cache[key + 1] = fresh\n"
    "    return fresh\n"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-merge-tail", "kind": "soundness", "expect": "verify",
     "module": _POS_MERGE_TAIL,
     "rationale": "structurally-different but CORRECT single-return reshape "
                  "(populate-on-miss then `return cache[key]` for both branches). "
                  "P3 holds via R3 on a hit, P4 via the just-inserted slot on a miss; "
                  "no framing lemma needed (only the resolved key is written). If it "
                  "fails to verify => SPEC-TOO-STRONG (over-fit to the two-return form)."},
    {"id": "pos-control-tmp-local", "kind": "soundness", "expect": "verify",
     "module": _POS_TMP_LOCAL,
     "rationale": "a correct impl that stages the return value through typed locals "
                  "(local-variable reshape, same two-branch flow) must verify; if not, "
                  "the spec is over-fit to the inline-return spelling => SPEC-TOO-STRONG. "
                  "Doubles as the cheapest-honest control: the spec is GROUNDED (no @Pure "
                  "answer-key to echo), so this honest impl IS the cheapest verifier."},
    {"id": "admiss-omitted-empty-cache", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the F2P-shaped omitted-selector-against-empty-cache "
                  "input establishes the precondition (dict_pred on a fresh {}; "
                  "cached==(0 in {})==False; R3/R4 vacuous). If the Requires cannot be "
                  "established for this normal first-call input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-overwrite-on-hit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERWRITE,
     "refinement": "this is the over-construct (django-12713) pattern: rebuild and "
                   "re-store the URLResolver on EVERY call, never reusing the memoized "
                   "object. Its faithful real patch defeats the whole optimization — "
                   "get_resolver() and get_resolver('...path_urls') each construct a new "
                   "URLResolver per call, so assertIs(get_resolver(), "
                   "get_resolver('...path_urls')) compares two freshly-built distinct "
                   "objects and FAILS — it would NOT resolve.",
     "rationale": "Rejection source: P3 Implies(cached, Result()==existing). On a HIT, "
                  "Result()==fresh which R4 fixes != existing. Memoization is gated on the "
                  "pre-state scalar `cached`/`existing` (not a query against the mutated "
                  "cache), so the overwrite cannot dodge it. If it verified => "
                  "SPEC-TOO-WEAK (the django-12713 unsoundness this spec was hardened "
                  "against, refinement.md §E)."},
    {"id": "rival-raw-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RAW_KEY,
     "refinement": "keys the memo on the RAW argument (omitted selector -> a separate -1 "
                   "slot), exactly model_prepatch.py / the pre-gold @lru_cache-on-get_resolver. "
                   "Its faithful real patch is the pre-patch code that memoizes on the raw "
                   "urlconf, so get_resolver() (None) and get_resolver('...path_urls') land "
                   "in different memo slots and build two URLResolvers — FAILING the F2P "
                   "assertIs. It would NOT resolve.",
     "rationale": "Rejection source: P1 resolve_selector(selector) in cache — when the "
                  "selector is omitted the resolved key (0) is never inserted (only -1 is), "
                  "so P1 (and hence P2) fail. This is the exact clause G-DIFF reports "
                  "model_prepatch failing. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-miss-returns-existing", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MISS_EXISTING,
     "refinement": "on a cache MISS returns the unconstrained `existing` object instead of "
                   "the freshly-built one. A faithful real patch of this shape hands back a "
                   "stale/unrelated resolver on a miss and does not return the object it "
                   "stored, so a repeated call returns a different object — the F2P assertIs "
                   "(same object on repeat) breaks. It would NOT resolve.",
     "rationale": "Rejection source: P4 Implies(not cached, Result()==fresh) — on a miss "
                  "`cached` is False so Result() must equal `fresh`, but it returns "
                  "`existing` (unpinned to fresh; R4 only constrains existing when cached). "
                  "Also P2: `existing` need not equal cache[resolved]. If it verified => "
                  "SPEC-TOO-WEAK (partial-domain: only the hit sub-domain pinned)."},
    {"id": "rival-corrupt-other-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CORRUPT_OTHER,
     "refinement": "on a miss it stores the resolved slot correctly but also clobbers a "
                   "neighbouring slot (key+1) with the same fresh token. A faithful real "
                   "patch of this shape corrupts the cached resolver for a DIFFERENT urlconf, "
                   "so a later get_resolver(other) returns the wrong (overwritten) object — "
                   "breaking the identity contract / assertIsNot. It would NOT resolve.",
     "rationale": "Rejection source: P5 the distinctness Forall "
                  "k != resolved ⇒ cache[k]==Old(cache[k]). The verifier cannot rule out "
                  "that key+1 was already cached with a different value, so the clause fails "
                  "for k==key+1. If it verified => SPEC-TOO-WEAK (distinctness hollow)."},
]

# ===========================================================================
# AXIOM LANE — none.
# ===========================================================================
# meta.json: axioms == [] and deep_model_references == []. There is no
# @ContractOnly axiom and no A-reference deep model standing in for a real
# library callee. The functools.lru_cache(maxsize=None) memo is modeled DEEPLY as
# a Dict lookup-or-insert in the impl region, and the URLResolver construction is
# abstracted as a fresh-token allocation (its contents are unobserved by the F2P).
# Hence there is nothing to falsify against a real callee (G-AX is vacuous). The
# out-of-band axiom_check.py already validates, against the REAL
# functools.lru_cache, the two modeling assumptions the refinement leans on
# (memo identity + no eviction; resolve-then-memoize shares one object vs
# memoize-then-resolve does not).
AXIOM_TESTS = []
