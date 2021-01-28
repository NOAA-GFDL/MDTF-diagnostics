.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Example Diagnostic Documentation
================================

Last update: 2021/01/28

This is the tropical cyclone (TC) diagnostics ("TC_diag") package.

Version & Contact info
----------------------

- Version/revision information: version 0 (2021/01/28)
- PIs: Daehyun Kim (Univ. of Washington, daehyun@uw.edu)
- Developers: Yumin Moon (Univ. of Washington, yum102@uw.edu)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
Unless you've distirbuted your script elsewhere, you don't need to change this.

Functionality
-------------

In this section you should summarize the stages of the calculations your 
diagnostic performs, and how they translate to the individual source code files 
provided in your submission. This will, e.g., let maintainers fixing a bug or 
people with questions about how your code works know where to look.

Required programming language and libraries
-------------------------------------------

In this section you should summarize the programming languages and third-party 
libraries used by your diagnostic. You also provide this information in the 
``settings.jsonc`` file, but here you can give helpful comments to human 
maintainers (eg, "We need at least version 1.5 of this library because we call
this function.")

Required model output variables
-------------------------------

In this section you should describe each variable in the input data your 
diagnostic uses. You also need to provide this in the ``settings.jsonc`` file, 
but here you should go into detail on the assumptions your diagnostic makes 
about the structure of the data.

References
----------

Here you should cite the journal articles providing the scientific basis for 
your diagnostic. To keep the documentation format used in version 2.0 of
the framework, we list references "manually" with the following command:

.. Note this syntax, which sets the "anchor" for the hyperlink: two periods, one
   space, one underscore, the reference tag, and a colon, then a blank line.

.. code-block:: restructuredtext

   .. _ref-Maloney: 

   1. E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate 
   and Weather Forecasting Models. *BAMS*, **100** (9), 1665–1686, 
   `doi:10.1175/BAMS-D-18-0042.1 <https://doi.org/10.1175/BAMS-D-18-0042.1>`__.

which produces

.. _ref-Maloney: 
   
1. E. D. Maloney et al. (2019): Process-Oriented Evaluation of Climate and 
Weather Forecasting Models. *BAMS*, **100** (9), 1665–1686, 
`doi:10.1175/BAMS-D-18-0042.1 <https://doi.org/10.1175/BAMS-D-18-0042.1>`__.

which can be cited in text as ``:ref:`a hyperlink <reference tag>```, which 
gives :ref:`a hyperlink <ref-Maloney>` to the location of the reference on the 
page. Because references are split between this section and the following "More 
about this diagnostic" section, unfortunately you'll have to number references 
manually.

We don't enforce any particular bibliographic style, but please provide a 
hyperlink to the article's DOI for ease of online access. Hyperlinks are written
as ```link text <URL>`__`` (text and url enclosed in backticks, followed by two 
underscores).

More about this diagnostic
--------------------------

In this section, you can go into more detail on the science behind your 
diagnostic, for example, by copying in relevant text articles you've written 
using th  It's especially helpful if you're able to teach users how to use 
your diagnostic's output, by showing how to interpret example plots.

Instead of doing that here, we provide more examples of RestructuredText
syntax that you can customize as needed.

As mentioned above, we recommend the online editor at `https://livesphinx.herokuapp.com/ 
<https://livesphinx.herokuapp.com/>`__, which gives immediate feedback and has
support for sphinx-specific commands.

Here's an 
`introduction <http://docutils.sourceforge.net/docs/user/rst/quickstart.html>`__ 
to the RestructuredText format, a 
`quick reference <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`__, 
and a `syntax comparison <http://hyperpolyglot.org/lightweight-markup>`__ to 
other text formats you may be familiar with.

Links to external sites
^^^^^^^^^^^^^^^^^^^^^^^

URLs written out in the text are linked automatically: https://ncar.ucar.edu/. 

To use custom text for the link, use the syntax 
```link text <https://www.noaa.gov/>`__`` (text and url enclosed in backticks, 
followed by two underscores). This produces `link text <https://www.noaa.gov/>`__.

More references and citations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's another reference:

.. code-block:: restructuredtext

   .. _ref-Charney: 

   2. Charney, Jule; Fjørtoft, Ragnar; von Neumann, John (1950). Numerical 
   Integration of the Barotropic Vorticity Equation. *Tellus* **2** (4) 237–254, 
   `doi:10.3402/tellusa.v2i4.8607 <https://doi.org/10.3402/tellusa.v2i4.8607>`__.

.. _ref-Charney: 

2. Charney, Jule; Fjørtoft, Ragnar; von Neumann, John (1950). Numerical 
Integration of the Barotropic Vorticity Equation. *Tellus* **2** (4) 237–254, 
`doi:10.3402/tellusa.v2i4.8607 <https://doi.org/10.3402/tellusa.v2i4.8607>`__.

Here's an example of citing these references:

.. code-block:: restructuredtext

   :ref:`Maloney et. al., 2019 <ref-Maloney>`, 
   :ref:`Charney, Fjørtoft and von Neumann, 1950 <ref-Charney>`

produces :ref:`Maloney et. al., 2019 <ref-Maloney>`, 
:ref:`Charney, Fjørtoft and von Neumann, 1950 <ref-Charney>`.

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

Use the following syntax for superscripts and subscripts in text:
``W m\ :sup:`-2`\ `` → W m\ :sup:`-2`\ ; ``CO\ :sub:`2`\ `` → CO\ :sub:`2`\ .
Note that spaces are needed before and after the forward slashes.

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
