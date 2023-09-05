NAME="docq"

LOCATION="${1:-"westeurope"}"

RESOURCE_GROUP="${NAME}-ml-rg-${LOCATION}"


#<get_access_token>
TOKEN=$(az account get-access-token --query accessToken -o tsv)
#</get_access_token>

API_VERSION="2022-05-01"

WORKSPACE="${NAME}-main-ws-${LOCATION}"

ENDPOINT_NAME="endpoint-10252"

# <create_variables>
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
#</create_variables>

echo -e "Using:\nSUBSCRIPTION_ID=$SUBSCRIPTION_ID\nLOCATION=$LOCATION\nRESOURCE_GROUP=$RESOURCE_GROUP\nWORKSPACE=$WORKSPACE"

wait_for_completion () {
    operation_id=$1
    status="unknown"

    if [[ $operation_id == "" || -z $operation_id  || $operation_id == "null" ]]; then
        echo "operation id cannot be empty"
        exit 1
    fi

    while [[ $status != "Succeeded" && $status != "Failed" ]]
    do
        echo "Getting operation status from: $operation_id"
        operation_result=$(curl --location --request GET $operation_id --header "Authorization: Bearer $TOKEN")
        # TODO error handling here
        status=$(echo $operation_result | jq -r '.status')
        echo "Current operation status: $status"
        sleep 5
    done

    if [[ $status == "Failed" ]]
    then
        error=$(echo $operation_result | jq -r '.error')
        echo "Error: $error"
    fi
}

# # <get_deployment>
# response=$(curl --location --request GET "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$WORKSPACE/onlineEndpoints/$ENDPOINT_NAME/deployments/blue?api-version=$API_VERSION" \
# --header "Content-Type: application/json" \
# --header "Authorization: Bearer $TOKEN")

# operation_id=$(echo $response | jq -r '.properties.properties.AzureAsyncOperationUri')
# wait_for_completion $operation_id

# scoringUri=$(echo $response | jq -r '.properties.scoringUri')
# # </get_endpoint>


# # <get_endpoint_access_token>
# response=$(curl -H "Content-Length: 0" --location --request POST "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$WORKSPACE/onlineEndpoints/$ENDPOINT_NAME/token?api-version=$API_VERSION" \
# --header "Authorization: Bearer $TOKEN")
# accessToken=$(echo $response | jq -r '.accessToken')
# # </get_endpoint_access_token>

# # <score_endpoint>
# curl --location --request POST $scoringUri \
# --header "Authorization: Bearer $accessToken" \
# --header "Content-Type: application/json" \
# --data-raw @sample-request.json
# # </score_endpoint>

# # <get_deployment_logs>
# curl --location --request POST "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$WORKSPACE/onlineEndpoints/$ENDPOINT_NAME/deployments/blue/getLogs?api-version=$API_VERSION" \
# --header "Authorization: Bearer $TOKEN" \
# --header "Content-Type: application/json" \
# --data-raw "{ \"tail\": 100 }"

az ml online-endpoint invoke --name $ENDPOINT_NAME --workspace-name $WORKSPACE --resource-group $RESOURCE_GROUP --request-file model-1/sample-request.json