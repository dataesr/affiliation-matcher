sh docker_push_ext.sh
kubectl delete deployment matcher-web
kubectl delete deployment matcher-worker
kubectl apply -k k8s
kubectl get pods
