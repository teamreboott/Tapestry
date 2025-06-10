import json
import glob

path = glob.glob("/home/jaeyoung/jy_workspace/web-agent/benchmark/simpleqa_results_claude3.7/*.json")
total_num = len(path)
correct_num = 0
for p in path:
    with open(p, "r") as f:
        data = json.load(f)
        grade = data['grade']
        if grade == 'A':
            correct_num += 1
        else:
            print(p)
            print(data['promblem'])
            print(data['answer'])
            print(data['predicted_answer'])
            print(data['grade'])
            print("--------------------------------")

accuracy = correct_num / total_num * 100
print(f"accuracy: {accuracy:.2f}%")
