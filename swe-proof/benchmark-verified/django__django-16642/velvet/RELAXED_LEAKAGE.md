# RELAXED_LEAKAGE — django__django-16642 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by this bundle's own recorded P2 audit
(`verdict.md`, defect D1): "**Faithful + non-leaking is therefore provably
impossible**: this is exactly the `RELAXED_LEAKAGE.md` condition." The
audit's precise fix — ship this file and record the relaxed disposition — is
what this file implements.

## The mismatch

The public `problem_statement` reads, in full substance: "Improper guessing
of Mime Type for 'br' and 'Z' file types … Below FileResponse will set the
content type as text/html, even if the last file extension is 'Z' or 'br'."
It names only the two INPUT file extensions (`br`, `Z`) and the symptom
(`text/html`). `hints_text` is only "Thanks for the report!". Token scan of
the PS: `brotli`, `x-brotli`, `x-compress`, `application/x`, `octet-stream`,
`bzip`, and even the encoding label `compress` are ALL absent.

The gold patch's entire substance is two ADDED entries in the
compression-override dict in `FileResponse.set_headers`
(`django/http/response.py`):

```
+ "br": "application/x-brotli",
+ "compress": "application/x-compress",
```

The spec view's `pure` region (`compressionMediaType`) reproduces both added
entries verbatim:

```
| some "br"       => some "application/x-brotli"
| some "compress" => some "application/x-compress"
```

Facet-by-facet public status:

- **The three pre-existing table entries (`bzip2`/`gzip`/`xz` → their
  types) — public.** They are context (unchanged) lines in `patch.diff`,
  i.e. pre-patch repo state at `base_commit`. Disclosing them reveals
  nothing about the gold edit.
- **The discriminating INPUT labels — public.** `br` and `Z` are named
  verbatim in the problem_statement; the `.Z ↔ "compress"` encoding-label
  correspondence is stdlib `mimetypes` behavior at the pinned interpreter
  (readable from `Lib/mimetypes.py`'s `encodings_map`), though the PS itself
  never says "compress".
- **The two exact OUTPUT strings `application/x-brotli` and
  `application/x-compress` — gold/test-only. THIS is the leak.** They appear
  only in the gold diff and are pinned by the hidden F2P test
  `test_compressed_response` (`.tar.br` → `application/x-brotli`,
  `.tar.Z` → `application/x-compress`). The `application/x-*` IANA-style
  convention does not fix `x-brotli` vs `x-br`/`brotli`, so a PS-only solver
  cannot derive them.

## Why the leak is unavoidable

Faithfulness forces the exact output strings into the spec:

- The hidden F2P test `test_compressed_response` asserts the response's
  Content-Type equals the exact strings `application/x-brotli` /
  `application/x-compress` for `.br` / `.Z` files. The post-gold behavior on
  real inputs IS those strings.
- Hence any spec faithful to the post-gold behavior — one that makes
  `Solution_prepatch` (the 3-key table omitting br/compress) fail, which it
  does (G-DIFF pass), and rejects a wrong-output impl such as
  `br → "application/x-brotli-WRONG"` (G-EQ atk_6, rejected) — MUST name the
  exact strings. A spec that left the two output values free would admit an
  implementation that fails the F2P test — a spec-too-weak defect.
- A spec derivable from the problem_statement alone could pin only "for
  `br`/`Z`-named files the announced type is not the wrapped payload's
  guessed type" — admitting any fresh string, e.g. `application/brotli`,
  which fails `test_compressed_response`. Faithful + non-leaking is provably
  impossible here.

Partial mitigation (why this is a MILDER leak than a plain LEAKAGE): three
of the five table entries are pre-patch public repo state; the
discriminating input labels are in the PS; and the `application/x-*` shape
is partly inferable. Only the two exact output strings are strictly
gold-derived. This is the same faithful-must-leak shape as the dispositioned
django__django-13023 instance (ValueError-membership facet): the
discriminator exists only in gold + hidden tests, and the spec cannot be
both faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit)

- G-VERIFY: Solution.lean verifies; proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (3-key table omitting br/compress) fails
  for the right reason: unsolved goal on the lone `ensures
  out = resolvedMediaType guessed encoding`, diverging precisely on the
  br/compress cases — exactly the F2P bug.
- G-EQ: SOUND / TIGHT — 7 same-spec wrong impls (prepatch bug,
  always-octet-stream, ignore-compression, guess-wins-ordering,
  wrong-generic-fallback, wrong-brotli-string, encoding-dropped) all
  rejected on the postcondition; positive control (structurally different
  correct impl) verifies. The divergence loophole (a same-spec infinite loop
  vacuously verifying under partial-correctness semantics) is closed: the
  bundle runs under `loom.semantics.termination "total"` /
  `TotalCorrectness`, where a non-terminating impl cannot discharge the
  obligation.
- G-CONF: 0 / 100017 disagreements (seed 16642) against the real
  gold-patched `FileResponse` Content-Type.
- G-PANEL-2 (faithfulness): FAITHFUL — the five-key table matches the
  patched dict key-for-key; the `x or d` ≡ `Option.getD` bijection is sound
  (`mimetypes.guess_type` never returns a falsy-but-non-None content_type).
- G-MUT: 6/6 mutants killed. G-AX: vacuous (genuinely axiom-free).
  G-RESOLVE: resolved (gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the two exact output media-type strings of the gold-added table
entries).
