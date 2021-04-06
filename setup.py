#!/usr/bin/env python
# encoding: utf-8
from setuptools import find_packages, setup

setup(
    name="bib",
    version="1.0.0dev",
    license="GNU GPL v3",
    author="Paul Natsuo Kishimoto",
    author_email="mail@paul.kishimoto.name",
    url="https://github.com/khaeru/bib",
    packages=find_packages(),
    setup_requires=["bibtexparser", "click", "pythondialog", "PyYAML"],
    entry_points="""
        [console_scripts]
        bib=bib:cli
        """,
)
