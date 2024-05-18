"""
https://docs.pyinvoke.org/en/stable/
"""

from invoke import task

ANSIBLE = 'ansible'
INVENTORY = 'inventory.ini'


@task
def ssh(c, host):
  c.run(f'ssh {host}', pty=True)


@task
def ping(c, hosts, askpass=False):
  cmd = f'{ANSIBLE} --module-name ping --inventory {INVENTORY} {hosts}'
  if askpass:
    cmd += ' --ask-pass'
  print(cmd)
  c.run(cmd)
