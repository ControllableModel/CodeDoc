# Clone each upstream baseline at the pinned commit and apply this artifact's patch.
# Nothing here downloads models, writes configuration, or touches credentials.
param(
    [string]$Root = "./third_party"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Clone-At {
    param([string]$Url, [string]$Commit, [string]$Dir)
    if (Test-Path (Join-Path $Dir ".git")) {
        Write-Host "  $Dir exists, fetching"
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dir) | Out-Null
        git clone $Url $Dir
    }
    git -C $Dir fetch --depth 50 origin $Commit
    git -C $Dir checkout -q $Commit
}

function Apply-Patch {
    param([string]$Dir, [string]$PatchFile)
    Write-Host "  applying $(Split-Path -Leaf $PatchFile)"
    git -C $Dir apply --whitespace=nowarn $PatchFile
}

New-Item -ItemType Directory -Force -Path $Root | Out-Null

Write-Host "DocAgent"
Clone-At "https://github.com/facebookresearch/DocAgent.git" "f27f685" "$Root/DocAgent"
Apply-Patch "$Root/DocAgent" "$here/patches/docagent/0001-openai-compatible-endpoint-and-token-params.patch"

Write-Host "MemDocAgent"
Clone-At "https://github.com/bsy99615/MemDocAgent.git" "1064f29" "$Root/MemDocAgent"
Apply-Patch "$Root/MemDocAgent" "$here/patches/memdocagent/0001-restore-base-agent-and-fix-runtime-blockers.patch"

Write-Host "CodeWiki"
Clone-At "https://github.com/FSoft-AI4Code/CodeWiki.git" "5b95c84" "$Root/CodeWiki"
Apply-Patch "$Root/CodeWiki" "$here/patches/codewiki/0001-reasoning-effort-none-for-tool-calling.patch"

Write-Host "Agentic Doc"
Clone-At "https://github.com/ishkapoor2000/agentic-ai.git" "b754200" "$Root/agentic-ai"
Apply-Patch "$Root/agentic-ai" "$here/patches/agentic-ai/0001-endpoint-syntax-and-cache-tolerance.patch"

Write-Host ""
Write-Host "Done. Set the generation endpoint before running a baseline, e.g.:"
Write-Host '  $env:OPENAI_API_KEY="..."; $env:OPENAI_BASE_URL="https://your-gateway/v1"'
Write-Host "Note: DocAgent and MemDocAgent also read model and endpoint from"
Write-Host "config/agent_config.yaml; that file is gitignored upstream and is not shipped here."
