# mapping.md — django__django-10097

## Symbol binding

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `urlUserinfoValid` / `problem_spec_urlUserinfoValid` / `implementation_urlUserinfoValid` / `correct_urlUserinfoValid` | the `user:pass authentication` alternation group of `URLValidator.regex` | `django/core/validators.py:97` (the changed regex line, inside the `regex = _lazy_re_compile(...)` block spanning 94–104) |

The gold patch changes exactly one regex sub-pattern — the optional credentials
(userinfo) group that precedes the `@` of a URL authority:

```
- r'(?:\S+(?::\S*)?@)?'          # user:pass authentication  (pre-patch)
+ r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication  (post-patch)
```

The `?` after the group makes the whole credentials portion optional; when
absent there is nothing to validate. The modeled function is the acceptance
predicate of the **inner** group (the credentials segment, i.e. the characters
that would match before the mandatory `@`, with the `@` excluded). That inner
group is what the fix rewrites; everything around it (`://`, host, port, path)
is unchanged and out of frame.

### Inner-group ↔ predicate correspondence (post-patch)

Post-patch inner pattern: `[^\s:@/]+(?::[^\s:@/]*)?`

* `[^\s:@/]` = a character that is not whitespace and not one of `:` `@` `/`.
  This is exactly `isUserinfoChar c = true`.
* `[^\s:@/]+` = the user part: one or more such characters (non-empty).
* `(?::[^\s:@/]*)?` = an optional password part: a single literal `:` followed
  by zero or more admissible characters.

A string `s` (the segment before `@`) matches the whole inner group iff:
* `s` is non-empty (the `+` on the user part), and
* `s` does not begin with `:` (the user part must consume ≥1 char first), and
* `s` contains **at most one** `:` (the only `:` allowed is the single optional
  separator; the user part and password part admit none), and
* every other character is admissible (`isUserinfoChar`).

That is `urlUserinfoValid s` verbatim. `s.count ':' ≤ 1` together with the
"not-first-char is `:`" guard captures the single-separator structure: a valid
segment is `<user>` (0 colons) or `<user>:<pass>` (exactly 1 colon, not first).

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Lean | Python |
|---|---|
| `s : List Char` | `str` — the credentials segment (code points before `@`), tested per code point. Domain: Unicode scalar values; a Python `str` can additionally hold lone surrogates (U+D800–DFFF), which `Char` cannot represent — such segments (never produced by well-formed text decoding) are outside the modeled domain, and on it the model is exact |
| `isUserinfoChar c : Bool` | membership test `c not in {whitespace} ∪ {':','@','/'}` (regex char-class `[^\s:@/]`) |
| `isUserinfoWhitespace` | Python `re` `\s` over Unicode `str` input — the full 29-code-point class |
| result `Bool` | whether Python's `re.fullmatch(r'[^\s:@/]+(?::[^\s:@/]*)?', s)` matches |

`\s` bijection note: `URLValidator` receives arbitrary Unicode text, and
Python's `re` `\s` in `str` mode matches 29 code points: the six ASCII
whitespace characters (`\t` `\n` `\v` `\f` `\r` space), the information
separators U+001C–U+001F, NEL (U+0085), NBSP (U+00A0), OGHAM SPACE MARK
(U+1680), the fixed-width spaces U+2000–U+200A, LINE SEPARATOR (U+2028),
PARAGRAPH SEPARATOR (U+2029), NARROW NBSP (U+202F), MEDIUM MATHEMATICAL SPACE
(U+205F) and IDEOGRAPHIC SPACE (U+3000). Lean's `Char.isWhitespace` covers only
four of these, so the spec enumerates the class by code point
(`isUserinfoWhitespace`). G-CONF asserts the Lean-class ↔ `re \s` equivalence
over ALL code points (0x0–0x10FFFF) against the real engine at run time, and
its edge set + fuzz alphabet include every `\s` code point plus non-`\s`
Unicode look-alikes (ZWSP, WORD JOINER, ZWNBSP, MONGOLIAN VOWEL SEPARATOR) to
exercise both sides of the boundary.

## Callee provenance / flag deps

No repo callee is consumed. The predicate is a pure function of the regex
character classes, modeled deeply. No `opaque`/`axiom`. No flag dependency (the
credentials group has no configuration toggle).

## G-CONF fuzz seed

Pinned seed: **10097** (also recorded in `meta.json.verifier_pins.conf_seed`).
