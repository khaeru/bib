import click

from ..util import pass_context


@click.command()
@pass_context
def curl(ctx):
    """Return args for `curl -K -` on 'url' fields.

    For each entry in the database, lines are output that specify the curl
    arguments --url, --output, and --time-cond. This output can be piped
    to
    """
    template = "\n".join(['url="{0}"', 'output="{1}"', "time-cond {1} "])

    for e in ctx.db.entries:
        url = e.get("url", None)
        localfile = e.get("localfile", None)
        if url is None or localfile is None:
            continue
        print(template.format(url, localfile[0]))
