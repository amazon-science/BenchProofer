# mapping.md — sphinx-doc__sphinx-11445

## Modeled function

`prepend_prolog(content: StringList, prolog: str) -> None`
— `sphinx/util/rst.py`, body at lines **78–97 @ base_commit
`71db08c05197545944949d5aa76cd340e7143627`**. The patch changes the
leading-line classifier used by this function (the `re.match` test inside its
`for line in content` loop) and the module-level regex it consults
(`docinfo_re` → `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])`).

Lean symbols (Solution.lean):
- `problem_spec_placePreamble`
- `implementation_placePreamble`
- `correct_placePreamble`
- helpers `fieldMarkerScan`, `isFieldLine`, `leadingFieldCount`,
  `placePreambleSpec` (pure region)

## What the function does (post-patch)

`prepend_prolog` mutates a `StringList` of document lines in place. When the
preamble (`prolog`) is non-empty:

1. It counts `pos` = the number of consecutive *leading* lines that the
   classifier accepts (`for line in content: if RE.match(line): pos += 1; else
   break`).
2. If `pos > 0` it inserts one blank line at `pos` (separator after the leading
   header block) and bumps `pos`.
3. It inserts each preamble line at `pos + lineno`, then one trailing blank line
   after the preamble.

The remaining lines of `content` (from the original index `pos` onward) follow
unchanged. The line-source/lineno metadata the real `StringList` tracks
(`'<generated>'`, `'<rst_prolog>'`, original `'dummy.rst'`) is bookkeeping that
does not affect the *ordering and content of the rendered lines* — the
observable the F2P/P2P tests assert via `content.xitems()`. The model captures
the line **values and their order**; the (source, lineno) triple is recomputed
deterministically from position by `StringList` and is reproduced by the
conformance oracle but is not part of the Lean value model (see §"Type
bijection").

## The fix (what the patch changes)

The classifier `RE.match(line)` decides which leading lines are "header" lines
that the preamble must be inserted *after*. Pre-patch the module used
`docinfo_re = re.compile(':\\w+:.*?')`, a loose pattern that matches any line
opening with `:word:` regardless of what follows. That wrongly accepts a line
whose first token is an interpreted-text **role** applied to a title — e.g. a
cross-reference heading written `:role:` immediately followed by back-quoted
text — so the preamble is spliced *between* that heading line and its underline,
destroying the heading. Post-patch the module uses
`FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])`, docutils' real
reStructuredText field-marker grammar, which rejects `:role:`-followed-by-text
and so leaves a leading role-heading uncounted (`pos = 0`), placing the preamble
before it.

The `lineno = 0` initialiser added in the second hunk guards the
`content.insert(pos + lineno + 1, ...)` after the preamble loop when
`prolog.splitlines()` is empty; for a non-empty preamble (the modeled and F2P
case) it has no observable effect.

## Type bijection (Lean ↔ Python)

| Python | Lean | note |
|---|---|---|
| `content : StringList` (line values) | `body : List String` | the ordered line strings |
| `prolog : str` | `preamble : List String` | `prolog.splitlines()` — the preamble already split into lines |
| `prolog == ''` (falsy) | `preamble = []` | empty preamble ⇒ no change (`splitlines('') == []`) |
| `RE.match(line)` truthiness (post-patch `field_marker`) | `isFieldLine line.toList : Bool` | leading-line classifier, modeled deeply |
| `line : str` per-character | `List Char` (`line.toList`) | total/sound char indexing |
| `pos` (count of leading accepted lines) | `leadingFieldCount body` / loop `pos` | `Nat` |
| inserted blank line `''` | `""` | literal |
| resulting `content` line order | `placePreambleSpec body preamble` | the spliced line list |

`prolog.splitlines()` maps `prolog` to the preamble line list. This is a
**quotient (many-to-one), NOT a bijection**: `"a\nb"`, `"a\nb\n"`, `"a\rb"`,
`"a\r\nb"` all collapse to `["a","b"]`. The abstraction is faithful because
`prepend_prolog` observes `prolog` ONLY through (a) its truthiness and (b)
`enumerate(prolog.splitlines())` — so modeling the preamble up to
`splitlines()`-equivalence loses no observable. In particular
`prolog.splitlines() == [] ↔ prolog == ''` (the empty-string ⇒ falsy ⇒ no-op
case is exactly `preamble = []`), and a single trailing newline is dropped (so
the with/without-newline F2P pair is identical) — both confirmed in
conformance_check.py. The blank-line insertions and the leading/trailing splice
positions are the observable line ordering the F2P `content.xitems()`
assertions pin.

**Model precondition on `body`.** Each `body` element models one already-split
logical line of `content` (a `StringList` whose entries carry no embedded line
breaks); the per-character `field_marker`/`splitlines` correspondence is stated
over that domain. This matches the Sphinx path: `content` is produced by prior
line splitting before `prepend_prolog` runs.

### field-marker grammar (the deeply-modeled classifier)

`Body.patterns['field_marker']` is the regex
`:(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)` (anchored by `re.match` at
the start of the line). `fieldMarkerScan` / `isFieldLine` is a faithful
left-to-right transliteration:

- opens with `:`, first name char not `:` and not space (`(?![: ])`);
- name characters: any non-`:`/non-`\` char, OR `\` + any char (escape), OR a
  `:` that is NOT followed by space/backtick/EOL (interior colon, the negative
  lookahead `:(?!([ `]|$))`);
- closes with a `:` not preceded by a space (`(?<! )`) and followed by one or
  more spaces or end of line (`( +|$)`).

Validated == the real compiled regex by G-CONF over the structured F2P/P2P
lines and ≥10⁵ fuzzed lines (0 mismatches; see conformance_check.py).

## Callee provenance / flag deps

**None consumed.** The changed operation IS the line classifier; SPEC_GUIDE §3
forbids axiomatizing the operation the patch changes, so it is modeled deeply as
`fieldMarkerScan`/`isFieldLine` over the line's characters. `re.match`,
`StringList.insert`, `list.take`/`drop` are language/library primitives
transliterated to `fieldMarkerScan` / `++` / `List.take`/`List.drop`, not
axiomatized callees. The `axioms` region is empty; **G-AX skips**. No flag
dependency.

## G-CONF fuzz seed

`11445` (pinned; also in conformance_check.py and meta.json).
