import re

from setuptools import setup, find_packages

if __name__ == '__main__':

    # get requirements
    with open('requirements.txt') as f:
        requirements = f.read()
        requirements = [
            r for r in requirements.splitlines() if r != '']

    # get version number
    with open('pgsheets/__init__.py') as f:
        version = f.read()
        version = re.search(
            r'^__version__\s*=\s*[\'"]([\d\.]*)[\'"]\s*$',
            version,
            re.MULTILINE).groups(1)[0]

    setup(name='pgsheets',
          version=version,
          packages=find_packages(exclude=['test', 'test.*']),
          author="Henry Stokeley",
          description=("A Python package for manipulating Google Sheets as "
                       "Pandas DataFrame objects"
                       ),
          license="MIT",
          url="https://github.com/henrystokeley/pgsheets",
          install_requires=requirements,
          test_suite='test',
          )
