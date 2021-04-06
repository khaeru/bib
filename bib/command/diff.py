import click

from ..util import pass_context


@click.command()
@click.option(
    "--exclude-from",
    "exclude",
    type=click.File("r"),
    help="Also omit keys from this file; one per line.",
)
@click.argument("other", type=click.Path(exists=True))
@pass_context
def diff(ctx, other, exclude):
    """Print keys in the database but not in OTHER."""
    keys = set(ctx.db.entries_dict.keys())

    other_db = ctx.read_database(other)
    keys -= set(other_db.entries_dict.keys())

    if exclude:
        keys -= set(exclude.read().split())

    print(*sorted(keys), sep="\n")
