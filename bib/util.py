import os
import re

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import click
import yaml


DEFAULT_CONFIG = {
    'kw_sep': ',|;',
    'lf_sep': ';',
    }


class BibItem(dict):
    """Biliography items."""

    def __init__(self, record, add_keywords, config):
        # Parse 'keywords' to a list
        if 'keywords' in record:
            record['keywords'] = [kw.strip() for kw in
                                  re.split(config['kw_sep'],
                                           record['keywords'])]
            add_keywords(record['keywords'])

        # Parse 'localfile' to a list
        if 'localfile' in record:
            record['localfile'] = [lf.strip() for lf in
                                   re.split(config['lf_sep'],
                                            record['localfile'])]

        dict.__init__(self, record)
        self.type = self['ENTRYTYPE']

    @property
    def has_file(self):
        return 'localfile' in self

    @property
    def file_exists(self):
        if type(self['localfile']) == list:
            return all([os.path.exists(lf) for lf in self['localfile']])
        else:
            return os.path.exists(self['localfile'])

    def file_rel_path(self):
        if type(self['localfile']) == list:
            return [os.path.relpath(lf) for lf in self['localfile']]
        else:
            return os.path.relpath(self['localfile'])

    def stringify(self):
        """Convert all entries to strings.

        bibtexparser.bwriter.BibTexWriter requires all records in an item
        to be strings.
        """
        for field in ('keywords', 'localfile'):
            if isinstance(self.get(field, None), list):
                self[field] = '; '.join(self[field])


class BibCLIContext:
    def __init__(self):
        self.config = DEFAULT_CONFIG

        self.keywords = set()

    def init(self, database, verbose, path):
        try:
            config_fn = os.path.join(path, '.bibpy.yaml')
            with open(config_fn) as f:
                self.config.update(yaml.load(f))
            self.config['path'] = path
        except FileNotFoundError:
            pass

        if database:
            self.config['database'] = database

        self.verbose = verbose

        # Parse the database
        self.database_fn = os.path.join(path, self.config['database'])
        self.db = self.read_database(self.database_fn)

    def cmd_config(self, cmd):
        return self.config.get(cmd, {})

    def read_database(self, filename):
        # Set up the BibTeX parser
        parser = BibTexParser()
        parser.homogenise_fields = False
        parser.ignore_nonstandard_types = False
        parser.customization = lambda r: BibItem(r,
                                                 self.keywords.update,
                                                 self.config)
        return bibtexparser.load(open(filename, 'r'), parser=parser)


# Custom decorator that uses BibCLIContext
pass_context = click.make_pass_decorator(BibCLIContext, ensure=True)


# A writer for converting entries back to strings
writer = BibTexWriter()
writer.indent = '\t'

# A database for converting entries back to strings
db = BibDatabase()


def to_string(entry_or_entries):
    """Convert *entry_or_entries* to a string."""
    # Create a fake 'database' with only one entry.
    db.entries = (entry_or_entries if isinstance(entry_or_entries, list) else
                  [entry_or_entries])

    [entry.stringify() for entry in db.entries]

    return writer.write(db)
