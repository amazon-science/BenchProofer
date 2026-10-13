# mapping.md — django__django-15098

## Modeled function

| Lean | Python | file:line @ base_commit `2c7846d992` |
|---|---|---|
| `implementation_langCodeFromPath` / `problem_spec_langCodeFromPath` / `correct_langCodeFromPath` | `get_language_from_path(path, strict=False)` — return the language code found in the URL `path`, or `None` | `django/utils/translation/trans_real.py:501-513` |

The gold patch edits the module-level matcher `language_code_prefix_re`
(`trans_real.py:46`) that this function consumes via `language_code_prefix_re.match(path)`.
The function body is unchanged; the behavioral change is entirely in the prefix
matcher it applies.

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `path : str` (URL path), per-code-point | `List Char` | the leading-segment extraction is a per-character scan; Lean `List` indexing is total/sound |
| `lang_code : str` (extracted candidate, regex group 1) | `List Char` | the candidate tag; `none` ↔ no regex match |
| return `str` (resolved code) | `some (List Char)` | a recognised, supported variant |
| return `None` | `none` | no prefix match, OR the candidate resolves to no supported variant |
| `re.match(...)` truthiness + `regex_match[1]` | `langPrefix : List Char → Option (List Char)` | deep model of `language_code_prefix_re.match(path)`; `none` ↔ no match, `some g1` ↔ matched group 1 |

### Regex deep model (the changed op)

`language_code_prefix_re` post-patch = `^/(\w+([@-]\w+){0,2})(/|$)`.
Group 1 (the captured candidate) is modeled by `langPrefix = langPrefixN 2`:

- `^/` — path must start with `/` (`'/' :: rest`).
- `\w+` — primary subtag: a non-empty maximal run of word chars
  (`isWord c = c.isAlpha || c.isDigit || c = '_'`, matching Python `\w` for ASCII;
  see flag deps). Modeled by `rest.span isWord` with the non-empty check.
- `([@-]\w+){0,2}` — up to **two** trailing subtags, each a separator
  (`[@-]`, modeled `isSep c = c = '-' || c = '@'`) immediately followed by a
  non-empty word run. Modeled by `grabSubtags 2` (greedy, stops at a non-sep or a
  sep not followed by a word char).
- `(/|$)` — the candidate must be terminated by `/` or end of string, where the
  `$` anchor (default, non-MULTILINE) also matches just before a single trailing
  newline. Modeled by the `rrest` match: `[]` (end), `'/' :: _`, or `['\n']`
  (exactly one trailing line-terminator) ⇒ `some`, otherwise `none`.

The PRE-patch matcher is `^/(\w+([@-]\w+)?)(/|$)` = `langPrefixN 1` (at most ONE
trailing subtag). The only change is `?` (0–1) → `{0,2}` (0–2): one extra
admissible trailing subtag, i.e. `language-script-region` instead of just
`language-region`/`language-script`.

Equivalence of the deep model to the real `re` engine is checked mechanically by
`conformance_check.py` over ≥10⁵ fuzzed paths (group-1 extraction, both pre and
post matchers), and was confirmed at construction time (0 mismatches / 300k).

## Callee provenance / flag deps

- `get_supported_language_variant(lang_code, strict=False)`
  (`trans_real.py:464-498`) is an **UNCHANGED** callee. `get_language_from_path`
  calls it and translates its `LookupError` into `None`. It is exposed by
  signature only as `opaque resolveVariant : List Char → Option (List Char)`,
  where the `LookupError` outcome is the `none` case. It is an **A-reference**
  in the sense that the impl invokes it identically to the real function; the
  proof needs no `_prop` axiom about it (the spec relates the result to
  `resolveVariant` of the same candidate), so **G-AX = skip**.
  `strict` is held at its default `False` (the path used by `i18n_patterns` /
  `LocaleMiddleware`); the candidate-extraction change is independent of `strict`.
- `\w` flag dep: Python 3 `re` is Unicode-aware by default, so `\w` matches
  `[A-Za-z0-9_]` AND Unicode word characters; Lean `Char.isAlpha`/`Char.isDigit`
  are ASCII-only, so `isWord` models the ASCII `\w` class. The spec therefore
  branches on `allAscii path`:
  - ALL-ASCII paths (the graded slice — every F2P input and every
    `settings.LANGUAGES` code is ASCII): the candidate extraction is deep-modeled
    exactly (`langPrefix`), validated by G-CONF.
  - Paths carrying a non-ASCII code point: the matcher's word class there is
    library/Unicode-table specific, so the whole-routine outcome is exposed by
    signature only as the opaque `nonAsciiOutcome : List Char → Option (List
    Char)` — a fixed deterministic function with NO asserted properties, used
    identically on both sides of the spec equation (like `resolveVariant`). This
    keeps the spec a TOTAL functional equation (every closing impl is
    extensionally the spec function; no free non-ASCII behavior) without
    over-claiming the Unicode `\w` class.
  (An earlier revision claimed the ASCII-only `isWord` model was sound on
  non-ASCII paths via "non-ASCII candidates never resolve"; that argument is
  WRONG — a non-ASCII path can still yield a resolvable candidate after the
  resolver's generic-variant fallback, e.g. a candidate whose trailing subtag is
  non-ASCII is truncated to its supported ASCII prefix. The `allAscii` branch
  supersedes it.) The conformance fuzz draws from BOTH a langtag-shaped ASCII
  alphabet and the full ASCII plane (code points 0–127) to cover the whole
  deep-modeled branch, including the `$`-before-trailing-newline anchor
  boundary.

## Out-of-scope edits

None — the gold patch is a single one-line change to one matcher.

## G-CONF fuzz seed

`conf_seed = 15098` (pinned; see conformance_check.py and meta.json).
