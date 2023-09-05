FILE="${1:-"online-deployment-llama2-7b-chat-v8.yaml"}"
ENDPOINT_NAME="${2:-"docq-endpoint"}"
az ml online-deployment update \
  --name "llama2-7b-chat-8" \
  --workspace-name "docq-main-ws-eastus" \
  --resource-group "docq-ml-rg-eastus" \
  --endpoint-name $ENDPOINT_NAME \
  --file $FILE