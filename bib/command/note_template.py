from datetime import datetime, timezone

from bibtexparser.customization import author
import click

from ..util import pass_context


note_string = """Content-Type: text/x-zim-wiki
Wiki-Format: zim 0.4
Creation-Date: {date}

====== {author} {year} ======
//{title}//
Created {date_text}

"""


@click.command()
@click.argument('key')
@pass_context
def note_template(ctx, key):
    """Return a Zim note template for KEY."""
    entry = author(ctx.db.entries_dict.get(key, None))

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
    else:
        values['author'] = '{} & {}'.format(surname(0), surname(1))

    print(note_string.format(**values))
