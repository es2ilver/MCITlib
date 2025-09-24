#!/bin/bash

HARD_PATH=/mnt/haiyangguo/mywork/CL-MLLM/MCITlib_v2

pip install -e .
bash scripts/MCITlib/Train/Task1.sh \
    $HARD_PATH/configs/modal_configs/llava.json \
    $HARD_PATH/configs/data_configs/MLLM-ACL/OCR.json \
    $HARD_PATH/configs/train_configs/ModalPrompt/LLaVA/MLLM-ACL/train/task1.json

pip install -e .
bash scripts/MCITlib/Train/Taskn.sh \
    $HARD_PATH/configs/modal_configs/llava.json \
    $HARD_PATH/configs/data_configs/MLLM-ACL/Math.json \
    $HARD_PATH/configs/train_configs/ModalPrompt/LLaVA/MLLM-ACL/train/task2.json

pip install -e .
bash scripts/MCITlib/Train/Taskn.sh \
    $HARD_PATH/configs/modal_configs/llava.json \
    $HARD_PATH/configs/data_configs/MLLM-ACL/VP.json \
    $HARD_PATH/configs/train_configs/ModalPrompt/LLaVA/MLLM-ACL/train/task3.json

pip install -e .
bash scripts/MCITlib/Train/Taskn.sh \
    $HARD_PATH/configs/modal_configs/llava.json \
    $HARD_PATH/configs/data_configs/MLLM-ACL/APP.json \
    $HARD_PATH/configs/train_configs/ModalPrompt/LLaVA/MLLM-ACL/train/task4.json