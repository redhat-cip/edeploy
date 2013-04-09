#!/bin/bash

script="$1"
actions="$2"
level="$3"

exec > /var/tmp/policy.out.$$ 2>&1

echo "$@"

if [ $level = unknown ]; then
   exit 101
else
   exit 0
fi
