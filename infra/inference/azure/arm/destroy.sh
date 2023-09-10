NAME="${1:-"docq"}"

LOCATION="${2:-"westeurope"}"

RESOURCE_GROUP="${3:-${NAME}-ml-rg-${LOCATION}}"

read -p "This will delete all resources in resource group '${RESOURCE_GROUP}'. Are you sure? [y/n]" confirm

if [ $confirm = "y" ] || [ $confirm = "Y" ] 
then

  workspaces=($(az ml workspace list --resource-group $RESOURCE_GROUP --query [].name --output tsv))
  echo "Deleting ${#workspaces[@]} Azure ML Workspaces"

  for workspace in $workspaces 
  do
      az ml workspace delete --name $workspace --resource-group $RESOURCE_GROUP --permanently-delete --all-resources --yes
      echo "'${workspace}' deleted."
  done
  wait

  res=$(az group delete --name ${RESOURCE_GROUP} -y)
  echo $res | jq '.'
  wait

  echo "Success! All resources in resource group '${RESOURCE_GROUP}' were deleted."
  exit 0
elif [ $confirm = "n" ] || [ $confirm = "N" ] 
then
    echo "Aborted! nothing was destroyed."
    exit -1
fi