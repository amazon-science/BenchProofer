# mapping.md — psf__requests-6028

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0192aac24123735b3eaf9b08df46429bb770c283`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change (gold patch.diff): `requests/utils.py`.

The modeled site is the function that re-assembles a URL from the components a
URL splitter returns and re-emits it with a scheme. The discriminating logic of
the fix lives entirely in how the URL's **authority** component is rebuilt: the
credentials that the splitter exposed in a separate slot must be folded back
into the authority, otherwise they are dropped on re-assembly. That rebuild is a
self-contained, pure string computation (see §3), modeled by `buildAuthority` /
`assembleAuthority`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildAuthority` | the authority-reconstruction segment of `prepend_scheme_if_needed(url, new_scheme)` — `requests/utils.py:960` (body lines 973-975 + the patched 977-980-region) | the modeled changed slice: produce the authority string the URL is re-assembled with |
| `assembleAuthority` (pure deep model) | post-patch: `netloc = '@'.join([auth, netloc])` when `auth` is truthy, else `netloc` unchanged | pure spec: fold credentials back into the authority when present |
| `authorityBase` (pure deep model) | `netloc = parsed.netloc; if not netloc: netloc, path = path, netloc` (lines 973-975) | the parser-quirk fallback: pick the path slot for the host portion when the authority slot is empty |
| `userinfo : List Char` | `auth` — element 2 of `parse_url(url)` (`scheme, auth, host, port, path, query, fragment = parsed`, line 967) | the optional credentials slot the splitter exposes |
| `authoritySlot : List Char` | `parsed.netloc` (line 973) | the parser's authority/host-portion slot |
| `fallbackSlot : List Char` | `path` — element 5 of `parse_url(url)` (line 967) | the path slot, which the parser quirk may have stashed the host portion in |

The two callees bracketing the modeled slice are **unchanged** and exercised
end-to-end by G-CONF rather than axiomatized (§3.1):
- upstream: `urllib3.util.parse_url` (`requests/utils.py:24`) — splits `url` into
  the seven-tuple whose `auth`/`netloc`/`path` slots feed `buildAuthority`.
- downstream: `urlunparse` (imported `requests/utils.py:33` from `requests.compat`,
  i.e. `urllib.parse.urlunparse`) — re-assembles `(scheme, netloc, path, '',
  query, fragment)` into the final URL (line 982).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `auth : str`, `netloc : str`, `path : str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; string literals ↔ `"…".toList`; the single `@` separator ↔ `['@']` |
| Python truthiness of `auth` (`if auth:`) | `userinfo = []` test | a `str` is falsy iff empty, so `if auth:` ↔ `userinfo ≠ []` and the empty-string branch ↔ `userinfo = []`. (`parse_url` never yields a non-`None` empty `auth`; `None` ↔ `[]` under the bridge — see §3.) |
| Python truthiness of `netloc` (`if not netloc:`) | `authoritySlot = []` test | `if not netloc:` ↔ `authoritySlot = []`; the fallback assigns the path slot in that case ↔ `authorityBase` picks `fallbackSlot` |
| `'@'.join([auth, netloc])` | `userinfo ++ ['@'] ++ base` | join of a two-element list with `'@'` ↔ left ++ `['@']` ++ right |

`parse_url`'s `auth`/`netloc`/`path` slots are `Optional[str]` (`None` when the
component is absent). The G-CONF bridge maps `None` and `''` alike to the empty
`List Char` `[]` for the two slots `buildAuthority` reads as values, and maps the
truthiness tests directly (`None`/`''` are both falsy). This is faithful because
the modeled slice only ever *reads* `auth`/`netloc`/`path` through `if`-truthiness
and string concatenation; it never distinguishes `None` from `''`. The one place
the original `None` identity still matters — the post-swap `path` that flows into
`urlunparse` — is **outside** the modeled authority slice and is reproduced
verbatim in the conformance shadow (§3.1), not by `buildAuthority`.

## 3. Callee provenance & multi-site handling

### 3.1 No axioms — fully deep model (band: pure-data)
The modeled authority rebuild calls NO unchanged callee: the authority string is
computed entirely from the three input slots (`userinfo`, `authoritySlot`,
`fallbackSlot`) by truthiness tests and concatenation. So **`axioms = []`,
`deep_model_references = []`**, and there is **no load-bearing axiom**; G-AX is
therefore a **skip** (`axiom_check.py` exits `status=skip`) — the
django__django-11138 / django__django-14376 no-axiom precedent.

The two real callees that bracket the slice (`parse_url` upstream, `urlunparse`
downstream) are **unchanged by the patch** and are run **live** in
`conformance_check.py` (G-CONF): the shadow calls the real `parse_url` to obtain
the slots, runs the R/I transliteration of `buildAuthority` + the verbatim
swap/defaults glue, then calls the real `urlunparse` — and diffs the whole
pipeline against the patched `prepend_scheme_if_needed`. They are thus validated
in situ rather than axiomatized; there is no axiom contract to over-claim.

**Domain note (the function's own partiality).** The real patched
`prepend_scheme_if_needed` raises `TypeError` on inputs where `auth` is truthy
but the post-swap `netloc` is `None` (e.g. `'user@'`, where `parse_url` yields
`auth='user', netloc='', path=None`, so the swap makes `netloc=None` and
`'@'.join([auth, None])` raises). G-CONF only compares on inputs where the
**real** patched function returns normally (it skips inputs on which the oracle
raises), so the shadow is held to the same domain as the gold patch. This
partiality is a property of the gold fix itself, not of the model.

### 3.2 Single change site
The gold patch.diff edits exactly one function in one file
(`requests/utils.py` `prepend_scheme_if_needed`, a single 4-line hunk). There is
no second change site and no `Solution_prepatch_<k>.lean`; the one F2P pair
(`test_prepend_scheme_if_needed[http://user:pass@…]` and `[http://user@…]`)
exercises exactly the credentials-preservation behavior `buildAuthority` models.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`6028`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `assembleAuthority`/`authorityBase` (the R/I-tagged ops) to Python
and runs the *patched* real `prepend_scheme_if_needed` as the oracle, with the
real `parse_url` / `urlunparse` callees live on both sides (no A-tagged callee to
leave un-substituted — this bundle has none).
