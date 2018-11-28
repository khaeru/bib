#!/usr/bin/env python3
"""\b
BibTeX database utilities
© 2016–2018 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
Licensed under the GNU GPL v3.

Reads a file .bibpy.yaml in the current directory or in PATH that may contain
general or command-specific keys. The only general configuration key is:

database: same as the --database option.

The following commands have command-specific keys. For these, use a top-level
key with the command name, and then place command-specific keys underneath. Use
'bib COMMAND --help' to see documentation about these keys.

\b
- check_files
- import
- queue
"""
# TODO speed up loading/defer reading of the database until it's needed/read in
#      a separate thread

import click

# TODO do this dynamically
from .command.check_files import check_files
from .command.curl import curl
from .command.diff import diff
from .command.import_ import import_command
from .command.list import list_command
from .command.note_template import note_template
from .command.queue import queue
from .command.read import read_command
from .util import pass_context


@click.group(help=__doc__)
@click.option('--database', type=click.Path('r'),
              help='Filename for the BibTeX database.')
@click.option('--verbose', is_flag=True, help='More detailed output.')
@click.option('--path', 'path', type=click.Path('r'),
              envvar='BIBPY_PATH', default='.',
              help='Path to the folder containing the database.')
@pass_context
def cli(ctx, database, verbose, path):
    # Initialize the context (load the database)
    ctx.init(database, verbose, path)


cli.add_command(check_files)
cli.add_command(curl)
cli.add_command(diff)
cli.add_command(import_command)
cli.add_command(list_command)
cli.add_command(note_template)
cli.add_command(queue)
cli.add_command(read_command)
