import click

from ..util import pass_context


@click.command("list")
@click.argument("field")
@click.option("--sort", is_flag=True)
@pass_context
def list_command(ctx, field, sort):
    """List all unique values of FIELD."""
    values = set()
    for e in filter(lambda e: field in e, ctx.db.iter_entries(True)):
        values |= set(e[field] if isinstance(e[field], list) else [e[field]])

    if sort:
        values = sorted(values)

    print("\n".join(values))
