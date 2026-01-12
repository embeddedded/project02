import tkinter as tk
from tkinter import font
import asyncio
import threading
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusDeviceContext

PORT = 503

class CallbackDataBlock(ModbusSequentialDataBlock):
    """콜백 기능이 있는 데이터 블록"""

    def __init__(self, app, addr, values):
        """초기화"""
        self.app = app
        super().__init__(addr, values)

    def setValues(self, address, value):
        """값이 설정될 때 콜백 호출"""
        super().setValues(address, value)
        # UI 업데이트 콜백
        if self.app:
            self.app.on_register_change(address, value)
            self.app.on_register_change(address, value)


class ParkingGuidePanel:
    def __init__(self, root):
        self.root = root
        self.root.title("주차유도판 - Modbus TCP Server")
        self.root.configure(bg='black')

        # Modbus 서버 설정
        self.server_port = PORT
        self.server_thread = None

        # 주차공간 데이터 (2개의 레지스터)
        self.parking_data = [0, 0]

        # UI 생성
        self.create_ui()

        # Modbus 서버 시작
        self.start_modbus_server()

    def create_ui(self):
        # 폰트 설정
        large_font = font.Font(family="Arial", size=48, weight="bold")
        number_font = font.Font(family="Arial", size=60, weight="bold")

        # 프레임 생성
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # 라벨 설정 (2행 5열)
        # 첫번째 행: ^^, 주차, >>(병합), B1, 주차
        # 두번째 행: 132, PARKING, >>(병합), PARKING, 123

        self.labels = []

        # 첫번째 행
        # 0,0: ^^ (화살표)
        label = tk.Label(main_frame, text="^^", font=large_font, bg='#2d2d2d', fg='lime', relief='raised',
                         borderwidth=5)
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 0,1: 주차
        label = tk.Label(main_frame, text="주차", font=large_font, bg='#2d2d2d', fg='white', relief='raised',
                         borderwidth=5)
        label.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 0,2 & 1,2: B1 (파란색) - 2행을 하나로 병합
        label = tk.Label(main_frame, text="B1", font=large_font, bg='blue', fg='white', relief='raised', borderwidth=5)
        label.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 0,3: 주차
        label = tk.Label(main_frame, text="주차", font=large_font, bg='#2d2d2d', fg='white', relief='raised',
                         borderwidth=5)
        label.grid(row=0, column=3, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 0,4: >> (화살표)
        label = tk.Label(main_frame, text=">>", font=large_font, bg='#2d2d2d', fg='lime', relief='raised',
                         borderwidth=5)
        label.grid(row=0, column=4, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 두번째 행
        # 1,0: 132 (숫자)
        label = tk.Label(main_frame, text="0", font=number_font, bg='red', fg='white', relief='raised', borderwidth=5)
        label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 1,1: PARKING
        label = tk.Label(main_frame, text="PARKING", font=large_font, bg='#2d2d2d', fg='white', relief='raised',
                         borderwidth=5)
        label.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 1,2는 rowspan으로 이미 위에서 병합됨 (B1)

        # 1,3: PARKING
        label = tk.Label(main_frame, text="PARKING", font=large_font, bg='#2d2d2d', fg='white', relief='raised',
                         borderwidth=5)
        label.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 1,4: 123 (숫자)
        label = tk.Label(main_frame, text="0", font=number_font, bg='red', fg='white', relief='raised', borderwidth=5)
        label.grid(row=1, column=4, padx=10, pady=10, sticky='nsew')
        self.labels.append(label)

        # 라벨 인덱스:
        # 0: ^^, 1: 주차, 2: B1(병합), 3: 주차, 4: >>
        # 5: 132(숫자), 6: PARKING, 7: PARKING, 8: 123(숫자)

        # 그리드 가중치 설정
        for i in range(2):
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            main_frame.grid_columnconfigure(i, weight=1)

        # 상태 표시
        self.status_label = tk.Label(
            self.root,
            text="Modbus TCP Server 시작 중...",
            font=('Arial', 12),
            bg='black',
            fg='yellow'
        )
        self.status_label.pack(side='bottom', pady=5)

    def start_modbus_server(self):
        """Modbus TCP 서버 시작"""

        def run_async_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 콜백 데이터블록 생성
            block = CallbackDataBlock(self, 0, [0] * 100)

            # 데이터 스토어 생성
            store = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
            context = ModbusServerContext(devices=store, single=True)

            # 서버 시작
            try:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Modbus TCP Server 실행 중 (Port: {self.server_port})",
                    fg='lime'
                ))
                loop.run_until_complete(
                    StartAsyncTcpServer(
                        context=context,
                        address=("0.0.0.0", self.server_port)
                    )
                )
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"서버 오류: {str(e)}",
                    fg='red'
                ))

        self.server_thread = threading.Thread(target=run_async_server, daemon=True)
        self.server_thread.start()

    def on_register_change(self, address, value):
        """레지스터 값 변경 시 콜백"""
        address -=1
        print(f"Register {address} changed to {value}")

        # 값이 리스트인 경우 모든 값 적용
        if isinstance(value, list):
            for i, val in enumerate(value):
                reg_addr = address + i
                if reg_addr == 0:  # 좌측 숫자
                    self.parking_data[0] = val
                elif reg_addr == 1:  # 우측 숫자
                    self.parking_data[1] = val
        else:
            # 단일 값인 경우
            if address == 0:  # 좌측 숫자
                self.parking_data[0] = value
            elif address == 1:  # 우측 숫자
                self.parking_data[1] = value

        # UI 업데이트 (메인 스레드에서 실행)
        self.root.after(0, self.update_display)

    def update_display(self):
        """화면 업데이트"""
        # 레지스터 0 -> 라벨 5 (좌측 숫자)
        if self.parking_data[0] == 0 :
            self.labels[5].config(text="만차", bg='red')
        else:
            self.labels[5].config(text=str(self.parking_data[0]), bg='green')

        # 레지스터 1 -> 라벨 8 (우측 숫자)
        if self.parking_data[1] == 0 :
            self.labels[8].config(text="만차", bg='red')
        else:
            self.labels[8].config(text=str(self.parking_data[1]), bg='green')


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1600x700")
    app = ParkingGuidePanel(root)
    root.mainloop()