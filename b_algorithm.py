from util import *
import itertools
import math
import gurobipy as gp
from gurobipy import GRB

from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, value

def solve_with_pulp(bike_bundles, walk_bundles, car_bundles, all_orders, all_riders):
    solution = []

    model = LpProblem("OGC", LpMinimize)

    I = list(range(0, len(bike_bundles)))
    J = list(range(0, len(walk_bundles)))
    K = list(range(0, len(car_bundles)))
    all_order_id = list(range(0, len(all_orders)))

    bundles = []
    for i in I:
        bundles.append(bike_bundles[i][0])
    for j in J:
        bundles.append(walk_bundles[j][0])
    for k in K:
        bundles.append(car_bundles[k][0])

    x = LpVariable.dicts("x", I, 0, 1, LpBinary)
    y = LpVariable.dicts("y", J, 0, 1, LpBinary)
    z = LpVariable.dicts("z", K, 0, 1, LpBinary)

    xyz = {i: x[i] for i in I}
    xyz.update({j + len(bike_bundles): y[j] for j in J})
    xyz.update({k + len(bike_bundles) + len(walk_bundles): z[k] for k in K})

    # Objective function
    model += lpSum((all_riders[0].fixed_cost + all_riders[0].var_cost * bike_bundles[i][2] / 100) * x[i] for i in I) + \
             lpSum((all_riders[1].fixed_cost + all_riders[1].var_cost * walk_bundles[j][2] / 100) * y[j] for j in J) + \
             lpSum((all_riders[2].fixed_cost + all_riders[2].var_cost * car_bundles[k][2] / 100) * z[k] for k in K)

    # Constraints
    model += lpSum(x[i] for i in I) <= all_riders[0].available_number
    model += lpSum(y[j] for j in J) <= all_riders[1].available_number
    model += lpSum(z[k] for k in K) <= all_riders[2].available_number

    for order in all_order_id:
        model += lpSum(xyz[i] for i, subset in enumerate(bundles) if order in subset) == 1

    # Solve the model
    model.solve()

    index_x = [i for i in I if value(x[i]) == 1]
    index_y = [j for j in J if value(y[j]) == 1]
    index_z = [k for k in K if value(z[k]) == 1]

    # Construct the solution
    for i in index_x:
        solution.append([all_riders[0].type, bike_bundles[i][0], bike_bundles[i][1]])

    for j in index_y:
        solution.append([all_riders[1].type, walk_bundles[j][0], walk_bundles[j][1]])

    for k in index_z:
        solution.append([all_riders[2].type, car_bundles[k][0], car_bundles[k][1]])

    return solution


def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):

    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat/r.speed + r.service_time)

    # A solution is a list of bundles
    solution = []

    #------------- Custom algorithm code starts from here --------------#
    
    # BIKE
    N = 3
    bnum = range(1, N+1)
    bikeOrd = {i:[] for i in bnum}

    min_dist, min_index = 0, 0

    for orders in all_orders:
        
        total_dist = []
        shop_or = []
        dlv_or = []
        
        for shop_pem in permutations([orders.id]):

            for dlv_pem in permutations([orders.id]):
                feasibility_check = test_route_feasibility(all_orders, all_riders[0], shop_pem, dlv_pem)

                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append([orders.id])
                    dlv_or.append([orders.id])

        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            bikeOrd[1].append([shop_or[min_index], dlv_or[min_index], min_dist])

    single_value = []

    for ord in bikeOrd[1]:
        single_value.append(ord[0])

    # 값이 2개인 조합을 생성
    combinations = list(itertools.combinations(single_value, 2))

    # 각 조합을 하나의 리스트로 병합
    combined_lists = [list(a + b) for a, b in combinations]

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[0], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            bikeOrd[2].append([shop_or[min_index], dlv_or[min_index], min_dist])

    combined_lists = []

    for ord1 in bikeOrd[1]:
        for ord2 in bikeOrd[2]:
            if ord1[0][0] not in ord2[0]:
                combined_lists.append(ord1[0]+ord2[0])

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[0], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            bikeOrd[3].append([shop_or[min_index], dlv_or[min_index], min_dist])

    bike_orders = bikeOrd[1] + bikeOrd[2] + bikeOrd[3]


    #WALK
    walk_order_1, walk_order_2, walk_order_3  = [], [], []
    min_dist, min_index = 0, 0

    for orders in all_orders:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations([orders.id]):
            for dlv_pem in permutations([orders.id]):
                feasibility_check = test_route_feasibility(all_orders, all_riders[1], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append([orders.id])
                    dlv_or.append([orders.id])
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            walk_order_1.append([shop_or[min_index], dlv_or[min_index], min_dist])

    single_value = []

    for ord in walk_order_1:
        single_value.append(ord[0])

    # 값이 2개인 조합을 생성
    combinations = list(itertools.combinations(single_value, 2))

    # 각 조합을 하나의 리스트로 병합
    combined_lists = [list(a + b) for a, b in combinations]

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[1], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            walk_order_2.append([shop_or[min_index], dlv_or[min_index], min_dist])

    combined_lists = []

    for ord1 in walk_order_1:
        for ord2 in walk_order_2:
            if ord1[0][0] not in ord2[0]:
                combined_lists.append(ord1[0]+ord2[0])

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[1], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            walk_order_3.append([shop_or[min_index], dlv_or[min_index], min_dist])

    walk_orders = walk_order_1 + walk_order_2 + walk_order_3


    #CAR
    car_order_1, car_order_2, car_order_3  = [], [], []
    min_dist, min_index = 0, 0

    for orders in all_orders:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations([orders.id]):
            for dlv_pem in permutations([orders.id]):
                feasibility_check = test_route_feasibility(all_orders, all_riders[2], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append([orders.id])
                    dlv_or.append([orders.id])
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            car_order_1.append([shop_or[min_index], dlv_or[min_index], min_dist])

    single_value = []

    for ord in car_order_1:
        single_value.append(ord[0])

    # 값이 2개인 조합을 생성
    combinations = list(itertools.combinations(single_value, 2))

    # 각 조합을 하나의 리스트로 병합
    combined_lists = [list(a + b) for a, b in combinations]

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[2], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            car_order_2.append([shop_or[min_index], dlv_or[min_index], min_dist])

    combined_lists = []

    for ord1 in car_order_1:
        for ord2 in car_order_2:
            if ord1[0][0] not in ord2[0]:
                combined_lists.append(ord1[0]+ord2[0])

    for orders in combined_lists:
        total_dist = []
        shop_or = []
        dlv_or = []
        for shop_pem in permutations(orders):
            for dlv_pem in permutations(orders):
                feasibility_check = test_route_feasibility(all_orders, all_riders[2], shop_pem, dlv_pem)
                if feasibility_check == 0: # feasible!
                    total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
                    shop_or.append(list(shop_pem))
                    dlv_or.append(list(dlv_pem))
        if total_dist != []:
            min_dist = min(total_dist)
            min_index = total_dist.index(min_dist)
            car_order_3.append([shop_or[min_index], dlv_or[min_index], min_dist])

    car_orders = car_order_1 + car_order_2 + car_order_3


    solution = solve_with_pulp(all_orders=all_orders,
                        all_riders=all_riders,
                        bike_bundles=bike_orders,
                        walk_bundles=walk_orders,
                        car_bundles=car_orders)


    #------------- End of custom algorithm code--------------#


    return solution

