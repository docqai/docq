poe test
VER=`poetry version --short`
TAG="v${VER}"
echo "Tagging release ${TAG}"
git tag $TAG_NAME
git push origin $TAG_NAME


