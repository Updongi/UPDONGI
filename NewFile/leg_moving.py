class LegMoving:
    """
    다리 움직임을 제어하는 클래스 (어깨→팔꿈치→내리기 순서)
    서브모터를 사용한 정밀한 다리 제어
    """
    def __init__(self):
        # 다리 모터 핀 설정
        self.leg_motor_pins = {
            'front_left': {
                'hip': 17,      # 힙 회전 (좌우)
                'knee': 18,     # 무릎 굽힘 (앞뒤)
                'ankle': 27     # 발목 미세 조정
            },
            'front_right': {
                'hip': 22,
                'knee': 23,
                'ankle': 24
            },
            'back_left': {
                'hip': 10,
                'knee': 9,
                'ankle': 11
            },
            'back_right': {
                'hip': 5,
                'knee': 6,
                'ankle': 13
            }
        }
        
        # 다리 움직임 제어 파라미터
        self.movement_speed = 2.0       # 각도/프레임
        self.step_height = 15.0         # 보행 시 다리 들어올리는 높이 (도)
        self.step_length = 20.0         # 보행 시 한 걸음 길이 (도)
        self.leg_clearance = 5.0        # 지면과의 여유 거리 (도)
        
        # 현재 다리 위치 상태
        self.leg_positions = {}
        for leg_name in self.leg_motor_pins:
            self.leg_positions[leg_name] = {
                'hip': 0.0,     # 힙 각도
                'knee': 0.0,    # 무릎 각도
                'ankle': 0.0    # 발목 각도
            }
        
        # 보행 시퀀스 상태
        self.walking_phase = 0          # 보행 단계 (0-3)
        self.leg_cycle = 0              # 다리 사이클
        self.is_walking = False         # 보행 중인지 여부
        
        # GPIO 초기화
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 모든 모터 핀을 출력으로 설정
            for leg_motors in self.leg_motor_pins.values():
                for pin in leg_motors.values():
                    GPIO.setup(pin, GPIO.OUT)
            
            # PWM 객체 생성
            self.pwm_objects = {}
            for leg_name, leg_motors in self.leg_motor_pins.items():
                self.pwm_objects[leg_name] = {}
                for joint_name, pin in leg_motors.items():
                    self.pwm_objects[leg_name][joint_name] = GPIO.PWM(pin, 50)  # 50Hz
                    self.pwm_objects[leg_name][joint_name].start(0)
            
            print("다리 모터 GPIO 초기화 완료")
        except ImportError:
            print("RPi.GPIO 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"GPIO 초기화 오류: {e}")
            self.simulation_mode = True

    def move_shoulder(self, leg_name, target_angle, speed_factor=1.0):
        """어깨(힙) 움직임"""
        if leg_name not in self.leg_motor_pins:
            print(f"알 수 없는 다리: {leg_name}")
            return False
        
        # 각도 제한 (-45도 ~ 45도)
        target_angle = max(-45.0, min(45.0, target_angle))
        
        # 현재 각도와 목표 각도 비교
        current_angle = self.leg_positions[leg_name]['hip']
        if abs(target_angle - current_angle) < 0.5:
            return True  # 이미 목표 각도에 도달
        
        # 움직임 실행
        success = self._move_joint(leg_name, 'hip', target_angle, speed_factor)
        
        if success:
            self.leg_positions[leg_name]['hip'] = target_angle
            print(f"{leg_name} 힙 각도: {current_angle:.1f}° → {target_angle:.1f}°")
        
        return success

    def move_elbow(self, leg_name, target_angle, speed_factor=1.0):
        """팔꿈치(무릎) 움직임"""
        if leg_name not in self.leg_motor_pins:
            print(f"알 수 없는 다리: {leg_name}")
            return False
        
        # 각도 제한 (-30도 ~ 60도)
        target_angle = max(-30.0, min(60.0, target_angle))
        
        # 현재 각도와 목표 각도 비교
        current_angle = self.leg_positions[leg_name]['knee']
        if abs(target_angle - current_angle) < 0.5:
            return True  # 이미 목표 각도에 도달
        
        # 움직임 실행
        success = self._move_joint(leg_name, 'knee', target_angle, speed_factor)
        
        if success:
            self.leg_positions[leg_name]['knee'] = target_angle
            print(f"{leg_name} 무릎 각도: {current_angle:.1f}° → {target_angle:.1f}°")
        
        return success

    def drop_leg(self, leg_name, target_height, speed_factor=1.0):
        """다리 내리기 (발목 조정)"""
        if leg_name not in self.leg_motor_pins:
            print(f"알 수 없는 다리: {leg_name}")
            return False
        
        # 높이 제한 (-20도 ~ 20도)
        target_height = max(-20.0, min(20.0, target_height))
        
        # 현재 높이와 목표 높이 비교
        current_height = self.leg_positions[leg_name]['ankle']
        if abs(target_height - current_height) < 0.5:
            return True  # 이미 목표 높이에 도달
        
        # 움직임 실행
        success = self._move_joint(leg_name, 'ankle', target_height, speed_factor)
        
        if success:
            self.leg_positions[leg_name]['ankle'] = target_height
            print(f"{leg_name} 발목 높이: {current_height:.1f}° → {target_height:.1f}°")
        
        return success

    def _move_joint(self, leg_name, joint_name, target_angle, speed_factor=1.0):
        """관절 움직임 실행"""
        try:
            if not hasattr(self, 'simulation_mode'):
                # 실제 하드웨어 제어
                pwm_obj = self.pwm_objects[leg_name][joint_name]
                
                # PWM 신호 생성 (서브모터 제어)
                duty_cycle = 2.5 + (target_angle / 180.0) * 10.0
                pwm_obj.ChangeDutyCycle(duty_cycle)
                
                # 모터 안정화 시간
                time.sleep(0.1)
                pwm_obj.ChangeDutyCycle(0)  # 신호 정지
                
            else:
                # 시뮬레이션 모드
                print(f"시뮬레이션: {leg_name} {joint_name}를 {target_angle}도로 이동")
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"관절 {leg_name} {joint_name} 움직임 오류: {e}")
            return False

    def start_walking(self, direction='forward', speed=1.0):
        """보행 시작"""
        if self.is_walking:
            print("이미 보행 중입니다.")
            return False
        
        self.is_walking = True
        self.walking_phase = 0
        self.leg_cycle = 0
        
        print(f"보행 시작: {direction}, 속도: {speed}")
        
        # 보행 시퀀스 실행
        return self._execute_walking_sequence(direction, speed)

    def _execute_walking_sequence(self, direction, speed):
        """보행 시퀀스 실행"""
        try:
            # 4단계 보행 패턴
            walking_pattern = self._get_walking_pattern(direction)
            
            for phase in walking_pattern:
                if not self.is_walking:
                    break
                
                # 각 단계별 다리 움직임
                for leg_name, movements in phase.items():
                    for joint_name, target_angle in movements.items():
                        if joint_name == 'hip':
                            self.move_shoulder(leg_name, target_angle, speed)
                        elif joint_name == 'knee':
                            self.move_elbow(leg_name, target_angle, speed)
                        elif joint_name == 'ankle':
                            self.drop_leg(leg_name, target_angle, speed)
                
                # 단계 간 지연
                time.sleep(0.2 / speed)
                self.walking_phase = (self.walking_phase + 1) % 4
            
            return True
            
        except Exception as e:
            print(f"보행 시퀀스 실행 오류: {e}")
            return False

    def _get_walking_pattern(self, direction):
        """보행 패턴 생성"""
        if direction == 'forward':
            # 전진 보행 패턴
            return [
                # 1단계: 앞왼쪽 다리 들어올리기
                {
                    'front_left': {'knee': self.step_height, 'ankle': 0},
                    'front_right': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_left': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_right': {'hip': 0, 'knee': 0, 'ankle': 0}
                },
                # 2단계: 앞왼쪽 다리 앞으로 이동
                {
                    'front_left': {'hip': self.step_length, 'knee': 0, 'ankle': 0},
                    'front_right': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_left': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_right': {'hip': 0, 'knee': 0, 'ankle': 0}
                },
                # 3단계: 앞왼쪽 다리 내리기
                {
                    'front_left': {'knee': 0, 'ankle': 0},
                    'front_right': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_left': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_right': {'hip': 0, 'knee': 0, 'ankle': 0}
                },
                # 4단계: 다음 다리 준비
                {
                    'front_left': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'front_right': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_left': {'hip': 0, 'knee': 0, 'ankle': 0},
                    'back_right': {'hip': 0, 'knee': 0, 'ankle': 0}
                }
            ]
        else:
            # 후진 보행 패턴 (방향만 반대)
            pattern = self._get_walking_pattern('forward')
            for phase in pattern:
                for leg_movements in phase.values():
                    if 'hip' in leg_movements:
                        leg_movements['hip'] = -leg_movements['hip']
            return pattern

    def stop_walking(self):
        """보행 정지"""
        if not self.is_walking:
            print("보행 중이 아닙니다.")
            return False
        
        self.is_walking = False
        print("보행 정지")
        
        # 모든 다리를 중립 위치로
        return self._return_to_neutral_position()

    def _return_to_neutral_position(self):
        """중립 위치로 복귀"""
        try:
            for leg_name in self.leg_motor_pins:
                self.move_shoulder(leg_name, 0.0)
                self.move_elbow(leg_name, 0.0)
                self.drop_leg(leg_name, 0.0)
            
            return True
            
        except Exception as e:
            print(f"중립 위치 복귀 오류: {e}")
            return False

    def get_leg_status(self):
        """다리 상태 정보 반환"""
        return {
            'leg_positions': self.leg_positions.copy(),
            'is_walking': self.is_walking,
            'walking_phase': self.walking_phase,
            'leg_cycle': self.leg_cycle
        }

    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'pwm_objects'):
            for leg_pwms in self.pwm_objects.values():
                for pwm in leg_pwms.values():
                    try:
                        pwm.stop()
                    except:
                        pass
        
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
        
        print("다리 모터 리소스 정리 완료") 
