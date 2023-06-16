# Infra-as-Code setup for Docq.AI hosting

## Azure

### GUI Wizrd

https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq%2Finfra%2Fazure-deploy%2Finfra%2Fazure%2Fappservice3.json

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq-qs%2Fmain%2Fdeploy%2Fazure%2Farm%2Fappservice.json) - App Service
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq-qs%2Fmain%2Fdeploy%2Fazure%2Farm%2Fcontainerinstances.json) - Container Instances

### CLI

- Create resource group CLI - `az group create --name docq-rg-westeurope --location westeurope`
- Deploy template CLI - `az deployment group create --resource-group docq-rg-westeurope --name docq1 --template-file appservice.json`
- Delete resources in resource group - `az group delete --name docq-rg-westeurope`
- Purge CognitionServices (you'll get an error next time otherwise)
  - list the names of soft deleted resources `az cognitiveservices account list-deleted --query "[].name"`
  - purge `az cognitiveservices account purge --name <name of deleted resource from above list command> --location westeurope --resource-group docq-rg-westeurope`

See the `models` tab in Azure AI Studio <https://oai.azure.com/portal> for models available to the specific Azure account along with version numbers"

See API ref for detials on avail options <https://learn.microsoft.com/en-us/rest/api/cognitiveservices/azureopenaistable/deployments/create>

@see <https://learn.microsoft.com/en-gb/azure/cognitive-services/openai/concepts/models>




## AWS