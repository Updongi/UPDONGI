import time
import RPi.GPIO as GPIO

class BodyActivateMotor:

class BodyActivateMotor:
    """
    기울기 복구용 모터 제어 (case 별 복구 프로토콜 실행)
    서브모터를 사용한 정밀한 각도 제어
    """
    def __init__(self):
        # 서브모터 핀 설정 (라즈베리파이 GPIO)
        self.motor_pins = {
            'front_left_hip': 17,      # 앞왼쪽 힙 모터
            'front_left_knee': 18,     # 앞왼쪽 무릎 모터
            'front_left_ankle': 27,    # 앞왼쪽 발목 모터
            'front_right_hip': 22,     # 앞오른쪽 힙 모터
            'front_right_knee': 23,    # 앞오른쪽 무릎 모터
            'front_right_ankle': 24,   # 앞오른쪽 발목 모터
            'back_left_hip': 10,       # 뒤왼쪽 힙 모터
            'back_left_knee': 9,       # 뒤왼쪽 무릎 모터
            'back_left_ankle': 11,     # 뒤왼쪽 발목 모터
            'back_right_hip': 5,       # 뒤오른쪽 힙 모터
            'back_right_knee': 6,      # 뒤오른쪽 무릎 모터
            'back_right_ankle': 13     # 뒤오른쪽 발목 모터
        }
        
        # 서브모터 각도 범위 (도)
        self.angle_limits = {
            'hip': (-45, 45),      # 힙: 좌우 회전
            'knee': (-30, 60),     # 무릎: 앞뒤 굽힘
            'ankle': (-20, 20)     # 발목: 미세 조정
        }
        
        # 현재 모터 각도 상태
        self.current_angles = {}
        for motor_name in self.motor_pins:
            self.current_angles[motor_name] = 0
        
        # 모터 제어 파라미터
        self.motor_speed = 1.0      # 각도/프레임
        self.recovery_threshold = 5.0  # 복구 시작 임계값 (도)
        
        # GPIO 초기화
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 모든 모터 핀을 출력으로 설정
            for pin in self.motor_pins.values():
                GPIO.setup(pin, GPIO.OUT)
            
            # PWM 객체 생성 (서브모터 제어용)
            self.pwm_objects = {}
            for motor_name, pin in self.motor_pins.items():
                self.pwm_objects[motor_name] = GPIO.PWM(pin, 50)  # 50Hz
                self.pwm_objects[motor_name].start(0)
            
            print("모터 GPIO 초기화 완료")
        except ImportError:
            print("RPi.GPIO 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"GPIO 초기화 오류: {e}")
            self.simulation_mode = True

    def set_motor_angle(self, motor_name, target_angle):
        """특정 모터의 각도를 설정"""
        if motor_name not in self.motor_pins:
            print(f"알 수 없는 모터: {motor_name}")
            return False
        
        # 각도 제한 확인
        motor_type = motor_name.split('_')[-1]  # hip, knee, ankle
        min_angle, max_angle = self.angle_limits[motor_type]
        target_angle = max(min_angle, min(max_angle, target_angle))
        
        # 서브모터 각도 제어 (0도 = 2.5% duty cycle, 180도 = 12.5% duty cycle)
        duty_cycle = 2.5 + (target_angle / 180.0) * 10.0
        
        try:
            if not hasattr(self, 'simulation_mode'):
                # 실제 하드웨어 제어
                self.pwm_objects[motor_name].ChangeDutyCycle(duty_cycle)
                time.sleep(0.1)  # 서브모터 안정화 시간
                self.pwm_objects[motor_name].ChangeDutyCycle(0)  # 신호 정지
            else:
                # 시뮬레이션 모드
                print(f"시뮬레이션: {motor_name} 모터를 {target_angle}도로 설정")
            
            self.current_angles[motor_name] = target_angle
            return True
            
        except Exception as e:
            print(f"모터 {motor_name} 제어 오류: {e}")
            return False

    def set_motor_power(self, power):
        """모터 파워 조정 (0.0 ~ 1.0)"""
        power = max(0.0, min(1.0, power))
        self.motor_speed = power * 2.0  # 최대 2도/프레임
        
        # 모든 모터의 속도 조정
        for motor_name in self.motor_pins:
            if hasattr(self, 'pwm_objects') and motor_name in self.pwm_objects:
                # PWM 주파수 조정으로 속도 제어
                new_freq = 50 + int(power * 100)  # 50Hz ~ 150Hz
                try:
                    self.pwm_objects[motor_name].ChangeFrequency(new_freq)
                except:
                    pass
        
        print(f"모터 파워를 {power:.2f}로 설정")

    def recover_balance(self, roll_error, pitch_error):
        """기울기 복구 프로토콜 실행"""
        print(f"균형 복구 시작 - Roll: {roll_error:.1f}°, Pitch: {pitch_error:.1f}°")
        
        # 복구 임계값 확인
        if abs(roll_error) < self.recovery_threshold and abs(pitch_error) < self.recovery_threshold:
            print("균형이 정상 범위 내에 있습니다.")
            return True
        
        # 복구 시퀀스 실행
        recovery_sequence = self._calculate_recovery_sequence(roll_error, pitch_error)
        
        for step in recovery_sequence:
            motor_name, target_angle, delay = step
            success = self.set_motor_angle(motor_name, target_angle)
            if success:
                time.sleep(delay)
            else:
                print(f"복구 단계 실패: {motor_name}")
                return False
        
        print("균형 복구 완료")
        return True

    def _calculate_recovery_sequence(self, roll_error, pitch_error):
        """복구 시퀀스 계산"""
        sequence = []
        
        # Roll 복구 (좌우 기울기)
        if abs(roll_error) > self.recovery_threshold:
            if roll_error > 0:  # 오른쪽으로 기울어짐
                # 왼쪽 다리들을 높이고 오른쪽 다리들을 낮춤
                sequence.extend([
                    ('front_left_ankle', 15, 0.2),
                    ('back_left_ankle', 15, 0.2),
                    ('front_right_ankle', -15, 0.2),
                    ('back_right_ankle', -15, 0.2)
                ])
            else:  # 왼쪽으로 기울어짐
                # 오른쪽 다리들을 높이고 왼쪽 다리들을 낮춤
                sequence.extend([
                    ('front_right_ankle', 15, 0.2),
                    ('back_right_ankle', 15, 0.2),
                    ('front_left_ankle', -15, 0.2),
                    ('back_left_ankle', -15, 0.2)
                ])
        
        # Pitch 복구 (앞뒤 기울기)
        if abs(pitch_error) > self.recovery_threshold:
            if pitch_error > 0:  # 앞으로 기울어짐
                # 앞다리들을 높이고 뒷다리들을 낮춤
                sequence.extend([
                    ('front_left_knee', 30, 0.2),
                    ('front_right_knee', 30, 0.2),
                    ('back_left_knee', -20, 0.2),
                    ('back_right_knee', -20, 0.2)
                ])
            else:  # 뒤로 기울어짐
                # 뒷다리들을 높이고 앞다리들을 낮춤
                sequence.extend([
                    ('back_left_knee', 30, 0.2),
                    ('back_right_knee', 30, 0.2),
                    ('front_left_knee', -20, 0.2),
                    ('front_right_knee', -20, 0.2)
                ])
        
        return sequence

    def emergency_stop(self):
        """비상 정지 - 모든 모터를 중립 위치로"""
        print("비상 정지 실행")
        
        for motor_name in self.motor_pins:
            self.set_motor_angle(motor_name, 0)
        
        # PWM 신호 정지
        if hasattr(self, 'pwm_objects'):
            for pwm in self.pwm_objects.values():
                try:
                    pwm.stop()
                except:
                    pass
        
        print("모든 모터가 중립 위치로 이동되었습니다.")

    def get_motor_status(self):
        """모터 상태 정보 반환"""
        return {
            'current_angles': self.current_angles.copy(),
            'motor_speed': self.motor_speed,
            'recovery_threshold': self.recovery_threshold
        }

    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'pwm_objects'):
            for pwm in self.pwm_objects.values():
                try:
                    pwm.stop()
                except:
                    pass
        
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
        
        print("모터 리소스 정리 완료") 
