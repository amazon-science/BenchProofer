# mapping.md — psf__requests-1724

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1ba83c47ce7b177efe90d5f51f7760680f72eda0`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalize_method(chars, native)` | the method-handling step of `Session.request` — `requests/sessions.py:278` (body line 312-314: `req = Request(method = method.upper(), …)`) | the modeled changed behaviour: the method carried into the constructed `Request` |
| `to_native(chars)` *(axiom — A-consumed)* | `builtin_str` — `requests/compat.py:95` (py2) / `:111` (py3); invoked post-patch at `requests/sessions.py` (`method = builtin_str(method)`) | unchanged native-text-flavour constructor the patch adds a call to before `.upper()` |
| `native_form(flavour)` *(axiom — opaque, A-consumed)* | the native text flavour itself: the result *type* of `builtin_str` — `str` (the byte-`str`) on py2, `str` on py3, `requests/compat.py:95`/`:111` | the property "this flavour is the native one", which a code-point carrier cannot express as a value; it has no body, `to_native` is its only source, and the flavour postcondition demands it |
| `upper_cp(c)` / `upper_seq(s)` *(deep model — A-reference)* | `str.upper` — CPython builtin, called as `method.upper()` at `requests/sessions.py:314` | pure spec: case-normalisation as a per-code-point ASCII upper map; the deep model of the **unchanged** `str.upper`, validated `upper_seq == str.upper` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `TextToken(chars, native)` | the `str`/`unicode` text value of `method`, and the `method` field of the constructed `Request` (`requests/models.py` `Request.method`) | minimal carrier of the two touched aspects of a text value: code-point content + native flavour |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a text value (`method`: a `str` on py3, a `str`/`unicode` on py2) | `TextToken` = (`chars: List[int]` of Unicode code points, `native: bool`) | `s[k]` ↔ `chars[k] == ord(s[k])`; `len(s)` ↔ `len(chars)`; the byte-`str`/native flavour ↔ `native == True`; the `unicode`/non-native flavour ↔ `native == False` |
| a text value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(chars)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `Request(method = …, url = …, …)` constructor (`requests/sessions.py:313`) | projection onto the `method` field only | the bug touches only `method`; every other `Request` argument (`url`, `headers`, `files`, `data`, `params`, `auth`, `cookies`, `hooks`) is forwarded unchanged and is irrelevant to the tested behaviour, so it is omitted from the model. |

`str` indexing/iteration is banned in Nagini, so the content carrier is
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`. The
flavour aspect (native vs. non-native) cannot be expressed by code points
alone — it is the *type* of the text object — so it is carried as an explicit
boolean field on `TextToken`. This is the precise aspect the bug concerns
(directive 5: `chars` is read-only, held at `Acc(list_pred(chars), 1/2)`; the
result is a freshly-constructed `TextToken` at full permission).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `to_native` ↔ `builtin_str` (A-consumed)
**Callee:** `requests.compat.builtin_str`. In `requests/compat.py` the name is
bound to the native string constructor **before** the module rebinds the
public `str` name:

```python
if is_py2:
    builtin_str = str          # the byte-str constructor
    bytes = str
    str = unicode              # public str is now unicode
    ...
elif is_py3:
    builtin_str = str          # py3: builtin_str IS str
    str = str
    ...
```

So `builtin_str(method)` always produces a value of the **native** text
flavour — a byte-`str` on py2 (the flavour the HTTP header assembly requires),
the ordinary `str` on py3 — independent of whether `method` was a `unicode`
(py2) or any other object.

`to_native` is read as **the flavour of the value that constructor produces for
the given content**, and the axiom encodes only the single property the proof
consumes: that flavour is a native one — `Ensures(native_form(Result()))`, with
`native_form` the opaque companion property below. It does **not** claim
character preservation (not needed — the content fold operates on the original
`chars`, which `builtin_str` leaves unchanged for the ASCII method names the
tests use) and does **not** claim termination/no-raise beyond what is needed.
This is the **weakest** contract the flavour postcondition needs.

**Why not `Ensures(Result() == True)`.** That contract names the produced
flavour with a literal, and a literal is something a caller can write down
itself: with a flavour postcondition of the shape `Result().native == True` —
a shape this bundle deliberately does **not** use — an implementation could hand
`True` to the carrier, satisfy the clause by `True == True`, and never invoke the
constructor at all — the ungrounded-oracle
trap of `spec_guide.md` directive 8 ("the caller discharges `P ⇒ Result()==2`
with a literal `return 2`, never invoking the helper"). It is not a theoretical
hole: an implementation of that shape does verify against the weaker
clause, and the tree its faithful refinement
produces — the supplied method never coerced — leaves a `unicode` method
non-native, where `test_requests.py::RequestsTestCase::test_unicode_method_name`
fails deterministically in the instance image (client-side `UnicodeDecodeError`
during header assembly, no network involved; PASSES once the coercion is
present). Leaving the produced flavour uninterpreted closes it: the only way to
satisfy `Result().native == to_native(ToSeq(chars))` is to apply `to_native` to
the supplied content, which refines to a real call on the supplied method.

### 3.1a `native_form` ↔ the native text flavour (A-consumed, opaque)
**Callee/aspect:** the *type* of `builtin_str`'s result — the byte-`str` on py2
(`requests/compat.py:95`), `str` on py3 (`:111`). A sequence-of-code-points
carrier cannot express this aspect as a value (both flavours hold the same code
points), and it is the entire subject of the change, so it is carried as the
opaque property `native_form` over the flavour bit. It has **no body**: nothing
computes it, so no implementation can assert it of a flavour of its own
choosing; `to_native` is its only source (`Ensures(native_form(Result()))`) and
the flavour postcondition (`Ensures(native_form(Result().native))`) its only
consumer. "The carried method is native" is thereby checkable rather than
merely claimable.

**Soundness check (G-AX):** the same executable check as `to_native` — the real
`builtin_str` is called on native, `bytes` and `unicode` arguments and its
result asserted to be of the native type on the running interpreter. That
assertion IS `native_form` of the flavour it yields; an unsound axiom would be a
`builtin_str` result that is not native, which is what axiom_check.py hunts.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`requests.compat.builtin_str` and asserts `type(builtin_str(v)) is str` (the
native flavour on the running interpreter) for native, bytes, and unicode
arguments. On the Python-2 runtime the issue reports, `builtin_str` is the
byte-`str` constructor, so the produced value is byte-`str` (native), never
`unicode` — which is exactly the fix.

### 3.2 `upper_seq` deep model ↔ `str.upper` (A-reference)
**Callee:** CPython `str.upper`, invoked as `method.upper()`. The
case-normalisation is **unchanged** by the patch (the patch only inserts the
coercion *before* it); it is modelled **deeply** by the `@Pure` fold
`upper_seq` (with `upper_cp`) in the `pure` region — there is **no `upper`
axiom** the proof consumes. The deep model is validated equal to the real
callee out-of-band by axiom_check.py (G-AX). On the ASCII domain that HTTP
method names inhabit (code points 0–127), `str.upper` is exactly:

  `'a'..'z' (97..122) → 'A'..'Z' (65..90)`, every other code point unchanged,

which is what `upper_cp` / `upper_seq` encode. G-AX asserts
`upper_seq(s) == str.upper(s)` over all 128 ASCII code points (exhaustive
single-character sweep), the ten HTTP method names, and 20 000 randomized ASCII
strings — 0 mismatch. (The model claims faithfulness only on this ASCII method
domain; full-Unicode `str.upper` has locale/multi-char expansions outside it,
which the tested method names never exercise.) Docs:
https://docs.python.org/3/library/stdtypes.html#str.upper.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: does the model agree with
the REAL patched repo code? Run in-container with the gold patch applied.

**Shadow.** The `# impl-start`/`# impl-end` region of `model.py`
`normalize_method`, copied verbatim with only the contract calls stripped
(`Requires`/`Ensures`/`Invariant`/`Assert` + the `# invariants-*` markers) —
no restructuring. The `@Pure` helpers `upper_cp`/`upper_seq` (§1, pure region)
are copied over the same way; `upper_seq` is additionally compared to the same
oracle as a loop-independent path. `PSeq`/`ToSeq` are realized by an immutable
tuple shim (`take`/`drop`/`+`/`len`/`[]`/`==`). The `@ContractOnly` callee
`to_native` has no body to copy, so it is **not** stubbed to its axiom
`Ensures(native_form(Result()))`: it calls the real callee §3.1 names,
`requests.compat.builtin_str`, on the real supplied value at its real supplied
flavour and returns `type(produced) is builtin_str`. The axiom is exercised,
not assumed.

**Oracle — called, not transliterated.** The real patched
`requests.sessions.Session.request` (§1: `requests/sessions.py:278`, method
step at 312-314). A real `Session` is constructed and `request` invoked; the
observable is read off the real `Request` the real code builds. Only two
members strictly downstream of the modeled step are intercepted:
`prepare_request` is wrapped to capture `Request.method` (the modeled
observable, §2 "projection onto the `method` field only") before delegating to
the real one, and `send` is stubbed to a sentinel (no live socket needed; the
modeled step is complete before it). No patched line is copied.
`_assert_patched()` aborts with exit 2 if `builtin_str(method)` is absent from
the imported source, so an unpatched container is an error, never a green.

**Runtime.** The instance image runs **Python 2.7.18** (conda env `testbed`).
That is the interpreter the reported failure is about, and the only one on
which the native/non-native text split this bundle models (`str` vs `unicode`,
`requests/compat.py:95`) exists at all. `conformance_check.py` and
`axiom_check.py` are therefore written to the Python-2 language (no `typing`
import -- absent from the 2.7 stdlib, and the impl region's `List[int]` is a
type *comment*; no underscore numeric literals; ASCII source), so that the
comparison executes on the interpreter that hosts the real code.

**Type bridge (§2 inverted).** `chars: List[int]` -> the text with those code
points, and `native` selects the runtime flavour of that text. On the Python-2
runtime the bridge is exact and needs no stand-in: `True` -> the native
byte-`str` (what `builtin_str` is bound to, `requests/compat.py:95`), `False`
-> `unicode` -- precisely the flavour §2 pairs with `native == False`, and
precisely the flavour the reported failure supplies (`method=u'POST'`). Off-image
(py3, where `builtin_str is str` and the non-native flavour has no builtin
inhabitant) the script falls back to `collections.UserString`; a startup guard
`_assert_flavours_distinct()` exits 2 rather than certify a vacuous flavour
comparison if the non-native carrier ever IS `builtin_str`.
Reading back: `m` -> `([ord(ch) for ch in m], type(m) is builtin_str)`.
Generation runs in the abstract direction, so every input satisfies
`Requires(Acc(list_pred(chars), 1/2))` by construction.

**Observables.** Both postconditions, per input: (1) content
(`ToSeq(Result().chars) == upper_seq(ToSeq(chars))`) and length preservation;
(2) flavour (`Result().native == to_native(ToSeq(chars))`, whose nativeness is
`native_form`) against the real carried method's nativeness, for **both**
supplied flavours — the aspect the fix is about, so a content-only check would
also pass on the prepatch behaviour. Because the shadow computes the flavour by
calling the REAL `builtin_str` (above), this compares the model's flavour clause
against the real carried flavour rather than against the constant `True`.

**Inputs.** 103 026 total; **pinned seed `SEED = 17242026`**. Domain: ASCII code
points 0-127 x {native, non-native} flavour. Exhaustive to length 2 in both
flavours (2 empty + 256 singleton + 32 768 pairs), which takes every branch of
the impl region — loop entered 0/1/2 times, `upper_cp` on a lowercase letter
and on a non-letter at each position, `to_native` on a native and a non-native
argument — then 70 000 seeded fuzz inputs (lengths 0-24) over the same domain
to pass 1e5. Exhaustive-then-fuzz on the same space, not a sample of it.

**Declared domain boundary.** Non-ASCII code points are excluded, matching the
faithfulness claim §3.2 already records for the `upper_seq` deep model. This is
a pre-existing, documented boundary of the frozen model with concrete
witnesses (real `str.upper`: `é`->`É`, `ß`->`SS`, `µ`->`Μ`, `ı`->`I`; the
per-code-point ASCII map yields none of these), not a domain narrowed to route
around a disagreement. Such code points are not RFC-7230 method tokens and are
unreachable from the tested behaviour. The exclusion is reported in the
script's structured JSON line as `declared_domain_boundary`, so it is visible
rather than silent.

**Negative controls** (run out-of-tree on the py2 image; the bundle ships only
the clean script): prepatch flavour echo (`native_flavour = native`) -> 51 518
disagreements; skip the upper on the first character -> 35 670; identity
instead of the upper map -> 73 048; unpatched oracle -> exit 2. Additionally,
running the clean script against the **prepatch** oracle (startup assert
bypassed) disagrees on `flavour` at exactly the `unicode`-supplied inputs
(first witnesses `u''`, `u'\x00'`, ...), i.e. the check pins the fixed
behaviour and not merely the unchanged case-normalisation. The check is capable
of failing.

**Recorded verdict.** `G-CONF=pass` — 103 026 inputs, 0 disagreements.
