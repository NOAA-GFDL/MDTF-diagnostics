# Security Policy

Security Policy for the MDTF Diagnostics Package
Draft v1 - October 8, 2020

The adoption of novel software contributions from the community inherently poses a risk to internal NOAA computing infrastructure. Whether intentional or unintentional, 
these risks include threats to data integrity as well as the introduction of malicious software. Since the mandate of the MDTF Diagnostics effort is to solicit weather 
and climate model analysis code from the community, we adopt the following security measures in order to mitigate these risks:

1. All software must be open source and fully transparent. No closed source code or dependencies will be permitted in the package.  The software should also use an open source license compatible with the LGPLv3 licence associated with the MDTF Diagnostics Framework.
2. As much testing as possible will take place outside of NOAA and DOC systems. This includes leveraging external testing platforms (e.g., LGTM) and our project partners at NCAR and UCLA.  Testing source code and procedures should also be open and be compatible with the project’s open source license.
3. Prior to running any submitted code on NOAA systems, at least two reviewers must certify to the best of their knowledge that the code is a reasonable contribution to the project and contains no obvious security issues that could potentially harm NOAA systems or data. At least one of these reviews must be conducted by a NOAA Federal employee.
4. Any security issues must be immediately reported to the local NOAA IT security officer.

## Supported Versions

| Version    | Supported          |
| ---------- | ------------------ |
| 3.0        | :white_check_mark: |
| 3.0 beta 5 | :white_check_mark: |
| 3.0 beta 4 | :white_check_mark: |
| 3.0 beta 3 | :white_check_mark: |
| 3.0 beta 2 | :x:                |
| 3.0 beta 1 | :x:                |
| 2.0        | :x:                |

## Reporting a Vulnerability

If you uncover a vulnerability in this software, please [open an issue](https://github.com/NOAA-GFDL/MDTF-diagnostics/issues) for this repository. If you have a remedy, a [pull request](https://github.com/NOAA-GFDL/MDTF-diagnostics/pulls) is welcome.

NOAA-GFDL IT Security: [oar.gfdl.itso@noaa.gov](mailto:oar.gfdl.itso@noaa.gov)
