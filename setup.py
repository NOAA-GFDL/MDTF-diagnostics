#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

# Leave option to run commands post-install
# see https://stackoverflow.com/a/36902139


def _post_install():
    pass


class PostDevelopCommand(develop):
    """Post-installation for development mode, same as install for now."""
    def run(self):
        _post_install()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        _post_install()
        install.run(self)


with open("README.md", 'r') as f:
    long_description = f.read()
packages = find_packages()
setup(
    name='MDTF-diagnostics',
    version='4.2',
    description='Process-oriented diagnostics for weather and climate simulations',
    license='LGPLv3',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='MDTF Collaboration',
    author_email='20195932+wrongkindofdoctor@users.noreply.github.com',
    url="https://github.com/NOAA-GFDL/MDTF-diagnostics",
    classifiers=[
            # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
            "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
            'Programming Language :: Python :: 3.12'
    ],
    packages=find_packages(),
    include_package_data=True,
    #entry_points={
    #    'console_scripts': [
    #        'mdtf = MDTF-diagnostics.mdtf_framework:main'
    #    ],
    #},
    cmdclass={  # hook for post-install commands
        'develop': PostDevelopCommand,
        'install': PostInstallCommand
    }
    #   install_requires=[...] #external packages as dependencies
)
