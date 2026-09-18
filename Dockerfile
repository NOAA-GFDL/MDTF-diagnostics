# Stage 1: Pull micromamba binary from official image
FROM mambaorg/micromamba:1.5.8 AS micromamba_bin

# Stage 2: Build main container on Rocky Linux 9
FROM rockylinux:9-minimal AS base

# Copy micromamba binary and setup user/paths
COPY --from=micromamba_bin /bin/micromamba /usr/local/bin/micromamba

USER root
ARG GIT_COMMIT_HASH=unknown


# Container Metadata
LABEL maintainer="mdtf-framework-team"
LABEL org.opencontainers.image.source=https://github.com/aradhakrishnanGFDL/MDTF-diagnostics/
LABEL org.opencontainers.image.description="This is a docker image for the MDTF-diagnostics package"
LABEL version="v3p"
LABEL org.opencontainers.image.revision=${GIT_COMMIT_HASH}
ENV APP_VERSION=${GIT_COMMIT_HASH}

RUN echo "Building image with commit: ${GIT_COMMIT_HASH}"

# Install core utilities via Rocky's microdnf
RUN microdnf -y update && \
    microdnf -y install \
      vim \
      git \
      tar \
      gzip \
      libnsl \
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
COPY Dockerfile ${CODE_ROOT}/Dockerfile.state

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


# Initialize shell hooks so 'micromamba activate' works natively

# 1. Create a dedicated hook file with NO interactive PS1 check
RUN mkdir -p /opt/conda/etc && \
    echo 'eval "$(micromamba shell hook --shell bash)"' > /opt/conda/etc/bash_init.sh

# 2. Force subshells to load the pure hook script + expose target environment paths
ENV BASH_ENV=/opt/conda/etc/bash_init.sh \
    PATH=/opt/conda/envs/_MDTF_NCL_base/bin:$PATH \
    NCARG_ROOT=/opt/conda/envs/_MDTF_NCL_base \
    LD_LIBRARY_PATH=/opt/conda/envs/_MDTF_NCL_base/lib:$LD_LIBRARY_PATH

# Create a dummy conda that turns 'conda activate' into a no-op
RUN echo '#!/bin/bash' > /usr/local/bin/conda && \
    echo 'if [ "$1" = "activate" ]; then exit 0; fi' >> /usr/local/bin/conda && \
    echo 'exec /usr/local/bin/micromamba "$@"' >> /usr/local/bin/conda && \
    chmod +x /usr/local/bin/conda

# Set conda execution path, root prefix, and prioritize target binaries in PATH
ENV CONDA_EXE=/usr/local/bin/conda \
    MAMBA_ROOT_PREFIX=/opt/conda \
    PATH="/opt/conda/envs/_MDTF_base/bin:/opt/conda/bin:/opt/conda/condabin:/usr/local/bin:${CODE_ROOT}:${PATH}"

# -------------------------------------------------------------------
# Install core framework base environment

RUN micromamba create -p /opt/conda/envs/_MDTF_base -f ${CODE_ROOT}/src/conda/env_base.yml -y && \
    /opt/conda/envs/_MDTF_base/bin/pip install "setuptools<81" && \
    micromamba clean --all --yes

FROM base AS python

RUN micromamba create -p /opt/conda/envs/_MDTF_python3_base -f ${CODE_ROOT}/src/conda/env_python3_base.yml -y && \
    micromamba clean --all --yes

FROM base AS ncl

RUN micromamba create -p /opt/conda/envs/_MDTF_NCL_base -f ${CODE_ROOT}/src/conda/env_NCL_base.yml -y && \
    micromamba clean --all --yes

FROM python AS full

RUN micromamba create -p /opt/conda/envs/_MDTF_NCL_base -f ${CODE_ROOT}/src/conda/env_NCL_base.yml -y && \
# ==============================================================================
# 1. FIX LIBNSL: Symlink libnsl directly into system and env library paths
# ==============================================================================
RUN dnf install -y libnsl && dnf clean all && \
    mkdir -p /opt/conda/envs/_MDTF_NCL_base/lib && \
    ln -sf $(find /usr/lib64 /opt/conda -name "libnsl.so*" | head -n 1) /opt/conda/envs/_MDTF_NCL_base/lib/libnsl.so.1
# Direct default PATH to the target NCL environment binaries
ENV PATH=/opt/conda/envs/_MDTF_NCL_base/bin:/usr/local/bin:$PATH
    micromamba clean --all --yes
# 2. Global environment variables (BASH_ENV + _MDTF_NCL_base environment paths)
ENV BASH_ENV=/opt/conda/etc/bash_init.sh \
    PATH=/opt/conda/envs/_MDTF_NCL_base/bin:/opt/conda/bin:$PATH \
    NCARG_ROOT=/opt/conda/envs/_MDTF_NCL_base \
    LD_LIBRARY_PATH=/opt/conda/envs/_MDTF_NCL_base/lib:$LD_LIBRARY_PATH
ENV PATH="/opt/conda/envs/_MDTF_base/bin:/opt/conda/bin:/opt/conda/condabin:/usr/local/bin:${CODE_ROOT}:${PATH}"
ENV PATH="${PATH}:/proj/MDTF-diagnostics/"
