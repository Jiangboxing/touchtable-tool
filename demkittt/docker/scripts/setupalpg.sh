#!/bin/sh
cd /apps/workspace/example/
git clone https://github.com/GENETX/alpg.git
cd alpg
python3 profilegenerator.py -c example -o demo --force 
cd /apps/demkit
