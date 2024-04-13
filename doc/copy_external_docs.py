"""Simple Sphinx extension to copy source files from outside the Sphinx
TOCtree root.
This is a longstanding limitation of sphinx; see
https://github.com/sphinx-doc/sphinx/issues/701 and
https://stackoverflow.com/q/10199233 .
This extension implements a workaround that simply copies the source files into
the Sphinx source directory before compilation, and generates the table of
contents automatically.
Implementation is based on
https://gist.github.com/khaeru/3185679f4dd83b16a0648f6036fb000e
by Paul Natsuo Kishimoto; adapted to python2 and the specific MDTF directory
structure.
Specifically, we use this to copy POD documentation files and site-specific
documentation files, stores alongside individual PODs and site files in
/diagnostics and /sites.
"""
import os
import shutil
import sphinx.util

# generate POD toc source file on-the-fly
_pod_toc_header = """
Diagnostics reference
---------------------
.. toctree::
   :maxdepth: 2

   pod_summary
"""

# generate site toc source file on-the-fly
_site_toc_header = """
Site-specific documentation
---------------------------
.. toctree::
   :maxdepth: 1

"""

# generate tools toc source file on-the-fly
_tools_toc_header = """
Tools documentation
---------------------------
.. toctree::
   :maxdepth: 1

"""


def find_copy_make_toc(type_, docs_dir, search_root, header):
    """Look for documentation files, copy them to the build directory, and
    generate toc file linking to pod/site documentation.
    Args:
        type_ (str): either "pod" or "site".
        docs_dir (str): Directory this script is located in.
        search_root (str): Directory to search for PODs or sites.
        header (str): header of the toc file.
    """

    def _docname(item):
        """Helper for status_iterator()."""
        return str(os.path.basename(item))

    # destination directory to copy docs to
    sphinx_subdir = 'sphinx_{}'.format(type_)
    sphinx_dir = os.path.join(docs_dir, sphinx_subdir)
    if not os.path.isdir(sphinx_dir):
        os.makedirs(sphinx_dir)

    # find PODs or sites as directories under search_root
    entries = [x for x in os.listdir(search_root)
               if os.path.isdir(os.path.join(search_root, x)) and x[0].isalnum()
               ]
    # Case-insensitive alpha sort
    entries = sorted(entries, key=(lambda s: s.lower()))  # handles unicode
    # put example POD documentation first
    if 'example' in entries:
        entries.remove('example')
        entries.insert(0, 'example')

    # find documentation files
    # = all non-PDF files (.rst and graphics) in /doc subdirectory
    docs = []
    for entry in entries:
        doc_dir = os.path.join(search_root, entry, 'doc')
        if os.path.isdir(doc_dir):
            docs.extend([
                os.path.join(doc_dir, x) for x in os.listdir(doc_dir)
                if os.path.isfile(os.path.join(doc_dir, x)) and not x.endswith('.pdf')
            ])

    # copy the docs we found
    iter_ = sphinx.util.display.status_iterator(
        docs, 'Copying {} files... '.format(type_),
        color='purple', stringify_func=_docname
    )
    for source in iter_:
        shutil.copy2(source, sphinx_dir)

    # create toc file, either "pod_toc.rst" or "site_toc.rst"
    toc_path = os.path.join(docs_dir, 'sphinx', '{}_toc.rst'.format(type_))
    if os.path.exists(toc_path):
        os.remove(toc_path)
    with open(toc_path, 'w') as file_:
        file_.write(header)
        for entry in entries:
            # correct number of spaces for .rst indentation
            file_.write('   ../{}/{}\n'.format(sphinx_subdir, entry))


def config_inited(app, config):
    cwd = app.srcdir

    # Process PODs: find, copy, make toc
    pod_root = os.path.abspath(os.path.join(cwd, '..', 'diagnostics'))
    find_copy_make_toc("pods", cwd, pod_root, _pod_toc_header)

    # Process tools docs: find, copy, make toc
    tools_root = os.path.abspath(os.path.join(cwd, '..', 'tools'))
    find_copy_make_toc("tools", cwd, tools_root, _tools_toc_header)


def setup(app):
    # call the above function in the Sphinx build process after the 'config'
    # object has been initialized but before anything else
    app.connect('config-inited', config_inited)
