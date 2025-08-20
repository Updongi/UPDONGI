class BodyActivateSteering:
    """
    조향 기능 → 다리 두 개 사용 시 균형 고려 조정
    서브모터를 사용한 정밀한 조향 제어
    """
    def __init__(self):
        # 조향 모터 핀 설정
        self.steering_motor_pins = {
            'front_left_hip': 17,      # 앞왼쪽 힙 회전
            'front_right_hip': 22,     # 앞오른쪽 힙 회전
            'back_left_hip': 10,       # 뒤왼쪽 힙 회전
            'back_right_hip': 5        # 뒤오른쪽 힙 회전
        }
        
        # 조향 제어 파라미터
        self.max_steering_angle = 30.0  # 최대 조향 각도 (도)
        self.steering_speed = 2.0       # 조향 속도 (도/프레임)
        self.balance_threshold = 3.0    # 균형 임계값 (도)
        
        # 현재 조향 상태
        self.current_steering = 0.0     # 현재 조향 각도
        self.target_steering = 0.0      # 목표 조향 각도
        self.is_steering = False        # 조향 중인지 여부
        
        # 균형 보정 파라미터
        self.balance_compensation = {
            'roll_offset': 0.0,         # Roll 축 오프셋
            'pitch_offset': 0.0,        # Pitch 축 오프셋
            'yaw_offset': 0.0           # Yaw 축 오프셋
        }
        
        # GPIO 초기화
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 조향 모터 핀을 출력으로 설정
            for pin in self.steering_motor_pins.values():
                GPIO.setup(pin, GPIO.OUT)
            
            # PWM 객체 생성
            self.pwm_objects = {}
            for motor_name, pin in self.steering_motor_pins.items():
                self.pwm_objects[motor_name] = GPIO.PWM(pin, 50)  # 50Hz
                self.pwm_objects[motor_name].start(0)
            
            print("조향 모터 GPIO 초기화 완료")
        except ImportError:
            print("RPi.GPIO 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"GPIO 초기화 오류: {e}")
            self.simulation_mode = True

    def adjust_steering(self, target_angle, speed_factor=1.0):
        """조향 각도 조정"""
        # 각도 제한
        target_angle = max(-self.max_steering_angle, min(self.max_steering_angle, target_angle))
        
        if abs(target_angle - self.current_steering) < 0.5:
            return True  # 이미 목표 각도에 도달
        
        self.target_steering = target_angle
        self.is_steering = True
        
        # 조향 방향 결정
        steering_direction = 1 if target_angle > self.current_steering else -1
        
        # 조향 속도 계산
        adjusted_speed = self.steering_speed * speed_factor
        
        print(f"조향 조정: {self.current_steering:.1f}° → {target_angle:.1f}°")
        
        # 조향 실행
        success = self._execute_steering(steering_direction, adjusted_speed)
        
        if success:
            self.current_steering = target_angle
            self.is_steering = False
        
        return success

    def _execute_steering(self, direction, speed):
        """조향 실행"""
        try:
            # 조향 각도에 따른 다리 위치 조정
            steering_sequence = self._calculate_steering_sequence(direction, speed)
            
            for step in steering_sequence:
                motor_name, angle_offset, delay = step
                
                if motor_name in self.pwm_objects:
                    # 서브모터 각도 제어
                    current_angle = self._get_current_motor_angle(motor_name)
                    target_angle = current_angle + angle_offset
                    
                    # PWM 신호 생성
                    duty_cycle = 2.5 + (target_angle / 180.0) * 10.0
                    self.pwm_objects[motor_name].ChangeDutyCycle(duty_cycle)
                    
                    time.sleep(delay)
                    self.pwm_objects[motor_name].ChangeDutyCycle(0)  # 신호 정지
                else:
                    # 시뮬레이션 모드
                    print(f"시뮬레이션: {motor_name} 조향 {angle_offset}도")
                    time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"조향 실행 오류: {e}")
            return False

    def _calculate_steering_sequence(self, direction, speed):
        """조향 시퀀스 계산"""
        sequence = []
        
        # 조향 각도에 따른 다리 조정
        if direction > 0:  # 오른쪽으로 조향
            # 왼쪽 다리들을 앞으로, 오른쪽 다리들을 뒤로
            sequence.extend([
                ('front_left_hip', 15, 0.1),
                ('back_left_hip', 15, 0.1),
                ('front_right_hip', -15, 0.1),
                ('back_right_hip', -15, 0.1)
            ])
        else:  # 왼쪽으로 조향
            # 오른쪽 다리들을 앞으로, 왼쪽 다리들을 뒤로
            sequence.extend([
                ('front_right_hip', 15, 0.1),
                ('back_right_hip', 15, 0.1),
                ('front_left_hip', -15, 0.1),
                ('back_left_hip', -15, 0.1)
            ])
        
        return sequence

    def balance_for_two_legs(self, roll_error, pitch_error, yaw_error):
        """두 다리 균형 조정"""
        print(f"두 다리 균형 조정 - Roll: {roll_error:.1f}°, Pitch: {pitch_error:.1f}°, Yaw: {yaw_error:.1f}°")
        
        # 균형 오차가 임계값을 넘으면 보정
        if (abs(roll_error) > self.balance_threshold or 
            abs(pitch_error) > self.balance_threshold or 
            abs(yaw_error) > self.balance_threshold):
            
            # 보정 각도 계산
            compensation_angles = self._calculate_compensation_angles(roll_error, pitch_error, yaw_error)
            
            # 보정 실행
            success = self._apply_balance_compensation(compensation_angles)
            
            if success:
                # 오프셋 업데이트
                self.balance_compensation['roll_offset'] += roll_error * 0.1
                self.balance_compensation['pitch_offset'] += pitch_error * 0.1
                self.balance_compensation['yaw_offset'] += yaw_error * 0.1
                
                print("균형 보정 완료")
                return True
            else:
                print("균형 보정 실패")
                return False
        
        return True

    def _calculate_compensation_angles(self, roll_error, pitch_error, yaw_error):
        """보정 각도 계산"""
        compensation = {}
        
        # Roll 보정 (좌우 기울기)
        if abs(roll_error) > self.balance_threshold:
            compensation['roll'] = -roll_error * 0.5  # 반대 방향으로 보정
        
        # Pitch 보정 (앞뒤 기울기)
        if abs(pitch_error) > self.balance_threshold:
            compensation['pitch'] = -pitch_error * 0.5
        
        # Yaw 보정 (회전)
        if abs(yaw_error) > self.balance_threshold:
            compensation['yaw'] = -yaw_error * 0.5
        
        return compensation

    def _apply_balance_compensation(self, compensation_angles):
        """균형 보정 적용"""
        try:
            for axis, angle in compensation_angles.items():
                if axis == 'roll':
                    # Roll 보정: 좌우 다리 높이 조정
                    self._adjust_leg_height('left', angle)
                    self._adjust_leg_height('right', -angle)
                elif axis == 'pitch':
                    # Pitch 보정: 앞뒤 다리 높이 조정
                    self._adjust_leg_height('front', angle)
                    self._adjust_leg_height('back', -angle)
                elif axis == 'yaw':
                    # Yaw 보정: 다리 회전 조정
                    self._adjust_leg_rotation(angle)
            
            return True
            
        except Exception as e:
            print(f"균형 보정 적용 오류: {e}")
            return False

    def _adjust_leg_height(self, leg_group, angle):
        """다리 그룹 높이 조정"""
        leg_motors = {
            'left': ['front_left_knee', 'back_left_knee'],
            'right': ['front_right_knee', 'back_right_knee'],
            'front': ['front_left_knee', 'front_right_knee'],
            'back': ['back_left_knee', 'back_right_knee']
        }
        
        if leg_group in leg_motors:
            for motor_name in leg_motors[leg_group]:
                if motor_name in self.pwm_objects:
                    current_angle = self._get_current_motor_angle(motor_name)
                    target_angle = current_angle + angle
                    
                    duty_cycle = 2.5 + (target_angle / 180.0) * 10.0
                    self.pwm_objects[motor_name].ChangeDutyCycle(duty_cycle)
                    time.sleep(0.1)
                    self.pwm_objects[motor_name].ChangeDutyCycle(0)

    def _adjust_leg_rotation(self, angle):
        """다리 회전 조정"""
        hip_motors = ['front_left_hip', 'front_right_hip', 'back_left_hip', 'back_right_hip']
        
        for motor_name in hip_motors:
            if motor_name in self.pwm_objects:
                current_angle = self._get_current_motor_angle(motor_name)
                target_angle = current_angle + angle
                
                duty_cycle = 2.5 + (target_angle / 180.0) * 10.0
                self.pwm_objects[motor_name].ChangeDutyCycle(duty_cycle)
                time.sleep(0.1)
                self.pwm_objects[motor_name].ChangeDutyCycle(0)

    def _get_current_motor_angle(self, motor_name):
        """모터 현재 각도 반환 (시뮬레이션용)"""
        # 실제 구현에서는 모터 인코더나 센서에서 읽어와야 함
        return 0.0

    def get_steering_status(self):
        """조향 상태 정보 반환"""
        return {
            'current_steering': self.current_steering,
            'target_steering': self.target_steering,
            'is_steering': self.is_steering,
            'balance_compensation': self.balance_compensation.copy()
        }

    def reset_steering(self):
        """조향을 중립 위치로 리셋"""
        return self.adjust_steering(0.0)

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
        
        print("조향 모터 리소스 정리 완료") 
