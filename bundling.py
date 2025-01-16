from util import *
from myalgorithm import algorithm as a1

import os
import traceback

# prob_dir = "alg_test_problems"
prob_dir = "stage1_problems"

problem_list = os.listdir(prob_dir)

timelimit = 60

record = []
weight_list = {}
bundles_list = {}

for file_name in problem_list:

    problem_file = os.path.join(prob_dir, file_name)
    re_file_name = file_name[:-5]

    with open(problem_file, 'r') as f:
        prob = json.load(f)

    K = prob['K']

    ALL_ORDERS = [Order(order_info) for order_info in prob['ORDERS']]
    ALL_RIDERS = [Rider(rider_info) for rider_info in prob['RIDERS']]

    DIST = np.array(prob['DIST'])
    for r in ALL_RIDERS:
        r.T = np.round(DIST/r.speed + r.service_time)

    exception = None

    solution = None
    try:
        # Run algorithm!
        print(f"#----------------Start {re_file_name}----------------#")
        solution, bundles_list[re_file_name], weight_list[re_file_name] = a1(K, ALL_ORDERS, ALL_RIDERS, DIST, timelimit)
    except Exception as e:
        exception = f'{e}'
        print(traceback.format_exc())
        break


import json
for file_name, data in weight_list.items():
    with open(os.path.join("weight", f'weight_{file_name}.json'), 'w') as json_file:
        json.dump(data, json_file, indent=4)  # indent를 사용하여 가독성을 높임


# 알고리즘 실행 후 선택된 번들이 필요함...
# for file_name, data in bundles_list.items():
#     with open(os.path.join("bundle", f'bundle_{file_name}.json'), 'w') as json_file:
#         json.dump(data, json_file, indent=4)  # indent를 사용하여 가독성을 높임