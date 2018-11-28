from pathlib import Path

import click

from ..util import pass_context, to_string


@click.command()
@click.argument('TARGET', type=click.Path())
@click.argument('KEYS', nargs=-1)
@click.option('--keys-file', type=click.File('r'))
@click.option('--force/-f', is_flag=True)
@pass_context
def export(ctx, target, keys, keys_file, force):
    """Export entries in KEYS to TARGET."""
    keys = set(keys)
    if keys_file:
        keys |= set(key.strip() for key in keys_file.readlines())

    entries = []

    again = True
    while again:
        again = False
        for entry in ctx.db.entries:
            if entry['ID'] not in keys:
                continue

            entries.append(entry)
            keys.remove(entry['ID'])

            crossref = entry.get('crossref', None)
            if crossref:
                keys.add(crossref)
                again = True

    if Path(target).exists() and not force:
        raise FileExistsError

    with open(target, 'w') as f:
        f.write(to_string(entries))
