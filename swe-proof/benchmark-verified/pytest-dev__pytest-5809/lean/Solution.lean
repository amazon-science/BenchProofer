import Mathlib
-- imports-end

/-!
Building the request-parameter mapping that is submitted to the remote paste
service when a captured terminal session is uploaded.

The upload is an HTTP form post whose body is the URL-encoding of three named
parameters:

  * `code`    — the captured session text to be pasted, taken verbatim from the
                caller-supplied contents;
  * `lexer`   — the syntax-highlighting language the service should assume for
                the pasted body. The captured terminal output is arbitrary
                console text rather than source in any particular programming
                language, so the language-neutral plain-`text` highlighter is
                requested;
  * `expiry`  — how long the paste is retained, always one week.

The mapping is fully determined by the contents: the `code` entry carries the
contents unchanged, while `lexer` and `expiry` are the constant values above.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The contents enter as plain data
-- (a `String`); the only operation performed is assembling the three named
-- parameter pairs, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the direct
-- assembly of the parameter mapping.
-- pure-end

-- post-conditions-start
/-- The submitted parameter mapping is fully pinned to the input:

  * the `code` entry is exactly the caller-supplied `contents`;
  * the `lexer` entry is the language-neutral `"text"` highlighter;
  * the `expiry` entry is `"1week"`;

and these three pairs, in this order, are the entire mapping — no parameter is
left free and no extra parameter is added. -/
def problem_spec_buildPasteParams
    (contents : String) (result : List (String × String)) : Prop :=
  result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]
-- post-conditions-end

-- impl-start
def implementation_buildPasteParams (contents : String) :
    List (String × String) := Id.run do
  let mut params : List (String × String) := []
  params := params ++ [("code", contents)]
  params := params ++ [("lexer", "text")]
  params := params ++ [("expiry", "1week")]
  return params
-- impl-end

-- proof-start
theorem correct_buildPasteParams :
    ∀ (contents : String),
      problem_spec_buildPasteParams contents
        (implementation_buildPasteParams contents) := by
  intro contents
  unfold problem_spec_buildPasteParams implementation_buildPasteParams
  rfl
-- proof-end
