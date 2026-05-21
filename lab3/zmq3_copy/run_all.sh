#!/bin/bash

SESSION="python_jobs"
PIPENV="/home/casa/miniconda3/envs/vs2lab/bin/pipenv"

tmux new-session -d -s $SESSION

tmux send-keys -t $SESSION:0 "$PIPENV run python reducer.py 1" C-m

tmux split-window -h
tmux send-keys "$PIPENV run python reducer.py 2" C-m

tmux split-window -v
tmux send-keys "$PIPENV run python mapper.py 1" C-m

tmux select-pane -t 0
tmux split-window -v
tmux send-keys "$PIPENV run python mapper.py 2" C-m

tmux select-pane -t 1
tmux split-window -v
tmux send-keys "$PIPENV run python mapper.py 3" C-m

tmux select-pane -t 2
tmux split-window -v
tmux send-keys "$PIPENV run python splitter.py 1 input.txt" C-m

tmux attach -t $SESSION