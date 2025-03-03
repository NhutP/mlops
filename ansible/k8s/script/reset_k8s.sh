kubeadm reset -f
rm -rf /var/lib/etcd
rm -rf /etc/kubernetes/manifests/*
rm -rf $HOME/.kube