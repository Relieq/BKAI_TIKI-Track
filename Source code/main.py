# Đọc dữ liệu từ file hoặc stdin
def read_input():
    N = int(input().split()[1])  # Points N
    distances = {}
    input_line = input().split()
    while input_line[0] != 'DISTANCES':
        input_line = input().split()
    num_distances = int(input_line[1])

    for _ in range(num_distances):
        i, j, d = map(int, input().split())
        if i not in distances:
            distances[i] = {}
        distances[i][j] = d

    # Đọc thông tin rơ mooc
    trailer_info = input().split()
    while trailer_info[0] != 'TRAILER':
        trailer_info = input().split()
    trailer_location = int(trailer_info[1])
    trailer_attach_time = int(trailer_info[2])

    # Đọc thông tin đầu kéo
    truck_info = input().split()
    while truck_info[0] != 'TRUCK':
        truck_info = input().split()
    m = int(truck_info[1])
    trucks = {}
    for _ in range(m):
        truck_id, location = map(int, input().split())
        trucks[truck_id] = {
            'location': location,
            'capacity': 2,  # Sức chứa tính theo đơn vị container 20ft
            'route': [],
            'load': 0,
            'time': 0,
        }

    # Đọc yêu cầu vận chuyển
    requests = {}
    line = input()
    while line.strip() != '#':
        if line.startswith('REQ'):
            parts = line.strip().split()
            req_id = int(parts[1])
            size = int(parts[2])
            p1 = int(parts[3])
            pickup_action = parts[4]
            pickup_duration = int(parts[5])
            p2 = int(parts[6])
            drop_action = parts[7]
            drop_duration = int(parts[8])
            requests[req_id] = {
                'size': size,
                'pickup_point': p1,
                'pickup_action': pickup_action,
                'pickup_duration': pickup_duration,
                'drop_point': p2,
                'drop_action': drop_action,
                'drop_duration': drop_duration,
                'assigned': False,
            }
        line = input()

    return N, distances, trailer_location, trailer_attach_time, trucks, requests

# Sắp xếp yêu cầu theo thứ tự ưu tiên
def sort_requests(requests):
    # Yêu cầu có hành động PICKUP_CONTAINER_TRAILER ưu tiên trước
    def priority(req):
        if req['pickup_action'] == 'PICKUP_CONTAINER_TRAILER':
            return 0
        else:
            return 1
    return sorted(requests, key=lambda req_id: priority(requests[req_id]))

def assign_requests(trucks, requests, distances, trailer_location, trailer_attach_time):
    unassigned_requests = sort_requests(requests)

    # Khởi tạo trạng thái cho các đầu kéo
    for truck_id in trucks:
        truck = trucks[truck_id]
        truck['route'] = []
        truck['time'] = 0
        truck['current_location'] = truck['location']
        truck['has_trailer'] = False
        truck['trailer_load'] = 0  # Tải trọng trên rơ mooc

    # Lặp cho đến khi tất cả các yêu cầu được gán
    while unassigned_requests:
        assigned = False
        for req_id in unassigned_requests:
            req = requests[req_id]
            required_capacity = 1 if req['size'] == 20 else 2

            # Tìm đầu kéo phù hợp nhất để phục vụ yêu cầu này
            best_truck_id = None
            min_completion_time = float('inf')
            best_actions = None

            for truck_id in trucks:
                truck = trucks[truck_id]

                # Tạo bản sao trạng thái đầu kéo để thử nghiệm
                temp_truck = {
                    'route': truck['route'][:],
                    'time': truck['time'],
                    'current_location': truck['current_location'],
                    'has_trailer': truck['has_trailer'],
                    'trailer_load': truck['trailer_load']
                }

                actions = []

                # Xác định xem đầu kéo có thể thực hiện yêu cầu này không
                if req['pickup_action'] == 'PICKUP_CONTAINER_TRAILER':
                    # Cần đầu kéo không có rơ mooc
                    if temp_truck['has_trailer']:
                        continue
                    # Đi đến điểm lấy và gắn rơ mooc có container
                    actions.append({
                        'point': req['pickup_point'],
                        'action': 'PICKUP_CONTAINER_TRAILER',
                        'request_id': req_id
                    })
                    travel_time = distances[temp_truck['current_location']][req['pickup_point']]
                    temp_truck['time'] += travel_time + req['pickup_duration']
                    temp_truck['current_location'] = req['pickup_point']
                    temp_truck['has_trailer'] = True
                    temp_truck['trailer_load'] = required_capacity
                else:
                    # Cần đầu kéo có rơ mooc
                    if not temp_truck['has_trailer']:
                        # Đi lấy rơ mooc
                        actions.append({
                            'point': trailer_location,
                            'action': 'PICKUP_TRAILER',
                            'request_id': None
                        })
                        travel_time = distances[temp_truck['current_location']][trailer_location]
                        temp_truck['time'] += travel_time + trailer_attach_time
                        temp_truck['current_location'] = trailer_location
                        temp_truck['has_trailer'] = True
                        temp_truck['trailer_load'] = 0
                    # Kiểm tra sức chứa
                    if temp_truck['trailer_load'] + required_capacity > 2:
                        continue
                    # Đi đến điểm lấy container
                    actions.append({
                        'point': req['pickup_point'],
                        'action': req['pickup_action'],
                        'request_id': req_id
                    })
                    travel_time = distances[temp_truck['current_location']][req['pickup_point']]
                    temp_truck['time'] += travel_time + req['pickup_duration']
                    temp_truck['current_location'] = req['pickup_point']
                    temp_truck['trailer_load'] += required_capacity

                # Đi đến điểm hạ container
                actions.append({
                    'point': req['drop_point'],
                    'action': req['drop_action'],
                    'request_id': req_id
                })
                travel_time = distances[temp_truck['current_location']][req['drop_point']]
                temp_truck['time'] += travel_time + req['drop_duration']
                temp_truck['current_location'] = req['drop_point']

                # Cập nhật trạng thái sau khi hạ container
                if req['drop_action'] == 'DROP_CONTAINER_TRAILER':
                    temp_truck['has_trailer'] = False
                    temp_truck['trailer_load'] = 0
                else:
                    temp_truck['trailer_load'] -= required_capacity

                # Kiểm tra xem đầu kéo có vượt quá sức chứa không
                if temp_truck['trailer_load'] < 0 or temp_truck['trailer_load'] > 2:
                    continue  # Vi phạm sức chứa

                # Thời gian hoàn thành dự kiến
                completion_time = temp_truck['time']
                if completion_time < min_completion_time:
                    min_completion_time = completion_time
                    best_truck_id = truck_id
                    best_actions = actions
                    best_temp_truck = temp_truck

            if best_truck_id is not None:
                # Gán yêu cầu cho đầu kéo tốt nhất
                truck = trucks[best_truck_id]
                truck['route'].extend(best_actions)
                truck['time'] = best_temp_truck['time']
                truck['current_location'] = best_temp_truck['current_location']
                truck['has_trailer'] = best_temp_truck['has_trailer']
                truck['trailer_load'] = best_temp_truck['trailer_load']
                requests[req_id]['assigned'] = True
                unassigned_requests.remove(req_id)
                assigned = True
                break  # Gán thành công, bắt đầu lại từ đầu

        if not assigned:
            # Không thể gán yêu cầu nào trong vòng lặp này
            print("Không thể gán các yêu cầu còn lại.")
            break

    # Hoàn thành lộ trình cho các đầu kéo
    for truck_id in trucks:
        truck = trucks[truck_id]
        if truck['has_trailer']:
            # Trả rơ mooc
            truck['route'].append({
                'point': trailer_location,
                'action': 'DROP_TRAILER',
                'request_id': None
            })
            travel_time = distances[truck['current_location']][trailer_location]
            truck['time'] += travel_time + trailer_attach_time
            truck['current_location'] = trailer_location
            truck['has_trailer'] = False
            truck['trailer_load'] = 0

        # Quay về bãi
        truck['route'].append({
            'point': truck['location'],
            'action': 'STOP',
            'request_id': None
        })
        travel_time = distances[truck['current_location']][truck['location']]
        truck['time'] += travel_time
        truck['current_location'] = truck['location']

def calculate_objective(trucks, distances):
    F1 = 0  # Makespan
    F2 = 0  # Tổng thời gian di chuyển
    for truck_id in trucks:
        truck = trucks[truck_id]
        F1 = max(F1, truck['time'])
        # Tính tổng thời gian di chuyển
        total_distance = 0
        route = truck['route']
        prev_point = truck['location']
        for step in route:
            point = step['point']
            total_distance += distances[prev_point][point]
            prev_point = point
        F2 += total_distance
    return F1, F2

def output_result(trucks):
    print(f'ROUTES {len(trucks)}')
    for truck_id in trucks:
        truck = trucks[truck_id]
        print(f'TRUCK {truck_id}')
        for step in truck['route']:
            point = step['point']
            action = step['action']
            if step['request_id'] is not None:
                request_id = step['request_id']
                print(f'{point} {action} {request_id}')
            else:
                print(f'{point} {action}')
        print('#')

def calculate_truck_time(truck, distances):
    total_time = 0
    prev_point = truck['location']
    for step in truck['route']:
        point = step['point']
        action = step['action']
        total_time += distances[prev_point][point]
        if action == 'PICKUP_TRAILER' or action == 'DROP_TRAILER':
            total_time += trailer_attach_time
        elif action in ['PICKUP_CONTAINER', 'DROP_CONTAINER', 'PICKUP_CONTAINER_TRAILER', 'DROP_CONTAINER_TRAILER']:
            request_id = step['request_id']
            req = requests[request_id]
            if action == req['pickup_action']:
                total_time += req['pickup_duration']
            elif action == req['drop_action']:
                total_time += req['drop_duration']
        prev_point = point
    return total_time

def is_feasible(truck, req, action, capacities):
    # Kiểm tra sức chứa
    required_capacity = 1 if req['size'] == 20 else 2
    if action == 'add':
        if truck['load'] + required_capacity > capacities:
            return False
    elif action == 'remove':
        if truck['load'] - required_capacity < 0:
            return False
    return True

def update_truck_route(truck, new_route):
    truck['route'] = new_route
    # Cập nhật lại thời gian và tải trọng
    truck['time'] = calculate_truck_time(truck, distances)
    # Tải trọng được cập nhật trong quá trình tính toán lộ trình

def swap_requests(trucks, requests, distances):
    improved = True
    while improved:
        improved = False
        for truck_id1 in trucks:
            for truck_id2 in trucks:
                if truck_id1 >= truck_id2:
                    continue
                truck1 = trucks[truck_id1]
                truck2 = trucks[truck_id2]
                # Lấy danh sách các yêu cầu của mỗi đầu kéo
                reqs_truck1 = [step['request_id'] for step in truck1['route'] if step['request_id'] is not None]
                reqs_truck2 = [step['request_id'] for step in truck2['route'] if step['request_id'] is not None]
                # Thử hoán đổi từng cặp yêu cầu
                for req_id1 in reqs_truck1:
                    for req_id2 in reqs_truck2:
                        req1 = requests[req_id1]
                        req2 = requests[req_id2]
                        # Kiểm tra tính khả thi của việc hoán đổi
                        if (is_feasible(truck1, req2, 'add', 2) and
                            is_feasible(truck1, req1, 'remove', 2) and
                            is_feasible(truck2, req1, 'add', 2) and
                            is_feasible(truck2, req2, 'remove', 2)):
                            # Tạo bản sao của lộ trình để thử nghiệm
                            new_route1 = replace_request_in_route(truck1['route'], req_id1, req2)
                            new_route2 = replace_request_in_route(truck2['route'], req_id2, req1)
                            # Tính toán thời gian mới
                            temp_truck1 = truck1.copy()
                            temp_truck1['route'] = new_route1
                            time1 = calculate_truck_time(temp_truck1, distances)
                            temp_truck2 = truck2.copy()
                            temp_truck2['route'] = new_route2
                            time2 = calculate_truck_time(temp_truck2, distances)
                            # Kiểm tra xem makespan có giảm không
                            old_makespan = max(truck1['time'], truck2['time'])
                            new_makespan = max(time1, time2)
                            if new_makespan < old_makespan:
                                # Chấp nhận hoán đổi
                                update_truck_route(truck1, new_route1)
                                update_truck_route(truck2, new_route2)
                                improved = True
                                break  # Có cải thiện, tiếp tục vòng lặp chính
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

def replace_request_in_route(route, old_req_id, new_req):
    new_route = []
    for step in route:
        if step['request_id'] == old_req_id:
            # Thay thế bằng yêu cầu mới
            if step['action'] == requests[old_req_id]['pickup_action']:
                action = new_req['pickup_action']
                duration = new_req['pickup_duration']
            elif step['action'] == requests[old_req_id]['drop_action']:
                action = new_req['drop_action']
                duration = new_req['drop_duration']
            new_step = {
                'point': step['point'],  # Giữ nguyên điểm
                'action': action,
                'request_id': new_req['id']
            }
            new_route.append(new_step)
        else:
            new_route.append(step)
    return new_route

def create_steps_for_request(req_id, req):
    steps = []
    steps.append({
        'point': req['pickup_point'],
        'action': req['pickup_action'],
        'request_id': req_id
    })
    steps.append({
        'point': req['drop_point'],
        'action': req['drop_action'],
        'request_id': req_id
    })
    return steps

def is_feasible_route(truck, capacities):
    load = 0
    for step in truck['route']:
        action = step['action']
        req_id = step['request_id']
        if action in ['PICKUP_CONTAINER', 'PICKUP_CONTAINER_TRAILER']:
            req = requests[req_id]
            required_capacity = 1 if req['size'] == 20 else 2
            load += required_capacity
            if load > capacities:
                return False
        elif action in ['DROP_CONTAINER', 'DROP_CONTAINER_TRAILER']:
            req = requests[req_id]
            required_capacity = 1 if req['size'] == 20 else 2
            load -= required_capacity
    return True

def insert_unassigned_requests(trucks, requests, distances):
    unassigned_reqs = [req_id for req_id, req in requests.items() if not req['assigned']]
    for req_id in unassigned_reqs:
        req = requests[req_id]
        best_truck_id = None
        best_insertion = None
        min_increase = float('inf')
        for truck_id in trucks:
            truck = trucks[truck_id]
            # Thử chèn yêu cầu vào các vị trí khác nhau trong lộ trình
            for i in range(len(truck['route']) + 1):
                for j in range(i, len(truck['route']) + 1):
                    new_route = truck['route'][:i] + \
                                create_steps_for_request(req_id, req) + \
                                truck['route'][i:]
                    temp_truck = truck.copy()
                    temp_truck['route'] = new_route
                    # Kiểm tra tính khả thi
                    if is_feasible_route(temp_truck, 2):
                        time_increase = calculate_truck_time(temp_truck, distances) - truck['time']
                        if time_increase < min_increase:
                            min_increase = time_increase
                            best_truck_id = truck_id
                            best_insertion = new_route
        if best_truck_id is not None:
            # Chèn yêu cầu vào lộ trình của đầu kéo tốt nhất
            truck = trucks[best_truck_id]
            update_truck_route(truck, best_insertion)
            requests[req_id]['assigned'] = True

def improve_solution(trucks, requests, distances):
    previous_makespan = None
    while True:
        swap_requests(trucks, requests, distances)
        insert_unassigned_requests(trucks, requests, distances)
        # Tính toán makespan mới
        F1, F2 = calculate_objective(trucks, distances)
        if previous_makespan is not None and F1 >= previous_makespan:
            break  # Không cải thiện được nữa
        previous_makespan = F1

if __name__ == '__main__':
    # Đọc dữ liệu đầu vào
    N, distances, trailer_location, trailer_attach_time, trucks, requests = read_input()

    # Khởi tạo giải pháp ban đầu
    assign_requests(trucks, requests, distances, trailer_location, trailer_attach_time)

    # Cải thiện giải pháp
    improve_solution(trucks, requests, distances)

    # Tính toán hàm mục tiêu
    '''F1, F2 = calculate_objective(trucks, distances)
    F = 100000 * F1 + F2
    print(f'OBJECTIVE {F}')'''

    # Xuất kết quả
    output_result(trucks)
