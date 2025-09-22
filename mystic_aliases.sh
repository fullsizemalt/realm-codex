# Generated mystical aliases — do not edit directly; run `make weave` (edit realm.yml)

export REALM="elysium"
export ENV_DEV="dawn"
export ENV_STG="dusk"
export ENV_PROD="zenith"
export REGION="usw"

alias scry-prod='echo "🔮 https://oracle.$ENV_PROD.$REALM.lan"'
alias inscribe='echo "📜 Publishing the scriptorium"; mkdocs gh-deploy --force'
alias ward='echo "🛡️ Entering the sanctum"; export VAULT_ADDR=http://sanctum.$ENV_PROD.$REALM.lan:8200'
alias kindle='echo "🧱 Building at the forge"; ./scripts/build.sh'
alias tend='echo "🐾 Tending the menagerie"; ./scripts/media_sync.sh'
alias convene='echo "🗝️ Bridging the conclave"; ./scripts/bridge_check.sh'
alias awaken='echo "🧠 Awakening the arcanum"; ./scripts/agent_orchestrate.sh'
