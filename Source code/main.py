import time

# Đọc dữ liệu từ stdin
def read_input():
    N = int(input().split()[1])  # 'POINTS N'
    distances = {}
    input_line = input().split()
    while input_line[0] != 'DISTANCES':
        input_line = input().split()
    num_distances = int(input_line[1])  # 'DISTANCES num_distances'

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
    m = int(truck_info[1])  # 'TRUCK m'
    trucks = {}
    for _ in range(m):
        truck_id, location = map(int, input().split())
        trucks[truck_id] = {
            'location': location,
            'capacity': 2,  # Sức chứa tính theo đơn vị container 20ft
            'route': [],
            'load': 0,
            'time': 0,
            'current_location': location,  # Khởi tạo current_location bằng location ban đầu
            'has_trailer': False,
            'trailer_load': 0
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
                'id': req_id,
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
    def priority(req_id):
        req = requests[req_id]
        if req['pickup_action'] == 'PICKUP_CONTAINER_TRAILER':
            return 0
        else:
            return 1
    return sorted(requests.keys(), key=lambda req_id: priority(req_id))

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
        for req_id in unassigned_requests[:]:  # Duyệt trên một bản sao của danh sách
            req = requests[req_id]
            required_capacity = 1 if req['size'] == 20 else 2

            # Tìm đầu kéo phù hợp nhất để phục vụ yêu cầu này
            best_truck_id = None
            min_completion_time = float('inf')
            best_actions = None
            best_temp_truck = None

            for truck_id, truck in trucks.items():
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
                    if temp_truck['trailer_load'] + required_capacity > truck['capacity']:
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
                if temp_truck['trailer_load'] < 0 or temp_truck['trailer_load'] > truck['capacity']:
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

# Tính toán hàm mục tiêu
def calculate_objective(trucks, distances):
    F1 = 0  # Makespan
    F2 = 0  # Tổng thời gian di chuyển
    for truck_id, truck in trucks.items():
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

# Xuất kết quả
def output_result(trucks):
    print(f'ROUTES {len(trucks)}')
    for truck_id, truck in trucks.items():
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

# Tính toán thời gian cho một đầu kéo dựa trên lộ trình
def calculate_truck_time(truck, distances):
    total_time = 0
    prev_point = truck['current_location']  # Sử dụng current_location làm điểm khởi đầu
    for step in truck['route']:
        point = step['point']
        action = step['action']
        if point not in distances[prev_point]:
            # Nếu không có đường trực tiếp, có thể sử dụng giá trị mặc định hoặc một số logic khác
            travel_time = 0
        else:
            travel_time = distances[prev_point][point]
        total_time += travel_time
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

# Kiểm tra tính khả thi của hành động thêm hoặc loại bỏ
def is_feasible(truck, req, action, capacities):
    required_capacity = 1 if req['size'] == 20 else 2
    if action == 'add':
        if truck['load'] + required_capacity > capacities:
            return False
    elif action == 'remove':
        if truck['load'] - required_capacity < 0:
            return False
    return True

# Cập nhật lộ trình và tính toán lại thời gian và tải trọng
def update_truck_route(truck, new_route, distances, trailer_attach_time, requests):
    # Cập nhật lộ trình
    truck['route'] = new_route

    # Khởi tạo lại trạng thái đầu kéo
    has_trailer = False
    trailer_load = 0
    current_location = truck['location']  # Bắt đầu từ vị trí gốc

    total_time = 0  # Tổng thời gian di chuyển và tác nghiệp

    for step in new_route:
        point = step['point']
        action = step['action']
        req_id = step['request_id']

        # Tính thời gian di chuyển đến điểm tiếp theo
        if current_location in distances and point in distances[current_location]:
            travel_time = distances[current_location][point]
        else:
            # Nếu không có đường trực tiếp, có thể sử dụng một giá trị mặc định hoặc logic khác
            travel_time = 0  # Hoặc đặt một giá trị lớn hơn để tránh
        total_time += travel_time

        # Cập nhật vị trí hiện tại
        current_location = point

        # Cập nhật trạng thái dựa trên hành động
        if action == 'PICKUP_TRAILER':
            has_trailer = True
            total_time += trailer_attach_time  # Thêm thời gian gắn rơ mooc
        elif action == 'DROP_TRAILER':
            has_trailer = False
            trailer_load = 0  # Reset tải trọng khi tháo rơ mooc
            total_time += trailer_attach_time  # Thêm thời gian tháo rơ mooc
        elif action in ['PICKUP_CONTAINER', 'PICKUP_CONTAINER_TRAILER']:
            if req_id is not None and req_id in requests:
                req = requests[req_id]
                load_change = 1 if req['size'] == 20 else 2
                trailer_load += load_change
                total_time += req['pickup_duration']  # Thêm thời gian lấy container
                if action == 'PICKUP_CONTAINER_TRAILER':
                    has_trailer = True  # Nếu hành động là PICKUP_CONTAINER_TRAILER, đảm bảo có rơ mooc
        elif action in ['DROP_CONTAINER', 'DROP_CONTAINER_TRAILER']:
            if req_id is not None and req_id in requests:
                req = requests[req_id]
                load_change = 1 if req['size'] == 20 else 2
                trailer_load -= load_change
                total_time += req['drop_duration']  # Thêm thời gian rải container
                if action == 'DROP_CONTAINER_TRAILER':
                    has_trailer = False  # Nếu hành động là DROP_CONTAINER_TRAILER, tháo rơ mooc

    # Cập nhật các thuộc tính của đầu kéo sau khi thực hiện lộ trình mới
    truck['current_location'] = current_location
    truck['has_trailer'] = has_trailer
    truck['trailer_load'] = trailer_load
    truck['time'] = total_time

# Hàm hoán đổi yêu cầu giữa các đầu kéo để cải thiện giải pháp
def swap_requests(trucks, requests, distances):
    improved = True
    while improved:
        improved = False
        # Tìm đầu kéo có thời gian hoàn thành lớn nhất và nhỏ nhất
        truck_times = sorted(trucks.items(), key=lambda x: x[1]['time'])
        fastest_truck_id = truck_times[0][0]
        slowest_truck_id = truck_times[-1][0]

        truck_fast = trucks[fastest_truck_id]
        truck_slow = trucks[slowest_truck_id]

        # Lấy danh sách các yêu cầu của mỗi đầu kéo
        reqs_fast = [step['request_id'] for step in truck_fast['route'] if step['request_id'] is not None]
        reqs_slow = [step['request_id'] for step in truck_slow['route'] if step['request_id'] is not None]

        # Giới hạn số lượng yêu cầu xem xét để giảm độ phức tạp
        reqs_fast = reqs_fast[:10]
        reqs_slow = reqs_slow[:10]

        for req_id_fast in reqs_fast:
            for req_id_slow in reqs_slow:
                req_fast = requests[req_id_fast]
                req_slow = requests[req_id_slow]

                # Kiểm tra tính khả thi của việc hoán đổi
                can_swap = (
                    is_feasible(truck_fast, req_slow, 'add', 2) and
                    is_feasible(truck_fast, req_fast, 'remove', 2) and
                    is_feasible(truck_slow, req_fast, 'add', 2) and
                    is_feasible(truck_slow, reqs_slow, 'remove', 2)
                )

                if not can_swap:
                    continue

                # Tạo lộ trình mới sau khi hoán đổi
                new_route_fast = replace_request_in_route(truck_fast['route'], req_id_fast, req_slow)
                new_route_slow = replace_request_in_route(truck_slow['route'], req_id_slow, req_fast)

                # Kiểm tra tính khả thi của lộ trình mới
                if not is_feasible_route({'route': new_route_fast}, truck_fast['capacity']) or not is_feasible_route({'route': new_route_slow}, truck_slow['capacity']):
                    continue

                # Tính toán thời gian mới
                temp_truck_fast = {
                    'location': truck_fast['location'],
                    'route': new_route_fast,
                    'current_location': truck_fast['current_location'],
                    'has_trailer': truck_fast['has_trailer'],
                    'trailer_load': truck_fast['trailer_load']
                }
                time_fast = calculate_truck_time(temp_truck_fast, distances)

                temp_truck_slow = {
                    'location': truck_slow['location'],
                    'route': new_route_slow,
                    'current_location': truck_slow['current_location'],
                    'has_trailer': truck_slow['has_trailer'],
                    'trailer_load': truck_slow['trailer_load']
                }
                time_slow = calculate_truck_time(temp_truck_slow, distances)

                # Kiểm tra xem makespan có giảm không
                old_makespan = max(truck_fast['time'], truck_slow['time'])
                new_makespan = max(time_fast, time_slow)

                if new_makespan < old_makespan:
                    # Chấp nhận hoán đổi
                    truck_fast['route'] = new_route_fast
                    truck_fast['time'] = time_fast
                    truck_slow['route'] = new_route_slow
                    truck_slow['time'] = time_slow
                    improved = True
                    break  # Có cải thiện, tiếp tục vòng lặp chính
            if improved:
                break
        if not improved:
            break  # Không cải thiện được nữa

# Hàm thay thế một yêu cầu bằng yêu cầu khác trong lộ trình
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

# Hàm tạo các bước cho một yêu cầu
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

# Kiểm tra tính khả thi của lộ trình
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

# Hàm chèn các yêu cầu chưa được gán vào lộ trình của các đầu kéo
def insert_unassigned_requests(trucks, requests, distances):
    unassigned_reqs = [req_id for req_id, req in requests.items() if not req['assigned']]
    # Sắp xếp đầu kéo theo thời gian hoàn thành tăng dần
    truck_times = sorted(trucks.items(), key=lambda x: x[1]['time'])

    for req_id in unassigned_reqs:
        req = requests[req_id]
        best_truck_id = None
        best_insertion = None
        min_increase = float('inf')
        for truck_id, truck in truck_times:
            # Chỉ thử chèn vào đầu hoặc cuối lộ trình
            for position in [0, len(truck['route'])]:
                new_route = truck['route'][:]
                steps = create_steps_for_request(req_id, req)
                new_route[position:position] = steps

                # Tạo đối tượng truck tạm để kiểm tra
                temp_truck = {
                    'location': truck['location'],
                    'route': new_route,
                    'current_location': truck['current_location'],
                    'has_trailer': truck['has_trailer'],
                    'trailer_load': truck['trailer_load']
                }

                # Kiểm tra tính khả thi
                if not is_feasible_route(temp_truck, truck['capacity']):
                    continue

                # Tính toán thời gian tăng thêm
                time_increase = calculate_truck_time(temp_truck, distances) - truck['time']
                if time_increase < min_increase:
                    min_increase = time_increase
                    best_truck_id = truck_id
                    best_insertion = new_route

        if best_truck_id is not None:
            # Chèn yêu cầu vào lộ trình của đầu kéo tốt nhất
            truck = trucks[best_truck_id]
            '''truck['route'] = best_insertion
            truck['time'] += min_increase
            # Cập nhật current_location dựa trên lộ trình mới
            if len(truck['route']) > 0:
                truck['current_location'] = truck['route'][-1]['point']
            else:
                truck['current_location'] = truck['location']'''
            update_truck_route(truck, best_insertion, distances, trailer_attach_time, requests)
            requests[req_id]['assigned'] = True

# Hàm cải thiện giải pháp bằng cách hoán đổi và chèn yêu cầu
def improve_solution(trucks, requests, distances, max_time=6):
    start_time = time.time()
    previous_makespan = None
    while True:
        current_time = time.time()
        if current_time - start_time > max_time:
            break  # Hết thời gian cho phép
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

    # Cải thiện giải pháp với thời gian giới hạn
    improve_solution(trucks, requests, distances, max_time=6)

    # Xuất kết quả
    output_result(trucks)