# Getting Started

There are two main [deployment scenarios](../overview/deployment-scenarios.md) as stated in [Overview](../overview/introduction.md).

To get you started, we show you one example for each scenario below.

## Pre-requisites

- Make sure to study the [environment variables template file](https://github.com/docqai/docq/blob/main/misc/docker.env.template) in the repo to collect all the values for required environment variables.
- Take a note on the default username and password for the _admin_ user created when running the application for the first time. Changing the password for this account will be the first thing you do after deploying this app.
  - username: `docq`
  - password: `Docq.AI`
- For Flexible Deployment, create a [Streamlit Community Cloud](https://streamlit.io/cloud) account.
- For Secure Deployment, create a [Microsoft Cloud / Azure](https://azure.microsoft.com/) account with a secure foundation.
- [Forking](https://github.com/docqai/docq/fork) the Docq repo at GitHub is highly recommended to have your own copy of code for your own deployment.


## Deployment Options

- [Streamlit: 5 Minutes and flexible](./deploy-to-streamlit.md)

- [Azure: 15 Minutes and decure](./deploy-to-azure.md)

- AWS: 15 Mintutes and Secure - on the roadmap

- GCP: 15 Mintutes and Secure - on the roadmap

## After Deployment

!!! warning
      Firstly, please change the default password for the _admin_ user as your first task after login.

Then use this installation as a blueprint for your production deployment, which may require more thorough planning and preparation. We are considering providing production ready Infra-as-Code (CDK for Terraform or Terraform HCL). Let us know if this would be valuable.

Please refer to [Installation](./installation.md) and [Configuration](./configuration.md) for details.
