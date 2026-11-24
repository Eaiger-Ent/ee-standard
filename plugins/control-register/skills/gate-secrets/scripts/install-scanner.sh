#!/usr/bin/env bash
# Install the secret scanner at the release the register pins, refusing anything whose
# checksum the register does not record.
#
# Usage: install-scanner.sh <tool> <owner/repo> <version> <sha256-x64> <sha256-arm64>
#   The five values are gate-secrets' TOOL, TOOL_REPO, TOOL_VERSION, TOOL_SHA256 and
#   TOOL_SHA256_ARM64, every one read from the register in pre-flight. Nothing here is a
#   default.
#
# The archive is the one for the processor this runs on, as .devcontainer/setup.sh picks
# it. Until 0.6.3 this always fetched the x64 build and checked it against the x64
# checksum, so on an Apple silicon container the check passed and installed a binary that
# could not run there (Phase 15 Run D).
#
# Exit: 0 installed to /usr/local/bin/<tool>
#       1 download failed, the checksum did not match, or no build is recorded for this
#         processor — nothing was installed or run
#       2 usage
#
# Works in a temporary directory, never the repository: the archive unpacks a file named
# <tool>, and the working directory is somebody's repository.
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "usage: install-scanner.sh <tool> <owner/repo> <version> <sha256-x64> <sha256-arm64>" >&2
  exit 2
fi
tool=$1 repo=$2 version=$3

machine=$(uname -m)
case "$machine" in
  x86_64|amd64)  arch=x64   sha256=$4 ;;
  aarch64|arm64) arch=arm64 sha256=$5 ;;
  *)
    echo "install-scanner: no $tool build is recorded for '$machine'. Nothing was installed." >&2
    exit 1 ;;
esac
if [ -z "$sha256" ]; then
  echo "install-scanner: the register records no $arch checksum for $tool. Nothing was installed." >&2
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

curl -sSfL -o "$work/$tool.tgz" \
  "https://github.com/$repo/releases/download/v$version/${tool}_${version}_linux_${arch}.tar.gz"

# The one step where continuing is worse than failing: an unverified secret scanner is a
# gate in name only.
if ! (cd "$work" && echo "$sha256  $tool.tgz" | sha256sum -c - >/dev/null); then
  echo "install-scanner: $tool $version ($arch) does not match the checksum the register records" \
       "($sha256). Nothing was installed." >&2
  exit 1
fi

tar -xzf "$work/$tool.tgz" -C "$work" "$tool"
sudo install "$work/$tool" "/usr/local/bin/$tool"
echo "install-scanner: installed $tool $version ($arch) to /usr/local/bin/$tool (checksum verified)"
