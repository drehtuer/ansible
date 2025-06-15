"""
python-invoke tasks
https://docs.pyinvoke.org/en/stable.

Collection of shell commands for ansible.
Acts as documentation of the command and
correct parameters as well as shorthand
for complex parameters.
"""

from invoke import context, task

ANSIBLE_BIN = 'ansible'
ANSIBLE_PLAYBOOK_BIN = 'ansible-playbook'
INVENTORY_DIR = 'inventories'
INVENTORY = f'{INVENTORY_DIR}/machines.yml'
HOSTS_ALL = 'all'
LOG_DIR = 'log'
ASK_PASS = '--ask-pass'
ASK_BECOME_PASS = '--ask-become-pass'
VERBOSE = '-vvv'


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
  ask_become_pass: bool = True,
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
  ask_become_pass: bool = True,
  verbose: bool = False,
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
  check_verbose(cmd, verbose)

  ctx_run(ctx, cmd)
