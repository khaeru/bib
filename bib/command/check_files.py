from glob import iglob
from itertools import filterfalse, zip_longest
import os
import re

import click

from ..util import pass_context


def _check_files_plain(ok, other, missing, broken, files):
    print('OK: %d entries + matching files' % len(ok),
          '\t' + ' '.join(sorted(ok)),
          '',
          'OK: %d other entries by filter rules' % len(other),
          '\t' + ' '.join(sorted(other)),
          '',
          "Missing: %d entries w/o 'localfile' key" % len(missing),
          '\t' + ' '.join(sorted(missing)),
          '',
          "Broken: %d entries w/ missing 'localfile'" % len(broken),
          '\n'.join(['\t{}\t→\t{}'.format(*e) for e in sorted(broken)]),
          '',
          'Not listed in any entry: %d files' % len(files),
          '\t' + '\n\t'.join(sorted(files)),
          sep='\n', end='\n')


def _check_files_csv(ok, other, missing, broken, files):
    lines = ['\t'.join(['ok', 'other', 'missing', 'broken', 'files'])]
    for group in zip_longest(ok, other, missing,
                             map(lambda x: '{} -> {}'.format(*x), broken),
                             files, fillvalue=''):
        lines.append('\t'.join(group))
    print('\n'.join(lines))


@click.command()
@click.option('--format', 'fmt', type=click.Choice(['plain', 'csv']),
              default=None, help="Output format.")
@pass_context
def check_files(ctx, fmt):
    """Check files listed in 'localfiles' fields.

    Configuration file keys:

    \b
    check_files:
      format: Same as the --format option.
      ignore: List of glob patterns of paths to ignore.
      filter: List of triples, each with the following keys:
        field: BibLaTeX data model field, eg. 'keywords'
        value: String value to match
         sort: One of 'ok', 'other', 'missing' or 'broken': the list in which
               to place matching entries.
    """
    # Get configuration options
    options = ctx.cmd_config('check_files')
    ignore = options.get('ignore', [])
    filters = options.get('filter', [])

    # Sets for recording entries:
    # - ok: has 'localfile' field, file exists
    # - other: hardcopies or online articles
    # - missing: no 'localfile' field
    # - broken: 'localfile' field exists, but is wrong
    sets = {k: set() for k in ['ok', 'other', 'missing', 'broken']}

    # Get the set of files in the current directory
    r = re.compile('(' + ')|('.join(ignore) + ')')
    files = filterfalse(os.path.isdir,
                        iglob(str(ctx.config['path'] / '**'), recursive=True))
    files = sorted(filterfalse(r.search, files))

    # Iterate through database entries
    for e in ctx.db.iter_entries():
        if e.has_file:
            if e.file_exists(ctx.config['path']):
                sets['ok'].add(e['ID'])
                for fn in e.file_rel_path(ctx.config['path']):
                    try:
                        files.remove(fn)
                    except ValueError:
                        if os.path.exists(fn):
                            # File exists, but has perhaps been filtered or
                            # is outside the tree.
                            continue
                        else:
                            raise
            else:
                sets['broken'] |= {(e['ID'], lf) for lf in e['localfile']}
        else:
            # Apply user filters
            done = False
            for f in filters:
                if f['field'] in e and f['value'] in e[f['field']]:
                    sets[f['sort']].add(e['ID'])
                    done = True
                    break
            if not done:
                sets['missing'].add(e['ID'])

    # Output
    output_format = options.get('format', 'csv') if fmt is None else fmt
    if output_format == 'plain':
        output = _check_files_plain
    elif output_format == 'csv':
        output = _check_files_csv
    output(sorted(sets['ok']), sorted(sets['other']),
           sorted(sets['missing']), sorted(sets['broken']),
           files)
