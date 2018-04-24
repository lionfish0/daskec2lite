# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('daskec2lite/daskec2lite.py').read(),
    re.M
    ).group(1)


setup(
    name = "cmdline-daskec2lite",
    packages = ["daskec2lite"],
    entry_points = {
        "console_scripts": ['daskec2lite = daskec2lite.daskec2lite:main']
        },
    version = version,
    description = "Setup and run a DASK cluster on EC2.",
    author = "Mike Smith",
    author_email = "m.t.smith@sheffield.ac.uk",
    url = "https://github.com/lionfish0/daskec2lite",
    )
