"""
python-invoke tasks
https://docs.pyinvoke.org/en/stable.

Collection of shell commands for ansible.
Acts as documentation of the command and
correct parameters as well as shorthand
for complex parameters.
"""

from pathlib import Path
from shutil import which

from invoke import Exit, context, task

ANSIBLE_BIN = 'ansible'
ANSIBLE_PLAYBOOK_BIN = 'ansible-playbook'
ANSIBLE_LINT_BIN = 'ansible-lint'
YAMLLINT_BIN = 'yamllint'
RUFF_BIN = 'ruff'
MOLECULE_BIN = 'molecule'
INVENTORY_DIR = 'inventories'
INVENTORY = f'{INVENTORY_DIR}/machines.yml'
# Fake, non-vaulted inventory used by the tests, so they run without
# the vault password. See doc/TESTING.adoc.
TEST_INVENTORY = f'{INVENTORY_DIR}/test/machines.yml'
TESTS_DIR = 'tests'
STATIC_TESTS = f'{TESTS_DIR}/static.yml'
ROLES_DIR = 'roles'
PLAYBOOKS_DIR = 'playbooks'
HOSTS_ALL = 'all'
LOG_DIR = 'log'
HOOKS_DIR = '.githooks'
ASK_PASS = '--ask-pass'
ASK_BECOME_PASS = '--ask-become-pass'
VERBOSE = '-vvv'
CHECK = '--check'
DIFF = '--diff'


def ctx_run(
  ctx: context,
  cmd: list[str],
) -> None:
  """
  Boiler plate function to
  flatten the command list
  and run the command.
  """
  ctx.run(' '.join(cmd))


def check_remote_user(
  cmd: list[str],
  remote_user: str,
) -> None:
  """
  If not empty, run operations as this user.
  """
  if remote_user is not None:
    cmd.append(f'--user {remote_user}')


def check_ask_pass(
  cmd: list[str],
  ask_pass: bool,
) -> None:
  """
  If requested, append flag to
  ask for password.
  """
  if ask_pass:
    cmd.append(ASK_PASS)


def check_host(
  cmd: str,
  hosts: str,
) -> None:
  """
  If not empty, append hosts to command.
  """
  if hosts and hosts != HOSTS_ALL:
    cmd.append(f"--limit '{hosts}'")


def check_ask_become_pass(
  cmd: list[str],
  ask_become_pass: bool,
) -> None:
  """
  If requested, append flag for sudo password.
  """
  if ask_become_pass:
    cmd.append(ASK_BECOME_PASS)


def check_verbose(
  cmd: list[str],
  verbose: bool,
) -> None:
  """
  If requested, append verbose
  flag.
  """
  if verbose:
    cmd.append(VERBOSE)


def check_tags(
  cmd: list[str],
  tags: str,
) -> None:
  """
  If not empty, append tags to command.
  """
  if tags:
    cmd.append(f"--tags '{tags}'")


def run_linter(
  ctx: context,
  cmd: list[str],
) -> bool:
  """
  Run a single linter and report
  whether it passed.

  A missing linter counts as a failure:
  a silently skipped check is worse than
  a noisy one.
  """
  binary = cmd[0]
  if which(binary) is None:
    print(f'{binary}: not found, rebuild the Dev Container')
    return False

  return ctx.run(' '.join(cmd), warn=True).ok


def run_linters(
  ctx: context,
  cmds: list[list[str]],
) -> None:
  """
  Run every linter before failing, so that
  one run reports everything that needs
  fixing instead of stopping at the first
  problem.
  """
  failed = {cmd[0] for cmd in cmds if not run_linter(ctx, cmd)}
  if failed:
    raise Exit(f'Linting failed: {", ".join(sorted(failed))}', code=1)


def yaml_lint_cmds() -> list[list[str]]:
  """
  Commands to lint YAML style, configured
  via `.yamllint`.
  """
  return [
    [
      YAMLLINT_BIN,
      # Warnings are errors, nothing rots
      # into background noise.
      '--strict',
      '.',
    ],
  ]


def ansible_lint_cmds(
  fix: bool,
) -> list[list[str]]:
  """
  Commands to lint playbooks and roles,
  configured via `.ansible-lint`.
  """
  cmd: list[str] = [ANSIBLE_LINT_BIN]
  if fix:
    cmd.append('--fix')

  return [cmd]


def python_lint_cmds(
  fix: bool,
) -> list[list[str]]:
  """
  Commands to lint and format-check Python,
  configured via `pyproject.toml`.
  """
  check: list[str] = [RUFF_BIN, 'check']
  fmt: list[str] = [RUFF_BIN, 'format']
  if fix:
    check.append('--fix')
  else:
    fmt.append('--check')

  return [check, fmt]


@task
def lint_yaml(
  ctx: context,
) -> None:
  """
  Lint YAML files via `yamllint`.
  """
  run_linters(ctx, yaml_lint_cmds())


@task
def lint_ansible(
  ctx: context,
  fix: bool = False,
) -> None:
  """
  Lint playbooks and roles via `ansible-lint`.
  """
  run_linters(ctx, ansible_lint_cmds(fix))


@task
def lint_python(
  ctx: context,
  fix: bool = False,
) -> None:
  """
  Lint and format-check Python via `ruff`.
  """
  run_linters(ctx, python_lint_cmds(fix))


@task
def lint(
  ctx: context,
  fix: bool = False,
) -> None:
  """
  Run all linters.

  With `--fix`, apply the fixes the linters
  can make on their own instead of only
  reporting them.
  """
  run_linters(
    ctx,
    yaml_lint_cmds() + ansible_lint_cmds(fix) + python_lint_cmds(fix),
  )


@task
def install_hooks(
  ctx: context,
) -> None:
  """
  Enable the git hooks in `.githooks`.

  Hooks live in the repo but git only runs
  them once `core.hooksPath` points at them,
  which has to be done per clone.
  """
  cmd: list[str] = [
    'git',
    'config',
    'core.hooksPath',
    HOOKS_DIR,
  ]
  ctx_run(ctx, cmd)


@task
def login(
  ctx: context,
  host: str,
  remote_user: str = None,
) -> None:
  """
  Login to remote host via `ssh`.
  """
  user = ''
  if remote_user is not None:
    user = f'{remote_user}@'

  cmd: list[str] = [
    'ssh',
    f'{user}{host}',
  ]
  ctx_run(ctx, cmd)


@task
def clean(
  ctx: context,
) -> None:
  """
  Clear temporary/intermediate data.

  Clears:
  - log/*.log
  """
  cmd: list[str] = [
    'rm',
    '-rf',
    f'{LOG_DIR}/*.log',
  ]
  ctx_run(ctx, cmd)


@task
def ping(
  ctx: context,
  hosts: str = HOSTS_ALL,
  remote_user: str = None,
  ask_pass: bool = False,
  ask_become_pass: bool = False,
) -> None:
  """
  Ping host(s) via ansible.
  """
  cmd: list[str] = [
    f'{ANSIBLE_BIN}',
    '--module-name ping',
    f'--inventory {INVENTORY}',
    hosts,
  ]
  check_remote_user(cmd, remote_user)
  check_ask_pass(cmd, ask_pass)
  check_ask_become_pass(cmd, ask_become_pass)

  ctx_run(ctx, cmd)


@task
def run_playbook(
  ctx: context,
  playbook: str,
  hosts: str = HOSTS_ALL,
  remote_user: str = None,
  ask_pass: bool = False,
  ask_become_pass: bool = False,
  verbose: bool = False,
  tags: str = None,
) -> None:
  """
  Run a playbook on machines.
  """
  cmd: list[str] = [
    ANSIBLE_PLAYBOOK_BIN,
    playbook,
    f'--inventory {INVENTORY}',
    '--become',
  ]
  check_remote_user(cmd, remote_user)
  check_ask_pass(cmd, ask_pass)
  check_ask_become_pass(cmd, ask_become_pass)
  check_host(cmd, hosts)
  check_verbose(cmd, verbose)
  check_tags(cmd, tags)

  ctx_run(ctx, cmd)


def molecule_roles() -> list[str]:
  """
  Roles that carry a molecule scenario.

  Discovered rather than listed, so adding
  `roles/<role>/molecule/` is all it takes to
  include a new role.
  """
  roles = Path(ROLES_DIR).glob('*/molecule/*/molecule.yml')

  return sorted({path.parents[2].name for path in roles})


@task
def test_static(
  ctx: context,
  verbose: bool = False,
) -> None:
  """
  Run the static tests: no host is contacted.

  Validates every role's `meta/argument_specs.yml`
  and renders every template against
  `inventories/test`. Needs no vault password, so
  it also runs in CI.
  """
  cmd: list[str] = [
    ANSIBLE_PLAYBOOK_BIN,
    STATIC_TESTS,
    f'--inventory {TEST_INVENTORY}',
  ]
  check_verbose(cmd, verbose)

  ctx_run(ctx, cmd)


@task(iterable=['role'])
def test_molecule(
  ctx: context,
  role: list[str] = None,
) -> None:
  """
  Run molecule scenarios in Docker containers.

  Without `--role`, every role that has a scenario
  is tested. Repeat `--role` to select several.
  Needs a working Docker daemon.
  """
  available = molecule_roles()
  if not available:
    raise Exit('No molecule scenarios found', code=1)

  selected = list(role) if role else available
  unknown = sorted(set(selected) - set(available))
  if unknown:
    raise Exit(
      f'No molecule scenario for: {", ".join(unknown)}. '
      f'Available: {", ".join(available)}',
      code=1,
    )

  failed: list[str] = []
  for name in selected:
    print(f'molecule: {name}')
    result = ctx.run(
      f'cd {ROLES_DIR}/{name} && {MOLECULE_BIN} test',
      warn=True,
    )
    if not result.ok:
      failed.append(name)

  if failed:
    raise Exit(f'Molecule failed for: {", ".join(failed)}', code=1)


@task
def test(
  ctx: context,
) -> None:
  """
  Run every automated test.

  Static tests first, since they are quick and
  need no container, then the molecule scenarios.
  """
  test_static(ctx)
  test_molecule(ctx)


@task
def check_drift(
  ctx: context,
  hosts: str = HOSTS_ALL,
  playbook: str = None,
) -> None:
  """
  Report drift on the real hosts, changing nothing.

  Runs the playbooks in `--check --diff` mode, so
  anything reported is a difference between the
  repository and the host - usually a manual change
  that was never written back.

  This needs the vault password and so cannot run
  in CI. Run it locally, e.g. weekly.

  Check mode is not perfect: tasks whose result
  depends on an earlier task having actually run
  are reported as changed or fail outright. Read
  the output, do not just look at the exit code.
  """
  playbooks = (
    [playbook]
    if playbook
    else sorted(str(path) for path in Path(PLAYBOOKS_DIR).glob('*.yml'))
  )

  drifted: list[str] = []
  for book in playbooks:
    print(f'check: {book}')
    cmd: list[str] = [
      ANSIBLE_PLAYBOOK_BIN,
      book,
      f'--inventory {INVENTORY}',
      '--become',
      CHECK,
      DIFF,
    ]
    check_host(cmd, hosts)
    if not ctx.run(' '.join(cmd), warn=True).ok:
      drifted.append(book)

  if drifted:
    raise Exit(
      'Check mode reported problems for: '
      f'{", ".join(drifted)}. See the output above; some tasks '
      'cannot run in check mode and fail for that reason alone.',
      code=1,
    )
