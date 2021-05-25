#!/bin/bash
# 
cd /home/mmv/mining/chia_move_plots
python move_plots.py config_ven >> logs/output.log 2>>error.log &
