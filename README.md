# Command-line utility for BibTeX databases
© 2016–2018 Paul Natsuo Kishimoto (<mail@paul.kishimoto.name>)

Licensed under the GNU GPL v3.

Use `bib --help` for documentation.

Reads a file `.bibpy.yaml` in the current directory or in `PATH` that may contain general or command-specific keys. The only general configuration key is:

```yaml
database: path/to/database  # same as the --database option
```

The following commands have command-specific keys. For these, use a top-level
key with the command name, and then place command-specific keys underneath. Use
`bib COMMAND --help` to see documentation about these keys:

- `check_files`
- `import`
- `queue`
