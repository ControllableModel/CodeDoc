#!/usr/bin/env bash
# Clone each upstream baseline at the pinned commit and apply this artifact's patch.
# Nothing here downloads models, writes configuration, or touches credentials.
set -euo pipefail

ROOT="${1:-./third_party}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clone_at() {           # clone_at <url> <commit> <dir>
  local url="$1" commit="$2" dir="$3"
  if [ -d "$dir/.git" ]; then
    echo "  $dir exists, fetching"
    git -C "$dir" fetch --depth 50 origin "$commit"
  else
    mkdir -p "$(dirname "$dir")"
    git clone "$url" "$dir"
    git -C "$dir" fetch --depth 50 origin "$commit"
  fi
  git -C "$dir" checkout -q "$commit"
}

apply() {              # apply <dir> <patch>
  echo "  applying $(basename "$2")"
  git -C "$1" apply --whitespace=nowarn "$2"
}

mkdir -p "$ROOT"

echo "DocAgent"
clone_at https://github.com/facebookresearch/DocAgent.git f27f685 "$ROOT/DocAgent"
apply "$ROOT/DocAgent" "$HERE/patches/docagent/0001-openai-compatible-endpoint-and-token-params.patch"

echo "MemDocAgent"
clone_at https://github.com/bsy99615/MemDocAgent.git 1064f29 "$ROOT/MemDocAgent"
apply "$ROOT/MemDocAgent" "$HERE/patches/memdocagent/0001-restore-base-agent-and-fix-runtime-blockers.patch"

echo "CodeWiki"
clone_at https://github.com/FSoft-AI4Code/CodeWiki.git 5b95c84 "$ROOT/CodeWiki"
apply "$ROOT/CodeWiki" "$HERE/patches/codewiki/0001-reasoning-effort-none-for-tool-calling.patch"

echo "Agentic Doc"
clone_at https://github.com/ishkapoor2000/agentic-ai.git b754200 "$ROOT/agentic-ai"
apply "$ROOT/agentic-ai" "$HERE/patches/agentic-ai/0001-endpoint-syntax-and-cache-tolerance.patch"

echo
echo "Done. Set the generation endpoint before running a baseline, e.g.:"
echo "  export OPENAI_API_KEY=...   OPENAI_BASE_URL=https://your-gateway/v1"
echo "Note: DocAgent also reads its model and endpoint from config/agent_config.yaml, and"
echo "MemDocAgent likewise; both files are gitignored upstream and are not shipped here."
