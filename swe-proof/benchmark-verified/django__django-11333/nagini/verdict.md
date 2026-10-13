# P2 adversarial audit — django__django-11333

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,6 @@
 """
 from typing import Dict, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -102,7 +101,6 @@
     # from the object already cached for the resolved selector (so a rebuild
     # would be observably a DIFFERENT object).
     Requires(Implies(cached, existing != fresh))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(cache))
@@ -130,9 +128,5 @@
     Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
     # post-conditions-end
     # impl-start
-    key = resolve_selector(selector)
-    if key in cache:
-        return cache[key]
-    cache[key] = fresh
-    return fresh
+
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routing-table object is expensive to build, so the lookup that hands one
  out memoizes its results in a shared cache keyed by a configuration selector.
  The selector may be supplied explicitly, or omitted; when it is omitted the
  lookup substitutes the process-wide default selector before doing anything
  else. The behaviour pinned here is that the memoization key is the
  RESOLVED selector -- the one obtained after the omitted-means-default
  substitution -- not the raw argument:

    (1) Omitting the selector and supplying the default selector explicitly are
        the same request: both resolve to the default selector, so they hand
        back the very same cached object. A routing table already built for the
        default selector is reused when the selector is omitted, rather than a
        second one being built and cached separately.

    (2) Two requests whose resolved selectors differ hand back distinct objects:
        each resolved selector owns its own cache slot, so omitting the selector
        never collides with a genuinely different selector.

  The consequence that matters: callers that omit the selector (e.g. before the
  default has been established for the thread) and callers that pass the default
  selector explicitly (e.g. after it has been established) share one cached
  routing table instead of redundantly constructing and storing two.

Modelling choices (Nagini fragment):
  * A selector is an ``int`` token; the omitted selector is ``Optional[int]``
    with ``None`` meaning "not supplied" (resolve to the default). The
    resolution mirrors the repo's "argument-or-default" expression
    (mapping.md §2). The process-wide default selector is the module-level
    constant ``default_selector()``.
  * The shared cache is a ``Dict[int, int]`` from a RESOLVED selector token to
    the identity token of the routing table built for it. Object identity in
    the repo (``is`` / ``is not`` in the tests) is carried by integer-identity
    of these tokens: equal tokens model the same object, distinct tokens model
    distinct objects (mapping.md §2).
  * Whether the RESOLVED selector is ALREADY cached at entry is captured as a
    ``bool`` parameter ``cached`` pinned by a precondition to the entry
    membership of the resolved selector, and the object already cached for it
    (when present) as an ``int`` parameter ``existing`` pinned to its entry
    value. These pre-state scalars let the memoization guarantee be gated on a
    genuine entry fact about the cache rather than on a membership/value query
    against the (mutated-in-place) cache, which an implementation could perturb
    by writing the slot itself (the django-12713 pattern).
  * The freshly built routing-table identity for a not-yet-cached selector is a
    ``fresh: int`` parameter, distinct from the already-cached object, modelling
    "construct a new object".

The cache is genuinely mutated in place (a new slot is added on a miss), so it
is held at FULL permission and its exact post-state is stated. No string
indexing is used (Nagini bans it). The whole behaviour is modelled deeply (the
omitted-means-default resolution and the lookup-or-insert keyed on the resolved
selector are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the memoized-on-resolved-selector lookup is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def default_selector() -> int:
    """The process-wide default selector substituted when none is supplied."""
    return 0


@Pure
def resolve_selector(selector: Optional[int]) -> int:
    """The resolved selector: the supplied one when supplied, otherwise the
    default. Mirrors the repo's argument-or-default expression. The omitted
    selector and the default selector resolve to the SAME value, which is the
    key fact the cache is keyed on."""
    if selector is None:
        return default_selector()
    return selector
# pure-end


def get_resolver(cache: Dict[int, int], selector: Optional[int],
                 cached: bool, existing: int, fresh: int) -> int:
    # pre-conditions-start
    # The shared cache may gain a new slot; full permission.
    Requires(dict_pred(cache))
    # ``cached`` captures, AT ENTRY, whether the RESOLVED selector already has a
    # cached object; ``existing`` captures that object's identity when it does.
    # Both are pre-state facts, bound before any mutation, so the memoization
    # guarantee below gates on the genuine entry state of the cache rather than
    # on a query against the (possibly mutated) cache.
    Requires(cached == (resolve_selector(selector) in cache))
    Requires(Implies(cached, cache[resolve_selector(selector)] == existing))
    # A freshly-built routing-table identity is a not-yet-used token: it differs
    # from the object already cached for the resolved selector (so a rebuild
    # would be observably a DIFFERENT object).
    Requires(Implies(cached, existing != fresh))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cache))
    # The handed-back object is the one cached under the RESOLVED selector. A
    # request whose selector resolves to the default therefore reuses the cache
    # slot of the default selector, regardless of whether the selector was
    # supplied explicitly or omitted: both share one cached object.
    Ensures(resolve_selector(selector) in cache)
    Ensures(Result() == cache[resolve_selector(selector)])
    # Memoization: when the resolved selector was ALREADY cached at entry, the
    # request hands back that very same object -- the slot is reused, never
    # rebuilt. (Gated on the entry scalar ``cached``/``existing``, so an impl
    # cannot dodge it by writing the slot itself.)
    Ensures(Implies(cached, Result() == existing))
    # When the resolved selector was NOT yet cached at entry, it is built fresh.
    Ensures(Implies(not cached, Result() == fresh))
    # Distinctness: every selector OTHER than the resolved one keeps its own
    # cached object untouched, so distinct resolved selectors never collide --
    # omitting the selector hands back the default's object, never a different
    # selector's object.
    Ensures(Forall(int, lambda k: (Implies(
        Old(k in cache) and k != resolve_selector(selector),
        (k in cache) and cache[k] == Old(cache[k])))))
    # No selector slot is dropped; the cache only ever grows.
    Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
    # post-conditions-end
    # impl-start
    key = resolve_selector(selector)
    if key in cache:
        return cache[key]
    cache[key] = fresh
    return fresh
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE benchmark-verified/django__django-11333/nagini (django__django-11333). Ran from project root with python -m swebench_unified.adversary and bash scripts/nagini_verify.sh.

SPEC SHAPE: deep model of the resolve-then-memoize fix. get_resolver(cache: Dict[int,int], selector: Optional[int], cached: bool, existing: int, fresh: int). Observable behaviour fully pinned on the RESOLVED key: resolve_selector(selector) in cache; Result()==cache[resolve_selector(selector)]; Implies(cached, Result()==existing); Implies(not cached, Result()==fresh); per-other-key distinctness (Old(cache[k]) preserved for k != resolved); no-key-dropped. Pre-state scalars cached/existing gate memoization (django-12713 pattern) so overwrite-on-hit cannot dodge the clause. NO axioms, NO deep-model-references.

A-LEG / REFINEMENT AUDIT: meta.json axioms=[] and deep_model_references=[]; refinement.md sec C states every leg is R (type refinement) or I (identical op), NO @ContractOnly axiom (neither A-consumed nor A-reference), NO kind-3. Hence NO axiom<->callee correspondence to falsify (G-AX vacuous, recorded pass). Single modeled function collapses gold get_resolver + _get_cached_resolver; base.py cache_clear edit is a mechanical follow-on naming the same cache the model's `cache` param abstracts. Correspondence holds: A1 selector<->urlconf token; A2 resolve_selector<->'if urlconf is None: urlconf=ROOT_URLCONF' run BEFORE the memo (the actual fix); A3 cache hit<->lru_cache hit; A4 cache miss insert<->URLResolver construct+store (contents unobserved, abstracted as fresh token; assertIs/assertIsNot test identity only).

SAME-SPEC: all 7 attacks byte-identical spec signature (adversary same-spec exit 0).

ATTACKS (impl-region-only edits; each `python -m swebench_unified.adversary weakness nagini django__django-11333 <atk> `; also direct `bash scripts/nagini_verify.sh <atk>`):
- atk_1 over-construct-on-hit (cache[key]=fresh; return fresh) — the §E historically-UNSOUND case: NOT-A-COUNTEREXAMPLE, verify FAILED (postcondition might not hold, 14.2s). Confirms scalar-gated memoization clause now soundly rejects it.
- atk_2 prepatch raw-key bug (key on raw arg, resolve only for build; None->-1 sentinel): NOT-A-COUNTEREXAMPLE, verify FAILED (14.7s). This is the pre-patch bug -> prepatch reproduced.
- atk_3 partial-domain (correct on hit, returns `existing` instead of `fresh` on miss): FAILED (14.0s) — violates Implies(not cached, Result()==fresh).
- atk_4 boundary (always key on default_selector(), mishandles non-None selector): FAILED (14.7s) — violates Result()==cache[resolve_selector(selector)] for non-default selectors.
- atk_5 control-flow-effect (correct return but writes cache[key+1]=fresh, corrupting a neighbour): FAILED (14.1s) — violates per-other-key distinctness.
- atk_6 ungrounded-oracle echo (branch on scalar `cached`, return existing on hit but never populate slot on that path): FAILED (15.3s) — violates resolve_selector(selector) in cache.
- atk_7 echo variant (rewrite slot with existing on hit): NOT-A-COUNTEREXAMPLE, verify FAILED (weakness).

All 7 are genuine postcondition rejections at ~14-15s (not timeouts/crashes; message 'Postcondition of get_resolver might not hold'), verified via both `adversary weakness` (exit 2) and direct `nagini_verify.sh` (exit 1). Runs done in parallel batches of <=3 JVM checks.

POSITIVE CONTROL: verbatim model.py copy VERIFIES (bash scripts/nagini_verify.sh -> 'Verification successful', 15.2s, exit 0).

No CANDIDATE (same-spec AND verifying) emerged, so there was no verifying-wrong-impl faithful patch to materialize/resolve-run — patches={}. prepatch_reproduced=true (atk_2 reproduces the raw-key pre-patch bug and is rejected). VERDICT: SOUND — >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect, over-construct, prepatch raw-key, ungrounded-oracle echo x2) all run and none breaks the spec; refinement legs all R/I with a holding correspondence and no A-legs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routing-table object is expensive to build, so the lookup that hands one
  out memoizes its results in a shared cache keyed by a configuration selector.
  The selector may be supplied explicitly, or omitted; when it is omitted the
  lookup substitutes the process-wide default selector before doing anything
  else. The behaviour pinned here is that the memoization key is the
  RESOLVED selector -- the one obtained after the omitted-means-default
  substitution -- not the raw argument:

    (1) Omitting the selector and supplying the default selector explicitly are
        the same request: both resolve to the default selector, so they hand
        back the very same cached object. A routing table already built for the
        default selector is reused when the selector is omitted, rather than a
        second one being built and cached separately.

    (2) Two requests whose resolved selectors differ hand back distinct objects:
        each resolved selector owns its own cache slot, so omitting the selector
        never collides with a genuinely different selector.

  The consequence that matters: callers that omit the selector (e.g. before the
  default has been established for the thread) and callers that pass the default
  selector explicitly (e.g. after it has been established) share one cached
  routing table instead of redundantly constructing and storing two.

Modelling choices (Nagini fragment):
  * A selector is an ``int`` token; the omitted selector is ``Optional[int]``
    with ``None`` meaning "not supplied" (resolve to the default). The
    resolution mirrors the repo's "argument-or-default" expression
    (mapping.md §2). The process-wide default selector is the module-level
    constant ``default_selector()``.
  * The shared cache is a ``Dict[int, int]`` from a RESOLVED selector token to
    the identity token of the routing table built for it. Object identity in
    the repo (``is`` / ``is not`` in the tests) is carried by integer-identity
    of these tokens: equal tokens model the same object, distinct tokens model
    distinct objects (mapping.md §2).
  * Whether the RESOLVED selector is ALREADY cached at entry is captured as a
    ``bool`` parameter ``cached`` pinned by a precondition to the entry
    membership of the resolved selector, and the object already cached for it
    (when present) as an ``int`` parameter ``existing`` pinned to its entry
    value. These pre-state scalars let the memoization guarantee be gated on a
    genuine entry fact about the cache rather than on a membership/value query
    against the (mutated-in-place) cache, which an implementation could perturb
    by writing the slot itself (the django-12713 pattern).
  * The freshly built routing-table identity for a not-yet-cached selector is a
    ``fresh: int`` parameter, distinct from the already-cached object, modelling
    "construct a new object".

The cache is genuinely mutated in place (a new slot is added on a miss), so it
is held at FULL permission and its exact post-state is stated. No string
indexing is used (Nagini bans it). The whole behaviour is modelled deeply (the
omitted-means-default resolution and the lookup-or-insert keyed on the resolved
selector are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the memoized-on-resolved-selector lookup is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def default_selector() -> int:
    """The process-wide default selector substituted when none is supplied."""
    return 0


@Pure
def resolve_selector(selector: Optional[int]) -> int:
    """The resolved selector: the supplied one when supplied, otherwise the
    default. Mirrors the repo's argument-or-default expression. The omitted
    selector and the default selector resolve to the SAME value, which is the
    key fact the cache is keyed on."""
    if selector is None:
        return default_selector()
    return selector
# pure-end


def get_resolver(cache: Dict[int, int], selector: Optional[int],
                 cached: bool, existing: int, fresh: int) -> int:
    # pre-conditions-start
    # The shared cache may gain a new slot; full permission.
    Requires(dict_pred(cache))
    # ``cached`` captures, AT ENTRY, whether the RESOLVED selector already has a
    # cached object; ``existing`` captures that object's identity when it does.
    # Both are pre-state facts, bound before any mutation, so the memoization
    # guarantee below gates on the genuine entry state of the cache rather than
    # on a query against the (possibly mutated) cache.
    Requires(cached == (resolve_selector(selector) in cache))
    Requires(Implies(cached, cache[resolve_selector(selector)] == existing))
    # A freshly-built routing-table identity is a not-yet-used token: it differs
    # from the object already cached for the resolved selector (so a rebuild
    # would be observably a DIFFERENT object).
    Requires(Implies(cached, existing != fresh))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cache))
    # The handed-back object is the one cached under the RESOLVED selector. A
    # request whose selector resolves to the default therefore reuses the cache
    # slot of the default selector, regardless of whether the selector was
    # supplied explicitly or omitted: both share one cached object.
    Ensures(resolve_selector(selector) in cache)
    Ensures(Result() == cache[resolve_selector(selector)])
    # Memoization: when the resolved selector was ALREADY cached at entry, the
    # request hands back that very same object -- the slot is reused, never
    # rebuilt. (Gated on the entry scalar ``cached``/``existing``, so an impl
    # cannot dodge it by writing the slot itself.)
    Ensures(Implies(cached, Result() == existing))
    # When the resolved selector was NOT yet cached at entry, it is built fresh.
    Ensures(Implies(not cached, Result() == fresh))
    # Distinctness: every selector OTHER than the resolved one keeps its own
    # cached object untouched, so distinct resolved selectors never collide --
    # omitting the selector hands back the default's object, never a different
    # selector's object.
    Ensures(Forall(int, lambda k: (Implies(
        Old(k in cache) and k != resolve_selector(selector),
        (k in cache) and cache[k] == Old(cache[k])))))
    # No selector slot is dropped; the cache only ever grows.
    Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
    # post-conditions-end
    # impl-start
    key = resolve_selector(selector)
    if key in cache:
        return cache[key]
    cache[key] = fresh
    return fresh
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE benchmark-verified/django__django-11333/nagini (django__django-11333). Ran from project root with python -m swebench_unified.adversary and bash scripts/nagini_verify.sh.

SPEC SHAPE: deep model of the resolve-then-memoize fix. get_resolver(cache: Dict[int,int], selector: Optional[int], cached: bool, existing: int, fresh: int). Observable behaviour fully pinned on the RESOLVED key: resolve_selector(selector) in cache; Result()==cache[resolve_selector(selector)]; Implies(cached, Result()==existing); Implies(not cached, Result()==fresh); per-other-key distinctness (Old(cache[k]) preserved for k != resolved); no-key-dropped. Pre-state scalars cached/existing gate memoization (django-12713 pattern) so overwrite-on-hit cannot dodge the clause. NO axioms, NO deep-model-references.

A-LEG / REFINEMENT AUDIT: meta.json axioms=[] and deep_model_references=[]; refinement.md sec C states every leg is R (type refinement) or I (identical op), NO @ContractOnly axiom (neither A-consumed nor A-reference), NO kind-3. Hence NO axiom<->callee correspondence to falsify (G-AX vacuous, recorded pass). Single modeled function collapses gold get_resolver + _get_cached_resolver; base.py cache_clear edit is a mechanical follow-on naming the same cache the model's `cache` param abstracts. Correspondence holds: A1 selector<->urlconf token; A2 resolve_selector<->'if urlconf is None: urlconf=ROOT_URLCONF' run BEFORE the memo (the actual fix); A3 cache hit<->lru_cache hit; A4 cache miss insert<->URLResolver construct+store (contents unobserved, abstracted as fresh token; assertIs/assertIsNot test identity only).

SAME-SPEC: all 7 attacks byte-identical spec signature (adversary same-spec exit 0).

ATTACKS (impl-region-only edits; each `python -m swebench_unified.adversary weakness nagini django__django-11333 <atk> `; also direct `bash scripts/nagini_verify.sh <atk>`):
- atk_1 over-construct-on-hit (cache[key]=fresh; return fresh) — the §E historically-UNSOUND case: NOT-A-COUNTEREXAMPLE, verify FAILED (postcondition might not hold, 14.2s). Confirms scalar-gated memoization clause now soundly rejects it.
- atk_2 prepatch raw-key bug (key on raw arg, resolve only for build; None->-1 sentinel): NOT-A-COUNTEREXAMPLE, verify FAILED (14.7s). This is the pre-patch bug -> prepatch reproduced.
- atk_3 partial-domain (correct on hit, returns `existing` instead of `fresh` on miss): FAILED (14.0s) — violates Implies(not cached, Result()==fresh).
- atk_4 boundary (always key on default_selector(), mishandles non-None selector): FAILED (14.7s) — violates Result()==cache[resolve_selector(selector)] for non-default selectors.
- atk_5 control-flow-effect (correct return but writes cache[key+1]=fresh, corrupting a neighbour): FAILED (14.1s) — violates per-other-key distinctness.
- atk_6 ungrounded-oracle echo (branch on scalar `cached`, return existing on hit but never populate slot on that path): FAILED (15.3s) — violates resolve_selector(selector) in cache.
- atk_7 echo variant (rewrite slot with existing on hit): NOT-A-COUNTEREXAMPLE, verify FAILED (weakness).

All 7 are genuine postcondition rejections at ~14-15s (not timeouts/crashes; message 'Postcondition of get_resolver might not hold'), verified via both `adversary weakness` (exit 2) and direct `nagini_verify.sh` (exit 1). Runs done in parallel batches of <=3 JVM checks.

POSITIVE CONTROL: verbatim model.py copy VERIFIES (bash scripts/nagini_verify.sh -> 'Verification successful', 15.2s, exit 0).

No CANDIDATE (same-spec AND verifying) emerged, so there was no verifying-wrong-impl faithful patch to materialize/resolve-run — patches={}. prepatch_reproduced=true (atk_2 reproduces the raw-key pre-patch bug and is rejected). VERDICT: SOUND — >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect, over-construct, prepatch raw-key, ungrounded-oracle echo x2) all run and none breaks the spec; refinement legs all R/I with a holding correspondence and no A-legs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break (spec-too-strong / drift) attack on django__django-11333 nagini bundle. Modeled function: django.urls.resolvers.get_resolver post-patch (resolve None->settings.ROOT_URLCONF FIRST, then memoize on the resolved key via _get_cached_resolver, lru_cache(maxsize=None)).

Machine checks:
- adversary same-spec nagini django__django-11333 -> exit 0 ('SAME'): spec region byte-identical.
- scripts/nagini_verify.sh model.py -> 'Verification successful' (15.56s).
- Gold patch.diff + problem_statement inspected: gold splits get_resolver/_get_cached_resolver so omitted->default substitution runs BEFORE the lru_cache(maxsize=None) memo, keying on the resolved urlconf.

Postcondition-by-postcondition vs the real gold callee (checked for an outcome the spec FORCES that the real code would NOT produce):
1. resolve_selector(selector) in cache -- resolved key always present after hit or construct+insert. Match.
2. Result()==cache[resolve_selector(selector)] -- returns object memoized under resolved key. Match.
3. Implies(cached, Result()==existing) -- lru_cache HIT returns stored object. Match.
4. Implies(not cached, Result()==fresh) -- lru_cache MISS constructs+returns new object. Match.
5. Per-other-key frame -- lru_cache never perturbs unrelated entries. Match.
6. No-key-dropped -- maxsize=None => no eviction, memo only grows. Match.

Type abstraction str->Optional[int]: only equality/identity of urlconf is observed (F2P uses assertIs/assertIsNot), faithfully carried by int equality and int-identity tokens; None<->None, settings.ROOT_URLCONF<->default_selector()==0, explicit-default==omitted sharing one slot is the fix itself. The cached/existing/fresh pre-state scalars are single-valued per real call (maxsize=None never-evicted memo), so a verifying impl is sound for the real call (django-12713 pattern).

The only slack is that on a miss, fresh is not constrained distinct from OTHER keys' tokens -- a spec-WEAKNESS (too-permissive) direction, NOT drift/over-strength; it never forces the model to a result the real code would not produce. No input found where the modeled function disagrees with the real gold callee. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over model.py) screened against the public problem_statement only. Mechanical G-LEAK screen (leakage.screen with the nagini backend) PASSES with zero hard failures. Manual semantic review confirms no leak beyond the public task:

- No diff markers, no gold-patch line reproduced, no patched file path/module path (django/urls/resolvers.py, django/urls/base.py) in the spec view.
- No spec-view identifier or comment/docstring echoes a patched repo symbol beyond what the problem_statement already discloses. The gold-specific symbols (_get_cached_resolver, the two-function split, URLResolver, lru_cache, ROOT_URLCONF, cache_clear) appear ONLY in the auditor-only mapping.md/refinement.md, which are NOT part of the consumer spec view that G-LEAK screens. The model uses abstract carriers (selector:int, default_selector(), cache:Dict[int,int], resolve_selector).
- No bug/fix narration (the NARRATION screen finds nothing; comments describe desired behaviour abstractly, not 'the edit').

Crucially, the public problem_statement is itself very explicit: it names get_resolver + functools.lru_cache, describes the None-vs-ROOT_URLCONF double-construction bug, and states the proposed fix verbatim ('modify get_resolver to look up settings.ROOT_URLCONF before the memoized function call'). The spec view's core content -- resolve the omitted-means-default selector BEFORE the memoized lookup and key the cache on the resolved selector -- is a faithful abstract restatement of behaviour ALREADY public in the problem statement, not new information about the gold edit. Therefore the spec view leaks nothing beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
