from util import *
import itertools
import math
import gurobipy as gp
from gurobipy import GRB

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


def bundling(all_orders, all_riders, K, dist_mat, rider_type, rider_type_num, max_bundle, W):
    bnum = range(max_bundle+1)

    l = range(len(all_orders))

    weight_matrix = [[0 for _ in l] for _ in l]

    memo_no_merge_order = {i:[i] for i in l}

    bundles = {i: [] for i in bnum}

    # Single-order bundle
    bundles[0] = [Bundle(
                            all_orders,
                            rider=all_riders[rider_type_num],
                            shop_seq=[i],
                            dlv_seq=[i],
                            total_volume=all_orders[i].volume,
                            total_dist=get_total_distance(K, dist_mat, [i], [i])
                            ) for i in l]

    count = 0

    while count < max_bundle:

        for bundle1 in bundles[count]:

            for idx, og_bundle in enumerate(bundles[0]):

                flag = False

                for ord in bundle1.shop_seq:
                    if idx in memo_no_merge_order[ord]:
                        flag = True
                        continue

                # for ord in bundle1.shop_seq:
                #     if ord in memo_no_merge_order[idx]:
                #         flag = True
                #         continue

                if flag:
                    continue

                new_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, og_bundle)

                # new_bundle = VRP()

                if new_bundle is not None:
                    bundles[count + 1].append(new_bundle)
                else:
                    # soft
                    # for ord in bundle1.shop_seq:
                    #     memo_no_merge_order[ord].append(idx)

                    # weight
                    for ord in bundle1.shop_seq:
                        weight_matrix[ord][idx] += W

                        if weight_matrix[ord][idx] >= 1:
                            memo_no_merge_order[ord].append(idx)
                    
                    # hard
                    # for ord in bundle1.shop_seq:
                    #     memo_no_merge_order[idx].append(ord)


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
    
    N = 3       # 최대 오더 개수: N+1
    
    bundles = {}
    weight = {}

    for idx, rider in enumerate(all_riders):
        bundles[rider.type], weight[rider.type]  = bundling( all_orders=all_orders,
                                        all_riders=all_riders,
                                        K=K,
                                        dist_mat=dist_mat,
                                        rider_type=rider.type,
                                        rider_type_num=idx,
                                        max_bundle=N,
                                        W=0.05 )
        

    # solve
    solution = solve_lp(all_orders=all_orders,
                        all_riders=all_riders,
                        bike_bundles=bundles["BIKE"],
                        walk_bundles=bundles["WALK"],
                        car_bundles=bundles["CAR"])



    #------------- End of custom algorithm code--------------#


    return solution, bundles, weight

