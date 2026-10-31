#!/usr/bin/env bash
# Install the secret scanner at the release the register pins, refusing anything whose
# checksum the register does not record.
#
# Usage: install-scanner.sh <tool> <owner/repo> <version> <sha256>
#   The four values are gate-secrets' TOOL, TOOL_REPO, TOOL_VERSION and TOOL_SHA256, every
#   one read from the register in pre-flight. Nothing here is a default.
#
# Exit: 0 installed to /usr/local/bin/<tool>
#       1 download failed, or the checksum did not match — nothing was installed or run
#       2 usage
#
# Works in a temporary directory, never the repository: the archive unpacks a file named
# <tool>, and the working directory is somebody's repository.
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "usage: install-scanner.sh <tool> <owner/repo> <version> <sha256>" >&2
  exit 2
fi
tool=$1 repo=$2 version=$3 sha256=$4

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

curl -sSfL -o "$work/$tool.tgz" \
  "https://github.com/$repo/releases/download/v$version/${tool}_${version}_linux_x64.tar.gz"

# The one step where continuing is worse than failing: an unverified secret scanner is a
# gate in name only.
if ! (cd "$work" && echo "$sha256  $tool.tgz" | sha256sum -c - >/dev/null); then
  echo "install-scanner: $tool $version does not match the checksum the register records" \
       "($sha256). Nothing was installed." >&2
  exit 1
fi

tar -xzf "$work/$tool.tgz" -C "$work" "$tool"
sudo install "$work/$tool" "/usr/local/bin/$tool"
echo "install-scanner: installed $tool $version to /usr/local/bin/$tool (checksum verified)"
