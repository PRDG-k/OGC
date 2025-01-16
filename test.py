from util import *
from b_algorithm import algorithm as b1
from myalgorithm import algorithm as a1
from myalgorithm_xgb import algorithm as test1


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

    alg_start_time = time.time()

    exception = None

    solution = None
    try:
        # Run algorithm!
        print(f"#----------------Start {re_file_name}----------------#")
        solution, bundles_list[re_file_name], weight_list[re_file_name] = test1(K, ALL_ORDERS, ALL_RIDERS, DIST, timelimit)
    except Exception as e:
        exception = f'{e}'
        print(traceback.format_exc())
        break


    alg_end_time = time.time()

    with open(problem_file, 'r') as f:
        prob = json.load(f)

    K = prob['K']

    ALL_ORDERS = [Order(order_info) for order_info in prob['ORDERS']]
    ALL_RIDERS = [Rider(rider_info) for rider_info in prob['RIDERS']]

    DIST = np.array(prob['DIST'])
    for r in ALL_RIDERS:
        r.T = np.round(DIST/r.speed + r.service_time)
    
    checked_solution = solution_check(K, ALL_ORDERS, ALL_RIDERS, DIST, solution)

    checked_solution['time'] = alg_end_time - alg_start_time
    checked_solution['timelimit_exception'] = (alg_end_time - alg_start_time) > timelimit + 1 # allowing additional 1 second!
    checked_solution['exception'] = exception

    checked_solution['prob_name'] = prob['name']
    checked_solution['prob_file'] = problem_file

    record.append(checked_solution)


    print(f"Alg end --{alg_end_time - alg_start_time}")
    print(f"\n\n#----------------Finished {re_file_name}----------------#\n\n")


import csv
with open("result_cur.csv", 'w', newline = '') as f:
    writer = csv.writer(f)

    writer.writerow(["prob","avg_cost","feasible","time"])

    for row in record:
        writer.writerow([row['prob_name'], row['avg_cost'], row['feasible'], row['time']])


import json
for file_name, data in weight_list.items():
    with open(os.path.join("weight", f'weight_{file_name}.json'), 'w') as json_file:
        json.dump(data, json_file, indent=4)  # indent를 사용하여 가독성을 높임