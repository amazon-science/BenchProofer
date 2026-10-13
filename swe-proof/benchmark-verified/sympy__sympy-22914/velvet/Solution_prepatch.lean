import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The recursive
--  rendering of each argument of a function application is unchanged upstream
--  infrastructure; here each argument arrives ALREADY rendered to its target
--  source text (`args : List (List Char)`). Likewise, the text the surrounding
--  printing machinery emits for a node whose head is NONE of the three
--  builtin-mapped heads modeled here is unchanged, pre-existing
--  infrastructure; its output arrives as the read-only input `fallback`. So
--  the only behavior modeled is the
--  per-node decision of how a function application is emitted. That decision is
--  modeled deeply below; every observable is computed from the inputs `head`,
--  `args` and `fallback`. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- Render an argument list as the comma-separated body of a call: the rendered
   argument texts joined by ", " (the standard call-argument separator). Written
   front-recursively over the list. -/
def joinComma : List (List Char) → List Char
  | []           => []
  | [a]          => a
  | a :: b :: rest => a ++ ", ".toList ++ joinComma (b :: rest)

/- Render a call expression "name(arg1, arg2, ...)": the callee name, an open
   parenthesis, the comma-joined rendered arguments, and a close parenthesis. -/
def renderCall (name : List Char) (args : List (List Char)) : List Char :=
  name ++ "(".toList ++ joinComma args ++ ")".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Emit the target-language source text for one function-application node.

   `head` is the application's head/function name (read-only, never altered:
   directive 5); `args` are its operands, each ALREADY rendered to its source
   text (the recursive rendering of operands is unchanged infrastructure and is
   supplied to this routine — modeled as `List (List Char)`); `fallback` is the
   source text the surrounding, pre-existing printing machinery emits for this
   node when its head is none of the three builtin-mapped heads modeled here
   (that machinery is unchanged infrastructure too — its output is supplied
   read-only).

   Desired behavior (the property the issue and its acceptance test demand): an
   application whose head is the symbolic minimum `Min` is emitted as a call to
   the Python builtin `min` applied to the rendered operands — `min(a, b, ...)` —
   and an application whose head is the symbolic maximum `Max` is emitted as a
   call to the builtin `max` — `max(a, b, ...)`. The absolute value `Abs` keeps
   emitting the builtin `abs`. EVERY other head is emitted exactly as the
   unchanged machinery would emit it (`fallback`) — nothing but the `Min`/`Max`
   emission may change. (Strings are modeled per code point as `List Char`;
   mapping.md §2.) -/
method printApp (head : List Char) (args : List (List Char)) (fallback : List Char) return (out : List Char)
  ensures head = "Min".toList → out = renderCall "min".toList args
  ensures head = "Max".toList → out = renderCall "max".toList args
  ensures head = "Abs".toList → out = renderCall "abs".toList args
  ensures head ≠ "Min".toList ∧ head ≠ "Max".toList ∧ head ≠ "Abs".toList →
    out = fallback
  do
    -- impl-start
    -- PRE-PATCH skeleton: the builtin-equivalent table contains only `Abs`.
    -- `Min`/`Max` have NO builtin entry, so they fall through and are emitted
    -- by the surrounding machinery (`fallback`) — never as `min(...)`/`max(...)`.
    if head = "Abs".toList then
      return renderCall "abs".toList args
    else
      return fallback
    -- impl-end

prove_correct printApp by
  loom_solve
  all_goals simp_all
