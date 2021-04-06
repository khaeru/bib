from copy import deepcopy
from datetime import datetime
from glob import iglob
from itertools import chain
import os
import re
import readline

from bibtexparser.customization import author
from bibtexparser.bparser import BibTexParser
from pyparsing import ParseException
import click
from dialog import Dialog

from ..util import pass_context, to_string


def _select_file(key, path):
    """Select a file from the directory containing *path*.

    A command-line dialog is displayed. *key* is used to prompt the user.
    """

    start = os.path.join(os.path.dirname(path), ".")

    d = Dialog()
    lines, cols = d.maxsize()
    args = dict(
        cancel_label="No file",
        height=lines - 10,
        width=cols - 2,
        no_shadow=True,
        no_lines=True,
        title="Select a file for entry: {}".format(key),
    )

    while True:
        result, target = d.fselect(start, **args)
        if target != start:
            break

    os.system("clear")

    if result == "ok":
        return target
    else:
        return None


def _add_clean(d):
    """Custom entry cleaning for add()."""

    # Delete the leading text 'ABSTRACT'
    if "abstract" in d and d["abstract"].lower().startswith("abstract"):
        d["abstract"] = d["abstract"][8:].strip()

    d["author"] = d["author"].replace("\n", " ")

    if "doi" in d:
        # Show a bare DOI, not a URL
        d["doi"] = re.sub("https?://(dx.)?doi.org/", "", d["doi"])
        # Don't show eprint or url fields if a DOI is present
        # (e.g ScienceDirect)
        d.pop("eprint", None)
        d.pop("url", None)

    # BibLaTeX: use 'journaltitle' for the name of the journal
    if "journal" in d:
        d["journaltitle"] = d.pop("journal")

    if "pages" in d:
        # Pages: use an en-dash
        d["pages"] = d["pages"].replace("--", "–").replace("-", "–").replace(" ", "")

    # Delete any empty fields or those containing '0'
    for k in list(d.keys()):
        if d[k] in ["0", ""]:
            del d[k]

    return d


def guess_key(entry):
    entry = author(deepcopy(entry))
    if len(entry["author"]) > 2:
        a = entry["author"][0].split(",")[0].lower()
    else:
        a = "-".join([a.split(",")[0].lower() for a in entry["author"]])

    # Use YYYY if the year is not present
    year = entry.get("year", "YYYY")

    return f"{a}-{year}"


# https://stackoverflow.com/a/8505387/2362198
def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def clean_str(s):
    # # Add a trailing comma on the last entry:
    # # https://github.com/sciunto-org/python-bibtexparser/issues/47
    # s = re.sub(r'([^,])(\s*}\s*)\Z', r'\1,\2', s)

    # Compress multiple 'keywords'
    parts = re.split(r'(keywords)\s=\s[{"]([^}"]*)[}"],', s)
    result = ""
    keywords = []
    take = False
    for p in parts:
        if p == "keywords":
            take = True
            continue
        elif take:
            keywords.append(p)
            take = False
            continue
        elif p.strip() == "":
            continue

        if len(keywords):
            result += "keywords = {%s}," % "; ".join(keywords)

        # DEBUG print the parts
        # print('part: <%s>' % p)

        result += p

    return result


@click.command(name="import")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@pass_context
def import_command(ctx, paths):
    """Read new entries into the database.

    PATHS may be zero or more .bib files or directories containing .bib files
    to import.

    Configuration file keys

    \b
    import:
      path: a default path to check for .bib files to import, if no PATHS are
            given.
    """
    # If no files
    if len(paths) == 0:
        # Directory from which to import entries
        paths = [ctx.cmd_config("import").get("path", ".")]

    paths = [os.path.join(p, "*.bib") if os.path.isdir(p) else p for p in paths]

    # A parser for reading entries
    parser = BibTexParser()
    parser.homogenise_fields = False
    parser.customization = _add_clean

    # Iterate over files in the add_dir
    for fn in chain(*map(iglob, paths)):
        os.system("clear")
        print("Importing", fn, end=":\n\n")

        # Read and parse the file
        with open(fn, "r") as f:
            s = f.read()
            print(s, end="\n\n")

        try:
            e = parser.parse(clean_str(s)).entries[-1]
        except ParseException:
            print(clean_str(s))
            raise

        abstract = e.pop("abstract", None)

        print("Parsed entry:", to_string(e), sep="\n\n")

        if abstract is not None:
            print("Abstract:", abstract, sep="\n\n")

        # Ask user for a key
        while True:
            key = input_with_prefill(
                "\nEnter key for imported entry "
                "([] Skip, [D]elete without importing, [Q]uit): ",
                guess_key(e),
            )
            try:
                ctx.db.get_entry(key)
                print("Key already exists.")
            except KeyError:
                break

        if key == "":
            continue
        elif key.lower() == "d":
            os.remove(fn)
            continue
        elif key.lower() == "q":
            break
        else:
            # Change the entry key
            e["ID"] = key

        # Add a custom field with the current date
        e["entrydate"] = datetime.now().isoformat(timespec="minutes")

        # Select a full text file to go with the entry
        fn_local = _select_file(e["ID"], ctx.cmd_config("import").get("path", "."))
        if fn_local:
            e["localfile"] = os.path.basename(fn_local)

        # Append the entry to the database
        with open(ctx.config["database"], "a") as f_db:
            f_db.write("\n")
            f_db.write(to_string(e))

        # Write the abstract
        if abstract:
            fn_abstract = ctx.config["path"] / "abstracts" / ("%s.tex" % key)
            with open(fn_abstract, "x") as f_abstract:
                f_abstract.write(abstract)

        # Move the full text file
        if fn_local:
            os.system(
                'mv -n "{}" "{}"'.format(fn_local, ctx.config["path"] / e["localfile"])
            )

        # Remove the imported entry file
        remove = input("\nRemove imported file %s ([Y]es, [enter] to " "keep)? " % fn)
        if remove.lower() == "y":
            os.remove(fn)
