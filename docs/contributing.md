# How to Contribute

We'd love to accept testing scripts for add-on applications. There are
just a few small guidelines and conditions you need to follow.

## Contributor License Agreement

Contributions to this project must be accompanied by a Contributor License
Agreement. You (or your employer) retain the copyright to your contribution;
this simply gives us permission to use and redistribute your contributions as
part of the project. Head over to <https://cla.developers.google.com/> to see
your current agreements on file or to sign a new one.

You generally only need to submit a CLA once, so if you've already submitted one
(even if it was for a different project), you probably don't need to do it
again.

## Coordination with Cortex Engineering
Please reach out to cortex-support@google.com before submitting a new application. Submissions will be required, at minimum, to:
1. Provide instructions for deployment, and a description of your solution including:
-   References to websites, contacts, repositories for customers to install, download or purchase the solution
-   Dependencies on the Data Foundation (e.g., modules, tables, images)
2. Provide a `cloudbuild.yaml` file with default values to serve as an entry point for the Cortex Framework's automated testing pipelines.
3. Provide a contact for the engineering team to reach out in case a breaking change needs addressing. The Cortex engineering team will use the cloudbuild.yaml to make sure changes in major releases do not affect an add-on built by a partner or customer. It is the responsibility of the owners and authors of the applications to fix the code. Applications causing errors for more than two consecutive minor releases will be removed from this repository.

Not all applications will be accepted into this repository and our automated testing pipelines. Acceptance is subject to the discretion of the Google Engineering team.

## Code Reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

The project team will try to review all contributions and consider them for merging.
However, contributions will be reviewed pending on maintainer time and not all pull requests will be reviewed or incorporated.

## Community Guidelines

This project follows [Google's Open Source Community
Guidelines](https://opensource.google/conduct/).
