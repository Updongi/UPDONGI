#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사족 보행 로봇 3D 시뮬레이션
Quadruped Robot 3D Simulation

사용된 하드웨어:
- 아두이노 라즈베리파이
- IOE-SR05 초음파 거리측정 센서 (2미터 거리 측정)
- 라즈베리파이 카메라모듈 8MP V2
- FSR 압력센서 0.5인치 원형 FSR402
- MPU6050 자이로 6축 가속 모듈
- 서브모터 (DC 모터 아님)
"""

import pygame
import numpy as np
import math
import sys
from pygame.locals import *
import time

class QuadrupedSimulation:
    def __init__(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("사족 보행 로봇 3D 시뮬레이션 - Quadruped Robot 3D Simulation")
        
        # 색상 정의
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        
        # 로봇 상태
        self.robot_x = width // 2
        self.robot_y = height // 2
        self.robot_angle = 0
        self.robot_speed = 0
        self.robot_steering = 0
        
        # 다리 상태 (4개 다리)
        self.legs = {
            'front_left': {'angle': 0, 'height': 0, 'contact': False},
            'front_right': {'angle': 0, 'height': 0, 'contact': False},
            'back_left': {'angle': 0, 'height': 0, 'contact': False},
            'back_right': {'angle': 0, 'height': 0, 'contact': False}
        }
        
        # 센서 데이터 시뮬레이션
        self.ultrasonic_distance = 100  # cm
        self.imu_data = {'roll': 0, 'pitch': 0, 'yaw': 0}
        self.pressure_sensors = {'front_left': 0, 'front_right': 0, 'back_left': 0, 'back_right': 0}
        
        # 시뮬레이션 설정
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # 제어 키 상태
        self.keys_pressed = set()
        
    def draw_3d_robot(self):
        """3D 로봇을 2D 화면에 투영하여 그리기"""
        # 바디 그리기
        body_width = 120
        body_height = 80
        body_rect = pygame.Rect(
            self.robot_x - body_width//2,
            self.robot_y - body_height//2,
            body_width,
            body_height
        )
        pygame.draw.rect(self.screen, self.BLUE, body_rect)
        pygame.draw.rect(self.screen, self.BLACK, body_rect, 3)
        
        # 방향 표시 (로봇의 앞쪽)
        direction_length = 40
        end_x = self.robot_x + direction_length * math.cos(math.radians(self.robot_angle))
        end_y = self.robot_y - direction_length * math.sin(math.radians(self.robot_angle))
        pygame.draw.line(self.screen, self.RED, (self.robot_x, self.robot_y), (end_x, end_y), 5)
        
        # 다리 그리기
        leg_length = 60
        leg_positions = {
            'front_left': (-body_width//2 - 20, -body_height//2 - 20),
            'front_right': (body_width//2 + 20, -body_height//2 - 20),
            'back_left': (-body_width//2 - 20, body_height//2 + 20),
            'back_right': (body_width//2 + 20, body_height//2 + 20)
        }
        
        for leg_name, (dx, dy) in leg_positions.items():
            leg_x = self.robot_x + dx
            leg_y = self.robot_y + dy
            
            # 다리 각도에 따른 끝점 계산
            leg_end_x = leg_x + leg_length * math.cos(math.radians(self.legs[leg_name]['angle']))
            leg_end_y = leg_y + leg_length * math.sin(math.radians(self.legs[leg_name]['angle']))
            
            # 다리 그리기
            leg_color = self.GREEN if self.legs[leg_name]['contact'] else self.GRAY
            pygame.draw.line(self.screen, leg_color, (leg_x, leg_y), (leg_end_x, leg_end_y), 8)
            
            # 다리 끝점 (발)
            foot_radius = 8
            pygame.draw.circle(self.screen, self.BLACK, (int(leg_end_x), int(leg_end_y)), foot_radius)
            
            # 압력 센서 표시
            pressure = self.pressure_sensors[leg_name]
            if pressure > 0:
                pressure_color = (min(255, pressure * 50), 0, 0)
                pygame.draw.circle(self.screen, pressure_color, (int(leg_end_x), int(leg_end_y)), foot_radius + 5, 3)
    
    def draw_sensor_data(self):
        """센서 데이터 표시"""
        # 초음파 센서 거리
        distance_text = self.font.render(f"초음파 거리: {self.ultrasonic_distance}cm", True, self.WHITE)
        self.screen.blit(distance_text, (10, 10))
        
        # IMU 데이터
        imu_text = self.font.render(f"IMU - Roll: {self.imu_data['roll']:.1f}° Pitch: {self.imu_data['pitch']:.1f}° Yaw: {self.imu_data['yaw']:.1f}°", True, self.WHITE)
        self.screen.blit(imu_text, (10, 50))
        
        # 압력 센서 데이터
        y_offset = 90
        for i, (leg_name, pressure) in enumerate(self.pressure_sensors.items()):
            pressure_text = self.small_font.render(f"{leg_name}: {pressure:.2f}", True, self.WHITE)
            self.screen.blit(pressure_text, (10, y_offset + i * 25))
        
        # 로봇 상태
        status_text = self.font.render(f"속도: {self.robot_speed:.1f} 방향: {self.robot_steering:.1f}°", True, self.YELLOW)
        self.screen.blit(status_text, (10, self.height - 60))
        
        # 제어 키 안내
        controls_text = self.small_font.render("제어: WASD(이동), QE(회전), Space(정지)", True, self.WHITE)
        self.screen.blit(controls_text, (10, self.height - 30))
    
    def update_robot_physics(self):
        """로봇 물리 시뮬레이션 업데이트"""
        # 속도에 따른 위치 업데이트
        self.robot_x += self.robot_speed * math.cos(math.radians(self.robot_angle))
        self.robot_y -= self.robot_speed * math.sin(math.radians(self.robot_angle))
        
        # 방향 조정
        self.robot_angle += self.robot_steering
        
        # 경계 체크
        if self.robot_x < 100:
            self.robot_x = 100
        elif self.robot_x > self.width - 100:
            self.robot_x = self.width - 100
            
        if self.robot_y < 100:
            self.robot_y = 100
        elif self.robot_y > self.height - 100:
            self.robot_y = self.height - 100
        
        # 다리 움직임 시뮬레이션
        for leg_name in self.legs:
            # 보행 패턴 시뮬레이션
            if self.robot_speed > 0:
                self.legs[leg_name]['angle'] += 2 * self.robot_speed
                if self.legs[leg_name]['angle'] > 360:
                    self.legs[leg_name]['angle'] -= 360
                
                # 다리 접촉 상태 시뮬레이션
                angle_rad = math.radians(self.legs[leg_name]['angle'])
                self.legs[leg_name]['contact'] = abs(math.sin(angle_rad)) < 0.3
                
                # 압력 센서 값 시뮬레이션
                if self.legs[leg_name]['contact']:
                    self.pressure_sensors[leg_name] = abs(math.sin(angle_rad)) * 2
                else:
                    self.pressure_sensors[leg_name] = 0
        
        # IMU 데이터 시뮬레이션
        self.imu_data['roll'] = math.sin(time.time() * 0.5) * 5
        self.imu_data['pitch'] = math.cos(time.time() * 0.3) * 3
        self.imu_data['yaw'] = self.robot_angle
        
        # 초음파 센서 거리 시뮬레이션
        self.ultrasonic_distance = max(10, 100 + math.sin(time.time() * 0.2) * 20)
    
    def handle_input(self):
        """키보드 입력 처리"""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            elif event.type == KEYDOWN:
                self.keys_pressed.add(event.key)
            elif event.type == KEYUP:
                self.keys_pressed.discard(event.key)
        
        # 이동 제어
        if K_w in self.keys_pressed:
            self.robot_speed = min(5.0, self.robot_speed + 0.2)
        elif K_s in self.keys_pressed:
            self.robot_speed = max(-3.0, self.robot_speed - 0.2)
        else:
            # 마찰력으로 인한 감속
            if self.robot_speed > 0:
                self.robot_speed = max(0, self.robot_speed - 0.1)
            elif self.robot_speed < 0:
                self.robot_speed = min(0, self.robot_speed + 0.1)
        
        # 방향 제어
        if K_a in self.keys_pressed:
            self.robot_steering = max(-3.0, self.robot_steering - 0.5)
        elif K_d in self.keys_pressed:
            self.robot_steering = min(3.0, self.robot_steering + 0.5)
        else:
            # 방향 자동 복원
            if self.robot_steering > 0:
                self.robot_steering = max(0, self.robot_steering - 0.1)
            elif self.robot_steering < 0:
                self.robot_steering = min(0, self.robot_steering + 0.1)
        
        # 회전 제어
        if K_q in self.keys_pressed:
            self.robot_angle -= 2
        if K_e in self.keys_pressed:
            self.robot_angle += 2
        
        # 정지
        if K_SPACE in self.keys_pressed:
            self.robot_speed = 0
            self.robot_steering = 0
        
        return True
    
    def run_simulation(self):
        """메인 시뮬레이션 루프"""
        running = True
        
        while running:
            # 입력 처리
            running = self.handle_input()
            
            # 물리 업데이트
            self.update_robot_physics()
            
            # 화면 그리기
            self.screen.fill(self.BLACK)
            
            # 그리드 그리기
            grid_size = 50
            for x in range(0, self.width, grid_size):
                pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, self.height))
            for y in range(0, self.height, grid_size):
                pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.width, y))
            
            # 로봇 그리기
            self.draw_3d_robot()
            
            # 센서 데이터 표시
            self.draw_sensor_data()
            
            # 화면 업데이트
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("사족 보행 로봇 3D 시뮬레이션을 시작합니다...")
    print("제어 방법:")
    print("W/S: 앞/뒤 이동")
    print("A/D: 좌/우 방향 조정")
    print("Q/E: 좌/우 회전")
    print("Space: 정지")
    print("ESC: 종료")
    
    simulation = QuadrupedSimulation()
    simulation.run_simulation()
