import mmap
import os
import re

from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import click
import yaml


DEFAULT_CONFIG = {
    'keywords_sep': ',|;',
    'localfile_sep': ';',
    }


class BibItem(dict):
    """Biliography item.

    bibtexparser uses dict() internally. This class adds some simple
    functionality.

    """
    def __init__(self, record, add_keywords, config):
        # Split some fields to lists
        for field in ('keywords', 'localfile'):
            try:
                separators = config[field + '_sep']
                record[field] = [part.strip() for part in
                                 re.split(separators, record[field])]
            except KeyError:
                pass

        add_keywords(record.get('keywords', []))

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
        """Convert all fields to strings.

        bibtexparser.bwriter.BibTexWriter requires all records in an item
        to be strings.
        """
        for field in ('keywords', 'localfile'):
            if isinstance(self.get(field, None), list):
                self[field] = '; '.join(self[field])


class LazyBibDatabase(BibDatabase):
    """Lazy-loading subclass of bibtexparser.bibdatabase.BibDatabase.

    To improve performance on large files, this class indexes (:func:`_index`)
    the start and end locations of each entry in the file, but does not read or
    parse them. When :func:`get_entry` is called, only the single entry is read
    and parsed.

    This functionality should be pushed upstream to bibtexparser, but that
    package is (as of 2018-11-29) unmaintained…

    """
    entry_re = re.compile(rb'^\s*@([^{]*){([^,}]*)', re.MULTILINE)

    def __init__(self, path, config):
        super(LazyBibDatabase, self).__init__()

        # Database file
        self._file = open(path, 'rb')

        # Keywords index
        self.keywords = set()

        # Index the database
        self._index()

        # Set up a parser to be used by _read_entry
        self._parser = BibTexParser(
            homogenize_fields=False,
            ignore_nonstandard_types=False,
            customization=lambda r: BibItem(r, self.keywords.update, config),
            )

    def _index(self):
        """Index the database."""
        # Use a mmap to avoid loading the entire file into memory
        m = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)

        # Iterate through matches of the regular expression for entries
        breaks = []
        for match in self.entry_re.finditer(m):
            # Store (start, entry type, entry ID)
            info = tuple([match.start()] +
                         list(map(bytes.decode, match.groups())))
            breaks.append(info)

        del m

        # Convert the breaks to an index
        self._entries_index = {}
        for idx, (start, entrytype, id) in enumerate(breaks):
            if entrytype in ('comment'):
                # Don't index comments
                continue

            try:
                # Current entry extends to the start of the next
                self._entries_index[id] = (start, breaks[idx+1][0] - start)
            except IndexError:
                # Last entry in file, length of -1 will make read() gobble
                self._entries_index[id] = (start, -1)

    def _read_entry(self, key):
        """Actually read and parse the entry with ID *key*."""
        # Locate the start of the entry
        start, length = self._entries_index[key]
        self._file.seek(start)

        # Parse the entry
        self._parser.parse(self._file.read(length))

        # bibtexparser.bparser.BibTexParser uses an internal BibDatabase that
        # is not emptied for successive calls to parse(). Empty it.
        entry = self._parser.bib_database.entries.pop()
        assert len(self._parser.bib_database.entries) == 0

        # Store for later access
        self._entries_dict[entry['ID']] = entry

        return entry

    def get_entry(self, key):
        """Retrieve the entry with ID *key*."""
        try:
            return self._entries_dict[key]
        except KeyError:
            return self._read_entry(key)

    def iter_entry_keys(self):
        """Return an iterator over entry IDs.

        This is much faster than in BibDatabase, because the entries are not
        fully parsed. Use :func:`get_entry` to retrieve the actual entry.
        """
        return self._entries_index.keys()


class BibCLIContext:
    def __init__(self):
        self.config = DEFAULT_CONFIG

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

        self.db = LazyBibDatabase(os.path.join(path, self.config['database']),
                                  self.config)

    def cmd_config(self, cmd):
        return self.config.get(cmd, {})


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
