# mapping.md — django__django-16667

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 02c356f2f3945b8075735d485c3cf48cad991011`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/forms/widgets.py` (the `SelectDateWidget`
composite widget's `value_from_datadict`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `value_from_components(all_blank, all_present, kind)` | `SelectDateWidget.value_from_datadict(self, data, files, name)` — `django/forms/widgets.py:1149` (body 1150-1165) | the modeled changed function |
| `construct_date(kind)` *(axiom — A-consumed)* | `datetime.date(int(y), int(m), int(d))` — CPython stdlib `datetime` C type, called at `django/forms/widgets.py:1159` (inside the `try`) | unchanged calendar-date constructor whose two failure shapes the patch must handle |
| `render_success()` / `success_text()` *(axiom — A-consumed)* | `date_value.strftime(input_format)` — `django/forms/widgets.py:1164` | unchanged success-path rendering callee (canonical date text) |
| `render_out_of_range()` / `out_of_range_text()` *(axiom — A-consumed)* | `"%s-%s-%s" % (y or 0, m or 0, d or 0)` — `django/forms/widgets.py:1163` (the `except ValueError` body) | unchanged out-of-range-path rendering (pseudo-ISO fallback) |
| `zero_zero_zero()` | the literal `"0-0-0"` introduced by the patch (`widgets.py:1164` post-patch) | pure spec: the fixed capacity-overflow sentinel as code points `[48,45,48,45,48]` |
| `absent_text()` | `None` returned by the all-blank branch (`widgets.py:1154`) | pure spec: the empty rendering, the model's marker for an absent value |
| `retrieve_raw()` / `raw_value()` *(axiom — A-consumed)* | `return data.get(name)` — `django/forms/widgets.py:1165` (the not-all-present fallback) | unchanged raw-retrieval callee: the raw value submitted under the field's own (undecomposed) name — `None` when nothing was posted under it, but possibly ARBITRARY text (e.g. `value_from_datadict({'mydate':'2008-4-1'},{},'mydate') == '2008-4-1'` at base_commit). Left fully abstract; the branch is pinned to EXACTLY this callee's value. |
| `DateOutOfRange` (exception) | `ValueError` raised by `datetime.date(...)` (and by `int(...)` on bad text), caught at `widgets.py:1160` | user-defined stand-in (builtin-exception `Exsures` crashes Nagini; §2) |
| `DateCapacityOverflow` (exception) | `OverflowError` raised by `datetime.date(...)` on too-large magnitude, caught by the patch at `widgets.py` post-patch | user-defined stand-in (§2) |

The pre-patch control flow the change extends (for the refinement audit, not
referenced from the consumer spec view): the `try` block at `widgets.py:1158`
catches ONLY `ValueError` (line 1160) and lets `OverflowError` escape, crashing
the request. The patch adds an `except OverflowError: return "0-0-0"` clause.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the three submitted components `y, m, d` (each `Optional[str]`) and the outcome of `datetime.date(int(y), int(m), int(d))` | the booleans `all_blank` / `all_present` + the integer `kind` (0 accepted, 1 out-of-range/`ValueError`, 2 capacity-overflow/`OverflowError`) | `all_blank` ↔ `y == m == d == ""`; `all_present` ↔ `y is not None and m is not None and d is not None`; `kind` ↔ how `datetime.date(int(y),int(m),int(d))` behaves on the submitted text. A blank component is non-`None`, so `all_blank ⇒ all_present` (modeled `Requires`). The discriminating observable is purely WHICH outcome the widget produces, a function of these classifiers. |
| `str` return value (`"0-0-0"`, the pseudo-ISO string, the strftime text, the raw `data.get(name)` value), or `None` | `List[int]` of Unicode code points; specification over `PSeq[int]` via `ToSeq`; an absent value ↔ the empty list | `s[k]` ↔ `ord(s[k])`; `len(s)` ↔ `len`; `None` ↔ the empty code-point list. The encoding `None ↔ []` is sound on every branch where the model ASSERTS emptiness (only the all-blank branch, whose real return is exactly `None`): the three text-producing constructions — `"0-0-0"` (5 chars), the pseudo-ISO `"%s-%s-%s"` (≥5 chars, always two dashes), `strftime` of a real date (non-empty) — are all pinned `len(...) > 0`, so emptiness never collides with them. The not-all-present branch's `data.get(name)` may be `None` OR arbitrary submitted text; the model does NOT assert emptiness there — it pins the branch to the abstract `raw_value()` callee value, faithful in either case. |
| `OverflowError` / `ValueError` (builtin exceptions) | `DateCapacityOverflow` / `DateOutOfRange` (user-defined) | builtin-exception `Exsures` crashes the Nagini translator (SPEC_GUIDE §2); a user-defined class per builtin rejection is the standard stand-in. |
| kwargs/defaults (`input_format`, `data`, `files`, `name`, `self`) | omitted | unobserved by the pinned overflow behaviour; the success/out-of-range renderings that consume them are axiomatised callees. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`;
the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `construct_date` ↔ `datetime.date(int(y), int(m), int(d))` (A-consumed)
**Callee:** CPython `datetime.date(year, month, day)` (the C-implemented
`datetime.date` constructor), applied to the integer parses of the three
submitted components. This is the single expression inside the widget's `try`
block (`widgets.py:1159`); the patch does NOT change it — it only adds a handler
for one of its failure modes.

The axiom encodes EXACTLY the three outcomes the proof needs, and asserts these
two rejection classes are the ONLY ways the constructor can fail:

  * kind 0 — returns normally (the components form a representable, valid date);
  * kind 1 — raises `ValueError` (an out-of-range failure: the components are
    representable but do not form a real calendar date, e.g. month 13, Feb 31,
    year 0, year 10000; also `int("")`/`int("abc")` raise `ValueError`);
  * kind 2 — raises `OverflowError` (a capacity-overflow failure: a component's
    magnitude exceeds the platform's C `long`, e.g. `sys.maxsize + 1`).

**Exhaustiveness / precedence (the soundness crux):** for integer arguments,
`datetime.date` raises ONLY `OverflowError` or `ValueError` and nothing else;
and when a magnitude exceeds the C `long` range the `OverflowError` is raised by
the C-level argument conversion BEFORE any range `ValueError` — so the F2P input
`(sys.maxsize+1, 12, 1)` is a kind-2 (capacity-overflow) outcome, not kind 1.
The axiom is the WEAKEST contract the proof needs (normal-iff-kind-0 plus the two
distinct `Exsures`), never the full calendar semantics. Docs:
https://docs.python.org/3/library/datetime.html#datetime.date .

### 3.2 `render_success` / `success_text` ↔ `date_value.strftime(input_format)` (A-consumed)
**Callee:** `datetime.date.strftime` (CPython stdlib), the unchanged success-path
rendering at `widgets.py:1164`. The axiom claims only that it returns a
**non-empty** code-point list (a rendered date string is never empty); its exact
characters are left abstract (`success_text()` is `@ContractOnly`, value
unconstrained beyond `len > 0`). The success branch returns EXACTLY this callee's
text, pinning the result to the callee rather than a fabricated literal
(directive 8). Unchanged by the patch.

### 3.3 `render_out_of_range` / `out_of_range_text` ↔ `"%s-%s-%s" % (y or 0, m or 0, d or 0)` (A-consumed)
**Callee:** the `%`-format pseudo-ISO fallback at `widgets.py:1163` (the existing
`except ValueError` body, unchanged by the patch). The axiom claims only that it
returns a **non-empty** code-point list (the format always emits three
dash-separated fields, ≥ 5 chars). Exact characters abstract. The out-of-range
branch returns EXACTLY this callee's text. Unchanged by the patch.

### 3.4 `retrieve_raw` / `raw_value` ↔ `return data.get(name)` (A-consumed)
**Callee:** the dict lookup under the field's own (undecomposed) name at
`widgets.py:1165` (the not-all-present fallback, unchanged by the patch). The
real callee returns the RAW submitted value under the bare field name: `None`
when nothing was posted under it (the shape the gold tests observe:
`(None,'12','1') -> None` etc.), but possibly ARBITRARY NON-EMPTY text when a
value WAS posted under the bare name — executing the real base_commit widget,
`value_from_datadict({'mydate': '2008-4-1'}, {}, 'mydate') == '2008-4-1'`.
The axiom is therefore left FULLY ABSTRACT (`raw_value()` is `@ContractOnly`
with the trivially-true `len(Result()) >= 0`; no emptiness or non-emptiness
claim). The not-all-present branch is pinned to EXACTLY this callee's value
(`ToSeq(Result()) == raw_value()`), so an implementation can satisfy it only by
returning the callee's own result — it can neither hard-code an absent value
nor fabricate text. Being contentless, the axiom needs no executable probe;
its faithfulness claim is structural (the branch defers to the unchanged
callee), matching the real `return data.get(name)` whatever the datadict holds.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `datetime.date` on
boundary inputs (each rejection class alone, the exact F2P `sys.maxsize+1`
overflow input, calendar-edge `ValueError`s, valid dates) plus randomized fuzz,
and asserts: every kind-0 input constructs without raising; every kind-1 input
raises EXACTLY `ValueError`; every kind-2 input raises EXACTLY `OverflowError`;
and NO input escapes with any other exception class — i.e. `{OverflowError,
ValueError}` is exhaustive for integer arguments (so the widget's two-handler
`try` covers every failure). It also confirms the strftime / pseudo-ISO
renderings are non-empty and the `"0-0-0"` sentinel decodes to `[48,45,48,45,48]`.
It imports only the standard-library `datetime`/`sys` modules (the very callee
the widget invokes); nothing repo-specific. Exit 0 iff sound.

## 4. G-CONF (conformance_check.py)

Differential check: the impl region run directly (contract-free shadow, with
the @ContractOnly callees bound to the real repo-relied functions above)
against the real patched `SelectDateWidget.value_from_datadict` in-container.
Boundary component cross-product plus 100000 fuzz probes; pinned fuzz seed:
**16667** (the instance number).
