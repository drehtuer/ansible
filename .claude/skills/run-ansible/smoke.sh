#!/usr/bin/env bash
# Drives this repo's automated checks the way an agent should: static
# tests always (fast, no container needed), molecule only if a Docker
# daemon is actually reachable (it needs one per role container). See
# ../../../doc/TESTING.adoc for what each layer catches.
#
# Usage: smoke.sh [--role=<role> ...]
# Extra args are passed straight through to `invoke test-molecule`.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo_root"

echo "== invoke test-static =="
invoke test-static

if docker info >/dev/null 2>&1; then
  echo "== invoke test-molecule $* =="
  invoke test-molecule "$@"
else
  cat <<'EOF'
== skipping invoke test-molecule: no Docker daemon reachable ==
   `docker info` failed. Molecule needs a running dockerd (started as
   root; see the Gotchas section in SKILL.md) plus the community.docker
   collection in a path ansible-core's collection search sees.
EOF
fi
