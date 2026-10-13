# mapping.md — django__django-9296

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 84322a29ce9b0940335f8ab3d60e55192bef1e50`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deeply-modeled callee.

Repo file under change: `django/core/paginator.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `enumeratePages (pageRange : List PageIdx)` | `Paginator.__iter__(self)` — `django/core/paginator.py` (added at line 37, between `__init__` and `validate_number`) | the modeled changed function (the iteration protocol) |
| `numPages` *(opaque `Nat`)* | `Paginator.num_pages` — `django/core/paginator.py:94` (`cached_property`) | how many sub-views the object presents. A fixed attribute of the object; opaque because no concrete count is relied on, and because it belongs to the OBJECT (it is not readable off any argument). |
| `PageIdx` = `{n : Nat // 1 ≤ n ∧ n ≤ numPages}` | a **valid** 1-based page number for this object: an integer `n` with `1 ≤ n ≤ self.num_pages`, i.e. exactly a member of `self.page_range` and exactly an argument `validate_number` accepts | the index carrier. It carries the accessor's DOMAIN with each index, so applying the accessor at an index the object does not name is not expressible (see §3.1 property (c) and refinement.md §C). |
| `pageOf` *(opaque — A-reference)* | `Paginator.page(self, number)` — `django/core/paginator.py:67` | unchanged accessor: returns the sub-view (a `Page`) for a **valid** 1-based index. PARTIAL in the repo (`validate_number` raises `EmptyPage` outside `[1 … num_pages]`), and modeled as a map on `PageIdx` — total on its real domain, undefined nowhere else because nowhere else is expressible. Validated == real `page`, domain included, by axiom_check.py (G-AX). NOT a consumed axiom. |
| `pageSeq (ps : List PageIdx)` | the per-index expansion `[self.page(n) for n in self.page_range]` that `__iter__`'s generator yields | pure spec: the ordered family of sub-views named by an index sequence |
| `pageRange` *(the input)* | `Paginator.page_range` — `django/core/paginator.py:101` (`range(1, self.num_pages + 1)`) | the 1-based index sequence iterated over. Every element is a `PageIdx` by construction — that identity (`list(page_range) == [1 … num_pages]`) is asserted by axiom_check.py. |

`Page` content is observed by the F2P test through `list(page)` — i.e. the page's
`object_list` slice (a list of objects). The carrier abstracts a `Page` to that
observable element list (see §2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.num_pages` | `numPages : Nat` | identity on non-negative integers (`num_pages ≥ 0`; it is `0` exactly when the object is empty and `allow_empty_first_page` is false) |
| a **valid** 1-based page index `n` (one `validate_number` accepts) | `PageIdx` = `{n : Nat // 1 ≤ n ∧ n ≤ numPages}` | identity on the integer, paired with the membership proof. Total on the real domain: `page(n)` returns for every `1 ≤ n ≤ num_pages` and raises `EmptyPage` for every other integer — measured in both directions by axiom_check.py property (c), so this subtype is the accessor's domain exactly, neither wider nor narrower |
| `self.page_range` = `range(1, num_pages+1)` | `List PageIdx` | the Python range materialized in order ↔ the list of indices; `len(range)` ↔ `.length`; element `k` ↔ list element `k`; empty range (num_pages = 0) ↔ `[]`. Well-typed because `list(page_range) == [1 … num_pages]` (asserted by axiom_check.py), i.e. every element carries the membership `PageIdx` demands |
| a `Page` object yielded by `__iter__` | `List Int` | `Page` ↔ `list(page)` — its observable `object_list` slice. The F2P test (`list(next(page_iterator))`) observes exactly this list; the test fixture uses `[1,2,3]` (integers), so `List Int` is the exact element carrier |
| `iter(paginator)` → generator of pages | `enumeratePages`'s `out : List (List Int)` | the generator materialized in order ↔ the result list; `out[k]` ↔ the k-th yielded `list(page)` |

The carrier for a page is `List Int` because the F2P test paginates `[1, 2, 3]`
and compares each yielded page via `list(...)` against integer lists `[1, 2]`,
`[3]`.

## 2.1 Arithmetic realization — a Lean operation is realized by its own semantics, never by a same-looking Python operator

The value bijection above is identity on the integers it covers, but the
OPERATIONS are not the same operations. Lean's numeric types are **total**, and
each is total in its own way — `Nat` by saturation, `Int` by answering `0` at a
zero divisor and by rounding EUCLIDEAN, fixed-width types by wrapping, `Float` by
IEEE `±inf`/`nan` — while Python's operators of the same spelling are variously
partial (`//` and `%` raise), differently signed, differently rounded and
unbounded. Reading one as the other is not a refinement of the type abstraction;
it is a silent change of algebra. This section fixes the realization, and it does
so as a LAW with an enumerated instance table, not as a list of the operators
that have already caused trouble.

**R0 — a closed term is realized by its value.** A sub-expression containing no
program variable and no spec symbol is a closed Lean term; Lean evaluates it, and
its realization is the literal it evaluates to, transported by the §2 bijection.
Not the same-looking Python expression: Python is not the semantics of Lean, and
where the two spellings coincide that is a coincidence of notation. So
`((1 : Int) % (-2))` realizes as `1` (measured), `((200 : UInt8) + 100)` as `44`
(measured), `(1.0 / 0.0 : Float)` as `inf` (measured) — regardless of what the
same characters would do in Python, and regardless of the type, including types
this table does not list.

**R1 — an open term is realized by a total Python function equal to the Lean
one.** For a Lean operation `f` applied to anything a variable flows into, the
realization is a Python function that (i) is defined on all of `f`'s Lean domain —
`f` is total, so a realization that raises anywhere is not one — and (ii) agrees
with `f` at every point of it, under the §2 bijection. The realization is derived
from `f`'s own defining equations. A Python operator may be used **only** where it
is the realization, i.e. where it is total and agrees everywhere; where it raises,
rounds differently, signs differently or is unbounded where Lean wraps, it is not
a realization and the explicit function below is used instead.

R1 is **extensional**, and both halves of that matter. It demands the same
FUNCTION, not the same evaluation strategy: where a Lean sub-term is provably a
constant, the realization is that constant, and the proof that fixes it is the
proof the module already carries — `0 * k` realizes as `0` by `Nat.zero_mul`,
whatever `k` is and however expensive `k` would be to build. And "defined on all
of `f`'s Lean domain" is a claim about the WHOLE domain, not about the arguments a
test happens to supply: Lean's `Nat` is unbounded and its `List.length` returns an
unbounded `Nat`, whereas CPython bounds every container and every `len` by
`ssize_t` (`sys.maxsize = 2^63 - 1`, measured), so a candidate realization that
raises `OverflowError` above that bound is not a realization of a total Lean
operation — it is a realization of a partial approximation to it.

**R2 — a composite is realized from ITS OWN defining equation, not by composing
the rows.** Realization does not distribute over composition for free. If `g ∘ f`
is total in Lean, a row for `f` and a row for `g` license the Python composition
only when every INTERMEDIATE value is itself representable on the Python side over
the whole Lean domain; otherwise the composition raises where the Lean composite
does not, and R1 rejects it. Where an intermediate is not representable, the
realization is derived from the defining equation of the COMPOSITE, which Lean
proves as a closed form. The instance of that in this bundle is one line long:
**realize the length, not the list.** `(List.range n).length` is `n` — Lean's
`List.length_range`, discharged by `simp` (measured) — so its realization is `n`,
NOT `len(list(range(n)))`, even though the `List` table below carries a row
`xs.length → len(xs)` and `range` transcribes Lean's `List.range`. Composing those
two rows produces a function that raises `OverflowError` for every
`n ≥ 2^63` while the Lean composite answers `n` for every `n : Nat`. R2 is what
makes the row table safe to read compositionally at all, and it is why the derived
lengths are tabled explicitly below rather than left to be assembled.

**R3 — an annotated STATEMENT is realized by its denotation, not by its
schedule.** R0–R2 fix expressions, and a loop is not an expression. In this
bundle a `while g invariant I done_with D decreasing m` is not a bare Python
`while` wearing comments: it is a statement whose meaning is fixed by its
annotations, because that is Velvet's own proof rule — the verifier establishes
`I` at entry, preserves `I` across the body, proves `m` descending, and hands the
continuation exactly `I ∧ D`. Nothing else about the loop is available to the
proof, so nothing else is what the loop MEANS. The realization of such a loop is
therefore any total Python statement that establishes `I ∧ D` from the entry
state, **provided `I ∧ D` determines the final value of every variable the loop
modifies**. Where it does, the realization may be a closed form. Where it does
not, `I ∧ D` under-determines the loop, R3 gives nothing, and the realization
transcribes the body step for step with R0–R2 applied to each step — which is what
the frozen impl's own realization does.

Two instances, both from a recorded finding, both measured:

* `k := 2 ^ (64 + pageRange.length)` then
  `while k > 0 invariant True done_with k = 0 decreasing k do k := k - 1`.
  The only variable the loop modifies is `k`, and `done_with k = 0` determines it,
  so the realization is `k = 0`. It is NOT that initialiser followed by a Python
  `while k > 0: k -= 1`. That transcription is not "the same function, slower": it
  is a Python statement that does not finish, and a statement that does not finish
  realizes nothing. Measured both ways — the transcription is recorded
  `completed=false` at a 3600s harness timeout; the R3 realization resolves in 97s.
* the frozen loop with its own counter WIDENED to
  `i := pageRange.length + 2 ^ (64 + pageRange.length)`. Its invariant
  `result = pageSeq (pageRange.drop i)` together with `done_with i = 0` determines
  `result = pageSeq pageRange`, so the realization is the traversal the frozen
  impl already has. Measured: transcription `completed=false` at 3600s, R3
  realization resolves.

R3 does **not** license realizing a wrong implementation as gold, and the reason
is the same one that makes R1 safe. R1 is extensionality about an operation; R3 is
extensionality about a statement. The realization must establish the loop's OWN
`I ∧ D` — the very pair the verifier has proved of that loop — so it ends in the
state the loop ends in. A loop that establishes something else establishes it in
Lean too, and is then either rejected by the obligation or, if it verifies,
satisfies `ensures out = pageSeq pageRange`, which by the single-valuedness
argument in refinement.md §B'''' is gold's output. The side condition is what
carries the weight, and it is checkable: `I ∧ D` determines the modified
variables, or R3 does not apply.

**R4 — a BINDING is realized by its denotation too, and a binding nothing reads
denotes the identity.** R3 settles annotated statements; a `let` is a statement as
well, and the shape that survived R3 binds a local and never reads it:

```
let _z : Nat := 2 ^ (2 ^ (64 + pageRange.length))
```

Every Velvet expression is pure and every Lean function is total, so this
statement cannot change the returned value and cannot fail. Its denotation is the
IDENTITY on the state, and its realization is therefore the EMPTY statement: the
value need not be built. Transliterating it is not "the same function, slower" —
it is the same conviction R3 records, by R1's own criterion: CPython is measured
to refuse an integer of `2^64 + 1` bits (2 305 843 009 213 693 953 bytes by
arithmetic), and a statement that does not finish realizes nothing.

**The side condition is that nothing the program EXECUTES reads the binder**, and
it is syntactic, so it is decided rather than claimed. `conformance_check.py`'s
`impl_reads_binding` counts reads in the impl region, skipping comments, the
binding's own line, and ANNOTATION lines (`invariant`, `done_with`, `decreasing`,
`assert`) — because under R3 an annotation is not executed, so a local mentioned
only in an invariant is still runtime-dead, and the refined patch contains no
invariants. Measured on three fixtures: the attack's own impl gives 0, that impl
with `return result.take z` gives 1, and the invariant-only impl gives 0 while a
naive whole-text count finds the mention. Where the count is NOT zero the local is
observable, R4 gives nothing, and R0–R2 realize the term it binds — measured, for
the live fixture, as a genuinely different output list.

R4 does not license deleting work: it licenses deleting a statement whose
denotation is the identity, which is the same move R3 makes for a loop whose
`I ∧ D` determines its post-state, and the same one R0 makes for a closed term.
What would license deleting real work is a claim of deadness that nothing checks,
which is exactly what `impl_reads_binding` removes. And the rule is answerable to
the oracle, not only to this document: the attack module above, realized under R4
(that one `let` dropped, everything else identical), is
`resolved=true, F2P 1/1, P2P 20/20` in 53.1s through the official harness, where
the transliteration of the same module never completed one resolve in 4 200s
(measured 2026-08-16; refinement.md §B'''''').

**Coverage, and what happens outside it.** The value-carrying symbols a verified
impl of this method can read are `pageRange : List PageIdx`, `numPages : Nat`,
`pageOf : PageIdx → List Int` and its own `out`/locals, so every OPEN term is
built over `Nat`, `Int`, `Bool`, `List` and the carrier `PageIdx`, plus whatever a
coercion carries those into; everything else is closed and settled by R0. The
tables below give the realizations for those types and for the two further
algebras a coercion reaches (fixed-width and `Float`). An operation with no row is
not licensed to reuse its Python spelling: R1 already fixes its realization, and
the row is ADDED by transcribing Lean's defining equations. Nor is a COMPOSITE
licensed to reuse a chain of rows: by R2 it is realized from its own defining
equation whenever an intermediate would leave what Python can represent. That is
the coverage obligation, it is part of this map, and it is what makes §C's
`verify ⇒ resolved` a claim about every impl rather than about the impls already
seen.

**`Nat` — total by SATURATION.**

| Lean `Nat` operation | Python realization | why they differ |
|---|---|---|
| `a + b`, `a * b` | `a + b`, `a * b` | identical on non-negative ints; both total |
| `a ^ b` **where the value is one Python can hold** | `a ** b` | valid only under that side condition, for the same reason `xs.length → len(xs)` carries one. CPython BUILDS the integer, so `2 ** (2 ^ 64)` raises `MemoryError` after 15s under a 2GiB cap (measured; and `2 ** 2^31` takes 13s to build a 256MiB integer), where Lean's `2 ^ (2 ^ 64) : Nat` is an ordinary closed term the kernel never expands. Above what Python can hold, R2 applies: realize the expression that CONSUMES the power from its own defining equation. `2 ^ m > 0` is the constant `True` (`Nat.two_pow_pos`), never `2 ** m > 0` |
| `(a ^ b) % m` — a power that is CONSUMED by a modulus | `pow_mod(a, b, m)` = CPython's THREE-argument `pow(a, b, |m|)`, and `int_pow(a, b)` when `m = 0` | the row above's escape clause, WORKED — and the reason that clause is not a dead letter. `Nat.pow_mod` is the composite's own defining equation, and three-argument `pow` implements exactly it: it reduces at every squaring, so it never builds `a ^ b`. Measured: `pow(2, 2^66, 7) = 2` in under a microsecond, where the spelling `(2 ** 2^66) % 7` must first build the intermediate the row above refuses (2 305 843 009 213 693 953 bytes at the smaller `2^64`). The two `%` conventions ride along: `m = 0` is `n % 0 = n`, which three-argument `pow` rejects with `ValueError`, and a negative modulus is `Int.emod`, never negative, where Python's `pow` follows its floored `%` into `(m, 0]` |
| `a - b` | `nat_sub(a, b)` = `a - b if b <= a else 0` | `Nat.sub` is TRUNCATED (`0 - 1 = 0`); Python's `-` is signed (`0 - 1 = -1`) |
| `a / b` | `nat_div(a, b)` = `a // b if b != 0 else 0` | `Nat.div` is total (`a / 0 = 0`); Python's `//` raises `ZeroDivisionError` |
| `a % b` | `nat_mod(a, b)` = `a % b if b != 0 else a` | `Nat.mod` is total (`a % 0 = a`); Python's `%` raises `ZeroDivisionError` |
| `a ≤ b`, `a < b`, `a = b` | `a <= b`, `a < b`, `a == b` | identical |
| a `Nat` literal `k` | `k` | identical |

**`Int` — total at a zero divisor, and EUCLIDEAN.** `Int` is spec-visible
(`pageOf : PageIdx → List Int`, `out : List (List Int)`), and it is a third
algebra: signed like Python, total like `Nat`, and rounded like neither. Lean's
`/` and `%` on `Int` are `Int.ediv`/`Int.emod`, whose remainder is never negative;
Python's are FLOORED. Every value below was measured in this workspace, one build.

| Lean `Int` operation | Python realization | measured divergence |
|---|---|---|
| `a + b`, `a - b`, `a * b` | `a + b`, `a - b`, `a * b` | identical; `Int` is signed, so nothing truncates |
| `a ^ (n : Nat)` **where the value is one Python can hold** | `int_pow(a, n)` (`a ** n` under that side condition, and a refusal above it) | the `Nat` `^` row's side condition, one type over, and for the identical reason: CPython BUILDS the integer. Measured, 2GiB cap: `(-2) ** (2 ^ 66)` raises `MemoryError` after 20.8s, while `(-2) ^ (2 ^ 66) : Int` is an ordinary closed term the kernel never expands. Above the bound R2 applies — realize the expression that CONSUMES the power |
| `a / b` (`Int.ediv`) | `int_ediv(a, b)` = `0` if `b == 0`, else `a // b` for `b > 0` and `-(a // -b)` for `b < 0` | `(7 : Int) / (-2) = -3` vs `7 // -2 == -4`; `(-7 : Int) / (-2) = 4` vs `-7 // -2 == 3`; `(5 : Int) / 0 = 0` vs `ZeroDivisionError` |
| `a % b` (`Int.emod`) | `int_emod(a, b)` = `a` if `b == 0`, else `a % abs(b)` | `(1 : Int) % (-2) = 1` vs `1 % -2 == -1`; `(-7 : Int) % (-2) = 1` vs `-7 % -2 == -1`; `(5 : Int) % 0 = 5` vs `ZeroDivisionError` |
| `Int.tdiv`, `Int.tmod` | `int_tdiv`, `int_tmod` (round toward zero; total at 0) | `(7 : Int).tdiv (-2) = -3`, `.tmod (-2) = 1` |
| `Int.fdiv`, `Int.fmod` | `int_fdiv`, `int_fmod` (Python's own `//`/`%`, but total at 0) | `(7 : Int).fdiv (-2) = -4`, `.fmod (-2) = -1`; `.fdiv 0 = 0` |
| `(↑n : Int)` for `n : Nat` | `n` | identical |
| `a.toNat` | `int_to_nat(a)` = `a if a >= 0 else 0` | `(-5 : Int).toNat = 0`; Python's `int()` does not saturate |
| `a.natAbs`, `a.sign` | `abs(a)`, `(a > 0) - (a < 0)` | identical |
| `a ≤ b`, `a < b`, `a = b` | `a <= b`, `a < b`, `a == b` | identical |

**Fixed width (`UInt8`/`UInt16`/`UInt32`/`UInt64`) — MODULAR.** Reached only by a
coercion (`Nat.toUInt8`, `Float.toUInt64`, …). Every operation wraps at `2^n`,
where Python's integers are unbounded; division and modulo are total as in `Nat`.
Measured: `(200 : UInt8) + 100 = 44`, `(3 : UInt8) - 5 = 254`,
`(2 : UInt64) ^ 70 = 0`, `(5 : UInt8) / 0 = 0`, `(5 : UInt8) % 0 = 5`,
`(300 : Nat).toUInt8 = 44`. Realizations: `uint_wrap(a op b, n)`,
`uint_div(a, b, n)`, `uint_mod(a, b, n)`.

**`Float` — IEEE-754, and TOTAL.** Also reached only by a coercion
(`Nat.toFloat`). Lean answers `±inf`/`nan` where Python's `/` raises
`ZeroDivisionError`, and its conversions to a fixed-width integer TRUNCATE and
SATURATE where Python's `int()` raises. Measured: `1.0 / 0.0 = inf`,
`-1.0 / 0.0 = -inf`, `0.0 / 0.0 = NaN`, `inf.toUInt64 = 2^64 - 1`,
`NaN.toUInt64 = 0`, `(-1.0).toUInt64 = 0`, `(3.7).toUInt64 = 3`. Comparisons are
IEEE on both sides and agree (`NaN < 1.0` and `NaN == NaN` are both false in
both). Realizations: `float_div`, `float_to_uint64`, and — because IEEE totality
is exactly what Python's spellings drop at the top of the range — `nat_to_float`
and `float_pow`: `float(2 ^ 1024)` raises `OverflowError: int too large to convert
to float` and `2.0 ** 2000` raises `OverflowError: Numerical result out of range`
(both measured), where Lean's `Float` saturates to `±inf`, so neither bare
spelling is a realization. `float(2 ^ 1023)` is `8.98846567431158e+307`, so the
side condition is the double range and the helpers saturate above it. There is no
`%` on `Float` (measured: `HMod Float Float` does not synthesize). **Also measured:** no impl of
this method can reach this leg and still verify — a counter offset by a `Float`
round trip leaves the frozen invariant `i ≤ pageRange.length` unsolved, because
Lean's `Float` operations are `@[extern]` and do not reduce. The rows are fixed
anyway: a leg that is unreachable today is not the same thing as a leg the map may
translate by spelling.

**`List`, `Bool`, and the carrier.**

| Lean operation | Python realization | note |
|---|---|---|
| `xs.length` **where `xs` is a materialized list** | `len(xs)` | valid only under that side condition. Python's `len` is `ssize_t`-bounded where Lean's `List.length` returns an unbounded `Nat`, so this row is a realization exactly for lists Python holds — which is every list this method's inputs and locals actually carry, `pageRange` and `result` included. For a DERIVED list, R2 applies and the next three rows are used instead |
| `xs[k]?`, `xs.take k`, `xs.drop k`, `xs.map f`, `xs.reverse`, `xs ++ ys` | `xs[k] if 0 <= k < len(xs) else None`, `xs[:k]`, `xs[k:]`, `[f(x) for x in xs]`, `xs[::-1]`, `xs + ys` | total on both sides once the index arithmetic above is realized; the `Option` read is the one the carrier forces (§2 last paragraph) |
| `(List.range n).length`, `(List.replicate n a).length` | `n`, `n` | **R2: realize the length, not the list.** Lean's `List.length_range` / `List.length_replicate`, both discharged by `simp` (measured). Emphatically NOT `len(list(range(n)))` or `len([a] * n)`: those raise `OverflowError: Python int too large to convert to C ssize_t` for `n ≥ 2^63` (measured at `n = 2^63, 2^64, 2^66`) while the Lean composite is total on all of `Nat` |
| `(xs.map f).length`, `(xs.take k).length`, `(xs.drop k).length`, `(xs ++ ys).length`, `xs.reverse.length` | `len(xs)`, `min(k, len(xs))`, `nat_sub(len(xs), k)`, `len(xs) + len(ys)`, `len(xs)` | same rule: the length of a derived list is its own closed form, so no intermediate is built. Each equation is `simp`-discharged in Lean (measured) |
| `List.range n` *(as a value that is actually traversed)* | `range(n)` — lazily, never `list(...)` | reached only if an impl iterates the container rather than measuring it. Materializing is not the realization: it changes definedness at the `ssize_t` bound and nothing about the Lean semantics licenses it. `range` itself is total here: `range(2 ^ 66)` and iterating it both work (measured); only `len` of it raises, which is the row above |
| `List.replicate n a` *(as a value that is actually traversed)* | `repeat_total(a, n)` = `itertools.repeat(a, n)` for `n < 2^63`, `itertools.repeat(a)` above it | `itertools.repeat` bounds its COUNT by `ssize_t`: `itertools.repeat(7, 2 ^ 63)` raises `OverflowError` immediately (measured) where `List.replicate` is total on `Nat`. Dropping the count is a realization because every prefix a TERMINATING consumer reads is identical, and R3 plus supplement 2 (total-correctness semantics) is what makes the consumer terminate |
| `p.val` for `p : PageIdx` | the index integer itself | the membership proof carries no runtime content |
| `if c then e₁ else e₂`, `&&`, `||`, `!` | the same, on the realized `c` | the CONDITION is realized by the rules above before the branch is taken |

Two consequences, both load-bearing for `verify ⇒ resolved`:

1. **Definedness transfers.** Every expression a verified impl can write evaluates
   in Python without raising, because each operation is realized by a total
   counterpart rather than by an operator that merely agrees with it on part of the
   domain — and, by R2, because no composite is realized through an intermediate
   Python cannot represent.
2. **Termination transfers.** This bundle proves every loop terminating under
   `TotalCorrectness` with a `Nat` measure. That proof carries over only because
   the realized step performs the same arithmetic: a measure that provably reaches
   `0` in Lean by truncation (`k := k - 2` from an odd start) walks the same
   descending sequence under `nat_sub`, and would run away forever under Python's
   signed `-`.

Two more, which are the same statement about control flow and about branches —
they are separated out because a recorded finding turned on each. A realized
CONDITION decides the same branch as the Lean one (`((1 : Int) % (-2)) < 0` is
false in Lean and false under `int_emod`, where `1 % -2 < 0` is true in Python),
and a realized DEAD local computes the same value (or, under R0, the same
literal), so neither a discarded local nor a consumed guard can diverge. Read that
second clause with R4: a dead local may be DISCARDED, because the identity is what
it denotes — what it may not be is realized by a spelling that fails, and what may
not be discarded is a local something reads. The three cases are decided by
`impl_reads_binding`, not by the translator's judgement.

The realization is executable and checked, not asserted. `conformance_check.py`
defines the whole library — `nat_sub`/`nat_div`/`nat_mod`,
`int_ediv`/`int_emod`/`int_tdiv`/`int_tmod`/`int_fdiv`/`int_fmod`/`int_to_nat`,
`uint_wrap`/`uint_div`/`uint_mod`, `float_div`/`float_to_uint64`/`nat_to_float`/`float_pow`,
`range_length`/`replicate_length`/`map_length`/`take_length`/`drop_length`/`append_length`,
`repeat_total`/`int_pow`/`pow_mod`, the loop library
`countdown_denotation`/`guarded_collect_denotation`/`two_pow_positive`, and the
binding library `impl_reads_binding`/`dead_local_denotation`/`live_local_denotation`
— performs every `Nat` operation in its shadow through it, and measures it in eight
blocks: `check_nat_algebra` (the four `Nat` laws exhaustively on `[0,96)²`),
`check_int_algebra` (the Euclidean identity and `0 ≤ a % b < |b|` exhaustively on
`[-48,48)²`, the four convention fixtures, and totality at every zero divisor),
`check_uint_algebra` and `check_float_algebra` (the measured Lean values above),
`check_container_realization` (each derived length against a materialized
reference at small `n`, then at `n = 2^63, 2^64, 2^66` where the materializing
route is measured to raise), and `check_loop_realization` (rule R3: the
countdown's denotation against the real loop exhaustively for every start below
1024 and with the step count as the witness that the loop ran; the guarded
backward collect from `n`, from the algebraically widened `n + 0 · 2^64`, and
then from `n + 2^64`, where 100 000 steps are measured not to reach the data at
all while the denotation is unchanged; the countdown from `k = 2^64` measured NOT
to have finished after 1 000 000 steps while `countdown_denotation` answers `0`
in constant time; and the `^` row at its side condition — `2 ** 2^64` needs
2 305 843 009 213 693 953 bytes by arithmetic and is measured to raise
`MemoryError` in a memory-capped child, while `0 < 2 ^ n` is realized as the
constant `True` that `Nat.two_pow_pos` proves), and `check_total_spellings` (the
four further rows whose Python spelling is not total: the lazy replicate against
`itertools.repeat`'s `ssize_t` count, the `Int` power against its side condition,
`nat_to_float`/`float_pow` against the two `OverflowError`s Lean's IEEE
totality does not have — each measured in both directions, with `range(2^66)`
alongside them because it is the one that does NOT need repairing — and the
CONSUMED power against the composite it is built from, `int_pow` then `int_emod`,
on the whole small grid including the zero and negative moduli, then above the `^`
row's bound where the realization answers `(2 ^ 2^66) % 7 = 2` in under a second
and the two-argument form is measured to refuse the same exponent), and
`check_dead_binding_realization` (rule R4: the deadness DECISION on the three
fixtures above, agreement between the transliteration and the denotation where
CPython can still hold the value, the measured refusal at `2 ^ (2 ^ 64)` against a
denotation that answers in microseconds, and the live fixture whose output really
changes if the binding is dropped). Each block also asserts
NON-VACUITY: that the realization really differs from Python's own operator
exactly where Lean differs from Python, and that Python's operator really still
raises or diverges. On the Lean side the same equations are discharged INSIDE the
impl region by `admiss-nat-semantics-carried`, `admiss-int-semantics-carried`,
`admiss-derived-length-carried` and `admiss-loop-denotation-carried`
(`properties.py`, G-PBT), each measured live against negative controls that claim
Python's answers instead. So both halves of this section are pinned to one shared
set of equations rather than to a resemblance between two operator spellings. See
refinement.md §B'', §B''', §B'''' and §B''''' for the recorded defects this
section fixes.

**Why the index carrier is a subtype and not `Nat`.** The accessor being modeled
is partial: `Paginator.page(n)` raises `EmptyPage` for every `n` outside
`[1 … num_pages]`. Modeling it as a total `Nat → List Int` would erase that
refusal, and — because a value-only postcondition cannot constrain applications
whose results are discarded — would admit an implementation that calls the
accessor at an index the object does not name, throws the result away, and still
satisfies `out = pageSeq pageRange`, while its real counterpart raises and fails
the target test. That is the hole this bundle's G-EQ record found and this carrier
closes: the membership proof travels with the index, so the off-domain
application does not typecheck (`omega could not prove the goal` on the bound),
and there is no way to conjure an index either — `PageIdx` deliberately has **no
`Inhabited`/`Nonempty` instance**, so `pageRange[k]!`, `.head!`, `default` and
`Classical.arbitrary` all fail to synthesize. An index can only be received from
the caller or built from the object's own count under a proof. The consequence
for the impl is visible in the region: reads are `pageRange[i - 1]?` (an
`Option`), mapped through the accessor, because the total read is unavailable.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `pageOf` deep-model reference ↔ `Paginator.page` (A-reference)
**Callee:** `Paginator.page(self, number)` (`django/core/paginator.py:67`),
**unchanged** by the patch. For one fixed `Paginator` it is a deterministic
function of the 1-based index `number` alone (it depends only on `self` and
`number`; `self` is fixed during one iteration). The patch does NOT change
`page`; `__iter__` merely *calls* it. Hence `page` is modeled as the opaque total
map `pageOf : PageIdx → List Int` — its concrete result is never pinned, the spec
relies only on the fact that the SAME accessor is applied to every index in
order. Its argument type carries the accessor's real domain, so the model is
total where `page` returns and silent where `page` raises (there is no index
outside `[1 … num_pages]` to apply it to). This is an **A-reference**, not a
consumed axiom: no `ensures` of `pageOf` is consumed by the proof.

**Soundness check (G-AX):** `axiom_check.py` constructs real `Paginator` objects
over many `(object_list, per_page, orphans, allow_empty_first_page)`
configurations and asserts the three properties the deep model relies on:
(a) **determinism** — `page(n)` called repeatedly returns the same observable
`list(page)` (so a map out of `PageIdx` is well-defined);
(b) **independence from the iteration order** — iterating via the patched
`__iter__` yields exactly `[list(self.page(n)) for n in self.page_range]`, i.e.
the materialized iteration equals `pageSeq` applied to `page_range` under the
mapping.md bijection; and
(c) **the domain** — `dom(page) == list(page_range) == [1 … num_pages]`,
measured in BOTH directions: `page(n)` never raises for `1 ≤ n ≤ num_pages`, and
raises `EmptyPage` for every other integer probed (`-1`, `0`, `num_pages+1`,
`num_pages+2`, `num_pages+17`), including `n = 1` when the object presents no
pages at all. (c) is what licenses the `PageIdx` carrier: the first half rules out
a carrier that is too WIDE (admitting calls that raise), the second a carrier that
is too NARROW (forbidding calls the object really serves, which would make the
spec too strong). stdlib + django only. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9296`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the fold (`pageSeq`/the backward `while`, all I/R ops) to Python statement for
statement — including the `Option`-shaped read `pageRange[i - 1]?` the carrier
forces — and leaves the A-tagged `pageOf` as the real repo callee
`Paginator.page` (run the real callee, not the model). It also asserts the
carrier membership it relies on (`1 ≤ p ≤ num_pages` for every index it hands the
accessor), which is the R/I side of §2's index carrier; the A side is
axiom_check.py property (c). The oracle is `list(iter(paginator))` from the
patched repo.
