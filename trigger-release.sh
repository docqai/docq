poe test
VER=`poetry version --short`
TAG="v${VER}"
echo "Tagging release ${TAG}"
git tag $TAG
git push origin $TAG


