# refinement.md — django__django-16139

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildRelativeLink` `do` block and the deep `relativeLink` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (axiomatized callee — not
used here), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The relative-link site — `UserChangeForm.__init__` (`forms.py:166`)

Gold hunk:
```
-            password.help_text = password.help_text.format("../password/")
+            password.help_text = password.help_text.format(
+                f"../../{self.instance.pk}/password/"
+            )
```

| # | Solution.lean impl op (`buildRelativeLink`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `key : Nat` | `self.instance.pk` (the bound record's primary key) | R | `int` (non-negative `AutoField` pk) ↔ `Nat` (mapping.md §2). G-CONF fuzzes pk magnitudes. |
| A2 | `"../../".toList` (leading segment) | the literal `"../../"` prefix of the f-string | I | identical concrete string literal (`List Char` ↔ `str`, mapping.md §2). |
| A3 | `(toString key).toList` (keyed middle segment) | `{self.instance.pk}` f-string interpolation, i.e. `str(self.instance.pk)` | R | decimal rendering: `toString n` (Lean `Nat`) ↔ `str(n)` (Python non-negative `int`) produce the identical glyph sequence (mapping.md §2). The change from the pre-patch fixed `"../password/"` — which had NO keyed segment — to a key-indexed URL is the behavioural fix. |
| A4 | `"/password/".toList` (trailing segment) | the literal `"/password/"` suffix of the f-string | I | identical concrete string literal. |
| A5 | `link` returned, then (in the repo) `help_text.format(link)` | `password.help_text = password.help_text.format(<arg>)` | R | substitution into the **constant** `help_text` template (UNCHANGED `'…<a href="{}">…'`, `forms.py:150-156`) is an R-identity wrapper on the single `{}` argument; the patch changes only that argument. The observable change is exactly `link` (mapping.md §2). |

Discriminating content of the change — the link ascends **two** levels and
embeds the **key** (`../../{pk}/password/`), not one level with no key
(`../password/`) — lives in `relativeLink key = "../../" ++ toString key ++
"/password/"` (model) ⇔ the gold `f"../../{self.instance.pk}/password/"` (real).
The pre-patch produced the keyless one-level `"../password/"`;
`Solution_prepatch.lean` reproduces that and **fails** `link = relativeLink key`
(G-DIFF) — at any `key` the two strings differ (e.g. `key = 22`: model
`"../../22/password/"` vs prepatch `"../password/"`).

Why this matters for the F2P test
(`test_link_to_password_reset_in_helptext_via_to_field`): the test reaches the
UserChange page via a `to_field` URL (`.../user/<username>/change/`) and then
`urljoin`s the help-text link against it, asserting the result equals the pk-based
password-change URL. With the keyless `"../password/"` the join lands on
`.../user/<username>/password/` (404 — the bug). With `"../../{pk}/password/"`
the two `..` segments climb past the `<id>/change/` pair and the `{pk}` re-descends
to the canonical pk-addressed `.../user/<pk>/password/` — independent of the
identifier the change page was addressed by. The spec pins exactly this string.

## A2. Termination semantics: TOTAL correctness

The bundle verifies under `loom.semantics.termination "total"`
(`TotalCorrectness`). The modeled real code — a straight-line f-string
construction in `UserChangeForm.__init__` — always terminates, so partial
correctness would be an unfaithful weakening: it would admit a diverging
"impl" (e.g. an infinite loop before returning a wrong string) that vacuously
satisfies the postcondition. Total semantics closes that loophole: any loop in
the impl region must carry `decreasing` annotations and actually terminate,
and the returned link must still equal `relativeLink key`. The
`set_option`/`open` lines are part of the frozen spec view (outside the impl
region), so a same-spec attack cannot flip them back to partial.

## B. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
construction of the format argument — is modeled **deeply** (the spelled-out
`relativeLink`, steps A1–A4), not hidden behind an axiom. There are **no
consumed axioms and no A-reference deep models of a callee**: `str(pk)` is the
total decimal-rendering function `toString` (R), and `str.format` is an
R-identity wrapper into a constant template (A5). Hence no `axiom_check.py`;
G-AX is skipped.

## C. verify(Solution) ⇒ resolved

`buildRelativeLink` verifies only if its output equals the exact two-levels-up,
key-indexed URL `relativeLink key` (A1–A4). By R (`int ↔ Nat`, `str ↔ List Char`,
`str(pk) ↔ toString key`, `str.format` into the unchanged template = identity on
the argument, A5) the verified link equals the gold post-patch
`f"../../{self.instance.pk}/password/"` substituted into `help_text`. By G-CONF
the R/I transliteration of `relativeLink` agrees with `patch.diff`'s behaviour on
≥10⁵ fuzzed pk values. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is the type bijection (mapping.md §2); there
are no axioms.
