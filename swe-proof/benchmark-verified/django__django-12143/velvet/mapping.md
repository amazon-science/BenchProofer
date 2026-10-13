# mapping.md — django__django-12143

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5573a54d409bb98b5c5acdb308310bed02d392c2`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `editedObjectPks (pfx pkname items)` | `_get_edited_object_pks(self, request, prefix)` — `django/contrib/admin/options.py:1633` | the modeled changed function: the comprehension that selects POST values whose key identifies an edited object |
| `matchesKey (pfx pkname key)` | the per-key decision `pk_pattern.match(key)` where `pk_pattern = re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), self.model._meta.pk.name))` (`options.py:1634-1636` post-patch) | pure spec: whether one request key names an edited object |
| `stripPrefix` | the literal-anchored leading segment of that regex — the `re.escape(prefix)` portion and the literal `pk.name` portion | pure spec: exact (literal) character-sequence match of a fixed string at a position |
| `takeDigits` | the `\d+` portion of the regex (a nonempty run of ASCII decimal digits) | pure spec: maximal leading decimal-digit run |
| `atEnd` | the `$` anchor of the regex | pure spec: end-of-input position (with `re`'s default trailing-`\n` tolerance) |
| `editedPks` | the list comprehension `[value for key, value in request.POST.items() if pk_pattern.match(key)]` (`options.py:1637`) | pure spec: the in-order selection over the request items |

There are **no axiomatized callees** (no `axiom`, no `:|` stub): the only repo
operation the change touches is the construction of `pk_pattern` and its use as a
matcher, and that matcher is modeled **deeply** by `matchesKey`/`stripPrefix`/
`takeDigits`/`atEnd`. `self.model._meta.pk.name` is bound to the spec parameter
`pkname` (an opaque, fixed identifier string supplied by the caller); it is data,
not a callee, so it carries no axiom. `request.POST.items()` is bound to the spec
parameter `items` (an ordered list of key/value pairs) — likewise data.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a request key / value `str`, and the `prefix`/`pk.name` `str` | `List Char` | `s` (Python str) ↔ its `List Char`; `len(s)` ↔ `l.length`; `str` slicing/concat ↔ `List.drop`/`++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `request.POST.items()` — the ordered (key, value) multidict items | `List (List Char × List Char)` | each `(key, value)` `str` pair ↔ a `(List Char × List Char)`; iteration order ↔ list order. The selection is order-preserving and per-item, so multidict identity beyond order/content is unobservable to `_get_edited_object_pks`. |
| `re.compile(...).match(key)` truthiness for `r'{P}-\d+-{N}$'` (P = `re.escape(prefix)`, N = `pk.name`) | `matchesKey pfx pkname key : Bool` | `.match` is anchored at the start (implicit `\A`); `re.escape(prefix)` matches `prefix` as a literal sequence ⇔ `stripPrefix pfx`; `-` ⇔ the `'-'` separators; `\d+` ⇔ `takeDigits` (nonempty); `pk.name` is a Python identifier (no regex metacharacters) so it matches literally ⇔ `stripPrefix pkname`; `$` ⇔ `atEnd` |

### 2.1 The `$` / `atEnd` correspondence (faithfulness note)
Python's `re` `$` (without `re.MULTILINE`) matches at the end of the string **or**
just before a single trailing `\n`. `atEnd cs := cs.isEmpty || cs == ['\n']`
captures exactly this: after the literal `pk.name`, either nothing remains, or
exactly one trailing newline remains. Verified mechanically against the real
`re` engine in the fuzz harness (§4) over keys carrying trailing `\n`.

### 2.2 The `\d+` / `takeDigits` correspondence (faithfulness note)
The pattern uses `\d` (not `[0-9]`), and the matcher is built with no `re.UNICODE`
suppression, so on Python 3 `str` patterns `\d` is Unicode-aware: it accepts the
decimal digits of every decimal number system (Unicode general category Nd), not
only `'0'..'9'`. The model reproduces this exactly: `isDigit` tests membership in
`digitRanges`, the inclusive code-point bounds of every Nd run per the Unicode
data shipped with the instance image's Python (unidata 9.0.0; the range table was
extracted mechanically in-container by enumerating `re.compile(r'\d').match(chr(i))`
over all scalar values — 54 runs, 580 code points, `0x30-0x39` through
`0x1E950-0x1E959`). `takeDigits` therefore takes the maximal leading run of
*Unicode* decimal digits, matching the real engine on every key, including
non-Latin-digit indices. The G-CONF fuzzer (§4) exercises both sides on non-Latin
decimal digits and on digit-like non-Nd near-misses (superscripts, fractions,
circled digits) so this correspondence is differentially tested, not assumed.

## 3. Callee provenance (kind-A) — none

There are no consumed axioms and no deep-model references to an external callee:
the entire changed behavior is the in-function matcher, modeled deeply in the
`pure` region. Consequently the bundle ships **no `axiom_check.py` with axioms**;
`axiom_check.py` is present only as an explicit no-op that records "no axioms"
and exits 0 (G-AX). The soundness of the deep matcher model is checked instead by
G-CONF, which differential-tests the R/I shadow against the **real patched
regex** running in-container.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12143`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`matchesKey`/`stripPrefix`/`takeDigits`/`atEnd`/`editedPks` (all R/I-tagged ops)
to Python and compares against the ORACLE — the real patched
`_get_edited_object_pks` behaviour, i.e. `[v for k,v in items if
re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname)).match(k)]`, the gold
patch applied at `base_commit`. There are no A-tagged callees to leave as real
(§3), so the shadow is pure R/I.
