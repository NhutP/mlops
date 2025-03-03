apt update -y && apt upgrade -y

swapoff -a

sed -i '/swap.img/s/^/#/' /etc/fstab

printf "overlay\nbr_netfilter\n" | tee /etc/modules-load.d/containerd.conf

modprobe overlay

modprobe br_netfilter

echo "net.bridge.bridge-nf-call-ip6tables = 1" | tee -a /etc/sysctl.d/kubernetes.conf

echo "net.bridge.bridge-nf-call-iptables = 1" | tee -a /etc/sysctl.d/kubernetes.conf

echo "net.ipv4.ip_forward = 1" | tee -a /etc/sysctl.d/kubernetes.conf

sysctl --system

apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates


if [ ! -f /etc/apt/trusted.gpg.d/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmour -o /etc/apt/trusted.gpg.d/docker.gpg
fi


add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

apt update -y

apt install -y containerd.io

containerd config default | tee /etc/containerd/config.toml >/dev/null 2>&1

sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

systemctl restart containerd

systemctl enable containerd

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

apt update -y

apt install -y kubelet kubeadm kubectl

apt-mark hold kubelet kubeadm kubectl