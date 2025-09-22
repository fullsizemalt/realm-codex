# Generated mystical aliases — do not edit directly; run `make weave` (edit realm.yml)

export REALM="{{REALM_SLUG}}"
export ENV_DEV="{{ENV_DEV}}"
export ENV_STG="{{ENV_STG}}"
export ENV_PROD="{{ENV_PROD}}"
export REGION="{{REGION}}"

alias scry-prod='echo "🔮 https://{{ORACLE_NAME}}.$ENV_PROD.$REALM.lan"'
alias inscribe='echo "📜 Publishing the {{SCRIPTORIUM_NAME}}"; mkdocs gh-deploy --force'
alias ward='echo "🛡️ Entering the {{SANCTUM_NAME}}"; export VAULT_ADDR=http://{{SANCTUM_NAME}}.$ENV_PROD.$REALM.lan:8200'
alias kindle='echo "🧱 Building at the {{FORGE_NAME}}"; ./scripts/build.sh'
alias tend='echo "🐾 Tending the {{MENAGERIE_NAME}}"; ./scripts/media_sync.sh'
alias convene='echo "🗝️ Bridging the {{CONCLAVE_NAME}}"; ./scripts/bridge_check.sh'
alias awaken='echo "🧠 Awakening the {{ARCANUM_NAME}}"; ./scripts/agent_orchestrate.sh'
