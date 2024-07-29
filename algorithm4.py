from util import *

def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):

    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat/r.speed + r.service_time)

    # A solution is a list of bundles
    solution = []

    #------------- Custom algorithm code starts from here --------------#
    import heapq

    car_rider = None
    for r in all_riders:
        if r.type == 'CAR':
            car_rider = r

    all_bundles = []
    uncombined_bundles = []

    for ord in all_orders:
        new_bundle = Bundle(all_orders, car_rider, [ord.id], [ord.id], ord.volume, dist_mat[ord.id, ord.id+K])
        all_bundles.append(new_bundle)
        car_rider.available_number -= 1

        uncombined_bundles.append(new_bundle)

    best_obj = sum((bundle.cost for bundle in all_bundles)) / K
    print(f'Best obj = {best_obj}')


    for bundle in all_bundles:
        new_rider = get_allcost_cheaper_riders(all_riders, bundle, bundle.rider)
        if new_rider is not None:
            old_rider = bundle.rider
            if try_bundle_rider_changing(all_orders, dist_mat, bundle, new_rider):
                old_rider.available_number += 1
                new_rider.available_number -= 1

    # 0이 아닌 값 추출
    # non_zero_elements = dist_mat[dist_mat != 0]
    # mean_dist = np.mean(non_zero_elements)

    # 평균거리 계산
    # distsum = 0
    # for k in range(K):
    #     distsum += dist_mat[k,k+K]
    # mean_dist = distsum/K
    
    # shop. dlv 거리 행렬 구성
    shop_distances = dist_mat[:K, :K]
    dlv_distances = dist_mat[K:2*K, K:2*K]

    # 파라미터
    p = 0.15
    c=K//9

    # std 먼 애들을 먼저 결합
    comp_dist_mat = []

    for o in range(K):
        sd = (np.std(heapq.nsmallest(c+1, shop_distances[o])[1:]) + np.std(heapq.nsmallest(c+1, dlv_distances[o])[1:]))/2
        comp_dist_mat.append(sd)

    indexed_comp_mat = list(enumerate((comp_dist_mat)))
    sorted_comp_mat = sorted(indexed_comp_mat,key=lambda x: x[1], reverse=True)



    # Very stupid random merge algorithm
    while True:

        iter = 0
        max_merge_iter = 1000
        
        while iter < max_merge_iter:

            while True:
                new_order = sorted_comp_mat.pop(0)
                bundle1 = find_bundle_by_id(all_bundles, new_order[0])

                bundle1_s = bundle1.shop_seq[0]
                bundle1_d = bundle1.dlv_seq[-1]

                # 가게와 배달지점 사용해 순위 매김
                combine_rank = find_ranks(np.array(shop_distances[bundle1_s]) + np.array(dlv_distances[bundle1_d]))
                
                # 가장 순위가 높은 c개의 요소와 인덱스를 튜플로 추출
                rank_c = heapq.nsmallest(c+1, enumerate(combine_rank), key=lambda x: x[1])

                # 인덱스만 추출
                rank_c_indices = [index for index, value in rank_c if value != 0]

                # 랜덤 추출
                bundle2 = find_bundle_by_id(all_bundles, random.choice(rank_c_indices))

                if bundle1 != bundle2:
                    new_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle2)
                else:
                    new_bundle = None

                if new_bundle is not None:
                    if (new_bundle.rider.calculate_cost(new_bundle.total_dist) < bundle1.rider.calculate_cost(bundle1.total_dist) + bundle2.rider.calculate_cost(bundle2.total_dist)):
                        sorted_comp_mat.append(new_order)
    
                        break
                else:
                    sorted_comp_mat.append(new_order)

                if time.time() - start_time > timelimit/(2):
                    break

            if time.time() - start_time > timelimit/(2):
                    break

            all_bundles.remove(bundle1)
            if len(bundle1.shop_seq) ==1:
                uncombined_bundles.remove(bundle1)
            bundle1.rider.available_number += 1
            
            all_bundles.remove(bundle2)
            if len(bundle2.shop_seq) ==1:
                uncombined_bundles.remove(bundle2)
            bundle2.rider.available_number += 1

            all_bundles.append(new_bundle)
            print(new_bundle)
            new_bundle.rider.available_number -= 1

            new_rider = get_allcost_cheaper_riders(all_riders, new_bundle, new_bundle.rider)
            if new_rider is not None:
                old_rider = new_bundle.rider
                if try_bundle_rider_changing(all_orders, dist_mat, new_bundle, new_rider):
                    old_rider.available_number += 1
                    new_rider.available_number -= 1

            cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
            if cur_obj < best_obj:
                best_obj = cur_obj
                print(f'Best obj = {best_obj}')

            iter += 1

            if time.time() - start_time > timelimit / (2):
                break


        cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
        if cur_obj < best_obj:
            best_obj = cur_obj
            print(f'Best obj = {best_obj}')

        while True:

            while True:
                bundle1 = select_two_bundles(uncombined_bundles)[0]

                bundle1_s = bundle1.shop_seq[0]
                bundle1_d = bundle1.dlv_seq[-1]

                # 가게와 배달지점 사용해 순위 매김
                combine_rank = find_ranks(np.array(shop_distances[bundle1_s]) + np.array(dlv_distances[bundle1_d]))
                
                # 가장 순위가 높은 c개의 요소와 인덱스를 튜플로 추출
                rank_c = heapq.nsmallest(c, enumerate(combine_rank), key=lambda x: x[1])

                # 인덱스만 추출
                rank_c_indices = [index for index, value in rank_c if value != 0]

                # 랜덤 추출
                bundle2 = find_bundle_by_id(all_bundles, random.choice(rank_c_indices))

                if bundle1 != bundle2:
                    new_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle2)
                else:
                    new_bundle = None

                if new_bundle is not None:
                    if (new_bundle.rider.calculate_cost(new_bundle.total_dist) < bundle1.rider.calculate_cost(bundle1.total_dist) + bundle2.rider.calculate_cost(bundle2.total_dist)):
                        break
                
                if time.time() - start_time > timelimit:
                    break

            if time.time() - start_time > timelimit:
                    break
            
            
            all_bundles.remove(bundle1)
            uncombined_bundles.remove(bundle1)
            bundle1.rider.available_number += 1
            
            all_bundles.remove(bundle2)
            if len(bundle2.shop_seq) ==1:
                uncombined_bundles.remove(bundle2)
            bundle2.rider.available_number += 1

            all_bundles.append(new_bundle)
            print(new_bundle)
            new_bundle.rider.available_number -= 1

            new_rider = get_allcost_cheaper_riders(all_riders, new_bundle, new_bundle.rider)
            if new_rider is not None:
                old_rider = new_bundle.rider
                if try_bundle_rider_changing(all_orders, dist_mat, new_bundle, new_rider):
                    old_rider.available_number += 1
                    new_rider.available_number -= 1

            cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
            if cur_obj < best_obj:
                best_obj = cur_obj
                print(f'Best obj = {best_obj}')



        if time.time() - start_time > timelimit:
            break


        cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
        if cur_obj < best_obj:
            best_obj = cur_obj
            print(f'Best obj = {best_obj}')
    



    # Solution is a list of bundle information
    solution = [
        # rider type, shop_seq, dlv_seq
        [bundle.rider.type, bundle.shop_seq, bundle.dlv_seq]
        for bundle in all_bundles
    ]

    #------------- End of custom algorithm code--------------#



    return solution


def get_allcost_cheaper_riders(all_riders, bundle, rider):
    for r in all_riders:
        if r.available_number > 0 and (r.calculate_cost(bundle.total_dist) < rider.calculate_cost(bundle.total_dist)):
            return r
        
    return None

# 오더 id로 번들 찾기
def find_bundle_by_id(bundle_list, target_id):
    for bundle in bundle_list:
        for id in bundle.shop_seq:
            if id == target_id:
                return bundle
    return None

def find_ranks(lst):
        # 리스트를 정렬하고 각 원소의 인덱스를 기억
        sorted_lst = sorted(lst)
        
        # 각 원소의 순위를 저장할 딕셔너리 생성
        ranks = {value: rank for rank, value in enumerate(sorted_lst, start=0)}
        
        # 원래 리스트의 각 원소에 대한 순위를 반환
        return [ranks[value] for value in lst]

def find_indices(matrix,c): #굳이 필요한 가 싶기도 하고
    # 행렬의 크기
    k = matrix.shape[0]
    
    # 결과를 저장할 새로운 행렬
    result = np.zeros((k, c), dtype=int)
    
    for i in range(k):
        # 각 행에 대해 1~10의 숫자가 저장된 인덱스를 찾음
        indices = np.where((matrix[i] >= 1) & (matrix[i] <= c))[0]
        
        # 인덱스를 결과 행렬의 i번째 행에 저장 (최대 10개)
        result[i, :len(indices)] = indices
    
    return result

def rank_dist_matrix_sd(matrix, K):
    # 가게들 간의 거리행렬 추출
    store_distances = matrix[:K, :K]
    
    # 배달지점들 간의 거리행렬 추출
    delivery_distances = matrix[K:2*K, K:2*K]
    
    shop_matrix = []
    dlv_matrix = []

    # 각 행렬의 거리들을 정렬
    for store in store_distances:
        shop_matrix.append(find_ranks(store))
    
    for dlv in delivery_distances:
        dlv_matrix.append(find_ranks(dlv))

    # 정렬된 거리행렬을 새로운 2K * 2K 행렬에 배치
    # ranked_matrix = np.zeros((2*K, 2*K))
    # ranked_matrix[:K, :K] = shop_matrix
    # ranked_matrix[K:2*K, K:2*K] = dlv_matrix
    
    # return ranked_matrix
    return shop_matrix, dlv_matrix