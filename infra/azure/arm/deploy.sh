
NAME="${1:-"docq"}"
PREFIX="${NAME}$(( $RANDOM % 90 + 10))"
LOCATION="${2:-"westeurope"}"


CPU_CORE_COUNT="${3:-"2"}"
MEMORY_IN_GB="${4:-"4"}"


RESOURCE_GROUP="${PREFIX}rg"
STORAGE_ACCOUNT="${PREFIX}sa"
BLOB_STORAGE_NAME="${PREFIX}blob"
FILE_STORAGE_NAME="${PREFIX}file"
FILESHARE_IN_GiB="${5:-"5"}"


CONTAINER_REGISTRY="${PREFIX}cr"
CONTAINER_GROUP="${PREFIX}cg"

az group create --name $RESOURCE_GROUP --location $LOCATION
az configure --defaults group=$RESOURCE_GROUP location=$LOCATION

az storage account create --name $STORAGE_ACCOUNT --sku Standard_LRS
BLOB_STORAGE_CONNECTION_STRING=`az storage account show-connection-string --name $STORAGE_ACCOUNT --query connectionString --output tsv`

echo $BLOB_STORAGE_CONNECTION_STRING

az storage container create --name $BLOB_STORAGE_NAME --account-name $STORAGE_ACCOUNT --public-access off --connection-string $BLOB_STORAGE_CONNECTION_STRING

az storage share create --name $FILE_STORAGE_NAME --account-name $STORAGE_ACCOUNT --quota $FILESHARE_IN_GiB --connection-string $BLOB_STORAGE_CONNECTION_STRING

#az acr create --name $CONTAINER_REGISTRY --sku Basic

#az container 

# az deployment group create --template-file template.json --parameters @azuredeploy.parameters.json
