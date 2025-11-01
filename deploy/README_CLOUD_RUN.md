# Deploy Vāhan-Rakshak to Google Cloud Run (Windows cmd.exe)

This guide deploys the FastAPI backend to Cloud Run using Artifact Registry.

## Prerequisites

- Google Cloud project with billing enabled
- gcloud CLI installed and logged in (`gcloud init`)
- APIs enabled:
  - Cloud Run Admin API
  - Cloud Build API
  - Artifact Registry API

## 1. Configure project and region

```
gcloud config set project PROJECT_ID
gcloud config set run/region REGION
```

Recommended regions: us-central1, us-east1, europe-west1, asia-south1

## 2. Create Artifact Registry (one-time)

```
gcloud artifacts repositories create vahan-rakshak ^
  --repository-format=docker ^
  --location=REGION
```

## 3. Build and push container

Option A: Using Cloud Build + Dockerfile

```
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT_ID/vahan-rakshak/vahan-rakshak:latest
```

Option B: Using cloudbuild.yaml (generates an image tagged with the commit SHA)

```
gcloud builds submit --config cloudbuild.yaml ^
  --substitutions=_REGION=REGION,_REPO=vahan-rakshak,_IMAGE=vahan-rakshak,_SERVICE=vahan-rakshak
```

## 4. Deploy to Cloud Run

Set environment variables for watsonx Orchestrate (replace values):

```
set WATSONX_API_URL=https://<your-orchestrate-endpoint>
set WATSONX_API_KEY=<your-api-key>
set WATSONX_PROJECT_ID=<your-project-id>
set WATSONX_SPACE_ID=<your-space-id>
set WATSONX_GUARDIAN_AGENT_ID=guardian_v1
set WATSONX_GUARDIAN_ACTION_MONITOR=monitor_driver
set WATSONX_GUARDIAN_ACTION_SPEED=monitor_speed
```

Deploy (using the image built in step 3):

```
gcloud run deploy vahan-rakshak ^
  --image REGION-docker.pkg.dev/PROJECT_ID/vahan-rakshak/vahan-rakshak:latest ^
  --region REGION ^
  --allow-unauthenticated ^
  --port 8080 ^
  --set-env-vars WATSONX_API_URL=%WATSONX_API_URL% ^
  --set-env-vars WATSONX_API_KEY=%WATSONX_API_KEY% ^
  --set-env-vars WATSONX_PROJECT_ID=%WATSONX_PROJECT_ID% ^
  --set-env-vars WATSONX_SPACE_ID=%WATSONX_SPACE_ID% ^
  --set-env-vars WATSONX_GUARDIAN_AGENT_ID=%WATSONX_GUARDIAN_AGENT_ID% ^
  --set-env-vars WATSONX_GUARDIAN_ACTION_MONITOR=%WATSONX_GUARDIAN_ACTION_MONITOR% ^
  --set-env-vars WATSONX_GUARDIAN_ACTION_SPEED=%WATSONX_GUARDIAN_ACTION_SPEED%
```

The deploy command returns a service URL like:

```
https://vahan-rakshak-xxxxx-uc.a.run.app
```

## 5. Quick checks

- Health: `GET /healthz`
- Agent endpoints (watsonx-backed):
  - `POST /v1/driver/monitoring` (requires valid watsonx credentials)
  - `POST /v1/speed` (requires valid watsonx credentials)
- Tool endpoints (local):
  - `POST /v1/tools/cargo/scan-qr`
  - `POST /v1/tools/regulator/check-cargo-compliance`
  - `POST /v1/tools/safety/{vehicle_id}/driver-alert`
  - `POST /v1/tools/speed/process`

## 6. (Optional) Use Secret Manager for sensitive values

Create secrets:

```
gcloud secrets create WATSONX_API_KEY --replication-policy=automatic

echo -n "<your-api-key>" > wx_key.txt
gcloud secrets versions add WATSONX_API_KEY --data-file=wx_key.txt
```

Deploy with secrets:

```
gcloud run deploy vahan-rakshak ^
  --image REGION-docker.pkg.dev/PROJECT_ID/vahan-rakshak/vahan-rakshak:latest ^
  --region REGION ^
  --allow-unauthenticated ^
  --port 8080 ^
  --set-secrets WATSONX_API_KEY=WATSONX_API_KEY:latest ^
  --set-env-vars WATSONX_API_URL=https://<your-orchestrate-endpoint> ^
  --set-env-vars WATSONX_PROJECT_ID=<your-project-id> ^
  --set-env-vars WATSONX_SPACE_ID=<your-space-id>
```

## 7. Troubleshooting

- 500 from POST /v1/driver/monitoring or /v1/speed: Check watsonx env vars; ensure the agent/action IDs exist and the endpoint is reachable.
- 404 on tool endpoints: Verify base path and service URL; list routes via `/docs` (OpenAPI).
- Startup failures: View Cloud Run logs: **Logs** tab in the service or

```
gcloud logs read --project=PROJECT_ID --limit=50 --format=json
```

## 8. Clean up

```
gcloud run services delete vahan-rakshak --region REGION
# Optionally delete the Artifact Registry repo (be careful; this removes images)
#gcloud artifacts repositories delete vahan-rakshak --location=REGION
```
