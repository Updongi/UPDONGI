class BodyDetectInclination:
    """
    자이로센서 기반 기울기 인식 (threshold별 case 분류)
    MPU6050 6축 자이로센서를 사용한 정밀한 기울기 측정
    """
    def __init__(self):
        # MPU6050 센서 설정
        self.mpu6050_address = 0x68  # I2C 주소
        self.accel_scale = 16384.0    # ±2g 스케일
        self.gyro_scale = 131.0       # ±250°/s 스케일
        
        # 기울기 임계값 설정
        self.inclination_thresholds = {
            'level': 2.0,          # 수평 (도)
            'slight': 5.0,         # 약간 기울어짐 (도)
            'moderate': 15.0,      # 중간 기울기 (도)
            'steep': 30.0,         # 급한 기울기 (도)
            'critical': 45.0       # 위험한 기울기 (도)
        }
        
        # 필터링 파라미터
        self.alpha = 0.96          # 상보필터 계수
        self.sample_rate = 100     # 샘플링 레이트 (Hz)
        
        # 센서 데이터
        self.raw_accel = {'x': 0, 'y': 0, 'z': 0}
        self.raw_gyro = {'x': 0, 'y': 0, 'z': 0}
        self.filtered_angles = {'roll': 0, 'pitch': 0, 'yaw': 0}
        self.calibrated_offsets = {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}
        
        # 센서 초기화
        self._initialize_sensor()
        
        # 캘리브레이션 실행
        self._calibrate_sensor()
        
        print("MPU6050 기울기 감지 센서 초기화 완료")
    
    def _initialize_sensor(self):
        """MPU6050 센서 초기화"""
        try:
            import smbus2 as smbus
            self.bus = smbus.SMBus(1)  # 라즈베리파이 I2C 버스 1
            
            # 센서 웨이크업
            self.bus.write_byte_data(self.mpu6050_address, 0x6B, 0x00)
            time.sleep(0.1)
            
            # 가속도계 설정 (±2g)
            self.bus.write_byte_data(self.mpu6050_address, 0x1C, 0x00)
            
            # 자이로스코프 설정 (±250°/s)
            self.bus.write_byte_data(self.mpu6050_address, 0x1B, 0x00)
            
            # 샘플링 레이트 설정
            self.bus.write_byte_data(self.mpu6050_address, 0x19, 0x07)
            
            print("MPU6050 센서 초기화 성공")
            
        except ImportError:
            print("smbus2 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"MPU6050 센서 초기화 오류: {e}")
            self.simulation_mode = True
    
    def _calibrate_sensor(self):
        """센서 캘리브레이션"""
        print("센서 캘리브레이션 시작...")
        
        try:
            if not hasattr(self, 'simulation_mode'):
                # 실제 센서 캘리브레이션
                accel_samples = []
                gyro_samples = []
                
                # 100개 샘플 수집
                for _ in range(100):
                    accel_data = self._read_raw_accelerometer()
                    gyro_data = self._read_raw_gyroscope()
                    
                    accel_samples.append(accel_data)
                    gyro_samples.append(gyro_data)
                    
                    time.sleep(0.01)
                
                # 평균값 계산하여 오프셋 설정
                for axis in ['x', 'y', 'z']:
                    accel_avg = sum(sample[axis] for sample in accel_samples) / len(accel_samples)
                    gyro_avg = sum(sample[axis] for sample in gyro_samples) / len(gyro_samples)
                    
                    self.calibrated_offsets['accel'][axis] = accel_avg
                    self.calibrated_offsets['gyro'][axis] = gyro_avg
                
                print("센서 캘리브레이션 완료")
            else:
                # 시뮬레이션 모드
                print("시뮬레이션 모드: 센서 캘리브레이션 완료")
                
        except Exception as e:
            print(f"센서 캘리브레이션 오류: {e}")
    
    def _read_raw_accelerometer(self):
        """가속도계 원시 데이터 읽기"""
        try:
            if not hasattr(self, 'simulation_mode'):
                # 실제 센서에서 데이터 읽기
                accel_data = self.bus.read_i2c_block_data(self.mpu6050_address, 0x3B, 6)
                
                # 16비트 데이터 변환
                accel_x = self._convert_to_signed_16bit(accel_data[0], accel_data[1])
                accel_y = self._convert_to_signed_16bit(accel_data[2], accel_data[3])
                accel_z = self._convert_to_signed_16bit(accel_data[4], accel_data[5])
                
                return {'x': accel_x, 'y': accel_y, 'z': accel_z}
            else:
                # 시뮬레이션 데이터
                return {'x': 0, 'y': 0, 'z': 16384}  # 1g (지구 중력)
                
        except Exception as e:
            print(f"가속도계 읽기 오류: {e}")
            return {'x': 0, 'y': 0, 'z': 0}
    
    def _read_raw_gyroscope(self):
        """자이로스코프 원시 데이터 읽기"""
        try:
            if not hasattr(self, 'simulation_mode'):
                # 실제 센서에서 데이터 읽기
                gyro_data = self.bus.read_i2c_block_data(self.mpu6050_address, 0x43, 6)
                
                # 16비트 데이터 변환
                gyro_x = self._convert_to_signed_16bit(gyro_data[0], gyro_data[1])
                gyro_y = self._convert_to_signed_16bit(gyro_data[2], gyro_data[3])
                gyro_z = self._convert_to_signed_16bit(gyro_data[4], gyro_data[5])
                
                return {'x': gyro_x, 'y': gyro_y, 'z': z}
            else:
                # 시뮬레이션 데이터
                return {'x': 0, 'y': 0, 'z': 0}
                
        except Exception as e:
            print(f"자이로스코프 읽기 오류: {e}")
            return {'x': 0, 'y': 0, 'z': 0}
    
    def _convert_to_signed_16bit(self, msb, lsb):
        """16비트 데이터를 부호 있는 정수로 변환"""
        value = (msb << 8) | lsb
        if value > 32767:
            value -= 65536
        return value
    
    def read_gyro(self):
        """센서 데이터 읽기 및 필터링"""
        try:
            # 원시 데이터 읽기
            accel_data = self._read_raw_accelerometer()
            gyro_data = self._read_raw_gyroscope()
            
            # 캘리브레이션 오프셋 적용
            for axis in ['x', 'y', 'z']:
                accel_data[axis] -= self.calibrated_offsets['accel'][axis]
                gyro_data[axis] -= self.calibrated_offsets['gyro'][axis]
            
            # 가속도 기반 각도 계산
            accel_roll = math.atan2(accel_data['y'], accel_data['z']) * 180 / math.pi
            accel_pitch = math.atan2(-accel_data['x'], math.sqrt(accel_data['y']**2 + accel_data['z']**2)) * 180 / math.pi
            
            # 자이로 기반 각도 변화율
            gyro_roll_rate = gyro_data['x'] / self.gyro_scale
            gyro_pitch_rate = gyro_data['y'] / self.gyro_scale
            gyro_yaw_rate = gyro_data['z'] / self.gyro_scale
            
            # 상보필터 적용
            dt = 1.0 / self.sample_rate
            self.filtered_angles['roll'] = self.alpha * (self.filtered_angles['roll'] + gyro_roll_rate * dt) + (1 - self.alpha) * accel_roll
            self.filtered_angles['pitch'] = self.alpha * (self.filtered_angles['pitch'] + gyro_pitch_rate * dt) + (1 - self.alpha) * accel_pitch
            self.filtered_angles['yaw'] += gyro_yaw_rate * dt
            
            # 데이터 저장
            self.raw_accel = accel_data
            self.raw_gyro = gyro_data
            
            return {
                'angles': self.filtered_angles.copy(),
                'accel': accel_data,
                'gyro': gyro_data,
                'accel_angles': {'roll': accel_roll, 'pitch': accel_pitch},
                'gyro_rates': {'roll': gyro_roll_rate, 'pitch': gyro_pitch_rate, 'yaw': gyro_yaw_rate}
            }
            
        except Exception as e:
            print(f"센서 데이터 읽기 오류: {e}")
            return None
    
    def classify_inclination(self, gyro_data=None):
        """기울기 case 분류"""
        if gyro_data is None:
            gyro_data = self.read_gyro()
        
        if gyro_data is None:
            return 'unknown'
        
        # 현재 각도 가져오기
        roll = abs(gyro_data['angles']['roll'])
        pitch = abs(gyro_data['angles']['pitch'])
        
        # 최대 기울기 계산
        max_inclination = max(roll, pitch)
        
        # 기울기 레벨 분류
        if max_inclination <= self.inclination_thresholds['level']:
            return 'level'
        elif max_inclination <= self.inclination_thresholds['slight']:
            return 'slight'
        elif max_inclination <= self.inclination_thresholds['moderate']:
            return 'moderate'
        elif max_inclination <= self.inclination_thresholds['steep']:
            return 'steep'
        elif max_inclination <= self.inclination_thresholds['critical']:
            return 'critical'
        else:
            return 'extreme'
    
    def get_inclination_details(self):
        """기울기 상세 정보 반환"""
        gyro_data = self.read_gyro()
        if gyro_data is None:
            return None
        
        inclination_case = self.classify_inclination(gyro_data)
        
        return {
            'case': inclination_case,
            'angles': gyro_data['angles'],
            'accel_data': gyro_data['accel'],
            'gyro_data': gyro_data['gyro'],
            'thresholds': self.inclination_thresholds.copy(),
            'is_stable': self._check_stability(gyro_data)
        }
    
    def _check_stability(self, gyro_data):
        """로봇 안정성 체크"""
        roll = abs(gyro_data['angles']['roll'])
        pitch = abs(gyro_data['angles']['pitch'])
        
        # 안정성 기준: roll과 pitch가 모두 level 임계값 이하
        return (roll <= self.inclination_thresholds['level'] and 
                pitch <= self.inclination_thresholds['level'])
    
    def set_inclination_thresholds(self, new_thresholds):
        """기울기 임계값 설정"""
        for key, value in new_thresholds.items():
            if key in self.inclination_thresholds:
                if 0 <= value <= 90:
                    self.inclination_thresholds[key] = value
                    print(f"{key} 임계값을 {value}도로 설정했습니다.")
                else:
                    print(f"{key} 임계값은 0~90도 범위 내에서 설정해야 합니다.")
    
    def get_sensor_status(self):
        """센서 상태 정보 반환"""
        return {
            'calibrated_offsets': self.calibrated_offsets.copy(),
            'filtered_angles': self.filtered_angles.copy(),
            'sample_rate': self.sample_rate,
            'alpha': self.alpha,
            'thresholds': self.inclination_thresholds.copy()
        }
    
    def reset_calibration(self):
        """캘리브레이션 리셋"""
        self.calibrated_offsets = {'accel': {'x': 0, 'y': 0, 'z': 0}, 'gyro': {'x': 0, 'y': 0, 'z': 0}}
        self.filtered_angles = {'roll': 0, 'pitch': 0, 'yaw': 0}
        print("센서 캘리브레이션이 리셋되었습니다.")
        
        # 재캘리브레이션 실행
        self._calibrate_sensor()
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'bus'):
            try:
                self.bus.close()
            except:
                pass
        
        print("MPU6050 센서 리소스 정리 완료") 
