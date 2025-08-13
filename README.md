# 사족 보행 로봇 (Quadruped Robot) - UPDONGI

## 프로젝트 개요

이 프로젝트는 아두이노 라즈베리파이를 기반으로 한 사족 보행 로봇의 제어 시스템입니다. 3D 시뮬레이션을 통해 로봇의 동작을 미리 확인할 수 있으며, 실제 하드웨어와 연동하여 동작합니다.

## 사용된 하드웨어

- **아두이노 라즈베리파이**: 메인 제어 보드
- **IOE-SR05 초음파 거리측정 센서**: 2미터 거리 측정
- **라즈베리파이 카메라모듈 8MP V2**: 환경 인식 및 이미지 캡처
- **FSR 압력센서 0.5인치 원형 FSR402**: 지면 접촉 감지
- **MPU6050 자이로 6축 가속 모듈**: 자세 및 기울기 측정
- **서브모터**: 정밀한 각도 제어 (DC 모터 아님)

## 주요 기능

### 1. 3D 시뮬레이션
- 실시간 로봇 동작 시뮬레이션
- 키보드로 로봇 제어 (WASD, QE, Space)
- 센서 데이터 시각화
- 물리 엔진 기반 움직임

### 2. 모터 제어 시스템
- 12개 서브모터 정밀 제어 (각 다리당 3개)
- PWM 기반 각도 제어
- 균형 복구 알고리즘
- 비상 정지 기능

### 3. 보행 제어
- 4단계 보행 패턴
- 보폭 및 속도 조정
- 방향 전환 및 회전
- 균형 유지 알고리즘

### 4. 센서 시스템
- MPU6050 기울기 감지
- FSR 압력 센서 데이터 처리
- 초음파 거리 측정
- 카메라 이미지 캡처

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 시뮬레이션 실행

```bash
python quadruped_simulation.py
```

### 3. 개별 모듈 테스트

```bash
# 모터 제어 테스트
python -c "from activate_motor import BodyActivateMotor; motor = BodyActivateMotor()"

# 보행 제어 테스트
python -c "from straight_walk import straight_walk; controller = straight_walk()"

# 센서 테스트
python -c "from detect_inclination import BodyDetectInclination; sensor = BodyDetectInclination()"
```

## 제어 방법

### 시뮬레이션 제어
- **W**: 앞으로 이동
- **S**: 뒤로 이동
- **A**: 왼쪽으로 방향 조정
- **D**: 오른쪽으로 방향 조정
- **Q**: 왼쪽으로 회전
- **E**: 오른쪽으로 회전
- **Space**: 정지
- **ESC**: 종료

### 실제 하드웨어 제어
```python
from activate_motor import BodyActivateMotor
from activate_steering import BodyActivateSteering
from leg_moving import LegMoving

# 모터 컨트롤러 초기화
motor_controller = BodyActivateMotor()
steering_controller = BodyActivateSteering()
leg_controller = LegMoving()

# 균형 복구
motor_controller.recover_balance(roll_error, pitch_error)

# 조향 조정
steering_controller.adjust_steering(target_angle)

# 보행 시작
leg_controller.start_walking(direction='forward', speed=1.0)
```

## 파일 구조

```
UPDONGI-main/
├── quadruped_simulation.py    # 메인 3D 시뮬레이션
├── activate_motor.py          # 모터 제어 시스템
├── activate_steering.py       # 조향 제어 시스템
├── leg_moving.py             # 다리 움직임 제어
├── straight_walk.py          # 직선 보행 제어
├── detect_inclination.py     # 기울기 감지 센서
├── import_image_data.py      # 카메라 이미지 관리
├── requirements.txt          # Python 패키지 의존성
└── README.md                # 프로젝트 문서
```

## 주요 클래스 및 함수

### BodyActivateMotor
- `set_motor_angle(motor_name, target_angle)`: 특정 모터 각도 설정
- `recover_balance(roll_error, pitch_error)`: 균형 복구
- `emergency_stop()`: 비상 정지

### BodyActivateSteering
- `adjust_steering(target_angle)`: 조향 각도 조정
- `balance_for_two_legs(roll_error, pitch_error, yaw_error)`: 두 다리 균형 조정

### LegMoving
- `move_shoulder(leg_name, target_angle)`: 힙 관절 제어
- `move_elbow(leg_name, target_angle)`: 무릎 관절 제어
- `drop_leg(leg_name, target_height)`: 발목 높이 조정
- `start_walking(direction, speed)`: 보행 시작

### BodyDetectInclination
- `read_gyro()`: 센서 데이터 읽기
- `classify_inclination(gyro_data)`: 기울기 분류
- `get_inclination_details()`: 상세 기울기 정보

### CameraImportImageData
- `capture_image(image_type, tags, metadata)`: 이미지 캡처
- `fetch_image_list(image_type, limit, offset)`: 이미지 목록 조회
- `get_image_by_id(image_id)`: 특정 이미지 데이터

## 설정 및 커스터마이징

### 모터 핀 설정
```python
# activate_motor.py에서 GPIO 핀 번호 수정
self.motor_pins = {
    'front_left_hip': 17,      # 앞왼쪽 힙 모터
    'front_left_knee': 18,     # 앞왼쪽 무릎 모터
    'front_left_ankle': 27,    # 앞왼쪽 발목 모터
    # ... 기타 모터들
}
```

### 센서 임계값 조정
```python
# detect_inclination.py에서 기울기 임계값 수정
self.inclination_thresholds = {
    'level': 2.0,          # 수평 (도)
    'slight': 5.0,         # 약간 기울어짐 (도)
    'moderate': 15.0,      # 중간 기울기 (도)
    'steep': 30.0,         # 급한 기울기 (도)
    'critical': 45.0       # 위험한 기울기 (도)
}
```

### 보행 파라미터 조정
```python
# straight_walk.py에서 보행 설정 수정
self.step_length = 12.0      # 보폭 (cm)
self.step_height = 8.0       # 다리 들어올리는 높이 (cm)
self.walking_speed = 1.0     # 보행 속도 (0.5 ~ 2.0)
```

## 시뮬레이션 모드

하드웨어가 연결되지 않은 환경에서는 자동으로 시뮬레이션 모드로 실행됩니다:

- 모터 제어: 콘솔 출력으로 동작 시뮬레이션
- 센서 데이터: 더미 데이터 생성
- 카메라: 랜덤 이미지 생성
- GPIO: 가상 인터페이스 사용

## 문제 해결

### 일반적인 오류

1. **RPi.GPIO 모듈 오류**
   - 시뮬레이션 모드로 자동 전환됩니다
   - 실제 하드웨어에서는 `sudo pip3 install RPi.GPIO` 실행

2. **카메라 초기화 실패**
   - 라즈베리파이 카메라가 활성화되어 있는지 확인
   - `sudo raspi-config`에서 Camera Enable

3. **I2C 통신 오류**
   - `sudo raspi-config`에서 I2C Enable
   - `i2cdetect -y 1`로 센서 주소 확인

### 디버깅 모드

```python
# 각 모듈에서 상세 로그 출력
import logging
logging.basicConfig(level=logging.DEBUG)

# 모터 상태 확인
motor_status = motor_controller.get_motor_status()
print(motor_status)

# 센서 상태 확인
sensor_status = inclination_sensor.get_sensor_status()
print(sensor_status)
```

## 성능 최적화

### 모터 제어 최적화
- PWM 주파수 조정으로 부드러운 움직임
- 각도 변화율 제한으로 진동 방지
- 상보필터로 센서 노이즈 제거

### 보행 알고리즘 최적화
- 4단계 보행 패턴으로 안정성 향상
- 균형 보정 임계값 조정
- 속도 기반 보폭 자동 조정

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 생성해 주세요.

---

**주의사항**: 실제 하드웨어와 연동하기 전에 반드시 시뮬레이션으로 동작을 확인하세요. 모터의 각도 제한과 안전 장치를 확인하여 로봇과 주변 환경의 안전을 보장하세요.
