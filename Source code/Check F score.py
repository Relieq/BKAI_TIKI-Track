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

def read_output():
    trucks_output = {}
    line = input()
    while not line.startswith('ROUTES'):
        line = input()
    num_trucks = int(line.strip().split()[1])

    for _ in range(num_trucks):
        line = input()
        while not line.startswith('TRUCK'):
            line = input()
        truck_id = int(line.strip().split()[1])
        route = []
        line = input().strip()
        while line != '#':
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
                line = input().strip()
                continue
            route.append({
                'point': point,
                'action': action,
                'request_id': request_id
            })
            line = input().strip()
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
        travel_time = distances[prev_point][point]
        total_time += travel_time
        total_distance += travel_time

        # Thời gian tác nghiệp tại điểm đến
        if action == 'PICKUP_TRAILER' or action == 'DROP_TRAILER':
            total_time += trailer_attach_time
        elif action in ['PICKUP_CONTAINER', 'DROP_CONTAINER', 'PICKUP_CONTAINER_TRAILER', 'DROP_CONTAINER_TRAILER']:
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
        truck_output = trucks_output[truck_id]
        truck_info = trucks[truck_id]
        truck = {
            'location': truck_info['location'],
            'route': truck_output['route']
        }
        total_time, total_distance = calculate_truck_time_and_distance(truck, distances, trailer_attach_time, requests)
        F1 = max(F1, total_time)
        F2 += total_distance
    return F1, F2

if __name__ == '__main__':
    # Đọc dữ liệu đầu vào
    N, distances, trailer_location, trailer_attach_time, trucks, requests = read_input()

    # Đọc output cần đánh giá
    trucks_output = read_output()

    # Tính toán hàm mục tiêu
    F1, F2 = calculate_objective(trucks_output, trucks, distances, trailer_attach_time, requests)
    F = 10000 * F1 + F2

    print(f'OBJECTIVE {F}')
