"""This module generates readme and feature files for mkdocs.

As part of the mkdocs-gen-file plugin, this module helps to automate
readme generation using the README file and feature pages using the feature
files if they do exist.
"""

from pathlib import Path

import mkdocs_gen_files

docs_parent_dir = Path(__file__).parent.parent

# Automagically injects README file into the documentation
readme_path = docs_parent_dir / "README.md"
if readme_path.exists():
    with open(readme_path, "r") as r, mkdocs_gen_files.open(
        "readme.md", "w"
    ) as f:
        f.write(r.read())


# Injects feature files into the documentation
head_lines = (
    "Feature:",
    "Scenario:",
    "Scenario Outline:",
    "Rule:",
    "Example:",
    "Background:",
)
ignore_lines = ("@", "#")
features_dir = docs_parent_dir / "features"
for feature_path in features_dir.glob("**/*.feature"):
    with open(feature_path, "r") as f:
        relative_dir = feature_path.parent.relative_to(features_dir)
        with mkdocs_gen_files.open(
            f"scenarios/{relative_dir}/{feature_path.stem}.md", "w"
        ) as gf:
            f_line_list = f.readlines()
            for line in f_line_list:
                if any([line.strip().startswith(hl) for hl in head_lines]):
                    write_line = f"### {line}\n"
                elif any([line.strip().startswith(il) for il in ignore_lines]):
                    continue
                else:
                    write_line = f">    {line}"

                gf.write(write_line)
