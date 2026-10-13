# mapping.md — django__django-14349

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a708f39ce67af174df90c5b5e50ad1976cec7cb8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the axiom.

Repo file under change: `django/core/validators.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateUrl (value) (baselineVerdict)` | `URLValidator.__call__(self, value)` — `django/core/validators.py:101` | the modeled changed function (URL validator entry point) |
| `containsForbidden (value : List Char)` | the new screen `self.unsafe_chars.intersection(value)` (treated as a boolean), against `unsafe_chars = frozenset('\t\r\n')` — added at `django/core/validators.py:94` (class attr) / `:105` (the guard) post-patch | pure spec: does `value` contain a forbidden control character |
| `isForbidden (c : Char)` | membership of a single code point in `frozenset('\t\r\n')` | pure spec: is one code point forbidden |
| `CallOutcome` (`accepted`/`rejected`/`crashed`) | how one `__call__` observably ends: return normally / raise `ValidationError` / any other exception escapes | pure spec: the observable outcome of a validation call |
| `BaselineOutcome` (`accepts`/`rejects`/`crashes`) + `liftBaseline` | the same three-way classification of the UNCHANGED post-`isinstance` body's ending; `liftBaseline` is the identity embedding of that classification into the call's observable outcome | pure spec: the unchanged validation's outcome and how it surfaces |
| `baselineOutcome` *(axiom — A-reference)* | the WHOLE pre-existing body of `URLValidator.__call__` *after* the `isinstance` guard — scheme split + `RegexValidator.__call__` (the `regex` match), the IDN/punycode retry, the IPv6 netloc check, and the host-length check (`validators.py:106-141` post-patch ≡ `:104-139` pre-patch). Unchanged by the patch. | the unchanged structural validation's three-way outcome |

`baselineOutcome` is an **A-reference**: it abstracts the unchanged validation
as a deterministic, total function of the value's code points onto THREE
outcomes — `accepts` (returns normally), `rejects` (raises `ValidationError`,
the designated refusal), `crashes` (an unrelated error escapes). The third
outcome is REAL unchanged-repo behavior: on inputs like `"http://?@[::1]"`
(and `"ftp://?@[::1]"`, `"https://?@[::1]"`, `"ftp://?q@[::ffff:1.2.3.4]"`)
`urlsplit(value).hostname` is `None` and the host-length check
`if len(urlsplit(value).hostname) > 253:` raises
`TypeError('object of type NoneType has no len()')` — both at base_commit and
with patch.diff applied, since the patch does not touch that code. The
artifact does not model *how* that validation decides; it constrains only that
the new forbidden-character screen is applied as an independent early check
**before** it (SPEC_GUIDE directive 7: never axiomatize the operation the
patch changes — the changed op is `containsForbidden`, modeled deeply; the
axiom is the *unchanged* surrounding validation, whose outcome — including a
crash — passes through untouched when the screen does not fire). The
`isinstance(value, str)` guard before both is outside scope: F2P inputs at the
change site are all `str` (mapping.md §2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `value` (a Python `str`) | `List Char` | `s` (Python str) ↔ `s`-as-`List Char`; per-code-point; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `frozenset('\t\r\n').intersection(value)` truthiness | `containsForbidden value : Bool` | non-empty intersection (Python truthy) ↔ `true`; empty (falsy) ↔ `false` |
| how `__call__` ends: return normally / `raise ValidationError` / another exception escapes | `outcome : CallOutcome` | return ↔ `CallOutcome.accepted`; `raise ValidationError` ↔ `CallOutcome.rejected`; any other exception escaping (e.g. the hostname-None `TypeError`) ↔ `CallOutcome.crashed`. The F2P test observes raise-vs-no-raise of `ValidationError`; the third constructor keeps the model faithful on inputs where the unchanged code lets a different error escape. `message`/`code`/`params` payload is not observed by the F2P list and is omitted; the crashed constructor likewise abstracts the escaping error's identity (G-CONF additionally compares the exception type on crashes and finds no disagreement). |
| the unchanged validation's ending on `value` | `baselineVerdict : BaselineOutcome`, required `= baselineOutcome value` | post-`isinstance` body returns ↔ `accepts`; raises `ValidationError` ↔ `rejects`; another exception escapes ↔ `crashes`; `liftBaseline` maps these to the call's observable outcome (identity embedding) |

The forbidden code points are `\t` (U+0009), `\r` (U+000D), `\n` (U+000A) —
`isForbidden`. Lean `Char`/`List Char` indexing is total and sound; the carrier
is `List Char` because the screen is per-code-point membership.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `baselineOutcome` ↔ the unchanged validation body (A-reference)
**Callee:** the body of `URLValidator.__call__` from the scheme split through the
host-length check — everything the patch leaves untouched. It is a pure function
of `value` (no mutation of `self`/globals on the F2P paths; the `regex` and
`schemes` are class constants), and deterministic.

The axiom claims **only** that this is a total, deterministic function of the
value's code points onto the three outcomes `accepts`/`rejects`/`crashes` — it
pins **no specific verdict**. (SPEC_GUIDE directive 8: the postcondition is
grounded in the input via `containsForbidden`; `baselineOutcome` is never used
as an answer-key, only as the pass-through unchanged behavior when the screen
does not fire. Pinning concrete verdicts would over-claim about an unchanged
callee — directive 7.)

**Soundness check (G-AX):** `axiom_check.py` constructs a real `URLValidator`
in-container and, for each fuzzed `value`, (a) runs the **prepatch** validator
(the unchanged body, reconstructed by skipping the new guard) twice and asserts
the three-way outcome class (return / `ValidationError` / other-exception,
incl. the exception's type) is **deterministic and total** onto those three
classes — the only properties the axiom asserts — and asserts the crash class
is actually exercised (the hostname-None family, e.g. `"http://?@[::1]"`); and
(b) checks
`containsForbidden value == bool(frozenset('\t\r\n').intersection(value))` (the
A-reference: the deep model equals the real screen) on boundary + fuzz inputs.
Imports only stdlib + django. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14349`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`isForbidden`/`containsForbidden` and the
`if … then rejected else liftBaseline baselineVerdict` control flow to Python;
the A-tagged `baselineOutcome` is left as the **real** unchanged validator's
three-way outcome (run the real post-`isinstance` body, not a model), and the
oracle is the patched `URLValidator.__call__`'s three-way outcome (return /
`ValidationError` / other exception, with the exception type compared on
crashes). Boundary inputs include the F2P matrix and the hostname-None crash
family.
