# LLM Configuration

Currently all supported LLM services are configured when Docq is deployed/started via environment variables.

These are documented in [/misc/docker.env.template](https://github.com/docqai/docq/blob/main/misc/docker.env.template).

Find a little bit more information on how to get these credentials from each respective service.

???+ warning
      In production, set secrets values in the shell. e.g. `set SOME_API_KEY=<your secret api key value>`.

      A tool like Infisical helps manage this process while keeping your secret values safe.

## OpenAI

- Sign up for an OpenAI account. Generate an API key

## Azure OpenAI

Assumes you have an Azure subscription

- If using the all in one ARM template to deploy Docq these env vars are set securely for you.
- If using and existing deployment or click-ops deployment. Login to your Azure console. Navigate to your Azure OpenAI deployment to find the required values.

## Vertex AI (PaLm2 and Gemini Pro)

Assumes you have a GCP account. 

- Login to your GCP console.
- You can either select an existing GCP project or create a new one.
- Navigate to 'IAM and Admin' > 'Service Accounts'. Create a new service account. You may also use an existing one.
- Assign the SA account the 'Vertex AI User' role.
- switch to the 'Keys' tab > 'Add key' > 'Create new key'. This will generate a credentials.json file. Copy the entire content of this file and set the env var.
