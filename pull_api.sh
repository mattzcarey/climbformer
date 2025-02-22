#!/bin/bash

DATABASES=(
  "aurora"
  "decoy"
  "grasshopper"
  "kilter"
  "soill"
  "tension"
  "touchstone"
)

for db in "${DATABASES[@]}"; do
  echo "Processing database: $db"
  uv run boardlib database "$db" "./db/$db.db"
done
