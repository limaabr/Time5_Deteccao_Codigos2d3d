"""
=======================================================================================
LEITOR DE CÓDIGOS DE BARRAS E QRCODE - Versão 6
=======================================================================================
Sistema de Detecção de Códigos 1D/2D com PDI
Desenvolvido para Ubuntu + VSCode
Python 3.10+

Time 5:
- Brenda Lima Cezar
- Fábio André da Frota Lima
- Luis Gustavo Corrêa
- Helmer Araujo Rodrigues
- Henrique da Rocha Andrade
=======================================================================================
"""

import sys
import cv2
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit,
    QCheckBox, QSlider, QGroupBox, QScrollArea, QListWidget,
    QSplitter, QFileDialog, QFrame, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QMutex
from PyQt5.QtGui import QImage, QPixmap, QFont, QIntValidator

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    print("⚠️ pyzbar não instalado. Use: pip install pyzbar")

try:
    from pylibdmtx import pylibdmtx
    PYLIBDMTX_AVAILABLE = True
except ImportError:
    PYLIBDMTX_AVAILABLE = False
    print("⚠️ pylibdmtx não instalado. Use: pip install pylibdmtx")


# ==================== CONFIGURAÇÕES OTIMIZADAS PARA PCYES FHD-03 ====================
DEFAULT_CONFIG = {
    "auto_exposure": True,      # Ativa auto exposição por padrão
    "exposure": -6,
    "gain": 0,
    "brightness": 128,
    "contrast": 40,             
    "gamma": 100,
    "auto_focus": True,         # Autofoco ativo por padrão
    "focus": 0,
    "boost": False,
    "alpha": 1.0,
    "beta": 0
}


# ==================== THREAD DE CAPTURA E PROCESSAMENTO ====================
class CameraThread(QThread):
    """Thread responsável pela captura de vídeo e detecção de códigos"""
    
    frame_ready = pyqtSignal(np.ndarray)
    code_detected = pyqtSignal(dict)
    inspection_complete = pyqtSignal(bool, int)
    
    def __init__(self):
        super().__init__()
        self.camera = None
        self.running = False
        self.camera_index = 0
        self.inspecting = False
        self.expected_codes = 1
        self.timeout = 10
        self.detected_codes = set()
        self.frame_skip = 1
        self.frame_count = 0
        self.thumbnail_mode = "Enhanced (CLAHE)"  # Default
        
        # Controle de parâmetros (thread-safe)
        self.pdi_params = DEFAULT_CONFIG.copy()
        self.params_mutex = QMutex()
        self.params_changed = False
        
        # Buffer de detecção para evitar duplicatas
        self.recent_detections = deque(maxlen=30)
        
    def set_camera(self, index: int) -> bool:
        """Configura e abre a câmera com otimizações para Pcyes FHD-03"""
        self.camera_index = index
        if self.camera is not None:
            self.camera.release()
        
        self.camera = cv2.VideoCapture(index, cv2.CAP_V4L2)  # ✅ Usa V4L2 no Linux
        if not self.camera.isOpened():
            # Tenta com backend padrão se V4L2 falhar
            self.camera = cv2.VideoCapture(index)
            if not self.camera.isOpened():
                return False
        
        # ✅ OTIMIZADO: Configuração específica para FHD-03
        # Usa 720p para melhor performance (a detecção não precisa de 1080p)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # ✅ IMPORTANTE: Desativa autofoco inicial para evitar delay
        # Será reativado pelos parâmetros do usuário
        self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        # ✅ Configura codec MJPEG para melhor performance
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # Aguarda 500ms para câmera estabilizar
        import time
        time.sleep(0.5)
        
        # Aplica configurações iniciais
        self.apply_pdi_params()
        
        print(f"✅ Câmera configurada: {int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ {int(self.camera.get(cv2.CAP_PROP_FPS))}fps")
        
        return True
    
    def apply_pdi_params(self):
        """Aplica parâmetros de PDI na câmera de forma assíncrona e otimizada"""
        if self.camera is None or not self.camera.isOpened():
            return
        
        self.params_mutex.lock()
        params = self.pdi_params.copy()
        self.params_mutex.unlock()
        
        try:
            # ✅ AUTOFOCO: Configuração otimizada para FHD-03
            if params.get("auto_focus", True):
                # Ativa autofoco contínuo (modo 1)
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                print("🔍 Autofoco ATIVADO (modo contínuo)")
            else:
                # Desativa autofoco para controle manual
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                focus_value = params.get("focus", 0)
                self.camera.set(cv2.CAP_PROP_FOCUS, focus_value)
                print(f"🔧 Foco MANUAL: {focus_value}")
            
            # ✅ AUTO EXPOSIÇÃO: Otimizada para códigos
            if params.get("auto_exposure", True):
                # Modo 3 = auto exposição com prioridade para velocidade
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
                print("💡 Auto exposição ATIVADA")
            else:
                # Modo 1 = exposição manual
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                exposure_value = params.get("exposure", -6)
                self.camera.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
                print(f"⚙️ Exposição MANUAL: {exposure_value}")
            
            # ✅ OUTROS PARÂMETROS: Aplicados de forma assíncrona
            self.camera.set(cv2.CAP_PROP_GAIN, params.get("gain", 0))
            self.camera.set(cv2.CAP_PROP_BRIGHTNESS, params.get("brightness", 128))
            self.camera.set(cv2.CAP_PROP_CONTRAST, params.get("contrast", 40))
            self.camera.set(cv2.CAP_PROP_GAMMA, params.get("gamma", 100))
            
            # ✅ IMPORTANTE: Define Sharpness (nitidez) para melhor leitura
            # Valor alto (200-255) melhora detecção de códigos
            self.camera.set(cv2.CAP_PROP_SHARPNESS, 200)
            
        except Exception as e:
            print(f"⚠️ Aviso ao aplicar parâmetros: {e}")
    
    def update_pdi_param(self, param: str, value):
        """Atualiza um parâmetro específico de PDI (thread-safe)"""
        self.params_mutex.lock()
        self.pdi_params[param] = value
        self.params_changed = True
        self.params_mutex.unlock()
    
    def start_inspection(self, expected: int, timeout: int):
        """Inicia um ciclo de inspeção"""
        self.expected_codes = expected
        self.timeout = timeout
        self.detected_codes.clear()
        self.recent_detections.clear()
        self.inspecting = True
        self.inspection_start_time = datetime.now()
        print(f"▶️ Inspeção iniciada: {expected} código(s), timeout: {timeout}s")
    
    def stop_inspection(self):
        """Para o ciclo de inspeção"""
        self.inspecting = False
        print("⏹️ Inspeção parada manualmente")

    def is_valid_code(self, code_type: str, code_data: str, bbox: tuple) -> bool:
        """Valida se o código detectado é legítimo (não é ruído)"""
        x, y, w, h = bbox
        
        # ✅ REGRA 1: Tamanho mínimo REDUZIDO (permite códigos distantes)
        if w < 15 or h < 8:  # Bem menor que antes (era 30x15)
            return False
        
        # ✅ REGRA 2: Conteúdo mínimo (códigos reais têm pelo menos 3 caracteres)
        if len(code_data) < 3:
            return False
        
        # ✅ REGRA 3: Apenas caracteres imprimíveis (evita lixo binário)
        if not all(32 <= ord(c) <= 126 for c in code_data):
            return False
        
        # ✅ REGRA 4: Validação específica DataBar (causa do WARNING)
        if code_type in ['DATABAR', 'DATABAR_EXP', 'RSS14', 'RSS_EXP']:
            # DataBar DEVE ser numérico e ter comprimento razoável
            if not code_data.isdigit() or len(code_data) < 10:
                return False
        
        return True
    
    def detect_codes(self, frame: np.ndarray) -> List[Dict]:
        """Detecta códigos 1D e 2D no frame com pré-processamento otimizado
        
        PIPELINE OTIMIZADO:
        1. Detecção inicial (localiza códigos)
        2. Recorte da região detectada
        3. Retificação de perspectiva (corrige inclinação)
        4. PDI completo na região retificada
        5. Re-detecção com maior precisão
        """
        codes = []
        
        # ============ ETAPA 1: DETECÇÃO INICIAL (LOCALIZAÇÃO) ============
        # Usa imagem em escala de cinza para localizar códigos rapidamente
        gray_initial = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        detected_regions = []  # Armazena regiões detectadas para processamento
        
        # Detecção inicial rápida com pyzbar
        if PYZBAR_AVAILABLE:
            try:
                import os
                stderr_backup = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                
                try:
                    decoded_objects = pyzbar.decode(gray_initial)
                finally:
                    sys.stderr.close()
                    sys.stderr = stderr_backup
                
                for obj in decoded_objects:
                    try:
                        data_key = obj.data.decode('utf-8', errors='ignore')
                        x, y, w, h = obj.rect
                        
                        # Valida se não é ruído
                        if not self.is_valid_code(obj.type, data_key, (x, y, w, h)):
                            continue
                        
                        # Armazena região para processamento refinado
                        detected_regions.append({
                            'type': obj.type,
                            'data': data_key,
                            'bbox': (x, y, w, h),
                            'polygon': obj.polygon,
                            'method': 'initial'
                        })
                    except Exception:
                        continue
            except Exception:
                pass
        
        # ============ ETAPA 2: PROCESSAMENTO REFINADO DAS REGIÕES ============
        processed_codes = set()  # Evita duplicatas
        
        for region in detected_regions:
            x, y, w, h = region['bbox']
            polygon = region['polygon']
            
            # ✅ MARGEM DE SEGURANÇA: Expande região em 20% para não cortar bordas
            margin_x = int(w * 0.2)
            margin_y = int(h * 0.2)
            
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(frame.shape[1], x + w + margin_x)
            y2 = min(frame.shape[0], y + h + margin_y)
            
            # ✅ RECORTE da região detectada
            roi = frame[y1:y2, x1:x2].copy()
            
            if roi.size == 0:
                continue
            
            # ============ ETAPA 3: RETIFICAÇÃO DE PERSPECTIVA ============
            try:
                # Ajusta coordenadas do polígono para o ROI
                polygon_adjusted = []
                for point in polygon:
                    px = point.x - x1
                    py = point.y - y1
                    polygon_adjusted.append([px, py])
                
                polygon_adjusted = np.array(polygon_adjusted, dtype=np.float32)
                
                # Calcula largura e altura do código retificado
                # Usa a distância entre pontos para preservar proporções
                width = int(max(
                    np.linalg.norm(polygon_adjusted[0] - polygon_adjusted[1]),
                    np.linalg.norm(polygon_adjusted[2] - polygon_adjusted[3])
                ))
                height = int(max(
                    np.linalg.norm(polygon_adjusted[1] - polygon_adjusted[2]),
                    np.linalg.norm(polygon_adjusted[3] - polygon_adjusted[0])
                ))
                
                # ✅ TAMANHO MÍNIMO: Garante resolução suficiente para leitura
                width = max(width, 100)
                height = max(height, 50)
                
                # Pontos destino (retângulo perfeito)
                dst_points = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)
                
                # ✅ MATRIZ DE TRANSFORMAÇÃO de perspectiva
                matrix = cv2.getPerspectiveTransform(polygon_adjusted, dst_points)
                
                # ✅ RETIFICAÇÃO: Corrige distorção angular
                rectified = cv2.warpPerspective(roi, matrix, (width, height))
                
                # Armazena imagem retificada original (para miniaturas)
                rectified_original = rectified.copy()
                
            except Exception as e:
                # Se retificação falhar, usa ROI original
                print(f"⚠️ Retificação falhou: {e}")
                rectified = roi
                rectified_original = roi.copy()
            
            # ============ ETAPA 4: PIPELINE DE PDI NA REGIÃO RETIFICADA ============
            
            # 4.1: CLAHE (equalização adaptativa)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab = cv2.cvtColor(rectified, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # 4.2: Escala de cinza
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
            
            # 4.3: Binarização adaptativa (CRÍTICO para códigos 1D)
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2
            )
            
            # 4.4: Remoção de ruído
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # 4.5: Sharpening (aguça bordas para melhor leitura)
            # Usa filtro Unsharp Mask
            gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
            sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
            
            # ✅ CACHE das versões processadas
            self.enhanced_frame_cache = enhanced
            self.gray_frame_cache = sharpened
            self.binary_frame_cache = denoised
            
            # ============ ETAPA 5: RE-DETECÇÃO COM ALTA PRECISÃO ============
            
            # Tenta detectar nas versões processadas (ordem de prioridade)
            frames_to_try = [
                ('binary', denoised),       # Melhor para códigos 1D
                ('sharpened', sharpened),   # Melhor para detalhes finos
                ('enhanced', enhanced),     # Melhor para códigos 2D
            ]
            
            best_result = None
            best_confidence = 0
            
            for frame_type, processed in frames_to_try:
                if PYZBAR_AVAILABLE:
                    try:
                        import os
                        stderr_backup = sys.stderr
                        sys.stderr = open(os.devnull, 'w')
                        
                        try:
                            refined_objects = pyzbar.decode(processed)
                        finally:
                            sys.stderr.close()
                            sys.stderr = stderr_backup
                        
                        for obj in refined_objects:
                            try:
                                refined_data = obj.data.decode('utf-8', errors='ignore')
                                
                                # Valida resultado
                                if len(refined_data) < 3:
                                    continue
                                
                                # ✅ CRITÉRIO DE CONFIANÇA: Prefere detecções com maior área
                                confidence = obj.rect.width * obj.rect.height
                                
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_result = {
                                        'type': obj.type,
                                        'data': refined_data,
                                        'bbox': region['bbox'],
                                        'points': region['polygon'],
                                        'detected_on': f'refined_{frame_type}',
                                        # ✅ ARMAZENA TODAS AS VERSÕES PROCESSADAS
                                        'rectified_original': rectified_original,  # Original retificada
                                        'rectified_enhanced': enhanced,            # Com CLAHE
                                        'rectified_gray': sharpened,               # Escala de cinza aguçada
                                        'rectified_binary': denoised               # Binarizada
                                    }
                            except Exception:
                                continue
                    except Exception:
                        pass
            
            # Se encontrou resultado refinado, adiciona
            if best_result:
                code_key = f"{best_result['type']}:{best_result['data']}"
                if code_key not in processed_codes:
                    processed_codes.add(code_key)
                    codes.append(best_result)
        
        # ============ FALLBACK: Se não detectou nada, tenta no frame completo ============
        if len(codes) == 0:
            # Pipeline PDI no frame completo (como backup)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced_frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)
            
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2
            )
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # Cache para miniaturas
            self.enhanced_frame_cache = enhanced_frame
            self.gray_frame_cache = gray
            self.binary_frame_cache = denoised
            
            # Tenta detectar
            frames_to_try = [
                ('binary', denoised),
                ('enhanced', enhanced_frame),
                ('gray', gray)
            ]
            
            detected_data = set()
            
            for frame_type, processed_frame in frames_to_try:
                if PYZBAR_AVAILABLE:
                    try:
                        import os
                        stderr_backup = sys.stderr
                        sys.stderr = open(os.devnull, 'w')
                        
                        try:
                            decoded_objects = pyzbar.decode(processed_frame)
                        finally:
                            sys.stderr.close()
                            sys.stderr = stderr_backup
                        
                        for obj in decoded_objects:
                            try:
                                data_key = obj.data.decode('utf-8', errors='ignore')
                                x, y, w, h = obj.rect
                                
                                if not self.is_valid_code(obj.type, data_key, (x, y, w, h)):
                                    continue
                                
                                if data_key not in detected_data:
                                    detected_data.add(data_key)
                                    # Recorta região do código
                                    code_roi = frame[y:y+h, x:x+w].copy()

                                    codes.append({
                                        'type': obj.type,
                                        'data': data_key,
                                        'bbox': (x, y, w, h),
                                        'points': obj.polygon,
                                        'detected_on': f'fullframe_{frame_type}',
                                        # ✅ Adiciona versões processadas da região recortada
                                        'rectified_original': code_roi,
                                        'rectified_enhanced': enhanced_frame[y:y+h, x:x+w].copy(),
                                        'rectified_gray': gray[y:y+h, x:x+w].copy(),
                                        'rectified_binary': denoised[y:y+h, x:x+w].copy()
                                    })
                            except Exception:
                                continue
                    except Exception:
                        pass
        
        return codes

    def apply_software_boost(self, frame: np.ndarray) -> np.ndarray:
        """Aplica boost de software (ganho digital)"""
        self.params_mutex.lock()
        alpha = self.pdi_params.get("alpha", 1.0)
        beta = self.pdi_params.get("beta", 0)
        self.params_mutex.unlock()
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    
    def is_duplicate_detection(self, code_data: str) -> bool:
        """Verifica se é uma detecção duplicada recente"""
        return code_data in self.recent_detections
    
    def run(self):
        """Loop principal da thread otimizado"""
        self.running = True
        params_update_counter = 0
        
        # ✅ Aguarda 1 segundo para autofoco estabilizar
        print("⏳ Aguardando autofoco estabilizar...")
        self.msleep(1000)
        print("✅ Pronto para detecção!")
        
        while self.running:
            if self.camera is None or not self.camera.isOpened():
                self.msleep(100)
                continue
            
            # ✅ Aplica parâmetros a cada 15 frames (mais conservador)
            params_update_counter += 1
            if self.params_changed and params_update_counter >= 15:
                self.apply_pdi_params()
                self.params_changed = False
                params_update_counter = 0
            
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            # Frame skip para modo rápido
            self.frame_count += 1
            if self.frame_count % self.frame_skip != 0:
                continue
            
            # Aplica boost de software se habilitado
            self.params_mutex.lock()
            boost_enabled = self.pdi_params.get("boost", False)
            self.params_mutex.unlock()
            
            if boost_enabled:
                frame = self.apply_software_boost(frame)
            
            # Detecta códigos
            codes = self.detect_codes(frame)

            # ✅ Escolhe a imagem baseado no modo selecionado
            if self.thumbnail_mode == "Binarizada" and hasattr(self, 'binary_frame_cache'):
                processed_frame = self.binary_frame_cache
            elif self.thumbnail_mode == "Escala de Cinza" and hasattr(self, 'gray_frame_cache'):
                processed_frame = self.gray_frame_cache
            elif hasattr(self, 'enhanced_frame_cache'):
                processed_frame = self.enhanced_frame_cache
            else:
                processed_frame = frame

            # Se boost está ativado, aplica (exceto em binarizada que já é P&B)
            if boost_enabled and self.thumbnail_mode != "Binarizada":
                processed_frame = self.apply_software_boost(processed_frame)
                        
            # Desenha retângulos e legendas
            display_frame = frame.copy()
            for code in codes:
                x, y, w, h = code['bbox']
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                
                label = f"{code['type']}: {code['data']}"
                cv2.putText(display_frame, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # ✅ PRIORIZA imagem retificada ESPECÍFICA do código
                if 'rectified_binary' in code:
                    # Tem versões retificadas disponíveis
                    if self.thumbnail_mode == "Binarizada":
                        code_image = code.get('rectified_binary', code.get('rectified_original')).copy()
                    elif self.thumbnail_mode == "Escala de Cinza":
                        code_image = code.get('rectified_gray', code.get('rectified_original')).copy()
                    else:  # Enhanced (CLAHE)
                        code_image = code.get('rectified_enhanced', code.get('rectified_original')).copy()
                    
                    # Aplica boost se ativo (exceto em binarizada)
                    if boost_enabled and self.thumbnail_mode != "Binarizada":
                        code_image = self.apply_software_boost(code_image)
                        
                elif 'rectified_image' in code:
                    # Fallback: usa rectified_image antiga (compatibilidade)
                    code_image = code['rectified_image'].copy()
                    
                    if boost_enabled:
                        code_image = self.apply_software_boost(code_image)
                    
                    # Aplica boost se ativo (exceto em binarizada)
                    if boost_enabled and self.thumbnail_mode != "Binarizada":
                        code_image = self.apply_software_boost(code_image)
                else:
                    # Fallback: recorta do frame processado (método antigo)
                    x, y, w, h = code['bbox']
                    if self.thumbnail_mode == "Binarizada" and hasattr(self, 'binary_frame_cache'):
                        code_image = self.binary_frame_cache[y:y+h, x:x+w].copy()
                    elif self.thumbnail_mode == "Escala de Cinza" and hasattr(self, 'gray_frame_cache'):
                        code_image = self.gray_frame_cache[y:y+h, x:x+w].copy()
                    elif hasattr(self, 'enhanced_frame_cache'):
                        code_image = self.enhanced_frame_cache[y:y+h, x:x+w].copy()
                    else:
                        code_image = processed_frame[y:y+h, x:x+w].copy()
                    
                    # Aplica boost se ativo
                    if boost_enabled and self.thumbnail_mode != "Binarizada":
                        code_image = self.apply_software_boost(code_image)

                # Emite sinal de código detectado (evita duplicatas)
                code_key = f"{code['type']}:{code['data']}"
                if not self.is_duplicate_detection(code_key):
                    self.recent_detections.append(code_key)
                    
                    self.code_detected.emit({
                        'type': code['type'],
                        'data': code['data'],
                        'image': code_image,  # ✅ Agora usa imagem retificada + PDI
                        'bbox': code['bbox'],
                        'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    })
                    
                    # Adiciona ao set de códigos detectados (inspeção)
                    if self.inspecting:
                        self.detected_codes.add(code['data'])
            
            # Lógica de inspeção
            if self.inspecting:
                elapsed = (datetime.now() - self.inspection_start_time).total_seconds()
                detected_count = len(self.detected_codes)
                
                # Adiciona informações na tela
                cv2.putText(display_frame, f"Detectados: {detected_count}/{self.expected_codes}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (106, 90, 205), 2)
                cv2.putText(display_frame, f"Tempo: {elapsed:.1f}s / {self.timeout}s",
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (106, 90, 205), 2)
                
                # Aguarda timeout completo
                if elapsed >= self.timeout:
                    success = (detected_count == self.expected_codes)
                    self.inspection_complete.emit(success, detected_count)
                    self.inspecting = False
            
            # Emite frame processado
            self.frame_ready.emit(display_frame)
            
            self.msleep(16)  # ~60 FPS máximo (mais suave)
    
    def stop(self):
        """Para a thread"""
        self.running = False
        if self.camera is not None:
            self.camera.release()
        self.wait()


# ==================== INTERFACE PRINCIPAL ====================
class MainWindow(QMainWindow):
    """Janela principal do sistema"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Detecção de Códigos 1D/2D - Pcyes FHD-03")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowFlags(Qt.Window)

        # Thread de câmera
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_frame)
        self.camera_thread.code_detected.connect(self.on_code_detected)
        self.camera_thread.inspection_complete.connect(self.on_inspection_complete)
        
        # Histórico de códigos detectados
        self.detected_history = []
        self.current_thumbnails = []
        
        # Setup UI
        self.setup_ui()
        self.list_cameras()

    def update_thumbnail_mode(self, mode: str):
        """Atualiza o modo de miniatura na thread"""
        self.camera_thread.thumbnail_mode = mode
        
    def setup_ui(self):
        """Configura a interface gráfica"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)

        # Cria menu bar
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu("📁 Arquivo")
        exit_action = file_menu.addAction("❌ Sair")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Menu Visualizar
        view_menu = menubar.addMenu("👁️ Visualizar")
        fullscreen_action = view_menu.addAction("⛶ Tela Cheia")
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.fullscreen_action = fullscreen_action
        
        minimize_action = view_menu.addAction("🗕 Minimizar")
        minimize_action.setShortcut("Ctrl+M")
        minimize_action.triggered.connect(self.showMinimized)
        
        # Menu Ajuda
        help_menu = menubar.addMenu("❓ Ajuda")
        about_action = help_menu.addAction("ℹ️ Sobre")
        about_action.triggered.connect(self.show_about)
        shortcuts_action = help_menu.addAction("⌨️ Atalhos")
        shortcuts_action.triggered.connect(self.show_shortcuts)
           
        
        # ===== PAINEL ESQUERDO: Controles =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)
        
        # Grupo: Câmera
        camera_group = QGroupBox("🎥 Controle de Câmera")
        camera_layout = QVBoxLayout()
        
        self.camera_combo = QComboBox()
        camera_layout.addWidget(QLabel("Selecionar Câmera:"))
        camera_layout.addWidget(self.camera_combo)
        
        btn_layout = QHBoxLayout()
        self.btn_reload = QPushButton("🔄 Recarregar")
        self.btn_open = QPushButton("▶️ Abrir")
        self.btn_close = QPushButton("⏹️ Fechar")
        btn_layout.addWidget(self.btn_reload)
        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_close)
        camera_layout.addLayout(btn_layout)
        
        self.btn_reload.clicked.connect(self.list_cameras)
        self.btn_open.clicked.connect(self.open_camera)
        self.btn_close.clicked.connect(self.close_camera)
        self.btn_close.setEnabled(False)
        
        camera_group.setLayout(camera_layout)
        left_layout.addWidget(camera_group)
        
        # Grupo: Inspeção
        inspection_group = QGroupBox("🔍 Configuração de Inspeção")
        inspection_layout = QGridLayout()
        
        inspection_layout.addWidget(QLabel("Códigos esperados:"), 0, 0)
        self.txt_expected = QLineEdit()
        self.txt_expected.setText("1")
        self.txt_expected.setPlaceholderText("Digite a quantidade (1-8)")
        self.txt_expected.setMaxLength(1)
        inspection_layout.addWidget(self.txt_expected, 0, 1)
        
        inspection_layout.addWidget(QLabel("Tempo limite (s):"), 1, 0)
        self.txt_timeout = QLineEdit()
        self.txt_timeout.setText("10")
        self.txt_timeout.setPlaceholderText("Digite em segundos (1-300)")
        self.txt_timeout.setMaxLength(3)
        inspection_layout.addWidget(self.txt_timeout, 1, 1)
        
        self.check_fast_mode = QCheckBox("Modo rápido (processa 1 a cada 3 frames)")
        inspection_layout.addWidget(self.check_fast_mode, 2, 0, 1, 2)
        self.check_fast_mode.toggled.connect(self.toggle_fast_mode)

        inspection_layout.addWidget(QLabel("Tipo de miniatura:"), 3, 0)
        self.combo_thumbnail_mode = QComboBox()
        self.combo_thumbnail_mode.addItems(["Binarizada", "Enhanced (CLAHE)", "Escala de Cinza"])
        self.combo_thumbnail_mode.setCurrentIndex(1)  # Default: Enhanced
        self.combo_thumbnail_mode.currentTextChanged.connect(self.update_thumbnail_mode)
        inspection_layout.addWidget(self.combo_thumbnail_mode, 3, 1)
        
        self.btn_start_inspection = QPushButton("▶️ Iniciar Inspeção")
        self.btn_start_inspection.clicked.connect(self.start_inspection)
        self.btn_start_inspection.setStyleSheet("font-weight: bold; padding: 10px; background-color: #4CAF50; color: white;")
        self.btn_start_inspection.setEnabled(False)
        inspection_layout.addWidget(self.btn_start_inspection, 4, 0, 1, 2)
        
        self.btn_stop_inspection = QPushButton("⏹️ Finalizar Inspeção")
        self.btn_stop_inspection.clicked.connect(self.stop_inspection)
        self.btn_stop_inspection.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f44336; color: white;")
        self.btn_stop_inspection.setEnabled(False)
        inspection_layout.addWidget(self.btn_stop_inspection, 5, 0, 1, 2)
        
        inspection_group.setLayout(inspection_layout)
        left_layout.addWidget(inspection_group)
        
        # Grupo: PDI (Processamento Digital de Imagens)
        self.pdi_group = QGroupBox("⚙️ Parâmetros de PDI")
        self.pdi_group.setCheckable(True)
        self.pdi_group.setChecked(False)
        pdi_layout = QVBoxLayout()
        
        # Scroll area para PDI
        pdi_scroll = QScrollArea()
        pdi_scroll.setWidgetResizable(True)
        pdi_widget = QWidget()
        pdi_form = QVBoxLayout(pdi_widget)
        
        # Auto Exposição
        self.check_auto_exp = QCheckBox("Auto Exposição (recomendado para FHD-03)")
        self.check_auto_exp.setChecked(DEFAULT_CONFIG["auto_exposure"])
        self.check_auto_exp.toggled.connect(lambda v: self.update_pdi("auto_exposure", v))
        pdi_form.addWidget(self.check_auto_exp)
        
        # Exposição
        self.slider_exposure = self.create_slider("Exposição", -13, -1, DEFAULT_CONFIG["exposure"], "exposure")
        pdi_form.addLayout(self.slider_exposure)
        
        # Ganho
        self.slider_gain = self.create_slider("Ganho", 0, 100, DEFAULT_CONFIG["gain"], "gain")
        pdi_form.addLayout(self.slider_gain)
        
        # Brilho
        self.slider_brightness = self.create_slider("Brilho", 0, 255, DEFAULT_CONFIG["brightness"], "brightness")
        pdi_form.addLayout(self.slider_brightness)
        
        # Contraste
        self.slider_contrast = self.create_slider("Contraste", 0, 100, DEFAULT_CONFIG["contrast"], "contrast")
        pdi_form.addLayout(self.slider_contrast)
        
        # Gamma
        self.slider_gamma = self.create_slider("Gamma", 0, 200, DEFAULT_CONFIG["gamma"], "gamma")
        pdi_form.addLayout(self.slider_gamma)
        
        # Auto Foco
        self.check_auto_focus = QCheckBox("Auto Foco (recomendado para FHD-03)")
        self.check_auto_focus.setChecked(DEFAULT_CONFIG["auto_focus"])
        self.check_auto_focus.toggled.connect(lambda v: self.update_pdi("auto_focus", v))
        pdi_form.addWidget(self.check_auto_focus)
        
        # Foco
        self.slider_focus = self.create_slider("Foco Manual", 0, 255, DEFAULT_CONFIG["focus"], "focus")
        pdi_form.addLayout(self.slider_focus)
        
        pdi_form.addWidget(QLabel("─" * 30))
        
        # Boost Software
        self.check_boost = QCheckBox("Boost (software)")
        self.check_boost.setChecked(DEFAULT_CONFIG["boost"])
        self.check_boost.toggled.connect(lambda v: self.update_pdi("boost", v))
        pdi_form.addWidget(self.check_boost)
        
        # Alpha
        self.slider_alpha = self.create_slider_float("Alpha", 0.1, 3.0, DEFAULT_CONFIG["alpha"], "alpha")
        pdi_form.addLayout(self.slider_alpha)
        
        # Beta
        self.slider_beta = self.create_slider("Beta", -100, 100, DEFAULT_CONFIG["beta"], "beta")
        pdi_form.addLayout(self.slider_beta)
        
        pdi_scroll.setWidget(pdi_widget)
        pdi_layout.addWidget(pdi_scroll)
        
        # Botões de salvar/carregar config
        config_btn_layout = QHBoxLayout()
        self.btn_save_config = QPushButton("💾 Salvar Config")
        self.btn_load_config = QPushButton("📂 Carregar Config")
        self.btn_save_config.clicked.connect(self.save_config)
        self.btn_load_config.clicked.connect(self.load_config)
        config_btn_layout.addWidget(self.btn_save_config)
        config_btn_layout.addWidget(self.btn_load_config)
        pdi_layout.addLayout(config_btn_layout)
        
        self.pdi_group.setLayout(pdi_layout)
        left_layout.addWidget(self.pdi_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # ===== PAINEL CENTRAL: Vídeo e Status =====
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Vídeo com tamanho fixo
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #555;")
        self.video_label.setScaledContents(False)
        center_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        
        # Status de inspeção
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        status_layout = QHBoxLayout(status_frame)
        
        self.lbl_status = QLabel("AGUARDANDO")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFont(QFont("Arial", 24, QFont.Bold))
        self.lbl_status.setStyleSheet("background-color: gray; color: white; padding: 20px; border-radius: 10px;")
        status_layout.addWidget(self.lbl_status)
                
        center_layout.addWidget(status_frame)
        center_layout.addStretch()
        main_layout.addWidget(center_panel, stretch=2)
        
        # ===== PAINEL DIREITO: Histórico e Miniaturas =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMinimumWidth(310)  # ✅ Reduzido de 350 para 310
        right_panel.setMaximumWidth(310)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        # ✅ TÍTULO COMPACTO
        history_label = QLabel("📋 Histórico")
        history_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        right_layout.addWidget(history_label)

        # ✅ HISTÓRICO MAIS COMPACTO
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(120)  # Reduzido de 200 para 120
        self.history_list.setStyleSheet("font-size: 9px;")
        right_layout.addWidget(self.history_list)

        # ✅ TÍTULO DAS MINIATURAS
        thumbnails_label = QLabel("🖼️ Miniaturas (máx: 8)")
        thumbnails_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        right_layout.addWidget(thumbnails_label)

        # ✅ SCROLL AREA para as miniaturas
        thumbnails_scroll = QScrollArea()
        thumbnails_scroll.setWidgetResizable(True)
        thumbnails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        thumbnails_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        thumbnails_scroll.setMinimumHeight(600)  # Altura fixa para caber 8 códigos

        # Container de miniaturas com grid layout
        self.thumbnails_container = QWidget()
        self.thumbnails_layout = QGridLayout(self.thumbnails_container)
        self.thumbnails_layout.setSpacing(5)  # Espaçamento reduzido
        self.thumbnails_layout.setContentsMargins(5, 5, 5, 5)
        self.thumbnails_layout.setAlignment(Qt.AlignTop)  # ✅ Alinha no topo

        thumbnails_scroll.setWidget(self.thumbnails_container)
        right_layout.addWidget(thumbnails_scroll)

        main_layout.addWidget(right_panel)


    
    def create_slider(self, label: str, min_val: int, max_val: int, default: int, param: str) -> QVBoxLayout:
        """Cria um slider com label e valor"""
        layout = QVBoxLayout()
        
        header = QHBoxLayout()
        lbl = QLabel(label)
        val_lbl = QLabel(str(default))
        val_lbl.setMinimumWidth(40)
        val_lbl.setAlignment(Qt.AlignRight)
        header.addWidget(lbl)
        header.addWidget(val_lbl)
        layout.addLayout(header)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
        slider.valueChanged.connect(lambda v: self.update_pdi(param, v))
        layout.addWidget(slider)
        
        return layout
    
    def create_slider_float(self, label: str, min_val: float, max_val: float, default: float, param: str) -> QVBoxLayout:
        """Cria um slider para valores float"""
        layout = QVBoxLayout()
        
        header = QHBoxLayout()
        lbl = QLabel(label)
        val_lbl = QLabel(f"{default:.2f}")
        val_lbl.setMinimumWidth(40)
        val_lbl.setAlignment(Qt.AlignRight)
        header.addWidget(lbl)
        header.addWidget(val_lbl)
        layout.addLayout(header)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * 100), int(max_val * 100))
        slider.setValue(int(default * 100))
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v/100:.2f}"))
        slider.valueChanged.connect(lambda v: self.update_pdi(param, v / 100))
        layout.addWidget(slider)
        
        return layout
    
    def list_cameras(self):
        """Lista todas as câmeras disponíveis"""
        self.camera_combo.clear()
        found_cameras = []
        
        print("🔍 Procurando câmeras disponíveis...")
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found_cameras.append(i)
                    self.camera_combo.addItem(f"Câmera {i}", i)
                    print(f"  ✅ Câmera {i} detectada")
                cap.release()
        
        if len(found_cameras) == 0:
            print("  ⚠️ Nenhuma câmera detectada!")
            self.camera_combo.addItem("Nenhuma câmera detectada", -1)
            self.camera_combo.setEnabled(False)
            self.btn_open.setEnabled(False)
        else:
            print(f"  📹 Total: {len(found_cameras)} câmera(s) disponível(is)")
            self.camera_combo.setEnabled(True)
            self.btn_open.setEnabled(True)
    
    def open_camera(self):
        """Abre a câmera selecionada"""
        if self.camera_combo.count() == 0:
            print("❌ Nenhuma câmera disponível!")
            return
        
        index = self.camera_combo.currentData()
        
        if index == -1:
            print("❌ Câmera inválida selecionada!")
            return
        
        print(f"📹 Abrindo Câmera {index}...")
        
        if self.camera_thread.set_camera(index):
            self.camera_thread.start()
            self.lbl_status.setText("AGUARDANDO")
            self.lbl_status.setStyleSheet("background-color: gray; color: white; padding: 20px; border-radius: 10px;")
            
            self.camera_combo.setEnabled(False)
            self.btn_open.setEnabled(False)
            self.btn_close.setEnabled(True)
            self.btn_reload.setEnabled(False)
            self.btn_start_inspection.setEnabled(True)
            
            print("✅ Câmera aberta com sucesso!")
        else:
            print(f"❌ Falha ao abrir Câmera {index}")
            self.lbl_status.setText("ERRO AO ABRIR")
            self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
    
    def close_camera(self):
        """Fecha a câmera"""
        print("⏹️ Fechando câmera...")
        
        if self.camera_thread.inspecting:
            self.camera_thread.stop_inspection()
        
        self.camera_thread.stop()
        
        self.video_label.clear()
        self.video_label.setText("Câmera fechada")
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #555; color: white;")
        
        self.lbl_status.setText("CÂMERA FECHADA")
        self.lbl_status.setStyleSheet("background-color: gray; color: white; padding: 20px; border-radius: 10px;")
        
        self.camera_combo.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_close.setEnabled(False)
        self.btn_reload.setEnabled(True)
        self.btn_start_inspection.setEnabled(False)
        self.btn_stop_inspection.setEnabled(False)
        
        print("✅ Câmera fechada com sucesso!")
    
    def update_frame(self, frame: np.ndarray):
        """Atualiza o frame de vídeo na interface"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        scaled_pixmap = pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
    
    def on_code_detected(self, code_data: dict):
        """Callback quando um código é detectado"""
        timestamp = code_data['timestamp']
        code_type = code_data['type']
        code_value = code_data['data']
        
        history_text = f"[{timestamp}] {code_type}: {code_value}"
        self.history_list.addItem(history_text)
        self.history_list.scrollToBottom()
        
        try:
            expected = int(self.txt_expected.text())
        except:
            expected = 1
        
        if len(self.current_thumbnails) < expected:
            self.add_thumbnail(code_data['image'], code_type, code_value, expected)
    
    def clear_thumbnails(self):
        """Limpa todas as miniaturas"""
        while self.thumbnails_layout.count():
            item = self.thumbnails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.current_thumbnails.clear()
    
    def add_thumbnail(self, img: np.ndarray, code_type: str, code_value: str, max_codes: int):
        """Adiciona miniatura do código detectado em grid com tamanho FIXO
        
        Layout otimizado para caber até 8 códigos em 2 colunas
        """
        if img.size == 0:
            return
        
        index = len(self.current_thumbnails)
        row = index // 2
        col = index % 2
        
        # ✅ TAMANHO REDUZIDO: 120x100 (era 150x130)
        thumb_widget = QWidget()
        thumb_widget.setFixedSize(140, 140)  # Container compacto
        thumb_layout = QVBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(3, 3, 3, 3)
        thumb_layout.setSpacing(3)
        
        # ============ PROCESSAMENTO DA IMAGEM ============
        
        # Verifica se é escala de cinza ou colorida
        if len(img.shape) == 2:
            # Escala de cinza ou binarizada
            h, w = img.shape
            
            # Converte para RGB para exibição no Qt
            if img.dtype == np.uint8 and len(np.unique(img)) <= 2:
                # Imagem binarizada (preto e branco puro)
                rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                # Escala de cinza normal
                rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            
            bytes_per_line = 3 * w
            qt_format = QImage.Format_RGB888
        else:
            # Imagem colorida
            h, w, ch = img.shape
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            bytes_per_line = ch * w
            qt_format = QImage.Format_RGB888
        
        # ============ CRIA QIMAGE ============
        
        qt_image = QImage(rgb_img.data, w, h, bytes_per_line, qt_format)
        pixmap = QPixmap.fromImage(qt_image)
        
        # ✅ LABEL COM TAMANHO REDUZIDO: 120x100 pixels
        img_label = QLabel()
        img_label.setFixedSize(120, 100)
        img_label.setAlignment(Qt.AlignCenter)
        
        # ✅ ESCALA para preencher exatamente o espaço
        scaled_pixmap = pixmap.scaled(
            120, 100,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        img_label.setPixmap(scaled_pixmap)
        
        # ✅ BORDA VERDE + FUNDO BRANCO (mais fina)
        img_label.setStyleSheet("""
            border: 2px solid #4CAF50;
            background-color: white;
            padding: 1px;
        """)
        
        thumb_layout.addWidget(img_label)
        
        # ============ TEXTO COMPACTO ============
        
        # Trunca texto longo
        display_text = code_value
        if len(display_text) > 15:
            display_text = display_text[:12] + "..."
        
        text_label = QLabel(f"{code_type}\n{display_text}")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setFixedHeight(30)  # Reduzido de 50 para 30
        text_label.setStyleSheet("""
            font-size: 8px;
            color: #333;
            font-weight: bold;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 2px;
        """)
        
        thumb_layout.addWidget(text_label)
        
        # ============ ADICIONA AO GRID ============
        
        self.thumbnails_layout.addWidget(thumb_widget, row, col)
        self.current_thumbnails.append(thumb_widget)
    
    def start_inspection(self):
        """Inicia ciclo de inspeção"""
        if not self.camera_thread.isRunning():
            self.lbl_status.setText("ERRO: Abra a câmera primeiro!")
            self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
            print("⚠️ Tentativa de iniciar inspeção sem câmera aberta!")
            return
        
        try:
            expected_text = self.txt_expected.text().strip()
            timeout_text = self.txt_timeout.text().strip()
            
            if not expected_text or not timeout_text:
                self.lbl_status.setText("ERRO: Preencha os campos")
                self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
                return
            
            expected = int(expected_text)
            timeout = int(timeout_text)
            
            if expected < 1 or expected > 8:
                self.lbl_status.setText("ERRO: Códigos deve ser 1-8")
                self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
                return
            
            if timeout < 1 or timeout > 300:
                self.lbl_status.setText("ERRO: Tempo deve ser 1-300s")
                self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
                return
            
        except ValueError:
            self.lbl_status.setText("ERRO: Digite apenas números")
            self.lbl_status.setStyleSheet("background-color: red; color: white; padding: 20px; border-radius: 10px;")
            return
        
        self.clear_thumbnails()
        
        self.lbl_status.setText("INSPECIONANDO...")
        self.lbl_status.setStyleSheet("background-color: orange; color: white; padding: 20px; border-radius: 10px;")
     
        self.btn_start_inspection.setEnabled(False)
        self.btn_stop_inspection.setEnabled(True)
        
        print(f"▶️ Inspeção iniciada: {expected} código(s), timeout: {timeout}s")
        
        self.camera_thread.start_inspection(expected, timeout)
    
    def stop_inspection(self):
        """Finaliza a inspeção manualmente"""
        self.camera_thread.stop_inspection()
        
        try:
            expected = int(self.txt_expected.text())
        except:
            expected = 0
        
        detected = len(self.camera_thread.detected_codes)
        
        self.lbl_status.setText("⏹️ INTERROMPIDO")
        self.lbl_status.setStyleSheet("background-color: #FF9800; color: white; padding: 20px; border-radius: 10px;")
        
        self.btn_start_inspection.setEnabled(True)
        self.btn_stop_inspection.setEnabled(False)
    
    def on_inspection_complete(self, success: bool, detected: int):
        """Callback quando a inspeção termina"""
        try:
            expected = int(self.txt_expected.text())
        except:
            expected = 1
        
        if detected == expected:
            self.lbl_status.setText("✅ OK")
            self.lbl_status.setStyleSheet("background-color: #4CAF50; color: white; padding: 20px; border-radius: 10px;")
            print(f"✅ Inspeção APROVADA: {detected}/{expected} códigos detectados")
        elif detected < expected:
            self.lbl_status.setText(f"❌ NG (Faltam {expected - detected})")
            self.lbl_status.setStyleSheet("background-color: #f44336; color: white; padding: 20px; border-radius: 10px;")
            print(f"❌ Inspeção REPROVADA: Apenas {detected}/{expected} códigos detectados (FALTANDO)")
        else:
            self.lbl_status.setText(f"❌ NG (+{detected - expected} a mais)")
            self.lbl_status.setStyleSheet("background-color: #FF9800; color: white; padding: 20px; border-radius: 10px;")
            print(f"❌ Inspeção REPROVADA: {detected}/{expected} códigos detectados (EXCESSO)")
        
        self.btn_start_inspection.setEnabled(True)
        self.btn_stop_inspection.setEnabled(False)
        
        QTimer.singleShot(1000, self.auto_restart_inspection)
    
    def auto_restart_inspection(self):
        """Reinicia automaticamente se ainda estiver na mesma tela"""
        if self.btn_start_inspection.isEnabled():
            self.start_inspection()
    
    def toggle_fast_mode(self, checked: bool):
        """Alterna modo rápido"""
        self.camera_thread.frame_skip = 3 if checked else 1
    
    def update_pdi(self, param: str, value):
        """Atualiza parâmetro de PDI"""
        self.camera_thread.update_pdi_param(param, value)
    
    def save_config(self):
        """Salva configuração em arquivo JSON com nome sequencial"""
        print("\n" + "="*60)
        print("💾 Salvando configuração...")
        
        try:
            self.camera_thread.params_mutex.lock()
            try:
                config = self.camera_thread.pdi_params.copy()
            finally:
                self.camera_thread.params_mutex.unlock()
            
            counter = 1
            while True:
                filename = f"modelo{counter}.json"
                if not Path(filename).exists():
                    break
                counter += 1
                if counter > 100:
                    print("❌ Erro: Muitos arquivos (modelo1 até modelo100 já existem)")
                    raise Exception("Limite de arquivos atingido")
            
            print(f"📝 Salvando em: {filename}")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Configuração salva com sucesso em: {filename}")
            print(f"📄 Conteúdo: {config}")
            
            original_text = self.btn_save_config.text()
            self.btn_save_config.setText(f"✅ Salvo: {filename}")
            self.btn_save_config.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            QTimer.singleShot(3000, lambda: self.btn_save_config.setText(original_text))
            QTimer.singleShot(3000, lambda: self.btn_save_config.setStyleSheet(""))
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {str(e)}")
            import traceback
            traceback.print_exc()
            
            original_text = self.btn_save_config.text()
            self.btn_save_config.setText("❌ Erro ao salvar!")
            self.btn_save_config.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            QTimer.singleShot(3000, lambda: self.btn_save_config.setText(original_text))
            QTimer.singleShot(3000, lambda: self.btn_save_config.setStyleSheet(""))

    def load_config(self):
        """Carrega configuração do último arquivo modelo disponível"""
        print("\n" + "="*60)
        print("📂 Carregando configuração...")
        
        try:
            modelo_files = sorted(Path('.').glob('modelo*.json'))
            
            if not modelo_files:
                print("❌ Nenhum arquivo modelo*.json encontrado!")
                self.show_config_error("Nenhum arquivo encontrado!")
                return
            
            filename = modelo_files[-1]
            print(f"📂 Carregando: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"📄 Configuração lida: {config}")
            
            if not isinstance(config, dict):
                raise ValueError("Arquivo JSON inválido")
            
            print("🔲 Atualizando checkboxes...")
            
            if "auto_exposure" in config:
                self.check_auto_exp.blockSignals(True)
                self.check_auto_exp.setChecked(bool(config["auto_exposure"]))
                self.check_auto_exp.blockSignals(False)
                
            if "auto_focus" in config:
                self.check_auto_focus.blockSignals(True)
                self.check_auto_focus.setChecked(bool(config["auto_focus"]))
                self.check_auto_focus.blockSignals(False)
                
            if "boost" in config:
                self.check_boost.blockSignals(True)
                self.check_boost.setChecked(bool(config["boost"]))
                self.check_boost.blockSignals(False)
            
            print("🎚️ Atualizando sliders...")
            self.update_slider_value(self.slider_exposure, "exposure", config)
            self.update_slider_value(self.slider_gain, "gain", config)
            self.update_slider_value(self.slider_brightness, "brightness", config)
            self.update_slider_value(self.slider_contrast, "contrast", config)
            self.update_slider_value(self.slider_gamma, "gamma", config)
            self.update_slider_value(self.slider_focus, "focus", config)
            self.update_slider_value(self.slider_beta, "beta", config)
            self.update_slider_value(self.slider_alpha, "alpha", config, is_float=True)
            
            print("🔒 Aplicando na thread...")
            self.camera_thread.params_mutex.lock()
            try:
                for key, value in config.items():
                    self.camera_thread.pdi_params[key] = value
                self.camera_thread.params_changed = True
            finally:
                self.camera_thread.params_mutex.unlock()
            
            print(f"✅ Configuração carregada de: {filename}")
            
            original_text = self.btn_load_config.text()
            self.btn_load_config.setText(f"✅ {filename.name}")
            self.btn_load_config.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            QTimer.singleShot(3000, lambda: self.btn_load_config.setText(original_text))
            QTimer.singleShot(3000, lambda: self.btn_load_config.setStyleSheet(""))
            
            print("="*60 + "\n")
            
        except FileNotFoundError:
            print("❌ Arquivo não encontrado")
            self.show_config_error("Arquivo não encontrado!")
            
        except json.JSONDecodeError:
            print("❌ JSON inválido")
            self.show_config_error("JSON inválido!")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_config_error("Erro ao carregar!")
    
    def update_slider_value(self, slider_layout, param_name, config, is_float=False):
        """Atualiza o valor de um slider a partir do config"""
        if param_name not in config:
            return
        
        try:
            slider = slider_layout.itemAt(1).widget()
            if slider and isinstance(slider, QSlider):
                slider.blockSignals(True)
                if is_float:
                    slider.setValue(int(config[param_name] * 100))
                else:
                    slider.setValue(int(config[param_name]))
                slider.blockSignals(False)
                print(f"  ✓ {param_name} atualizado para {config[param_name]}")
        except Exception as e:
            print(f"  ⚠️ Erro ao atualizar {param_name}: {e}")

    def show_config_error(self, message):
        """Mostra erro de configuração no botão"""
        original_text = self.btn_load_config.text()
        self.btn_load_config.setText(f"❌ {message}")
        self.btn_load_config.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        QTimer.singleShot(3000, lambda: self.btn_load_config.setText(original_text))
        QTimer.singleShot(3000, lambda: self.btn_load_config.setStyleSheet(""))
    
    def closeEvent(self, event):
        """Cleanup ao fechar a aplicação"""
        print("🛑 Fechando aplicação...")
        self.camera_thread.stop()
        print("✅ Aplicação fechada com sucesso!")
        event.accept()

    def toggle_fullscreen(self):
        """Alterna entre tela cheia e modo janela"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)
            print("🖼️ Modo janela")
        else:
            self.showFullScreen()
            self.fullscreen_action.setChecked(True)
            print("⛶ Modo tela cheia (pressione F11 ou ESC para sair)")
    
    def keyPressEvent(self, event):
        """Detecta teclas pressionadas"""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)
    
    def show_about(self):
        """Mostra informações sobre o sistema"""
        about_text = """
        <h2>Sistema de Detecção de Códigos 1D/2D</h2>
        <p><b>Versão:</b> 4.1 (Otimizado para Pcyes FHD-03)</p>
        <p><b>Câmera:</b> Webcam Pcyes Raza Auto Focus FHD-03 1080P</p>
        <p><b>Desenvolvido para:</b> Ubuntu + VSCode</p>
        <p><b>Python:</b> 3.10+</p>
        
        <h3>Otimizações FHD-03:</h3>
        <ul>
            <li>✅ Suporte completo a autofoco automático</li>
            <li>✅ Resolução otimizada (720p para melhor performance)</li>
            <li>✅ Pré-processamento CLAHE para objetos próximos (10cm+)</li>
            <li>✅ Codec MJPEG para menor latência</li>
            <li>✅ Auto exposição otimizada para leitura de códigos</li>
        </ul>
        
        <h3>Bibliotecas:</h3>
        <ul>
            <li>PyQt5 - Interface gráfica</li>
            <li>OpenCV - Processamento de imagem</li>
            <li>pyzbar - Detecção de códigos 1D/2D</li>
            <li>pylibdmtx - Detecção de DataMatrix</li>
        </ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre o Sistema")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    def show_shortcuts(self):
        """Mostra atalhos de teclado"""
        shortcuts_text = """
        <h2>⌨️ Atalhos de Teclado</h2>
        
        <h3>Geral:</h3>
        <ul>
            <li><b>F11</b> - Alternar tela cheia</li>
            <li><b>ESC</b> - Sair da tela cheia</li>
            <li><b>Ctrl+Q</b> - Fechar aplicação</li>
            <li><b>Ctrl+M</b> - Minimizar janela</li>
        </ul>
        
        <h3>Dicas para FHD-03:</h3>
        <ul>
            <li>Mantenha autofoco ATIVADO (recomendado)</li>
            <li>Mantenha auto exposição ATIVADA (recomendado)</li>
            <li>Distância mínima: 10cm do código</li>
            <li>Salve suas configurações personalizadas</li>
            <li>Use modo rápido apenas se necessário</li>
        </ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Atalhos de Teclado")
        msg.setTextFormat(Qt.RichText)
        msg.setText(shortcuts_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()


# ==================== EXECUÇÃO PRINCIPAL ====================
def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 Sistema de Detecção de Códigos 1D/2D")
    print("📹 Otimizado para: Webcam Pcyes Raza Auto Focus FHD-03")
    print("=" * 60)
    print()
    
    if not PYZBAR_AVAILABLE:
        print("⚠️  AVISO: pyzbar não está instalado!")
        print("   Instale com: pip install pyzbar")
        print()
    
    if not PYLIBDMTX_AVAILABLE:
        print("⚠️  AVISO: pylibdmtx não está instalado!")
        print("   Instale com: pip install pylibdmtx")
        print()
    
    if not PYZBAR_AVAILABLE and not PYLIBDMTX_AVAILABLE:
        print("❌ ERRO: Nenhuma biblioteca de detecção disponível!")
        print("   O sistema não conseguirá detectar códigos.")
        print()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    print("✅ Interface carregada com sucesso!")
    print()
    print("📌 Otimizações aplicadas para FHD-03:")
    print("   • Resolução: 1280x720 @ 30fps (otimizado)")
    print("   • Codec: MJPEG (menor latência)")
    print("   • Autofoco: Ativado por padrão")
    print("   • Auto exposição: Ativada por padrão")
    print("   • Pré-processamento CLAHE para objetos próximos")
    print("   • Sharpness alto (200) para melhor detecção")
    print()
    print("🎯 Instruções:")
    print("   1. Conecte a Pcyes FHD-03")
    print("   2. Clique em 'Recarregar' e 'Abrir'")
    print("   3. Aguarde 1s para autofoco estabilizar")
    print("   4. Configure quantidade de códigos e timeout")
    print("   5. Clique em 'Iniciar Inspeção'")
    print()
    print("⚠️ Lembre-se: Distância mínima de 10cm do código!")
    print()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()