NAME="${1:-"docq"}"

LOCATION="${2:-"westeurope"}"

RESOURCE_GROUP="${3:-${NAME}-rg-${LOCATION}}"

read -p "This will delete all resources in resource group '${RESOURCE_GROUP}'. Are you sure? [y/n]" confirm

if [ $confirm = "y" ] || [ $confirm = "Y" ] 
then
  res=$(az group delete --name ${RESOURCE_GROUP} -y)
  echo $res | jq '.'
  wait
  deleted_instances=$(az cognitiveservices account list-deleted --query [].name --output tsv)

  echo "Purging ${#deleted_instances[@]} Microsoft.CognitiveServies"

  for deleted_instance in $deleted_instances 
  do
      az cognitiveservices account purge --name $deleted_instance --location $LOCATION --resource-group $RESOURCE_GROUP
      echo "'${deleted_instance}' purged."
  done
  echo "Success! All resources in resource group '${RESOURCE_GROUP}' were deleted."
  exit 0
elif [ $confirm = "n" ] || [ $confirm = "N" ] 
then
    echo "Aborted! nothing was destroyed."
    exit -1
fi