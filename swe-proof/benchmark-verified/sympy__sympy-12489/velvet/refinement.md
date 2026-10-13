# refinement.md — sympy__sympy-12489

Operation-by-operation correspondence between `Solution.lean`'s impl regions and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep/opaque
model validated == the real callee, here by same-map cancellation in G-CONF), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the maps below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## 0. The change is ONE shared mechanism threaded through every construction site

The gold patch threads the runtime class through object construction instead of
hardwiring the base class. There is exactly ONE place where a produced object's
class is decided — the internal factory `_af_new`:

```
-    @staticmethod
-    def _af_new(perm):
-        p = Basic.__new__(Perm, perm)
+    @classmethod
+    def _af_new(cls, perm):
+        p = Basic.__new__(cls, perm)
```

and every construction site stops calling the module-global `_af_new` (bound to
the base class) and dispatches the factory through its own source class:
`self._af_new(...)` (instance sites, class = `type(self)`) /
`cls._af_new(...)` / `cls(...)` (classmethod sites, class = `cls`). **Values are
byte-identical** pre/post-patch; the only observable that changes is the runtime
**class** of constructed result objects.

`Solution.lean` models this faithfully and completely:

  * `buildVia(builtOn, value)` ≙ the post-patch `@classmethod` `_af_new`. Its
    behaviour-under-change is `out.classId = builtOn` (the result is an instance
    of the dispatched-on class); its value passthrough is `out.contents = value`.
  * EVERY threaded construction site is modeled as a thin operation that invokes
    `buildVia` passing its OWN dispatch class, with its own postcondition
    (`out.classId = self.classId` for instance sites, `out.classId = cls` for
    classmethod sites). The operation verifies ONLY if it threads correctly.

Modeling the shared factory PLUS every threaded site (rather than a representative
per structural shape) is what makes `verify ⟹ resolved` hold: see §G for the
in-container evidence that the FAIL_TO_PASS test's resolution depends on threading
at an interacting set of sites, so any unmodeled site is a soundness hole.

## A. `buildVia` — the factory `Permutation._af_new` (`permutations.py:944`)

| # | impl op (`buildVia`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `builtOn : ClassTag` | the `@classmethod` receiver `cls` of `_af_new` | R | the class the factory is dispatched on ↔ a class tag (mapping.md §2). |
| A2 | `value : List Nat` | the `perm` array argument | R | the array form ↔ `List Nat`; unchanged by the patch. |
| A3 | `return { contents := value, classId := builtOn }` | `p = Basic.__new__(cls, perm); … return p` | R + I | building a fresh object of the dispatched-on class `cls` ↔ `classId := builtOn` (R, mapping.md §2); the contents wrap is **I**. The pre-patch `Basic.__new__(Perm, perm)` (fixed base class) ↔ `classId := 0`, modeled in `Solution_prepatch.lean`, fails `out.classId = builtOn`. |

## B. Instance-method sites — `buildVia self.classId …`

Each instance-method site's gold tail is `return self._af_new(<value>)`. The
model is `let r ← buildVia self.classId (<contents map> …); return r`, with
postcondition `out.classId = self.classId` and `out.contents = <contents map>`.

| model symbol | gold site (hunk) | value map (A-reference + I) | class leg (R) |
|---|---|---|---|
| `composeProduct` | `__mul__` `return self._af_new(perm)` | `composeContents` ↔ `perm = [b[i] for i in a]+b[len(a):]` | `self.classId` ↔ `type(self)` |
| `powerSelf` | `__pow__` `return self._af_new(_af_pow(...))` | `powerContents` ↔ `_af_pow(self.array_form, n)` | `self.classId` |
| `reverseSelf` | `__invert__` `return self._af_new(_af_invert(...))` | `reverseContents` ↔ `_af_invert(self._array_form)` | `self.classId` |

(`divideSelf` is an instance site too, but it REFUSES part of its domain, so it is
tabled with the other refusing sites in §B3.)

Each value map is UNCHANGED by the patch (A-reference, opaque, value never
pinned; same map both sides — cancels in G-CONF). The class leg is the R-refined
class threading. `Solution_prepatch_instance.lean` models the pre-patch base-class
dispatch at the `composeProduct` site (`buildVia 0 …`) and fails
`out.classId = self.classId` exactly when the operand is a subclass — the
`type(p*q) == CustomPermutation` discriminator (G-DIFF).

### B2. The two PARTIAL instance sites — `Option Obj`, one order each

Two instance sites do not always construct anything: each walks its OWN
enumeration order and returns `None` for the operand that is LAST in that order.
Both facts are modeled, and each site gets its own value map and its own
definedness predicate.

| model symbol | gold site (hunk) | value map (A-reference + I) | definedness (A-reference) | class leg (R) |
|---|---|---|---|---|
| `stepSelf` | `next_lex` — `if i == -1: return None` … `return self._af_new(perm)` | `stepContents` ↔ the next-lex array | `stepDefined` ↔ `not (i == -1)`, i.e. the operand is not lexically last | `self.classId` ↔ `type(self)`, on the branch where a successor exists |
| `stepAltSelf` | `next_trotterjohnson` — `if m == 0: return None` … `return self._af_new(pi)` | `stepAltContents` ↔ the next-Trotter-Johnson array — a **different symbol** from `stepContents` | `stepAltDefined` ↔ `not (m == 0)`, i.e. the operand is not last in the alternative order | `self.classId`, on the branch where a successor exists |

Contract shape (both sites):

    ensures <pred> self.contents = true → out.map (·.classId) = some self.classId
    ensures <pred> self.contents = true → out.map (·.contents) = some (<map> self.contents)
    ensures <pred> self.contents = false → out = none

TWO DIFFERENT MAPS, not one. The two orders are different enumerations of the same
operands, so an operand's successor under one is not its successor under the
other. Re-derived against the worktree at `base_commit` with `patch.diff`
applied: `next_lex([0,2,1]) = [1,0,2]` while `next_trotterjohnson([0,2,1]) =
[2,0,1]`; the two orders disagree on 4 of 6 operands at size 3, 19 of 24 at size
4 and 105 of 120 at size 5. `conformance_check.py` transliterates BOTH orders
(rather than substituting a free stand-in for either) and measures the
disagreement on its own input set: 64511 rows where the two orders disagree on a
commonly-defined operand. An earlier revision of this table stated BOTH rows over
`stepContents`, which asserted the two orders agree everywhere; that is the
G-PANEL-2 faithfulness defect this section records as repaired, and the
`weak-step-alt-delegates` case in properties.py is the rival it made refutable.

INDEPENDENT PARTIALITY, not one predicate. Which operand is last differs between
the orders: `next_lex([2,1,0]) = None` while `next_trotterjohnson([2,1,0])` is an
object, and `next_trotterjohnson([1,0,2]) = None` while `next_lex([1,0,2])` is an
object. So the two definedness predicates are separate opaque symbols, and
neither is pinned to a concrete set of operands — only that where the order runs
out, NOTHING is produced (`out = none`), which is what the two
`...-fabricates-when-exhausted` rivals in properties.py violate.
`conformance_check.py` measures 3315 rows where the two orders disagree on which
operand is last, and each order running out on ~13.3k rows.

DOMAIN. These two sites are the ones whose real domain excludes the empty array
form: `next_lex` reads `perm[i + 1]` with `i = n - 2`, so `n = 0` raises rather
than returning `None`. The declared carrier for these two sites is therefore the
non-empty array forms (mapping.md §2), which is where the tests reach them; the
conformance diff excludes exactly those rows for exactly these two sites and no
others.

### B3. The six REFUSING sites — `Option Obj`, one acceptance test each

Six more sites do not construct anything for every input: each REFUSES a
sub-domain outright, abandoning the call rather than constructing an object with
substitute contents. Three do so EXPLICITLY (`raise ValueError(...)` in their own
body) and three IMPLICITLY, by raising `IndexError` out of an array-form helper
they index through or off the end of their own buffer. Three are instance sites and
three are classmethod sites; they are tabled together because they share the
contract shape, and the explicit/implicit distinction is not observable to a
caller (see mapping.md §2, the refusal row).

| model symbol | gold site (hunk) | value map (A-reference + I) | acceptance (R) | class leg (R) |
|---|---|---|---|---|
| `conjugateSelf` | `__xor__` — `if self.size != h.size: raise ValueError(...)` (`permutations.py:1432`) … `return self._af_new(a)` (`:1439`) | `conjugateContents` ↔ the conjugation array `a` | `sameExtent` ↔ `not (self.size != h.size)`, a transparent length equality (`size` is `len(_array_form)`, set at `:948`) | `self.classId` ↔ `type(self)`, on the branch where the pair is accepted |
| `bracketSelf` | `commutator` — `if len(b) != n: raise ValueError(...)` (`:2120`) … `return self._af_new([...])` (`:2128`) | `bracketContents` ↔ the commutator array | `sameExtent` ↔ `not (len(b) != n)` — the SAME test, so the same transparent symbol serves both | `self.classId` |
| `fromVectorFor` | `from_inversion_vector` — `except IndexError: raise ValueError(...)` (`:2734`) … `return cls._af_new(perm)` (`:2737`) | `fromVectorContents` ↔ the offset-vector array | `vectorValid` ↔ the vector's entries staying inside the shrinking pool `N`, i.e. the loop not raising — opaque | `cls` |
| `divideSelf` | `mul_inv` — `return self._af_new(_af_rmul(a, b))` (`:1237`), raising `IndexError` through `_af_rmul` (`:45`) | `divideContents` ↔ `_af_rmul(_af_invert(self), other)` | `fitsWithin other.contents self.contents` ↔ `len(b) ≤ len(a)`, a transparent and **asymmetric** length comparison | `self.classId`, on the branch where the pair is accepted |
| `foldOver` | `rmul_with_af` — `rv = cls._af_new(_af_rmuln(*a))` (`:1228`), raising through `_af_rmuln` (`:48-106`) | `foldContents` ↔ `_af_rmuln(*a)` | `foldDefined` ↔ the fold composing at all — opaque | `cls`, on the branch where the sequence is accepted |
| `rankedThirdFor` | `unrank_trotterjohnson` — `return cls._af_new(perm)` (`:2426`), raising at `:2420`/`:2424` | `rankedThirdContents` ↔ the TJ array | `rankedThirdDefined` ↔ the index being in range for THIS variant, which does not reduce it first — opaque | `cls`, on the branch where the index is accepted |

Contract shape (all six):

    ensures <guard> = true  → out.map (·.classId) = some <dispatch class>
    ensures <guard> = true  → out.map (·.contents) = some (<map> <args>)
    ensures <guard> = false → out = none

WHY THIS IS NOT AN IDEALIZATION (the first three). Their refusals are the literal
inputs the tests reach: `sympy/combinatorics/tests/test_permutations.py:104`
(`raises(ValueError, lambda: p ^ Permutation([]))` for a `p` of extent 7), `:109`
(`p.commutator(Permutation([]))`) and `:120`
(`Permutation.from_inversion_vector([0, 2])`) — all inside `test_Permutation`,
which is a PASS_TO_PASS test AND the body the FAIL_TO_PASS test
`test_Permutation_subclassing` re-runs with `Permutation := CustomPermutation`.
Re-derived against the worktree at `base_commit` with `patch.diff` applied on the
subclass the F2P test uses, all three raise. An earlier revision modeled these
three sites as TOTAL (`return (out : Obj)` with an unconditional
`out.contents = <map> …`), which asserted an object is constructed on exactly
those inputs; an implementation could satisfy every frozen `ensures` by dropping
the guard (padding the shorter operand and keeping the threaded construction) and
would then FAIL `test_Permutation`, so `verify ⟹ resolved` did not hold. That is
the G-PANEL-2 faithfulness defect this section records as repaired; the three
`...-builds-refused-input` rivals in properties.py are exactly that old shape, and
they are now rejected.

WHY THIS IS NOT A WEAKENING (the second three). `divideSelf`, `foldOver` and
`rankedThirdFor` were repaired in a second round, after a further G-PANEL-2 pass
found the SAME defect shape at three sites the first round did not reach. They
differ from the first three in one way that matters and one that does not.

What does not matter: their refusal is IMPLICIT. `mul_inv` has no guard of its own
— it raises `IndexError` out of `_af_rmul(a, b) = [a[i] for i in b]` when the right
operand's entries run past the inverted left operand; `rmul_with_af` raises out of
`_af_rmuln` (`ValueError` on the empty sequence, `IndexError` where successive
operands do not compose); `unrank_trotterjohnson` walks `perm[k] = j - 1` off the
end because, alone among the three index variants, it does not reduce its index
first. The caller cannot tell an implicit refusal from an explicit one — it gets no
object either way — so all six refine to the same carrier. The earlier revision of
mapping.md §2.1 asserted `mul_inv` and `rmul_with_af` were total precisely because
it looked for a `raise` in their own bodies; the sweep below is why that method was
abandoned.

What does matter: the tests do NOT reach the refused side of these three (they
exercise `unrank_trotterjohnson(4, i)` for `i` in `0..4` and `rmul_with_af` over
equal-extent operands — all accepted). So the argument for the repair is not "a
test asserts the refusal" but the plainer one: on the refused sub-domain GOLD
produces no object, so an obligation to produce one there is unsatisfiable by the
implementation the bundle is about. Removing an obligation gold cannot meet is not
a weakening of the spec against gold; and it is confined to that sub-domain,
because the class obligation still binds on every input the real operation accepts
(`<guard> = true → out.map (·.classId) = some <dispatch>` forces BOTH that an
object exists and that it carries the dispatch class). The rival that drops the
guard and constructs anyway is rejected at each of the three sites, and the rival
that dispatches the base class on the accepted branch still is — so neither
direction of the guard is free.

MEASURED, not reasoned. Each site was executed on the patched worktree over a
shared operand pool, on both `Permutation` and a subclass. The pool is stated so
each count is reproducible: the 10 array forms of extents `0..3` (`[]`, `[0]`,
`[0,1]`, `[1,0]` and the six of extent 3), hence 100 operand PAIRS, 1111 item
SEQUENCES of length `0..3`, and — for the index variant, which takes two numbers
rather than operands — the 65 pairs `extent 0..4 × rank 0..12`:

  * `divideSelf` refused 29 of the 100 pairs and accepted 71, and its refusal
    predicate is EXACTLY `len(other) > len(self)` — 0 mismatches over all 23716
    pairs of array forms of extents `0..5 × 0..5`. Because that IS a decidable
    length comparison, it is modeled TRANSPARENTLY, as `fitsWithin`. It is
    deliberately NOT `sameExtent`: the test is asymmetric, so reusing the
    symmetric symbol would refuse pairs gold accepts.
  * `foldOver` refused 530 of the 1111 sequences (1 `ValueError` on the empty
    one, 529 `IndexError`) and accepted 581. Its accepted set is NOT "non-empty
    with non-increasing extents" — 48 of 1111 disagree, e.g. the extent pattern
    `[0,1,0]` is accepted — so it is modeled OPAQUELY, as `foldDefined`.
  * `rankedThirdFor` refused 9 of the 65 index pairs and accepted 56, and its
    accepted set is NOT `rank < extent!` (33 of those same 65 pairs disagree with
    that predicate): every index is accepted at extents 0, 1 and 5, but only
    `0..3` at extent 2, `0..14` at extent 3 and `0..71` at extent 4 — not monotone
    in the extent and not any plain comparison of the two parameters. Modeled
    OPAQUELY, as `rankedThirdDefined`.

The same sweep checked the sites NOT repaired, which is what stops this from
becoming a blanket loosening: `unrank_lex` and `unrank_nonlex` reduce their index
(`rank % new_psize`, `r % ifac(n)`) and accept every one, so `rankedFor` and
`rankedAltFor` stay TOTAL. Three index variants, two total and one partial, is a
real asymmetry of the repo and the spec now states it.

WHAT IS AND IS NOT MODELED HERE. The modeled observable is that NO OBJECT IS
CONSTRUCTED on the refused sub-domain — which is what makes each site's class
obligation vacuous there, and what stops the spec from forcing a construction the
real code never performs. The refusal SIGNAL (a raised `ValueError` here, versus
the `return None` of §B2) is deliberately not modeled: those three guards are
UNCHANGED by `patch.diff` (their lines occur in the diff only as context, and at
`base_commit` they stand at `:1432`, `:2120`, `:2734` already), so the signal is
not the behaviour under change, and mapping.md §2 records the two different
refinements of `out = none` per site rather than letting one carrier stand for
both silently.

`conformance_check.py` transliterates all six guards AND their value computations
VERBATIM from the patched worktree, refusal branch included (including the three
array-form helpers the implicit refusals raise through — `_af_rmul`, `_af_rmuln`,
`_af_invert`), and its ORACLE lets them raise — so each modeled acceptance test is
measured against the real refusal on every row, rather than assumed by a total
stand-in (which is how the first three escaped the previous G-CONF: its
`conjugate_contents` was a free total map, so no size guard was ever executed, and
how the second three escaped the one after that: `divide_contents`,
`fold_contents` and `ranked_third_contents` were free total stand-ins for the same
reason). The oracle catches `IndexError` as well as `ValueError`, because for these
three the refusal arrives as the former and a ValueError-only catch would abort
the diff instead of recording a refusal. The counters are asserted non-zero per
site in both directions (some row refused, some row accepted); §F records them.

### B4. `generateFor` draws from the generator state

`Permutation.random` (`permutations.py:2754-2756`) is `perm_array =
list(range(n)); random.shuffle(perm_array); return cls._af_new(perm_array)`. Its
constructed value is therefore a map of the extent AND the ambient generator
state, not of the extent alone: successive draws at one extent differ. The model
takes a second binder and states `out.contents = generatedContents n entropy`. An
earlier revision stated `out.contents = generatedContents n`, which entails that
two constructions of one extent carry the SAME contents — a deterministic
generator, which this one is not. The clause is otherwise unchanged (the value is
opaque, an A-reference), and `conformance_check.py` executes the transliterated
generator and counts the rows where two draws at one extent differ (asserted
non-zero, §F), so the added binder is measured rather than asserted.

## C. Classmethod sites — `buildVia cls …`

Each classmethod site's gold tail is `return cls._af_new(<value>)` / `cls(...)`.
The model is `let r ← buildVia cls (<contents map> …); return r`, postcondition
`out.classId = cls`, `out.contents = <contents map>`. (`fromVectorFor`, `foldOver`
and `rankedThirdFor` are classmethod sites too, but each REFUSES part of its
domain, so all three are tabled with the other refusing sites in §B3.)

| model symbol | gold site (hunk) | value map (A-reference + I) | class leg (R) |
|---|---|---|---|
| `fromUnit` | `__new__` g-branch `return cls(a.array_form, size=size)` | `fromUnitContents` ↔ the resized array | `cls` |
| `extentFor` | `__new__` build `return cls._af_new(aform)` (+ the `cls._af_new(...)` dispatches in `__new__`) | `extentContents` ↔ the `aform`/`range`/`Cycle` array | `cls` |
| `generateFor` | `random` `return cls._af_new(perm_array)` | `generatedContents n entropy` ↔ the generated array, a map of the extent AND the generator state (§B4) | `cls` |
| `rankedFor` | `unrank_lex` `return cls._af_new(perm_array)` | `rankedContents` ↔ the lex-indexed array | `cls` |
| `rankedAltFor` | `unrank_nonlex` `return self._af_new(id_perm)` (classmethod receiver) | `rankedAltContents` ↔ the non-lex array | `cls` |
| `scheduleFor` | `josephus` `return cls(perm)` | `scheduleContents` ↔ the Josephus array | `cls` |

`Solution_prepatch_classmethod.lean` models the pre-patch base-class dispatch at
the `generateFor` site (`buildVia 0 …`) and fails `out.classId = cls` exactly when
invoked on a subclass — the `Permutation.random(2)` discriminator the test reaches
first under the monkeypatch (G-DIFF).

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
which class a constructed result is an instance of — is modeled **directly** as
the `classId` observation at the shared factory `buildVia` (`out.classId =
builtOn`) and threaded by each site's own `out.classId = self.classId` /
`out.classId = cls` postcondition. No `axiom` is shipped; G-AX is `skip`. The only
opaque symbols are the unchanged value maps (A-references).

## E. G-DIFF prepatch coverage

Three prepatches, byte-identical spec (`same_spec=True`), each failing for a
distinct discriminating reason:

  * `Solution_prepatch.lean` — the factory hardwires the base class
    (`buildVia` returns `classId := 0`): fails `out.classId = builtOn`
    (`0 = builtOn`). The root-cause `@staticmethod` → `@classmethod` bug.
  * `Solution_prepatch_instance.lean` — an instance site dispatches the base
    class (`buildVia 0 …`) instead of `self.classId`: fails
    `out.classId = self.classId`. The instance-shape call-site threading bug.
  * `Solution_prepatch_classmethod.lean` — a classmethod site dispatches the base
    class instead of `cls`: fails `out.classId = cls`. The classmethod-shape
    call-site threading bug.

## F. G-CONF coverage

`conformance_check.py` differential-tests all 17 modeled sites: for every site
the SHADOW (R/I transliteration: build via the factory dispatched on the source
class) must agree with the ORACLE (patch.diff's real construction dispatch) on the
result's runtime class and contents, over ≥10⁵ inputs across both structural
shapes and a subclass. 0 disagreements (seed 12489).

The six REFUSING sites (§B3) are compared on WHETHER an object is constructed
at all, on its class, and on its contents, with the real guards and the real value
computations transliterated verbatim and the ORACLE letting them raise. Their
non-degeneracy counters are asserted non-zero in BOTH directions — each site
refused some rows and accepted some rows — because a site that never refused
would leave its `out = none` clause untested (which is how the previous revisions'
total stand-ins hid both rounds of this defect), and a site that never accepted
would leave its class/contents clauses untested. Measured on the shipped input set
(seed 12489), refused / accepted rows of 100012: `conjugateSelf` 92243 / 7769,
`bracketSelf` 92243 / 7769 (the two extents are drawn independently, so most fuzz
rows differ; the boundary rows and the matching-extent draws are accepted),
`divideSelf` 46188 / 53824, `fromVectorFor` 42331 / 57681, `foldOver` 46760 /
53252, `rankedThirdFor` 9555 / 90457. The fold's refused side includes the EMPTY
sequence, reached on the rows whose left operand is empty. The generator
state is measured too: the transliterated `random` body is executed twice per row
at one extent and the differing rows are counted, non-zero (§B4). Four more
deliberately wrong variants of this check were each measured to FAIL (exit 1),
each on a different leg: modeling `conjugateSelf` as TOTAL with a free stand-in
value — the shape that let this defect escape — trips its refusal counter; a
modeled extent guard of `len(a) >= len(b)` at `bracketSelf` trips the existence
leg against the real refusal (`bracketSelf-EXISTENCE DISAGREE: shadow=none
oracle=some self=[] other=[3, 0, 1, 2]`); treating every offset vector as
well-formed trips `fromVectorFor`'s refusal counter; and dropping the
`random.shuffle` from the transliterated generator trips the generator-state
counter.

The two PARTIAL sites (§B2) are additionally compared on WHETHER an object is
produced at all, and their two value maps are the only ones NOT instantiated by a
free stand-in: both successor orders are transliterated from the patched worktree,
so the diff also measures the two facts the repaired spec relies on — 64511 rows
where the orders disagree on a commonly-defined operand, 3315 rows where they
disagree on which operand is last, and ~13.3k rows per order where the order runs
out. Those counters are asserted non-zero (a zero is a FAIL, not a silent pass),
and the check itself was measured live: an oracle minting the base class at the
partial sites, a shadow ignoring exhaustion, and a shadow serving the lexical
successor at the alternative-order site each make it exit 1.

## G. verify(Solution) ⇒ resolved — and why modeling every site is necessary

In-container site-isolation against the eval image
`sweb.eval.x86_64.sympy_1776_sympy-12489` (testbed env), applying the gold patch
then reverting ONE site at a time to base-class dispatch:

  * the first three refusals of §B3 are reached by the F2P test itself: its body
    (the re-run `test_Permutation`) asserts each of them at
    `sympy/combinatorics/tests/test_permutations.py:104`, `:109` and `:120`, so a
    model asserting an object is constructed there is unsound even though the
    guards themselves are untouched by the patch — the spec would admit an
    implementation that removes them;
  * the other three refusals of §B3 (`divideSelf`, `foldOver`, `rankedThirdFor`)
    are not asserted by a test, but gold produces no object on their refused
    sub-domain either, so an obligation to produce one there is unsatisfiable by
    gold — the direction of unfaithfulness is spec-too-strong, and the repair
    removes exactly that and nothing on the accepted sub-domain, where every class
    obligation still binds. `verify ⟹ resolved` is unaffected: the F2P and P2P
    tests only ever reach these three on inputs they accept;
  * reverting any single one of `__new__`, `__mul__`, `__pow__`, `__invert__`,
    `__xor__`, `unrank_nonlex`, `commutator`, `random` FAILS the FAIL_TO_PASS test
    `test_Permutation_subclassing` (these are individually required);
  * the remaining threaded sites are not individually required, BUT once several
    are un-threaded together, additional sites (e.g. `from_inversion_vector`)
    become required — the required set has non-trivial interaction structure.

So a spec that models only a representative per structural shape (the two prior
passes: 1 site, then 5 sites) is **unsound**: a verifying model leaves some
test-reached site un-threaded, refining to a partial patch that does NOT resolve.
The two prior re-audits caught exactly this — the 5-site model left `__xor__`
(line 99) and `from_inversion_vector` (line 117) un-threaded.

This bundle closes the hole by modeling **every site the gold patch threads**
(the complete list of `_af_new`/`cls(...)`/`self.X(...)` dispatches in
`patch.diff`; post-gold there are NO remaining base-class construction sites —
verified by grep over the patched file). Each modeled site verifies ONLY if it
threads its source class into `buildVia`. Therefore a model satisfying this spec,
refined by the maps above, threads the runtime class through EVERY construction
site — i.e. it is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE confirmed: all-sites-threaded passes; factory-only and every
partial patch fail).

The one trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is no
axiom soundness obligation (no consumed axiom; G-AX skip).
