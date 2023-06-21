# Infra-as-Code setup for Docq.AI hosting

## Azure ARM Templates

These docs are mainly for contributing and developing the various deployment methods available in the `/infra` folder. We recommend users start with installation instruction layed out in the user guide in the main docs site. But feel free if you want to get your hands dirty.

The ARM template in `/infra/azure/arm` powers the whizard based one-click deploy method described in the main docs.

### Deploy and destroy scripts

There two scripts combine several azure CLI commands to for convinience.

Running `./deploy.sh` is the easiest way to test when interating on the template.

- `./deploy.sh <NAME> <LOCATION> <RESOURCE_GROUP>` - args are optional. creates a resource group and deploys the ARM template based on several defaults. Inspect the script to discover the defaults and available parameters. Params can be overridden by passing argument values in order
- `./destroy.sh <NAME> <LOCATION> <RESOURCE_GROUP>` - args are optional. Destroys the resource group and all resources within. Handles purging all Congnitive Services in the resource group that are deleted.

### Useful CLI commands

If using the scripts above you shouldn't need these but occasionally you they might help when troubleshooting.

- Create resource group CLI - `az group create --name docq-rg-westeurope --location westeurope`
- Deploy template CLI - `az deployment group create --resource-group docq-rg-westeurope --name docq1 --template-file appservice.json`
- Delete resources in resource group - `az group delete --name docq-rg-westeurope`
- Purge CognitionServices (you'll get an error next time otherwise)
  - list the names of soft deleted resources `az cognitiveservices account list-deleted --query "[].name"`
  - purge `az cognitiveservices account purge --name <name of deleted resource from above list command> --location westeurope --resource-group docq-rg-westeurope`

### Useful references

See the `models` tab in Azure AI Studio <https://oai.azure.com/portal> for models available to the specific Azure account along with version numbers"

See API ref for detials on avail options <https://learn.microsoft.com/en-us/rest/api/cognitiveservices/azureopenaistable/deployments/create>

Explanation about models <https://learn.microsoft.com/en-gb/azure/cognitive-services/openai/concepts/models>

### Testing the template

- Run `./deploy.sh` to test the template deploys all resources sucessfully.
- Navigate to the app URL for this instance. Verify the app is working as expect.
- Test template deployment method aka one-click deploy. This is important as some times what works when deploying from the CLI doesn't work in template deployment.
  - push the template change to your branch (origin) such that it's publicly available.
  - Copy the 'raw' URL for the template file: Navigate to the file on Github.com. Click on the 'raw' button on the top right area.
  - URL encode the github raw URL.
  - Trigger Azure template deployment by navigaiting to `https://portal.azure.com/#create/Microsoft.Template/uri/<encoded Github raw URL to the template file on your branch>`
  Example: The URL on main <https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq%2Fmain%2Finfra%2Fazure%2Farm%2Fappservice.json>


## AWS

Coming soon
