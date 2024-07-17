FROM mambaorg/micromamba:1.5.8 as micromamba
  
USER root
# Container Metadata
LABEL maintainer="mdtf-framework-team"
LABEL version="071724"
LABEL description="This is a docker image for the MDTF-diagnostics package"

# Copy the MDTF-diagnostics package contents from local machine to image (or from git)
ENV CODE_ROOT=/proj/MDTF-diagnostics

COPY src ${CODE_ROOT}/src

COPY data ${CODE_ROOT}/data
COPY diagnostics ${CODE_ROOT}/diagnostics
COPY mdtf_framework.py ${CODE_ROOT}
COPY shared ${CODE_ROOT}/shared
COPY tests ${CODE_ROOT}/tests

# Install conda environments
ENV CONDA_ROOT=/opt/conda/
ENV CONDA_ENV_DIR=/opt/conda/envs
RUN apt-get -y update
#dev purpose only - install vim
RUN apt-get -y install vim

RUN micromamba create -f /proj/MDTF-diagnostics/src/conda/env_base.yml && \
    micromamba create -f /proj/MDTF-diagnostics/src/conda/env_python3_base.yml && \
    micromamba create -f /proj/MDTF-diagnostics/src/conda/_env_synthetic_data.yml && \
    micromamba clean --all --yes && \
    micromamba clean --force-pkgs-dirs --yes

ENV PATH="${PATH}:/proj/MDTF-diagnostics/"
