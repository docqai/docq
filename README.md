<div id="top"></div>

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

<div align="center">

  <h1 align="center"> Docq - Private & Secure AI Knowledge Insight</h1>
  <h3 align="center">
    A turnkey product to utilise your organisation's documents for AI-induced productivity boost.
  </h3>

![Docq Logo](docs/img/Docq_design_key_ingredients.png)

  <p align="center">
    <a href="https://docqai.github.io/docq/readme.html"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/docqai/docq/issues">Report Bug</a>
    ·
    <a href="https://github.com/docqai/docq/issues">Request Feature</a>

  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

Docq offers private and secure AI to utilise your organisation's documents for knowledge insight with minimal onboarding and operational effort.

- Self-hosting with your organisation's choice of cloud vendor.
- Plug-n-Play with minimal onboarding and operational effort.
- Multi-modal document format support including text and image.

We offer Docq as a **turnkey** solution to maximise ROI for your organisation to adopt the latest AI innovations.

- Open-source (AGPLv3) to address your organisation's security and compliance needs.
- Commercial support available via a UK-based entity.
- Re-licensing option also available.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

To run this project locally, you will need to install the prerequisites and follow the installation section.

### Prerequisites

This Project depends on the following projects.

- Poetry

  ```sh
  pip install --user --upgrade poetry
  ```

- Poe the Poet
  ```sh
  pip install --user --upgrade poethepoet
  ```

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/docqai/docq
   cd docq
   ```
2. Install Poe the Poet and Poetry
   ```sh
   pip install --user --upgrade poethepoet poetry
   ```
3. Install requirements for development
   ```sh
   poe install-dev
   ```
4. Run tests
   ```sh
   poe test
   ```

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

Some useful examples of how this project can be used:

- Install requirements

  ```sh
  poe install-dev
  ```

- Run tests

  ```sh
  poe test
  ```

- Run the project

  ```sh
  poe run
  ```

- Generate API documentation

  ```sh
  poe doc
  ```

- Build a docker image for tests

  ```sh
  poe docker-build --target test --build-tag 3.10-alpine
  docker run -ti --rm docq:test-3.10-alpine
  ```

- Build a docker image to run the root files only without running any test
  ```sh
  poe docker-build --target prod --build-tag 3.10-alpine --no-test
  docker run -ti --rm docq:prod-3.10-alpine
  ```

_For more examples, please refer to the [Documentation](https://docqai.github.io/docq/readme.html)_

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [x] Add tests
- [x] Add code coverage
- [x] Improve documentation
- [ ] Include more tests

See the [open issues](https://github.com/docqai/docq/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Docq.AI - [@docqai](https://github.com/docqai) - support@docq.ai

Project Link: [https://github.com/docqai/docq/](https://github.com/docqai/docq/)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

The project would not have been possible without the following libraries:

- @jerryjliu [Llama Index](https://github.com/jerryjliu/llama_index)
- [Streamlit](https://streamlit.io/) and many open-source Streamlit components as well as its [Community Cloud](https://streamlit.io/cloud)

This project was created using cookiecutter and NullHack's python-project-template:

- @NullHack [python-project-template](https://github.com/nullhack/python-project-template/)

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LICENSE -->

## License

Distributed under the AGPLv3 License. See [`LICENSE`](https://github.com/docqai/docq/blob/main/LICENSE) for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/docqai/docq.svg?style=for-the-badge
[contributors-url]: https://github.com/docqai/docq/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/docqai/docq.svg?style=for-the-badge
[forks-url]: https://github.com/docqai/docq/network/members
[stars-shield]: https://img.shields.io/github/stars/docqai/docq.svg?style=for-the-badge
[stars-url]: https://github.com/docqai/docq/stargazers
[issues-shield]: https://img.shields.io/github/issues/docqai/docq.svg?style=for-the-badge
[issues-url]: https://github.com/docqai/docq/issues
[license-shield]: https://img.shields.io/badge/license-AGPL_3.0-green?style=for-the-badge
[license-url]: https://github.com/docqai/docq/blob/main/LICENSE
