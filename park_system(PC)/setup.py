import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import serial.tools.list_ports
from pymodbus.client import ModbusSerialClient
import time

# =======주소 정의==========
CL_ID_SETTING_MODE = 0  # ID 설정 모드
CL_FIND_MODE = 1        # 노드 찾기 모드
CL_DEVICE_RESET = 2     # 장치 리셋
HR_SLAVE_ID = 100       # 슬레이브 ID

CONFIG_FILE = 'serial.json'

# =======설정 읽기==========
try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

default_port = config.get('port', '')
default_baud = config.get('baud_rate', 115200)

# =======사용 가능한 포트/보드 설정==========
available_ports = [port.device for port in serial.tools.list_ports.comports()]
baud_rates = [9600, 19200, 38400, 57600, 115200]

if default_port in available_ports:
    init_port = default_port
elif available_ports:
    init_port = available_ports[0]
else:
    init_port = ''

if default_baud in baud_rates:
    init_baud = default_baud
else:
    init_baud = 115200

# =======콤보박스 선택값 저장==========
def save_combobox_selection(*args):
    port = port_combo.get()
    baud = baud_combo.get()
    data = {'port': port, 'baud_rate': int(baud) if baud.isdigit() else 0}
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# =======Modbus 실행 함수==========
def run_modbus_action(action_func,title,msg):
    port = port_combo.get()
    baud = int(baud_combo.get())

    if port not in available_ports:
        messagebox.showerror('오류', '선택한 포트가 없습니다.')
        return False

    client = ModbusSerialClient(
        port=port,
        baudrate=baud,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=0.1,
        retries=0
    )

    try:
        if not client.connect():
            messagebox.showerror('연결 실패', f'{port} 포트에 연결할 수 없습니다.')
            return False
        action_func(client,int(id_spin.get()))
        client.close()
        messagebox.showinfo(title, msg)
        return True

    except Exception as e:
        messagebox.showerror('예외 발생', str(e))
        try:
            client.close()
        except:
            pass
        return False

# =======이벤트 핸들러==========
def on_set_id():
    def run(client,sid):
        client.write_coil(device_id=0, address=CL_ID_SETTING_MODE, value=True, no_response_expected =True )
        time.sleep(0.1)
        client.write_register(device_id=0, address=HR_SLAVE_ID, value=sid ,no_response_expected =True)
        time.sleep(0.1)
        client.write_coil(device_id=0, address=CL_ID_SETTING_MODE, value=False ,no_response_expected =True)
        time.sleep(0.1)
        client.write_coil(device_id=0, address=CL_DEVICE_RESET, value=True ,no_response_expected =True)
    run_modbus_action(run,'설정', 'ID 설정 성공!')

def on_find_start():
    def run(client,sid):
        client.write_coil(device_id=sid, address=CL_FIND_MODE, value=True)
    run_modbus_action(run,'Find', '찾기 시작!')

def on_find_stop():
    def run(client,sid):
        client.write_coil(device_id=sid, address=CL_FIND_MODE, value=False)
    run_modbus_action(run,'Find', '찾기 종료!')

def create_base_layout(main_frame, id_from =1, id_to = 247):
    global port_combo, baud_combo, id_spin

    tk.Label(main_frame, text='Port:').grid(row=0, column=0, sticky='w', padx=2, pady=3)
    port_combo = ttk.Combobox(main_frame, values=available_ports, width=8, state='readonly')
    port_combo.set(init_port)
    port_combo.grid(row=0, column=1, padx=3)

    baud_combo = ttk.Combobox(main_frame, values=baud_rates, width=8, state='readonly')
    baud_combo.set(init_baud)
    baud_combo.grid(row=0, column=2, padx=3)

    port_combo.bind('<<ComboboxSelected>>', save_combobox_selection)
    baud_combo.bind('<<ComboboxSelected>>', save_combobox_selection)

    tk.Label(main_frame, text='ID:').grid(row=1, column=0, sticky='w', padx=2, pady=3)
    id_spin = tk.Spinbox(main_frame, from_=id_from, to=id_to, width=5)
    id_spin.grid(row=1, column=1, padx=2)
    tk.Button(main_frame, text='설정', width=10, command=on_set_id).grid(row=1, column=2, padx=2)

    tk.Label(main_frame, text='Find:').grid(row=2, column=0, sticky='w', padx=2, pady=3)
    tk.Button(main_frame, text='시작', width=10, command=on_find_start).grid(row=2, column=1, padx=2, sticky='w')
    tk.Button(main_frame, text='종료', width=10, command=on_find_stop).grid(row=2, column=2, padx=2, sticky='w')

    for i in range(3):
        main_frame.grid_columnconfigure(i, weight=1, uniform='col')

    separator = ttk.Separator(main_frame, orient='horizontal')
    separator.grid(row=3, column=0, columnspan=3, sticky='ew', pady=6)

# =======GUI 구성==========
if __name__ == '__main__':
    root = tk.Tk()
    root.title('ID 설정')
    root.geometry('280x120')

    main_frame = tk.Frame(root)
    main_frame.pack(anchor='w', padx=10, pady=10)
    create_base_layout(main_frame)

    root.mainloop()
