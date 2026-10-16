# Deploying to OpenShift

Three containers (frontend, backend, a local mock sign-in page), no external
database — SQLite lives on a small PVC next to the backend. Everything below
assumes you're logged in (`oc login ...`) and `helm` is installed locally.

## 1. Pick your cluster's apps domain

Every other value in this walkthrough derives from this one. If you don't
already know it:

```bash
oc get ingresscontroller default -n openshift-ingress-operator -o jsonpath='{.status.domain}'
# e.g. apps.mycluster.example.com
```

Three public URLs will exist once deployed, all under that domain (`dha` is
this walkthrough's release name — swap in your own if you pick a different
one):

| Route        | URL                                   | Purpose                              |
|--------------|----------------------------------------|---------------------------------------|
| `dha`        | `https://dha.<domain>`                | the app itself                       |
| `dha-backend`| `https://dha-backend.<domain>`        | API the browser calls directly       |
| `dha-idp`    | `https://dha-idp.<domain>`            | mock sign-in page (dev/demo only)    |

## 2. Create the project and build the images

```bash
export DOMAIN=apps.mycluster.example.com   # from step 1
export NS=dhl-hosting-advisor

oc new-project $NS   # or: oc project $NS, if it already exists
```

Backend image (also runs the mock IdP — same image, different command):

```bash
oc new-build --name=dha-backend --strategy=docker --binary -n $NS
oc start-build dha-backend --from-dir=./backend --follow -n $NS
```

Frontend image — **the backend's public URL must be baked in at build
time** (it's compiled into the static JS, not read at runtime), so build
this one second, pointing at the backend Route from the table above:

```bash
oc new-build --name=dha-frontend --strategy=docker --binary \
  --build-arg=VITE_API_BASE_URL=https://dha-backend.$DOMAIN -n $NS
oc start-build dha-frontend --from-dir=./frontend --follow -n $NS
```

Both land in this project's slice of the internal registry
(`image-registry.openshift-image-registry.svc:5000/$NS/dha-backend:latest`,
`.../dha-frontend:latest`) — the chart's default `image.registry` already
points there, and pulls need no `imagePullSecret` as long as you stay in
this same namespace.

## 3. Install the chart

```bash
helm install dha ./helm/dhl-hosting-advisor \
  -n $NS \
  --set namespace=$NS \
  --set route.domain=$DOMAIN \
  --set-string auth.clientSecret=$(openssl rand -hex 16)
```

`helm install` prints the three URLs when it finishes. Watch the rollout:

```bash
oc get pods -n $NS -w
```

Open the frontend URL, click **Sign in**, pick any of the five demo
identities on the mock sign-in page — same ones as local `docker compose`
(Alex Admin, Dana/Priya Assessor, Jordan Approver, Morgan Viewer).

## Redeploying after a code change

Plain `Deployment`s don't watch for new images the way OpenShift's older
`DeploymentConfig` does — a fresh push to the same `:latest` tag needs an
explicit nudge:

```bash
oc start-build dha-backend --from-dir=./backend --follow -n $NS    # if backend changed
oc start-build dha-frontend --from-dir=./frontend --follow -n $NS  # if frontend changed
oc rollout restart deployment/dha-backend deployment/dha-frontend deployment/dha-mock-idp -n $NS
```

## Switching off the mock sign-in page (real Azure AD)

No code changes — this is exactly what the OIDC-pluggable design in
`backend/app/auth/oidc.py` is for:

```bash
helm upgrade dha ./helm/dhl-hosting-advisor -n $NS \
  --set namespace=$NS \
  --set route.domain=$DOMAIN \
  --set auth.provider=azuread \
  --set auth.azuread.tenantId=<your-tenant-id> \
  --set auth.clientId=<app-registration-client-id> \
  --set-string auth.clientSecret=<app-registration-client-secret> \
  --set mockIdp.enabled=false
```

Register `https://dha-backend.$DOMAIN/auth/callback` as the app
registration's redirect URI in Azure AD first, or the callback will fail.

## What's deliberately not here

- **No autoscaling / HPA.** This is a pilot-scale governance tool, not a
  high-traffic service; the resource requests in `values.yaml` are small on
  purpose.
- **Backend is pinned to 1 replica.** SQLite is single-writer — see the
  comment in `values.yaml` and `backend/app/db/session.py`. Frontend and the
  mock IdP scale freely since they're stateless.
- **No CI/CD wiring.** `oc start-build --from-dir` is the whole deploy
  pipeline here, by design — lowest operational surface area for a tool this
  size. Point a real pipeline at the same `oc new-build`/`helm upgrade`
  commands later if this grows past that.
