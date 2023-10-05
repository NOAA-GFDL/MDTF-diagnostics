# Base OS
FROM ubuntu:latest
FROM mambaorg/micromamba:latest as micromamba

#micromamba set up

USER root

RUN micromamba info

##
# Container Metadata
LABEL maintainer="mdtf-leads-AR"
LABEL version="test-01"
LABEL description="This is a docker image for the MDTF-diagnostics package"
# Copy the MDTF-diagnostics package contents from local machine to image 
ENV CODE_ROOT=/proj/MDTF-diagnostics
COPY src ${CODE_ROOT}/src                          
COPY data ${CODE_ROOT}/data
#COPY diagnostics ${CODE_ROOT}/diagnostics
COPY mdtf_framework.py ${CODE_ROOT}
COPY shared ${CODE_ROOT}/shared
COPY sites ${CODE_ROOT}/sites
COPY tests ${CODE_ROOT}/tests
# Install conda environments
ENV CONDA_ROOT=/opt/conda/
ENV CONDA_ENV_DIR=/opt/conda/envs

#USER mambauser
RUN micromamba create -f /proj/MDTF-diagnostics/src/conda/env_base.yml
RUN micromamba create -f /proj/MDTF-diagnostics/src/conda/env_NCL_base.yml

ENV PATH="${PATH}:/proj/MDTF-diagnostics/"
#RUN eval "$(micromamba shell hook --shell bash )";micromamba activate _MDTF_base
ENV PATH=$PATH:"/opt/conda/envs/_MDTF_NCL_base/bin/"

