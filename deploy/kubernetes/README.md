# Kubernetes deployment

These manifests deploy one MooPiew application replica with persistent SQLite
storage and two read-only engineering dashboard replicas. Apply them with
Kustomize after creating the runtime secret:

```bash
kubectl create namespace moopiew
kubectl -n moopiew create secret generic moopiew-runtime \
  --from-literal=ADMIN_KEY="$(openssl rand -base64 32)" \
  --from-literal=EMPLOYEE_KEY="$(openssl rand -base64 32)" \
  --from-literal=KITCHEN_KEY="$(openssl rand -base64 32)"
kubectl -n moopiew create secret generic dashboard-basic-auth \
  --from-file=auth=/path/to/reviewed/htpasswd
kubectl apply -k deploy/kubernetes
kubectl -n moopiew rollout status deployment/moopiew
```

Validate the fully rendered manifests against strict Kubernetes schemas before
applying them:

```bash
./scripts/ci/install-kubernetes-tools.sh
./scripts/ci/validate-kubernetes.sh
```

Set immutable image digests and replace `moopiew.example.invalid` before
production; also replace `dashboard.example.invalid` and provision both TLS
secrets. The dashboard ingress requires the external basic-auth secret and
should additionally sit behind Cloudflare Access or the organization's OIDC
proxy. The application deliberately has one replica because SQLite on a
`ReadWriteOnce` volume does not support horizontal application replicas. Its
zero-unavailable disruption budget blocks voluntary drains until an operator
accepts downtime or moves the pod. Backups and restore drills remain mandatory.

The ingress controller namespace must carry the standard
`kubernetes.io/metadata.name=ingress-nginx` label for the NetworkPolicy. If a
different controller is used, update that selector before applying.
