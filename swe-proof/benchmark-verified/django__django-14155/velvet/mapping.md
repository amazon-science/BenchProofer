# mapping.md — django__django-14155

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2f13c476abe4ba787b6cb71131818341911f43cc`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance (there are none consumed — see §3).

Repo file under change: `django/urls/resolvers.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolverMatchRepr (m : MatchView)` | `ResolverMatch.__repr__(self)` — `django/urls/resolvers.py:61` (class at :32) | the modeled changed function: render a resolved-URL match to its single text line |
| `matchRepr (m : MatchView)` | the body of `ResolverMatch.__repr__` (`resolvers.py:62-64`, post-patch the `if isinstance(...partial)` choice + the `%`-format line) | pure spec: the text line a match renders to |
| `MatchView` | the `ResolverMatch` instance `self` (the touched fields only — see §2) | pure spec: the observable slice of a match |
| `MatchView.isPartialFunc` | `isinstance(self.func, functools.partial)` (`resolvers.py:62` post-patch) | flag: the matched callable carries pre-bound arguments |
| `MatchView.funcPartialText` | `repr(self.func)` (`resolvers.py:63` post-patch) | the full textual form of the callable when it is a partial-application callable |
| `MatchView.funcPath` | `self._func_path` (set in `__init__`, `resolvers.py:50/53`) | the dotted import path of an ordinary callable |
| `MatchView.argsText` | `repr(self.args)` (the `%r` of `self.args`, `resolvers.py` post-patch) | the already-rendered positional-argument tuple |
| `MatchView.kwargsText` | `repr(self.kwargs)` | the already-rendered keyword-argument mapping |
| `MatchView.urlName` | `self.url_name` (`resolvers.py:36`; `None` by default) | the optional symbolic name of the match |
| `MatchView.appNamesText` | `repr(self.app_names)` | the already-rendered application-namespace list |
| `MatchView.namespacesText` | `repr(self.namespaces)` | the already-rendered instance-namespace list |
| `MatchView.route` | `self.route` (`resolvers.py:37`; `None` by default) | the optional route pattern string of the match |

The pre-patch text the change edits (refinement audit only, not in the consumer
spec view): the single `return "...%s..." % (self._func_path, ...)` statement at
`resolvers.py:62-64`, which (a) used `self._func_path` unconditionally for the
callable and (b) used `%s` (str) — not `%r` (repr) — for every component.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement (the falsifiability the plan §4 trust statement relies on).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `ResolverMatch` instance `self` | `MatchView` structure | a match ↔ the record of its observable fields (the nine fields `__repr__` reads, below). Only these fields are observed. |
| `isinstance(self.func, functools.partial)` | `isPartialFunc : Bool` | identity test result; `True` ↔ `isPartialFunc = true`. |
| `repr(self.func)` | `funcPartialText : String` | the callable's full textual form; carried **verbatim** — `__repr__` does not vary it, it inserts the result of an unchanged rendering operation. |
| `self._func_path` | `funcPath : String` | the dotted path string; carried verbatim (computed in `__init__`, unchanged by the patch). |
| `repr(self.args)`, `repr(self.kwargs)`, `repr(self.app_names)`, `repr(self.namespaces)` | `argsText` / `kwargsText` / `appNamesText` / `namespacesText : String` | the already-rendered text of each container; carried verbatim. **Key subtlety (§2a):** for these container types `str(x) == repr(x)`, so the `%s`→`%r` change is observationally inert on them — the only fields where `%r` differs from `%s` are the two string-valued ones (`url_name`, `route`), modeled explicitly via `quoted`. |
| `self.url_name` (`str` or `None`) | `urlName : Option String` | `None` ↔ `none`; a `str` ↔ `some s`. |
| `self.route` (`str` or `None`) | `route : Option String` | `None` ↔ `none`; a `str` ↔ `some s`. |
| `"...%r..." % s` for a `str` `s` | `quoted s` (delimiter choice + per-char `escChar` escaping incl. control-code escapes) | Python `repr(str)` over the ASCII plane: wrap in single quotes, escaping each inner backslash (`\` → `\\`) and single quote (`'` → `\'`); EXCEPT that a string containing a single quote but no double quote wraps in double quotes instead (then only the backslash needs escaping); tab/LF/CR render as their two-letter escape codes (`\t`/`\n`/`\r`), and every other control character plus DEL (codepoints < 32 or = 127) renders as a two-lowercase-hex-digit `\xNN` escape. `quoted` models exactly this rule: `delim := if s.contains '\'' && !(s.contains '"') then '"' else '\''`, each character mapped through `escChar delim` (backslash → doubled; the delimiter → backslash-prefixed; tab/LF/CR → two-letter code; other control/DEL → `\x` + `hexDigit` pair; all else verbatim), wrapped in `delim`. Faithful on ALL ASCII strings (validated exhaustively on every 1- and 2-char ASCII string plus 600k+ differential fuzz cases including quotes, backslashes and control characters); the `require asciiOpt` preconditions scope the claim to that plane (outside ASCII, CPython's printable/non-printable classification is Unicode-table-driven and is not claimed; every graded input is ASCII). URL names and regex routes (which DO contain backslashes, e.g. `\d{4}`) fall inside this domain, and G-CONF fuzzes it. `"...%r..." % None` ↔ `quotedOpt none = "None"` (Python `repr(None) == 'None'`). |
| `"...%s..." / "...%r..." % (...)` string interpolation | `++` concatenation of the literal fragments and the components | the format template is a fixed literal with `%s`/`%r` holes filled left-to-right; modeled as the literal fragments concatenated with the (pre-rendered or quoted) components in source order. Exact. |

### 2a. Why `%s`→`%r` is modeled only on the two string fields
The gold patch flips every conversion in the format string from `%s` to `%r`.
For the tuple `args`, the dict `kwargs`, and the lists `app_names` /
`namespaces`, Python's `str` and `repr` coincide (`str((…)) == repr((…))`,
`str({…}) == repr({…})`, `str([…]) == repr([…])`), so the flip changes nothing
observable on those components — they are carried verbatim as their (identical
under str/repr) rendered text. The flip is observable **only** on the two
string-valued fields `url_name` and `route` (and they are the two fields the
F2P `test_repr` assertion changes from `url_name=no-kwargs` /
`route=^…$` to `url_name='no-kwargs'` / `route='^…$'`). Those two are the only
ones modeled through `quoted`/`quotedOpt`; the bijection above is exact on the
F2P inputs and the fuzz corpus (G-CONF, §4).

## 3. Callees — none consumed

`ResolverMatch.__repr__` performs no call whose contract the proof consumes. Its
sub-expressions are an `isinstance` identity test, attribute reads
(`self.func`, `self._func_path`, `self.args`, …), the unchanged renderings
`repr(self.func)` / `repr(self.args)` / … (whose results are carried verbatim as
opaque text, not re-derived), and `%`-string formatting — all R/I-modeled
directly (§2). There is therefore **no module-level `axiom`** and **no `:|`
imperative-callee stub**; `meta.json` `axioms` and `deep_model_references` are
empty, and **G-AX is `skip`** (no `axiom_check.py`). The entire impl region is
R/I-tagged, so G-CONF carries the full mechanical refinement check (and
`conf_skip = false`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14155`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`matchRepr`/`resolverMatchRepr` (all R/I ops) to Python and runs the REAL
patched `ResolverMatch.__repr__` as the oracle over fuzzed `ResolverMatch`
instances (callables spanning the partial / non-partial branches; optional name
and route present and absent; empty and non-empty containers), comparing the
rendered text line for equality.
