#!/bin/bash
# Create a new release with automatic versioning
# Usage: ./scripts/create-release.sh 0.1.2

set -e

VERSION="${1:?Version required. Usage: $0 <version>}"

# Validate semantic versioning
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format: $VERSION"
    echo "Use semantic versioning (e.g., 0.1.2)"
    exit 1
fi

echo "📦 Creating release v$VERSION..."

# Update version in files
python scripts/update_version.py "$VERSION"

# Commit version bump
git add .
git commit -m "chore: bump version to v$VERSION" || echo "No changes to commit"

# Create and push tag
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

echo "✅ Release v$VERSION created and pushed!"
echo "📝 Workflow will automatically build and create a GitHub release"
