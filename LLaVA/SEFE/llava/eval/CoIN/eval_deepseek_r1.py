import os
import argparse
import json
import re
import time
from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError, APITimeoutError
from multiprocessing import Pool, cpu_count


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation-file', type=str, default='./LLaVA/cl_dataset/TextVQA/TextVQA_0.5.1_val.json')
    parser.add_argument('--result-file', type=str, default='./LLaVA/results/Instructions/TextVQA/Zero_shot/merge.jsonl')
    parser.add_argument('--output-dir', type=str)
    return parser.parse_args()

def prompt_processor(prompt):
    if prompt.startswith('OCR tokens:'):
        pattern = r"Question: (.*?) Short answer:"
        match = re.search(pattern, prompt, re.DOTALL)
        question = match.group(1)
    elif 'Reference OCR token:' in prompt and len(prompt.split('\n')) == 3:
        if prompt.startswith('Reference OCR token:'):
            question = prompt.split('\n')[1]
        else:
            question = prompt.split('\n')[0]
    elif len(prompt.split('\n')) == 2:
        question = prompt.split('\n')[0]
    else:
        assert False

    return question.lower()


def eval_single(annotation_file, result_file):
    annotations = json.load(open(annotation_file))
    annotations = {annotation['question_id']: annotation for annotation in annotations}
    results = [json.loads(line) for line in open(result_file)]

    total = len(results)
    right = 0
    answer_gt_file = []
    for result in results:
        annotation = annotations[result['question_id']]
        pred = result['text']
        ground_truth = annotation['answer']
        if pred.upper() == ground_truth.upper():
            right += 1
        answer_gt_file.append({
        "pred": pred,
        "ground_truth": ground_truth
        })
        # if ground_truth.upper() in pred.upper():
        #     right += 1
    ans_gt_file = os.path.join(args.output_dir, 'ans_gt.json')
    with open(ans_gt_file, "w", encoding="utf-8") as f:
        json.dump(answer_gt_file, f, ensure_ascii=False, indent=4)

    print('Samples: {}\nAccuracy: {:.2f}%\n'.format(total, 100. * right / total))
    #将结果写入文件
    if args.output_dir is not None:
        output_file = os.path.join(args.output_dir, 'Result.text')
        with open(output_file, 'w') as f:
            f.write('Samples: {}\nAccuracy: {:.2f}%\n'.format(total, 100. * right / total))

    return ans_gt_file

def process_batch(api_key, batch, max_retries=5):
    user_text = (
        "You are an expert evaluator assessing the semantic similarity between model-generated responses and ground truth answers. "
        "For each pair, provide a similarity score between 0 and 10 based on meaning, where 10 means the two responses are identical in meaning, "
        "and 0 means they are completely unrelated. Use the format 'Score: X' for each pair without explanations."
        "\n\nPairs:\n" +
        "\n".join([f"{i+1}. Model Response: {item['pred']}\n   Ground Truth: {item['ground_truth']}" for i, item in enumerate(batch)])
    )

    client = OpenAI(api_key=api_key)

    for attempt in range(max_retries):
        try:
            resp = client.responses.create(
                model="gpt-4o-mini",  # or gpt-4o
                input=[{
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_text}]
                }],
                instructions="You are an AI assistant evaluating the semantic similarity of responses.",
            )
            # 안정적으로 텍스트 추출
            if hasattr(resp, "output") and resp.output:
                evaluation_text = resp.output[0].content[0].text
            else:
                evaluation_text = resp.choices[0].message.content
            break  # 성공 시 루프 탈출

        except (APIError, RateLimitError, APIConnectionError, APITimeoutError) as e:
            wait_time = 2 ** attempt  # exponential backoff
            print(f"[Retry {attempt+1}/{max_retries}] Error: {type(e).__name__} - waiting {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"[Fatal Error] {str(e)}")
            return 0.0, len(batch)
    else:
        # 모든 재시도 실패
        print(f"[Batch Failed] after {max_retries} attempts.")
        return 0.0, len(batch)

    # 점수 추출
    scores = []
    for line in evaluation_text.splitlines():
        if "Score:" in line:
            try:
                score = float(line.split(":")[1].strip())
                scores.append(score)
            except Exception:
                continue

    average_score = sum(scores) / len(scores) if scores else 0
    return average_score, len(batch)


def deepseek_chat_final(api_key, path, batch_size=10):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
    num_batches = len(batches)

    print(f"Total data: {len(data)}, Total batches: {num_batches}, Batch size: {batch_size}")

    total_score = 0
    total_samples = 0

    with Pool(cpu_count()) as pool:
        results = pool.starmap(
            process_batch, [(api_key, batch) for batch in batches]
        )

        for batch_score, batch_total in results:
            total_score += batch_score * batch_total  # 还原该批次总分 
            total_samples += batch_total 

    overall_average_score = total_score / total_samples if total_samples > 0 else 0
    return overall_average_score
    

if __name__ == "__main__":
    args = get_args()

    if args.result_file is not None:
        ans_gt_file = eval_single(args.annotation_file, args.result_file)

        secrets_path = os.path.expanduser("/home/data/vgilab/jeongeun/.secrets.json")
        api_key = json.load(open(secrets_path))['api_key']

        if not api_key:
            raise ValueError("API key not found in secrets.json")

        batch_size = 2 
        overall_accuracy = deepseek_chat_final(api_key, ans_gt_file, batch_size=batch_size)
        print(f"Overall Accuracy: {overall_accuracy*10:.2f}")
        if args.output_dir is not None:
            output_file = os.path.join(args.output_dir, 'Result_api.text')
            with open(output_file, 'w') as f:
                f.write('Accuracy: {:.2f}%\n'.format(overall_accuracy*10))
