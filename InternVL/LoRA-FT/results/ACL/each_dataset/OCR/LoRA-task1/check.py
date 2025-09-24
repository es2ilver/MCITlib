import json
import argparse
from collections import Counter

def extract_ids_from_jsonl(filepath):
    """从jsonl文件中逐行提取question_id"""
    ids = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                if "question_id" in data:
                    ids.append(data["question_id"])
                else:
                    print(f"警告: {filepath} 文件第 {i} 行没有 'question_id' 字段。")
            except json.JSONDecodeError:
                print(f"警告: {filepath} 文件第 {i} 行不是有效的JSON格式。")
    return ids

def extract_ids_from_json(filepath):
    """
    从json文件中提取question_id。
    假设JSON文件的顶层结构是一个包含对象的列表，例如:
    [{"question_id": 1, ...}, {"question_id": 2, ...}]
    """
    ids = []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"错误: {filepath} 的内容不是一个JSON列表。请检查文件格式。")
                return []

            for i, item in enumerate(data, 1):
                if isinstance(item, dict) and "question_id" in item:
                    ids.append(item["question_id"])
                else:
                    print(
                        f"警告: {filepath} 文件中第 {i} 个元素没有 'question_id' 字段或格式不正确。"
                    )
        except json.JSONDecodeError:
            print(f"错误: {filepath} 文件不是有效的JSON格式。")
    return ids

def check_uniqueness(id_list, filename):
    """检查列表中的ID是否唯一"""
    print(f"--- 正在检查文件: {filename} ---")
    if not id_list:
        print("文件中没有找到任何 question_id，无法检查唯一性。")
        return False

    counts = Counter(id_list)
    duplicates = {item: count for item, count in counts.items() if count > 1}

    if not duplicates:
        print(f"✅ 成功: 文件中的 {len(id_list)} 个 question_id 全部唯一。")
        return True
    else:
        print(f"❌ 失败: 文件中发现重复的 question_id：")
        for qid, count in duplicates.items():
            print(f"  - ID: {qid}, 重复次数: {count}")
        return False

def compare_id_sets(ids1, set_name1, ids2, set_name2):
    """比较两个ID集合是否相同"""
    print("\n--- 正在比较两个文件的 question_id 集合 ---")
    set1 = set(ids1)
    set2 = set(ids2)

    if set1 == set2:
        print(f"✅ 成功: 两个文件中的 question_id 集合完全相同。")
        print(f"   总共 {len(set1)} 个唯一的ID。")
        return True
    else:
        print(f"❌ 失败: 两个文件中的 question_id 集合不相同。")

        only_in_set1 = set1 - set2
        if only_in_set1:
            print(f"\n   仅存在于 {set_name1} 中的ID ({len(only_in_set1)} 个):")
            # 打印前几个以防列表过长
            for qid in list(only_in_set1)[:10]:
                print(f"     - {qid}")
            if len(only_in_set1) > 10:
                print("     ...")

        only_in_set2 = set2 - set1
        if only_in_set2:
            print(f"\n   仅存在于 {set_name2} 中的ID ({len(only_in_set2)} 个):")
            # 打印前几个
            for qid in list(only_in_set2)[:10]:
                print(f"     - {qid}")
            if len(only_in_set2) > 10:
                print("     ...")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="检查JSON和JSONL文件中的question_id是否唯一且相互匹配。"
    )
    parser.add_argument("--jsonl_file", help="输入的JSONL文件路径")
    parser.add_argument("--json_file", help="输入的JSON文件路径")

    args = parser.parse_args()

    jsonl_filepath = args.jsonl_file
    json_filepath = args.json_file

    print(f"开始处理文件...\nJSONL文件: {jsonl_filepath}\nJSON文件:  {json_filepath}\n")

    try:
        # 1. 提取ID
        jsonl_ids = extract_ids_from_jsonl(jsonl_filepath)
        json_ids = extract_ids_from_json(json_filepath)

        # 2. 检查各自的唯一性
        check_uniqueness(jsonl_ids, jsonl_filepath)
        print("-" * 40)
        check_uniqueness(json_ids, json_filepath)

        # 3. 比较两个ID集合
        compare_id_sets(jsonl_ids, jsonl_filepath, json_ids, json_filepath)

    except FileNotFoundError as e:
        print(f"错误: 找不到文件 {e.filename}。请检查文件路径是否正确。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    main()
