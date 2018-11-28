# Command-line utility for BibTeX databases
© 2016–2018 Paul Natsuo Kishimoto (<mail@paul.kishimoto.name>)

Licensed under the GNU GPL v3.

`bib` provides commands to work with BibTeX databases. To specify the default database, use the `--database` command-line option, or set a configuration file (below).

 - `check_files`: check for the existence of file paths pointed to by entry `localfile` fields.
 - `curl`: return args for `curl -K -`, using entry `url` fields.
 - `diff OTHER`: display entries in the database but not in `OTHER`.
 - `import PATHS`: read new entries into the database from `.bib` files in `PATHS`.
 - `list FIELD`: list all unique values of `FIELD`.
 - `note_template`: return a (Zim)[] note template for entry `KEY`.
 - `read KEY`: open the local file for entry `KEY`.
 - `queue`: display a reading queue.

Use `bib --help` for more detailed documentation.

## Configuration

`bib` reads a configuration file `.bibpy.yaml` in:
- the current directory,
- `BIBPY_PATH`, or
- the path given by `--path` command-line option.

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
