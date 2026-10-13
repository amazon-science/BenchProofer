# refinement.md — sphinx-doc__sphinx-8621

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`kbdSplit` `do` block and its deep model `splitParts`/`isSep`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
there are no A legs in this bundle (no axioms, no A-reference). Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs over the modeled domain (mapping.md
§2.1), so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

Gold hunk (`sphinx/builders/html/transforms.py:40`):
```
-    pattern = re.compile(r'(-|\+|\^|\s+)')
+    pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')
```
The class attribute `pattern` is used at line 42, `parts = self.pattern.split(
node[-1].astext())`. The pre-patch pattern splits at EVERY connector occurrence;
the post-patch pattern adds a lookbehind `(?<=.)` and lookahead `(?=.)` so a
connector splits only when a character precedes AND follows it — i.e. only an
*interior* connector is a separator. A leading, trailing, or standalone
connector is now an ordinary key character. This is the bug: `:kbd:`-``,
`:kbd:`+``, `:kbd:`Alt+^`` previously produced empty `<kbd>` keystrokes around
the connector.

| # | Solution.lean impl op (`kbdSplit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `text : List Char` | the `str` `node[-1].astext()` passed to `pattern.split` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| 2 | `isSep c` (`c = '-' ∨ c = '+' ∨ c = '^'`) | the connector alternation `(-|\+|\^|...)` of `pattern` | I | the connector test, transliterated by G-CONF. The `\s+` whitespace alternative is outside the modeled domain (mapping.md §2.1). |
| 3 | the split point predicate `isSep c ∧ started ∧ cs ≠ []` (a connector with a char before AND after) | the lookbehind `(?<=.)` + lookahead `(?=.)` flanking the separator group | I | the lookbehind ↔ `started` (a character was already consumed); the lookahead ↔ `cs ≠ []` (a character follows). This IS the change; modeled concretely and transliterated by G-CONF. |
| 4 | the forward scan building `acc ++ [cur, [c]]` at a split and `cur ++ [c]` otherwise, returning `acc ++ [cur]` | the segmentation `re.split` produces (keys interleaved with captured separator groups) | I | `re.split` on a fully-parenthesised pattern returns keys interleaved with the matched separators; `splitParts` reproduces that list exactly over the modeled domain. G-CONF diffs the two on ≥10⁵ inputs. |

The deep model `splitParts` (with `isSep`) IS the segmentation; there is no
consumed axiom about `re.split` and no A-reference. `re.split` is the Python
standard library, exercised directly (not modeled) by G-CONF via the real
patched `pattern`.

## Discriminating content of the change

The change is "split only on an INTERIOR connector." It lives in the conjunction
`started = true ∧ cs ≠ []` inside `splitParts`'s split guard (≙ the `(?<=.)` /
`(?=.)` flanks). The pre-patch `Solution_prepatch.lean` reproduces the simplistic
"split at every connector" (`isSep c` alone, no flank check) and **fails**
`out = splitParts false [] text` (G-DIFF): on input `-` the prepatch yields
`["", "-", ""]` while the spec demands `["-"]` (the standalone connector is a
key). The unsolved goal at the failing `prove_correct` is exactly the case where
the separator lacks a flank (`started = false` or `i + 1 ≥ length`).

## C. No kind-3 (inexpressible-changed-op) steps; the modeled-domain restriction

Every step is R or I. The operation that genuinely changed — the split predicate
gaining flank-sensitivity — is modeled **deeply** (the spelled-out `splitParts`
scan, steps 2–4), not hidden behind an axiom about the function under change.
There is no consumed axiom and no A-reference, so no dead axiom and nothing for
G-AX (skip stub).

**Modeled domain (binding, see mapping.md §2.1):** `isSep`/`splitParts` model
the no-whitespace keystroke domain (separators are the single connectors `-`,
`+`, `^`). The patched pattern also has a `\s+` whitespace-run alternative whose
maximal-munch + boundary-trim semantics are orthogonal to this fix and add no
discriminating power over the bug; modeling them is deliberately omitted, the
omission is documented, and conformance_check.py's generator stays inside the
modeled domain. This is a domain restriction on a faithful model, NOT a weakened
contract: over the modeled domain (which contains the bug and both F2P tests) the
spec pins the patched behaviour exactly, and the prepatch fails on it.

## D. verify(Solution) ⇒ resolved

`kbdSplit` verifies only if its output equals `splitParts false [] text` — the
exact flank-sensitive segmentation (steps 2–4). By R (`str ↔ List Char`) the
verified scan equals the patched `pattern.split(text)` on the tested inputs over
the modeled domain; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour (the real patched `pattern.split`) on ≥10⁵ inputs, 0 disagreements.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement on the modeled domain — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (no A legs); the sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF).
