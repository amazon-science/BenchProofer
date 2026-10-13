# refinement.md — scikit-learn__scikit-learn-10908

The operation-by-operation correspondence between `model.py`'s implementation
(the `get_feature_names` impl region and the deep `materialise_from_param`
helper) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses a `@ContractOnly` axiom's guarantee),
**A-reference** (a deep model validated `==` the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `get_feature_names()` (`text.py:994`)

Gold hunk:
```
     def get_feature_names(self):
         """Array mapping from feature integer indices to feature name"""
+        if not hasattr(self, 'vocabulary_'):
+            self._validate_vocabulary()
+
         self._check_vocabulary()

         return [t for t, i in sorted(six.iteritems(self.vocabulary_),
                                      key=itemgetter(1))]
```

| # | model.py impl op (`get_feature_names`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `self: Vectoriser` with fields `fitted`, `has_param`, `param`, `supplied`, `names`, `idx` | `self`, the `CountVectorizer` instance, carrying `vocabulary_` (presence **and content**), `vocabulary` (ctor param), `fixed_vocabulary_` | R | dynamic-attribute presence `hasattr(self,'vocabulary_')` ↔ `self.fitted`; `self.vocabulary is not None` ↔ `self.has_param`; the ctor list ↔ `self.param: List[int]` of term ids; `fixed_vocabulary_` ↔ `self.supplied`; and the mapping `self.vocabulary_` **as a whole** ↔ the parallel pair `(self.names, self.idx): (List[int], List[int])` — the terms in ascending index order and the index each of them carries — so that `vocabulary_ == {names[k]: idx[k]}` (mapping.md §2). The pair, not `names` alone, is the carrier: `names` alone is many-to-one on `vocabulary_` (`{'a':0,'b':1}` and `{'a':0,'b':7}` share an index-ordered key list), so a `names`-only carrier would make a **renumbering** of the mapping inexpressible, and R would be lossy on an observable the F2P test reads (`assert_equal(idx, cv.vocabulary_.get(name))`, `test_text.py:573-574`). |
| A2 | `if not self.fitted:` | `if not hasattr(self, 'vocabulary_'):` | R | the materialised-mapping presence test; flag ↔ `hasattr` (mapping.md §2). **This guard is the head of the new hunk.** |
| A3 | `if self.has_param: if usable_terms(self.param): materialise_from_param(self)` | `self._validate_vocabulary()` (called inside the new guard), taking its list branch and reaching the two assignments `self.fixed_vocabulary_ = True; self.vocabulary_ = dict(vocab)` (`text.py:296-297`) | A-reference | `_validate_vocabulary` is the **unchanged** routine; the patch adds only the guarded *call*. Its effect (build `vocabulary_` from the ctor list, set `fixed_vocabulary_=True`) is modelled **deeply** by the helper's verified loop + contract (`self.fitted`, `self.supplied`, `ToSeq(self.names)==ToSeq(self.param)`, `numbered_by_place(self.idx, self.names)`), validated `==` the real routine by G-AX (mapping.md §3.1). The fourth conjunct refines `vocab.setdefault(t, i)` over `enumerate(vocabulary)` (`text.py:280`) at the level of the index **values**, not merely of the resulting key order: term `i` of the ctor list is given index `i`, so the helper's loop must build `idx` as `places(k)` and G-AX asserts `cv.vocabulary_[vocab[i]] == i` term by term (not just `get_feature_names() == list(vocab)`). The model splits `has_param` explicitly because the real `_validate_vocabulary` is a *no-op materialisation that still records `fixed_vocabulary_=False`* (and sets no `vocabulary_`) when `vocabulary is None` — so a `vocabulary is None` object stays unfitted and the next op (A4) still fails, with the model's `else` branch reproducing both the `fixed_vocabulary_=False` side effect (`self.supplied = False`) and the raise. The `usable_terms` screen is the second split (A3b): the real routine reaches those assignments only for a list it can turn into a mapping, so the model invokes the helper only there. |
| A3b | `else: raise UnusableTermsError()` (when `not fitted`, `has_param`, and `not usable_terms(self.param)`) | the same `self._validate_vocabulary()` call, taking its list branch to a *rejection*: `raise ValueError("Duplicate term in vocabulary: %r" % t)` (`text.py:281-283`) when a term repeats, or `raise ValueError("empty vocabulary passed to fit")` (`text.py:294-295`) when the list is empty — **before** either assignment, so `vocabulary_` stays absent and `fixed_vocabulary_` keeps its entry value | R + I | the ctor `vocabulary` is an arbitrary caller-supplied list, so this is a reachable outcome of the very call the patch adds, not an excluded input. `usable_terms(self.param)` ↔ the routine's two acceptance conditions (mapping.md §1); `UnusableTermsError` ↔ that `ValueError` (mapping.md §2, a builtin in an `Exsures` crashes the translator). The no-write half is refined exactly: the model's rejection branch assigns nothing, matching `text.py:283`/`295` raising ahead of `text.py:296-297`; the `Exsures` states it as `not self.fitted and self.supplied == Old(self.supplied)`, and — the mapping being carried in two halves — as `ToSeq(self.names) == Old(ToSeq(self.names)) and ToSeq(self.idx) == Old(ToSeq(self.idx))`, so neither the names nor their numbering may be disturbed on the way out of the rejection. G-AX observes both halves of the class rejecting *and* writing nothing (sentinel-checked); G-CONF diffs this branch against the real function on 11 372 states. |
| A4 | `else: self.supplied = False; raise NotFittedError()` (when `not fitted` and `not has_param`) | the new guard runs `self._validate_vocabulary()` UNCONDITIONALLY on the unfitted path; on `vocabulary is None` it takes its else-branch `self.fixed_vocabulary_ = False` (`text.py:299`) and sets no `vocabulary_`, then the existing `self._check_vocabulary()` → `check_is_fitted(self,'vocabulary_')` raises `NotFittedError` (`text.py:996`, unchanged) | R + I | the unusable check, preceded by the load-bearing raise-path side effect. The gold's inserted guard calls `_validate_vocabulary` on EVERY unfitted object (not only the `has_param` one); when no ctor list was supplied, `_validate_vocabulary` records `fixed_vocabulary_ = False` and leaves `vocabulary_` unset, so `_check_vocabulary` still raises. The model reproduces both halves: `self.supplied = False` (modelling `fixed_vocabulary_ = False`) then `raise NotFittedError()`. The F2P test asserts this side effect *first* (`assert_false(cv.fixed_vocabulary_)`, `test_text.py:547`) — an impl that raises without recording `not supplied` (the pre-patch `_check_vocabulary`-only path) does NOT resolve. Reached on exactly the modelled condition (`not Old(self.fitted) and not Old(self.has_param)`). `NotFittedError` ↔ user-defined stand-in (mapping.md §2). |
| A5 | `result = [...]` copy of `self.names` in order, `return result` | `return [t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` (`text.py:998`, unchanged) | R + I | return the index-ordered feature names. The sorted-by-index comprehension over `vocabulary_` IS, by mapping.md §3.1, the terms in index order = `self.names`; the model copies `self.names` element-wise into `Result()`. This is not merely the model's *chosen* impl text: the spec **enforces** it, as `Ensures(ToSeq(Result()) == ToSeq(self.names))` together with the frame legs A6/A7 below. The copy (rather than handing back the object's own list) is enforced too — `Ensures(Acc(list_pred(Result())))` on top of `Ensures(Acc(list_pred(self.names)))` is unsatisfiable if `Result()` aliases `self.names`, matching the gold's fresh comprehension. |
| A6 | **no statement**: on the `self.fitted` path the impl region falls straight through to A5, writing nothing | on the already-materialised path the inserted guard `if not hasattr(self, 'vocabulary_')` is FALSE, so `_validate_vocabulary` — the **only** writer of `vocabulary_` (`text.py:297`) and `fixed_vocabulary_` (`text.py:296`/`:299`) — is never entered; `_check_vocabulary` (`text.py:301-307`) only reads, and the return comprehension (`text.py:998-999`) reads `six.iteritems(self.vocabulary_)` without rebinding a single key **or value** | R + I | the query is an **observation**, so the already-present mapping — *both* halves of it — and the recorded supplied-at-construction flag come back out unchanged. The spec pins this rather than leaving it to the impl text: `Ensures(Implies(Old(self.fitted), ToSeq(self.names) == Old(ToSeq(self.names)) and ToSeq(self.idx) == Old(ToSeq(self.idx)) and self.supplied == Old(self.supplied) and ToSeq(Result()) == Old(ToSeq(self.names))))`. Without the `names` leg a rival could clear, truncate, reverse or re-badge a learned mapping and still satisfy `ToSeq(Result()) == ToSeq(self.names)` (both sides move together) — and such a rival fails F2P `test_feature_names` (`test_text.py:552`, `assert_array_equal(['beer',...,'water'], feature_names)` after `fit_transform`) plus P2P `test_count_vectorizer_max_features` / `test_count_binary_occurrences`. Without the **`idx` leg** a strictly sneakier rival survives: leave the reported names exactly where they are and **renumber** the mapping underneath them (`self.vocabulary_ = {t: 2*i for t, i in self.vocabulary_.items()}` prepended to the gold hunk). Every `names`-level clause still holds — the sorted-by-index key order is unchanged by a monotone renumbering — yet the object is broken, and the test patch's added `assert_equal(idx, cv.vocabulary_.get(name))` over `enumerate(feature_names)` (`test_text.py:573-574`) catches it, as do the column-addressing P2P tests via `transform`'s `feature_idx = vocabulary[feature]` (`text.py:817`). This is the family the pre-repair carrier could not even express. |
| A7 | **no statement**: nothing in the impl region assigns `self.param` or `self.has_param`, on any of the four exits | `get_feature_names` never assigns `self.vocabulary`; `_validate_vocabulary` rebinds only the **local** `vocabulary` (`text.py:274`, `:277`, `:284`) and writes the distinct attribute `self.vocabulary_` from a `dict(vocabulary)` **copy** (`text.py:297`) | R + I | whether a list was supplied at construction, and that list itself, are read-only inputs to this query. The spec pins them on **every** exit — `Ensures(self.has_param == Old(self.has_param))`, `Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))`, restated inside both `Exsures`. This is what stops a rival from vacating a discriminating `Old(...)` clause by overwriting the input it is read off, and what makes A5's `Result()` claim bite on the supplied-list path. |
| A8 | **no statement** on the read path; the numbering is *established* by A3's helper and *carried* by the copy loop's `Invariant(numbered_by_place(self.idx, self.names))` | every site that can put a `vocabulary_` on the object numbers it by place: `enumerate(vocabulary)` for a list/set ctor vocabulary (`text.py:280`), the validated index bijection onto `range(len)` for a `Mapping` one (`text.py:286-293`), `_sort_features`' `enumerate` renumbering (`text.py:749-751`) and `_limit_features`' keep-mask `cumsum` (`text.py:783-789`) for a learned one | R + I | the *unconditional* `Ensures(numbered_by_place(self.idx, self.names))`, paired with `Ensures(ToSeq(Result()) == ToSeq(self.names))`, is what makes the returned list mean something: together they say the name at place `k` of the returned list is the one the mapping the object now holds sends to index `k`. Its matching `Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))` is a **representation invariant, not a domain narrowing** — it excludes no reachable state, per the four repo sites above, and `axiom_check.py`'s `check_every_mapping_is_numbered_by_place` *executes* the guards that enforce them (four rejected numberings; an accepted permutation, a list vocabulary and a learned `vocabulary_` plain and under `max_features`/`min_df`/`max_df`, all positional). `conformance_check.py` reports four labelled probes *outside* the restriction that **agree**, so nothing is hidden behind it; and the sixth-field determinism sweep in §B shows the clause removes exactly 40-fold freedom per pre-state rather than being decorative. |

## B. The discriminating clause and the prepatch

The spec's load-bearing clauses are the **Exsures**, the **not-already-fitted**
postcondition, the **numbering** clause (A8) that says which index each reported
name carries, and the **frame** legs (A6/A7) that make an observation an
observation. Quoted verbatim from `model.py`:

```
Ensures(self.has_param == Old(self.has_param))
Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
Ensures(ToSeq(Result()) == ToSeq(self.names))
Ensures(numbered_by_place(self.idx, self.names))
Ensures(Implies(not Old(self.fitted),
                Old(self.has_param) and Old(usable_terms(self.param))
                and self.supplied
                and ToSeq(Result()) == ToSeq(self.param)))
Ensures(Implies(Old(self.fitted),
                ToSeq(self.names) == Old(ToSeq(self.names))
                and ToSeq(self.idx) == Old(ToSeq(self.idx))
                and self.supplied == Old(self.supplied)
                and ToSeq(Result()) == Old(ToSeq(self.names))))
Exsures(NotFittedError, ... and not Old(self.fitted) and not Old(self.has_param)
                            and not self.supplied
                            and not self.fitted
                            and ToSeq(self.names) == Old(ToSeq(self.names))
                            and ToSeq(self.idx) == Old(ToSeq(self.idx))
                            and self.has_param == Old(self.has_param)
                            and ToSeq(self.param) == Old(ToSeq(self.param)))
Exsures(UnusableTermsError, ... and not Old(self.fitted) and Old(self.has_param)
                                and not Old(usable_terms(self.param))
                                and not self.fitted
                                and self.supplied == Old(self.supplied)
                                and ToSeq(self.names) == Old(ToSeq(self.names))
                                and ToSeq(self.idx) == Old(ToSeq(self.idx))
                                and self.has_param == Old(self.has_param)
                                and ToSeq(self.param) == Old(ToSeq(self.param)))
```

Taken together these pin **all six fields plus the result on all three exits**,
so the spec is a *total, deterministic* function on its domain: for every
in-domain pre-state there is exactly one `(exit, post-state, Result())` the
clauses admit. Enumerated over the **six**-field carrier
(`fitted`/`has_param`/`supplied` free, `param`/`names` every list of length ≤ 3
over a 3-term pool — so empty, singleton, repeated-term and order-swapped lists
all occur; `idx` forced positional when `fitted` by the representation invariant,
and taken over a gapped / shifted / doubled / empty representative when not, where
the field is inert and appears in the clauses only as `Old(ToSeq(self.idx))`):
**28 000 in-domain pre-states, 0 with more than one admitted outcome and 0 with
none**. A same-spec rival therefore has no observable freedom left to differ in.

That sweep is also the measurement of the repair. Re-run with the two numbering
clauses deleted — `Ensures(numbered_by_place(self.idx, self.names))` and the
`ToSeq(self.idx) == Old(ToSeq(self.idx))` frame legs, i.e. the spec as it stood
before — **every one of the 28 000 pre-states admits 40 outcomes** instead of one:
exactly the 40 candidate post-`idx` values, the mapping's numbering being wholly
unconstrained. The clauses therefore remove a 40-fold observable freedom on every
single reachable state; they are not decorative, and they narrow no domain (the
in-domain count is identical in both runs, 28 000).

The three exits **partition** the not-already-fitted case on read-only pre-state
(`Old(self.has_param)`, `Old(usable_terms(self.param))`), so every object the
query can be handed has exactly one modelled outcome and no input is left
unspecified: no list ⇒ `NotFittedError` with `not supplied`; a list that cannot
become a mapping ⇒ `UnusableTermsError` with the object untouched; a usable list
⇒ return it in order with `supplied`. The `Old(usable_terms(self.param))`
conjunct in the success clause is what forbids returning an unusable list instead
of rejecting it — that case must exit through the second `Exsures`. `param`
itself carries **no precondition**: an arbitrary ctor list is admissible, exactly
as in the repo.

The discriminating clauses read the **pre-state** of `has_param`
(`Old(self.has_param)`), because whether a list was supplied at construction is a
read-only input to this query — an impl must not be able to vacate the failure
clause (or satisfy the success consequent) by overwriting the flag.

The **Exsures** additionally pins the raise-path side effect `not self.supplied`.
On the genuinely-unfitted path the gold runs `_validate_vocabulary()`
unconditionally and, finding `vocabulary is None`, records `fixed_vocabulary_ =
False` (`text.py:299`) before `_check_vocabulary` raises (A4) — and the F2P test
checks this *first* (`assert_false(cv.fixed_vocabulary_)`, `test_text.py:547`).
A faithful refinement that raises WITHOUT recording `not supplied` (the pre-patch
`_check_vocabulary`-only path: `if not hasattr(self,'vocabulary_') and
self.vocabulary is not None: self._validate_vocabulary()`, which skips the call
on the unfitted object) verifies a weaker spec but does NOT resolve — it leaves
`fixed_vocabulary_` unset and fails that assertion with `AttributeError`. Pinning
`not self.supplied` on the raise path forbids that refinement.

The **frame** legs are equally load-bearing, and each is a fact about the real
patched routine, not a convenience:

* *already-fitted read path* (A6) — `Ensures(Implies(Old(self.fitted), ToSeq(self.names) == Old(ToSeq(self.names)) and ToSeq(self.idx) == Old(ToSeq(self.idx)) and self.supplied == Old(self.supplied) and ToSeq(Result()) == Old(ToSeq(self.names))))`. TRUE of the gold because the inserted guard `if not hasattr(self, 'vocabulary_')` is false there, so the sole writer of `vocabulary_`/`fixed_vocabulary_` (`_validate_vocabulary`, `text.py:296-299`) never runs and `_check_vocabulary` (`text.py:301-307`) only reads; the return comprehension (`text.py:998-999`) iterates the mapping without rebinding a key or a value. Load-bearing because `ToSeq(Result()) == ToSeq(self.names)` alone reads the **post**-state of the mapping: a rival that first wipes/permutes/truncates the learned mapping and then reports it satisfies that clause with both sides moved together. Such a rival refines to `if hasattr(self,'vocabulary_'): self.vocabulary_ = {}; return []` prepended to the gold hunk, and it does **not** resolve — F2P `test_feature_names` (`test_text.py:552`) gets `[]` where it asserts `['beer',…,'water']`, and P2P `test_count_vectorizer_max_features` / `test_count_binary_occurrences` regress. Pinning the pre-state of the mapping is what forbids that whole family.
* *the numbering of the reported mapping* (A8) — the unconditional `Ensures(numbered_by_place(self.idx, self.names))` plus the `ToSeq(self.idx) == Old(ToSeq(self.idx))` legs on the already-fitted path and in **both** `Exsures`. TRUE of the gold for the reason spelled out in A8: every repo site that can install a `vocabulary_` numbers it by place, and the patched query installs one only via `_validate_vocabulary`'s `enumerate`. Load-bearing because it is the *only* thing that closes the renumbering family, which the `names`-level clauses cannot see at all: the rival `if hasattr(self,'vocabulary_'): self.vocabulary_ = {t: 2*i for t, i in six.iteritems(self.vocabulary_)}` prepended to the gold hunk keeps the sorted-by-index key order — hence `Result()`, `self.names` and every clause above — bit-identical, while destroying the column each name addresses. It does **not** resolve: the test patch's own added assertion `for idx, name in enumerate(feature_names): assert_equal(idx, cv.vocabulary_.get(name))` (`test_text.py:573-574`) fails outright, and `transform`'s `feature_idx = vocabulary[feature]` (`text.py:817`) then writes out-of-range columns, regressing the P2P count tests. Three G-CONF mutants (`2*k`, `k+1`, and the fitted-path renumber) are exactly this family and are caught only by the `idx` component of the observation; six reject cases in `properties.py` — including `_HEAD_FITTED_RETURN_PARAM` and `_HEAD_FITTED_REORDER`, which keep both halves internally consistent so they cannot be dismissed as half-updated representations — fail verification on this clause.
* *read-only construction inputs* (A7) — `Ensures(self.has_param == Old(self.has_param))` and `Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))`, restated in both `Exsures` alongside `ToSeq(self.names) == Old(ToSeq(self.names))`, `ToSeq(self.idx) == Old(ToSeq(self.idx))` and (for `NotFittedError`) `not self.fitted`. TRUE of the gold because nothing on any path assigns `self.vocabulary`: `_validate_vocabulary` rebinds only its local `vocabulary` (`text.py:274`, `:277`, `:284`) and copies it into the distinct attribute `self.vocabulary_` (`text.py:297`); on the two rejection paths it raises at `text.py:283`/`:295` **ahead of** both writes at `:296-297`, so no attribute changes at all. Load-bearing because the discriminating clauses are stated over `Old(self.has_param)` / `Old(usable_terms(self.param))`: without the frames a rival could pollute the object on the way out of a failure exit (set `vocabulary_`, flip `fixed_vocabulary_`, renumber the mapping it leaves behind) while still satisfying the `Old(...)`-only conjuncts.

i.e. the unfitted-object failure is raised **only** when there is neither a
materialised mapping nor a construction-supplied list, and on that path the
object records that its vocabulary was **not** supplied at construction
(`not supplied`); whenever a ctor list was supplied to an unfitted object, the
query must instead **succeed**, materialise the mapping (`supplied` becomes
`True`), and return that list in order. This is exactly the issue's requirement
("`get_feature_names` should not raise `NotFittedError` if the vocabulary
parameter is provided") and the new F2P assertions (`feature_names ==
['beer',...]`, `cv.fixed_vocabulary_ is True` on the supplied object,
`cv.fixed_vocabulary_ is False` on the unfitted object).

`model_prepatch.py` keeps the spec **byte-identical** and uses the pre-patch
skeleton: it goes straight to the unusable check — `if not self.fitted: raise
NotFittedError()` — without the guarded materialisation (the pre-patch
`get_feature_names`, which only called `_check_vocabulary`). It **fails**
verification precisely on `Exsures(NotFittedError, ... not Old(self.has_param))`:
the prepatch raises `NotFittedError` whenever `not self.fitted`, including the
`has_param` case the spec forbids it on (Nagini reports `Assertion
(not Old(self.has_param)) might not hold`). This is the one
independently-observable fixed behaviour, so one prepatch suffices (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — inserting the **guarded on-demand materialisation** before the
unusable check — is modelled **directly** as the impl control flow (A2 guard →
A3 materialise / A3b reject / A4 raise), the very structure the prepatch removes. The
unchanged routine the new code calls (`_validate_vocabulary`) is modelled
**deeply** as `materialise_from_param`, an **A-reference** validated `==` the
real routine by G-AX (mapping.md §3.1) — there is **no consumed `@ContractOnly`
axiom**, hence no dead axiom. There is no axiom about the function under change.

## D. verify(model) ⇒ resolved

`get_feature_names` verifies only if (i) it does **not** raise on an unfitted
object that has a **usable** ctor list — it instead materialises and returns that
list in order with `supplied` set (A3 + the not-already-fitted postcondition),
(ii) it **does** raise on a genuinely-unfitted object **after recording `not
supplied`** (A4, the Exsures with `not self.supplied`) — mirroring the gold's
unconditional `_validate_vocabulary()` setting `fixed_vocabulary_ = False` before
the raise — and (iii) on an unfitted object whose ctor list cannot become a
mapping it reports the materialise step's own rejection and **writes nothing**
(A3b, the `UnusableTermsError` Exsures), mirroring `_validate_vocabulary` raising
at `text.py:283`/`295` ahead of its two assignments, and (iv) it leaves the
mapping it reports **numbered by its places** and, when that mapping was already
there, numbered exactly as it found it (A8) — so the names it returns still
address the columns they name. By R (attribute
presence ↔ `fitted`; ctor list ↔ `param`; the mapping ↔ the parallel pair
`(names, idx)`, its index-ordered terms **and** their indices; sorted
comprehension ↔ element-wise copy) the verified query equals the gold
`get_feature_names`: it calls the on-demand `_validate_vocabulary` exactly under
the `not hasattr(...,'vocabulary_')` guard and then returns the index-ordered
names, raising `NotFittedError` only on the truly-unfitted object and propagating
that call's own `ValueError` on a list it cannot turn into a mapping. By G-AX the
deep helper `materialise_from_param` equals the real `_validate_vocabulary` on the
list-vocabulary domain, and rejects-without-writing exactly outside it
(A-reference); by G-CONF the whole impl region equals the real patched function on
100 180 states including 11 372 in that rejection class, with the observation
carrying the mapping's **numbering** as well as its names on every one of them
(and four labelled probes confirming the two sides also agree on states the
representation invariant excludes). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
one audited (A-reference) callee — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: callee soundness (G-AX) and
refinement fidelity (this document, G-EQ).
