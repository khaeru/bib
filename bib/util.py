import mmap
import os
import re
from collections import OrderedDict
from pathlib import Path

import click
import yaml
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from tqdm import tqdm

DEFAULT_CONFIG = {
    "keywords_sep": ",|;",
    "localfile_sep": ";",
}


class BibItem(dict):
    """Biliography item.

    bibtexparser uses dict() internally. This class adds some simple
    functionality.

    """

    def __init__(self, record, add_keywords, config):
        # Split some fields to lists
        for field in ("keywords", "localfile"):
            try:
                separators = config[field + "_sep"]
                record[field] = [
                    part.strip() for part in re.split(separators, record[field])
                ]
            except KeyError:
                pass

        add_keywords(record.get("keywords", []))

        dict.__init__(self, record)

        self.type = self["ENTRYTYPE"]

    @property
    def has_file(self):
        return "localfile" in self

    def file_exists(self, root=Path()):
        return all([(root / lf).exists() for lf in self["localfile"]])

    def file_rel_path(self, root=Path()):
        return [(root / lf).relative_to(Path.cwd()) for lf in self["localfile"]]

    def stringify(self):
        """Convert all fields to strings.

        bibtexparser.bwriter.BibTexWriter requires all records in an item
        to be strings.
        """
        for field in ("keywords", "localfile"):
            if isinstance(self.get(field, None), list):
                self[field] = "; ".join(self[field])


class LazyBibDatabase(BibDatabase):
    """Lazy-loading subclass of bibtexparser.bibdatabase.BibDatabase.

    To improve performance on large files, this class indexes (:func:`_index`)
    the start and end locations of each entry in the file, but does not read or
    parse them. When :func:`get_entry` is called, only the single entry is read
    and parsed.

    This functionality should be pushed upstream to bibtexparser.

    """

    entry_re = re.compile(rb"^\s*@([^{]*){([^,}]*)", re.MULTILINE)

    def __init__(self, path, config):
        # To ##### from BibDatabase.__init__()

        # super(LazyBibDatabase, self).__init__()
        self._entries_dict = {}
        # List of BibTeX comment (`@comment{...}`) blocks.
        self.comments = []
        # OrderedDict of BibTeX string definitions (`@string{...}`). In order of
        # definition.
        self.strings = OrderedDict()
        #: List of BibTeX preamble (`@preamble{...}`) blocks.
        self.preambles = []

        #: List of fields that should not be updated when resolving crossrefs
        self._not_updated_by_crossref = ["_FROM_CROSSREF"]

        #####

        # Database file
        self._file = open(path, "rb")

        # Keywords index
        self.keywords = set()

        # Index the database
        self._all_loaded = False
        self._index()

        # Set up a parser to be used by _read_entry
        self._parser = BibTexParser(
            homogenize_fields=False,
            ignore_nonstandard_types=False,
            customization=lambda r: BibItem(r, self.keywords.update, config),
        )

    @property
    def entries(self):
        yield from self._generate_entries()

    def _index(self):
        """Index the database."""
        # Use a mmap to avoid loading the entire file into memory
        m = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)

        # Iterate through matches of the regular expression for entries
        breaks = []
        for match in self.entry_re.finditer(m):
            # Store (start, entry type, entry ID)
            info = [match.start()] + list(map(bytes.decode, match.groups()))
            if info[2] == "":
                info[2] = "<entry without ID at {0}>".format(*info)
            breaks.append(tuple(info))

        del m

        # Convert the breaks to an index
        self._entries_index = {}
        for idx, (start, entrytype, id) in enumerate(breaks):
            if entrytype in ("comment"):
                # Don't index comments
                continue

            try:
                # Current entry extends to the start of the next
                self._entries_index[id] = (start, breaks[idx + 1][0] - start)
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
        self._entries_dict[entry["ID"]] = entry

        return entry

    def iter_entries(self, progress=False):
        if progress:
            return tqdm(
                self._generate_entries(), total=len(self._entries_index), leave=False
            )
        else:
            return iter(self._generate_entries())

    def _generate_entries(self):
        if self._all_loaded:
            yield from self._entries_dict.values()
        else:
            for key in self.iter_entry_keys():
                yield self.get_entry(key)
            self._all_loaded = True

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
        self.config["path"] = Path(path)
        try:
            config_fn = self.config["path"] / ".bibpy.yaml"
            with open(config_fn) as f:
                self.config.update(yaml.safe_load(f))
        except FileNotFoundError:
            pass

        if database:
            self.config["database"] = Path(database).resolve()

        self.config["database"] = self.config["path"] / self.config["database"]

        self.verbose = verbose

        self.db = LazyBibDatabase(
            os.path.join(path, self.config["database"]), self.config
        )

    def cmd_config(self, cmd):
        return self.config.get(cmd, {})


# Custom decorator that uses BibCLIContext
pass_context = click.make_pass_decorator(BibCLIContext, ensure=True)


# A writer for converting entries back to strings
writer = BibTexWriter()
writer.indent = "\t"

# A database for converting entries back to strings
db = BibDatabase()


def to_string(entry_or_entries):
    """Convert *entry_or_entries* to a string."""
    # Create a fake 'database' with only one entry.
    db.entries = (
        entry_or_entries if isinstance(entry_or_entries, list) else [entry_or_entries]
    )

    try:
        [entry.stringify() for entry in db.entries]
    except AttributeError:
        pass

    return writer.write(db)
