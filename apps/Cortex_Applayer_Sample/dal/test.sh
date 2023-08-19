
PROJECT=${1}
LOCATION=${2}
ML_DATASET=${3}
REPORTING_DS=${4}

cat <<EOF >data.json
{
  "project": "${PROJECT}",
  "location" : "${LOCATION}",
  "ml_dataset" : "${ML_DATASET}",
  "reporting_dataset" : "${REPORTING_DS}"
}
EOF

curl --header "Content-Type: application/json" --data @data.json http://localhost:8080