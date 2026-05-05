#!/bin/bash
set -e

echo "🔄 Rolling back deployment..."

# Rollback Kubernetes deployment
kubectl rollout undo deployment/aiverse-api

# Wait for rollback
kubectl rollout status deployment/aiverse-api

echo "✅ Rollback complete!"