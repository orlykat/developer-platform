#!/usr/bin/env bash
set -euo pipefail

helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm upgrade --install argocd argo/argo-cd \
  --version 10.18.2 \
  --namespace argocd \
  --create-namespace \
  --values platform/argocd/values.yaml \
  --wait \
  --timeout 10m
