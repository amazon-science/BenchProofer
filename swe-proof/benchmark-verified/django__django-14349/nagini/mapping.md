# mapping.md — django__django-14349

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a708f39ce67af174df90c5b5e50ad1976cec7cb8`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/core/validators.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validate_url(value, accepted)` | `URLValidator.__call__(self, value)` — `django/core/validators.py:101` | the modeled changed function (the URL screen whose forbidden-character check the patch adds) |
| `is_forbidden(c)` | the membership test `self.unsafe_chars.intersection(value)` where `unsafe_chars = frozenset('\t\r\n')` — `django/core/validators.py:95` (attr) / `:105-106` (test, post-patch) | pure spec: a single code point is one of TAB(9)/LF(10)/CR(13) |
| `downstream_validate(accepted)` *(axiom — A-consumed)* | the UNCHANGED remainder of `URLValidator.__call__`: the scheme check (`value.split('://')[0].lower() not in self.schemes`, `:105-107` pre-patch / `:107-109` post-patch), the regex `super().__call__(value)` (`RegexValidator.__call__`, `:43-51`), the IDN/`punycode` retry (`django/utils/encoding.py:203`), and the IPv6 `validate_ipv6_address` recheck (`:278`) | unchanged callee chain the screen defers to; the patch does not touch any of it |
| `InvalidValue` (exception) | `django.core.exceptions.ValidationError` — `django/core/exceptions.py:107` | the rejection both the screen and the remaining validation raise |

The change is a single hunk that (a) adds the class attribute
`unsafe_chars = frozenset('\t\r\n')` and (b) inserts, immediately after the
`isinstance(value, str)` guard and BEFORE the scheme/regex/IDN validation, the
early rejection

```python
if self.unsafe_chars.intersection(value):
    raise ValidationError(self.message, code=self.code, params={'value': value})
```

Everything downstream of that insertion is byte-for-byte unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `value` argument) | `List[int]` of Unicode code points | `value[k]` ↔ `ord(value[k])`; `len(value)` ↔ `len(value)`; an empty `str` ↔ `[]` |
| `self.unsafe_chars.intersection(value)` is truthy | `Exists k. is_forbidden(value[k])` | `frozenset('\t\r\n') ∩ value ≠ ∅` ⟺ some code point of `value` is in `{9,10,13}`; `intersection` over a `str` iterates its characters, so the test is exactly "value contains TAB or LF or CR" |
| `isinstance(value, str)` guard (`:102-103`) | (omitted) | the model's domain is str values (`List[int]`); the new F2P inputs are all `str`, so the guard always passes. The non-str rejection is orthogonal to the change. |
| `raise ValidationError(...)` | `raise InvalidValue()` | user-defined exception stands in for the builtin-carrying `ValidationError` (a builtin exception in an `Exsures` crashes the Nagini translator); only the raised/not-raised control flow is observed. |
| the remaining validation's verdict (accept / reject) | the boolean `accepted` | the single observable bit of the unchanged downstream callee chain — whether it accepts the value. Abstracted exactly as django-13410 abstracts `fcntl.flock`'s world-state by `available`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`;
membership of a forbidden code point is the existential over that list.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `downstream_validate` ↔ the unchanged remainder of `URLValidator.__call__` (A-consumed)

**Callee:** the scheme/regex/IDN/IPv6 validation chain that runs AFTER the new
forbidden-character screen. None of it is touched by the patch. Its only
observable on the model's domain (str values containing none of TAB/LF/CR — the
only path on which `downstream_validate` stands in for it, because the screen is
a no-op there) is whether it accepts the value:

  * it **returns the empty value `None`** (normal completion) exactly when the
    value passes scheme + regex + IDN + IPv6 validation — the `accepted` case;
  * it **raises `ValidationError`** (and nothing else) exactly when the value
    fails any of those checks — the not-`accepted` case.

This is the definitional contract of a Django validator and is the WEAKEST
contract the screen's proof needs: the screen never inspects the verdict, it
only sequences its own check before deferring. The axiom is therefore
`Ensures(accepted is True)` / `Exsures(InvalidValue, accepted is False)`, NOT
any claim about which concrete URLs are valid (that would over-claim).

The axiom additionally carries `Requires(MustTerminate(1))`: the unchanged
downstream chain is a bounded computation that always DELIVERS its verdict —
it returns or raises, never diverges (every axiom_check.py oracle/fuzz input
observes an answer). This lets the caller's own total-correctness obligation
(`validate_url`'s `Requires(MustTerminate(2))`, which forbids a same-spec
implementation from smuggling in an infinite loop and satisfying the
postconditions vacuously) be discharged across the deferral.

**Soundness check (G-AX):** `axiom_check.py` constructs a real `URLValidator`
and runs it on the repository's own valid/invalid URL oracle inputs plus 5000
randomized forbidden-character-free fuzz strings, asserting for each that the
call is total over `{accept → None, reject → ValidationError}` — i.e. it never
produces any other out-of-band signal and never silently accepts a value the
repo marks invalid. The check is restricted to forbidden-character-free values,
which is exactly the domain on which `downstream_validate` abstracts the real
callee. It imports only the standard library plus the Django callee under
abstraction (present in the evaluation container). Exit 0 iff sound.

**Flag dependency:** none. `frozenset('\t\r\n')` and `str.intersection` carry no
configurable flags; the three forbidden code points are fixed literals
(TAB=U+0009, LF=U+000A, CR=U+000D). Recorded here per the SPEC_GUIDE flag-
dependency rule even though it is the empty set.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned seed:** `SEED = 14349` (module constant in `conformance_check.py`).
**Input count:** boundary block (52 curated values) + seeded fuzz, run until
**100 000 inputs have actually been CHECKED** (`N_CHECKED_TARGET = 100_000`,
loop bound `FUZZ_CAP = 400_000`); the script hard-FAILS if the target is not
reached, so the bridge exclusions below cannot erode the count.

**Shadow.** The `# impl-start` … `# impl-end` region of `model.py`, copied
verbatim with only the `Invariant(...)` lines (and their
`# invariants-start`/`-end` markers) removed — the model is Python on this
backend, so there is no transliteration. The `@Pure` helper `is_forbidden` is
copied as a plain function. No `PSeq`/`ToSeq` shim is needed: the impl region's
only carriers are `List[int]` and the user-defined `InvalidValue`.

**`@ContractOnly` callee.** `downstream_validate` has no body to copy, so it is
NOT stubbed with a model: it calls the REAL callee §3.1 axiomatizes — the
unchanged remainder of `URLValidator.__call__` (`django/core/validators.py:107-137`
post-patch), realized as a real patched `URLValidator` instance with the newly
added guard neutralized (`unsafe_chars = frozenset()`), so the call runs exactly
the post-guard body. The shim maps that real call's control flow into the
axiom's terms (return iff accepted, `InvalidValue` iff `ValidationError`) and
asserts the real outcome equals the `accepted` bit bridged in, so the axiom is
exercised on every input rather than assumed.

**Oracle.** The real patched repo function, CALLED (not transliterated):
`django.core.validators.URLValidator.__call__` (§1), with `patch.diff` already
applied to /testbed by the gate. Observable = the three-way call outcome
(normal return / `ValidationError` / any other escaping exception, by type
name — the last is a real third outcome of the unchanged code, e.g. the
`TypeError` from `len(urlsplit(value).hostname)` on `"http://?@[::1]"`).

**Bridge (§2 inverted).** Inputs are generated as concrete `str` and mapped to
the model carrier by `[ord(c) for c in value]`; `InvalidValue` ↔
`ValidationError`; the abstract world-state bit `accepted` is obtained by
running the real unchanged-remainder callee on the same `str`. Non-`str` values
are outside the model's domain (§2 omits the `isinstance` guard) and are not
generated.

**Domain / exclusions.** Every checked input satisfies `validate_url`'s
`Requires` (`Acc(list_pred(value), 1/2)` holds for a freshly built code-point
list; `MustTerminate(2)` is a proof obligation, not an input restriction). One
class is excluded by the BRIDGE, not by the Requires: a forbidden-character-free
value whose unchanged remainder raises a non-`ValidationError` has no boolean
`accepted` that faithfully models it (§3.1's axiom domain is
`{accept → None, reject → ValidationError}`). Those are counted and reported in
the summary line (~2 283 of ~102 300 generated), never silently dropped. The
same values WITH a forbidden character present are kept and checked — they are
exactly where the new screen must take precedence over a downstream crash.

**Branch coverage (asserted, not assumed).** The run fails unless all four impl
paths are taken: loop not entered (empty value), loop body raising (forbidden
code point), and loop completing then deferring to the callee on each of its two
outcomes. Last recorded run: raise=43 664, empty=2 976, defer-accept=19 246,
defer-reject=34 114.

**Recorded verdict.** `G-CONF=pass` — 100 000 checked inputs, 0 disagreements.
Refutation capability was demonstrated before recording: the check exits 1 on
(a) a shadow that screens only the first code point, (b) a shadow with the
forbidden screen removed (the pre-patch body), (c) a shadow whose forbidden set
drops CR, and (d) the true shadow run against the UNPATCHED oracle.
