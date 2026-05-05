#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Load environment
source .env.production

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME:$VERSION .
docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest

echo "📤 Pushing to registry..."
docker push $IMAGE_NAME:$VERSION
docker push $IMAGE_NAME:latest

# Apply Kubernetes manifests
echo "☸️  Deploying to Kubernetes..."
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for rollout
echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/aiverse-api

# Run health check
echo "🏥 Running health check..."
HEALTH_URL=$(kubectl get svc aiverse-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -f http://$HEALTH_URL/api/v1/health || exit 1

echo "✅ Deployment complete!"