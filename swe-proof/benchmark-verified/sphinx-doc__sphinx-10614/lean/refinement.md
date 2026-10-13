# refinement.md — sphinx-doc__sphinx-10614

Maps every operation in `implementation_buildUrls` to its `patch.diff` /
real-source counterpart in the `urls`-building loop of
`html_visit_inheritance_diagram` (`sphinx/ext/inheritance_diagram.py:411-423`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Source (post-patch loop)
```python
urls = {}                                                # (1)
for child in pending_xrefs:                              # (2)
    if child.get('refuri') is not None:                 # (3)
        if not child.get('internal', True):             # (4)
            refname = child['refuri'].rsplit('#', 1)[-1] # (5)
        else:
            refname = child['reftitle']                 # (6)
        urls[refname] = child.get('refuri')             # (7)
    elif child.get('refid') is not None:                # (8)
        if graphviz_output_format == 'SVG':             # (9)
            urls[child['reftitle']] = current_filename + '#' + child.get('refid')  # (10)
        else:
            urls[child['reftitle']] = '#' + child.get('refid')                     # (11)
```

## Implementation (`implementation_buildUrls`)
```lean
let mut urls : List (String × String) := []                                   -- (1)
for child in children do                                                      -- (2)
  match child.refuri with
  | some uri =>                                                               -- (3)
      let mut refname := child.reftitle                                       -- (6)
      if !child.internal then                                                 -- (4)
        refname := uriTail uri                                                -- (5)
      urls := urls ++ [(refname, uri)]                                        -- (7)
  | none =>
      match child.refid with
      | some rid =>                                                           -- (8)
          if isSVG then                                                       -- (9)
            urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)] -- (10)
          else
            urls := urls ++ [(child.reftitle, "#" ++ rid)]                    -- (11)
      | none => pure ()                                                       -- drop
```

## Operation correspondence
| # | impl op | patch.diff / source op | tag | note |
|---|---------|------------------------|-----|------|
| 1 | `let mut urls := []` | `urls = {}` | R | dict → insertion-ordered `List (String × String)` (mapping.md) |
| 2 | `for child in children` | `for child in pending_xrefs` | R | ordered iterable → `List Xref`, order preserved |
| 3 | `match child.refuri with \| some uri` | `if child.get('refuri') is not None` | R | `Option`-some refines `is not None` |
| 4 | `if !child.internal` | `if not child.get('internal', True)` | R | default-True folded into `internal : Bool` (mapping.md); negation identical |
| 5 | `refname := uriTail uri` | `refname = child['refuri'].rsplit('#', 1)[-1]` | I | `uriTail` == `rsplit('#',1)[-1]` (trailing component; deep string model, G-CONF-checked) |
| 6 | `let mut refname := child.reftitle` | `refname = child['reftitle']` | I | identity |
| 7 | `urls := urls ++ [(refname, uri)]` | `urls[refname] = child.get('refuri')` | R | dict-insert → list-append; URL is the URI verbatim, NO `'../'` prefix (the fix) |
| 8 | `match child.refid with \| some rid` | `elif child.get('refid') is not None` | R | `elif` precedence preserved (refuri branch checked first) |
| 9 | `if isSVG` | `if graphviz_output_format == 'SVG'` | R | `'SVG'.upper() == 'SVG'` → `Bool` |
| 10 | `urls := urls ++ [(reftitle, currentFilename ++ "#" ++ rid)]` | `urls[reftitle] = current_filename + '#' + refid` | I | string concat; NO `'../'` prefix (the fix) |
| 11 | `urls := urls ++ [(reftitle, "#" ++ rid)]` | `urls[reftitle] = '#' + refid` | I | string concat, raster format unchanged |
| — | `\| none => pure ()` | child with neither attr: no dict write | I | dropped by `filterMap` |

Every step is R or I. No A-consumed and no A-reference rows ⇒ `axioms = []`,
`deep_model_references = []`, `axiom_check.py` is a skip stub. The impl region has
genuine R/I content ⇒ `conf_skip = false`; the R/I legs are mechanically refuted
by `conformance_check.py` (G-CONF) against a faithful replica of the post-patch
loop over ≥1.2e5 fuzzed inputs (0 disagreements).

### Faithfulness of the `dict → List` refinement (op 1/7/10/11)
The real code accumulates into a `dict` (`urls[key] = url`), so on a **key
collision** the last write wins and only one entry survives, keeping the key's
first-occurrence position. The Lean model is an ordered `List (String × String)`
that keeps every appended pair. This refinement is faithful: the rendered diagram
keys each node once, and the differential check validates the refinement directly
— G-CONF's oracle is the real post-patch **dict** and the shadow is the Lean list
collapsed through `dict(...)` (Python dict semantics), with explicit
key-collision cases (same title / same refid / same `uriTail` / refuri-vs-refid
sharing a key) all agreeing. A `correct_buildUrls` over the exact list still pins
behavior maximally (no wrong impl satisfies list equality), and the patch.diff
(the real dict code) is the verifiable face the refinement maps onto.

## The fix, as seen by the spec
Two independently-observable behavior changes, both folded into the single
`problem_spec_buildUrls` postcondition (one observable behavior — the link map):
1. **SVG link no longer prefixed with `'../'`.** Pre-patch (operations 7 & 10 in
   the SVG arm) wrote `'../' + refuri` and `'../' + current_filename + '#' + refid`.
   The diagram image is embedded via an `<object>` tag and its links are resolved
   relative to the image file, so the extra `'../'` produced 404s for diagrams in
   non-root documents. The spec pins the SVG URL to the un-prefixed value.
2. **External (intersphinx) references keyed by the URI tail.** The new `internal`
   test (operations 4-6) keys an external reference by `refuri.rsplit('#',1)[-1]`
   rather than its title, so the absolute intersphinx URL is matched to the right
   diagram node. The spec pins the key per the `internal` flag.

`patch.diff` == gold verbatim.
