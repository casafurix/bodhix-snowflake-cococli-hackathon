# Snowflake-native deployment

TrialOps ships as one multi-stage Docker image: Vite compiles the React client,
then FastAPI serves the static application and same-origin `/api/*` routes.

The production service uses the short-lived workload identity mounted by
Snowpark Container Services at `/snowflake/session/token`. No Snowflake password,
PAT, API key, or private key is built into the image.

## Publish

```bash
snow sql -c hackathon -f snowflake/migrations/006_spcs_deployment.sql
docker build --platform linux/amd64 -t trialops:latest .
snow spcs image-registry login -c hackathon --role CTOPS_TEAM_ROLE
docker tag trialops:latest \
  pmwcgsc-yq79089.registry.snowflakecomputing.com/ctops_hackathon/app/trialops_repository/trialops:latest
docker push \
  pmwcgsc-yq79089.registry.snowflakecomputing.com/ctops_hackathon/app/trialops_repository/trialops:latest
snow spcs service create TRIALOPS_SERVICE \
  -c hackathon --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP \
  --compute-pool CTOPS_COMPUTE_POOL \
  --spec-path snowflake/deployment/service-spec.yaml \
  --min-instances 1 --max-instances 1 --query-warehouse CTOPS_WH
snow sql -c hackathon -f snowflake/deployment/post_deploy.sql
```

For later image releases, push the new image and use `snow spcs service upgrade`
with the same service specification.

## Verify

```bash
snow spcs service list-containers TRIALOPS_SERVICE \
  -c hackathon --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP
snow spcs service logs TRIALOPS_SERVICE \
  -c hackathon --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP \
  --container-name trialops --instance-id 0 --num-lines 100
snow spcs service list-endpoints TRIALOPS_SERVICE \
  -c hackathon --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP
```

Opening the HTTPS ingress URL redirects to Snowflake sign-in. Use a user granted
`CTOPS_TEAM_ROLE`; Snowflake then forwards the signed-in username to the app for
human-decision audit attribution.

## Cost control

The dedicated pool is one `CPU_X64_XS` node and has a five-minute pool
auto-suspend. Snowflake does not currently detect ingress idleness for public
endpoints, so explicitly suspend the service after a demo:

```bash
snow spcs service suspend TRIALOPS_SERVICE \
  -c hackathon --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP
```

The service has auto-resume enabled. Opening its ingress URL resumes it; allow a
short cold-start before the page appears, and suspend it again after the demo.
