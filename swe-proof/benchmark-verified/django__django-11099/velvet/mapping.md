# mapping.md — django__django-11099

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d26b2424437dabeeca94d7900b37d2df4410da0c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
absence of axioms (the changed behaviour — the end-of-input anchoring — is
modeled deeply; the UNCHANGED per-code-point class membership is a free input).

Repo file under change: `django/contrib/auth/validators.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateName (isAllowed) (s : List Char)` | `ASCIIUsernameValidator` / `UnicodeUsernameValidator` acceptance — `django/contrib/auth/validators.py:9-15` and `:18-25` (their `regex` class attribute, evaluated by the inherited `validators.RegexValidator.__call__`) | the modeled changed acceptance decision (accept = no `ValidationError`), **parametric** in the per-code-point class |
| `isAllowed : Char → Bool` (free method parameter) | the character class `[\w.@+-]` **under the validator's regex flags** — `\w` is ASCII word chars for `ASCIIUsernameValidator` (`re.ASCII`) and Unicode word chars for `UnicodeUsernameValidator` (`flags=0`) | UNCHANGED building block, left abstract: the gold patch does not touch which single code points are in the class, only the end anchoring. The spec quantifies over every `isAllowed`, so it makes NO claim about class membership (in particular none about non-ASCII letters such as `é`). |
| `allowedAll isAllowed (s : List Char)` | the `+` quantifier applying the class to every code point | pure spec: every code point is in the class |
| `validName isAllowed (s : List Char)` | the whole pattern `^[\w.@+-]+\Z` post-patch: non-empty AND all-in-class AND no stray end-of-input code point | pure spec: the acceptance predicate, parametric in the class |

No callee is axiomatized. The behaviour that CHANGED — the universal
quantification up to the true end of input (the `$`→`\Z` anchoring) — is
modeled **deeply** (the `pure` region). The per-code-point class membership,
which the patch leaves untouched and whose exact Unicode `\w` boundary the
tests do not exercise, is a **free input** (`isAllowed`): the `ensures` holds
for every value of it, so nothing about it is asserted and nothing needs a
G-AX validation. Instantiating `isAllowed` at each validator's real class (this
table's binding) is the single R-refinement leg, refuted by G-CONF.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `value` : `str` (the username argument of `RegexValidator.__call__`) | `List Char` | `s` (Python str) ↔ `s` as `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`; per-code-point |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `re.match(pattern, value)` is non-`None` (no `ValidationError`) | `validName isAllowed s = true` | accept ↔ `true`; the `ValidationError` raise ↔ `false` |
| one-code-point membership in `[\w.@+-]` under the validator's flags | the free input `isAllowed : Char → Bool`, instantiated per validator | ASCII validator: `[A-Za-z0-9_.@+-]` membership; Unicode validator: Unicode `\w` (word character) or one of `. @ + -`. The spec is parametric, so this instantiation carries no proof obligation; G-CONF differential-tests it. The discriminating F2P case is the trailing line terminator, which is in NO `\w`/punctuation class under either flag set. |
| `\Z` (end of string, post-patch) | absence of ANY out-of-class code point through the very last one — no code point is dropped or exempted before the check | the `$`→`\Z` fix: `$` would tolerate one trailing newline; `\Z` does not. Since no `\w` class contains U+000A, a trailing `'\n'` is rejected under every faithful instantiation. |

`List Char` indexing is total and sound. The carrier is `List Char` because the
operation is per-code-point.

## 3. Callee provenance

None (no axioms; `conf_skip = false`). The changed behaviour — quantification to
the true end of input — is the deep `allowedAll`/`validName` model. The
unchanged per-code-point class is the free input `isAllowed`; because the spec
holds for every value of it, it is a spec parameter, not an axiomatized callee,
and there is no axiom about the regex engine.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **11099**. The R/I shadow
is `validName` transliterated to Python and **instantiated at each validator's
real class** per §2 (`s != "" and all(isAllowed(ch) for ch in s)`, with
`isAllowed` = ASCII word chars + `.@+-` for the ASCII validator and Unicode
word chars + `.@+-` for the Unicode validator); the oracle is the patched
validator behaviour — preferentially the real patched validators (accept = no
`ValidationError`), with a documented fallback to
`re.search(r'^[\w.@+-]+\Z', value[, re.ASCII])` transliterating the patched
regex when the live validator cannot be imported. The fuzz set includes
trailing-newline candidates (the discriminating F2P case) and non-ASCII
letters (exercising the per-mode instantiation).
