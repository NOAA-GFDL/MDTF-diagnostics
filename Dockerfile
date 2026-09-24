# Stage 1: Explicitly pull micromamba binary from Docker Hub
FROM docker.io/mambaorg/micromamba:1.5.8 AS micromamba_bin

# Stage 2: Minimal Rocky Linux base image
FROM docker.io/rockylinux/rockylinux:9-minimal AS base

# Copy micromamba binary and setup user/paths
COPY --from=micromamba_bin /bin/micromamba /usr/local/bin/micromamba

USER root

# Container Metadata
LABEL maintainer="mdtf-framework-team"
LABEL org.opencontainers.image.source=https://github.com/aradhakrishnanGFDL/MDTF-diagnostics/
LABEL org.opencontainers.image.description="This is a docker image for the MDTF-diagnostics package"
LABEL version="v4p3"

# Install core utilities via Rocky's microdnf
RUN microdnf -y update && \
    microdnf -y install \
      vim \
      git \
      tar \
      gzip \
      bzip2 \
      ca-certificates \
      shadow-utils \
    && microdnf clean all

# Copy the MDTF-diagnostics package contents from local machine to image
ENV CODE_ROOT=/proj/MDTF-diagnostics

COPY src ${CODE_ROOT}/src
COPY data ${CODE_ROOT}/data
COPY diagnostics ${CODE_ROOT}/diagnostics
COPY mdtf_framework.py ${CODE_ROOT}
COPY shared ${CODE_ROOT}/shared
COPY tests ${CODE_ROOT}/tests

# Configure Conda / Micromamba environment paths
ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV CONDA_ROOT=/opt/conda
ENV CONDA_ENV_DIR=/opt/conda/envs

# -------------------------------------------------------------------
# Smart Micromamba -> Conda Compatibility Wrapper for MDTF
# -------------------------------------------------------------------
RUN mkdir -p /opt/conda/bin /opt/conda/condabin /usr/local/bin

# Create wrapper script that intercepts unsupported flags like 'conda info --base'
# Write the wrapper script using echo
RUN echo $'#!/bin/bash\nif [ "$1" = "info" ] && [ "$2" = "--base" ]; then\n    echo "${MAMBA_ROOT_PREFIX:-/opt/conda}"\n    exit 0\nfi\nexec /usr/local/bin/micromamba "$@"' > /usr/local/bin/conda

# Make executable and symlink into standard Conda paths
RUN chmod +x /usr/local/bin/conda && \
    ln -sf /usr/local/bin/conda /opt/conda/bin/conda && \
    ln -sf /usr/local/bin/conda /opt/conda/condabin/conda

# Configure environment variables expected by MDTF processes
ENV CONDA_EXE=/usr/local/bin/conda \
    MAMBA_ROOT_PREFIX=/opt/conda \

    PATH="/opt/conda/envs/_MDTF_base/bin:/opt/conda/bin:/opt/conda/condabin:/usr/local/bin:${CODE_ROOT}:${PATH}"
# -------------------------------------------------------------------
# Install core framework base environment

RUN micromamba create -p /opt/conda/envs/_MDTF_base -f ${CODE_ROOT}/src/conda/env_base.yml -y && \
    /opt/conda/envs/_MDTF_base/bin/pip install "setuptools<81" && \
    micromamba clean --all --yes

# Initialize shell hooks so 'micromamba activate' works natively
RUN micromamba shell init --shell bash --root-prefix /opt/conda
ENV BASH_ENV=/root/.bashrc

FROM base AS python

RUN micromamba create -p /opt/conda/envs/_MDTF_python3_base -f ${CODE_ROOT}/src/conda/env_python3_base.yml -y && \
    micromamba clean --all --yes

FROM base AS ncl

RUN micromamba create -p /opt/conda/envs/_MDTF_NCL_base -f ${CODE_ROOT}/src/conda/env_NCL_base.yml -y && \
    micromamba clean --all --yes

FROM python AS full

RUN micromamba create -p /opt/conda/envs/_MDTF_NCL_base -f ${CODE_ROOT}/src/conda/env_NCL_base.yml -y && \
    micromamba create -p /opt/conda/envs/_MDTF_synthetic_data -f ${CODE_ROOT}/src/conda/_env_synthetic_data.yml && \ 
    micromamba clean --all --yes
