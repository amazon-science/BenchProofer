"""PBT manifest for django__django-15814 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  related_reported_fields(canonical: Dict[int,int], attr_owner: Dict[int,int],
                          primary: int, primary_pk: int, ref_attr: int,
                          related: int, related_pk: int, chosen_attr: int)
                          -> Dict[int, Dict[int, int]]

    Requires:
      Acc(dict_pred(canonical), 1/2)            -- canonical is READ-ONLY (1/2)
      Acc(dict_pred(attr_owner), 1/2)           -- attr_owner is READ-ONLY (1/2)
      related_pk != chosen_attr                 -- pk and chosen attr distinct
      canonical_of(canonical, canonical_of(canonical, related))
          == canonical_of(canonical, related)   -- idempotence at the related
      canonical_of(canonical, canonical_of(canonical, primary))
          == canonical_of(canonical, primary)   -- idempotence at the primary
      canonical_of(canonical, primary) != canonical_of(canonical, related)
                                                -- separate storage identities
      chosen_attr in attr_owner
      and canonical_of(canonical, attr_owner[chosen_attr])
          == canonical_of(canonical, related)   -- the chosen attribute is one
                                                   the related model's own
                                                   storage holds (stated on the
                                                   declaring model's STORAGE
                                                   identity, so the declaring
                                                   token is not itself pinned to
                                                   canonical_of(related))
    Ensures (frame):
      Acc(dict_pred(canonical), 1/2)            -- the 1/2 perms are returned
      Acc(dict_pred(attr_owner), 1/2)              (neither map is written)
    Ensures (permission):
      Acc(dict_pred(Result()))
      Acc(dict_pred(Result()[rk]))  where rk = canonical_of(canonical, related)
      Acc(dict_pred(Result()[pk]))  where pk = canonical_of(canonical, primary)
    Ensures (PRESENCE / canonical keying, load-bearing):
      rk in Result()  AND  pk in Result()
      chosen_attr in Result()[rk]  AND  Result()[rk][chosen_attr] == chosen_attr
      related_pk  in Result()[rk]  AND  Result()[rk][related_pk]  == related_pk
      primary_pk  in Result()[pk]  AND  Result()[pk][primary_pk]  == primary_pk
      ref_attr    in Result()[pk]  AND  Result()[pk][ref_attr]    == ref_attr
    Ensures (CLOSURE, per bucket):
      Forall a:int :: a in Result()[rk] ==> a == related_pk or a == chosen_attr
      Forall a:int :: a in Result()[pk] ==> a == primary_pk or a == ref_attr
    Ensures (ANTI-SCATTER / provenance, per participant):
      related != rk ==> not (related in Result())
      primary != pk ==> not (primary in Result())

  canonical_of(canonical, m) = canonical[m] if m in canonical else m   (@Pure)

This models the behaviour the loader must have when an optimized query pulls a
related object alongside the primary one and keeps one chosen attribute of the
related object: the reported per-model mapping is consumed WHOLE downstream, so
BOTH participating buckets are pinned -- the related model's canonical bucket
(its own primary key + the chosen attribute, nothing else) and the primary
model's canonical bucket (its own primary key + the reference attribute the
related object is reached through, nothing else) -- and each primary key must be
accumulated under its model's CANONICAL identity rather than under a raw alias
identity. When the passthrough primary key is keyed by a raw alias identity it
is missing from the concrete reported bucket the identification step reads,
raising `ValueError: 'id' is not in list` in RelatedPopulator.__init__; when the
primary model's bucket loses its own primary key or the reference attribute, the
relation can no longer be both restricted and traversed.

GROUNDED-ORACLE NOTE: the postcondition's only "oracle" is canonical_of, a @Pure
map application GROUNDED entirely in the argument `canonical` (canonical[m] with
an m-itself fallback). It is not an opaque answer-key: there is no WRONG value a
rival could echo and still verify, because the whole keying/closure/anti-scatter
constraint is expressed as a function of `canonical`, `primary`, `primary_pk`,
`ref_attr`, `related`, `related_pk`, `chosen_attr`. So the uniqueness lane is NOT
an ungrounded-oracle echo; it is about whether a rival can satisfy one bucket's
CONTENTS while keying a pk under the wrong (raw alias) identity, over-fetching,
scattering under a raw key, or corrupting the OTHER participating bucket --
exactly the behaviours the reported mapping's whole-mapping consumer cannot
tolerate. The honest cheapest impl (direct-build of both canonical buckets) is
included as a POSITIVE control.

CONTROL-FLOW-EFFECT: N/A. related_reported_fields is a pure value computation
returning a Dict[int,Dict[int,int]]; there is no raise / return-channel /
external side-effect that the value abstraction hides. The postcondition pins
both participating buckets' contents EXACTLY (presence + closure) and pins the
KEYING (anti-scatter) of each, so every observable of the result that the
downstream consumer reads is constrained. No capability-token rival is
meaningful here.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The changed key-normalization is modelled DEEPLY (the @Pure canonical_of plus the
impl) and validated == the real Django `_meta.concrete_model` out-of-band by
axiom_check.py (G-AX, an A-reference). PBT re-runs that real-callee equivalence as
an axiom-soundness probe in the instance Docker image: canonical_of must equal the
real `._meta.concrete_model` (proxy->concrete, concrete->self, idempotent) and the
replayed accumulation must place the pk in the concrete bucket iff normalized.
axiom_check.py's source is read on the HOST at load time and embedded into the
probe string (the runner mounts only the probe at /work).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end. The frozen spec (axioms/pure/pre/post-conditions/
signature) is never touched, so same_spec holds for every spec case.
"""
from pathlib import Path

INSTANCE = "django__django-15814"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_REL_KEY = "    rel_key = canonical_of(canonical, related)  # type: int\n"
_PRIM_KEY = "    prim_key = canonical_of(canonical, primary)  # type: int\n"
_NORMALIZE = "    cur_model = canonical_of(canonical, cur_model)\n"
_REF_RECORD = "        from_set[ref_attr] = ref_attr\n"
_LEAF_SET = "    leaf_set[chosen_attr] = chosen_attr\n"
_SEEN_REL = "    seen[rel_key] = leaf_set\n"
_RETURN = "    return seen\n"
_IMPL_HEAD = ("    # Canonical identities under which the two participating "
              "models report.\n"
              "    prim_key = canonical_of(canonical, primary)  # type: int\n"
              "    rel_key = canonical_of(canonical, related)  # type: int\n")

for _a in (_REL_KEY, _PRIM_KEY, _NORMALIZE, _REF_RECORD, _LEAF_SET, _SEEN_REL,
           _RETURN, _IMPL_HEAD):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The exact body from the impl head onward to # impl-end (for whole-body
# replacements).
_BODY_START = _BASE.index(_IMPL_HEAD)
_BODY_END = _BASE.index("    # impl-end")
_BODY = _BASE[_BODY_START:_BODY_END]


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5) POSITIVE CONTROL -- direct build of both canonical buckets. A structurally
# DIFFERENT but CORRECT impl: it skips the two-accumulator (must_include + seen)
# merge dance entirely and builds the two canonical buckets directly, putting
# BOTH the chosen attribute and the related primary key under rel_key =
# canonical_of(related), and BOTH the primary model's own primary key and the
# reference attribute under prim_key = canonical_of(primary). It MUST verify (it
# satisfies presence, closure, anti-scatter -- the only keys of Result() are
# rel_key and prim_key, each equal to a canonical_of, so a raw alias identity is
# never a key); else the postcondition is over-fit to the gold two-accumulator
# FORM => SPEC-TOO-STRONG. No read-only write, no extra keys.
_POS_DIRECT = _swap(
    _BASE, _BODY,
    "    # Direct build of both canonical reported buckets (structurally\n"
    "    # different from the gold accumulate-then-merge, behaviourally same).\n"
    "    rel_key = canonical_of(canonical, related)  # type: int\n"
    "    prim_key = canonical_of(canonical, primary)  # type: int\n"
    "    bucket = {}  # type: Dict[int, int]\n"
    "    bucket[chosen_attr] = chosen_attr\n"
    "    bucket[related_pk] = related_pk\n"
    "    prim_bucket = {}  # type: Dict[int, int]\n"
    "    prim_bucket[primary_pk] = primary_pk\n"
    "    prim_bucket[ref_attr] = ref_attr\n"
    "    seen = {}  # type: Dict[int, Dict[int, int]]\n"
    "    seen[rel_key] = bucket\n"
    "    seen[prim_key] = prim_bucket\n"
    "    return seen\n",
)

# (5b) POSITIVE CONTROL -- statement reorder. Record the primary key into each
# canonical bucket BEFORE the other attribute (the gold records the chosen
# attribute first on the related side, and the primary key first on the primary
# side), and build the primary bucket before the related one. Order of two
# distinct self-keyed inserts into the same Dict cannot change the reported set,
# and the two buckets are independent; this MUST verify. Keeps the canonical
# keying and every clause; the only change is statement order. Else
# SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _BODY,
    "    # Reorder: build the primary bucket first, and record each bucket's\n"
    "    # primary key before its other attribute. Same reported sets.\n"
    "    rel_key = canonical_of(canonical, related)  # type: int\n"
    "    prim_key = canonical_of(canonical, primary)  # type: int\n"
    "    seen = {}  # type: Dict[int, Dict[int, int]]\n"
    "    prim_bucket = {}  # type: Dict[int, int]\n"
    "    prim_bucket[ref_attr] = ref_attr\n"
    "    prim_bucket[primary_pk] = primary_pk\n"
    "    seen[prim_key] = prim_bucket\n"
    "    bucket = {}  # type: Dict[int, int]\n"
    "    bucket[related_pk] = related_pk\n"
    "    bucket[chosen_attr] = chosen_attr\n"
    "    seen[rel_key] = bucket\n"
    "    return seen\n",
)

# (6) ADMISSIBILITY -- a fresh, F2P-shaped input must satisfy every Requires.
# The F2P scenario is a related proxy model (token 2) whose concrete identity is
# token 1, pk token 10, chosen attr token 20, reached from a primary model
# (token 3, its own canonical) through a reference attribute (token 30) with the
# primary key token 40. We build a canonical map {2:1, 1:1, 3:3} (proxy->concrete,
# concrete->self, primary->self) and an owner map {20:1} (the chosen attribute is
# stored by the related model's canonical identity), then Assert every Requires
# conjunct on that input -- read-only permission, distinctness, idempotence at
# both participants, separate storage identities, and chosen-attribute ownership.
# MUST verify; else the precondition rejects a normal F2P-shaped input =>
# PRECOND-TOO-STRONG. (Uses guarded dict access; no string indexing.)
_POS_ADMISS = _swap(
    _BASE, _IMPL_HEAD,
    "    # ADMISSIBILITY probe on a fresh F2P-shaped proxy scenario.\n"
    "    cmap = {}  # type: Dict[int, int]\n"
    "    cmap[2] = 1   # proxy token 2 -> concrete token 1\n"
    "    cmap[1] = 1   # concrete is its own canonical (idempotent)\n"
    "    cmap[3] = 3   # the primary model is its own canonical\n"
    "    omap = {}  # type: Dict[int, int]\n"
    "    omap[20] = 1  # the chosen attribute is stored by the related model\n"
    "    Assert(canonical_of(cmap, canonical_of(cmap, 2)) == canonical_of(cmap, 2))\n"
    "    Assert(canonical_of(cmap, canonical_of(cmap, 3)) == canonical_of(cmap, 3))\n"
    "    Assert(canonical_of(cmap, 3) != canonical_of(cmap, 2))\n"
    "    Assert(20 in omap\n"
    "           and canonical_of(cmap, omap[20]) == canonical_of(cmap, 2))\n"
    "    Assert(Acc(dict_pred(cmap), 1 / 2))\n"
    "    Assert(Acc(dict_pred(omap), 1 / 2))\n"
    "    Assert(10 != 20)\n"
    "    Assert(40 != 30)\n"
    "    # Canonical identities under which the two participating models report.\n"
    "    prim_key = canonical_of(canonical, primary)  # type: int\n"
    "    rel_key = canonical_of(canonical, related)  # type: int\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). `canonical` is read-only at
# 1/2. This rival WRITES `canonical[related] = related` before the body, trying to
# force the related model to be its own canonical (so the alias/anti-scatter case
# never arises and the pre-patch raw keying becomes vacuously correct). Under
# Acc(dict_pred(canonical),1/2) a store needs FULL permission, so it must be
# rejected for INSUFFICIENT PERMISSION (not a value mismatch). Every gold
# invariant/clause is kept verbatim so the rejection is attributable solely to the
# write through the half-permission reference.
_RIVAL_FRAME = _swap(
    _BASE, _IMPL_HEAD,
    "    # FRAME-MUTATION probe: overwrite the read-only canonical map.\n"
    "    canonical[related] = related\n"
    "    # Canonical identities under which the two participating models report.\n"
    "    prim_key = canonical_of(canonical, primary)  # type: int\n"
    "    rel_key = canonical_of(canonical, related)  # type: int\n",
)

# (2) PARTIAL-DOMAIN / PRE-PATCH KEYING -- drop the canonical normalization line
# `cur_model = canonical_of(canonical, cur_model)`. This is EXACTLY model_prepatch:
# the passthrough pk is keyed by the RAW related identity. On a non-alias input
# (related == canonical) it is correct; on an ALIAS input (related != canonical)
# the merge folds the pk into seen[related] (the raw bucket), leaving the canonical
# bucket Result()[canonical_of(related)] WITHOUT the pk, and creating a raw-key
# bucket. Fails the presence clause (related_pk in Result()[rk]) AND the
# anti-scatter clause (related != rk ==> related not in Result()).
_RIVAL_PREPATCH = _swap(_BASE, _NORMALIZE, "")

# (3) PARTIAL-DOMAIN / OVER-FETCH -- key the pk and chosen attr under the canonical
# identity correctly, but ALSO record a spurious third self-keyed attribute (token
# 888) into the related canonical bucket. Presence + keying + anti-scatter still
# hold, but the CLOSURE clause (Forall a in bucket :: a==related_pk or
# a==chosen_attr) is violated: the verifier must prove 888 == related_pk or
# 888 == chosen_attr, which it cannot (related_pk/chosen_attr are symbolic).
# Rejected on closure.
_RIVAL_OVERFETCH = _swap(
    _BASE, _LEAF_SET,
    "    leaf_set[chosen_attr] = chosen_attr\n"
    "    leaf_set[888] = 888  # spurious over-fetch attribute\n",
)

# (4) ANTI-SCATTER / "paper over the symptom" -- key the pk under the canonical
# identity correctly (so presence + closure hold), but ALSO inject a raw-alias
# bucket keyed by `related` itself when `related` is not already a key (i.e. only
# in the alias case, so the non-alias canonical bucket is never overwritten). This
# is the a8 bug-retaining post-hoc injection: it leaves the symptom-fixing
# canonical bucket intact yet still scatters a bucket under the raw alias key. On
# an alias input (related != canonical) `related in Result()` becomes True, so the
# anti-scatter clause (related != rk ==> related not in Result()) is violated.
_RIVAL_SCATTER = _swap(
    _BASE, _RETURN,
    "    if related not in seen:\n"
    "        scatter = {}  # type: Dict[int, int]\n"
    "        scatter[related_pk] = related_pk\n"
    "        seen[related] = scatter\n"
    "    return seen\n",
)

# (7) WHOLE-MAPPING CORRUPTION -- the related model's canonical bucket is built
# EXACTLY as gold (presence + closure + anti-scatter all hold there), but the
# OTHER participating bucket is overwritten with the related model's primary key.
# The reported mapping is consumed whole downstream, so a mapping that is perfect
# at the related key and corrupt at the primary key is wrong: the primary object
# is no longer identifiable and the reference it is reached through is no longer
# fetched. Rejected on the primary-side presence clauses (primary_pk in
# Result()[prim_key] and ref_attr in Result()[prim_key]) -- the verifier cannot
# prove related_pk == primary_pk.
_RIVAL_PRIM_CLOBBER = _swap(
    _BASE, _RETURN,
    "    junk = {}  # type: Dict[int, int]\n"
    "    junk[related_pk] = related_pk\n"
    "    seen[prim_key] = junk  # corrupt the other participating bucket\n"
    "    return seen\n",
)

# (8) WHOLE-MAPPING ERASURE -- as (7) but the other participating bucket is
# emptied rather than repopulated (an empty reported set is not "no restriction";
# it is a restriction to nothing). Rejected on the same primary-side presence
# clauses.
_RIVAL_PRIM_EMPTY = _swap(
    _BASE, _RETURN,
    "    empty = {}  # type: Dict[int, int]\n"
    "    seen[prim_key] = empty  # erase the other participating bucket\n"
    "    return seen\n",
)

# (9) MISSING PASSTHROUGH REFERENCE -- record the primary model's own primary key
# but NOT the reference attribute the related object is reached through. Every
# related-side clause still holds and the primary bucket is a subset of what the
# closure clause allows, so only the ref_attr presence clause can reject it.
_RIVAL_NO_REF = _swap(
    _BASE, _REF_RECORD,
    "        pass  # the reference attribute is not recorded\n",
)

# (10) ANTI-SCATTER ON THE PRIMARY PARTICIPANT -- the mirror of (4): keep both
# canonical buckets exactly right, but ALSO lodge a bucket under the primary
# model's RAW identity when that identity is a non-canonical alias. Violates the
# primary provenance clause (primary != prim_key ==> primary not in Result()).
_RIVAL_PRIM_SCATTER = _swap(
    _BASE, _RETURN,
    "    if primary not in seen:\n"
    "        pscatter = {}  # type: Dict[int, int]\n"
    "        pscatter[primary_pk] = primary_pk\n"
    "        seen[primary] = pscatter\n"
    "    return seen\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-direct-build", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "structurally-different (both canonical buckets built directly, "
                  "skipping the gold must_include+seen merge) but CORRECT impl: "
                  "chosen_attr and related_pk are self-keyed under rel_key, "
                  "primary_pk and ref_attr under prim_key, and those two "
                  "canonical_of values are the only keys of Result(), so presence "
                  "+ closure + anti-scatter all hold on both sides. Must verify; "
                  "else the postcondition is over-fit to the two-accumulator FORM "
                  "=> SPEC-TOO-STRONG. (This is the panel's direct-build positive "
                  "control, extended to the whole reported mapping.)"},
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "statement reorder: the primary bucket is built first and each "
                  "bucket records its primary key before its other attribute "
                  "(gold does the opposite on the related side). Distinct "
                  "self-keyed inserts into one Dict commute and the two buckets "
                  "are independent, so the reported sets are identical. Must "
                  "verify; else the postcondition is sensitive to insert ORDER => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall-proxy", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a fresh F2P-shaped proxy scenario (canonical map {2:1,1:1,3:3}, "
                  "proxy token 2 -> concrete token 1, primary token 3, owner map "
                  "{20:1}, pk 10, chosen 20, primary pk 40, reference 30) must "
                  "establish EVERY Requires conjunct: read-only permission on both "
                  "maps, attname distinctness, idempotence at both participants, "
                  "separate storage identities, and chosen-attribute ownership. If "
                  "the precondition rejects this normal proxy input => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-canonical", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: deferred_to_data only "
                   "READS `_meta.concrete_model` (an attribute), it never mutates the "
                   "model's _meta / concrete map. The rival exists solely to test whether "
                   "the read-only (1/2) precondition on `canonical` can be subverted by "
                   "overwriting it (forcing related to be its own canonical so the buggy "
                   "raw keying becomes vacuously correct). A patch that mutated the global "
                   "model-metadata map to make a proxy its own concrete model would corrupt "
                   "Django's ORM for every other query and would NOT resolve the F2P -- a "
                   "verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous satisfaction via self-normalizing the read-only input).",
     "rationale": "MANDATORY frame-mutation probe. `canonical[related] = related` writes "
                  "through a 1/2 (read-only) reference and MUST fail for INSUFFICIENT "
                  "PERMISSION (a dict store needs full Acc(dict_pred(canonical))), NOT a "
                  "value mismatch; every gold clause is kept verbatim so the rejection is "
                  "attributable to the write. Rejection source: the PERMISSION SYSTEM. If "
                  "it verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "weak-prepatch-raw-keying", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this is EXACTLY model_prepatch.py: it drops the inserted line "
                   "`cur_model = cur_model._meta.concrete_model`, keying the passthrough pk "
                   "by the RAW (proxy) model. A faithful patch doing this is the unfixed "
                   "Django: on the F2P scenario (Issue.assignee -> ProxyTrackerUser proxy of "
                   "TrackerUser, .only('assignee__status')) the pk 'id' is keyed by the "
                   "proxy and absent from the concrete TrackerUser bucket, so "
                   "RelatedPopulator.__init__ raises `ValueError: 'id' is not in list` and "
                   "the F2P test_select_related_only FAILS -- verify-not-resolve.",
     "rationale": "rejection source: TWO postcondition clauses. On an alias input "
                  "(related != canonical_of(related)) the pk is folded into seen[related] "
                  "(raw bucket), so (a) `related_pk in Result()[canonical_of(related)]` is "
                  "FALSE (the canonical bucket lacks the pk) and (b) the anti-scatter clause "
                  "`related != rk ==> not(related in Result())` is FALSE (a raw-key bucket "
                  "exists). The verifier cannot close either on alias inputs. If it verified "
                  "=> SPEC-TOO-WEAK (the canonical-keying fix would be unenforced)."},
    {"id": "weak-over-fetch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERFETCH,
     "refinement": "recording a spurious extra attribute in the related model's reported "
                   "set is exactly the over-fetch the downstream RelatedPopulator does not "
                   "tolerate: init_list is built from the reported attnames and the pk index "
                   "is looked up positionally; an extra attname shifts/breaks that list. A "
                   "faithful patch that over-fetches an unrelated attribute for the related "
                   "model changes the selected columns and the init_list, so the F2P "
                   "select_related().only() path does not reconstruct the object as expected "
                   "-- verify-not-resolve (it fetches columns the gold fix does not).",
     "rationale": "rejection source: the CLOSURE clause `Forall a:int :: a in "
                  "Result()[rk] ==> a == related_pk or a == chosen_attr`. The rival adds a "
                  "third self-keyed key 888 to the related canonical bucket; the verifier "
                  "must prove 888 == related_pk or 888 == chosen_attr, which is false in "
                  "general (both symbolic). Cannot close closure. If it verified => "
                  "SPEC-TOO-WEAK (no-over-fetch guarantee hollow)."},
    {"id": "weak-scatter-injection", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SCATTER,
     "refinement": "this is the a8 'paper over the symptom' rival: it keeps the canonical "
                   "bucket correct (so the immediate ValueError might not fire) yet ALSO "
                   "scatters a raw-alias bucket keyed by the proxy. A faithful patch that "
                   "left the pk under BOTH the concrete and the raw proxy key (rather than "
                   "moving it cleanly to the concrete identity) would report a bucket for a "
                   "model identity (the proxy) the loader does not expect as a key, "
                   "diverging from the gold keying that the downstream consumer relies on "
                   "-- it does not faithfully implement the single-canonical-key fix the "
                   "F2P exercises -- verify-not-resolve.",
     "rationale": "rejection source: the ANTI-SCATTER clause `related != "
                  "canonical_of(related) ==> not(related in Result())`. On an alias input "
                  "the rival adds seen[related] (raw key) while related != canonical, so "
                  "`related in Result()` is True and the implication is violated. The guard "
                  "`if related not in seen` ensures the non-alias canonical bucket is never "
                  "overwritten, so the rejection is attributable solely to the scatter. If "
                  "it verified => SPEC-TOO-WEAK (provenance/canonical-keying unenforced)."},
    {"id": "weak-other-bucket-clobber", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRIM_CLOBBER,
     "refinement": "a faithful patch of this shape keeps the gold accumulation for the "
                   "traversed model but overwrites the reported set of the model the query "
                   "starts from with the related model's pk. The reported per-model mapping "
                   "is handed to the column builder WHOLE (deferred_to_columns feeds every "
                   "bucket), so on the F2P scenario the query's own model loses both its pk "
                   "and the reference attname it is traversed through; the related object "
                   "can then no longer be both restricted and select_related-traversed and "
                   "the F2P test FAILS while the related bucket is byte-for-byte gold -- "
                   "verify-not-resolve unless the OTHER bucket is pinned too.",
     "rationale": "rejection source: the PRIMARY-SIDE PRESENCE clauses `primary_pk in "
                  "Result()[canonical_of(primary)]` and `ref_attr in "
                  "Result()[canonical_of(primary)]`. The rival replaces that bucket with "
                  "{related_pk}; the verifier must prove related_pk == primary_pk and "
                  "related_pk == ref_attr, which is false in general (all symbolic). If it "
                  "verified => SPEC-TOO-WEAK (the mapping is only pinned at one key)."},
    {"id": "weak-other-bucket-erased", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRIM_EMPTY,
     "refinement": "as the clobber rival, but the query-own model's reported set is emptied. "
                   "An empty reported set is not 'no restriction' -- downstream it means the "
                   "model is mentioned with nothing to load, so the F2P query cannot build "
                   "its own object at all and the F2P test FAILS with the related bucket "
                   "still exactly gold -- verify-not-resolve.",
     "rationale": "rejection source: the same PRIMARY-SIDE PRESENCE clauses. An empty bucket "
                  "contains neither primary_pk nor ref_attr, so both conjuncts fail. If it "
                  "verified => SPEC-TOO-WEAK (a reported bucket could be erased "
                  "unobserved)."},
    {"id": "weak-missing-passthrough-reference", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_NO_REF,
     "refinement": "a faithful patch of this shape records the query-own model's pk but "
                   "drops the reference attribute it passes through, i.e. it treats a "
                   "restriction on the related object as licence to defer the reference "
                   "itself. On the F2P scenario the reference column is then not selected "
                   "while the relation is still traversed, which the loader rejects "
                   "outright, so the F2P test FAILS -- verify-not-resolve.",
     "rationale": "rejection source: the presence clause `ref_attr in "
                  "Result()[canonical_of(primary)]`. Every other clause still holds (the "
                  "bucket {primary_pk} is inside what closure allows), so the rejection is "
                  "attributable solely to the missing passthrough reference. If it verified "
                  "=> SPEC-TOO-WEAK (the passthrough obligation would be partial)."},
    {"id": "weak-primary-scatter-injection", "kind": "uniqueness",
     "expect": "reject",
     "module": _RIVAL_PRIM_SCATTER,
     "refinement": "the mirror of the scatter rival on the other participant: a patch that "
                   "reports the query-own model's requirements under BOTH its canonical "
                   "identity and its raw alias identity. The mapping's consumer looks the "
                   "model up by its canonical identity, so a bucket lodged under the alias "
                   "identity is a key the loader does not expect and does not read, "
                   "diverging from the gold keying -- the same provenance defect the "
                   "canonical-keying behaviour exists to prevent.",
     "rationale": "rejection source: the PRIMARY PROVENANCE clause `primary != "
                  "canonical_of(primary) ==> not(primary in Result())`. On an input where "
                  "the query-own model is a non-canonical alias the rival adds seen[primary] "
                  "while primary != prim_key, violating the implication. If it verified => "
                  "SPEC-TOO-WEAK (provenance pinned on only one participant)."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed; the changed key-normalization
# is an A-reference deep model (canonical_of == real _meta.concrete_model). We
# re-run that real-callee equivalence (axiom_check.py's logic, read on the HOST and
# embedded into a self-contained probe) as an axiom-soundness check: if the deep
# model canonical_of ever disagrees with the real Django attribute, or the replayed
# accumulation does not place the pk in the concrete bucket iff normalized, the
# A-reference is unsound. A containment probe is N/A: there is no axiom Requires
# domain (no @ContractOnly axiom); canonical_of is total over the int-token map
# (the m-itself fallback covers every model not in the map), so every input the
# caller can pass is in its domain by construction.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-canonical-equals-concrete-model",
        "axiom": "canonical_of",  # the A-reference deep model (not a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model canonical_of (pure region) is an A-reference: it must "
                     "equal the REAL Django attribute `model._meta.concrete_model` "
                     "(proxy->concrete parent, concrete->self, idempotent) on every model. "
                     "This probe (axiom_check.py verbatim) configures Django, builds a "
                     "concrete model, a proxy, and a proxy-of-proxy, reads the real "
                     "._meta.concrete_model, asserts canonical_of agrees and is idempotent, "
                     "and replays the deferred_to_data-style accumulation asserting the "
                     "related pk lands in the CONCRETE reported set iff the canonical "
                     "normalization is applied (and stays put when the model is already "
                     "concrete). Exit 0 iff every obligation holds; any disagreement => the "
                     "A-reference (canonical_of == _meta.concrete_model) is UNSOUND.",
    },
]
