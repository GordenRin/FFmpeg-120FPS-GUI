import sys
import os
import time
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox, QLineEdit
from PyQt5.QtGui import QFont

def estimate_time(input_file, mode):
    try:
        # 獲取影片時長
        result = subprocess.run(f'ffprobe -i "{input_file}" -show_entries format=duration -v quiet -of csv="p=0"', 
                                shell=True, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        
        # 獲取 GPU 型號
        gpu_info = subprocess.run('nvidia-smi --query-gpu=name --format=csv,noheader', shell=True, capture_output=True, text=True)
        gpu_model = gpu_info.stdout.strip()
        
        # 估算時間 (根據 GPU 型號粗略推測)
        if "3070" in gpu_model:
            factor = 0.5  # RTX 3070 約每分鐘處理 2 分鐘影片
        else:
            factor = 1.0  # 預設較慢的 GPU 速度
        
        estimated_time = duration * factor
        return f"估計轉換時間: {int(estimated_time)} 秒 (GPU: {gpu_model})"
    except:
        return "無法估算時間"

def run_ffmpeg(input_file, output_file, mode, fps):
    if mode == "minterpolate":
        cmd = f'ffmpeg -hwaccel cuda -i "{input_file}" -vf "minterpolate=fps={fps}:mi_mode=mci" -c:v h264_nvenc -preset slow -b:v 20M -c:a aac -b:a 256k "{output_file}"'
    else:  # 修正 tinterlace 造成的畫面定格問題，確保整個影片時間同步
        cmd = f'ffmpeg -hwaccel cuda -i "{input_file}" -vf "tinterlace=mode=2,setpts=PTS/1.0,fps={fps}" -c:v h264_nvenc -preset slow -b:v 20M -c:a aac -b:a 256k "{output_file}"'
    print(cmd)
    os.system(cmd)

class FFmpegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("FFmpeg 120FPS GUI")
        self.setGeometry(100, 100, 550, 400)  # 放大視窗

        layout = QVBoxLayout()
        
        font = QFont("Arial", 14, QFont.Bold)  # 加大字體 + 粗體
        
        self.label = QLabel("選擇輸入影片:")
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self.btn_input = QPushButton("選擇影片")
        self.btn_input.setFont(font)
        self.btn_input.clicked.connect(self.selectInputFile)
        layout.addWidget(self.btn_input)
        
        self.label_output = QLabel("選擇輸出位置:")
        self.label_output.setFont(font)
        layout.addWidget(self.label_output)
        
        self.btn_output = QPushButton("選擇輸出資料夾")
        self.btn_output.setFont(font)
        self.btn_output.clicked.connect(self.selectOutputFile)
        layout.addWidget(self.btn_output)
        
        self.label_filename = QLabel("輸出檔案名稱:")
        self.label_filename.setFont(font)
        layout.addWidget(self.label_filename)
        
        self.filename_input = QLineEdit()
        self.filename_input.setFont(font)
        self.filename_input.setPlaceholderText("預設為 output_fps")
        layout.addWidget(self.filename_input)
        
        self.label_fps = QLabel("選擇FPS:")
        self.label_fps.setFont(font)
        layout.addWidget(self.label_fps)

        self.combo_fps = QComboBox()
        self.combo_fps.setFont(font)
        self.combo_fps.addItems(["60", "120"])
        layout.addWidget(self.combo_fps)

        self.label_mode = QLabel("選擇補偵模式:")
        self.label_mode.setFont(font)
        layout.addWidget(self.label_mode)
        
        self.combo_mode = QComboBox()
        self.combo_mode.setFont(font)
        self.combo_mode.addItems(["minterpolate", "tinterp"])
        layout.addWidget(self.combo_mode)
        
        self.label_estimate = QLabel("估計轉換時間: --")
        self.label_estimate.setFont(font)
        layout.addWidget(self.label_estimate)
        
        self.btn_start = QPushButton("開始轉換")
        self.btn_start.setFont(font)
        self.btn_start.clicked.connect(self.startConversion)
        layout.addWidget(self.btn_start)
        
        self.setLayout(layout)

    def selectInputFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "選擇輸入影片", "", "Video Files (*.mp4 *.avi *.mov *.webm)")
        if file_name:
            self.label.setText(f"輸入影片: {file_name}")
            self.input_file = file_name
            self.label_estimate.setText(estimate_time(file_name, self.combo_mode.currentText()))

    def selectOutputFile(self):
        folder_name = QFileDialog.getExistingDirectory(self, "選擇輸出資料夾")
        if folder_name:
            self.label_output.setText(f"輸出位置: {folder_name}")
            self.output_folder = folder_name

    def startConversion(self):
        if hasattr(self, 'input_file') and hasattr(self, 'output_folder'):
            mode = self.combo_mode.currentText()
            fps = self.combo_fps.currentText()
            filename = self.filename_input.text().strip()
            if not filename:
                filename = f"output_{fps}fps"
            output_file = f"{self.output_folder}/{filename}.mp4"
            run_ffmpeg(self.input_file, output_file, mode, fps)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FFmpegGUI()
    window.show()
    sys.exit(app.exec_())
