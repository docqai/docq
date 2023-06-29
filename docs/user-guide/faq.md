# Frequently Asked Questions

## Q: Does Docq use OpenAI?

No, the deployments to Azure, AWS, and GCP do _**not**_ use the OpenAI model hosting service. I currently uses the serverless ML Model hosting offered the respective could providers.

On Azure Docq uses a Azure hosted OpenAI service. Which is a dedicated serverless instance for you. It comes with a different Data Processing Agreement (DPA) and doesn't connect with system run by the company OpenAI.

Please see the Microsoft page [Data, privacy, and security for Azure OpenAI Service](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy?context=%2Fazure%2Fcognitive-services%2Fopenai%2Fcontext%2Fcontext).

In the future we will offer options for self-hosted models.

## Q: Does the Large Langugage Model (LLM) service store/remember my private data?

No, a LLM does not store or remember your data. Docq indexes documents you provide and uses these to provide the LLM with context related you questions.

In the future when we offer fine-tuning a model with your data this will be an option you explicitly opt into.

## Q: Where is Docq hosted?

Docq is entirely hosted within your cloud account. All data and communication remains within the network boundary (VPC) that you control. The exception are any data sources you connect that are inherently external or if the application is published for access via the public Internet.
