.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Finite Amplitude Rossby Wave Diagnostics Documentation
======================================================

.. rst-class:: center

Clare S. Y. Huang\ |^1|, Christopher Polster |^2| and Noboru Nakamura\ |^1|

.. rst-class:: center

|^1|\ The University of Chicago, Chicago, Illinois

|^2|\ Johannes Gutenberg-Universität Mainz, Germany

.. rst-class:: center

Last update: 03/12/2024

Description
-----------
(to be filled in )

.. Underline with '-'s to make a second-level heading.

Version & Contact info
----------------------

Here you should describe who contributed to the diagnostic, and who should be
contacted for further information:

- Version/revision information: version 1 (03/12/2024)
- PI (name, affiliation, email): Clare S. Y. Huang (The University of Chicago, csyhuang@uchicago.edu)
- Developer/point of contact: Clare S. Y. Huang (The University of Chicago, csyhuang@uchicago.edu)
- Other contributors: Christopher Polster, Noboru Nakamura

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
Unless you've distributed your script elsewhere, you don't need to change this.

Functionality
-------------

(to be filled in)

Required programming language and libraries
-------------------------------------------

(to be filled in)


Required model output variables
-------------------------------

(to be filled in)

References
----------

(to be filled in)

More about this diagnostic
--------------------------

(to be filled in)

Links to external sites
^^^^^^^^^^^^^^^^^^^^^^^

(to be filled in)

More references and citations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(to be filled in)

Figures
^^^^^^^

Images **must** be provided in either .png or .jpeg formats in order to be 
displayed properly in both the html and pdf output.

Here's the syntax for including a figure in the document:

.. code-block:: restructuredtext

   .. _my-figure-tag: [only needed for linking to figures]

   .. figure:: [path to image file, relative to the source.rst file]
      :align: left
      :width: 75 % [these both need to be indented by three spaces]

      Paragraphs or other text following the figure that are indented by three
      spaces are treated as a caption/legend, eg:

      - red line: a Gaussian
      - blue line: another Gaussian

which produces

.. _my-figure-tag:

.. figure:: gaussians.jpg
   :align: left
   :width: 75 %

   Paragraphs or other text following the figure that are indented by three
   spaces are treated as a caption/legend, eg:

   - blue line: a Gaussian
   - orange line: another Gaussian

The tag lets you refer to figures in the text, e.g. 
``:ref:`Figure 1 <my-figure-tag>``` → :ref:`Figure 1 <my-figure-tag>`.

Equations
^^^^^^^^^

Accented and Greek letters can be written directly using Unicode: é, Ω. 
(Make sure your text editor is saving the file in UTF-8 encoding).

Use the following syntax for superscripts and subscripts in in-line text:

.. code-block:: restructuredtext

   W m\ :sup:`-2`\ ; CO\ :sub:`2`\ .

which produces: W m\ :sup:`-2`\ ; CO\ :sub:`2`\ .
Note one space is needed after both forward slashes in the input; these spaces 
are not included in the output.

Equations can be written using standard 
`latex <https://www.reed.edu/academic_support/pdfs/qskills/latexcheatsheet.pdf>`__ 
(PDF link) syntax. Short equations in-line with the text can be written as 
``:math:`f = 2 \Omega \sin \phi``` → :math:`f = 2 \Omega \sin \phi`.

Longer display equations can be written as follows. Note that a blank line is 
needed after the ``.. math::`` heading and after each equation, with the 
exception of aligned equations.

.. code-block:: restructuredtext

   .. math::

      \frac{D \mathbf{u}_g}{Dt} + f_0 \hat{\mathbf{k}} \times \mathbf{u}_a &= 0; \\
      \frac{Dh}{Dt} + f \nabla_z \cdot \mathbf{u}_a &= 0,

      \text{where } \mathbf{u}_g = \frac{g}{f_0} \hat{\mathbf{k}} \times \nabla_z h.

which produces:

.. math::

   \frac{D \mathbf{u}_g}{Dt} + f_0 \hat{\mathbf{k}} \times \mathbf{u}_a &= 0; \\
   \frac{Dh}{Dt} + f \nabla_z \cdot \mathbf{u}_a &= 0,

   \text{where } \mathbf{u}_g = \frac{g}{f_0} \hat{\mathbf{k}} \times \nabla_z h.

The editor at `https://livesphinx.herokuapp.com/ 
<https://livesphinx.herokuapp.com/>`__ can have issues formatting complicated 
equations, so you may want to check its output with a latex-specific editor, 
such as `overleaf <https://www.overleaf.com/>`__ or other `equation editors 
<https://www.codecogs.com/latex/eqneditor.php>`__.
