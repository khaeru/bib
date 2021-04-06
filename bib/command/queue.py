import re

import click

from ..util import pass_context


@click.command()
@pass_context
def queue(ctx):
    """Display a reading queue.

    Entries matching the configuration value are considered to be part of a
    reading queue, sorted from lowest to highest according to priority.

    With --verbose/-v, *queue* also displays list of entries with no
    keywords; and with keywords but no queue match.


    Configuration File Keys

    \b
    queue:
      include: Required. A regular expression to match against values in each
               entry's 'keywords' field. Must contain a named group 'priority'
               that gives a sortable value indicating queue priority.
    """
    r = re.compile(ctx.cmd_config("queue")["include"])

    to_read = list()

    for e in filter(lambda e: "keywords" in e, ctx.db.iter_entries(True)):
        matches = list(filter(None, [r.match(kw) for kw in e["keywords"]]))

        if len(matches) > 1:
            print("Error: entry contains multiple queue priority keywords:", e)
            return
        elif len(matches) == 1:
            to_read.append(
                "{0} {1[ID]}: {2}".format(
                    matches[0].group("priority"), e, e["title"].strip("{}")
                )
            )

    if len(to_read):
        print("\n".join(sorted(to_read, reverse=True)), end="\n\n")
    else:
        print("Empty reading queue.")
