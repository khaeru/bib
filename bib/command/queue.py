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
    r = re.compile(ctx.cmd_config('queue').get('include', None))

    sets = {'no_kw': set(), 'no_queue': set(), 'to_read': list()}

    for e in ctx.db.entries:
        if 'keywords' in e:
            matches = list(filter(None,
                                  [r.match(kw) for kw in e['keywords']]))
            if len(matches) > 1:
                assert False
            elif len(matches) == 1:
                pri = matches[0].groupdict()['priority']
                sets['to_read'].append(('({0}) {1[ID]}: {1[title]}\n\t'
                                        '{1[localfile]}').format(pri, e))
            else:
                sets['no_queue'].add(e['ID'])
        else:
            sets['no_kw'].add(e['ID'])

    if ctx.verbose:
        print('No keywords: %d entries' % len(sets['no_kw']),
              '\t' + ' '.join(sorted(sets['no_kw'])),
              '',
              'Some keywords: %d entries' % len(sets['no_queue']),
              '\t' + ' '.join(sorted(sets['no_queue'])),
              sep='\n', end='\n\n')

    print('Read next:',
          '\n'.join(sorted(sets['to_read'])),
          sep='\n', end='\n\n')
