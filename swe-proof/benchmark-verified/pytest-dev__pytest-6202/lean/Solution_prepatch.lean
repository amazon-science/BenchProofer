import Mathlib
-- imports-end

/-!
Computing a test item's module-relative dotted path.

When a collected test item is described in a report, it is identified by a
dotted path relative to its containing module. That path is assembled from the
sequence of enclosing scope names (class names, the function name, parametrize
id, …), already gathered in inner-to-outer order. The desired behaviour is:

* the names are placed in outer-to-inner order (the reverse of how they were
  gathered) and joined into a single string with `.` as the separator;
* the resulting path is exactly that join — every supplied name appears
  verbatim, in order, with a single `.` between consecutive names and nothing
  added, removed, or rewritten.

In particular the path must preserve each name's characters literally: a name
that itself contains punctuation (brackets, dots) is carried through unchanged.
-/

-- axioms-start
-- No unchanged callee is consumed: the path is built entirely from a standard
-- string join over the supplied names, so no `opaque`/`axiom` decl is needed.
-- axioms-end

-- pure-start
-- (no functional helpers needed)
-- pure-end

-- post-conditions-start
/-- `parts` are the enclosing scope names in the order they were gathered
(inner-to-outer). The module-relative path is those names taken in reverse
(outer-to-inner) order and joined with `.`; nothing else is added or altered. -/
def problem_spec_getmodpath (parts : List String) (result : String) : Prop :=
  result = String.intercalate "." parts.reverse
-- post-conditions-end

-- impl-start
def implementation_getmodpath (parts : List String) : String := Id.run do
  let mut parts := parts
  parts := parts.reverse
  -- Pre-patch bug: after joining, a leftover post-processing step rewrites every
  -- occurrence of ".[" into "[", corrupting any name that legitimately contains
  -- "[" preceded by a "." boundary.
  let s := String.intercalate "." parts
  return s.replace ".[" "["
-- impl-end

-- proof-start
theorem correct_getmodpath :
    ∀ (parts : List String),
      problem_spec_getmodpath parts (implementation_getmodpath parts) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
