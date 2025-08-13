def straight_walk():
    """
    직선 보행 모드 (10~15cm 보폭 조정 포함)
    사족 보행 로봇의 기본적인 직선 보행 기능
    """
    import time
    from leg_moving import LegMoving
    from activate_motor import BodyActivateMotor
    from activate_steering import BodyActivateSteering
    
    class StraightWalkController:
        def __init__(self):
            # 하위 시스템 초기화
            self.leg_controller = LegMoving()
            self.motor_controller = BodyActivateMotor()
            self.steering_controller = BodyActivateSteering()
            
            # 보행 파라미터
            self.step_length = 12.0      # 보폭 (cm)
            self.step_height = 8.0       # 다리 들어올리는 높이 (cm)
            self.walking_speed = 1.0     # 보행 속도 (0.5 ~ 2.0)
            self.step_interval = 0.3     # 걸음 간격 (초)
            
            # 보행 상태
            self.is_walking = False
            self.current_step = 0
            self.total_steps = 0
            self.target_distance = 0.0   # 목표 거리 (cm)
            
            # 보행 패턴 (4단계)
            self.walking_pattern = self._create_walking_pattern()
            
            print("직선 보행 컨트롤러 초기화 완료")
        
        def _create_walking_pattern(self):
            """보행 패턴 생성"""
            # 각 단계별 다리 움직임 정의
            pattern = {
                0: {  # 1단계: 앞왼쪽 다리 들어올리기
                    'front_left': {'action': 'lift', 'height': self.step_height, 'angle': 0},
                    'front_right': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_left': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_right': {'action': 'support', 'height': 0, 'angle': 0}
                },
                1: {  # 2단계: 앞왼쪽 다리 앞으로 이동
                    'front_left': {'action': 'move_forward', 'height': self.step_height, 'angle': self.step_length},
                    'front_right': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_left': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_right': {'action': 'support', 'height': 0, 'angle': 0}
                },
                2: {  # 3단계: 앞왼쪽 다리 내리기
                    'front_left': {'action': 'place', 'height': 0, 'angle': self.step_length},
                    'front_right': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_left': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_right': {'action': 'support', 'height': 0, 'angle': 0}
                },
                3: {  # 4단계: 다음 다리 준비
                    'front_left': {'action': 'support', 'height': 0, 'angle': self.step_length},
                    'front_right': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_left': {'action': 'support', 'height': 0, 'angle': 0},
                    'back_right': {'action': 'support', 'height': 0, 'angle': 0}
                }
            }
            return pattern
        
        def start_walking(self, distance_cm=100.0, speed=1.0):
            """직선 보행 시작"""
            if self.is_walking:
                print("이미 보행 중입니다.")
                return False
            
            self.target_distance = distance_cm
            self.walking_speed = max(0.5, min(2.0, speed))
            self.step_interval = 0.3 / self.walking_speed
            
            # 총 걸음 수 계산 (보폭 기준)
            self.total_steps = int(distance_cm / self.step_length)
            
            print(f"직선 보행 시작: {distance_cm}cm, 속도: {self.walking_speed}, 총 걸음: {self.total_steps}")
            
            self.is_walking = True
            self.current_step = 0
            
            # 보행 루프 시작
            return self._walking_loop()
        
        def _walking_loop(self):
            """보행 루프"""
            try:
                while self.is_walking and self.current_step < self.total_steps:
                    # 현재 보행 단계 실행
                    success = self._execute_walking_step()
                    
                    if not success:
                        print("보행 단계 실행 실패")
                        self.stop_walking()
                        return False
                    
                    # 다음 단계로 진행
                    self.current_step += 1
                    
                    # 진행률 표시
                    progress = (self.current_step / self.total_steps) * 100
                    print(f"보행 진행률: {progress:.1f}% ({self.current_step}/{self.total_steps})")
                    
                    # 단계 간 지연
                    time.sleep(self.step_interval)
                
                if self.current_step >= self.total_steps:
                    print("목표 거리에 도달했습니다.")
                    self.stop_walking()
                    return True
                
                return True
                
            except Exception as e:
                print(f"보행 루프 오류: {e}")
                self.stop_walking()
                return False
        
        def _execute_walking_step(self):
            """보행 단계 실행"""
            try:
                # 현재 단계의 패턴 가져오기
                step_pattern = self.walking_pattern[self.current_step % 4]
                
                # 각 다리별 동작 실행
                for leg_name, leg_action in step_pattern.items():
                    success = self._execute_leg_action(leg_name, leg_action)
                    if not success:
                        return False
                
                # 균형 보정
                self._balance_adjustment()
                
                return True
                
            except Exception as e:
                print(f"보행 단계 실행 오류: {e}")
                return False
        
        def _execute_leg_action(self, leg_name, leg_action):
            """다리 동작 실행"""
            try:
                action = leg_action['action']
                height = leg_action['height']
                angle = leg_action['angle']
                
                if action == 'lift':
                    # 다리 들어올리기
                    return self.leg_controller.move_elbow(leg_name, height)
                
                elif action == 'move_forward':
                    # 다리 앞으로 이동
                    hip_success = self.leg_controller.move_shoulder(leg_name, angle)
                    knee_success = self.leg_controller.move_elbow(leg_name, height)
                    return hip_success and knee_success
                
                elif action == 'place':
                    # 다리 내리기
                    return self.leg_controller.drop_leg(leg_name, 0)
                
                elif action == 'support':
                    # 지지 상태 유지
                    return True
                
                else:
                    print(f"알 수 없는 다리 동작: {action}")
                    return False
                
            except Exception as e:
                print(f"다리 동작 실행 오류: {e}")
                return False
        
        def _balance_adjustment(self):
            """균형 보정"""
            try:
                # IMU 데이터 읽기 (시뮬레이션)
                roll_error = 0.0  # 실제로는 IMU에서 읽어와야 함
                pitch_error = 0.0
                yaw_error = 0.0
                
                # 균형 보정 실행
                if abs(roll_error) > 2.0 or abs(pitch_error) > 2.0:
                    self.motor_controller.recover_balance(roll_error, pitch_error)
                
                # 조향 보정
                if abs(yaw_error) > 1.0:
                    self.steering_controller.balance_for_two_legs(roll_error, pitch_error, yaw_error)
                
            except Exception as e:
                print(f"균형 보정 오류: {e}")
        
        def stop_walking(self):
            """보행 정지"""
            if not self.is_walking:
                print("보행 중이 아닙니다.")
                return False
            
            self.is_walking = False
            print("직선 보행 정지")
            
            # 모든 다리를 중립 위치로
            return self.leg_controller.stop_walking()
        
        def adjust_step_length(self, new_length_cm):
            """보폭 조정"""
            if 8.0 <= new_length_cm <= 20.0:
                self.step_length = new_length_cm
                print(f"보폭을 {new_length_cm}cm로 조정했습니다.")
                
                # 보행 패턴 재생성
                self.walking_pattern = self._create_walking_pattern()
                return True
            else:
                print("보폭은 8.0cm ~ 20.0cm 범위 내에서 설정해야 합니다.")
                return False
        
        def adjust_walking_speed(self, new_speed):
            """보행 속도 조정"""
            if 0.5 <= new_speed <= 2.0:
                self.walking_speed = new_speed
                self.step_interval = 0.3 / self.walking_speed
                print(f"보행 속도를 {new_speed}로 조정했습니다.")
                return True
            else:
                print("보행 속도는 0.5 ~ 2.0 범위 내에서 설정해야 합니다.")
                return False
        
        def get_walking_status(self):
            """보행 상태 정보 반환"""
            return {
                'is_walking': self.is_walking,
                'current_step': self.current_step,
                'total_steps': self.total_steps,
                'target_distance': self.target_distance,
                'progress_percentage': (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0,
                'step_length': self.step_length,
                'walking_speed': self.walking_speed
            }
        
        def emergency_stop(self):
            """비상 정지"""
            print("비상 정지 실행")
            self.stop_walking()
            self.motor_controller.emergency_stop()
            return True
        
        def cleanup(self):
            """리소스 정리"""
            self.stop_walking()
            self.leg_controller.cleanup()
            self.motor_controller.cleanup()
            self.steering_controller.cleanup()
            print("직선 보행 컨트롤러 리소스 정리 완료")
    
    # 전역 인스턴스 생성
    walk_controller = StraightWalkController()
    
    # 사용 예시
    def demo_straight_walk():
        """직선 보행 데모"""
        try:
            # 100cm 직선 보행 시작
            success = walk_controller.start_walking(distance_cm=100.0, speed=1.0)
            
            if success:
                print("직선 보행 완료")
            else:
                print("직선 보행 실패")
                
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            walk_controller.emergency_stop()
        except Exception as e:
            print(f"보행 중 오류 발생: {e}")
            walk_controller.emergency_stop()
        finally:
            walk_controller.cleanup()
    
    return walk_controller

# 메인 실행
if __name__ == "__main__":
    controller = straight_walk()
    demo_straight_walk() 