# RELAXED_LEAKAGE — django__django-14155 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

## The mismatch

The gold fix to `ResolverMatch.__repr__` (`django/urls/resolvers.py:61`)
makes TWO independent behavioral changes:

- **(a) `functools.partial` handling — fully public.** The
  `problem_statement` is exclusively about this: it names
  `functools.partial`, "the func argument", and asks that partials be
  unwrapped "so they are accessible in `__repr__`". The spec's
  `isPartialFunc ? funcPartialText : funcPath` choice discloses nothing
  beyond the public issue. This facet does NOT leak.
- **(b) The `%s` → `%r` conversion flip — gold/test_patch-only.** Observable
  exactly on the two string-valued fields: `url_name` and `route` now render
  as Python `repr` (quoted, with backslash/quote escaping) instead of bare
  text. Token scan of the `problem_statement` for
  quote/quoted/%r/%s/single/url_name/route = 0 hits (its three "repr"
  tokens all name the `__repr__` method itself); `hints_text` is empty. Yet
  the quoting is a MANDATORY F2P discriminator: the hidden `test_patch`
  flips `test_repr` (in FAIL_TO_PASS) to assert `url_name='no-kwargs'` and
  `route='^no_kwargs/([0-9]+)/([0-9]+)/$'` (single-quoted).

The spec view discloses facet (b) via `quoted`/`escChar`/`quotedOpt` and the
`matchRepr` clauses wiring `url_name`/`route` through `quotedOpt` — the
repr-style rendering of the two string fields is derivable only from the
gold patch / hidden test_patch, not from the public issue.

## Why the leak is unavoidable

A faithful spec must pin the gold behavior the F2P tests check.
`Solution_prepatch_2.lean` is precisely the impl a PS-only solver would
write (facet (a) fixed, `url_name`/`route` rendered unquoted): it fails
`prove_correct` against the frozen spec (G-DIFF) exactly because the spec
pins the quoting — and it would fail the hidden F2P `test_repr`. A spec
weak enough to hide facet (b) would ADMIT `Solution_prepatch_2.lean`, i.e.
admit an implementation that does not resolve the instance. Faithful +
non-leaking is therefore provably impossible here; this is the defining
shape of the relaxed-leakage exception (spec_guide.md directive 6). It is
NOT ordinary de-narration: no patched file/symbol/diff line/mechanism is
named in the spec view.

## Core soundness is intact

- G-VERIFY: `resolverMatchRepr` verifies against `ensures out = matchRepr m`
  (total concrete equality, no oracle).
- G-DIFF: both prepatch skeletons fail under the byte-identical spec, each
  on exactly one gold discriminator (partial branch; quoting).
- G-CONF: the R/I shadow (including the full `quoted` escaping/delimiter
  rule) agrees with the real patched `ResolverMatch.__repr__` on a
  100k+-input fuzz corpus whose name/route alphabets include backslashes
  and both quote characters (seed 14155).
- G-AX: skip — genuinely axiom-free (no consumed callee contract).
- G-RESOLVE: `patch.diff` is the gold patch verbatim; harness `resolved`.

Only the secondary no-leakage property is relaxed, for this one documented
facet.
