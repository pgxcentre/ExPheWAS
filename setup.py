#!/usr/bin/env python

# How to build source distribution
#   - python setup.py sdist --format bztar
#   - python setup.py sdist --format gztar
#   - python setup.py sdist --format zip
#   - python setup.py bdist_wheel


import os

from setuptools import setup, find_packages


MAJOR = 1
MINOR = 2
MICRO = 1
VERSION = "{0}.{1}.{2}".format(MAJOR, MINOR, MICRO)


def write_version_file(fn=None):
    if fn is None:
        fn = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.join("exphewas", "version.py"),
        )

    content = ("\n# THIS FILE WAS GENERATED AUTOMATICALLY\n"
               'exphewas_version = "{version}"\n')

    a = open(fn, "w")
    try:
        a.write(content.format(version=VERSION))
    finally:
        a.close()


def setup_package():
    # Saving the version into a file
    write_version_file()

    setup(
        name="exphewas",
        version=VERSION,
        description="Browser and tools for the gene-based PheWAS analysis.",
        url="https://github.com/legaultmarc/exphewas",
        license="MIT",
        zip_safe=False,
        install_requires=["sqlalchemy >= 1.3.10", "Flask >= 1.1.1",
                          "Flask-Cors >= 3.0.8", "psycopg2-binary >= 2.8.4",
                          "sqlalchemy-datatables >= 2.0.1",
                          "pandas >= 0.25.3"],
        packages=find_packages(),
        package_data={
            "exphewas.backend": ["templates/*", "static/*", "data/*"],
            "exphewas.db.scripts": ["data/*"],
        },
        classifiers=["Development Status :: 4 - Beta",
                     "Intended Audience :: Science/Research",
                     "License :: MIT",
                     "Operating System :: Unix",
                     "Operating System :: POSIX :: Linux",
                     "Operating System :: MacOS :: MacOS X",
                     "Operating System :: Microsoft",
                     "Programming Language :: Python",
                     "Programming Language :: Python :: 3.4",
                     "Programming Language :: Python :: 3.5",
                     "Programming Language :: Python :: 3.6",
                     "Topic :: Scientific/Engineering :: Bio-Informatics"],
        keywords="bioinformatics genetics statistics",
        entry_points={
            "console_scripts": [
                "exphewas-db=exphewas.db.scripts.cli:main"
            ],
        },
    )


if __name__ == "__main__":
    setup_package()
