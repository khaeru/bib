from subprocess import DEVNULL, run
from sys import stdout

import click
from click import ClickException

from ..util import pass_context


@click.command('read')
@click.argument('key')
@click.option('--clock/--no-clock', default=False,
              help="Start the timewarrior clock.")
@pass_context
def read_command(ctx, key, clock):
    """Open the 'localfile'(s) associated with KEY."""

    try:
        entry = ctx.db.get_entry(key)
    except KeyError:
        raise ClickException("no entry with key '{}'.".format(key))

    try:
        for fn in entry['localfile']:
            run(['xdg-open', ctx.config['path'] / fn], stderr=DEVNULL)
    except KeyError:
        raise ClickException("entry '{}' has no localfile field."
                             .format(key))

    if clock:
        args = ['timew', 'start', 'Read', key]
        run(args, stdout=stdout)
