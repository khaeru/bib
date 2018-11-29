from pathlib import Path
from sys import stdout

import click

from ..util import pass_context, to_string


@click.command()
@click.argument('TARGET', type=click.Path())
@click.argument('KEYS', nargs=-1)
@click.option('--keys-file', type=click.File('r'), metavar='KEYFILE',
              help='Also read keys from file, one per line.')
@click.option('--force/-f', is_flag=True,
              help='Overwrite TARGET if it exists.')
@click.option('--strict', is_flag=True,
              help='Require all KEYS to be found.')
@pass_context
def export(ctx, target, keys, keys_file, force, strict):
    """Export entries with given KEYS to TARGET.

    KEYS may be zero or more (space-separated) BibTeX entry IDs.
    When TARGET is '-', write to standard output.
    """
    # Use keys from the command line, and from a keys file
    keys = set(keys)
    if keys_file:
        keys |= set(key.strip() for key in keys_file.readlines())

    entries = []

    for key in ctx.db.iter_entry_keys():
        if key not in keys:
            continue

        entry = ctx.db.get_entry(key)
        entries.append(entry)
        keys.remove(entry['ID'])

        crossref = entry.get('crossref', None)
        if crossref:
            entries.append(ctx.db.get_entry(crossref))

    if strict and len(keys):
        raise click.ClickException('did not find keys %r' % keys)

    if Path(target).exists() and not force:
        raise FileExistsError

    with (stdout if target == '-' else open(target, 'w')) as f:
        f.write(to_string(entries))
