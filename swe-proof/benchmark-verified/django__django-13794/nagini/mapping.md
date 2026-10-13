# mapping.md — django__django-13794

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fe886eee36be8022f34cfe59aa61ff1c21fe01d9`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/utils/functional.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `forward_combine(realized, other)` | `__proxy__.__add__(self, other)` — added by the patch inside `lazy()` at `django/utils/functional.py` (after `__mod__`, body line 177; the new method is inserted at line 179) | the first modelled changed method (lazy value on the left of `+`) |
| `reverse_combine(realized, other)` | `__proxy__.__radd__(self, other)` — added by the patch inside `lazy()` at `django/utils/functional.py` (line 182) | the second modelled changed method (reflected/right-operand `+`; lazy value on the right) |
| `realized` (parameter) | `self.__cast()` — `__proxy__.__cast` at `django/utils/functional.py:148-154` | the forced (realized) value of the proxy; an UNCHANGED callee, modelled as an R-refinement (its result is the input value) |
| `other` (parameter) | the `other` argument of `__add__` / `__radd__` | the other operand |
| `Result()` | the value `self.__cast() + other` (`__add__`) / `other + self.__cast()` (`__radd__`) returns | the result of the concatenation |

The pre-patch repo state (for the refinement audit, not referenced from the
consumer spec view): the `__proxy__` class has NO `__add__`/`__radd__`. The
public consequence (`problem_statement`): the `add` template filter
(`django/template/defaultfilters.py:675`) falls into its `value + arg` branch,
which raises `TypeError`, and the surrounding `except Exception: return ''`
collapses the result to the empty string.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the realized value of a text proxy, and the `other` operand in the F2P template-filter cases `test_add08`/`test_add09`) | `List[int]` of Unicode code points | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; `str` concatenation `a + b` ↔ list/`PSeq` concatenation; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self.__cast()` (the forced lazy value) | the input parameter `realized` | `__cast()` forces the wrapped callable and returns its value; the patch does NOT change it. Its result IS the modelled input `realized` — an R-refinement, not an axiom (see §3). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
and the specification is phrased over `PSeq[int]` via `ToSeq`. The integer F2P
case (`test_lazy_add`: `lazy_4() + lazy_5() == 9`) is the same `+` operation;
its tested behaviour (operand combination preserving order, never collapsing to
empty) is what the concatenation spec pins — the `List[int]` carrier models the
headline string-concatenation case (`test_add08`/`test_add09`) while the
operation modelled, ordinary `+`, is exactly the one the int case also exercises.

## 3. Callee provenance — no consumed axiom; `__cast` is an R-refinement

The two patched methods call only:

- `self.__cast()` — the proxy's forcing method (`django/utils/functional.py:148`).
  The patch does NOT change it. It is the realized value of the proxy. Because
  its result is opaque-but-fixed for a given proxy and is simply the LEFT (for
  `__add__`) or RIGHT (for `__radd__`) operand of the modelled `+`, it is
  represented as the read-only input `realized`. This is a **type/value
  R-refinement** of an unchanged callee, exactly like the exemplar treats
  `str(text)` as identity — NOT a `@ContractOnly` axiom. There is no consumed
  axiom and no deep-model reference: the only changed operation is the `+`
  itself, which is concatenation, **modelled deeply** (spelled out as the
  element-by-element fold in the impl regions).

- the binary `+` operator. On `str`/`bytes`/`list`/`int` operands the changed
  code performs ordinary `+`. Modelled deeply as `PSeq[int]` concatenation
  (`ToSeq(realized) + ToSeq(other)` for `__add__`,
  `ToSeq(other) + ToSeq(realized)` for `__radd__`).

Because nothing is axiomatized, `axiom_check.py` (G-AX) has no `@ContractOnly`
to validate against a real callee; it instead validates the deep concatenation
model against the **real** behaviour of the patched methods executed on a live
`lazy()` proxy (an A-reference-style executable soundness check: the real
`__proxy__.__add__`/`__radd__` produce exactly the modelled concatenation —
`forward_combine` resp. `reverse_combine` — on strings AND on the integer F2P
case). Provenance for that check is the patched method bodies themselves:

```python
def __add__(self, other):
    return self.__cast() + other        # realized ++ other

def __radd__(self, other):
    return other + self.__cast()        # other ++ realized
```
