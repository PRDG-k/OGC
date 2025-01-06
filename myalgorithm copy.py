from util import *
import itertools
import math
import gurobipy as gp
from gurobipy import GRB


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
    cur_ord_list = all_orders.copy()    # 내부 객체 건드리면 안됨

    # for num in bnum:

    #     for orders in cur_ord_list:

    #         total_dist = []
    #         shop_or = []
    #         dlv_or = []
            
    #         for shop_pem in permutations([orders.id]):

    #             for dlv_pem in permutations([orders.id]):
    #                 feasibility_check = test_route_feasibility(all_orders, all_riders[0], shop_pem, dlv_pem)

    #                 if feasibility_check == 0: # feasible!
    #                     total_dist.append(get_total_distance(K, dist_mat, shop_pem, dlv_pem))
    #                     shop_or.append([orders.id])
    #                     dlv_or.append([orders.id])

    #         if total_dist != []:
    #             min_dist = min(total_dist)
    #             min_index = total_dist.index(min_dist)
    #             bikeOrd[1].append([shop_or[min_index], dlv_or[min_index], min_dist])

    #     values = []

    #     for ord in bikeOrd[num]:
    #         values.append(ord[0])

        
    #     cur_ord_list = [list(a + b) for a, b in list(itertools.combinations(single_value,2))]


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



    model = gp.Model("OGC")

    I = list(range(0,len(bike_orders)))
    J = list(range(0,len(walk_orders)))
    K = list(range(0,len(car_orders)))
    all_order_id = list(range(0,len(all_orders)))

    bundles = []
    for i in I:
        bundles.append(bike_orders[i][0])
    for j in J:
        bundles.append(walk_orders[j][0])
    for k in K:
        bundles.append(car_orders[k][0])

    x = model.addVars([i for i in I], vtype=GRB.BINARY, name="x")
    y = model.addVars([j for j in J], vtype=GRB.BINARY, name="y")
    z = model.addVars([k for k in K], vtype=GRB.BINARY, name="z")

    xyz = {i: x[i] for i in I}
    xyz.update({j + len(bike_orders): y[j] for j in J})
    xyz.update({k + len(bike_orders) + len(walk_orders): z[k] for k in K})

    model.setObjective((gp.quicksum((all_riders[0].fixed_cost + all_riders[0].var_cost*bike_orders[i][2]/100)*x[i] for i in I) + gp.quicksum((all_riders[1].fixed_cost + all_riders[1].var_cost*walk_orders[j][2]/100)*y[j] for j in J) + gp.quicksum((all_riders[2].fixed_cost + all_riders[2].var_cost*car_orders[k][2]/100)*z[k] for k in K)), sense=GRB.MINIMIZE)

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
        solution.append([all_riders[0].type, bike_orders[i][0], bike_orders[i][1]])

    for i in index_y:
        solution.append([all_riders[1].type, walk_orders[i][0], walk_orders[i][1]])

    for i in index_z:
        solution.append([all_riders[2].type, car_orders[i][0], car_orders[i][1]])


    #------------- End of custom algorithm code--------------#


    return solution

