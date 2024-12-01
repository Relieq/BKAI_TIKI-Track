def read_input(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    line_idx = 0

    # Đọc số điểm N
    N = int(lines[line_idx].split()[1])  # 'POINTS N'
    line_idx += 1

    # Đọc đến phần DISTANCES
    while not lines[line_idx].strip().startswith('DISTANCES'):
        line_idx += 1
    num_distances = int(lines[line_idx].strip().split()[1])  # 'DISTANCES num_distances'
    line_idx += 1

    distances = {}
    for _ in range(num_distances):
        i, j, d = map(int, lines[line_idx].strip().split())
        if i not in distances:
            distances[i] = {}
        distances[i][j] = d
        line_idx += 1

    # Đọc thông tin rơ mooc
    while not lines[line_idx].strip().startswith('TRAILER'):
        line_idx += 1
    trailer_info = lines[line_idx].strip().split()
    trailer_location = int(trailer_info[1])
    trailer_attach_time = int(trailer_info[2])
    line_idx += 1

    # Đọc thông tin đầu kéo
    while not lines[line_idx].strip().startswith('TRUCK'):
        line_idx += 1
    m = int(lines[line_idx].strip().split()[1])  # 'TRUCK m'
    line_idx += 1

    trucks = {}
    for _ in range(m):
        truck_id, location = map(int, lines[line_idx].strip().split())
        trucks[truck_id] = {
            'location': location,
            'capacity': 2,  # Sức chứa tính theo đơn vị container 20ft
            'route': [],
            'load': 0,
            'time': 0,
        }
        line_idx += 1

    # Đọc yêu cầu vận chuyển
    requests = {}
    while line_idx < len(lines) and lines[line_idx].strip() != '#':
        line = lines[line_idx].strip()
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
        line_idx += 1

    return N, distances, trailer_location, trailer_attach_time, trucks, requests

def read_output(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    line_idx = 0

    # Tìm đến phần OUTPUT
    while line_idx < len(lines) and not lines[line_idx].strip().startswith('ROUTES'):
        line_idx += 1

    if line_idx >= len(lines):
        print("Không tìm thấy phần OUTPUT trong file.")
        return {}

    num_trucks = int(lines[line_idx].strip().split()[1])  # 'ROUTES num_trucks'
    line_idx += 1

    trucks_output = {}
    for _ in range(num_trucks):
        # Đọc thông tin TRUCK
        while line_idx < len(lines) and not lines[line_idx].strip().startswith('TRUCK'):
            line_idx += 1
        if line_idx >= len(lines):
            break
        truck_id = int(lines[line_idx].strip().split()[1])  # 'TRUCK truck_id'
        line_idx += 1

        route = []
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            if line == '#':
                line_idx += 1
                break
            parts = line.strip().split()
            if len(parts) == 2:
                point = int(parts[0])
                action = parts[1]
                request_id = None
            elif len(parts) == 3:
                point = int(parts[0])
                action = parts[1]
                request_id = int(parts[2])
            else:
                line_idx += 1
                continue
            route.append({
                'point': point,
                'action': action,
                'request_id': request_id
            })
            line_idx += 1
        trucks_output[truck_id] = {
            'route': route
        }
    return trucks_output

def calculate_truck_time_and_distance(truck, distances, trailer_attach_time, requests):
    total_time = 0
    total_distance = 0
    prev_point = truck['location']
    for step in truck['route']:
        point = step['point']
        action = step['action']
        request_id = step['request_id']

        # Thời gian di chuyển giữa các điểm
        if prev_point in distances and point in distances[prev_point]:
            travel_time = distances[prev_point][point]
        else:
            print(f"Không tìm thấy khoảng cách giữa điểm {prev_point} và {point}.")
            return None, None
        total_time += travel_time
        total_distance += travel_time

        # Thời gian tác nghiệp tại điểm đến
        if action == 'PICKUP_TRAILER' or action == 'DROP_TRAILER':
            total_time += trailer_attach_time
        elif action in ['PICKUP_CONTAINER', 'DROP_CONTAINER', 'PICKUP_CONTAINER_TRAILER', 'DROP_CONTAINER_TRAILER']:
            if request_id is None or request_id not in requests:
                print(f"Yêu cầu {request_id} không tồn tại.")
                return None, None
            req = requests[request_id]
            if action == req['pickup_action']:
                total_time += req['pickup_duration']
            elif action == req['drop_action']:
                total_time += req['drop_duration']
        # Không có thời gian tác nghiệp cho 'STOP'

        prev_point = point
    return total_time, total_distance

def calculate_objective(trucks_output, trucks, distances, trailer_attach_time, requests):
    F1 = 0  # Makespan
    F2 = 0  # Tổng thời gian di chuyển
    for truck_id in trucks_output:
        if truck_id not in trucks:
            print(f"Đầu kéo {truck_id} không tồn tại.")
            continue
        truck_output = trucks_output[truck_id]
        truck_info = trucks[truck_id]
        truck = {
            'location': truck_info['location'],
            'route': truck_output['route']
        }
        total_time, total_distance = calculate_truck_time_and_distance(truck, distances, trailer_attach_time, requests)
        if total_time is None or total_distance is None:
            continue
        F1 = max(F1, total_time)
        F2 += total_distance
    return F1, F2

if __name__ == '__main__':
    # Nhập tên file input và output từ người dùng
    input_filename = input("Vui lòng nhập tên file input: ")
    output_filename = input("Vui lòng nhập tên file output: ")

    # Đọc dữ liệu đầu vào
    N, distances, trailer_location, trailer_attach_time, trucks, requests = read_input("../Input/" + input_filename)

    # Đọc output cần đánh giá
    trucks_output_admin = read_output("../Output/" + output_filename + " - Admin.txt")
    trucks_output_user = read_output("../Output/" + output_filename + " - User.txt")

    print("Admin:")
    # Tính toán hàm mục tiêu
    F1, F2 = calculate_objective(trucks_output_admin, trucks, distances, trailer_attach_time, requests)
    F = 10000 * F1 + F2

    # In kết quả
    print(f'MAKESPAN {F1}')
    print(f'TOTAL DISTANCE {F2}')
    print(f'OBJECTIVE {F} = 10000 * {F1} + {F2}')
    print("Total score: ", 1e9 - F)

    print("\nUser:")
    # Tính toán hàm mục tiêu
    F1, F2 = calculate_objective(trucks_output_user, trucks, distances, trailer_attach_time, requests)
    F = 10000 * F1 + F2

    # In kết quả
    print(f'MAKESPAN {F1}')
    print(f'TOTAL DISTANCE {F2}')
    print(f'OBJECTIVE {F} = 10000 * {F1} + {F2}')
    print("Total score: ", 1e9 - F)
