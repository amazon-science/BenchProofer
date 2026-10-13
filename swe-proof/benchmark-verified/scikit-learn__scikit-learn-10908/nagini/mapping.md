# mapping.md — scikit-learn__scikit-learn-10908

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 67d06b18c68ee4452768f8a1e868565dd4354abf`, states the type
abstraction, and gives the provenance of the unchanged callee whose effect the
deep helper models (validated by axiom_check.py / G-AX).

Repo file under change: `sklearn/feature_extraction/text.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `get_feature_names(self)` | `CountVectorizer.get_feature_names(self)` — `sklearn/feature_extraction/text.py:994` (body 994-999) | the modeled changed function: the feature-name query |
| `materialise_from_param(self)` | `VectorizerMixin._validate_vocabulary(self)` — `sklearn/feature_extraction/text.py:273` (the list-vocabulary branch, 278-297) | the UNCHANGED routine the query now calls on demand; builds `vocabulary_` from the constructor `vocabulary` and sets `fixed_vocabulary_ = True` |
| `Vectoriser.fitted` | the presence of the `vocabulary_` attribute on `self` — tested by `hasattr(self, 'vocabulary_')` (`text.py:953` in `transform`, and the guard the gold patch inserts at the head of `get_feature_names`, post-patch `text.py:996`) | whether the learned name→index mapping is materialised |
| `Vectoriser.has_param` | `self.vocabulary is not None` — the constructor `vocabulary` parameter (`_validate_vocabulary`, `text.py:274-275`) | whether a fixed list was supplied at construction |
| `Vectoriser.param` | the constructor `vocabulary` list (a sequence of terms) — `_validate_vocabulary`'s `for i, t in enumerate(vocabulary)` (`text.py:280`) | the supplied terms, in their given order |
| `Vectoriser.supplied` | `self.fixed_vocabulary_` — set `True` for a supplied vocabulary (`text.py:296`), `False` otherwise (`text.py:299`) | whether the object reports a fixed (construction-supplied) vocabulary |
| `Vectoriser.names` | the learned mapping `self.vocabulary_` viewed as its terms in ascending index order — i.e. the value `get_feature_names` returns: `[t for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` (`text.py:998-999`) | the index-ordered feature names (the *keys* half of the mapping) |
| `Vectoriser.idx` | the **values** of that same sorted view: `[i for t, i in sorted(six.iteritems(self.vocabulary_), key=itemgetter(1))]` — the index `self.vocabulary_[t]` each of those terms carries. Read wherever a term's column is addressed: `transform`'s `feature_idx = vocabulary[feature]` (`text.py:817`), `_sort_features`'s `vocabulary[term] = new_val` (`text.py:749-751`), `_limit_features`'s `vocabulary[term] = new_indices[old_index]` (`text.py:783-789`), and — decisively — the F2P assertion the test patch **adds** for the custom-vocabulary case, `for idx, name in enumerate(feature_names): assert_equal(idx, cv.vocabulary_.get(name))` (`test_text.py:573-574` post-test-patch) | the *numbering* half of the mapping: **which** index each reported name carries. `names` and `idx` run in parallel and together **are** `vocabulary_`, so a renumbering is a state change the model can express and the contract can forbid |
| `NotFittedError` *(user-defined exception)* | `sklearn.exceptions.NotFittedError`, raised by `check_is_fitted(self, 'vocabulary_', msg=...)` inside `_check_vocabulary` (`text.py:304`; `check_is_fitted`, `sklearn/utils/validation.py:859-860`) | the unfitted-object failure |
| `UnusableTermsError` *(user-defined exception)* | the `ValueError` `_validate_vocabulary` raises for a constructor list it cannot turn into a mapping: `ValueError("Duplicate term in vocabulary: %r" % t)` (`text.py:281-283`) and `ValueError("empty vocabulary passed to fit")` (`text.py:294-295`) | the materialise step's rejection of an unusable supplied list |
| `usable_terms(xs)` *(`@Pure`)* | the two acceptance conditions of `_validate_vocabulary`'s list branch: no term occurs twice (`if vocab.setdefault(t, i) != i: raise`, `text.py:280-283`) and the resulting map is non-empty (`if not vocabulary: raise`, `text.py:294-295`) | when a term list can serve as a name→index mapping |
| `places(n)` *(`@Pure`, spec-only)* | the index sequence `range(n)` that every numbering site in the file produces: `enumerate(vocabulary)` (`text.py:280`), `enumerate(sorted_features)` (`text.py:749`), `np.cumsum(mask) - 1` (`text.py:783`), and the index set `xrange(len(vocabulary))` the `Mapping` branch demands (`text.py:289-293`) | spec vocabulary: the first `n` places, in order |
| `numbered_by_place(idx, names)` *(`@Pure`, spec-only)* | `[i for t, i in sorted(vocabulary_.items(), key=itemgetter(1))] == list(range(len(vocabulary_)))` — i.e. `vocabulary_[names[k]] == k`. This is literally the F2P's added assertion `assert_equal(idx, cv.vocabulary_.get(name))` over `enumerate(feature_names)` (`test_text.py:573-574`), and it is the invariant the `Mapping` branch validates (`text.py:286-293`) | the mapping is numbered by place: the name reported at place `k` is the one the mapping sends to index `k` |

The gold patch (`text.py:994`) inserts, at the head of `get_feature_names`,
`if not hasattr(self, 'vocabulary_'): self._validate_vocabulary()` — i.e. the
guarded on-demand materialisation that `transform` already performs
(`text.py:953-954`) — before the existing `self._check_vocabulary()` call.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `hasattr(self, 'vocabulary_')` (the materialised-mapping presence test) | `self.fitted: bool` | attribute present ↔ `fitted == True`. (Modelled as an explicit boolean field because Nagini objects have a fixed field set; the dynamic-attribute test becomes a boolean flag.) |
| `self.vocabulary is not None` (constructor parameter present) | `self.has_param: bool` | a non-`None` constructor `vocabulary` ↔ `has_param == True`. |
| the constructor `vocabulary` list of terms (e.g. `['beer','burger',...]`) | `self.param: List[int]` | each distinct term ↔ a distinct `int` identifier; the list order is preserved (position = enumeration index). Term *strings* are opaque to the query — only their identity and order matter — so an `int` carrier is observationally identical (Nagini bans `str` indexing). The carrier is **unconstrained**: an arbitrary caller may pass any list, including an empty one or one repeating a term, and each such list has a model state. |
| `self.fixed_vocabulary_: bool` | `self.supplied: bool` | identical boolean. |
| the index-ordered feature-name list returned by `get_feature_names` | `self.names: List[int]` / `Result(): List[int]` | term `int` ids in ascending-index order; `Result()` is the same carrier. The F2P test compares with `assert_array_equal(['beer',...], feature_names)`, i.e. element-wise sequence equality — exactly `ToSeq(Result()) == ToSeq(self.param)` under the term-id bijection. |
| the mapping `self.vocabulary_` **as a whole** (a `dict` from term to index) | the parallel pair `(self.names, self.idx): (List[int], List[int])` | `vocabulary_ == {names[k]: idx[k] for k}`, with the pair listed in ascending `idx`. **This pair, not `names` alone, is the carrier of the mapping.** `names` alone is many-to-one on `vocabulary_` — `{'a':0,'b':1}` and `{'a':0,'b':7}` have the same index-ordered key list — so a carrier consisting of `names` only would make a renumbering unobservable, and any refinement of a *renumbering* implementation would verify against a spec that pins only `names`. Nagini has no `Dict` carrier that would let a term index a heap-allocated map, so the mapping is carried in its two halves; the `idx` half is the one that is otherwise lost. |
| `NotFittedError` (a real exception class) | the user-defined `NotFittedError(Exception)` | a builtin-exception `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so a user-defined stand-in is used; the F2P test asserts `assert_raises(ValueError, cv.get_feature_names)` on the genuinely-unfitted object (`NotFittedError` is a subclass of `ValueError` in sklearn), which corresponds to the modelled raise on `not fitted and not has_param`. |
| the `ValueError` of `_validate_vocabulary`'s list branch (`text.py:283` / `text.py:295`) | the user-defined `UnusableTermsError(Exception)` | same stand-in reason. The two failures are **distinct** model classes because they are distinct repo events on distinct inputs (no mapping *and* no list ⇒ `NotFittedError`; a supplied list that cannot become a mapping ⇒ this one), and `conformance_check.py` observes them separately (catching `NotFittedError` *before* `ValueError`, since sklearn makes the former a subclass of the latter). |

`X` / `raw_documents` do not appear: `get_feature_names` takes no data
argument; the only inputs are the object's own state.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `materialise_from_param` ↔ `_validate_vocabulary` (A-reference, NOT consumed)
**Callee:** `VectorizerMixin._validate_vocabulary` (`text.py:273-299`), the
**unchanged** routine. The patch does not modify it; it adds a guarded *call* to
it. For a list (non-`Mapping`, non-`set`) `vocabulary`, the routine builds
`vocab = {}; for i, t in enumerate(vocabulary): vocab.setdefault(t, i)` and then
sets `self.fixed_vocabulary_ = True; self.vocabulary_ = dict(vocab)`
(`text.py:279-297`). Therefore, for a **usable** list vocabulary — non-empty and
with no term listed twice, i.e. `usable_terms(self.param)`:

  * `vocabulary_[t] == i` for the term `t` at position `i`, so the
    index-ordered names `[t for t,i in sorted(items, key=index)]` equal the
    supplied list **in its original order**;
  * and those indices are *exactly the places* `0 … len-1`, in that order — the
    numbering half of the mapping, not just its key order. `setdefault(t, i)`
    over `enumerate(vocabulary)` assigns each surviving term its own enumeration
    position, and on a repetition-free list every position survives, so the
    sorted-by-index value list is `range(len(vocabulary))`. This is the half
    `names` alone cannot see (`{a:0,b:1}` and `{a:0,b:7}` share a key order) and
    the half the test patch newly asserts (`test_text.py:573-574`);
  * `fixed_vocabulary_` becomes `True`;
  * `hasattr(self, 'vocabulary_')` becomes `True`.

These four facts are exactly the `Ensures` of `materialise_from_param`
(`self.fitted`, `self.supplied`, `ToSeq(self.names) == ToSeq(self.param)`,
`numbered_by_place(self.idx, self.names)`). The
helper is modelled **deeply** (its effect spelled out) and is therefore an
**A-reference**: its effect is validated `==` the real `_validate_vocabulary`
out-of-band by `axiom_check.py` (G-AX), **not** consumed as a `@ContractOnly`
axiom. No `@ContractOnly` axiom appears in `model.py`; the proof depends only on
the helper's contract, which G-AX confirms against the real routine.

**Flag/precondition dependency:** the modelled equivalence holds for the
**list/sequence** vocabulary form that is **usable** — non-empty, no term listed
twice (the F2P case: a list of nine distinct food terms). That is exactly
`materialise_from_param`'s `Requires(usable_terms(self.param))`, so the helper's
domain and the real routine's acceptance set coincide rather than the former being
a convenience restriction of the latter. Outside that domain the real routine
raises instead of materialising (`text.py:283` duplicate, `text.py:295` empty),
and the **caller** models that outcome: `get_feature_names` leaves `param`
unconstrained, screens it with `usable_terms`, and exits through
`Exsures(UnusableTermsError, ...)` for the rest of the class — so an arbitrary
caller-supplied list is admissible at the top level and every such list has a
modelled outcome.

**Carrier boundary for the other two `vocabulary` forms**, stated precisely,
because `usable_terms` is the acceptance set of the **sequence** form only.
`self.param` is bound (§2) to the sequence (non-`Mapping`, non-`set`) constructor
`vocabulary` — the form the issue reports and the form the F2P test uses
(`vocab = ['beer', 'burger', …]`). The routine normalises or diverts the other two
forms *before* the branch this carrier models:

  * `set` — normalised by `vocabulary = sorted(vocabulary)` (`text.py:276-277`) and
    then handled by the very sequence branch modelled here, so such an input enters
    the carrier as `param = sorted(terms)`. It is repetition-free by construction,
    so on it `usable_terms(param)` reduces to non-emptiness — still exactly the
    routine's acceptance test (`text.py:294-295`).
  * `Mapping` — handled by a **different** branch (`text.py:285-293`) that screens
    the *indices*, not the terms: repeated indices (`text.py:287-288`) or an index
    set that is not exactly `0 … len-1` (`text.py:289-293`) are rejected. Mapping
    keys are unique, so `usable_terms` (non-empty, no repeated term) would accept
    e.g. `{'a': 0, 'b': 2}` where the real routine raises. A `Mapping` vocabulary
    is therefore **out of the `param` carrier**: `materialise_from_param`'s domain
    claim ("helper domain == real acceptance set") is asserted for the sequence
    form only, and the model neither claims nor is checked for the `Mapping`
    *entry* path.

    That same branch is, however, **the justification for the `numbered_by_place`
    representation invariant** on the *already-fitted* side, and it is load-bearing
    rather than an aside. `get_feature_names` requires
    `Implies(self.fitted, numbered_by_place(self.idx, self.names))`: not a
    convenience narrowing, but the statement that a `vocabulary_` this package can
    put on an object is numbered by its places. Every write site enforces it —
    the sequence branch by `enumerate` (`text.py:280`), the `Mapping` branch by
    literally validating that the index set is `0 … len-1` with no repeats
    (`text.py:286-293`), the learned path by `_sort_features`' `enumerate`
    renumbering (`text.py:749-751`) and `_limit_features`' `np.cumsum(mask) - 1`
    compaction (`text.py:783-789`). So the precondition excludes **no reachable
    state**, and `axiom_check.py`'s `check_every_mapping_is_numbered_by_place`
    *executes* those guards (four rejected numberings; an accepted permutation, a
    list vocabulary and a learned `vocabulary_` plain and under `max_features` /
    `min_df` / `max_df`, all observed positional) instead of arguing it in prose.
    `conformance_check.py` additionally reports four labelled probes showing model
    and repo **agree** on states outside the restriction, so it hides no divergence.

axiom_check.py fuzzes the list form (incl. order
sensitivity), exercises the empty and duplicate-term rejections **and the fact
that neither writes anything** (so the caller's rejection-exit state claim is
observed, not assumed), and covers the already-fitted / no-vocabulary boundaries,
so the helper's domain is honestly bounded on both sides.

**Soundness check (G-AX):** `axiom_check.py` constructs real `CountVectorizer`
objects and asserts: (a) for a freshly-constructed object with a list
`vocabulary`, `hasattr(cv,'vocabulary_')` is initially `False`, and after
`get_feature_names()` it is `True`, `cv.fixed_vocabulary_ is True`, and
`get_feature_names() == list(vocabulary)`; and — term by term, against
`cv.vocabulary_[term]` itself rather than against the order the names come back
in — `cv.vocabulary_[vocab[i]] == i` with `sorted(cv.vocabulary_.values()) ==
list(range(len(vocab)))` (the deep helper's four `Ensures`, the last being
`numbered_by_place`); (a′) the caller's representation-invariant premise, via
`check_every_mapping_is_numbered_by_place`: the `Mapping` branch still rejects a
gapped (`{'beer':0,'burger':2}`), a repeated (`{'beer':0,'burger':0}`), a 1-based
(`{'a':1,'b':2}`) and a trailing-gap (`{'a':0,'b':1,'c':3}`) numbering, while an
accepted permutation `{'beer':2,'burger':0,'celeri':1}` is positional and reports
`['burger','celeri','beer']`, and a learned `vocabulary_` is positional plainly
and under `max_features` / `min_df` / `max_df` (so `_sort_features`' and
`_limit_features`' renumberings actually run) — i.e. the `Implies(self.fitted,
numbered_by_place(...))` precondition describes the reachable states rather than
excluding any;
(b) the differential witness — on the **pre-patch** code path (calling
`_check_vocabulary` directly without materialising) a `NotFittedError` is raised
for the same object, while a genuinely-unfitted object (no `vocabulary`) raises
`NotFittedError` on both code paths; (c) every **unusable** list — empty, or with
a term listed twice — raises `ValueError` **and leaves the object untouched**
(`vocabulary_` still absent, `fixed_vocabulary_` still at its entry value, checked
with a sentinel), which is the exact boundary of `usable_terms` and the exact
state `Exsures(UnusableTermsError, ...)` claims. Imports only `sklearn` (the
package under test). Exit 0 iff every obligation holds.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned fuzz seed: `10908`** (module constant `SEED`; `N_FUZZ = 100_000`).

**Shadow.** The `# impl-start` / `# impl-end` regions of `model.py` —
`get_feature_names` and `materialise_from_param` — copied **verbatim** with only
the contract calls (`Requires`, `Ensures`, `Invariant`, `Assert`,
`MustTerminate`, `Acc`) and the `# invariants-start`/`-end` blocks removed; the
executable statements are byte-identical to `model.py`, branch order, the
`usable_terms` screen, the comments and all. No `PSeq` shim is needed — every
`ToSeq`/sequence term in `model.py` occurs inside a contract and is stripped, so
the runtime carrier is a plain `List[int]`. `model.py` declares no
`@ContractOnly` axiom. Its one module-level `@Pure` helper, `usable_terms`, is
copied over with its `Requires` stripped like any other contract, and its nested
`Forall` pair over `0 <= i < j < len(xs)` is spelled as the equivalent
comprehension over that same index range — the file's **only** transliteration,
called out in the script, because a `Forall` term is a static Viper construct and
cannot be executed; the predicate (non-empty, no term listed twice) is unchanged.
The two other module-level `@Pure` helpers, `places` and `numbered_by_place`, are
**spec-only**: neither has any occurrence in an impl region, so neither is copied
at all. Their executable counterpart `_is_numbered_by_place(idx, names)` —
`len(idx) == len(names) and list(idx) == list(range(len(names)))` — belongs to the
*harness*, where it screens generated states for restriction (2) and reads the real
object's numbering back; it is never part of the diffed shadow.

**Oracle.** The **real patched** `CountVectorizer.get_feature_names`
(§1: `sklearn/feature_extraction/text.py:994`), **called**, not transliterated.
The script asserts the gold patch is actually applied (`_patch_is_applied`), so a
pre-patch run reports an error instead of passing. The A-reference callee
`materialise_from_param` is realised in the shadow by the **real** unchanged
`VectorizerMixin._validate_vocabulary` (§3.1, `text.py:273`) — matching both
sibling bundles — with `fitted`/`supplied` read back off the real object rather
than hardcoded; additionally the verbatim copy of the helper's own impl region is
diffed against that same real routine on every supplied-list input, so the deep
body is checked here and not merely deferred to G-AX.

**Type bridge (§2 inverted).** `_TERMS[i]` is the concrete term string for the
opaque `int` id `i` (`_TERM_ID` inverts it; ids 0-8 are the F2P food terms). A
model state `(fitted, has_param, supplied, param, names, idx)` — six components,
the sixth being the numbering half of the mapping — becomes a real
`CountVectorizer` via `vocabulary=[_TERMS[t] for t in param]` when `has_param`
else `None`; when `fitted`, `vocabulary_ = {_TERMS[names[j]]: idx[j]}`, i.e. the
mapping is rebuilt with the model's **own** indices rather than with positional
ones, and `fixed_vocabulary_ = supplied`. Observation is the 4-tuple
`(outcome, fixed_vocabulary_, names-in-index-order, indices-in-index-order)`, so
the returned list, the recorded supplied-at-construction flag, the resulting index
**order** and the actual index **values** must all agree. The fourth component is
load-bearing and not decoration: `names` alone is many-to-one on `vocabulary_`
(`{a:0,b:1}` and `{a:0,b:7}` have the same index-ordered key list), so an
implementation that renumbers the mapping it reports is invisible to the first
three components — three of the fourteen mutants below do exactly that and are
caught only by this one. The verbatim helper diff likewise compares
`(names, idx, fitted, supplied)`, and `_is_numbered_by_place(idx, names)` is the
executable counterpart of the spec-only `places` / `numbered_by_place` pair (which
have no impl-region occurrence and so are not transliterated). Both modelled
failures are observed and **distinguished**: model
`NotFittedError` ↔ `sklearn.exceptions.NotFittedError` (`text.py:304`), model
`UnusableTermsError` ↔ `_validate_vocabulary`'s `ValueError` (`text.py:283` /
`text.py:295`) — the former is caught first, because sklearn makes
`NotFittedError` a `ValueError` subclass; `_check_failures_distinguishable`
asserts that ordering still separates them rather than trusting it.

**Inputs.** 180 boundary states covering all **four** impl branches — including
the exact F2P vocabulary, the `fixed_vocabulary_`-absent fresh object, singleton
and full-pool lists, reverse and shuffled index orders, stale-`names` states,
states taken from a real `fit_transform`, **empty and repeated-term supplied lists
in every flag combination (with and without stale `names`, and on an
already-fitted object where the list must be ignored entirely)**, and an
**exhaustive sweep of every list up to length 3 over a 3-term pool** — then
100 000 seeded fuzz states whose supplied lists are drawn **with replacement**, so
empty and repeating lists occur throughout. Recorded branch hits:
`unfitted-raise 21045`, `unusable-reject 11372`, `materialise 25459`,
`already-fitted 42304`. **Total 100 180.**

**Domain restrictions (two, from the frozen artifacts, documented in the script).**
Both are the two halves of one representation invariant on a *materialised
mapping*, and both are **executed** in-container rather than assumed:

  1. when `fitted`, `names` is a non-empty list of *distinct* ids — exactly
     `Requires(Implies(self.fitted, usable_terms(self.names)))`. Distinctness is
     structural (`vocabulary_` is a dict *keyed* by term); non-emptiness is a repo
     invariant, because no repo path produces a present-but-empty `vocabulary_`
     (all three assignment sites guard it: `text.py:294-297`, and `text.py:928` via
     `_count_vocab`'s `text.py:834`, plus `_limit_features`' "After pruning, no
     terms remain"), and that premise is checked by `_check_nonempty_invariant`.
  2. when `fitted`, the mapping is **numbered by place** — read in ascending index
     order its indices are exactly `0 … n-1`, i.e.
     `Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))`.
     Justified site by site in §3.1: the `Mapping` branch validates the index set
     is a bijection onto `range(len)` (`text.py:286-293`), the list/set branch
     numbers by `enumerate` (`text.py:280-283`), the learned path is renumbered by
     `_sort_features`' `enumerate` (`text.py:749-751`) and `_limit_features`'
     keep-mask `cumsum` (`text.py:783-789`). `_check_positional_invariant`
     *executes* five sub-checks of that premise (a gapped and a repeated-index
     `Mapping` must still be rejected; an accepted permutation must be positional;
     a real `fit_transform`, plain and under `max_features`, must yield
     `sorted(values) == range(n)`) and fails the gate if any stops holding.
     Restriction (2) **costs no impl path** — both `fitted` branches are reached by
     positionally numbered states, and the recorded branch/boundary counts are
     identical with and without it — but because the interesting question about a
     precondition is what it *hides*, four non-positional states (gapped,
     all-shifted, doubled, singleton-at-7) are run as **labelled probes**
     (`_numbering_probes`) and reported in the JSON: all four **AGREE**, the query
     reading only the mapping it reports. So (2) states which objects the repo can
     build; it is not cover for a divergence.

**`param` is not restricted at all** — the constructor vocabulary is an arbitrary
caller-supplied list, so empty and repeated-term lists are generated and diffed
like any other, which is what exercises the `UnusableTermsError` exit against the
real routine's `ValueError`.
One bridge exclusion sits on the model side: `supplied is None` realises the
model's always-present flag as an *absent* `fixed_vocabulary_`, admissible only
where the impl writes the flag before it can be observed (the unfitted-raise
path), not on the rejection path (no write there, on either side) nor on a fitted
object (the real query never touches the attribute). The sole unreached in-domain
path — the zero-trip copy loop — is exercised as a **labelled out-of-domain
probe** reported in the JSON (there the model returns `[]` while the real
`_check_vocabulary` raises `ValueError("Vocabulary is empty")`, a divergence no
repo path can witness and the precondition excludes).

**Capable of failing (mutation-tested).** Fourteen deliberately wrong shadows are
each caught and reported: dropping the on-demand materialisation (reverting the
gold patch's effect), **dropping the usable-list screen so an unusable list is
copied through instead of rejected**, **reporting the unfitted-object failure for
an unusable supplied list**, **writing the supplied flag on the rejection path**,
omitting the `self.supplied = False` write before the raise, an off-by-one copy
loop, reversed output order, `supplied=False` instead of `True`, sorting the
supplied terms instead of preserving order, a swapped branch guard, and a sorting
verbatim helper body — plus **three that attack the numbering half specifically**:
a verbatim helper that numbers the terms it materialises `2*k` instead of `k`, one
that numbers them from `1`, and an already-fitted path that renumbers the mapping
it reports while leaving the reported names untouched. Those three agree with the
real function on **every** component of the old three-part observation and on the
old `(names, fitted, supplied)` helper diff; each is caught only because the
numbering is now observed — the third by the observation's fourth component, the
first two by the helper diff's `idx` comparison — and the reported disagreement
shows `idx` as the only differing field, which is the direct evidence that the new
observable, not some incidental change, is what does the work. **14/14 caught.**

**Verdict:** `G-CONF=pass` — 100 180 Requires-satisfying states, 0
disagreements, with the numbering observed on every one of them; the four
`numbering_probes` outside restriction (2) also agree. stdlib + sklearn only;
exit 0 iff zero disagreements.
