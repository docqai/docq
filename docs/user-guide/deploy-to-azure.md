# Deploy to Azure: 15 Minutes and Secure

In this deployment, you're going to utilise [Microsoft Cloud / Azure](https://azure.microsoft.com/) which is Microsoft's cloud offering trusted by many organisations.

1. [Fork](https://github.com/docqai/docq/fork) the Docq repo at GitHub;
2. Click this [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fdocqai%2Fdocq%2Fmain%2Finfra%2Fazure%2Farm%2Fappservice.json) button to start the configuration wizard on Azure.
   ![Azuere deploy whizard params screenshot](../assets/azure_deploy_params_screen.png)
3. Resource group: create a new one by clicking the 'Create new' link next to the Resource Group label.
4. Region: select your preferred region. `East US` or `West Europe` are recommended because of LLM support.
5. Leave all the remaining parameters values as default unless you encounter a resource naming clash.
6. Click 'Next: Reveiw + create'. Azure will validate the template + parameter values. You should see 'Validation Passed'.
7. Click 'Create' to initiate resouece deployment. It will take 5-10mins. A successful deployment looks like the following.
   ![Azure deploy complete screenshot](../assets/azure_deploy_complete.png)
8. Click on the 'Outputs' left menu option to grab the URL to the Docq web app you just deployed.