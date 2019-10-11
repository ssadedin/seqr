#!/bin/bash

set -x
set -e

mkdir -p cert

cd cert

echo "
[req]
default_bits       = 2048
default_keyfile    = localhost.key
distinguished_name = mcri_seqr
req_extensions     = req_ext
x509_extensions    = v3_ca

[mcri_seqr]
countryName                 = AU
countryName_default         = AU
stateOrProvinceName         = Victoria
stateOrProvinceName_default = Victoria
localityName                = Parkville
localityName_default        = Parkville
organizationName            = Murdoch Childrens Research Institute
organizationName_default    = localhost
organizationalUnitName      = Bioinformatics
organizationalUnitName_default = Bioinformatics
commonName                  = seqr.mcri.edu.au
commonName_default          = seqr.mcri.edu.au
commonName_max              = 64

[req_ext]
subjectAltName = @alt_names

[v3_ca]
subjectAltName = @alt_names

[alt_names]
DNS.1   = seqr.mcri.edu.au
" > seqr.conf

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout seqr.key -out seqr.crt -config seqr.conf 

mkdir -p ../secrets/gcloud/nginx

sudo cp -v seqr.key ../secrets/gcloud/nginx/tls.key

sudo cp -v seqr.crt ../secrets/gcloud/nginx/tls.crt

sudo chown seqr ../secrets/gcloud/nginx/tls.key
sudo chown seqr ../secrets/gcloud/nginx/tls.crt

mkdir -p ../secrets/gcloud/nginx-gcloud-prod
cp -v ../secrets/gcloud/nginx/tls.key ../secrets/gcloud/nginx-gcloud-prod/tls.key
cp -v ../secrets/gcloud/nginx/tls.crt ../secrets/gcloud/nginx-gcloud-prod/tls.crt

