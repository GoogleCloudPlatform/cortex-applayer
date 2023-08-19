PROJECT=${1}
LOCATION=${2}
ML_DATASET=${3}
REPORTING_DS=${4}
SVC_EP=${5}

echo "project is  ${PROJECT}"

# export GOOGLE_APPLICATION_CREDENTIALS="/usr/local/google/home/stabby/delete.json"
# export DAL_SVC="http://localhost:8080"
# export PBOUT_SVC="http://localhost:8082"
### npm start <<the DAL>>
### export PB_OUT_NAME="cortex-kmeans-clustering"
### npm start <<pubsub out>>
### npm start the listener - run this


cat <<EOF >data.json
{
  "project": "${PROJECT}",
  "location" : "${LOCATION}",
  "ml_dataset" : "${ML_DATASET}",
  "reporting_dataset" : "${REPORTING_DS}"
}
EOF

curl --header "Content-Type: application/json" --data @data.json "${SVC_EP)"