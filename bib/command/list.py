import click

from ..util import pass_context


@click.command('list')
@click.argument('field')
@click.option('--sort', is_flag=True)
@pass_context
def list_command(ctx, field, sort):
    """List all unique values of FIELD."""
    values = set()
    for e in ctx.db.entries:
        value = e.get(field, None)
        if value is None:
            continue
        elif not isinstance(value, list):
            value = [value]
        values |= set(value)

    if sort:
        values = sorted(values)

    print('\n'.join(values))
