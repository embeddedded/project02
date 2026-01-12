import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk
import json
import time
import threading
from pymodbus.client import ModbusSerialClient
from pymodbus.client import ModbusTcpClient
import random

DEMO =True

SCAN_INTERVAL = 5
SYSTEM_JSON = 'system.json'
POS_JSON = 'monitoring.json'

HR_AVAIL_FLOOR = 50
HR_AVAIL_GUIDE = 0

# 창 크기
W, H = 1024, 768
LABEL_SIZE = 25
N_FLOORS = 0
TEXT_COLOR = 'black'  # 글자색 고정
TEXT_SIZE = 6  # 글자 크기

result_avail = {}
sensor_of_floor = {}
MAX_ID = 240

#스캔여부    #새로들어감
scan = []
#가용 주차가능 true/안됨 false
avail = [False] * (MAX_ID + 1)
not_avail = avail[:]
#장애인 주차장
disabled = [False] * (MAX_ID + 1) #장애인주차장 표시 true/false
guide = []
total_guide={}
areas ={}

def load_json_file(path):
    global scan, avail, disabled ,total_guide,guide, areas
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for c in range(ord('A'), ord('Z') + 1):  # A~Z
        areas[chr(c)] = []

    for c in range(ord('a'), ord('z') + 1):  # a~z
        areas[chr(c)] = []

    area = data.get("Area", [])
    g = data.get("Guide", [])
    t_guide = data.get("TotalGuide", ['127,0,0,1', 502])

    total_guide = {'HOST':t_guide[0],'PORT':t_guide[1]}
    id = 1
    for row in area:
        for i in range(15, -1, -1):
            c = row[i]  #해당위치 문자: 구역
            if c != '0' :
                scan.append(id)
                areas[c].append(id)
                if c.islower(): #장애인 구역
                    disabled[id] = True

            id += 1

    print(areas)

    for ip,port, code1, code2 in g:
        guide.append( {'HOST':ip,'PORT':port, 'LEFT' : code1,'RIGHT' : code2   })
    print(guide)

# 가용 상태 스캔
def scan_sensor(client: ModbusSerialClient):
    local_avail = not_avail[:]
    if DEMO:  # 가상데이터 채우기
        for i in range(1, MAX_ID + 1):
            local_avail[i] = random.choice([True, False])

    for id in scan:
        print('<SENSOR', id ,end=':')
        a = False
        try:
            result = client.read_discrete_inputs(device_id=id, address=0, count=1 )
            a = result.getBit(0)
            print(a)
        except Exception as e:
            print('ERROR')
            if DEMO:
                a = random.choice([True,False])

        local_avail[id] = a

    return local_avail


def send_to_guide(host,port, values):
    client = ModbusTcpClient(host, port=port)
    if not client.connect():
        print("서버 연결 실패!")
        return

    try:
        # 레지스터에 값 쓰기 (한번에 2개)
        result = client.write_registers(0, values)
    finally:
        client.close()



# 백그라운드 스레드에서 일정 간격으로 센서 스캔 및 가용성 계산
def ccu_worker():
    global avail , result_avail
    client = ModbusSerialClient(
        port=COM_PORT,
        baudrate=BAUD_RATE,
        timeout=0.05,
        parity='N',
        stopbits=1,
        bytesize=8,retries=0
    )


    if not client.connect():
        print('연결 실패!')
        return

    while True:
        start = time.time()  # 루프 시작 시각 기록
        avail = scan_sensor(client) # 센서 스캔
        # 결과 정리
        # 층별/ 종합안내판
        floor_avail=[65535]* 5
        new_result_avail ={}
        for f in range(1, N_FLOORS + 1):
            key = str(f)
            new_result_avail[key] =[0,0]
            for s_id in sensor_of_floor[key]:
                 if avail[s_id]:
                    if disabled[s_id]:
                        new_result_avail[key][1] += 1
                    else:
                        new_result_avail[key][0] += 1

        result_avail = new_result_avail

        for f in range(1, N_FLOORS + 1):
            key = str(f)
            floor_avail[f-1] = result_avail[key][0]


        send_to_guide(total_guide['HOST'],total_guide['PORT'],floor_avail)

        # 안내판
        for g in guide:
            print(g)
            left_cnt = 0
            for a in g['LEFT']:
                for s_id in areas[a]:
                    if avail[s_id]:
                        left_cnt += 1
            right_cnt = 0
            for a in g['RIGHT']:
                for s_id in areas[a]:
                    if avail[s_id]:
                        right_cnt += 1

            send_to_guide(g['HOST'], g['PORT'], [left_cnt, right_cnt])
            print(left_cnt,right_cnt)


        # 루프 주기 보정
        elapsed = time.time() - start
        sleep_time = max(0, SCAN_INTERVAL - elapsed)
        time.sleep(sleep_time)

def update_labels():
    for f in range(1,N_FLOORS+1):
        a= result_avail[str(f)]
        status_labels[str(f)].config(text=f'{pos['names'][str(f)]:<5}: {a[0]:>3}/{a[1]:>3}')

# 각 캔버스에 사각형 + 텍스트 표시
def draw_active():
    current_tab = notebook.index('current')
    canvas = canvases[current_tab]
    canvas.delete('all')

    # 배경 이미지 다시 그리기
    canvas.create_image(0, 0, image=bg_photo[current_tab+1], anchor='nw')

    tab_name = f'{current_tab+1}'
    if tab_name in pos:
        for item in pos[tab_name]:
            x = item['x']
            y = item['y']
            sensor_id = item['id']
            text = str(sensor_id)
            bg = 'darkgray'

            if(avail[sensor_id]): #가용?
                if (disabled[sensor_id]):#장애인구역
                    bg = 'lightblue'
                else:
                    bg = 'lightgreen'
            else:
                bg= 'lightcoral'
            fg = TEXT_COLOR
            half = LABEL_SIZE // 2
            canvas.create_rectangle(x-half, y-half, x+half, y+half, fill=bg, outline='black', width=2)
            canvas.create_text(x, y, text=text, fill=fg, font=('Arial', TEXT_SIZE, 'bold'))

    # 우측 하단에 최종 업데이트 시간 표시
    timestamp = datetime.now().strftime('%H:%M:%S')
    canvas.create_text(W-60, H-80, text=f'Updated: {timestamp}', fill='black', font=('Arial', 8))
    update_labels()
    root.after(1000, draw_active)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('주차유도시스템 모니터링')
    root.geometry(f'{W}x{H}')


    # JSON 파일 로드
    try:
        load_json_file(SYSTEM_JSON)

        with open(POS_JSON, 'r', encoding='utf-8') as f:
            pos = json.load(f)
            COM_PORT = pos.get('port','COM3')
            BAUD_RATE = pos.get('baud_rate',115200)
    except FileNotFoundError:
        pos = {}

    for i in range(1,9):
        floor_id = str(i)
        if not floor_id in pos:
            break
        result_avail[floor_id] = [0,0] # 초기값
        sensor_of_floor[floor_id] = []
        for p in pos[floor_id]:
            sensor_of_floor[floor_id].append(p['id'])

        N_FLOORS = i
    print(sensor_of_floor)

    if N_FLOORS  == 0:
        messagebox.showerror('오류', '층 데이터가 필요합니다.')
        exit()

    top_frame = tk.Frame(root, bg='#ddd', height=40)
    top_frame.pack(fill='x')

    status_labels = {}
    for i in range(N_FLOORS):
        f = i+1
        lbl = tk.Label(
            top_frame,
            text='',
            font=('Arial', 10, 'bold'),
            width=14,
            relief='groove',
            bd=1
        )
        lbl.pack(side='left', padx=5, pady=5)

        status_labels[str(f)] = lbl

    # Notebook (탭컨트롤)
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    bg_photo={}
    # 이미지 로드 (배경용)
    for i in range(N_FLOORS):
        f = i+1
        bg_image = Image.open('img/' + pos['imgs'][str(f)])
        bg_image = bg_image.resize((W, H-60))
        bg_photo[f] = ImageTk.PhotoImage(bg_image)

    tabs = []
    canvases = []
    for i in range(N_FLOORS):
        tab = tk.Frame(notebook)
        notebook.add(tab, text=pos['names'][str(i + 1)])
        canvas = tk.Canvas(tab, width=W, height=H-60, bg='white')
        canvas.pack(fill='both', expand=True)
        canvas.create_image(0, 0, image=bg_photo[i+1], anchor='nw')
        tabs.append(tab)
        canvases.append(canvas)

    t = threading.Thread(target=ccu_worker, daemon=True)
    t.start()

    draw_active()
    root.mainloop()