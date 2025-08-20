class CameraImportImageData:
    """
    카메라 이미지 데이터 불러오기 (DB에서 학습용 이미지 불러오기)
    라즈베리파이 카메라모듈 8MP V2를 사용한 이미지 캡처 및 저장
    """
    def __init__(self):
        # 카메라 설정
        self.camera_resolution = (3280, 2464)  # 8MP V2 기본 해상도
        self.camera_framerate = 30
        self.image_format = 'JPEG'
        self.image_quality = 95
        
        # 저장 경로 설정
        self.base_path = "/home/pi/quadruped_images"
        self.training_path = f"{self.base_path}/training"
        self.testing_path = f"{self.base_path}/testing"
        self.raw_path = f"{self.base_path}/raw"
        
        # 데이터베이스 연결 정보
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'quadruped_robot',
            'user': 'pi',
            'password': 'raspberry'
        }
        
        # 카메라 초기화
        self._initialize_camera()
        
        # 데이터베이스 연결
        self._connect_database()
        
        # 디렉토리 생성
        self._create_directories()
        
        print("카메라 이미지 데이터 관리자 초기화 완료")
    
    def _initialize_camera(self):
        """라즈베리파이 카메라 초기화"""
        try:
            import picamera
            import picamera.array
            
            # 카메라 객체 생성
            self.camera = picamera.PiCamera()
            
            # 카메라 설정
            self.camera.resolution = self.camera_resolution
            self.camera.framerate = self.camera_framerate
            self.camera.rotation = 0
            
            # 카메라 안정화 시간
            time.sleep(2)
            
            print("라즈베리파이 카메라 초기화 성공")
            
        except ImportError:
            print("picamera 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"카메라 초기화 오류: {e}")
            self.simulation_mode = True
    
    def _connect_database(self):
        """데이터베이스 연결"""
        try:
            import mysql.connector
            
            self.db_connection = mysql.connector.connect(**self.db_config)
            self.db_cursor = self.db_connection.cursor()
            
            # 테이블 생성 (없는 경우)
            self._create_tables()
            
            print("데이터베이스 연결 성공")
            
        except ImportError:
            print("mysql-connector-python 모듈을 찾을 수 없습니다. 시뮬레이션 모드로 실행됩니다.")
            self.simulation_mode = True
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            self.simulation_mode = True
    
    def _create_tables(self):
        """필요한 테이블 생성"""
        try:
            # 이미지 메타데이터 테이블
            create_images_table = """
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                filepath VARCHAR(500) NOT NULL,
                resolution VARCHAR(20),
                file_size BIGINT,
                capture_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_type ENUM('training', 'testing', 'raw') DEFAULT 'raw',
                tags TEXT,
                metadata JSON
            )
            """
            
            # 이미지 분류 테이블
            create_classifications_table = """
            CREATE TABLE IF NOT EXISTS image_classifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_id INT,
                class_name VARCHAR(100),
                confidence FLOAT,
                classification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
            """
            
            self.db_cursor.execute(create_images_table)
            self.db_cursor.execute(create_classifications_table)
            self.db_connection.commit()
            
            print("데이터베이스 테이블 생성 완료")
            
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        import os
        
        directories = [self.base_path, self.training_path, self.testing_path, self.raw_path]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"디렉토리 생성: {directory}")
    
    def capture_image(self, image_type='raw', tags=None, metadata=None):
        """이미지 캡처 및 저장"""
        try:
            if hasattr(self, 'simulation_mode'):
                # 시뮬레이션 모드: 더미 이미지 생성
                return self._create_dummy_image(image_type, tags, metadata)
            
            # 타임스탬프 기반 파일명 생성
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"quadruped_{image_type}_{timestamp}.jpg"
            
            # 저장 경로 결정
            if image_type == 'training':
                filepath = os.path.join(self.training_path, filename)
            elif image_type == 'testing':
                filepath = os.path.join(self.testing_path, filename)
            else:
                filepath = os.path.join(self.raw_path, filename)
            
            # 이미지 캡처
            self.camera.capture(filepath, format=self.image_format, quality=self.image_quality)
            
            # 파일 정보 수집
            file_size = os.path.getsize(filepath)
            
            # 데이터베이스에 저장
            image_id = self._save_image_to_db(filename, filepath, file_size, image_type, tags, metadata)
            
            print(f"이미지 캡처 완료: {filename} (ID: {image_id})")
            
            return {
                'id': image_id,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"이미지 캡처 오류: {e}")
            return None
    
    def _create_dummy_image(self, image_type, tags, metadata):
        """시뮬레이션용 더미 이미지 생성"""
        import numpy as np
        from PIL import Image
        
        # 더미 이미지 생성 (320x240)
        dummy_image = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        # 타임스탬프 기반 파일명
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"dummy_{image_type}_{timestamp}.jpg"
        
        # 저장 경로
        if image_type == 'training':
            filepath = os.path.join(self.training_path, filename)
        elif image_type == 'testing':
            filepath = os.path.join(self.testing_path, filename)
        else:
            filepath = os.path.join(self.raw_path, filename)
        
        # 이미지 저장
        Image.fromarray(dummy_image).save(filepath, quality=self.image_quality)
        
        # 파일 정보
        file_size = os.path.getsize(filepath)
        
        # 데이터베이스에 저장
        image_id = self._save_image_to_db(filename, filepath, file_size, image_type, tags, metadata)
        
        return {
            'id': image_id,
            'filename': filename,
            'filepath': filepath,
            'file_size': file_size,
            'timestamp': timestamp
        }
    
    def _save_image_to_db(self, filename, filepath, file_size, image_type, tags, metadata):
        """이미지 정보를 데이터베이스에 저장"""
        try:
            if hasattr(self, 'simulation_mode'):
                return 1  # 시뮬레이션 모드에서는 더미 ID 반환
            
            # 이미지 정보 삽입
            insert_query = """
            INSERT INTO images (filename, filepath, resolution, file_size, image_type, tags, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            resolution_str = f"{self.camera_resolution[0]}x{self.camera_resolution[1]}"
            tags_str = ','.join(tags) if tags else None
            metadata_json = json.dumps(metadata) if metadata else None
            
            self.db_cursor.execute(insert_query, (
                filename, filepath, resolution_str, file_size, image_type, tags_str, metadata_json
            ))
            
            self.db_connection.commit()
            
            return self.db_cursor.lastrowid
            
        except Exception as e:
            print(f"데이터베이스 저장 오류: {e}")
            return None
    
    def fetch_image_list(self, image_type=None, limit=100, offset=0):
        """이미지 목록 불러오기"""
        try:
            if hasattr(self, 'simulation_mode'):
                return self._get_dummy_image_list(image_type, limit, offset)
            
            # 쿼리 구성
            query = "SELECT * FROM images"
            params = []
            
            if image_type:
                query += " WHERE image_type = %s"
                params.append(image_type)
            
            query += " ORDER BY capture_timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            self.db_cursor.execute(query, params)
            results = self.db_cursor.fetchall()
            
            # 컬럼명 가져오기
            columns = [desc[0] for desc in self.db_cursor.description]
            
            # 딕셔너리 형태로 변환
            image_list = []
            for row in results:
                image_dict = dict(zip(columns, row))
                image_list.append(image_dict)
            
            return image_list
            
        except Exception as e:
            print(f"이미지 목록 조회 오류: {e}")
            return []
    
    def _get_dummy_image_list(self, image_type, limit, offset):
        """시뮬레이션용 더미 이미지 목록"""
        dummy_images = []
        
        for i in range(offset, min(offset + limit, 50)):  # 최대 50개 더미 이미지
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time() - i * 3600))
            filename = f"dummy_{image_type or 'raw'}_{timestamp}.jpg"
            
            dummy_images.append({
                'id': i + 1,
                'filename': filename,
                'filepath': f"/dummy/path/{filename}",
                'resolution': '320x240',
                'file_size': 1024 * (i % 10 + 1),
                'capture_timestamp': timestamp,
                'image_type': image_type or 'raw',
                'tags': 'dummy,simulation',
                'metadata': '{"simulation": true}'
            })
        
        return dummy_images
    
    def get_image_by_id(self, image_id):
        """특정 이미지 데이터 반환"""
        try:
            if hasattr(self, 'simulation_mode'):
                return self._get_dummy_image_by_id(image_id)
            
            # 이미지 정보 조회
            query = "SELECT * FROM images WHERE id = %s"
            self.db_cursor.execute(query, (image_id,))
            result = self.db_cursor.fetchone()
            
            if result:
                # 컬럼명 가져오기
                columns = [desc[0] for desc in self.db_cursor.description]
                image_data = dict(zip(columns, result))
                
                # 이미지 파일 읽기
                if os.path.exists(image_data['filepath']):
                    with open(image_data['filepath'], 'rb') as f:
                        image_data['image_bytes'] = f.read()
                
                return image_data
            else:
                print(f"이미지 ID {image_id}를 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"이미지 조회 오류: {e}")
            return None
    
    def _get_dummy_image_by_id(self, image_id):
        """시뮬레이션용 더미 이미지"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"dummy_image_{image_id}_{timestamp}.jpg"
        
        return {
            'id': image_id,
            'filename': filename,
            'filepath': f"/dummy/path/{filename}",
            'resolution': '320x240',
            'file_size': 1024 * (image_id % 10 + 1),
            'capture_timestamp': timestamp,
            'image_type': 'raw',
            'tags': 'dummy,simulation',
            'metadata': '{"simulation": true}',
            'image_bytes': b'dummy_image_data'
        }
    
    def capture_training_sequence(self, num_images=10, interval=1.0):
        """학습용 이미지 시퀀스 캡처"""
        print(f"학습용 이미지 {num_images}개 캡처 시작 (간격: {interval}초)")
        
        captured_images = []
        
        for i in range(num_images):
            print(f"이미지 {i+1}/{num_images} 캡처 중...")
            
            # 이미지 캡처
            result = self.capture_image(
                image_type='training',
                tags=['training', 'sequence'],
                metadata={'sequence_number': i+1, 'total_images': num_images}
            )
            
            if result:
                captured_images.append(result)
            
            # 간격 대기
            if i < num_images - 1:
                time.sleep(interval)
        
        print(f"학습용 이미지 시퀀스 캡처 완료: {len(captured_images)}개")
        return captured_images
    
    def get_image_statistics(self):
        """이미지 통계 정보 반환"""
        try:
            if hasattr(self, 'simulation_mode'):
                return self._get_dummy_statistics()
            
            # 전체 이미지 수
            self.db_cursor.execute("SELECT COUNT(*) FROM images")
            total_images = self.db_cursor.fetchone()[0]
            
            # 타입별 이미지 수
            self.db_cursor.execute("SELECT image_type, COUNT(*) FROM images GROUP BY image_type")
            type_counts = dict(self.db_cursor.fetchall())
            
            # 최근 24시간 이미지 수
            self.db_cursor.execute("""
                SELECT COUNT(*) FROM images 
                WHERE capture_timestamp >= NOW() - INTERVAL 1 DAY
            """)
            recent_24h = self.db_cursor.fetchone()[0]
            
            return {
                'total_images': total_images,
                'type_counts': type_counts,
                'recent_24h': recent_24h,
                'storage_path': self.base_path
            }
            
        except Exception as e:
            print(f"통계 정보 조회 오류: {e}")
            return {}
    
    def _get_dummy_statistics(self):
        """시뮬레이션용 통계 정보"""
        return {
            'total_images': 50,
            'type_counts': {'raw': 30, 'training': 15, 'testing': 5},
            'recent_24h': 10,
            'storage_path': self.base_path
        }
    
    def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'camera'):
                self.camera.close()
            
            if hasattr(self, 'db_connection'):
                self.db_cursor.close()
                self.db_connection.close()
                
        except Exception as e:
            print(f"리소스 정리 오류: {e}")
        
        print("카메라 이미지 데이터 관리자 리소스 정리 완료") 
