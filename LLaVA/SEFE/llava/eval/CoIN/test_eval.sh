#!/bin/bash

# 테스트용 디렉토리 생성
mkdir -p test_output

# eval_deepseek_r1.py 테스트 실행
python eval_deepseek_r1.py \
    --annotation-file test_annotation.json \
    --result-file test_result.jsonl \
    --output-dir test_output

