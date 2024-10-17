#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

set -e

pushd "${SCRIPT_DIR}/terraform" 1> /dev/null
terraform init
terraform validate
terraform plan -var-file="terraform.tfvars" -out="tf.plan"

terraform -chdir="${SCRIPT_DIR}/terraform" apply "tf.plan"

popd 1> /dev/null
