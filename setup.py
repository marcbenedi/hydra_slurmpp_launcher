#!/usr/bin/env python

from setuptools import setup, find_namespace_packages
from pathlib import Path
from hydra_plugins.hydra_slurmpp_launcher import __version__

setup(
    name="hydra_slurmpp_launcher",
    version=__version__,
    description="A highly-customizable Slurm launcher for Hydra.cc",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Marc Benedi",
    author_email="marc@marcb.pro",
    url="https://github.com/marcbenedi/hydra_slurmpp_launcher",
    install_requires=[
        "hydra-core>=1.3.2", 
        "submitit>=1.4.5", 
        "hydra-submitit-launcher>=1.2.0"
    ],
    packages=find_namespace_packages(include=["hydra_plugins.*"]),
)
