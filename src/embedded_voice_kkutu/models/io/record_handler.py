import pyaudio
from array import array
from math import sqrt
import time  # 타이머 추가


class RecordHandler:
    CHUNK = 1024  # 오디오 데이터 버퍼 크기
    FORMAT = pyaudio.paInt16  # 오디오 포맷
    CHANNELS = 1  # 모노
    RATE = 44100  # 샘플링 레이트
    SILENCE_THRESHOLD = 1000  # 무음 기준 볼륨
    SILENCE_CHUNKS = 30  # 무음 지속 길이
    INITIAL_SILENCE_DURATION = 5  # 초기 무음 허용 시간 (초)

    def calculate_rms(self, data):
        """RMS 에너지 계산: 데이터의 평균 에너지를 계산"""
        if len(data) == 0:
            return 0  # 데이터가 비어 있으면 RMS는 0
        squares = [sample**2 for sample in data]
        mean_square = sum(squares) / len(data)
        return sqrt(max(mean_square, 0))  # 음수 방지

    def validate_data(self, data):
        """데이터 유효성 검사"""
        if len(data) == 0:
            return False
        # 데이터에 이상값이 포함되어 있는지 확인
        if any(abs(sample) > 32767 for sample in data):  # paInt16 범위 초과 확인
            return False
        return True

    def record_until_silence(self):
        """사용자의 음성을 녹음하고, 무음 기준값을 초과하는 데이터만 기록"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        print("Listening... Speak now!")

        frames = []
        silent_chunks = 0
        is_speaking = False
        start_time = time.time()  # 녹음 시작 시간 기록
        initial_silence_start = time.time()  # 초기 무음 감지 시작 시간

        while True:
            data = stream.read(self.CHUNK)
            array_data = array("h", data)

            # 데이터 유효성 검사
            if not self.validate_data(array_data):
                print("Invalid data detected, skipping...")
                continue

            # 데이터를 float으로 변환하여 오버플로우 방지
            float_data = [float(sample) for sample in array_data]

            # RMS 에너지 계산
            rms = self.calculate_rms(float_data)

            # 실시간으로 RMS 값과 무음 기준값 비교 출력
            print(f"RMS: {rms:.2f}, Threshold: {self.SILENCE_THRESHOLD}")

            # 초기 무음 상태 체크
            if (
                not is_speaking
                and time.time() - initial_silence_start > self.INITIAL_SILENCE_DURATION
            ):
                print(
                    "No speech detected within the initial silence duration. Stopping recording..."
                )
                break

            # 입력 음성이 무음 기준값을 초과하면 녹음 시작
            if rms > self.SILENCE_THRESHOLD:
                is_speaking = True
                silent_chunks = 0
                frames.append(data)
                print("Speaking detected...")

            # 무음 상태가 일정 시간 지속되면 녹음 종료
            elif is_speaking:
                frames.append(data)
                silent_chunks += 1
                print("Silence detected...")

                if silent_chunks > self.SILENCE_CHUNKS:
                    print("Silence duration exceeded. Stopping recording...")
                    break

        print("Done recording")

        # 녹음 종료
        stream.stop_stream()
        stream.close()
        p.terminate()

        return frames
