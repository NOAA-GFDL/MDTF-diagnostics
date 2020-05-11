"""Crude Sphinx extension to copy source files from outside the Sphinx 
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
"""
import os
import shutil
from sphinx.util import status_iterator

# generate POD toc source file on-the-fly
_pod_toc_header = """
Diagnostics reference
---------------------

.. toctree::
   :maxdepth: 2

   pod_summary
   ../sphinx_pods/example
"""

def config_inited(app, config):
    def _docname(item):
        """Helper for status_iterator()."""
        return str(os.path.basename(item))

    cwd = app.srcdir
    pod_root = os.path.abspath(os.path.join(cwd, '..', 'diagnostics'))
    sphinx_dir = os.path.join(cwd, 'sphinx_pods')
    if not os.path.isdir(sphinx_dir):
        os.makedirs(sphinx_dir)

    # assemble list of docs in POD's folders
    docs = []
    pods = sorted([
            x for x in os.listdir(pod_root) \
            if os.path.isdir(os.path.join(pod_root, x)) and x[0].isalnum()
        ], key=(lambda s: s.lower()) # handles unicode 
    )
    for pod in pods:
        pod_doc = os.path.join(pod_root, pod, 'doc')
        if os.path.isdir(pod_doc):
            docs.extend([
                os.path.join(pod_doc, x) for x in os.listdir(pod_doc) \
                if os.path.isfile(os.path.join(pod_doc, x)) and not x.endswith('.pdf')
            ])

    # Wrap iterator for logging
    iter_ = status_iterator(
        docs, 'Copying POD files... ', color='purple', stringify_func=_docname
    )
    # Copy the POD files
    for source in iter_:
        shutil.copy2(source, sphinx_dir)

    # generate POD toc
    pod_toc_path = os.path.join(cwd, 'sphinx', 'pod_toc.rst')
    if os.path.exists(pod_toc_path):
        os.remove(pod_toc_path)
    if 'example' in pods:
        pods.remove('example')
    with open(pod_toc_path, 'w') as file_:
        file_.write(_pod_toc_header)
        for pod in pods:
            file_.write('   ../sphinx_pods/'+pod+'\n')

def setup(app):
    # call the above function in the Sphinx build process after the 'config' 
    # object has been initialized but before anything else
    app.connect('config-inited', config_inited)
