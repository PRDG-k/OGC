from util import *
import itertools
import math
import gurobipy as gp
from gurobipy import GRB
import pickle
import xgboost as xgb
import pandas as pd

from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, value, PULP_CBC_CMD

def solve_with_pulp(bike_bundles, walk_bundles, car_bundles, all_orders, all_riders):
    solution = []

    model = LpProblem("OGC", LpMinimize)

    I = list(range(0, len(bike_bundles)))
    J = list(range(0, len(walk_bundles)))
    K = list(range(0, len(car_bundles)))
    all_order_id = list(range(0, len(all_orders)))

    bundles = []
    for i in I:
        bundles.append(bike_bundles[i].shop_seq)
    for j in J:
        bundles.append(walk_bundles[j].shop_seq)
    for k in K:
        bundles.append(car_bundles[k].shop_seq)

    x = LpVariable.dicts("x", I, 0, 1, LpBinary)
    y = LpVariable.dicts("y", J, 0, 1, LpBinary)
    z = LpVariable.dicts("z", K, 0, 1, LpBinary)

    xyz = {i: x[i] for i in I}
    xyz.update({j + len(bike_bundles): y[j] for j in J})
    xyz.update({k + len(bike_bundles) + len(walk_bundles): z[k] for k in K})

    # Objective function
    model += lpSum((all_riders[0].fixed_cost + all_riders[0].var_cost * bike_bundles[i].total_dist / 100) * x[i] for i in I) + \
             lpSum((all_riders[1].fixed_cost + all_riders[1].var_cost * walk_bundles[j].total_dist / 100) * y[j] for j in J) + \
             lpSum((all_riders[2].fixed_cost + all_riders[2].var_cost * car_bundles[k].total_dist / 100) * z[k] for k in K)

    # Constraints
    model += lpSum(x[i] for i in I) <= all_riders[0].available_number
    model += lpSum(y[j] for j in J) <= all_riders[1].available_number
    model += lpSum(z[k] for k in K) <= all_riders[2].available_number

    for order in all_order_id:
        model += lpSum(xyz[i] for i, subset in enumerate(bundles) if order in subset) == 1

    # Solve the model
    model.solve(PULP_CBC_CMD(msg=True))

    index_x = [i for i in I if value(x[i]) == 1]
    index_y = [j for j in J if value(y[j]) == 1]
    index_z = [k for k in K if value(z[k]) == 1]

    # Construct the solution
    for i in index_x:
        solution.append([all_riders[0].type, bike_bundles[i].shop_seq, bike_bundles[i].dlv_seq])

    for j in index_y:
        solution.append([all_riders[1].type, walk_bundles[j].shop_seq, walk_bundles[j].dlv_seq])

    for k in index_z:
        solution.append([all_riders[2].type, car_bundles[k].shop_seq, car_bundles[k].dlv_seq])

    return solution


def solve_lp(all_orders, all_riders, bike_bundles, walk_bundles, car_bundles):
    
    solution = []

    model = gp.Model("OGC")


    I = list(range(0,len(bike_bundles)))
    J = list(range(0,len(walk_bundles)))
    K = list(range(0,len(car_bundles)))
    all_order_id = list(range(0,len(all_orders)))

    bundles = []
    for i in I:
        bundles.append(bike_bundles[i].shop_seq)
    for j in J:
        bundles.append(walk_bundles[j].shop_seq)
    for k in K:
        bundles.append(car_bundles[k].shop_seq)

    x = model.addVars([i for i in I], vtype=GRB.BINARY, name="x")
    y = model.addVars([j for j in J], vtype=GRB.BINARY, name="y")
    z = model.addVars([k for k in K], vtype=GRB.BINARY, name="z")

    xyz = {i: x[i] for i in I}
    xyz.update({j + len(bike_bundles): y[j] for j in J})
    xyz.update({k + len(bike_bundles) + len(walk_bundles): z[k] for k in K})

    model.setObjective((gp.quicksum((all_riders[0].fixed_cost + all_riders[0].var_cost*bike_bundles[i].total_dist/100)*x[i] for i in I) +
                         gp.quicksum((all_riders[1].fixed_cost + all_riders[1].var_cost*walk_bundles[j].total_dist/100)*y[j] for j in J) +
                           gp.quicksum((all_riders[2].fixed_cost + all_riders[2].var_cost*car_bundles[k].total_dist/100)*z[k] for k in K)),
                             sense=GRB.MINIMIZE)

    model.addConstr(gp.quicksum(x[i] for i in I) <= all_riders[0].available_number)
    model.addConstr(gp.quicksum(y[j] for j in J) <= all_riders[1].available_number)
    model.addConstr(gp.quicksum(z[k] for k in K) <= all_riders[2].available_number)

    for order in all_order_id:
        model.addConstr(gp.quicksum(xyz[i] for i, subset in enumerate(bundles) if order in subset) == 1)

    model.optimize()

    index_x = []
    for i in I:
        if x[i].X ==1:
            index_x.append(i)

    index_y = []
    for i in J:
        if y[i].X ==1:
            index_y.append(i)

    index_z = []
    for i in K:
        if z[i].X ==1:
            index_z.append(i)


    # Solution is a list of bundle information
    for i in index_x:
        solution.append([all_riders[0].type, bike_bundles[i].shop_seq, bike_bundles[i].dlv_seq])

    for i in index_y:
        solution.append([all_riders[1].type, walk_bundles[i].shop_seq, walk_bundles[i].dlv_seq])

    for i in index_z:
        solution.append([all_riders[2].type, car_bundles[i].shop_seq, car_bundles[i].dlv_seq])

    return solution
        

def test_deadline(all_orders, rider, shop_seq, dlv_seq):
    pickup_times, dlv_times = get_pd_times(all_orders, rider, shop_seq, dlv_seq)

    for k, dlv_time in dlv_times.items():
        return all_orders[k].deadline - dlv_time
    

def bundling(all_orders, all_riders, K, dist_mat, rider_type, rider_type_num, max_bundle, W):
    xgb_model = pickle.load(open('xgb_v_t.model', 'rb'))

    # init weight
    volume_array = []
    tw_array = []

    for order1 in all_orders:
        for order2 in all_orders:
            volume_array.append(
                all_riders[rider_type_num].capa - (order1.volume + order2.volume)
                )

            merged_orders = [order1.id, order2.id]
            max_gap = -100000
            for shop_pem in permutations(merged_orders):
                for dlv_pem in permutations(merged_orders):
                    gap = test_deadline(
                        all_orders, all_riders[rider_type_num], shop_pem, dlv_pem
                        )

                    if gap > max_gap:
                        max_gap = gap
                    
            tw_array.append(max_gap)
    
    model_input = xgb.DMatrix(pd.DataFrame({'vol': volume_array, 'tw': tw_array }))
    
    pred_weight = xgb_model.predict(model_input)


    bnum = range(max_bundle+1)

    l = range(len(all_orders))

    # weight_matrix = [[0 for _ in l] for _ in l]
    pred_weight = pred_weight / 2
    weight_matrix = pred_weight.reshape(len(all_orders), len(all_orders)).tolist()

    memo_no_merge_order = {i:[i] for i in l}

    bundles = {i: [] for i in bnum}

    # Single-order bundle -> feasible check needed
    bundles[0] = [
                    Bundle(
                            all_orders,
                            rider=all_riders[rider_type_num],
                            shop_seq=[i],
                            dlv_seq=[i],
                            total_volume=all_orders[i].volume,
                            total_dist=get_total_distance(K, dist_mat, [i], [i]),
                            # feasible=assign_booltype_feasibility(test_route_feasibility(all_orders, all_riders[rider_type_num], [i], [i]))
                            ) for i in l if test_route_feasibility(all_orders, all_riders[rider_type_num], [i], [i]) == 0
                    ]

    count = 0

    while count < max_bundle:

        for bundle1 in bundles[count]:

            for og_bundle in bundles[0]:
                ord_id = og_bundle.shop_seq[0]

                if og_bundle.feasible != True:
                    continue

                flag = False

                for ord in bundle1.shop_seq:
                    if ord_id in memo_no_merge_order[ord]:
                        flag = True
                        break

                if flag:
                    continue

                new_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, og_bundle)

                # new_bundle = VRP()

                if new_bundle is not None:
                    bundles[count + 1].append(new_bundle)

                    # for ord in bundle1.shop_seq:
                    #     if weight_matrix[ord][ord_id] > 0:
                    #         weight_matrix[ord][ord_id] -= W
                else:

                    # weight
                    for ord in bundle1.shop_seq:
                        if count == 0:
                            weight_matrix[ord][ord_id] = 1
                            weight_matrix[ord_id][ord] = 1

                            memo_no_merge_order[ord].append(ord_id)
                            memo_no_merge_order[ord_id].append(ord)

                        else:
                            weight_matrix[ord][ord_id] += W

                            if weight_matrix[ord][ord_id] >= 1:
                                memo_no_merge_order[ord].append(ord_id)


        count += 1
        
    for key in bundles.keys():
        print(f"Length of {rider_type}-bundle {key+1}-orders: {len(bundles[key])}")
        

    # Result Export
    bundling_result = []
    for bundle in bundles.values():
        bundling_result += bundle

    return bundling_result, weight_matrix


def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):
    
    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat/r.speed + r.service_time)

    # A solution is a list of bundles
    solution = []

    #------------- Custom algorithm code starts from here --------------#
    
    N = 4       # 최대 오더 개수: N+1
    
    bundles = {}
    weight = {}

    for idx, rider in enumerate(all_riders):
        bundles[rider.type], weight[rider.type] = bundling( all_orders=all_orders,
                                        all_riders=all_riders,
                                        K=K,
                                        dist_mat=dist_mat,
                                        rider_type=rider.type,
                                        rider_type_num=idx,
                                        max_bundle=N,
                                        W=0.1 )
        

    # solve
    # solution = solve_lp(all_orders=all_orders,
    #                     all_riders=all_riders,
    #                     bike_bundles=bundles["BIKE"],
    #                     walk_bundles=bundles["WALK"],
    #                     car_bundles=bundles["CAR"])

    # solve with pulp fuck gurobipy
    solution = solve_with_pulp(all_orders=all_orders,
                        all_riders=all_riders,
                        bike_bundles=bundles["BIKE"],
                        walk_bundles=bundles["WALK"],
                        car_bundles=bundles["CAR"])

    #------------- End of custom algorithm code--------------#


    return solution, bundles, weight

