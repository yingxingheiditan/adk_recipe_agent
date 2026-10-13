#!/usr/bin/env bash
# deploy.sh - Build container images with Cloud Build, store them in Artifact
# Registry, and deploy the three services to Cloud Run in dependency order:
#
#   grocery_db_service -> recipe_agent -> main_chatbot
#
# Each service's URL is passed to the next one as an environment variable.
#
# Usage:
#   ./deploy.sh [all|grocery|recipe|chatbot]      (default: all)
#
# Configuration (environment variables or a .env file next to this script):
#   PROJECT_ID     Google Cloud project ID (required)
#   REGION         Cloud Run / Artifact Registry region (default: us-central1)
#   REPO           Artifact Registry repository name (default: recipe-agents)
#   ALLOW_UNAUTH   true = public services, false = IAM-only (default: true)
set -euo pipefail

cd "$(dirname "$0")"
[[ -f .env ]] && set -a && source .env && set +a

PROJECT_ID="${PROJECT_ID:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-recipe-agents}"
ALLOW_UNAUTH="${ALLOW_UNAUTH:-true}"
TARGET="${1:-all}"
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d-%H%M%S)"

log() { echo -e "\033[1;34m==>\033[0m $*"; }
die() { echo -e "\033[1;31mERROR:\033[0m $*" >&2; exit 1; }

[[ -n "$PROJECT_ID" ]] || die "PROJECT_ID is not set (export it or add it to .env)."
command -v gcloud >/dev/null || die "gcloud CLI not found."
[[ "$TARGET" =~ ^(all|grocery|recipe|chatbot)$ ]] || die "Unknown target '$TARGET'. Use: all|grocery|recipe|chatbot"

if [[ "$ALLOW_UNAUTH" == "true" ]]; then AUTH_FLAG="--allow-unauthenticated"; else AUTH_FLAG="--no-allow-unauthenticated"; fi

# Create the Artifact Registry Docker repository if it does not exist yet.
ensure_repo() {
  if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    log "Creating Artifact Registry repository '$REPO' in $REGION"
    gcloud artifacts repositories create "$REPO" --repository-format=docker \
      --location="$REGION" --project="$PROJECT_ID" --quiet
  fi
}

# build_image <source_dir> <image_name>: builds with Cloud Build, prints the image URI.
build_image() {
  local image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/$2:${TAG}"
  log "Building $2 with Cloud Build -> $image" >&2
  gcloud builds submit "$1" --tag="$image" --project="$PROJECT_ID" --quiet >&2
  echo "$image"
}

# get_url <service_name>: prints the Cloud Run URL of a deployed service.
get_url() {
  gcloud run services describe "$1" --region="$REGION" --project="$PROJECT_ID" \
    --format='value(status.url)' 2>/dev/null || true
}

# deploy_service <service_name> <source_dir> <env_vars>: build, deploy, health-check.
deploy_service() {
  local name="$1" dir="$2" env_vars="$3" image url
  image="$(build_image "$dir" "$name")"
  log "Deploying $name to Cloud Run ($REGION)"
  gcloud run deploy "$name" --image="$image" --region="$REGION" --project="$PROJECT_ID" \
    $AUTH_FLAG --set-env-vars="$env_vars" --quiet
  url="$(get_url "$name")"
  check_health "$name" "$url"
}

# check_health <service_name> <url>: fails the script if /health is not 200.
check_health() {
  local headers=()
  [[ "$ALLOW_UNAUTH" != "true" ]] && headers=(-H "Authorization: Bearer $(gcloud auth print-identity-token)")
  if curl -fsS --max-time 30 ${headers[@]+"${headers[@]}"} "$2/health" >/dev/null; then
    log "$1 is healthy at $2"
  else
    die "$1 failed its health check at $2/health"
  fi
}

# require_url <service_name>: URL of an already-deployed dependency, or exit.
require_url() {
  local url; url="$(get_url "$1")"
  [[ -n "$url" ]] || die "Dependency '$1' is not deployed. Deploy it first (./deploy.sh all)."
  echo "$url"
}

COMMON_ENV="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"

log "Project: $PROJECT_ID | Region: $REGION | Repo: $REPO | Tag: $TAG | Public: $ALLOW_UNAUTH"
ensure_repo

if [[ "$TARGET" == "all" || "$TARGET" == "grocery" ]]; then
  deploy_service grocery-db-service grocery_db_service "GROCERY_DB_PATH=groceries.db"
fi

if [[ "$TARGET" == "all" || "$TARGET" == "recipe" ]]; then
  GROCERY_URL="$(require_url grocery-db-service)"
  deploy_service recipe-grocery-agent recipe_agent "${COMMON_ENV},GROCERY_DB_SERVICE_URL=${GROCERY_URL}"
fi

if [[ "$TARGET" == "all" || "$TARGET" == "chatbot" ]]; then
  RECIPE_URL="$(require_url recipe-grocery-agent)"
  deploy_service main-chatbot-agent main_chatbot "${COMMON_ENV},RECIPE_AGENT_URL=${RECIPE_URL}"
fi

GROCERY_URL="$(get_url grocery-db-service)"
RECIPE_URL="$(get_url recipe-grocery-agent)"
CHATBOT_URL="$(get_url main-chatbot-agent)"

echo
log "Deployed services:"
echo "  grocery-db-service    ${GROCERY_URL:-<not deployed>}"
echo "  recipe-grocery-agent  ${RECIPE_URL:-<not deployed>}"
echo "  main-chatbot-agent    ${CHATBOT_URL:-<not deployed>}"
echo
log "Run the evaluation pipeline against this deployment:"
echo "  python3 eval_pipeline.py --grocery-url=$GROCERY_URL --recipe-url=$RECIPE_URL --chatbot-url=$CHATBOT_URL"
