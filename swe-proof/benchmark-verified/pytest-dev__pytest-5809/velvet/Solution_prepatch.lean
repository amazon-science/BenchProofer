import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The submitted parameter mapping is assembled entirely
--  from the function's own input and constant labels — a pure data construction
--  modeled in full below. Nothing is delegated to an unchanged callee, so there
--  are no consumed axioms and no deep-model references.)
-- axioms-end

-- pure-start
/- The set of parameters submitted alongside a chunk of captured console output
   when it is uploaded to a remote paste service.

   - `code`   — the uploaded payload, carried through verbatim.
   - `lexer`  — the syntax-highlighting language label the service is asked to
                apply to the payload. The payload is arbitrary captured output,
                not source code in any particular programming language, so the
                correct label is a generic plain-text label.
   - `expiry` — the retention-period label.

   Only the submitted fields are modeled; the bijection to the real parameter
   mapping is in mapping.md §2. -/
structure UploadParams where
  code : List Char
  lexer : List Char
  expiry : List Char
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the parameters for uploading captured console output to a remote
   paste service.

   The payload `contents` is submitted unchanged under `code`. The
   syntax-highlighting language label `lexer` is the generic plain-text label
   `"text"`: the payload is arbitrary text rather than source code in any
   language, so a constant plain-text label is what the service is told to use.
   The retention period `expiry` is the constant label `"1week"`.

   `contents` is read-only (not `mut`); the assembler only reads it
   (directive 5) and returns a fresh parameter mapping. -/
method buildUploadParams (contents : List Char) return (out : UploadParams)
  ensures out.code = contents
  ensures out.lexer = "text".toList
  ensures out.expiry = "1week".toList
  do
    -- impl-start
    -- Pre-image skeleton: the language label is a specific programming-language
    -- label ("python3") rather than the generic plain-text label the frozen spec
    -- requires (`out.lexer = "text".toList`), so prove_correct MUST fail.
    return { code := contents, lexer := "python3".toList, expiry := "1week".toList }
    -- impl-end

prove_correct buildUploadParams by
  loom_solve
