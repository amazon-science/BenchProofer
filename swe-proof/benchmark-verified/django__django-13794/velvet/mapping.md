# mapping.md — django__django-13794

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fe886eee36be8022f34cfe59aa61ff1c21fe01d9`, states the type
abstraction (the Lean↔Python bijection G-CONF and G-AX use to bridge values),
and gives the provenance of every modeled / referenced callee.

Repo file under change: `django/utils/functional.py` (the lazy-value proxy class
built by `lazy(func, *resultclasses)`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deferredConcatLeft (forced : List Char) (other : List Char)` | the binary-add behaviour when the lazy value is the **left** operand and the underlying values are character sequences — `lazy.<locals>.__proxy__.__add__` (`django/utils/functional.py:179` post-patch) at `str` result class | modeled changed behaviour (left-operand add, string case) |
| `deferredConcatRight (forced : List Char) (other : List Char)` | the binary-add behaviour when the lazy value is the **right** operand and the underlying values are character sequences — `lazy.<locals>.__proxy__.__radd__` (`django/utils/functional.py:182` post-patch) at `str` result class | modeled changed behaviour (right-operand add, string case) |
| `deferredSumLeft (forced : Int) (other : Int)` | the same left-operand add behaviour at the `int` result class (`__proxy__.__add__`) | modeled changed behaviour (left-operand add, integer case) |
| `deferredSumRight (forced : Int) (other : Int)` | the same right-operand add behaviour at the `int` result class (`__proxy__.__radd__`) | modeled changed behaviour (right-operand add, integer case) |

There are **no axiomatized callees** and **no deep-model references**: each
modeled function is a *changed* function whose new logic is a single binary
combination of its (forced) operands, modeled deeply and directly. The
forcing step (`self.__cast()`, `django/utils/functional.py:152`) is **unchanged**
infrastructure and is represented by the input `forced` already holding the
underlying value (an R-refinement, §2), so it is neither axiom nor reference.

The pre-patch repo state the change repairs (refinement audit only, not in the
consumer spec view): before the patch the proxy had only the auto-generated
magic-method wrapper for the left-operand add (built by `__prepare_class__`,
`django/utils/functional.py:108`) and **no** right-operand handler at all. The
auto wrapper evaluates `getattr(self.__cast(), '__add__')(other)` directly, so
when `other` cannot be combined with the forced value it **raises** rather than
returning the not-implemented sentinel, and the right-operand fallback is never
reached.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and the conformance shadow use to translate
values between the Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` underlying value / `str` other operand (the `add08`/`add09` template inputs) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat `+` ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `int` underlying value / `int` other operand (the `test_lazy_add` inputs) | `Int` | Python arbitrary-precision `int` ↔ Lean `Int`; `int` `+` ↔ `Int` `+` |
| `self.__cast()` — forcing the deferred value to its underlying result (`functional.py:152`) | identity onto the input `forced` | the forcing is unchanged behaviour; the modeled function receives the already-forced underlying value as `forced`. Observationally the identity on the carrier. |
| the operation succeeds (returns a value) vs. raises `TypeError` | `Except AddOutcome _` (`.ok v` vs `.error .unsupportedOperand`) | the proxy operator either returns the combined value or raises `TypeError`; the add template filter that calls it turns a raise into the empty string. The changed function's two outcomes ↔ the two `Except` constructors. |

Lean `String`/`List Char` indexing is total and sound; the string carrier is
`List Char` because the operation is per-code-point concatenation. Integer
addition uses `Int` directly (the underlying values in `test_lazy_add` are
small, but `Int` is exact and unbounded — no precision/overflow gap).

Operand order is preserved by the carrier: left-operand add ↔ `forced ++ other`
(string) / `forced + other` (int); right-operand add ↔ `other ++ forced` /
`other + forced`. For integers the two coincide (`+` commutes); for character
sequences they differ, and the `str + lazy` vs `lazy + str` cases observe the
difference (F2P `add08` is the right-operand string case).

## 3. Callee provenance (kind-A) — none

There are **no axioms** and **no deep-model references** in this bundle, so
there is no `axiom_check.py` and G-AX is `skip` (cf. the no-axiom exemplar
django__django-10914). The only callee the changed operators invoke is the
unchanged forcing step `self.__cast()`, which §2 models as the identity onto the
input `forced` (an R-refinement), not as an axiomatized callee: the changed
function's *new* content is purely the binary combination of forced operands,
modeled deeply and concretely. Per SPEC_GUIDE §3, a deeply-modeled changed op is
not a consumed axiom, and here it is not even an A-reference — the combination is
ordinary `++`/`+`, transliterated verbatim and checked by G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13794`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the four
methods (`deferredConcatLeft/Right` → `forced+other` / `other+forced` on `str`;
`deferredSumLeft/Right` → `forced+other` / `other+forced` on `int`) to Python;
the oracle constructs a real lazy proxy (`lazy(lambda v: v, str|int)`) at
`base_commit` **with patch.diff applied** and exercises the actual `+` operator
in both operand positions. They must agree on every fuzzed input.
