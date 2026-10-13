#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Exercise this installation end to end and report what it can do.
#
#   bash scripts/smoke.sh              # offline: no network, no container, no API key
#   bash scripts/smoke.sh benchmarks   # ingest a sample of every registered benchmark
#   bash scripts/smoke.sh oracles      # every correctness oracle, SWE-bench included
#   bash scripts/smoke.sh all          # everything; what this machine cannot run is skipped
#   bash scripts/smoke.sh ci           # offline, and a skipped case is a failure
#
# The cases themselves live in the package, one module per group, under
# src/benchproofer/smoke/cases/. `benchproofer smoke --list` shows them, and any
# group or single case id can be run directly:
#
#   benchproofer smoke benchmarks.swebench-verified --slow
#
# This script only chooses the arguments the profiles above stand for. Extra
# arguments are appended to the command, so anything `benchproofer smoke -h`
# documents also works here:
#
#   bash scripts/smoke.sh all --jobs 8 --json
#
# Exit status: 0 all good, 1 the tool could not do its job, 3 the run did not meet
# the bar the profile asked for.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/lib/common.sh"

# Help is asked for with a dash, which is how a profile is told from an extra argument,
# so it is answered before a profile is chosen rather than by the profile case.
case "${1-}" in
  -h | --help) sed -n '5,26p' "${BASH_SOURCE[0]}" | cut -c 3-; exit 0 ;;
esac

profile="offline"
if [ "$#" -gt 0 ] && [ "${1#-}" = "$1" ]; then
  profile="$1"
  shift
fi

case "${profile}" in
  offline) selection="offline"; extra=() ;;
  benchmarks) selection="benchmarks"; extra=(--slow) ;;
  oracles) selection="oracles"; extra=(--slow) ;;
  all) selection="all"; extra=(--slow) ;;
  ci) selection="offline"; extra=(--strict) ;;
  *)
    die "unknown profile: ${profile}
  Known profiles: offline, benchmarks, oracles, all, ci
  To run one group or case instead, name it directly:
    benchproofer smoke ${profile}"
    ;;
esac

require_python
report_dir="${SMOKE_REPORT_DIR:-${REPO_ROOT}/smoke-out/${profile}}"

info "profile ${profile}: benchproofer smoke ${selection} ${extra[*]-}"
status=0
"${PYTHON}" -m benchproofer smoke "${selection}" \
  --jobs "${JOBS:-4}" \
  --report "${report_dir}" \
  ${extra[@]+"${extra[@]}"} "$@" || status=$?

info "report: $(relative "${report_dir}")/smoke.md"
exit "${status}"
