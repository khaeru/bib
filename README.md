# Command-line utility for BibTeX databases
© 2016–2018 Paul Natsuo Kishimoto (<mail@paul.kishimoto.name>)

Licensed under the GNU General Public License, version 3.

`bib` provides commands to work with BibTeX databases. To specify the default database, use the `--database` command-line option, or set a configuration file (below).

 - `check-files`: check for the existence of file paths pointed to by entry `localfile` fields.
 - `curl`: return args for `curl -K -`, using entry `url` fields.
 - `diff OTHER`: display entries in the database but not in `OTHER`.
 - `export KEYS`: print out a subset of the entries in the database.
 - `import PATHS`: interactively read new entries into the database from `.bib` files found in `PATHS`.
 - `list FIELD`: list all unique values appearing in `FIELD` (e.g. 'keywords') across the entire database.
 - `note-template`: return a (Zim)[http://zim-wiki.org] note template for entry `KEY`.
 - `read KEY`: open the local file for entry `KEY`.
 - `queue`: display a reading queue.

Use `bib --help` and `bib COMMAND --help` for more detailed documentation.

## Configuration

`bib` reads a configuration file `.bibpy.yaml` in:

- the path given by `--path` command-line option,
- the current directory, or
- the directory given by the `BIBPY_PATH` environment variable.

The only general configuration key is:

```yaml
database: path/to/database.bib  # same as the --database option
```

The following commands have command-specific keys. For these, use a top-level
key with the command name, and then place command-specific keys underneath. Use
`bib COMMAND --help` to see documentation about these keys:

- `check_files`
- `import`
- `queue`

For example:

```yaml
import:
  path: 0sort/bib

check_files:
  format: csv

  ignore:
    - .git
    - .gitignore
    - .rsync-filter
    - references.bib
    - biblatex-dm.cfg

  filter:
    # Don't check for files for all entries of a given type
    - field: ENTRYTYPE
      value: online
      sort: other

    # Don't check for files with a given keyword
    - field: keywords
      value: x-custom:hardcopy
      sort: other

queue:
  # Get queue inclusion and priority from a custom keyword
  include: x-queue-priority:(?P<priority>\w+)
```
