from configparser import ConfigParser
from datetime import datetime, timezone
from pathlib import Path
from subprocess import DEVNULL, run
from sys import stdout

from bibtexparser.customization import author
import click
from click import ClickException
from xdg.BaseDirectory import xdg_config_home

from ..util import pass_context


note_string = """Content-Type: text/x-zim-wiki
Wiki-Format: zim 0.4
Creation-Date: {date}

====== {author} {year} ======
//{title}//
Created {date_text}

"""


def note_template(entry):
    """Return a Zim note template for *entry*."""
    entry = author(entry)

    def surname(index):
        return entry['author'][index].split(',')[0]

    now = datetime.now(timezone.utc).astimezone().replace(microsecond=0)

    values = {
        'date': now.isoformat(),
        'date_text': now.strftime('%A %d %B %Y'),
        'year': entry['year'],
        'title': entry['title'],
        }

    if len(entry['author']) > 2:
        values['author'] = surname(0) + ' et al.'
    elif len(entry['author']) == 2:
        values['author'] = '{} & {}'.format(surname(0), surname(1))
    else:
        values['author'] = surname(0)

    return note_string.format(**values)


@click.command('read')
@click.argument('key')
@click.option('--clock/--no-clock', '-c', default=False,
              help="Start the timewarrior clock.")
@click.option('--note/--no-note', '-n', default=False,
              help="Open Zim to a notes page for the entry.")
@pass_context
def read_command(ctx, key, clock, note):
    """Open the full-text 'localfile'(s) associated with KEY."""

    try:
        entry = ctx.db.get_entry(key)
    except KeyError:
        raise ClickException("no entry with key '{}'.".format(key))

    try:
        # Open the localfile(s)
        for fn in entry['localfile']:
            run(['xdg-open', ctx.config['path'] / fn], stderr=DEVNULL)
    except KeyError:
        raise ClickException("entry '{}' has no localfile field."
                             .format(key))

    if clock:
        args = ['timew', 'start', 'Read', key]
        run(args, stdout=stdout)

    if note:
        # Read the ZIM configuration and find the path of the default notebook
        zim_cfg_path = Path(xdg_config_home, 'zim', 'notebooks.list')
        zim_cfg = ConfigParser()
        zim_cfg.read(zim_cfg_path)
        nb_path = Path(zim_cfg['NotebookList']['Default']).expanduser()

        # Location in the notebook hierarchy
        # TODO move to a configuration setting
        tree = ['Reading notes']

        # Candidate path for the note
        note_path = Path(
            nb_path,
            *map(lambda s: s.replace(' ', '_'), tree),
            key,
            ).with_suffix('.txt')

        # Create the note
        if not note_path.exists():
            with open(note_path, 'w') as f:
                f.write(note_template(entry))

        # Open the note
        args = ['zim', nb_path, ':'.join(tree + [key])]
        run(args)
