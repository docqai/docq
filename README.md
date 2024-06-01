<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![AGPLv3 License][license-shield]][license-url]
[![Slack][slack-shield]][slack-url]
[![X (formerly Twitter) Follow][twitter-shield]][twitter-url]

# Your private ChatGPT alternative

**Q&A with business documents securely. Depend less on other teams for answers.**

![Docq overview in a single diagram](https://docqai.github.io/docq/assets/docq-diag-apr2024.png)

<!-- ABOUT THE PROJECT -->

## About The Project

Docq offers **private** and **secure** GenAI that unlocks knowledge from your organisation's documents, with minimal onboarding and operational effort.

Design tenets:

- **Data stays within your boundary**:
bring ML models to the data. Cloud-vendor-hosted & self-hosted LLMs within the same cloud account to address data security and privacy concerns.
- **Self-hosting**:
with your organisation's choice of cloud vendor. Minimal onboarding and operational effort. Can support air-gap use cases with local models.
- **Multi-model**:
ability to utilise a variety of models and ability adopt new models quickly.
- **Multi-modal**:
supports text today. Image, video, and audio formats are on the roadmap.
- **Extensible**:
Abstractions to easily add custom data sources. Plugin system for extending application, from UI to database.

We offer Docq as a **turnkey** solution to lower the barrier for your organisation to adopt the latest AI innovation safely.

- Open-source (AGPLv3) to address your organisation's security and compliance needs.
- Commercial license and support available (via Docq.AI based in London, UK).
- Re-licensing option also available.

## Vision

Be the goto OSS GenAI application stack for the privacy and security conscious.

## Demo

A [demo app](https://docq-ai.streamlit.app/) is hosted by [Streamlit Community Cloud](https://streamlit.io/cloud), subject to frequent data refresh and feature update.

Credentials for _admin_ user:

- username: `docq`
- password: `Docq.AI`

There are also recordings (Loom) to demonstrate Docq's major features:

- [Ask your documents vs shared spaces](https://www.loom.com/share/21bb34d1bcb54f8ebf47c68f347d484c)
- [Multi-user access](https://www.loom.com/share/599aa123ddce4a3d916ee8bdcd61095f)

## Deploy Your Own Instance

### Deploy to Azure in 15mins

Click and follow the Azure wizard [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq%2Fmain%2Finfra%2Fazure%2Farm%2Fappservice.json)

For more details see section [Deploy to Azure: 15 Minutes and Secure](./docs/user-guide/getting-started.md)

### Deploy to AWS in 15mins

<img src="./docs/assets/vendor-logos/aws-logo.svg" width="50">&nbsp;&nbsp;On the roadmap.

### Deploy to GCP in 15mins

<img src="./docs/assets/vendor-logos/gcp-logo.svg" width="40">&nbsp;&nbsp;On the roadmap.

## Documentation

[Documentation](https://docqai.github.io/docq/) site is hosted by [GitHub Pages](https://pages.github.com/).

- [Overview](https://docqai.github.io/docq/overview/introduction/)
- [User Guide](https://docqai.github.io/docq/user-guide/getting-started/)
- [Developer Guide](https://docqai.github.io/docq/developer-guide/getting-started/)

<!-- ROADMAP -->

## Roadmap

We aim to support the following features in the future:

- More data ingestion options such as SaaS data connectors and network storage options
- A plugin platform and ecosystem
- Model fine-tuning as an option for self-hosted, open-source LLMs

We also have plan to offer enterprise add-ons such as SSO support and enhanced audit.

Stay tuned!

<!-- CONTACT -->

## Contact

Docq.AI - [@docqai](https://github.com/docqai) - support@docq.ai

Project Link: [https://github.com/docqai/docq/](https://github.com/docqai/docq/)

<!-- LICENSE -->

## Licenses

The code in the repo is distributed under the licenses below. If a file has a specific license and copyright notice displayed then that wins.

- AGPLv3. See [`LICENSE`](./LICENSE.AGPL3) and [`NOTICE`](./NOTICE.AGPL3)  for more information.
- Commercial licenses available via [Docq.AI](https://docq.ai)
- Copyright (C) 2023-2024 FABR Ltd t/a [Docq.AI](https://docq.ai). 

Made :heart: London.



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/docqai/docq.svg?style=flat
[contributors-url]: https://github.com/docqai/docq/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/docqai/docq.svg?style=flat
[forks-url]: https://github.com/docqai/docq/network/members
[stars-shield]: https://img.shields.io/github/stars/docqai/docq.svg?style=flat
[stars-url]: https://github.com/docqai/docq/stargazers
[issues-shield]: https://img.shields.io/github/issues/docqai/docq.svg?style=flat
[issues-url]: https://github.com/docqai/docq/issues
[license-shield]: https://img.shields.io/badge/license-AGPL_3.0-green?style=flat
[license-url]: https://github.com/docqai/docq/blob/main/LICENSE.AGPL3
[slack-shield]: https://img.shields.io/badge/Join-orange?style=flat&logo=slack&label=Slack
[slack-url]: https://join.slack.com/t/docqai/shared_invite/zt-27p17lu6v-6KLJxSmt61vfNqCavSE73A
[twitter-shield]: https://img.shields.io/twitter/follow/docqai?logo=x&style=flat
[twitter-url]: https://twitter.com/docqai
