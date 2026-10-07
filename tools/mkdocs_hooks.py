"""MkDocs hooks for the course website.

The lectures are written for GitHub (README.md files in en/ and hu/). These hooks
let MkDocs publish them unchanged:

* on_files   adds the repository's README.md, LICENSE, en/ and hu/ to the site,
             with their figures, programs and scripts (MkDocs cannot use the
             repository root itself as its docs folder);
* on_config  builds the navigation from the lecture titles (the first "# "
             line of each README.md), in folder order;
* on_page_markdown  marks every <details> box as Markdown, because GitHub
             renders Markdown inside HTML blocks and Python-Markdown does not.
"""

import os
import re

from mkdocs.structure.files import File

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ["README.md", "LICENSE", "en", "hu"]
SKIP_DIRS = {"__pycache__", ".git"}
LANGUAGES = [("en", "English"), ("hu", "Magyar")]


def _title(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return default


def on_config(config):
    nav = [{_title(os.path.join(ROOT, "README.md"), "Home"): "README.md"}]
    for lang, label in LANGUAGES:
        lang_dir = os.path.join(ROOT, lang)
        section = [f"{lang}/README.md"]
        for name in sorted(os.listdir(lang_dir)):
            readme = os.path.join(lang_dir, name, "README.md")
            if re.match(r"\d\d-", name) and os.path.isfile(readme):
                number = int(name[:2])
                section.append({f"{number}. {_title(readme, name)}": f"{lang}/{name}/README.md"})
        nav.append({label: section})
    config["nav"] = nav
    return config


def on_files(files, config):
    for source in SOURCES:
        full = os.path.join(ROOT, source)
        if os.path.isfile(full):
            paths = [source]
        else:
            paths = []
            for directory, subdirs, names in os.walk(full):
                subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS)
                for name in sorted(names):
                    rel = os.path.relpath(os.path.join(directory, name), ROOT)
                    paths.append(rel.replace(os.sep, "/"))
        for rel in paths:
            files.append(File(rel, ROOT, config["site_dir"], config["use_directory_urls"]))
    return files


_DETAILS = re.compile(r"<details(?![^>]*\bmarkdown=)([^>]*)>")
_FENCE = re.compile(r"^(```|~~~)")
# A relative link to a folder, e.g. (../05-interrupts/#anchor) or (en/).
_DIR_LINK = re.compile(r"\]\((?![a-z]+:|/|#)([^()\s#]*/)(#[^()\s]*)?\)")


def on_page_markdown(markdown, page, config, files):
    page_dir = os.path.dirname(os.path.join(ROOT, page.file.src_path))

    def dir_link(m):
        # GitHub shows a folder's README.md; point MkDocs at that file so it can
        # check the link and its anchor and produce the right URL.
        target, anchor = m.group(1), m.group(2) or ""
        if os.path.isfile(os.path.join(page_dir, target, "README.md")):
            return f"]({target}README.md{anchor})"
        return m.group(0)

    out, in_code = [], False
    for line in markdown.split("\n"):
        if _FENCE.match(line.lstrip()):
            in_code = not in_code
        elif not in_code:
            line = _DETAILS.sub(r'<details markdown="1"\1>', line)
            line = _DIR_LINK.sub(dir_link, line)
        out.append(line)
    return "\n".join(out)
