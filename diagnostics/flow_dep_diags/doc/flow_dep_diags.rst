.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Flow-Dependent, Cross-Timescale Model Diagnostics Documentation
================================

Last update: 01/02/2021

The flow-dependent model diagnostics compares daily atmospheric circulation pattern, or weather types, characteristics in reanalyses and models to analyze misrepresented physical processes related to spatiotemporal systematic errors in those models. Relationships between these biases and climate teleconnections (e.g., SST patterns, ENSO, MJO, etc.) can be explored in different models.

.. Underline with '-'s to make a second-level heading.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

.. Here you should describe who contributed to the diagnostic, and who should be
.. contacted for further information:

- Version/revision information: version 1 (01/02/2021)

.. - PI (name, affiliation, email)

- Developer/point of contact: Ángel G. Muñoz (agmunoz@iri.columbia.edu) and Andrew W. Robertson (awr@iri.columbia.edu)

- Other contributors: Drew Resnick (drewr@iri.columbia.edu)

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

.. Unless you've distirbuted your script elsewhere, you don't need to change this.

.. Functionality
.. -------------

.. In this section you should summarize the stages of the calculations your 
.. diagnostic performs, and how they translate to the individual source code files 
.. provided in your submission. This will, e.g., let maintainers fixing a bug or 
.. people with questions about how your code works know where to look.

Required programming language and libraries
-------------------------------------------

.. In this section you should summarize the programming languages and third-party 
.. libraries used by your diagnostic. You also provide this information in the 
.. ``settings.jsonc`` file, but here you can give helpful comments to human 
.. maintainers (eg, "We need at least version 1.5 of this library because we call
.. this function.")

Programming language: Python3

Python Libraries used: Xarray, numpy, pandas, sklearn, cartopy, matplotlib, PyWR

Required model output variables
-------------------------------

.. In this section you should describe each variable in the input data your diagnostic uses. Here you should go into detail on the assumptions your diagnostic makes about the structure of the data.

Geopotential height anomalies at 500 hPa

Rainfall

2-m temperature

References
----------

.. Here you should cite the journal articles providing the scientific basis for your diagnostic. To keep the documentation format used in version 2.0 of the framework, we list references "manually" with the following command:

.. Note this syntax, which sets the "anchor" for the hyperlink: two periods, one
   space, one underscore, the reference tag, and a colon, then a blank line.


.. _ref-Muñoz: 
   
Muñoz, Á. G., Yang, X., Vecchi, G. A., Robertson, A. W., & Cooke, W. F. (2017): PA Weather-Type-Based Cross-Time-Scale Diagnostic Framework for Coupled Circulation Models. *Journal of Climate*, **30** (22), 8951–8972, 
`doi:10.1175/JCLI-D-17-0115.1 <https://doi.org/10.1175/JCLI-D-17-0115.1>`__.

.. which can be cited in text as ``:ref:`a hyperlink <reference tag>```, which 
.. gives :ref:`a hyperlink <ref-Maloney>` to the location of the reference on the 
.. page. Because references are split between this section and the following "More 
.. about this diagnostic" section, unfortunately you'll have to number references 
.. manually.

.. We don't enforce any particular bibliographic style, but please provide a 
.. hyperlink to the article's DOI for ease of online access. Hyperlinks are written
.. as ```link text <URL>`__`` (text and url enclosed in backticks, followed by two 
.. underscores).

.. More about this diagnostic
.. --------------------------

.. In this section, you can go into more detail on the science behind your 
.. diagnostic, for example, by copying in relevant text articles you've written 
.. using th  It's especially helpful if you're able to teach users how to use 
.. your diagnostic's output, by showing how to interpret example plots.

.. Instead of doing that here, we provide more examples of RestructuredText
.. syntax that you can customize as needed.

.. As mentioned above, we recommend the online editor at `https://livesphinx.herokuapp.com/ 
.. <https://livesphinx.herokuapp.com/>`__, which gives immediate feedback and has
.. support for sphinx-specific commands.

.. Here's an 
.. `introduction <http://docutils.sourceforge.net/docs/user/rst/quickstart.html>`__ 
.. to the RestructuredText format, a 
.. `quick reference <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`__, 
.. and a `syntax comparison <http://hyperpolyglot.org/lightweight-markup>`__ to 
.. other text formats you may be familiar with.

.. Links to external sites
.. ^^^^^^^^^^^^^^^^^^^^^^^

.. URLs written out in the text are linked automatically: https://ncar.ucar.edu/. 

.. To use custom text for the link, use the syntax 
.. ```link text <https://www.noaa.gov/>`__`` (text and url enclosed in backticks, 
.. followed by two underscores). This produces `link text <https://www.noaa.gov/>`__.

.. More references and citations
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

