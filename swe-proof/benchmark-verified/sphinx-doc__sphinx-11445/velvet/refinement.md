# refinement.md — sphinx-doc__sphinx-11445

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `countLeadingMetadataLines` `do` block) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses an axiom's `ensures`, **A-reference** where a
deep model is validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-AX** /
**G-EQ**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The leading-line count — `prepend_prolog` (`sphinx/util/rst.py:78`)

Gold hunk (the classifier swap, plus the unrelated defensive `lineno = 0`):
```
- docinfo_re = re.compile(':\\w+:.*?')
+ FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])
  ...
  for line in content:
-     if docinfo_re.match(line):
+     if FIELD_NAME_RE.match(line):
          pos += 1
      else:
          break
```

| # | Solution.lean impl op (`countLeadingMetadataLines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `content : List (List Char)` | `content: StringList` arg of `prepend_prolog` | R | `StringList` (list of source lines) ↔ `List (List Char)` (mapping.md §2). G-CONF bridges line ↔ `str`, char ↔ `Char.ofNat (ord ch)`. |
| A2 | `let mut i := 0` | `pos = 0` | I | identical initialisation of the leading counter. |
| A3 | loop guard `i < content.length ∧ isMetadataLine content[i]!` | `for line in content: if FIELD_NAME_RE.match(line): … else: break` | A-reference + I | the bounded forward scan that stops at the first non-matching line is the **I** transliteration of the `for … else: break`; the per-line predicate `isMetadataLine content[i]!` **deeply models** the post-patch classifier `FIELD_NAME_RE.match(line)` — the changed op, modeled deeply (mapping.md §3.1), is the **A-reference** G-AX validates. No consumed classifier axiom. |
| A4 | `i := i + 1` | `pos += 1` | I | identical increment per matched leading line. |
| A5 | `return i` ⇒ `pos = leadingMetadata content` | the value `pos` then used as the prolog insertion offset | R | the returned `Nat` is the leading count `pos`; `leadingMetadata` is the front-recursive fold of `isMetadataLine` over the prefix (mapping.md §1), pinned exactly by the postcondition. |

Discriminating content of the change — a leading cross-reference role marker
such as `:mod:` `` `foo` `` must **not** be counted — lives in
`isMetadataLine (':' :: 'm' :: …)` reducing through `metaScan`'s `` ` ``-guard to
`false` (model) ⇔ `FIELD_NAME_RE.match(':mod:`foo`')` returning `None` (real).
The pre-patch loose classifier `docinfo_re = ':\\w+:.*?'` *does* match it (its
`:\w+:` prefix needs no terminating constraint), so it over-counts;
`Solution_prepatch.lean` reproduces that loose classifier in the loop guard and
**fails** `pos = leadingMetadata content` (G-DIFF).

## B. The insertion arithmetic — outside the modeled function (I)

The remainder of `prepend_prolog` (the `if pos > 0` blank-line insertion, the
`for lineno, line in enumerate(prolog.splitlines())` prolog insertion, the
trailing `<generated>` blank, and the gold patch's defensive `lineno = 0`
initialisation for the empty-prolog edge) is **unchanged in behaviour by the
classifier swap** and depends only on `pos`. It is an **I** leg: a concrete,
type-faithful copy carrying no field-marker semantics, so it is not part of the
modeled function. The two new F2P tests differ from the buggy run **only** in the
value of `pos` (the first heading line is no longer mis-counted), which is
exactly what `countLeadingMetadataLines` pins.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the per-line classifier (`docinfo_re` → `FIELD_NAME_RE`) — is modeled **deeply**
(the spelled-out `isMetadataLine` / `metaScan` grammar, step A3, an A-reference),
not hidden behind an axiom about the function under change. There are **no
consumed axioms** (the `axioms` region is empty); the only kind-A obligation is
the A-reference deep model, validated `isMetadataLine == FIELD_NAME_RE.match` by
G-AX. The `leadingMetadata` fold and the counting loop are concrete (I), so
G-CONF mechanically refutes the R/I legs against the real patched
`prepend_prolog`.

## D. verify(Solution) ⇒ resolved

`countLeadingMetadataLines` verifies only if its output equals
`leadingMetadata content` — the count of the leading run of lines satisfying the
**strict** classifier `isMetadataLine` (A3, A5). By R (`StringList ↔
List (List Char)`, line ↔ `str`) the verified count equals the post-patch `pos`
on the tested inputs; by G-AX the deep model `isMetadataLine` equals the real
`FIELD_NAME_RE.match` (A-reference) over the grammar's full input space; by
G-CONF the R/I transliteration of the counting loop agrees with the real patched
`prepend_prolog`'s insertion offset on ≥10⁵ inputs. The downstream insertion
arithmetic (B) is an unchanged I leg driven by `pos`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep model — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: deep-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
