# refinement.md — django__django-12304

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `publishChoicesClass` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here empty) A legs and this narrative are audited by **G-EQ**.
`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The publish site — the tail of `ChoicesMeta.__new__` (`enums.py:29–34`)

Gold hunk:
```
  cls.label = property(lambda self: cls._value2label_map_.get(self.value))
+ cls.do_not_call_in_templates = True
  return enum.unique(cls)
```

| # | Solution.lean impl op (`publishChoicesClass`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `built : ChoicesClass` | the class object `cls` as it exists after `cls._value2label_map_ = …` and `cls.label = property(…)` (`enums.py:29–33`) | R | the class object ↔ the `ChoicesClass` record of its touched/observed fields (mapping.md §2). |
| A2 | `{ built with doNotCallInTemplates := true }` — set the one boolean field | `cls.do_not_call_in_templates = True` (`enums.py:34`, the added line) | I | identical concrete op: assign the boolean class flag to true. The bijection `getattr(cls,'do_not_call_in_templates',False) ↔ doNotCallInTemplates` (mapping.md §2) is the R wrapper around it. G-CONF transliterates A2 and diffs it against the real assignment. |
| A3 | the record update leaves `valueToLabel` untouched (`out.valueToLabel = built.valueToLabel`) | the assignment touches only `do_not_call_in_templates`; `cls._value2label_map_` (`enums.py:29`) is unaffected | I + R | the frame: the new line does not disturb the previously-built value→label map. `{ x with f := v }` changes exactly `f`; everything else is copied. This pins directive 5/8 — the F2P `.label`/`.value` read still works. |
| A4 | `out` returned (`ChoicesClass`) | `return enum.unique(cls)` | R | `enum.unique(cls)` checks for duplicate values and returns `cls` itself — identity on the attributes modeled here (it sets no attribute and raises only on duplicate enum values, which the F2P fixtures do not have). The returned class object ↔ `out`. |

Discriminating content of the change — the published class must carry
`do_not_call_in_templates = True` — lives in the postcondition
`out.doNotCallInTemplates = true` (model) ⇔ the `cls.do_not_call_in_templates =
True` assignment (real). The pre-patch code omits this line, so the class keeps
the default for an arbitrary callable (no such attribute ⇒
`getattr(..., False)` is falsey ⇒ the template engine auto-calls the class);
`Solution_prepatch.lean` reproduces that (`return built`, flag stays `false`) and
**fails** `out.doNotCallInTemplates = true` (G-DIFF — confirmed: the unsolved
goal is exactly `⊢ built.doNotCallInTemplates = true`).

## B. No axioms; no A-reference

No outside callee is consumed or deeply modeled. The only callee in the modeled
tail, `enum.unique(cls)`, is identity on the attributes under observation (A4, an
R-refinement), not a contract the proof leans on. The bundle declares **no
`axiom`** and **no A-reference**, so `axiom_check.py` is **absent** and G-AX is a
**skip** (cf. django__django-10914, the thin-constant precedent).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — adding the flag
assignment — is the concrete, directly-expressible record update A2; there is no
operation Velvet cannot express, hence nothing hidden behind an axiom about the
function under change.

## D. verify(Solution) ⇒ resolved

`publishChoicesClass` verifies only if its output sets `doNotCallInTemplates =
true` (A2) AND preserves the value→label map (A3). By R (the class-object ↔
record bijection, the `getattr(...,False)` flag reading, `enum.unique` identity)
the verified step equals the patched tail of `__new__` on the published class:
the flag is set and the rest of the construction is intact. By G-CONF the I/R
transliteration of the `do` block agrees with `patch.diff`'s observable effect
on ≥10⁵ inputs. The unchanged downstream `Variable._resolve_lookup` then reads
the flag and skips auto-calling the class (mapping.md §2), so
`{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}` renders `Diamond|1` instead
of failing — the F2P `test_templates`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement, and the gold
patch resolves (G-RESOLVE). There are no axiom trust points; the only trust
point is refinement fidelity (this doc, G-EQ + G-CONF).
