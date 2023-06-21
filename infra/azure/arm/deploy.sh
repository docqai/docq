
NAME="${1:-"docq"}"

LOCATION="${2:-"westeurope"}"

RESOURCE_GROUP="${NAME}-rg-${LOCATION}"


res1=$(az group create --name $RESOURCE_GROUP --location $LOCATION)
echo $res1 | jq '.'

echo "Resource group '${RESOURCE_GROUP}' created."

res2=$(az deployment group create --resource-group $RESOURCE_GROUP --name $NAME --template-file appservice.json --parameters @appservice.parameters.json)

status=$(echo $res2 | (grep -E -o 'Failed' || echo 'Success') | head -1)

echo $res2 | jq '.'

echo "status=${status}"
echo $status

if [ $status = "Failed" ]
then  
  echo "Deployment failed."
  exit 1
else
  echo "Outputs:"
  echo $res2 | jq -r '.properties.outputs'
  echo "Docq stack successfully deployed."
  exit 0
fi

