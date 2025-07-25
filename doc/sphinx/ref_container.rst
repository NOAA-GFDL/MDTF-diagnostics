.. role:: code-rst(code)
   :language: reStructuredText
.. _ref-container:

Container Reference
===================

This section provides basic directions for downloading,
installing, and running the example_multicase POD in the
Model Diagnostics Task Force (MDTF) container.

Getting the Container
---------------------
The container assumes that the MDTF-diagnostics GitHub repo is located on your local machine.
If you have not already, please clone the repo to your local machine with:

   .. code-block:: bash

      git clone https://github.com/NOAA-GFDL/MDTF-diagnostics.git

The container can then be pulled from the GitHub
container registry with the command:

   .. code-block:: bash

      docker pull ghcr.io/noaa-gfdl/mdtf-diagnostics:container

or with the equivalent command in your container software.
If you do not have a container software, Docker can be downloaded from `here <https://docs.docker.com/desktop/>`_.

Launching the Container
-----------------------

The container itself can be launched with Docker using:

   .. code-block:: bash

      docker run -it -v {DIAG_DIR}:/proj/MDTF-diagnostics/diagnostics/ -v {WKDIR}:/proj/wkdir mdtf

wherein:
   * :code-rst:`{DIAG_DIR}` is the path to the diagnostics directory on your local machine.
     This volume is not required, but heavily recommended.
   * :code-rst:`{WKDIR}` is where you would like to store the output on your local machine.
     This allows the output HTML to be reachable without having to open a port to the container.

These happen to be the only required volumes. Further volumes may need to be mounted including volumes such as data storage.

Generating Synthetic Data
-------------------------

Now that we are in the container, we can create some data to run the POD with.
The MDTF has a synthetic data generator for just this case. First,`cd` into the MDTF-diagnostics directory:

   .. code-block:: bash

      cd /proj/MDTF-diagnostics/

We generate our synthetic data by running:

   .. code-block:: bash

      micromamba activate _MDTF_synthetic_data
      pip install mdtf-test-data
      mkdir mdtf_test_data && cd mdtf_test_data
      mdtf_synthetic.py -c CMIP --startyear 1980 --nyears 5 --freq day
      mdtf_synthetic.py -c CMIP --startyear 1985 --nyears 5 --freq day

Now would be a good time to generate a catalog for the synthetic data, but, in the sake
of testing, we provide a catalog for the files needed to run the example POD.

Running the POD
---------------
The POD can now be ran using:

   .. code-block:: bash

      micromamba activate _MDTF_base
      mdtf_framework.py -f /proj/MDTF-diagnostics/diagnostics/example_multicase/container_config_demo.jsonc

The results can be found in :code-rst:`/proj/wkdir/`

Building the Container
----------------------

If you would like, you can build the container using the Dockerfile found in the GitHub repo.
If using podman (as required internally at the GFDL),
please build with the command:

   .. code-block:: bash

      podman build . --format docker -t mdtf

:code-rst:`--format docker` is essential to have your copy commands work and
have the expected permissions in your container.
