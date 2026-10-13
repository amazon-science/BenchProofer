# mapping.md — django__django-11099

## Instance

- Repo `django/django`, base_commit `d26b2424437dabeeca94d7900b37d2df4410da0c`.
- Changed file: `django/contrib/auth/validators.py` (both modeled symbols live here).
- The two changed symbols are the class-attribute `regex` of
  `ASCIIUsernameValidator` (`validators.py:10` @ base_commit) and of
  `UnicodeUsernameValidator` (`validators.py:20` @ base_commit). Each changes from
  `r'^[\w.@+-]+$'` to `r'^[\w.@+-]+\Z'`.

## Symbol binding (Lean ↔ Python @ base_commit)

| Lean symbol | Python counterpart | file:line @ base_commit |
|---|---|---|
| `implementation_validateAscii` / `problem_spec_validateAscii` | applying `ASCIIUsernameValidator()` to a value — i.e. `RegexValidator.__call__` with `self.regex = re.compile(r'^[\w.@+-]+$', re.ASCII)` (post-fix `\Z`); result = "does NOT raise `ValidationError`" | class `django/contrib/auth/validators.py:9-15`; `__call__` `django/core/validators.py:50-59` |
| `implementation_validateUnicode` / `problem_spec_validateUnicode` | applying `UnicodeUsernameValidator()` — same `__call__`, `self.regex = re.compile(r'^[\w.@+-]+$', 0)` (post-fix `\Z`) | class `django/contrib/auth/validators.py:18-25`; `__call__` `django/core/validators.py:50-59` |
| `isAllowedAscii : Char → Bool` | "this single character is matched by the class `[\w.@+-]` under `re.ASCII`": an English letter `[A-Za-z]`, digit `[0-9]`, underscore, or one of `.` `@` `+` `-` | the char class inside `validators.py:10` regex |
| `isAllowedUnicode : Char → Bool` | "this single character is matched by `[\w.@+-]` under flags `0`": any Unicode word character (`str.isalnum`-ish per `re` `\w`) or one of `.` `@` `+` `-` | the char class inside `validators.py:20` regex |

## Type bijection (G-CONF / G-AX use this)

- Python `str value` (the argument to the validator) ↔ Lean `username : List Char`
  — the per-code-point view of `str(value)`. Indexing is total in Lean (§2). The
  bridge in `conformance_check.py` maps a Python `str s` to `list(s)` and back.
- Validator outcome ↔ `Bool`: the validator **accepts** (`__call__` returns
  without raising `ValidationError`) ↔ `result = true`; it **rejects** (raises
  `ValidationError`) ↔ `result = false`. `RegexValidator.__call__` raises iff
  `self.regex.search(str(value))` is `None` (with `inverse_match = False`, the
  default, which both username validators keep).
- `Char` ↔ a Python single-character `str` (one code point).

## Behavioral facts pinned outside Lean (validated by G-AX / used by G-CONF)

- `re.compile(r'^[\w.@+-]+\Z', flags).search(s) is not None`
  == `len(s) >= 1 and all(c matched by [\w.@+-] for c in s)`.
  The `^` anchor + the `+` quantifier (≥1) + `\Z` (true end-of-string) together
  mean: non-empty AND every character is in the class. `\Z`, unlike `$`, does NOT
  match the position before a trailing `'\n'`, so a trailing newline must itself
  satisfy the class (it does not) ⇒ rejected. This is exactly
  `!username.isEmpty && username.all isAllowed*`.
- The per-character predicate `isAllowedAscii` / `isAllowedUnicode` is the
  UNCHANGED `[\w.@+-]` membership; left `opaque` in Lean (the proof never inspects
  it — the loop computes `all isAllowed*` regardless), bridged to the REAL class
  test in `conformance_check.py`. In particular `isAllowed* '\n' = false` and
  `isAllowed*` is `true` on letters/digits — facts the real callee satisfies and
  G-CONF exercises; the Lean proof does NOT depend on them.
- Flag dependency: ASCII validator uses `re.ASCII` (so `\w` = `[A-Za-z0-9_]`);
  Unicode validator uses flags `0` (so `\w` includes non-ASCII letters). This only
  affects which characters `isAllowed*` accepts — NOT the anchoring fix — and is
  recorded so G-CONF fuzzes each validator under its own flag.

## G-CONF fuzz seed

Pinned seed: `1109920190320` (instance number + gold `created_at` date). Fuzz
corpus mixes allowed chars, disallowed chars (space, apostrophe, non-ASCII
letters), and trailing/embedded `'\n'` to exercise the `\Z` vs `$` discriminator.
