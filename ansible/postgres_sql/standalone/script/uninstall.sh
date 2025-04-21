#!/usr/bin/env bash
#
# uninstall_percona_patroni.sh
#
# This script removes Percona PostgreSQL 17, Patroni, Etcd, and related packages
# installed by your setup script. It also cleans up configuration files
# and systemd services.

# set -e

echo "Stopping and disabling services..."
sudo systemctl stop patroni etcd postgresql || true
sudo systemctl disable patroni etcd postgresql || true
sudo systemctl stop percona-patroni || true
sudo systemctl disable percona-patroni || true

echo "Removing Percona PostgreSQL and related packages..."
sudo apt remove -y percona-postgresql-17 python3-pip python3-dev binutils \
  percona-patroni etcd etcd-server etcd-client percona-pgbackrest gnupg2 lsb-release
# sudo apt remove -y percona-postgresql-17 python3-pip python3-dev binutils \
#   percona-patroni percona-pgbackrest gnupg2 lsb-release

# echo "Purging leftover configs for removed packages..."
# sudo apt purge -y percona-postgresql-17 python3-pip python3-dev binutils \
#   percona-patroni etcd etcd-server etcd-client percona-pgbackrest gnupg2 lsb-release

DEBIAN_FRONTEND=noninteractive \
     apt-get purge -y \
     -o Dpkg::Options::="--force-confdef" \
     -o Dpkg::Options::="--force-confold" \
     percona-postgresql-17 python3-pip python3-dev binutils \
     percona-patroni etcd etcd-server etcd-client percona-pgbackrest \
     gnupg2 lsb-release

# DEBIAN_FRONTEND=noninteractive \
#      apt-get purge -y \
#      -o Dpkg::Options::="--force-confdef" \
#      -o Dpkg::Options::="--force-confold" \
#      percona-postgresql-17 python3-pip python3-dev binutils \
#      percona-patroni percona-pgbackrest \
#      gnupg2 lsb-release

echo "Removing Percona repository..."
sudo apt remove -y percona-release || true
sudo apt purge -y percona-release || true

echo "Performing autoremove to clean up unused dependencies..."
sudo apt autoremove -y

echo "Cleaning up config files and directories..."
# Patroni service file
sudo rm -f /etc/systemd/system/percona-patroni.service

# Patroni config
sudo rm -f /etc/patroni/patroni.yml

# Etcd config
sudo rm -rf /etc/etcd

# PostgreSQL data directory
sudo rm -rf /var/lib/postgresql/17/main

# Remove leftover .deb if present
sudo rm -f /home/$USER/percona-release_latest.generic_all.deb
sudo rm -f /root/percona-release_latest.generic_all.deb
sudo rm -f ./percona-release_latest.generic_all.deb

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Uninstall complete. If any manual cleanup remains, please remove them accordingly."
