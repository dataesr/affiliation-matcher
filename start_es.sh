#!/bin/bash

echo "starting ES and setting vm.max_map_count"
sudo sysctl -w vm.max_map_count=262144
