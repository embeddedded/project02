from setup import *

HR_SPACE_TYPE = 101
spins = []
type_map = {0: '0: 이용불가', 1: '1: 일반', 2: '2: 장애인'}
labels = ['주차 감지 시간(초):', '출차 감지 시간(초):', '설치 높이(cm):', '물체 높이(cm):']
keys = [ 'detect_time',  'exit_time' , 'install_height', 'object_height']
ranges = [[1, 60], [1, 60], [0, 400], [0, 400]]
defaults = [5, 5, 250, 100]

CONFIG_FILE = 'sensor.json'

# =======설정 저장 함수 ==========
def save_sensor_settings():
    try:
        data = { 'space_type':
                     int(combo_space_type.get().split(':')[0].strip())   }
        for i in range(4):
            data[keys[i]] = int(spins[i].get())

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print('설정 저장 완료:', data)
    except Exception as e:
        print('설정 저장 실패:', e)

# =======설정 불러오기 함수==========
def load_sensor_settings():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print('설정 복원:', data)
    except FileNotFoundError:
        print('저장된 설정 파일 없음 — 기본값 사용')
        data={}
    combo_space_type.set(type_map.get(data.get('space_type', 1), type_map[1]))

    for i in range(4):
        spins[i].delete(0, tk.END)
        spins[i].insert(0, data.get(keys[i], defaults[i]))

# =======이벤트 핸들러==========
def on_read():
    def run(client,id):
        response  = client.read_holding_registers(device_id=id, address=HR_SPACE_TYPE,count=5)
        data = response.registers
        combo_space_type.set(type_map.get(data[0], type_map[1]))
        for i in range(4):
            spins[i].delete(0, tk.END)
            spins[i].insert(0, data[i+1])
    run_modbus_action(run,'읽기', '데이터를 읽었습니다.')

def on_write():
    if not messagebox.askyesno('쓰기 확인', '설정값을 장치에 쓰시겠습니까?'):
        return
    def run(client,id):
        data = [ int(combo_space_type.get().split(':')[0].strip()) ]
        for i in range(4):
            data.append(int(spins[i].get()) )
        client.write_registers(device_id=id, address=HR_SPACE_TYPE, values=data)
    save_sensor_settings()  # JSON 저장
    run_modbus_action(run,'쓰기', '설정값이 저장되었습니다.')

# =======GUI 구성==========
if __name__ == '__main__':
    root = tk.Tk()
    root.title('주차감지 센서 설정')
    root.geometry('280x300')

    main_frame = tk.Frame(root)
    main_frame.pack(anchor='w', padx=10, pady=10)
    create_base_layout(main_frame, 1, 240)

    tk.Label(main_frame, text='주차면 타입:').grid(row=4, column=0, columnspan=2, sticky='w', padx=2, pady=3)
    combo_space_type = ttk.Combobox(
        main_frame,
        values=['0: 이용불가', '1: 일반', '2: 장애인'],
        width=10,
        state='readonly'
    )
    combo_space_type.set('1: 일반')
    combo_space_type.grid(row=4, column=2, padx=2, pady=3, sticky='w')

    for i in range(4):
        tk.Label(main_frame, text=labels[i]).grid(row=5+i, column=0, columnspan=2, sticky='w', padx=2, pady=3)
        spin = tk.Spinbox(main_frame, from_=ranges[i][0], to=ranges[i][1], width=6)
        spin.grid(row=5+i, column=2, padx=2, pady=3, sticky='w')
        spins.append(spin)

    ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=3, sticky='ew', pady=6)

    tk.Button(main_frame, text='읽기', width=10, command=on_read).grid(row=10, column=1, padx=3, pady=5, sticky='e')
    tk.Button(main_frame, text='쓰기', width=10, command=on_write).grid(row=10, column=2, padx=3, pady=5, sticky='w')

    load_sensor_settings()
    root.mainloop()