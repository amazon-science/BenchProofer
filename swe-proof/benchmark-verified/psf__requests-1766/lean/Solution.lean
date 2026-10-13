import Mathlib
-- imports-end

/-!
Assembling the value of an HTTP **Digest** scheme `Authorization` header from its
component directives.

The header value is the literal `Digest ` followed by a comma-separated list of
directives:

  * the mandatory `username`, `realm`, `nonce`, `uri` and `response` directives,
    each carrying a quoted-string parameter;
  * then, when supplied, the optional `opaqueVal`, `algorithm` and message-digest
    directives, in that order;
  * and, when a quality-of-protection value is in effect, the
    quality-of-protection directive together with the nonce-count and
    client-nonce directives.

Per the Digest scheme, a directive whose value is a *quoted string* parameter is
emitted wrapped in double quotes; the quality-of-protection directive's value is
one such quoted-string parameter, and the nonce-count value is a bare token.

The component values themselves (the response digest, the client nonce, the
request URI, …) are produced upstream and pass through this assembly unchanged;
they are taken here as arbitrary strings, so the behavior pinned below is exactly
"the directives are assembled, ordered and quoted as the scheme requires."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Every directive value
-- handed to the assembly (the response digest, client nonce, request URI, nonce
-- count, realm, …) is computed by upstream code that this assembly does not
-- touch; each is taken as an arbitrary `String` parameter. The assembly's result
-- is therefore pinned for EVERY possible set of component values, so the spec
-- needs no `opaqueVal`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The assembled `Authorization` header value for the Digest scheme.

`opaqueVal`, `algorithm`, `entdig` (message digest) and `qop` (quality of
protection) are optional directives: an empty string denotes "not supplied", in
which case the directive is omitted. Each present directive is appended in the
canonical order. Quoted-string parameters are wrapped in double quotes; the
nonce-count (`nc`) value is a bare token. -/
def assembledDigestHeader
    (username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce : String) :
    String :=
  let base0 :=
    "username=\"" ++ username ++ "\", realm=\"" ++ realm ++ "\", nonce=\"" ++ nonce
      ++ "\", uri=\"" ++ uri ++ "\", response=\"" ++ respdig ++ "\""
  let base1 := if opaqueVal ≠ "" then base0 ++ ", opaque=\"" ++ opaqueVal ++ "\"" else base0
  let base2 := if algorithm ≠ "" then base1 ++ ", algorithm=\"" ++ algorithm ++ "\"" else base1
  let base3 := if entdig ≠ "" then base2 ++ ", digest=\"" ++ entdig ++ "\"" else base2
  let base4 :=
    if qop ≠ "" then
      base3 ++ ", qop=\"auth\", nc=" ++ ncvalue ++ ", cnonce=\"" ++ cnonce ++ "\""
    else base3
  "Digest " ++ base4
-- pure-end

-- post-conditions-start
/-- The header value is fully pinned to its component inputs: it is the assembled
directive list in canonical order, with the optional directives present exactly
when their component value is non-empty, and with every quoted-string parameter —
in particular the quality-of-protection directive's value — wrapped in double
quotes. No output component is left free. -/
def problem_spec_digestAuthHeader
    (username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce : String)
    (result : String) : Prop :=
  result =
    assembledDigestHeader username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce
-- post-conditions-end

-- impl-start
def implementation_digestAuthHeader
    (username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce : String) :
    String := Id.run do
  let mut base :=
    "username=\"" ++ username ++ "\", realm=\"" ++ realm ++ "\", nonce=\"" ++ nonce
      ++ "\", uri=\"" ++ uri ++ "\", response=\"" ++ respdig ++ "\""
  if opaqueVal ≠ "" then
    base := base ++ ", opaque=\"" ++ opaqueVal ++ "\""
  if algorithm ≠ "" then
    base := base ++ ", algorithm=\"" ++ algorithm ++ "\""
  if entdig ≠ "" then
    base := base ++ ", digest=\"" ++ entdig ++ "\""
  if qop ≠ "" then
    -- the quality-of-protection directive carries a quoted-string parameter
    base := base ++ ", qop=\"auth\", nc=" ++ ncvalue ++ ", cnonce=\"" ++ cnonce ++ "\""
  return "Digest " ++ base
-- impl-end

-- proof-start
theorem correct_digestAuthHeader :
    ∀ (username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce : String),
      problem_spec_digestAuthHeader username realm nonce uri respdig opaqueVal algorithm entdig
          qop ncvalue cnonce
        (implementation_digestAuthHeader username realm nonce uri respdig opaqueVal algorithm
          entdig qop ncvalue cnonce) := by
  intro username realm nonce uri respdig opaqueVal algorithm entdig qop ncvalue cnonce
  unfold problem_spec_digestAuthHeader implementation_digestAuthHeader assembledDigestHeader
  simp only [Id.run, bind, pure]
  split <;> split <;> split <;> split <;> rfl
-- proof-end
