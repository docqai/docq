<!-- ## Getting Started -->

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

<!-- USAGE EXAMPLES -->

## Usage

Some useful examples of how this project can be used:

- Install requirements

  ```sh
  poe install-dev
  ```

- Run tests
  
  - Unit tests

  ```sh
  poe test
  ``` 

  - Integration tests
  - Prepare env vars by supplying a pytest.env file required for the integration tests

    ```sh
    cp misc/pytest.env.template pytest.env
    ## Make edits on pytest.env with the correct values for the test environment then run the tests
    ```
  
  ```sh
  poe test-integration
  ```

- Run the project

  - Prepare env vars by supplying a Streamlit secrets file

    ```sh
    cp misc/secrets.toml.template .streamlit/secrets.toml
    ## Make edits on .streamlit/secrets.toml
    ## Customise other files in .streamlit/ directory to influence Streamlit behaviour
    ```

  - TIP: Make sure `.streamlit` directory is in the `.gitignore` file so it isn't checked in with secrets.

  - Run the application

    ```sh
    poe run
    ```

  and it will be available at http://localhost:8501

  - To change the port number

    ```sh
    poe run --port PORT
    ```

- Run doc site locally

  ```sh
  poe doc
  ```

- Generate doc site

  ```sh
  poe doc-html
  ```

- Build a docker image for tests

  ```sh
  poe docker-build --target test --build-tag 3.10-alpine --test true
  poe docker-run --target test
  ```

- Build a docker image to run the root files only without running any test

  - Build image

    ```sh
    poe docker-build
    ```

  - Set env vars

    ```sh
    cp misc/docker.env.template docker.env
    ## Make edits on docker.env
    ```

  - TIP: Make sure `docker.env` is in the `.gitignore` file so it isn't checked in with secrets. It's also safer if you only have the environment variable name for secrets and set the value in your shell with `export`.

  - Run container

    ```sh
    poe docker-run
    ```

- Release

  Switch to `main` branch locally and run

  ```sh
  ./trigger-release.sh
  ```

  which creates a new release tag which further creates a GitHub release and a container image published to GitHub registry, via GitHub Actions.

_For more examples, please refer to the [Documentation](https://docqai.github.io/docq/)_
