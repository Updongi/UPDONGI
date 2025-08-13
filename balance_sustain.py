def maintain_balance():
    """
    몸의 평형 유지 로직
    MPU6050 센서와 FSR 압력센서를 사용한 실시간 균형 제어
    """
    import time
    import math
    from detect_inclination import BodyDetectInclination
    from activate_motor import BodyActivateMotor
    from activate_steering import BodyActivateSteering
    
    class BalanceSustainController:
        def __init__(self):
            # 하위 시스템 초기화
            self.inclination_sensor = BodyDetectInclination()
            self.motor_controller = BodyActivateMotor()
            self.steering_controller = BodyActivateSteering()
            
            # 균형 제어 파라미터
            self.balance_threshold = 3.0      # 균형 임계값 (도)
            self.correction_strength = 0.8    # 보정 강도 (0.0 ~ 1.0)
            self.update_rate = 50             # 업데이트 주기 (Hz)
            self.stabilization_time = 0.5     # 안정화 시간 (초)
            
            # 균형 상태
            self.is_balanced = True
            self.last_correction_time = 0
            self.correction_history = []
            
            # PID 제어 파라미터
            self.pid_params = {
                'roll': {'Kp': 2.0, 'Ki': 0.1, 'Kd': 0.5},
                'pitch': {'Kp': 2.0, 'Ki': 0.1, 'Kd': 0.5},
                'yaw': {'Kp': 1.5, 'Ki': 0.05, 'Kd': 0.3}
            }
            
            # PID 제어 상태
            self.pid_state = {
                'roll': {'error_sum': 0, 'last_error': 0},
                'pitch': {'error_sum': 0, 'last_error': 0},
                'yaw': {'error_sum': 0, 'last_error': 0}
            }
            
            print("균형 유지 컨트롤러 초기화 완료")
        
        def start_balance_monitoring(self):
            """균형 모니터링 시작"""
            print("균형 모니터링 시작")
            
            try:
                while True:
                    # 현재 균형 상태 확인
                    balance_status = self._check_balance_status()
                    
                    if not balance_status['is_balanced']:
                        # 균형 보정 실행
                        self._correct_balance(balance_status)
                    
                    # 안정화 대기
                    time.sleep(1.0 / self.update_rate)
                    
            except KeyboardInterrupt:
                print("\n균형 모니터링 중단")
            except Exception as e:
                print(f"균형 모니터링 오류: {e}")
            finally:
                self.cleanup()
        
        def _check_balance_status(self):
            """균형 상태 확인"""
            try:
                # 센서 데이터 읽기
                sensor_data = self.inclination_sensor.read_gyro()
                
                if sensor_data is None:
                    return {'is_balanced': False, 'error': '센서 데이터 읽기 실패'}
                
                # 현재 각도 가져오기
                angles = sensor_data['angles']
                roll = angles['roll']
                pitch = angles['pitch']
                yaw = angles['yaw']
                
                # 균형 상태 판단
                roll_balanced = abs(roll) <= self.balance_threshold
                pitch_balanced = abs(pitch) <= self.balance_threshold
                yaw_balanced = abs(yaw) <= self.balance_threshold
                
                is_balanced = roll_balanced and pitch_balanced and yaw_balanced
                
                # 균형 상태 업데이트
                self.is_balanced = is_balanced
                
                return {
                    'is_balanced': is_balanced,
                    'angles': angles,
                    'roll_balanced': roll_balanced,
                    'pitch_balanced': pitch_balanced,
                    'yaw_balanced': yaw_balanced,
                    'max_deviation': max(abs(roll), abs(pitch), abs(yaw))
                }
                
            except Exception as e:
                print(f"균형 상태 확인 오류: {e}")
                return {'is_balanced': False, 'error': str(e)}
        
        def _correct_balance(self, balance_status):
            """균형 보정 실행"""
            try:
                current_time = time.time()
                
                # 보정 간격 확인
                if current_time - self.last_correction_time < self.stabilization_time:
                    return
                
                angles = balance_status['angles']
                roll_error = angles['roll']
                pitch_error = angles['pitch']
                yaw_error = angles['yaw']
                
                print(f"균형 보정 시작 - Roll: {roll_error:.1f}°, Pitch: {pitch_error:.1f}°, Yaw: {yaw_error:.1f}°")
                
                # PID 제어로 보정 각도 계산
                correction_angles = self._calculate_pid_correction(roll_error, pitch_error, yaw_error)
                
                # 모터 제어로 균형 보정
                success = self._apply_balance_correction(correction_angles)
                
                if success:
                    self.last_correction_time = current_time
                    
                    # 보정 기록 저장
                    correction_record = {
                        'timestamp': current_time,
                        'angles': angles,
                        'correction': correction_angles,
                        'success': success
                    }
                    self.correction_history.append(correction_record)
                    
                    # 보정 기록 최대 100개 유지
                    if len(self.correction_history) > 100:
                        self.correction_history.pop(0)
                    
                    print("균형 보정 완료")
                else:
                    print("균형 보정 실패")
                
            except Exception as e:
                print(f"균형 보정 오류: {e}")
        
        def _calculate_pid_correction(self, roll_error, pitch_error, yaw_error):
            """PID 제어로 보정 각도 계산"""
            correction = {}
            
            # Roll 축 PID 제어
            roll_correction = self._pid_control('roll', roll_error)
            correction['roll'] = roll_correction
            
            # Pitch 축 PID 제어
            pitch_correction = self._pid_control('pitch', pitch_error)
            correction['pitch'] = pitch_correction
            
            # Yaw 축 PID 제어
            yaw_correction = self._pid_control('yaw', yaw_error)
            correction['yaw'] = yaw_correction
            
            return correction
        
        def _pid_control(self, axis, error):
            """PID 제어 계산"""
            params = self.pid_params[axis]
            state = self.pid_state[axis]
            
            # 비례 제어 (P)
            p_term = params['Kp'] * error
            
            # 적분 제어 (I)
            state['error_sum'] += error
            i_term = params['Ki'] * state['error_sum']
            
            # 미분 제어 (D)
            d_term = params['Kd'] * (error - state['last_error'])
            state['last_error'] = error
            
            # PID 출력 계산
            output = p_term + i_term + d_term
            
            # 출력 제한
            output = max(-30.0, min(30.0, output))
            
            return output
        
        def _apply_balance_correction(self, correction_angles):
            """균형 보정 적용"""
            try:
                # Roll 보정 (좌우 기울기)
                if abs(correction_angles['roll']) > 0.5:
                    self._apply_roll_correction(correction_angles['roll'])
                
                # Pitch 보정 (앞뒤 기울기)
                if abs(correction_angles['pitch']) > 0.5:
                    self._apply_pitch_correction(correction_angles['pitch'])
                
                # Yaw 보정 (회전)
                if abs(correction_angles['yaw']) > 0.5:
                    self._apply_yaw_correction(correction_angles['yaw'])
                
                return True
                
            except Exception as e:
                print(f"균형 보정 적용 오류: {e}")
                return False
        
        def _apply_roll_correction(self, roll_correction):
            """Roll 축 보정 적용"""
            # 좌우 다리 높이 조정
            if roll_correction > 0:  # 오른쪽으로 기울어짐
                # 왼쪽 다리들을 높이고 오른쪽 다리들을 낮춤
                self.motor_controller.set_motor_angle('front_left_ankle', 15)
                self.motor_controller.set_motor_angle('back_left_ankle', 15)
                self.motor_controller.set_motor_angle('front_right_ankle', -15)
                self.motor_controller.set_motor_angle('back_right_ankle', -15)
            else:  # 왼쪽으로 기울어짐
                # 오른쪽 다리들을 높이고 왼쪽 다리들을 낮춤
                self.motor_controller.set_motor_angle('front_right_ankle', 15)
                self.motor_controller.set_motor_angle('back_right_ankle', 15)
                self.motor_controller.set_motor_angle('front_left_ankle', -15)
                self.motor_controller.set_motor_angle('back_left_ankle', -15)
        
        def _apply_pitch_correction(self, pitch_correction):
            """Pitch 축 보정 적용"""
            # 앞뒤 다리 높이 조정
            if pitch_correction > 0:  # 앞으로 기울어짐
                # 앞다리들을 높이고 뒷다리들을 낮춤
                self.motor_controller.set_motor_angle('front_left_knee', 30)
                self.motor_controller.set_motor_angle('front_right_knee', 30)
                self.motor_controller.set_motor_angle('back_left_knee', -20)
                self.motor_controller.set_motor_angle('back_right_knee', -20)
            else:  # 뒤로 기울어짐
                # 뒷다리들을 높이고 앞다리들을 낮춤
                self.motor_controller.set_motor_angle('back_left_knee', 30)
                self.motor_controller.set_motor_angle('back_right_knee', 30)
                self.motor_controller.set_motor_angle('front_left_knee', -20)
                self.motor_controller.set_motor_angle('front_right_knee', -20)
        
        def _apply_yaw_correction(self, yaw_correction):
            """Yaw 축 보정 적용"""
            # 조향 제어로 회전 보정
            self.steering_controller.adjust_steering(-yaw_correction * 0.5)
        
        def get_balance_status(self):
            """균형 상태 정보 반환"""
            return {
                'is_balanced': self.is_balanced,
                'balance_threshold': self.balance_threshold,
                'correction_strength': self.correction_strength,
                'update_rate': self.update_rate,
                'last_correction_time': self.last_correction_time,
                'correction_history_count': len(self.correction_history)
            }
        
        def set_balance_parameters(self, threshold=None, strength=None, rate=None):
            """균형 제어 파라미터 설정"""
            if threshold is not None:
                self.balance_threshold = max(1.0, min(10.0, threshold))
                print(f"균형 임계값을 {self.balance_threshold}도로 설정했습니다.")
            
            if strength is not None:
                self.correction_strength = max(0.1, min(1.0, strength))
                print(f"보정 강도를 {self.correction_strength}로 설정했습니다.")
            
            if rate is not None:
                self.update_rate = max(10, min(100, rate))
                print(f"업데이트 주기를 {self.update_rate}Hz로 설정했습니다.")
        
        def emergency_stabilize(self):
            """비상 안정화"""
            print("비상 안정화 실행")
            
            try:
                # 모든 모터를 중립 위치로
                self.motor_controller.emergency_stop()
                
                # 조향을 중립으로
                self.steering_controller.reset_steering()
                
                # 안정화 대기
                time.sleep(2.0)
                
                print("비상 안정화 완료")
                return True
                
            except Exception as e:
                print(f"비상 안정화 오류: {e}")
                return False
        
        def cleanup(self):
            """리소스 정리"""
            try:
                self.inclination_sensor.cleanup()
                self.motor_controller.cleanup()
                self.steering_controller.cleanup()
                
            except Exception as e:
                print(f"리소스 정리 오류: {e}")
            
            print("균형 유지 컨트롤러 리소스 정리 완료")
    
    # 전역 인스턴스 생성
    balance_controller = BalanceSustainController()
    
    # 사용 예시
    def demo_balance_maintenance():
        """균형 유지 데모"""
        try:
            # 균형 모니터링 시작
            balance_controller.start_balance_monitoring()
            
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            balance_controller.emergency_stabilize()
        except Exception as e:
            print(f"균형 유지 중 오류 발생: {e}")
            balance_controller.emergency_stabilize()
        finally:
            balance_controller.cleanup()
    
    return balance_controller

# 메인 실행
if __name__ == "__main__":
    controller = maintain_balance()
    demo_balance_maintenance() 