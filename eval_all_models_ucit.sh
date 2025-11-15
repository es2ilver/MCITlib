#!/bin/bash

# 통합 평가 스크립트: O-LoRA, HiDe-LLaVA, SEFE, DISCO 모델에 대한 UCIT benchmark 평가
# Task 1~6 평가를 각 모델에 대해 진행

# 오류 발생 시 즉시 스크립트 종료
set -e

HARD_PATH="/home/data/vgilab/jeongeun/MCITlib"
GPU_LIST="4,5,6,7"

# 로그 파일 경로 설정
LOG_DIR="$HARD_PATH/logs/eval_ucit"
mkdir -p "$LOG_DIR"

# 타임스탬프 생성
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/eval_all_models_${TIMESTAMP}.log"

# GPU 설정
export CUDA_VISIBLE_DEVICES=$GPU_LIST

# 로그 파일에 시작 정보 기록 (화면 출력과 동시에)
{
    echo "=========================================="
    echo "UCIT Benchmark 평가 시작"
    echo "GPU: $GPU_LIST"
    echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "로그 파일: $LOG_FILE"
    echo "=========================================="
} | tee -a "$LOG_FILE"


# 모델 리스트
MODELS=("OLoRA" "HiDe" "SEFE" "DISCO")

# Task 리스트
TASKS=(1 2 3 4 5 6)

# 각 모델에 대해 평가 진행
for MODEL in "${MODELS[@]}"; do
    {
        echo ""
        echo "=========================================="
        echo "모델: $MODEL 평가 시작"
        echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=========================================="
    } | tee -a "$LOG_FILE"
    
    # 모델별 디렉토리 경로
    MODEL_DIR="$HARD_PATH/LLaVA/$MODEL"
    EVAL_SCRIPT="$MODEL_DIR/scripts/MCITlib/Eval_UCIT/Eval_finetune1.sh"
    
    # 스크립트 존재 확인
    if [ ! -f "$EVAL_SCRIPT" ]; then
        echo "경고: $EVAL_SCRIPT 파일을 찾을 수 없습니다. 건너뜁니다." | tee -a "$LOG_FILE"
        continue
    fi
    
    # 모델 디렉토리로 이동하여 pip install -e . 실행 (한 번만)
    {
        echo "모델: $MODEL 패키지 설치 중..."
        echo "설치 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    } | tee -a "$LOG_FILE"
    
    cd "$MODEL_DIR"
    pip install -e . 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✓ 모델: $MODEL 패키지 설치 완료" | tee -a "$LOG_FILE"
    else
        echo "✗ 모델: $MODEL 패키지 설치 실패" | tee -a "$LOG_FILE"
        cd "$HARD_PATH"
        continue
    fi
    
    cd "$HARD_PATH"
    
    # 각 Task에 대해 평가 진행
    for TASK in "${TASKS[@]}"; do
        {
            echo ""
            echo "----------------------------------------"
            echo "모델: $MODEL, Task: $TASK 평가 시작"
            echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "----------------------------------------"
        } | tee -a "$LOG_FILE"
        
        # 모델 디렉토리로 이동하여 평가 실행
        cd "$MODEL_DIR"
        
        # GPU 설정을 환경변수로 전달
        export CUDA_VISIBLE_DEVICES=$GPU_LIST
        
        # 평가 스크립트 실행 (로그 파일에 저장)
        bash "$EVAL_SCRIPT" "$TASK" 2>&1 | tee -a "$LOG_FILE"
        
        # 실행 결과 확인
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo "✓ 모델: $MODEL, Task: $TASK 평가 완료 ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOG_FILE"
        else
            echo "✗ 모델: $MODEL, Task: $TASK 평가 실패 ($(date '+%Y-%m-%d %H:%M:%S'))" | tee -a "$LOG_FILE"
        fi
        
        # 원래 디렉토리로 복귀
        cd "$HARD_PATH"
    done
    
    {
        echo ""
        echo "=========================================="
        echo "모델: $MODEL 평가 완료"
        echo "완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=========================================="
    } | tee -a "$LOG_FILE"
done

{
    echo ""
    echo "=========================================="
    echo "모든 모델 평가 완료"
    echo "완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "로그 파일: $LOG_FILE"
    echo "=========================================="
} | tee -a "$LOG_FILE"

