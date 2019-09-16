#!/bin/bash
#
# Copies and creates custom settings files for MCRI
# 
# Note: this is just a dump of my bash history from setting it up; probably incomplete and needs
# to be improved to make it an actual runnable script
#
set -x
cp -v deploy/secrets/minikube/seqr/postmark_server_token deploy/secrets/gcloud/seqr/postmark_server_token
cp -v deploy/secrets/minikube/seqr/mme_node_admin_token  deploy/secrets/gcloud/seqr/mme_node_admin_token
cp -v deploy/secrets/minikube/postgres/* deploy/secrets/gcloud/postgres/
cp -v deploy/secrets/minikube/postgres/* deploy/secrets/gcloud/postgres/
vi deploy/secrets/gcloud/postgres/postgres.password 
vi deploy/secrets/gcloud/postgres/postgres.username 
mkdir cert
cd cert/
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout seqr.key -out seqr.crt -config seqr.conf 
cp -v seqr.crt  seqr.key  ../deploy/secrets/gcloud/nginx/
cp -v seqr.crt ../deploy/secrets/gcloud/nginx/tls.crt
sudo cp -v seqr.key ../deploy/secrets/gcloud/nginx/tls.key
sudo chown simon.sadedin deploy/secrets/gcloud/nginx/tls.key
mkdir deploy/secrets/gcloud/nginx-gcloud-dev
cp -v deploy/secrets/gcloud/nginx/tls.key deploy/secrets/gcloud/nginx-gcloud-dev/tls.key
cp -v deploy/secrets/gcloud/nginx/tls.crt deploy/secrets/gcloud/nginx-gcloud-dev/tls.crt
mkdir deploy/secrets/gcloud/matchbox
cp -v deploy/secrets/minikube/matchbox/nodes.json deploy/secrets/gcloud/matchbox/
cp -v deploy/secrets/minikube/matchbox/config.xml  deploy/secrets/gcloud/matchbox/config.xml 

gcloud compute disks create --zone australia-southeast1-b --size 400 gcloud-dev-mongo-disk 

gcloud compute disks create --zone australia-southeast1-b --size 20 gcloud-client-secrets-volume


cd ~/seqr; echo 'apt-get install -y zip' | ./servctl shell pipeline-runner gcloud-dev

echo "export SPARK_HOME='$HOME/spark-2.0.2-bin-hadoop2.7'" >> ~/.bashrc

echo "Please make sure the spark / hadoop binaries are at $HOME/spark-2.0.2-bin-hadoop2.7"

echo "TODO: This command needs the ip address of seqr service"

gcloud compute firewall-rules create allowseqrelasticsearch --allow tcp:9200 --source-tags=seqr-test --source-ranges=10.47.248.181/32
