#!/bin/bash

echo "starting worker ..."
sudo sysctl -w vm.max_map_count=262144
python3 manage.py run_worker
