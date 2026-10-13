# mapping.md — sympy__sympy-12489

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = aa9780761ad8c3c0f68beeef3a0ce5caac9e100b`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), and records the pinned
fuzz seed.

Repo file under change: `sympy/combinatorics/permutations.py`.

## 0. The change is ONE shared construction mechanism, threaded through every site

The gold patch is a single coherent **object-model refactor**. There is exactly
ONE place where the produced object's class is decided: the internal factory
`_af_new`. Pre-patch it is a `@staticmethod` that always builds
`Basic.__new__(Perm, perm)` — `Perm` is hardwired to the base class. Post-patch
it becomes a `@classmethod` building `Basic.__new__(cls, perm)`, so the produced
object is an instance of the class the factory is **dispatched on**. In addition,
every internal construction site stops calling the module-global `_af_new`
(which, being bound to the base class, would still produce the base class) and
instead dispatches the factory through its own source class:
`self._af_new(...)` (instance-method sites, source class = `type(self)`),
`cls._af_new(...)` / `cls(...)` (classmethod sites, source class = `cls`).

The **values produced are byte-identical** pre/post-patch; the *only* observable
that changes is the **runtime class** of constructed result objects — a
(possibly derived) operand's / invoked-on class is preserved instead of being
forced to the base class.

`Solution.lean` models this faithfully. It declares ONE shared primitive,
`buildVia(builtOn, value)` (≙ the post-patch `@classmethod` `_af_new`), whose
behaviour-under-change is `out.classId = builtOn` (the result is an instance of
the class it is dispatched on). Every modeled construction site is a thin
operation that **invokes `buildVia` passing its OWN dispatch class** and whose
own postcondition (`out.classId = self.classId` for instance sites,
`out.classId = cls` for classmethod sites) therefore holds ONLY if it threads
correctly. This pins the *whole* family together: the factory AND the dispatch
threading at every site, which is exactly the gold change.

### Why model EVERY threaded site (not a representative per shape)

The FAIL_TO_PASS test `test_Permutation_subclassing` monkeypatches
`Permutation := CustomPermutation` and re-runs the **entire** `test_Permutation()`
body, exercising an interacting set of construction sites. In-container site
isolation (driven against the eval image; see refinement.md §G) shows the test's
resolution depends on threading at MANY sites with non-trivial interaction:
individually-required sites are `__new__`, `__mul__`, `__pow__`, `__invert__`,
`__xor__`, `unrank_nonlex`, `commutator`, `random`, and additional sites
(e.g. `from_inversion_vector`) become required once others are also un-threaded.
Modeling only a representative per structural shape is therefore unsound — a
verifying model would leave some test-reached site un-threaded and fail to
resolve (the defect the two prior passes hit). The robust sound choice is to
model **every site the gold patch threads**, so that a verifying full model
threads every site and is the gold patch.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildVia (builtOn) (value)` | `Permutation._af_new` (post-patch `@classmethod`, `permutations.py:945`, `Basic.__new__(cls, perm)`) | the SHARED construction primitive; result is an instance of the dispatched-on class `builtOn` |
| `composeProduct (self) (other)` | `Permutation.__mul__` — `permutations.py:1304` (`return self._af_new(perm)`) | binary product; result class = `type(self)` |
| `powerSelf (self) (n)` | `Permutation.__pow__` — `permutations.py:1347` (`return self._af_new(...)`) | integer power; result class = `type(self)` |
| `reverseSelf (self)` | `Permutation.__invert__` — `permutations.py:1526` (`return self._af_new(...)`) | inverse; result class = `type(self)` |
| `conjugateSelf (self) (other)` | `Permutation.__xor__` — the extent guard at `permutations.py:1432` (`if self.size != h.size: raise ValueError("The permutations must be of equal size.")`) and the tail at `:1439` (`return self._af_new(a)`) | conjugation, **REFUSING**: a pair of operands of DIFFERING extent is refused outright and NO object is constructed for it; on an accepted pair the result class = `type(self)`. Returns `Option Obj`; its value map is `conjugateContents`, its acceptance test the transparent `sameExtent` |
| `stepSelf (self)` | `Permutation.next_lex` — `permutations.py:1636` (`if i == -1: return None` … `return self._af_new(perm)`) | lexical successor, **PARTIAL**: `None` for the operand that is last in lexical order, else result class = `type(self)`. Returns `Option Obj`; its value map is `stepContents`, its definedness predicate `stepDefined` |
| `divideSelf (self) (other)` | `Permutation.mul_inv` — the refusal is IMPLICIT, raised through `_af_rmul(a, b)` at `permutations.py:1237` (`return [a[i] for i in b]`, `:45`), and the tail is the same line (`return self._af_new(...)`) | left-divide, **REFUSING** on an ASYMMETRIC test: the value indexes the LEFT operand's inverse at the RIGHT operand's entries, so a right operand of GREATER extent raises `IndexError` and no object is constructed; on an accepted pair the result class = `type(self)`. Returns `Option Obj`; its value map is `divideContents`, its acceptance test the transparent `fitsWithin other.contents self.contents` |
| `bracketSelf (self) (other)` | `Permutation.commutator` — the extent guard at `permutations.py:2120` (`if len(b) != n: raise ValueError("The permutations must be of equal size.")`, where `n = len(self.array_form)`) and the tail at `:2128` (`return self._af_new(...)`) | commutator, **REFUSING** on the same extent test as `conjugateSelf`: a pair of differing extents produces no object at all; on an accepted pair the result class = `type(self)`. Returns `Option Obj`; its value map is `bracketContents`, its acceptance test `sameExtent` |
| `stepAltSelf (self)` | `Permutation.next_trotterjohnson` — `permutations.py:2484` (`if m == 0: return None` … `return self._af_new(pi)`) | alternative-order successor, **PARTIAL** and over its OWN order: `None` for the operand that is last in *that* order, else result class = `type(self)`. Returns `Option Obj`; its value map is `stepAltContents` (a DIFFERENT symbol from `stepSelf`'s — the two orders disagree on 4 of 6 operands at size 3, 19 of 24 at size 4, 105 of 120 at size 5), its definedness predicate `stepAltDefined` |
| `foldOver (cls) (items)` | `Permutation.rmul_with_af` — `permutations.py:1232` (`@classmethod`, `cls._af_new(...)`); the refusal is raised through `_af_rmuln(*a)` (`:48-106`: `raise ValueError` on the empty sequence, `IndexError` where successive operands do not compose) | fold over a sequence of operands, **REFUSING**: a sequence it cannot compose (the EMPTY one among them) yields no object; on an accepted sequence the result class = `cls`. Returns `Option Obj`; its value map is `foldContents`, its acceptance test the opaque `foldDefined` |
| `fromUnit (cls) (a) (b)` | the `__new__` g-branch `cls(a.array_form, size=size)` — `permutations.py:868` | coerce-and-rebuild; result class = `cls` |
| `extentFor (cls) (size)` | the `__new__` build dispatches `cls._af_new(...)` / `return cls._af_new(aform)` — `permutations.py:862,930` | size-parameterized construction in `__new__`; result class = `cls` |
| `generateFor (cls) (n) (entropy)` | `Permutation.random` — `permutations.py:2754-2756` `@classmethod` (`perm_array = list(range(n)); random.shuffle(perm_array); return cls._af_new(perm_array)`) | generation from the ambient generator; result class = `cls`. The constructed value is a map of the extent AND the generator state (`generatedContents n entropy`), because `random.shuffle` draws from that state: successive draws at one extent differ, so the value is NOT a function of `n` alone |
| `rankedFor (cls) (size) (rank)` | `Permutation.unrank_lex` — `permutations.py` `@classmethod` (`cls._af_new(perm_array)`) | construction-by-index; result class = `cls` |
| `rankedAltFor (cls) (n) (r)` | `Permutation.unrank_nonlex` — `permutations.py:1668` (`self._af_new(id_perm)`, classmethod receiver) | second index variant; result class = `cls` |
| `rankedThirdFor (cls) (size) (rank)` | `Permutation.unrank_trotterjohnson` — `permutations.py:2430` (`@classmethod`, `cls._af_new(perm)`); the refusal is raised at `:2420`/`:2424` (`perm[j - k - 1] = j - 1` / `perm[k] = j - 1`), which this variant reaches WITHOUT reducing `rank` into range first | third index variant, **REFUSING**: an out-of-range index walks the assignment off the end (`IndexError`) and no object is constructed; on an accepted index the result class = `cls`. Returns `Option Obj`; its value map is `rankedThirdContents`, its acceptance test the opaque `rankedThirdDefined`. Contrast `rankedFor`/`rankedAltFor`, which DO reduce (`rank % new_psize`, `r % ifac(n)`) and are therefore total |
| `fromVectorFor (cls) (vec)` | `Permutation.from_inversion_vector` — the validity refusal at `permutations.py:2734-2735` (`except IndexError: raise ValueError("The inversion vector is not valid.")`) and the tail at `:2737` (`return cls._af_new(perm)`) | construction from an offset vector, **REFUSING**: an ill-formed vector (one whose successive entries leave the shrinking pool of remaining positions) describes no object and none is constructed for it; on a well-formed vector the result class = `cls`. Returns `Option Obj`; its value map is `fromVectorContents`, its acceptance test the opaque `vectorValid` |
| `scheduleFor (cls) (m) (n) (s)` | `Permutation.josephus` — `permutations.py` `@classmethod` (`cls(perm)`) | scheduling construction; result class = `cls` |
| `Obj.classId : ClassTag` | the runtime class (`type(...)`) of an operand / result object | which class an object is an instance of (base vs a user subclass) |
| `Obj.contents : List Nat` | the operand's `_array_form` (the permutation array) | the ordered value contents of the object |
| `generatedContents : Nat → Nat → List Nat` | `random`'s generated `perm_array` — a value of the extent AND the ambient generator state (`random.shuffle`), `permutations.py:2754-2755` | the unchanged generation, opaque in both arguments. The second binder is what stops the spec from entailing that two draws of one extent agree; `conformance_check.py` executes the real generator and measures that they do not |
| each other `*Contents : … → List Nat` | the UNCHANGED array-form value computation at the corresponding site (e.g. `composeContents` ↔ `perm = [b[i] for i in a] + b[len(a):]`, `reverseContents` ↔ `_af_invert`, `powerContents` ↔ `_af_pow`, etc.) | the unchanged per-site value computation (A-reference, opaque, value never pinned). **One symbol per site**: in particular `stepContents` ↔ the next-lex array and `stepAltContents` ↔ the next-Trotter-Johnson array are two different symbols for two different orders |
| `sameExtent (a b : List Nat) : Bool` (a transparent `def`, `a.length == b.length`) | the extent test both refusing pair sites apply before constructing anything: `self.size != h.size` in `__xor__` (`permutations.py:1432`) and `len(b) != n` in `commutator` (`:2120`). `size` is `len(_array_form)` (the factory sets `p._size = len(perm)`, `:948`), so the real test IS array-form length equality | "this pair of operands is accepted at all". Concrete and decidable rather than opaque, because it is a settled length comparison, not one of the unchanged value computations; it is UNCHANGED by the patch (both hunks' guard lines are context) |
| `vectorValid : List Nat → Bool` | "this offset vector describes an object at all" — the negation of `from_inversion_vector`'s refusal (`except IndexError: raise ValueError`, `permutations.py:2734`): the vector's successive entries must stay inside the shrinking pool `N` of remaining positions | the (unchanged) well-formedness test of the offset vector, opaque: the spec pins WHERE nothing is constructed without pinning WHICH vectors those are |
| `fitsWithin (inner outer : List Nat) : Bool` (a transparent `def`, `inner.length ≤ outer.length`) | the IMPLICIT domain of `mul_inv`: `_af_rmul(a, b) = [a[i] for i in b]` indexes the inverted LEFT operand at the RIGHT operand's entries, and for array forms those entries are exactly `0 … len(b)-1`, so the call succeeds precisely when `len(b) ≤ len(a)`. Re-derived by executing the patched callee: 0 mismatches with this predicate over all extent pairs `0..5 × 0..5` | "this left-divide pair is accepted at all". Concrete and decidable rather than opaque, because it IS a settled length comparison. Deliberately a SEPARATE symbol from `sameExtent`: the test is ASYMMETRIC (a shorter right operand is accepted, a longer one refused), so reusing the symmetric symbol would be wrong in both directions |
| `foldDefined : List (List Nat) → Bool` | "this sequence composes at all" — the negation of `_af_rmuln`'s refusals (`raise ValueError` on the empty sequence, `IndexError` where an operand indexes past the next). Opaque because the real accepted set is NOT a length ordering: measured, `[[1,0],[0]]` is accepted while `[[0],[1,0]]` is refused, and 48 of 1111 sequences disagree with a "non-empty and non-increasing extents" predicate | the (unchanged) composability test of the fold, opaque: the spec pins WHERE nothing is constructed without pinning WHICH sequences those are |
| `rankedThirdDefined : Nat → Nat → Bool` | "this index describes an object at all" for the Trotter-Johnson variant — the negation of the off-the-end assignment at `permutations.py:2420`/`:2424`. Opaque because the accepted set is NOT `rank < extent!` and not monotone in the extent: measured, every index is accepted at extents 0, 1 and 5, but only `0..3` at extent 2, `0..14` at extent 3 and `0..71` at extent 4 (33 of the 65 pairs `extent 0..4 × rank 0..12` disagree with `rank < extent!`) | the (unchanged) in-range test of this one index variant, opaque |
| `stepDefined` / `stepAltDefined : List Nat → Bool` | "this operand HAS a successor in this order" — the negation of the `return None` guard of `next_lex` (`i == -1`) and of `next_trotterjohnson` (`m == 0`) respectively | the (unchanged) exhaustion test of each order, opaque and INDEPENDENT per order: which operand is last differs between the two orders (e.g. at size 3 the lexically-last operand is `[2,1,0]` while the alternative order's last is `[1,0,2]`) |
| `out : Obj` | the returned object of each modeled method | the constructed result: `out.classId` = its runtime class, `out.contents` = its array form |

No callee is consumed as a contract. The factory `_af_new` is modeled DIRECTLY
as `buildVia` (its sole behaviour-under-change — "the result is an instance of
the class it is dispatched on" — IS the `out.classId = builtOn` postcondition),
not axiomatized. Each value-level computation is modeled deeply as an opaque
total map and is an **A-reference** (the same map is applied on both sides; its
concrete result is never pinned), not a consumed axiom.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| runtime class of an object (`type(p)`) | `ClassTag` (`Nat`) | each distinct Python class ↔ a distinct tag; the base class ↔ tag `0`, a user subclass ↔ a distinct nonzero tag. Equality of tags ↔ `type(x) is type(y)`. Only equality is relied upon. |
| the class a classmethod is invoked on (`cls`) | `ClassTag` (`Nat`) | the receiver class of a `@classmethod` ↔ a class tag; `cls = type(receiver)`. |
| an object's `_array_form` (`list[int]`) | `List Nat` | the ordered array form; `len` ↔ `.length`, indexing ↔ `getElem`, entries are non-negative `Nat`. |
| `_af_new(perm)` dispatched on class `K` (post-patch `@classmethod`, `Basic.__new__(K, perm)`) | `buildVia K perm` → `{ contents := perm, classId := K }` | building a fresh object of the dispatched-on class ↔ `out.classId = builtOn`. |
| `self._af_new(...)` (instance site) | site method calls `buildVia self.classId …` | building via the factory dispatched on the LEFT operand's class ↔ `out.classId = self.classId`. |
| `cls._af_new(...)` / `cls(...)` (classmethod site) | site method calls `buildVia cls …` | building via the factory dispatched on the invoked-on class ↔ `out.classId = cls`. |
| each unchanged array-form value computation | the matching opaque `*Contents` map | the unchanged value computation ↔ `out.contents = *Contents …`; opaque (value never pinned), the SAME map on both sides. |
| a construction method that returns `None` for some operands (`next_lex`, `next_trotterjohnson`) | `Option Obj` result | "no object is produced" ↔ `out = none`; "an object is produced" ↔ `out = some o`, with `o.classId` / `o.contents` read through `out.map (·.classId)` / `out.map (·.contents)`. The definedness test itself is the matching opaque `*Defined` predicate of that order, so the spec pins WHERE nothing is produced without pinning WHICH operands those are. |
| a construction method that REFUSES some inputs by ABANDONING the call — explicitly (`__xor__` / `commutator` on a pair of differing extents, `from_inversion_vector` on an ill-formed vector, each `raise ValueError(...)`) or IMPLICITLY, by raising `IndexError` out of an array-form helper it indexes through (`mul_inv` through `_af_rmul`, `rmul_with_af` through `_af_rmuln`, `unrank_trotterjohnson` off the end of its own buffer) | `Option Obj` result, with `out = none` on the refused sub-domain | "no object is constructed for this input" ↔ `out = none`; "an object is constructed" ↔ `out = some o`, read through `out.map (·.classId)` / `out.map (·.contents)`. The acceptance test itself is `sameExtent` or `fitsWithin` (transparent) or `vectorValid` / `foldDefined` / `rankedThirdDefined` (opaque). An IMPLICIT refusal refines to the same carrier as an explicit one, because the observable is the same: the caller gets no object. Which exception class surfaces (`ValueError` vs `IndexError`) is not modeled for the same reason the message is not. NOTE the difference from the successor row above: there `none` refines a real `return None`, here it refines a refusal that abandons the call with an error. What is modeled at both is the same observable — that NO object is constructed, so the class obligation says nothing there and the spec cannot force a construction the real code never performs. WHICH signal accompanies the refusal is not modeled, deliberately: those three guards are UNCHANGED by `patch.diff` (their lines appear only as context), so the signal is not the behaviour under change, while the absence of a constructed object is what makes the modeled class obligation vacuous on that sub-domain. The same holds of the three IMPLICIT refusals: the helper lines they raise through (`_af_rmul` `:45`, `_af_rmuln` `:48-106`, the two `perm[...] = j - 1` assignments at `:2420`/`:2424`) are untouched by `patch.diff` |
| the ambient pseudo-random generator state that `random` draws from (`random.shuffle`) | an extra `entropy : Nat` binder, fed to `generatedContents n entropy` | the generator state at the moment of the draw ↔ a value binder; only that the constructed value MAY depend on it is relied upon (the value itself is never pinned), which is what makes a state-independent generator a different function rather than an admissible reshape |
| the operand reaching `next_lex` / `next_trotterjohnson` | non-empty `List Nat` | these two are the sites whose real domain excludes the empty array form (`next_lex` reads `perm[i + 1]` with `i = n - 2`, so `n = 0` raises rather than returning `None`); the modeled carrier for these two sites is the non-empty array forms, which is where the tests reach them. |

### 2.1 Per-site domain: which inputs each modeled site accepts

Every modeled site is TOTAL on its carrier except the eight below, and for each of
those the spec carries an explicit clause pinning that nothing is constructed
outside the accepted sub-domain. Each guard is quoted from the worktree at
`base_commit` with `patch.diff` applied, and each is UNCHANGED by the patch (the
guard lines appear in the diff only as context, if at all).

The list was built by EXECUTING every modeled site on the patched worktree over a
shared operand pool, on both `Permutation` and a subclass, and recording which
inputs produce no object — not by grepping for `raise`. That distinction is what an
earlier revision of this table got wrong: it listed only the five sites with an
explicit `raise`/`return None` in their own body and asserted the rest total,
missing the three that refuse by raising THROUGH a helper they index into or off
the end of their own buffer.

| site | real guard (verbatim) | modeled as |
|---|---|---|
| `conjugateSelf` (`__xor__`, `:1432`) | `if self.size != h.size: raise ValueError("The permutations must be of equal size.")` | `sameExtent self.contents other.contents = false → out = none` |
| `bracketSelf` (`commutator`, `:2120`) | `if len(b) != n: raise ValueError("The permutations must be of equal size.")` | `sameExtent self.contents other.contents = false → out = none` |
| `fromVectorFor` (`from_inversion_vector`, `:2734`) | `except IndexError: raise ValueError("The inversion vector is not valid.")` | `vectorValid vec = false → out = none` |
| `divideSelf` (`mul_inv`, `:1237` → `_af_rmul`, `:45`) | `return [a[i] for i in b]` — no explicit guard; raises `IndexError` when `b` has an entry outside `a`, i.e. when `len(b) > len(a)` | `fitsWithin other.contents self.contents = false → out = none` |
| `foldOver` (`rmul_with_af`, `:1228` → `_af_rmuln`, `:48-106`) | `if m == 0: raise ValueError("String must not be empty")`, and `[a[i] for i in b]` raising `IndexError` where successive operands do not compose | `foldDefined items = false → out = none` |
| `rankedThirdFor` (`unrank_trotterjohnson`, `:2420`/`:2424`) | `perm[j - k - 1] = j - 1` / `perm[k] = j - 1` — reached without reducing `rank` into range, so an out-of-range index raises `IndexError` | `rankedThirdDefined extent rank = false → out = none` |
| `stepSelf` (`next_lex`, `:1636`) | `if i == -1: return None` | `stepDefined self.contents = false → out = none` |
| `stepAltSelf` (`next_trotterjohnson`, `:2484`) | `if m == 0: return None` | `stepAltDefined self.contents = false → out = none` |

The first three refusals are reached by the tests, not just reachable in principle:
`sympy/combinatorics/tests/test_permutations.py:104` (`raises(ValueError, lambda:
p ^ Permutation([]))`), `:109` (`p.commutator(Permutation([]))`) and `:120`
(`Permutation.from_inversion_vector([0, 2])`), all three inside
`test_Permutation` — a PASS_TO_PASS test whose body the FAIL_TO_PASS test
`test_Permutation_subclassing` re-runs under its subclass. So a spec asserting an
object is constructed there would be satisfied by an implementation that fails
those tests; see refinement.md §B3.

The last three are NOT reached on their refused side by any shipped test — the
tests exercise `unrank_trotterjohnson(4, i)` for `i` in `0..4` and `rmul_with_af`
over equal-extent operands, all of which are ACCEPTED. Their partiality is
therefore a domain restriction to what the real callee can do, not a modeling of
an asserted test: on the refused sub-domain the gold code produces no object, so a
spec obliging one there is unsatisfiable BY GOLD, which is the defect being fixed.
Nothing is given up on the accepted sub-domain, where each site's class obligation
still binds in full.

The remaining sites are total on their carriers, and that was measured in the same
sweep rather than assumed: `unrank_lex` and `unrank_nonlex` reduce their index
first (`rank % new_psize`, `r % ifac(n)`) so `rankedFor`/`rankedAltFor` accept
every index; `__mul__`, `__pow__`, `__invert__`, `josephus`, `random` and the
`__new__`-family sites construct unconditionally on the branch the patch threads.
Flattening those the same way as the eight above would be unfaithful in the
opposite direction.

The pre-patch bug — `_af_new` is a `@staticmethod` calling `Basic.__new__(Perm,
perm)`, the fixed base class — is modeled in `Solution_prepatch.lean` as
`buildVia` ignoring `builtOn` and returning `classId := 0`, which violates
`out.classId = builtOn` exactly when the source class is a subclass. The
site-level prepatches (`Solution_prepatch_instance.lean`,
`Solution_prepatch_classmethod.lean`) model the orthogonal pre-patch fact that a
call site dispatched the module-global `_af_new` (base class, tag `0`) rather
than its own source class, violating `out.classId = self.classId` / `= cls`.

## 3. Callee provenance

### 3.1 `buildVia` ↔ the post-patch `_af_new` factory (modeled directly)
The shared factory is the ONE site where the produced object's class is decided.
Its changed behaviour ("instance of the dispatched-on class") is modeled directly
as `out.classId = builtOn`; its unchanged value passthrough as `out.contents =
value`. It is not axiomatized.

### 3.2 The opaque `*Contents` maps ↔ the unchanged array computations (A-references)
Each `*Contents` symbol models an in-method array computation that the patch does
**not** touch (the per-site array form: composition, `_af_pow`, `_af_invert`, the
generated/indexed `perm_array`, etc.). Each is an opaque total map; the spec never
pins its concrete value, only that the SAME map feeds both the model and the
patch — an **A-reference** (validated by same-map cancellation in G-CONF), not a
consumed axiom.

**No consumed axioms ⇒ G-AX skip.** There is no `axiom_check.py`: the bundle
declares no `axiom`; the opaque symbols are A-references whose concrete values
are never relied upon.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12489`**. Its R/I shadow
builds each modeled site's result via the shared factory dispatched on the source
class (`self._af_new(...)` for instance sites, `cls._af_new(...)` for classmethod
sites, each via the post-patch `@classmethod` `_af_new` building through the
runtime class), instantiating each opaque `*Contents` with a concrete value rule
on both sides (so it cancels). The discriminating observable at every site is the
runtime class of the constructed result.
