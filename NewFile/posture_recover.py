def execute_recovery():
    """
    복구 모터 실행
    MPU6050 센서와 모터 제어를 통한 자세 복구 시스템
    """
    import time
    import math
    from detect_inclination import BodyDetectInclination
    from activate_motor import BodyActivateMotor
    from activate_steering import BodyActivateSteering
    
    class PostureRecoveryController:
        def __init__(self):
            # 하위 시스템 초기화
            self.inclination_sensor = BodyDetectInclination()
            self.motor_controller = BodyActivateMotor()
            self.steering_controller = BodyActivateSteering()
            
            # 복구 파라미터
            self.recovery_threshold = 5.0      # 복구 시작 임계값 (도)
            self.max_recovery_attempts = 3     # 최대 복구 시도 횟수
            self.recovery_timeout = 10.0       # 복구 타임아웃 (초)
            self.stabilization_delay = 1.0     # 안정화 대기 시간 (초)
            
            # 복구 상태
            self.is_recovering = False
            self.recovery_attempts = 0
            self.last_recovery_time = 0
            self.recovery_history = []
            
            # 복구 시퀀스 정의
            self.recovery_sequences = self._define_recovery_sequences()
            
            print("자세 복구 컨트롤러 초기화 완료")
        
        def _define_recovery_sequences(self):
            """복구 시퀀스 정의"""
            sequences = {
                'roll_left': [  # 왼쪽으로 기울어짐
                    ('front_left_ankle', 20, 0.2),
                    ('back_left_ankle', 20, 0.2),
                    ('front_right_ankle', -20, 0.2),
                    ('back_right_ankle', -20, 0.2)
                ],
                'roll_right': [  # 오른쪽으로 기울어짐
                    ('front_right_ankle', 20, 0.2),
                    ('back_right_ankle', 20, 0.2),
                    ('front_left_ankle', -20, 0.2),
                    ('back_left_ankle', -20, 0.2)
                ],
                'pitch_forward': [  # 앞으로 기울어짐
                    ('front_left_knee', 35, 0.2),
                    ('front_right_knee', 35, 0.2),
                    ('back_left_knee', -25, 0.2),
                    ('back_right_knee', -25, 0.2)
                ],
                'pitch_backward': [  # 뒤로 기울어짐
                    ('back_left_knee', 35, 0.2),
                    ('back_right_knee', 35, 0.2),
                    ('front_left_knee', -25, 0.2),
                    ('front_right_knee', -25, 0.2)
                ],
                'yaw_left': [  # 왼쪽으로 회전
                    ('front_left_hip', 25, 0.2),
                    ('back_left_hip', 25, 0.2),
                    ('front_right_hip', -25, 0.2),
                    ('back_right_hip', -25, 0.2)
                ],
                'yaw_right': [  # 오른쪽으로 회전
                    ('front_right_hip', 25, 0.2),
                    ('back_right_hip', 25, 0.2),
                    ('front_left_hip', -25, 0.2),
                    ('back_left_hip', -25, 0.2)
                ]
            }
            return sequences
        
        def check_posture_status(self):
            """자세 상태 확인"""
            try:
                # 센서 데이터 읽기
                sensor_data = self.inclination_sensor.read_gyro()
                
                if sensor_data is None:
                    return {'status': 'error', 'message': '센서 데이터 읽기 실패'}
                
                # 현재 각도 가져오기
                angles = sensor_data['angles']
                roll = angles['roll']
                pitch = angles['pitch']
                yaw = angles['yaw']
                
                # 자세 상태 판단
                posture_status = self._analyze_posture(roll, pitch, yaw)
                
                return {
                    'status': 'normal' if posture_status['is_stable'] else 'unstable',
                    'angles': angles,
                    'posture_analysis': posture_status,
                    'timestamp': time.time()
                }
                
            except Exception as e:
                print(f"자세 상태 확인 오류: {e}")
                return {'status': 'error', 'message': str(e)}
        
        def _analyze_posture(self, roll, pitch, yaw):
            """자세 분석"""
            # 각 축별 안정성 판단
            roll_stable = abs(roll) <= self.recovery_threshold
            pitch_stable = abs(pitch) <= self.recovery_threshold
            yaw_stable = abs(yaw) <= self.recovery_threshold
            
            # 전체 안정성
            is_stable = roll_stable and pitch_stable and yaw_stable
            
            # 기울기 방향 판단
            roll_direction = 'left' if roll < -self.recovery_threshold else 'right' if roll > self.recovery_threshold else 'stable'
            pitch_direction = 'forward' if pitch > self.recovery_threshold else 'backward' if pitch < -self.recovery_threshold else 'stable'
            yaw_direction = 'left' if yaw < -self.recovery_threshold else 'right' if yaw > self.recovery_threshold else 'stable'
            
            return {
                'is_stable': is_stable,
                'roll': {'stable': roll_stable, 'direction': roll_direction, 'angle': roll},
                'pitch': {'stable': pitch_stable, 'direction': pitch_direction, 'angle': pitch},
                'yaw': {'stable': yaw_stable, 'direction': yaw_direction, 'angle': yaw}
            }
        
        def execute_recovery_sequence(self, posture_analysis):
            """복구 시퀀스 실행"""
            if self.is_recovering:
                print("이미 복구 중입니다.")
                return False
            
            # 복구 필요성 확인
            if posture_analysis['is_stable']:
                print("자세가 안정적입니다. 복구가 필요하지 않습니다.")
                return True
            
            # 복구 시도 횟수 확인
            if self.recovery_attempts >= self.max_recovery_attempts:
                print(f"최대 복구 시도 횟수({self.max_recovery_attempts})에 도달했습니다.")
                return False
            
            # 복구 시작
            self.is_recovering = True
            self.recovery_attempts += 1
            start_time = time.time()
            
            print(f"자세 복구 시작 (시도 {self.recovery_attempts}/{self.max_recovery_attempts})")
            
            try:
                # 복구 시퀀스 결정
                recovery_sequence = self._determine_recovery_sequence(posture_analysis)
                
                if recovery_sequence:
                    # 복구 실행
                    success = self._run_recovery_sequence(recovery_sequence)
                    
                    if success:
                        # 안정화 대기
                        time.sleep(self.stabilization_delay)
                        
                        # 복구 결과 확인
                        final_status = self.check_posture_status()
                        recovery_successful = final_status['status'] == 'normal'
                        
                        # 복구 기록 저장
                        recovery_record = {
                            'timestamp': time.time(),
                            'attempt': self.recovery_attempts,
                            'initial_posture': posture_analysis,
                            'recovery_sequence': recovery_sequence,
                            'final_status': final_status,
                            'success': recovery_successful,
                            'duration': time.time() - start_time
                        }
                        self.recovery_history.append(recovery_record)
                        
                        if recovery_successful:
                            print("자세 복구 성공")
                            self.recovery_attempts = 0  # 성공 시 카운터 리셋
                        else:
                            print("자세 복구 실패 - 자세가 여전히 불안정합니다")
                        
                        return recovery_successful
                    else:
                        print("복구 시퀀스 실행 실패")
                        return False
                else:
                    print("적절한 복구 시퀀스를 찾을 수 없습니다.")
                    return False
                    
            except Exception as e:
                print(f"복구 실행 오류: {e}")
                return False
            finally:
                self.is_recovering = False
        
        def _determine_recovery_sequence(self, posture_analysis):
            """복구 시퀀스 결정"""
            sequences = []
            
            # Roll 축 복구
            if not posture_analysis['roll']['stable']:
                direction = posture_analysis['roll']['direction']
                if direction == 'left':
                    sequences.extend(self.recovery_sequences['roll_left'])
                elif direction == 'right':
                    sequences.extend(self.recovery_sequences['roll_right'])
            
            # Pitch 축 복구
            if not posture_analysis['pitch']['stable']:
                direction = posture_analysis['pitch']['direction']
                if direction == 'forward':
                    sequences.extend(self.recovery_sequences['pitch_forward'])
                elif direction == 'backward':
                    sequences.extend(self.recovery_sequences['pitch_backward'])
            
            # Yaw 축 복구
            if not posture_analysis['yaw']['stable']:
                direction = posture_analysis['yaw']['direction']
                if direction == 'left':
                    sequences.extend(self.recovery_sequences['yaw_left'])
                elif direction == 'right':
                    sequences.extend(self.recovery_sequences['yaw_right'])
            
            return sequences
        
        def _run_recovery_sequence(self, recovery_sequence):
            """복구 시퀀스 실행"""
            try:
                print(f"복구 시퀀스 실행: {len(recovery_sequence)}개 단계")
                
                for i, (motor_name, target_angle, delay) in enumerate(recovery_sequence):
                    print(f"단계 {i+1}/{len(recovery_sequence)}: {motor_name} → {target_angle}°")
                    
                    # 모터 각도 설정
                    success = self.motor_controller.set_motor_angle(motor_name, target_angle)
                    
                    if not success:
                        print(f"모터 {motor_name} 제어 실패")
                        return False
                    
                    # 지연 대기
                    time.sleep(delay)
                
                print("복구 시퀀스 실행 완료")
                return True
                
            except Exception as e:
                print(f"복구 시퀀스 실행 오류: {e}")
                return False
        
        def auto_recovery_mode(self, duration=60.0):
            """자동 복구 모드"""
            print(f"자동 복구 모드 시작 (지속 시간: {duration}초)")
            
            start_time = time.time()
            
            try:
                while time.time() - start_time < duration:
                    # 현재 자세 상태 확인
                    posture_status = self.check_posture_status()
                    
                    if posture_status['status'] == 'unstable':
                        # 복구 실행
                        posture_analysis = posture_status['posture_analysis']
                        success = self.execute_recovery_sequence(posture_analysis)
                        
                        if not success:
                            print("복구 실패 - 비상 안정화 실행")
                            self.emergency_stabilization()
                    
                    # 대기
                    time.sleep(2.0)
                
                print("자동 복구 모드 종료")
                
            except KeyboardInterrupt:
                print("\n자동 복구 모드 중단")
            except Exception as e:
                print(f"자동 복구 모드 오류: {e}")
        
        def emergency_stabilization(self):
            """비상 안정화"""
            print("비상 안정화 실행")
            
            try:
                # 모든 모터를 중립 위치로
                self.motor_controller.emergency_stop()
                
                # 조향을 중립으로
                self.steering_controller.reset_steering()
                
                # 안정화 대기
                time.sleep(3.0)
                
                print("비상 안정화 완료")
                return True
                
            except Exception as e:
                print(f"비상 안정화 오류: {e}")
                return False
        
        def get_recovery_status(self):
            """복구 상태 정보 반환"""
            return {
                'is_recovering': self.is_recovering,
                'recovery_attempts': self.recovery_attempts,
                'max_recovery_attempts': self.max_recovery_attempts,
                'last_recovery_time': self.last_recovery_time,
                'recovery_history_count': len(self.recovery_history),
                'recovery_threshold': self.recovery_threshold
            }
        
        def set_recovery_parameters(self, threshold=None, max_attempts=None, timeout=None):
            """복구 파라미터 설정"""
            if threshold is not None:
                self.recovery_threshold = max(1.0, min(15.0, threshold))
                print(f"복구 임계값을 {self.recovery_threshold}도로 설정했습니다.")
            
            if max_attempts is not None:
                self.max_recovery_attempts = max(1, min(10, max_attempts))
                print(f"최대 복구 시도 횟수를 {self.max_recovery_attempts}로 설정했습니다.")
            
            if timeout is not None:
                self.recovery_timeout = max(5.0, min(30.0, timeout))
                print(f"복구 타임아웃을 {self.recovery_timeout}초로 설정했습니다.")
        
        def reset_recovery_counters(self):
            """복구 카운터 리셋"""
            self.recovery_attempts = 0
            self.last_recovery_time = 0
            print("복구 카운터가 리셋되었습니다.")
        
        def cleanup(self):
            """리소스 정리"""
            try:
                self.inclination_sensor.cleanup()
                self.motor_controller.cleanup()
                self.steering_controller.cleanup()
                
            except Exception as e:
                print(f"리소스 정리 오류: {e}")
            
            print("자세 복구 컨트롤러 리소스 정리 완료")
    
    # 전역 인스턴스 생성
    recovery_controller = PostureRecoveryController()
    
    # 사용 예시
    def demo_posture_recovery():
        """자세 복구 데모"""
        try:
            # 자동 복구 모드 시작 (60초)
            recovery_controller.auto_recovery_mode(duration=60.0)
            
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            recovery_controller.emergency_stabilization()
        except Exception as e:
            print(f"자세 복구 중 오류 발생: {e}")
            recovery_controller.emergency_stabilization()
        finally:
            recovery_controller.cleanup()
    
    return recovery_controller

# 메인 실행
if __name__ == "__main__":
    controller = execute_recovery()
    demo_posture_recovery() 
