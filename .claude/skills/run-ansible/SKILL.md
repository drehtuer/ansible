---
name: run-ansible
description: Build, lint, and test this Ansible role/playbook repo. Use when asked to run its tests, run molecule, lint it, render templates, check for drift, or verify a role/playbook change actually works. Not a web/desktop app — driven via the `invoke` task runner and the `.claude/skills/run-ansible/smoke.sh` driver.
---

This repo is Ansible automation (roles + playbooks), not a running app — there's nothing to launch or screenshot. It's driven through `invoke` tasks (`tasks.py`), and the primary agent path is `.claude/skills/run-ansible/smoke.sh`, which runs the static tests and then molecule (via `sudo` — see Gotchas — if Docker is reachable). All paths below are relative to the repo root.

## Prerequisites

Nothing to install if you're inside the project's Dev Container (`.devcontainer/`) — `ansible`, `ansible-lint`, `yamllint`, `ruff`, `invoke`, `molecule` and the `docker` CLI are already on `PATH` there, and `sudo` is passwordless. Verify:

```bash
which invoke ansible ansible-playbook molecule docker
sudo -n true && echo "passwordless sudo OK"
```

Molecule additionally needs, on this container as observed in this session (may already be fixed in a freshly rebuilt one — see Gotchas): `community.docker` installed under `/usr/share/ansible/collections`, and the `python3-requests`/`python3-docker` apt packages. Check and fix in one go:

```bash
sudo ansible-galaxy collection install --requirements-file .devcontainer/ansible-galaxy.yml --collections-path /usr/share/ansible/collections --force
sudo apt-get install -y python3-requests python3-docker
```

## Run (agent path)

```bash
.claude/skills/run-ansible/smoke.sh
```

This always runs `invoke test-static` (renders every `*.j2` template and validates every `meta/argument_specs.yml` against the fake `inventories/test/` inventory — no host or container needed, takes a few seconds). Verified output ends with:

```
TASK [Report] ***
ok: [testhost] => {
    "msg": "10 argument specs validated, 25 templates rendered"
}
PLAY RECAP ***
testhost : ok=10  changed=0  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

It then checks `sudo -n docker info` (see the sudo Gotcha below for why `sudo` is needed). If that succeeds it runs `sudo -E env "PATH=$PATH" invoke test-molecule` (extra args are passed through, e.g. `--role=users` to test one role); otherwise it prints why it skipped rather than hanging. Verified in this session: all three scenarios (`apt`, `cron`, `users`) pass end to end, including the idempotence check, ending with:

```
SCENARIO RECAP
default : actions=12  successful=7  disabled=0  skipped=0  missing=6  failed=0
```

(`missing=6` is expected — these scenarios don't define `side_effect`/`verify`/a second `cleanup`, which molecule reports as "missing playbook" rather than a failure.)

Test one role directly, bypassing the driver:

```bash
sudo -E env "PATH=$PATH" invoke test-molecule --role=users
# or: cd roles/users && sudo -E env "PATH=$PATH" molecule test
```

`invoke test-molecule` without `--role` discovers every role under `roles/*/molecule/*/molecule.yml` (today: `apt`, `cron`, `users`) and runs each in turn.

## Test

```bash
invoke test-static                            # no container, no sudo needed
sudo -E env "PATH=$PATH" invoke test-molecule # needs sudo - see Gotchas
invoke lint                                   # yamllint --strict, ansible-lint (production profile), ruff
invoke lint --fix                             # same, applying what the tools can fix automatically
```

`invoke test-static`, `invoke test-molecule` (all three scenarios, via `sudo`) and the `ruff`/`yamllint` parts of `invoke lint` were run in this session and pass. `invoke lint` as a whole currently fails on the `ansible-lint` step — see Troubleshooting.

## Run (human path)

Applying a playbook against real machines or checking drift needs the vault password and SSH access to real hosts, neither of which exist in a sandbox — don't attempt these here:

```bash
invoke run-playbook --playbook=playbooks/users.yml --ask-become-pass
invoke check-drift   # --check --diff against inventories/machines.yml, local only
```

## Gotchas

- **Docker access needs `sudo`, at least in a shell that predates the group fix.** `devcontainer.json` bind-mounts the *host's* `/var/run/docker.sock` into the container rather than running a nested `dockerd` — there's no daemon inside the container to manage. Its `postStartCommand` runs `.devcontainer/fix-docker-gid.sh`, which creates a `docker-host` group matching the socket's GID and adds the user to it (`getent group docker-host` shows the user as a member). The catch: that `usermod` only takes effect in a *new* login session — a shell that was already open when the container started (this one, most likely) keeps its old group list (`id` won't show `docker-host`) and gets `permission denied while trying to connect to the docker API`. Passwordless `sudo` is deliberately configured in the Dockerfile for exactly this gap, so `sudo docker ...` / `sudo molecule test` always works regardless of session age — that's what `smoke.sh` and every command below use. If `id` shows `docker-host` in your groups, plain `docker`/`molecule` without `sudo` will also work; there's no need to detect which case you're in, `sudo` works either way.
- **`sudo -E env "PATH=$PATH" invoke ...`, not plain `sudo invoke ...`.** `sudo` resets `PATH` and drops the invoking user's environment by default, so a bare `sudo molecule test` fails with `molecule: command not found` (it's a symlink into `/opt/molecule`, not on root's default `PATH`). `-E` plus explicitly re-passing `PATH` is what actually works — confirmed in this session; `sudo which molecule` alone finds it (system dirs are on root's default `PATH` too), but a plain `sudo invoke test-molecule` still fails until `PATH` is preserved.
- **`community.docker` needs to be installed to the canonical collections path, `/usr/share/ansible/collections`** — that's the one molecule's own virtualenv actually searches (confirmed: its default search list includes that path but not `/usr/lib/python3/dist-packages/ansible_collections`, the one the `ansible` apt package populates). If it's missing there — this session's container was, apparently built from an older layer than the current `.devcontainer/ansible-galaxy.yml` — plain `ansible-galaxy collection install --requirements-file .devcontainer/ansible-galaxy.yml` reports "Nothing to do" without fixing it (it's satisfied by the apt-installed copy elsewhere on the search path and doesn't realize the *target* directory is missing it). Force it into the right place: `sudo ansible-galaxy collection install --requirements-file .devcontainer/ansible-galaxy.yml --collections-path /usr/share/ansible/collections --force`. Confirmed this resolves `Collection 'community.docker' not found` for `molecule test` with no other workaround needed.
- **`community.docker`'s Ansible modules need the `docker`/`requests` Python libraries available to *system* Python** (`/usr/bin/python3`, which `ansible-playbook` uses — not `/opt/molecule`'s venv, which is fine on its own). The Dockerfile doesn't install these today, so a container missing them fails late, on `destroy`, with `Failed to import the required Python library (requests) on dev_host's Python /usr/bin/python3` — after syntax/create/converge/idempotence already ran, which makes it look like everything worked except cleanup. Fix: `sudo apt-get install -y python3-requests python3-docker`. Confirmed this is what unblocked the full `apt`/`cron`/`users` scenarios in this session.
- **Molecule needs an init-enabled image**, not a plain `ubuntu:24.04`/`26.04` — most roles use `systemd_service`, which needs PID 1 to be systemd. Scenarios already pull `geerlingguy/docker-ubuntu2404-ansible` with `privileged: true` and `/lib/systemd/systemd` as the command; don't change that.
- **`invoke test-molecule --role=<name>` only accepts roles that actually have a scenario** (`roles/<name>/molecule/*/molecule.yml`). Passing an unknown name fails fast with the list of available roles rather than doing anything.

## Troubleshooting

- **`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`**: this shell predates the `docker-host` group fix — use `sudo` (see the sudo Gotcha above), don't try to fix group membership in-place.
- **`molecule: command not found` (or `invoke: command not found`) under `sudo`**: `PATH` got reset. Use `sudo -E env "PATH=$PATH" invoke ...` / `... molecule ...`, not bare `sudo invoke ...`.
- **`ansible_compat.errors.InvalidPrerequisiteError: Collection 'community.docker' not found in [...]`**: see the collections-path Gotcha above — `sudo ansible-galaxy collection install --requirements-file .devcontainer/ansible-galaxy.yml --collections-path /usr/share/ansible/collections --force`.
- **`Failed to import the required Python library (requests) on dev_host's Python /usr/bin/python3`**, surfacing on the `destroy` step after `converge`/`idempotence` already passed: `sudo apt-get install -y python3-requests python3-docker`.
- **`ERROR Unable to contact the Docker daemon`**: `sudo -n docker info` itself is failing, i.e. the socket genuinely isn't mounted/reachable even as root — this is a container-configuration problem (check `devcontainer.json`'s docker.sock mount), not something a workaround in this repo fixes.
- **`invoke lint` fails with 18× `var-naming[no-role-prefix]`** (e.g. `roles/http/tasks/main.yml:24` on `set_fact: php_version`, and one per role's `defaults/main.yml`), and reports `Profile 'production' was required, but 'min' profile passed`, even though `doc/STATUS.adoc` claims the whole repo passes `production`. `ansible-lint` is installed unpinned in the Dockerfile (`RUN ... ansible-lint`, no version), so this is very likely version drift between what's on `PATH` here (`ansible-lint 26.1.1`) and whatever version the repo was last actually green against, rather than a real regression to fix as part of an unrelated change. `yamllint --strict` and both `ruff` checks pass cleanly on their own.
