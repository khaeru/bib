"""Utility for BibTeX databases.

An optional configuration file `.bibpy.yaml` is read in:

\b
- the path given by `--path` command-line option,
- the current directory, or
- the directory given by the `BIBPY_PATH` environment variable.

The only general configuration key is:

    database: path/to/database.bib  # same as the --database option

The following commands have command-specific keys. For these, use a top-level
key with the command name, and then place command-specific keys underneath. Use
'bib COMMAND --help' to see documentation about these keys.

\b
- check_files
- import
- queue
"""
import click

# TODO do this dynamically
from .command.check_files import check_files
from .command.curl import curl
from .command.diff import diff
from .command.export import export
from .command.import_ import import_command
from .command.list import list_command
from .command.queue import queue
from .command.read import read_command

from .util import pass_context


@click.group(help=__doc__)
@click.option('--database', type=click.Path('r'), metavar='FILE',
              help='Filename of the BibTeX database.')
@click.option('--verbose', is_flag=True, help='Print detailed output.')
@click.option('--path', type=click.Path('r'), metavar='DIR',
              envvar='BIBPY_PATH', default='.',
              help='Directory containing the database and/or .bibpy.yaml.')
@pass_context
def cli(ctx, database, verbose, path):
    # Initialize the context (load the database)
    ctx.init(database, verbose, path)


cli.add_command(check_files)
cli.add_command(curl)
cli.add_command(diff)
cli.add_command(export)
cli.add_command(import_command)
cli.add_command(list_command)
cli.add_command(queue)
cli.add_command(read_command)
