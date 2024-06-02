"""
python-invoke tasks
https://docs.pyinvoke.org/en/stable.

Collection of shell commands for ansible.
Acts as documentation of the command and
correct parameters as well as shorthand
for complex parameters.
"""

from invoke import context, task

ANSIBLE = 'ansible'
ANSIBLE_PLAYBOOK = 'ansible-playbook'
PLAYBOOK_TEST_CONNECTION = 'playbooks/test-connection.yml'
PLAYBOOK_BASE_SETUP = 'playbooks/base-setup.yml'
INVENTORY = 'inventories/dev.yml'
HOSTS_ALL = 'all'
HOST_MANAGED = 'managed'
LOG_DIR = 'log'
ASK_PASS = '--ask-pass'


def ctx_run(ctx: context, cmd: list[str]) -> None:
  """
  Boiler plate function to
  flatten the command list
  and run the command.
  """
  ctx.run(' '.join(cmd))


def check_ask_pass(cmd: list[str], ask_pass: bool) -> None:
  """
  If requested, append flag to
  ask for password.
  """
  if ask_pass:
    cmd.append(ASK_PASS)


@task
def login(ctx: context, host: str = HOST_MANAGED) -> None:
  """
  Login to remote host via `ssh`.
  """
  cmd: list[str] = [
    'ssh',
    host,
  ]
  ctx_run(ctx, cmd)


@task
def clean(ctx: context) -> None:
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
def ping(ctx: context, hosts: str = HOSTS_ALL, ask_pass: bool = False) -> None:
  """
  Ping all hosts via ansible
  If no pubkey auth is setup on the
  remote host, the optional
  flag `--ask-pass` is needed to
  switch to password based login.
  Mainly used for testing if all
  remote hosts are available.

  Note: May need an `ssh` login first
        if host key is not known, yet.
  """
  cmd: list[str] = [
    f'{ANSIBLE}',
    '--module-name ping',
    f'--inventory {INVENTORY}',
    hosts,
  ]
  check_ask_pass(cmd, ask_pass)

  ctx_run(ctx, cmd)


@task
def reboot_managed(ctx: context) -> None:
  """
  Reboot remote server via docker command.
  The container does not contain a `shutdown`
  command, need to restart via docker instead.
  """
  cmd: list[str] = [
    'docker',
    'container',
    'restart',
    'ansible_devcontainer-ansible-managed-1',
  ]

  ctx_run(ctx, cmd)


@task
def playbook_test_connection(
  ctx: context, hosts: str = HOSTS_ALL, ask_pass: bool = False
) -> None:
  """
  Run connection test playbook.
  """
  cmd: list[str] = [
    ANSIBLE_PLAYBOOK,
    f'--inventory {INVENTORY}',
    PLAYBOOK_TEST_CONNECTION,
  ]
  check_ask_pass(cmd, ask_pass)

  ctx_run(ctx, cmd)


@task
def playbook_base_setup(
  ctx: context, hosts: str = HOSTS_ALL, ask_pass: bool = False
) -> None:
  """
  Playbook for base server setup.
  """
  cmd: list[str] = [
    ANSIBLE_PLAYBOOK,
    f'--inventory {INVENTORY}',
    PLAYBOOK_BASE_SETUP,
    '--become',
    '--ask-become-pass',
  ]
  check_ask_pass(cmd, ask_pass)

  ctx_run(ctx, cmd)
