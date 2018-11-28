import os

import click
from click import ClickException

from ..util import pass_context


@click.command('read')
@click.argument('key')
@pass_context
def read_command(ctx, key):
    """Open the 'localfile'(s) associated with KEY."""
    entry = ctx.db.entries_dict.get(key, None)

    if entry is None:
        raise ClickException("no entry with key '{}'.".format(key))
    elif 'localfile' not in entry:
        raise ClickException("entry '{}' has no localfile field."
                             .format(key))

    for fn in entry['localfile']:
        fn = os.path.join(ctx.config['path'], fn)
        os.system('xdg-open "{}"'.format(fn))
