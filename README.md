# 📚 Sistema de Detecção de Códigos 1D/2D
```
=======================================================================================
LEITOR DE CÓDIGOS DE BARRAS E QRCODE 
=======================================================================================
Sistema de Detecção de Códigos 1D/2D com PDI (Processamento Digital de Imagens)
Desenvolvido para Ubuntu + VSCode
Python 3.10+

=======================================================================================
```

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Características](#-características)
3. [Requisitos](#-requisitos)
4. [Instalação](#-instalação)
5. [Pipeline de Funcionamento](#-pipeline-de-funcionamento)
6. [Arquitetura do Sistema](#-arquitetura-do-sistema)
7. [Guia de Uso](#-guia-de-uso)
8. [Parâmetros e Configurações](#-parâmetros-e-configurações)


---

## 🎯 Visão Geral

Sistema profissional de detecção e validação de códigos de barras (1D) e códigos 2D (QR Code, DataMatrix) utilizando visão computacional e processamento digital de imagens. Otimizado especificamente para a **Webcam Pcyes Raza Auto Focus FHD-03**.

### Principais Funcionalidades

- ✅ **Detecção Multi-Código**: Suporta até 8 códigos simultaneamente
- ✅ **Tipos Suportados**: EAN13, CODE128, QR Code, DataMatrix, CODE39, UPC-A, RSS14, e mais
- ✅ **Retificação de Perspectiva**: Corrige códigos inclinados/tortos automaticamente
- ✅ **Pipeline PDI Completo**: CLAHE, binarização adaptativa, sharpening, morfologia
- ✅ **Interface Gráfica Intuitiva**: PyQt5 com feedback visual em tempo real
- ✅ **Configurações Salváveis**: Sistema de profiles para diferentes cenários
- ✅ **Modo Inspeção**: Validação automática com timeout configurável
- ✅ **Miniaturas Processadas**: Visualização das etapas de PDI aplicadas

---

## ⭐ Características

### Detecção Avançada
- **Retificação de Perspectiva**: Códigos tortos são automaticamente corrigidos
- **Multi-Etapa PDI**: Pipeline de 5 etapas para máxima precisão
- **Validação Inteligente**: Filtros anti-ruído e validação de conteúdo
- **Detecção em Tempo Real**: 30 FPS com processamento otimizado

### Interface Profissional
- **3 Painéis Organizados**: Controles, Vídeo/Status, Histórico/Miniaturas
- **Feedback Visual**: Retângulos verdes, legendas, contador em tempo real
- **Miniaturas Procesadas**: Visualize imagens binarizadas, enhanced ou grayscale
- **Modo Tela Cheia**: Maximiza área de visualização (F11)

### Configuração Flexível
- **Parâmetros de Câmera**: Exposição, ganho, brilho, contraste, gamma, foco
- **Boost Digital**: Alpha/Beta para ajustes pós-captura
- **Profiles Salvos**: Crie e carregue configurações personalizadas
- **Modo Rápido**: Processa 1 a cada 3 frames para economia de recursos

---

## 💻 Requisitos

### Hardware
- **Sistema Operacional**: Ubuntu 20.04+ (testado em 22.04)
- **Câmera**: Pcyes Raza Auto Focus FHD-03 1080P (recomendado)
  - Qualquer webcam USB com suporte V4L2 também funciona
- **Processador**: Dual-core 2.0GHz+ (Quad-core recomendado)
- **RAM**: 4GB mínimo (8GB recomendado)
- **USB**: Porta USB 2.0+ disponível

### Software
- **Python**: 3.10 ou superior
- **pip**: Gerenciador de pacotes Python
- **Git**: Para clonar o repositório (opcional)

---

## 📦 Instalação

### 1. Clonar o Repositório
```bash
git clone https://github.com/limaabr/Time5_Deteccao_Codigos2d3d.git
cd detector-codigos
```

### 2. Criar Ambiente Virtual (Recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

**Arquivo `requirements.txt`:**
```
PyQt5==5.15.9
opencv-python==4.8.1.78
numpy==1.24.3
pyzbar==0.1.9
pylibdmtx==0.1.10
```

### 4. Instalar Dependências do Sistema (Ubuntu/Debian)
```bash
# Para pyzbar
sudo apt-get install libzbar0

# Para pylibdmtx
sudo apt-get install libdmtx0b

# Para OpenCV (se necessário)
sudo apt-get install python3-opencv
```

### 5. Verificar Instalação
```bash
python3 -c "import cv2, pyzbar, pylibdmtx; print('✅ Tudo OK!')"
```

### 6. Executar o Sistema
```bash
python3 Time5_Deteccao_Codigos2.py
```

---

## 🔄 Pipeline de Funcionamento

O sistema utiliza um pipeline otimizado de **5 etapas** para máxima precisão na detecção:

### 📊 Diagrama do Pipeline
```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPTURA DE VÍDEO                            │
│  Câmera → Frame RAW (1280x720 @ 30fps) → Boost (se ativo)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 ETAPA 1: DETECÇÃO INICIAL (LOCALIZAÇÃO)            │
│  • Converte para escala de cinza                                   │
│  • pyzbar.decode() - Detecção rápida                              │
│  • Valida tamanho e conteúdo (anti-ruído)                         │
│  • Armazena regiões detectadas (bbox + polígono)                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ETAPA 2: RECORTE COM MARGEM DE SEGURANÇA              │
│  • Expande região em 20% (não corta bordas)                        │
│  • Recorta ROI (Region of Interest)                               │
│  • Preserva coordenadas originais                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│             ETAPA 3: RETIFICAÇÃO DE PERSPECTIVA                    │
│  • Ajusta coordenadas do polígono para ROI                         │
│  • Calcula matriz de transformação (cv2.getPerspectiveTransform)  │
│  • Aplica warpPerspective → Código RETO                          │
│  • Define tamanho mínimo (100x50px) para resolução adequada       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│           ETAPA 4: PIPELINE DE PDI (Imagem Retificada)            │
│                                                                     │
│  4.1 CLAHE (Equalização Adaptativa)                               │
│      • clipLimit=2.0, tileGridSize=(8,8)                          │
│      • Melhora contraste em iluminação irregular                   │
│                                                                     │
│  4.2 Conversão para Escala de Cinza                               │
│      • Reduz dimensões (BGR → GRAY)                               │
│      • Foca na luminosidade                                        │
│                                                                     │
│  4.3 Binarização Adaptativa (Gaussian)                            │
│      • CRITICAL para códigos 1D!                                   │
│      • blockSize=11, C=2                                          │
│      • Separa barras pretas de brancas                            │
│                                                                     │
│  4.4 Morfologia (Remoção de Ruído)                                │
│      • Kernel 3x3, MORPH_CLOSE                                    │
│      • Remove artefatos pequenos                                   │
│                                                                     │
│  4.5 Sharpening (Unsharp Mask)                                    │
│      • GaussianBlur + addWeighted                                 │
│      • Aguça bordas para leitura precisa                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│           ETAPA 5: RE-DETECÇÃO COM ALTA PRECISÃO                  │
│  Tenta detectar em MÚLTIPLAS versões (ordem de prioridade):       │
│                                                                     │
│  1️⃣ Binary (denoised)    → Melhor para códigos 1D               │
│  2️⃣ Sharpened (gray)     → Melhor para detalhes finos           │
│  3️⃣ Enhanced (CLAHE)     → Melhor para códigos 2D               │
│                                                                     │
│  • Seleciona melhor resultado (maior confiança)                   │
│  • Valida conteúdo (mínimo 3 caracteres)                         │
│  • Armazena TODAS as versões para miniaturas                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FALLBACK (Se nada detectado)                    │
│  • Aplica PDI no FRAME COMPLETO                                    │
│  • Tenta detectar novamente (3 versões)                           │
│  • Última chance para códigos difíceis                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RESULTADO FINAL                                 │
│  • Desenha retângulos verdes no frame                             │
│  • Adiciona legendas (tipo + conteúdo)                            │
│  • Emite sinal para interface (miniaturas + histórico)           │
│  • Atualiza contador de inspeção                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura do Sistema

### Estrutura de Classes
```
┌────────────────────────────────────────────────────────────────┐
│                         MainWindow                             │
│  • Interface PyQt5                                             │
│  • Controles de usuário                                        │
│  • Histórico e miniaturas                                      │
└──────────────────────┬─────────────────────────────────────────┘
                       │ (sinais/slots)
                       │
                       ▼
┌────────────────────────────────────────────────────────────────┐
│                      CameraThread                              │
│  • QThread (processamento assíncrono)                          │
│  • Captura de vídeo                                            │
│  • Detecção de códigos                                         │
│  • Aplicação de PDI                                            │
└────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados
```
[Câmera] → [CameraThread] → [detect_codes()] → [Validação] → [MainWindow]
                ↓                                                   ↓
        [apply_pdi_params()]                              [Histórico/Miniaturas]
                ↓                                                   ↓
        [Parâmetros Hardware]                          [Feedback Visual]
```

### Thread Safety

O sistema utiliza **QMutex** para garantir acesso thread-safe aos parâmetros:
```python
# Atualização de parâmetros (MainWindow → CameraThread)
self.params_mutex.lock()
self.pdi_params[param] = value
self.params_changed = True
self.params_mutex.unlock()

# Leitura de parâmetros (CameraThread)
self.params_mutex.lock()
params = self.pdi_params.copy()
self.params_mutex.unlock()
```

---

## 📖 Guia de Uso

### 1️⃣ Iniciar o Sistema
```bash
python3 detector_codigos.py
```

### 2️⃣ Conectar Câmera

1. Conecte a Pcyes FHD-03 via USB
2. Clique em **"🔄 Recarregar"** para buscar câmeras
3. Selecione a câmera na lista
4. Clique em **"▶️ Abrir"**
5. Aguarde **1 segundo** (autofoco estabilizando)

### 3️⃣ Configurar Inspeção

| Parâmetro | Descrição | Valores |
|-----------|-----------|---------|
| **Códigos esperados** | Quantidade de códigos a detectar | 1-8 |
| **Tempo limite** | Timeout para inspeção | 1-300s |
| **Modo rápido** | Processa 1 a cada 3 frames | ☐/☑ |
| **Tipo de miniatura** | Versão PDI nas miniaturas | Binary/Enhanced/Gray |

### 4️⃣ Iniciar Inspeção

1. Clique em **"▶️ Iniciar Inspeção"**
2. Posicione códigos a **10-30cm** da câmera
3. Aguarde detecção (retângulos verdes)
4. Sistema mostra: **✅ OK** ou **❌ NG**

### 5️⃣ Resultados

**Aprovado (OK):**
- Status verde: **✅ OK**
- Detectou exatamente a quantidade esperada

**Reprovado (NG):**
- Status vermelho: **❌ NG (Faltam X)**
- Status laranja: **❌ NG (+X a mais)**

---

## ⚙️ Parâmetros e Configurações

### Parâmetros de Câmera (Hardware)

Estes ajustam **fisicamente** a câmera Pcyes FHD-03:

#### 📸 Auto Exposição ✅ (Recomendado)
- **Ativo**: Câmera ajusta exposição automaticamente
- **Desativo**: Controle manual via slider (-13 a -1)
- **Quando desativar**: Iluminação muito variável

#### 🔍 Auto Foco ✅ (Recomendado)
- **Ativo**: Câmera foca automaticamente
- **Desativo**: Foco manual via slider (0-255)
- **Quando desativar**: Códigos em distância fixa

#### 📊 Ganho (ISO)
- **Valores**: 0-100
- **Baixo (0-20)**: Imagem limpa, precisa luz
- **Médio (20-50)**: Balanceado
- **Alto (50-100)**: Ambiente escuro, mais ruído

#### 💡 Brilho
- **Valores**: 0-255 (padrão: 128)
- **Função**: Offset de luminosidade
- **Uso**: Ajuste fino após exposição

#### 🎨 Contraste
- **Valores**: 0-100 (padrão: 40)
- **CRÍTICO para códigos 1D!**
- **60-80**: Ideal para barras (EAN, CODE128)
- **30-50**: Ideal para códigos 2D (QR, DataMatrix)

#### 🌈 Gamma
- **Valores**: 0-200 (padrão: 100)
- **Função**: Ajusta curva de luminosidade
- **Uso**: Realça sombras ou highlights

---

### Parâmetros de Software (Boost)

Estes ajustam a imagem **após captura**:

#### ⚡ Boost (Checkbox)
- Ativa ganho digital (alpha/beta)
- Usa quando hardware não resolve

#### 📈 Alpha (Contraste Digital)
- **Valores**: 0.1-3.0 (padrão: 1.0)
- **Função**: Multiplica valores de pixel
- **1.5-2.0**: Aumenta contraste para códigos desbotados

#### ➕ Beta (Offset Digital)
- **Valores**: -100 a +100 (padrão: 0)
- **Função**: Adiciona valor fixo aos pixels
- **+20 a +50**: Clareia imagem escura

---

### Salvar/Carregar Configurações

#### 💾 Salvar Config
```bash
Gera arquivo: modelo1.json, modelo2.json, ...
```

**Conteúdo:**
```json
{
  "auto_exposure": true,
  "exposure": -6,
  "gain": 0,
  "brightness": 128,
  "contrast": 50,
  "gamma": 100,
  "auto_focus": true,
  "focus": 0,
  "boost": false,
  "alpha": 1.0,
  "beta": 0
}
```

#### 📂 Carregar Config
- Carrega **último** arquivo `modeloX.json`
- Aplica **todos** os parâmetros automaticamente

---

## 🔧 Troubleshooting

### ❌ Câmera não detectada

**Sintomas:**
```
⚠️ Nenhuma câmera detectada!
```

**Soluções:**
1. Verifique se USB está conectado
2. Teste câmera em outro aplicativo:
```bash
   cheese  # Ubuntu camera app
```
3. Verifique permissões:
```bash
   sudo chmod 666 /dev/video0
```
4. Liste dispositivos V4L2:
```bash
   v4l2-ctl --list-devices
```

---

### ❌ Não detecta NADA

**Sintomas:**
- Vídeo aparece mas não detecta códigos
- Nenhum retângulo verde

**Soluções:**
1. **Desative Modo Rápido**
2. **Ative Auto Exposição** e **Auto Foco**
3. **Aumente Contraste** (50-70)
4. Verifique distância: **10-30cm**
5. Teste com código impresso grande

---

### ❌ Códigos 1D (barras) não detectam

**Sintomas:**
- QR Code detecta, mas EAN/CODE128 não

**Soluções:**
1. **Aumente CONTRASTE** (60-80) ← **CRÍTICO!**
2. Verifique miniatura **Binarizada**:
   - Deve ter barras **pretas puras**
   - Se cinza, aumente contraste
3. **Desative Modo Rápido**
4. Verifique foco (barras devem estar nítidas)

---

### ❌ Códigos 2D (QR) não detectam

**Sintomas:**
- Barras detectam, mas QR Code não

**Soluções:**
1. **Ative Auto Foco** ← **Essencial!**
2. **Reduza Contraste** (30-40)
3. Aumente **Brilho** se QR muito escuro
4. Verifique miniatura **Enhanced**:
   - Deve ter boa iluminação
   - Pixels visíveis e claros

---

### ❌ Sistema LENTO/Travando

**Sintomas:**
- Interface congela
- Vídeo com delay

**Soluções:**
1. **Ative Modo Rápido** ← Reduz 66% processamento
2. Feche outros programas
3. Reduza **Códigos Esperados** (menos miniaturas)
4. Verifique uso de CPU:
```bash
   top
```

---

### ❌ Miniaturas tortas/erradas

**Sintomas:**
- Miniaturas mostram códigos inclinados
- Miniaturas de códigos diferentes

**Solução:**
- **Já corrigido na versão 6!**
- Sistema usa retificação de perspectiva
- Se persistir, reporte o bug

---

## 📊 Códigos Suportados

| Tipo | 1D/2D | Uso Comum | Configuração Ideal |
|------|-------|-----------|-------------------|
| **EAN13** | 1D | Produtos de varejo | Contraste: 70 |
| **CODE128** | 1D | Logística, embalagens | Contraste: 65 |
| **CODE39** | 1D | Indústria, inventário | Contraste: 60 |
| **UPC-A** | 1D | Produtos americanos | Contraste: 70 |
| **QR Code** | 2D | URLs, textos, vCards | Auto Foco ✅ |
| **DataMatrix** | 2D | Eletrônicos, PCBs | Enhanced mode |
| **PDF417** | 2D | Documentos, IDs | Contraste: 50 |
| **AZTEC** | 2D | Bilhetes, ingressos | Enhanced mode |

---

## 🎯 Workflows Recomendados

### Códigos 1D (EAN, CODE128, CODE39)
```yaml
Configuração:
  - Contraste: 60-80  # CRÍTICO!
  - Auto Exposição: ✅
  - Auto Foco: ✅
  - Modo Rápido: ❌ (desligado)
  - Miniatura: Binarizada (para debug)

Checklist:
  ✓ Barras nítidas e pretas
  ✓ Distância 15-25cm
  ✓ Iluminação uniforme
  ✓ Código reto (ou use retificação)
```

### Códigos 2D (QR Code, DataMatrix)
```yaml
Configuração:
  - Contraste: 30-50
  - Auto Exposição: ✅
  - Auto Foco: ✅  # ESSENCIAL!
  - Modo Rápido: ✅ (pode usar)
  - Miniatura: Enhanced (visualização)

Checklist:
  ✓ Código completo visível
  ✓ Distância 10-20cm
  ✓ Sem reflexos na superfície
  ✓ Foco nítido (autofoco ativo)
```

---

## 🔬 Modos de Miniatura

Controlam **qual versão processada** aparece nas miniaturas:

### 🖤 Binarizada (Preto e Branco)

**Pipeline:**
```
Retificada → Escala de Cinza → Binarização Adaptativa → Morfologia
```

**Resultado:**
- Apenas preto (0) e branco (255)
- **Melhor** para códigos **1D** (barras)

**Quando usar:**
- ✅ Debugar detecção de **códigos 1D**
- ✅ Ver se binarização está **correta**
- ✅ Identificar **ruído** (pontos indesejados)

---

### 🎨 Enhanced (CLAHE)

**Pipeline:**
```
Retificada → CLAHE (equalização adaptativa) → Colorida
```

**Resultado:**
- Imagem **colorida** com contraste melhorado
- **Melhor** para códigos **2D** (QR, DataMatrix)

**Quando usar:**
- ✅ Visualização **natural** do código
- ✅ Debugar problemas de **iluminação**
- ✅ Ver resultado do **CLAHE**

---

### ⚪ Escala de Cinza (Sharpened)

**Pipeline:**
```
Retificada → Enhanced → Escala de Cinza → Sharpening
```

**Resultado:**
- 256 tons de cinza **aguçados**
- **Melhor** para ver **detalhes finos**

**Quando usar:**
- ✅ Códigos **pequenos** ou **distantes**
- ✅ Debugar **foco** (se está nítido)
- ✅ Meio-termo entre binarizada e enhanced

---

## ⌨️ Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| **F11** | Alternar tela cheia |
| **ESC** | Sair da tela cheia |
| **Ctrl+Q** | Fechar aplicação |
| **Ctrl+M** | Minimizar janela |

---

## 📁 Estrutura de Arquivos
```
Desafio5_CodeDetect_2D3D/
├── Desafio5_CodeDetect_2D3D_v6.py      # Código principal
├── requirements.txt                    # Dependências Python
├── README.md                           # Esta documentação
├── GUIA DETALHADO PARAMETROS.md        # Guia de Parâmetros  
├── modelo1.json                        # Configuração salva (se gerada)
└── GUIA RÁPIDO DE TROUBLESHOOTING      # Guia de Troubleshooting
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 🙏 Agradecimentos

- **OpenCV** - Biblioteca de visão computacional
- **pyzbar** - Decodificador de códigos de barras
- **pylibdmtx** - Decodificador DataMatrix
- **PyQt5** - Framework de interface gráfica
- **Pcyes** - Hardware utilizado no desenvolvimento

---

## 📚 Referências

- [OpenCV Documentation](https://docs.opencv.org/)
- [pyzbar GitHub](https://github.com/NaturalHistoryMuseum/pyzbar)
- [pylibdmtx GitHub](https://github.com/NaturalHistoryMuseum/pylibdmtx)
- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

---

**Última Atualização:** 2024  
**Status:** Em Produção