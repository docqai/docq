poe test
VERSION=(poetry version --short)
TAG_NAME="v${VERSION}"
git tag $TAG_NAME
git push origin $TAG_NAME


