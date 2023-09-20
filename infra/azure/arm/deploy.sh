
NAME="${1:-"docq"}"

LOCATION="${2:-"westeurope"}"

RESOURCE_GROUP="${NAME}-rg-${LOCATION}"

echo "Resourse Group Create response:"
res1=$(az group create --name $RESOURCE_GROUP --location $LOCATION)

echo $res1 | jq '.'
status1=$(echo $res1 | (grep -E -o -i -w '"provisioningState": "Succeeded"') | head -1)
echo "status=${status1}"


if [ -n "$status1" ]
then  
  echo "Outputs:"
  echo "Resource group '${RESOURCE_GROUP}' created."
else
  echo "Resource group '${RESOURCE_GROUP}' creation failed!"
  echo "Deployment failed."
  exit 1
fi


echo "Deployment Group Create response:"
echo "---"
res2=$(az deployment group create --resource-group $RESOURCE_GROUP --name $NAME --template-file appservice.json --parameters @appservice.parameters.json)
echo "---"
status2=$(echo $res2 | (grep -E -o -i -w '"provisioningState": "Succeeded"') | head -1)

echo "---"
echo $res2 | jq '.'
echo "---"
echo "status=${status2}"

if [ -n "$status2" ]
then  
  echo "Outputs:"
  echo $res2 | jq -r '.properties.outputs'
  echo "Deployment group creation completed!"
else
  echo "Deployment group creation failed!"
  echo "Deployment failed."
  exit 1
fi

if [ -n "$status1" ] && [ -n "$status2" ]
then  
  echo "Docq stack successfully deployed."
  exit 0
else
  echo "Deployment failed."
  exit 1
fi
