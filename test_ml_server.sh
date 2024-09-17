#!/bin/bash
set -ex

curl -v -H "Content-type:application/json"  --data '{"s1":"This is a Surface Studio Laptop","s2":"That is a car"}' http://127.0.0.1:5000

