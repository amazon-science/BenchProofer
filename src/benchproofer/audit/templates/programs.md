## What changed in `conformance.py` and `axioms.py` since the last round

A repair since the last round changed the bundle's programs, as below: each as the last
round judged it, against the file now. A repair may change them -- to correct a conversion
or a comparison, or to keep them in step with a specification it changed -- and the gates
run them again, but no gate checks that a program still compares as much as the
specification needs. Check each change for that. A change that makes a program compare less
-- fewer inputs or narrower ones drawn, a result compared less strictly, a disagreement no
longer reported, a function, an input or a callee newly skipped -- where the specification
states more is a finding: quote the lines.

```diff
$diff
```
