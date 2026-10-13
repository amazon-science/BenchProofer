import Mathlib
-- imports-end

/-!
Assembling the final text of an included code example from a source file.

A reader pulls a block of lines out of a source file and may then transform it
according to several options. Two of those options let the author add extra
content: a `prepend` line placed before the block and an `append` line placed
after it. A separate `dedent` option removes a uniform amount of leading
whitespace so the example lines up nicely in the surrounding document.

The desired behaviour is that the de-indentation applies ONLY to the content
selected from the source file — never to the author-supplied `prepend` or
`append` lines. Concretely the block is assembled in this order:

* first the relevant lines are selected from the file;
* then the de-indentation (when requested) is applied to that selected content;
* then the `prepend` line, if any, is placed at the front;
* then the `append` line, if any, is placed at the end.

So the leading whitespace of a `prepend`/`append` line is preserved verbatim:
the de-indentation must not touch it. Each line carries its own trailing
newline. A `prepend`/`append` value that is present but EMPTY adds nothing:
the reader only inserts a line when the option's value is a non-empty string.
-/

-- axioms-start
-- The leading content-selection pass (choosing which lines of the source file
-- to include) and the de-indentation routine are UNCHANGED library operations.
-- They are modeled as opaque callees so they appear identically in both the
-- specification and the implementation; the behaviour of interest is the ORDER
-- in which the de-indentation runs relative to the author-supplied lines, not
-- the internals of either callee. No property of either callee is consumed by
-- the proof, so no `axiom … _prop` is declared.

/-- The content-selection pass: given the file's lines, yields the chosen block.
Identical in spec and impl; runs first in both. -/
opaque selectContent : List String → List String

/-- The de-indentation routine: removes a uniform amount of leading whitespace
from each given line. Identical in spec and impl. -/
opaque dedentCore : List String → List String
-- axioms-end

-- pure-start
/-- The options that drive the assembly tail: whether de-indentation is
requested, and the optional lines to place before / after the selected content.
Each optional line is given without its trailing newline. -/
structure IncludeOptions where
  dedent : Bool
  prepend : Option String
  append : Option String

/-- Apply de-indentation to `lines` when requested, otherwise leave them alone. -/
def applyDedent (opts : IncludeOptions) (lines : List String) : List String :=
  if opts.dedent then dedentCore lines else lines

/-- Place the `prepend` line (with its trailing newline) at the front, if any.
The reader inserts only when the value is a NON-EMPTY string (a truthiness
test in the original): a present-but-empty `prepend` adds nothing. -/
def addPrepend (opts : IncludeOptions) (lines : List String) : List String :=
  match opts.prepend with
  | some p => if p = "" then lines else (p ++ "\n") :: lines
  | none   => lines

/-- Place the `append` line (with its trailing newline) at the end, if any.
The reader inserts only when the value is a NON-EMPTY string (a truthiness
test in the original): a present-but-empty `append` adds nothing. -/
def addAppend (opts : IncludeOptions) (lines : List String) : List String :=
  match opts.append with
  | some a => if a = "" then lines else lines ++ [a ++ "\n"]
  | none   => lines
-- pure-end

-- post-conditions-start
/-- The assembled block: select the content from the file, de-indent that
selected content (when requested), then add the `prepend` and `append` lines.
De-indentation sees only the selected file content; the added lines are placed
afterwards and so keep their leading whitespace.

Note for reviewers: this post-condition is an exact equality to a TOTAL
function of the inputs, so the spec is DETERMINISTIC — for each input there is
exactly one satisfying `result`. Any same-spec implementation whose
`correct_assembleLines` closes (no sorry, clean axioms) is therefore
extensionally identical to the gold behavior; in particular `addPrepend` and
`addAppend` act on opposite ends of the list and commute, so a variant that
restructures or reorders THOSE two steps computes the same function. A
verifying same-spec variant is a positive control, not evidence of spec
weakness. -/
def problem_spec_assembleLines
    (opts : IncludeOptions) (lines : List String) (result : List String) : Prop :=
  result = addAppend opts (addPrepend opts (applyDedent opts (selectContent lines)))
-- post-conditions-end

-- impl-start
def implementation_assembleLines
    (opts : IncludeOptions) (lines : List String) : List String := Id.run do
  -- Pre-patch bug: the de-indentation pass runs LAST, after the prepend/append
  -- lines have already been added — so it strips leading whitespace from the
  -- author-supplied lines too, instead of acting only on the selected content.
  let filters : List (List String → List String) :=
    [selectContent, addPrepend opts, addAppend opts, applyDedent opts]
  let mut acc := lines
  for f in filters do
    acc := f acc
  return acc
-- impl-end

-- proof-start
theorem correct_assembleLines :
    ∀ (opts : IncludeOptions) (lines : List String),
      problem_spec_assembleLines opts lines
        (implementation_assembleLines opts lines) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
