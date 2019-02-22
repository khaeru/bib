import os

import click
from click import ClickException

from ..util import pass_context


@click.command('read')
@click.argument('key')
@pass_context
def read_command(ctx, key):
    """Open the 'localfile'(s) associated with KEY."""

    try:
        entry = ctx.db.get_entry(key)
    except KeyError:
        raise ClickException("no entry with key '{}'.".format(key))

    try:
        for fn in entry['localfile']:
            fn = os.path.join(ctx.config['path'], fn)
            os.system('xdg-open "{}"'.format(fn))
    except KeyError:
        raise ClickException("entry '{}' has no localfile field."
                             .format(key))
