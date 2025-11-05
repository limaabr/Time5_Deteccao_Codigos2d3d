# 📚 GUIA COMPLETO: Entendendo o Sistema

Explicação **detalhada** de cada funcionalidade do sistema!

---

## ⚡ 1. MODO RÁPIDO vs MODO NORMAL

### **MODO NORMAL (Padrão)**
```python
self.frame_skip = 1  # Processa TODOS os frames
```

**Como funciona:**
- Processa **cada frame** da câmera (30 frames por segundo)
- **30 tentativas de detecção por segundo**
- Maior chance de detectar códigos em movimento
- Maior uso de CPU

**Quando usar:**
- ✅ Códigos em **movimento** (esteira, mão tremendo)
- ✅ Códigos **pequenos** ou **distantes**
- ✅ Códigos **borrados** (foco instável)
- ✅ Primeira tentativa de detecção

---

### **MODO RÁPIDO**
```python
self.frame_skip = 3  # Processa 1 frame a cada 3
```

**Como funciona:**
- Processa apenas **1 frame a cada 3** (10 frames por segundo)
- **10 tentativas de detecção por segundo**
- 66% menos processamento
- Menor uso de CPU/bateria

**Quando usar:**
- ✅ Códigos **parados** (fixos na mesa)
- ✅ Códigos **grandes** e **nítidos**
- ✅ Sistema **lento** (PC fraco)
- ✅ Economizar energia (laptop)

---

### **COMPARAÇÃO PRÁTICA:**

| Situação | Modo Normal | Modo Rápido |
|----------|-------------|-------------|
| Código parado, grande | 🟡 Ok (overkill) | ✅ Ideal |
| Código em movimento | ✅ Ideal | ❌ Pode perder frames |
| Código pequeno/distante | ✅ Necessário | ⚠️ Pode falhar |
| PC lento/travando | ❌ Sobrecarga | ✅ Resolve |
| Notebook (bateria) | 🔋🔋🔋 Alto consumo | 🔋 Econômico |

---

## 🎛️ 2. PARÂMETROS DE CÂMERA (Hardware)

Estes ajustam **fisicamente** a câmera antes de capturar a imagem.

---

### **📸 AUTO EXPOSIÇÃO** (Recomendado: ✅ ATIVO)

**O que faz:**
- Ajusta automaticamente a **quantidade de luz** que entra na câmera
- Equivalente ao "brilho automático" do celular

**Como funciona:**
```python
# ATIVO (modo 3):
self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
# Câmera ajusta exposição automaticamente
# Prioriza velocidade (evita motion blur)

# DESATIVO (modo 1):
self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
# Você controla manualmente via slider "Exposição"
```

**Quando usar MANUAL:**
- ❌ Ambiente com iluminação **muito variável** (sol entrando pela janela)
- ❌ Auto exposição **muito lenta** (demora para ajustar)
- ✅ Iluminação **controlada** (LED fixo)
- ✅ Códigos ficam **super claros ou super escuros**

**Valor do slider (se manual):**
- **-13 a -7**: Escuro (menos luz) → Evita "estourar" códigos em papel branco
- **-6 a -4**: Médio (padrão -6) → Equilibrado
- **-3 a -1**: Claro (mais luz) → Para ambientes escuros

---

### **🔍 AUTO FOCO** (Recomendado: ✅ ATIVO)

**O que faz:**
- Ajusta automaticamente o **foco** da lente
- Equivalente ao "toque para focar" do celular

**Como funciona:**
```python
# ATIVO (modo 1):
self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
# Câmera foca automaticamente no objeto mais próximo

# DESATIVO (modo 0):
self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
# Você controla manualmente via slider "Foco Manual"
```

**Quando usar MANUAL:**
- ❌ Autofoco **caçando** (fica focando e desfocando)
- ❌ Códigos em **distância fixa** (sempre 20cm da câmera)
- ✅ Autofoco muito **lento**
- ✅ Quer **máxima velocidade** (evita delay do autofoco)

**Valor do slider (se manual):**
- **0-50**: Foco próximo (5-15cm)
- **50-150**: Foco médio (15-50cm) → **Ideal para códigos**
- **150-255**: Foco longe (50cm+)

---

### **📊 GANHO (ISO)**

**O que faz:**
- **Amplifica** eletronicamente o sinal do sensor
- Equivalente ao ISO da fotografia

**Como funciona:**
```python
self.camera.set(cv2.CAP_PROP_GAIN, valor)
# 0 = sem amplificação (limpo)
# 100 = máxima amplificação (ruidoso)
```

**Valores:**
- **0-20**: Baixo ganho → Imagem limpa, precisa de BOA iluminação
- **20-50**: Médio ganho → Balanceado
- **50-100**: Alto ganho → Ambiente ESCURO, mas com **ruído**

**Quando aumentar:**
- ✅ Ambiente **escuro**
- ✅ Códigos ficam muito **escuros**
- ❌ Evite se iluminação for boa (gera ruído)

---

### **💡 BRILHO**

**O que faz:**
- Ajusta o **offset de luminosidade** (adiciona branco)
- **NÃO** muda a exposição física

**Como funciona:**
```python
self.camera.set(cv2.CAP_PROP_BRIGHTNESS, valor)
# 0 = muito escuro
# 128 = neutro (padrão)
# 255 = muito claro
```

**Quando ajustar:**
- ✅ Imagem toda muito **escura** (mesmo com exposição ok)
- ✅ Imagem toda muito **clara** (códigos desbotados)
- ⚠️ Use com moderação (pode "estourar" ou "esmagar" detalhes)

---

### **🎨 CONTRASTE**

**O que faz:**
- Aumenta a **diferença** entre claro e escuro
- Essencial para códigos **1D** (barras pretas vs brancas)

**Como funciona:**
```python
self.camera.set(cv2.CAP_PROP_CONTRAST, valor)
# 0 = imagem "chapada" (cinza uniforme)
# 40 = balanceado (padrão)
# 100 = alto contraste (preto puro vs branco puro)
```

**Valores:**
- **20-35**: Baixo → Códigos em **superfícies reflexivas** (metal)
- **40-60**: Médio → **Ideal** para maioria dos casos
- **60-100**: Alto → Códigos **desbotados** ou em papel reciclado

**Quando aumentar:**
- ✅ Códigos 1D (barras) ficam **cinzas** ao invés de pretas
- ✅ Papel **amarelado** ou **reciclado**
- ❌ Evite em códigos já nítidos (pode criar artefatos)

---

### **🌈 GAMMA**

**O que faz:**
- Ajusta a **curva de luminosidade** (meio-tons)
- Afeta mais as **áreas cinzas** do que preto/branco puro

**Como funciona:**
```python
self.camera.set(cv2.CAP_PROP_GAMMA, valor)
# 50 = escurece meio-tons
# 100 = neutro (padrão)
# 200 = clareia meio-tons
```

**Valores:**
- **50-80**: Baixo → Realça **sombras** (códigos em baixo-relevo)
- **100-120**: Médio → Neutro
- **120-200**: Alto → Realça **detalhes claros**

**Quando ajustar:**
- ✅ Códigos em **superfícies curvas** (cilindros)
- ✅ Iluminação **lateral** (cria sombras)
- ⚠️ Parâmetro **avançado** (use só se outros não funcionarem)

---

### **🔬 FOCO MANUAL** (Só se autofoco desligado)

**O que faz:**
- Ajusta **manualmente** a distância focal da lente

**Como ajustar:**
1. **Desative** o Auto Foco
2. Posicione código na **distância de trabalho**
3. Ajuste slider até código ficar **nítido**
4. **Trave** esse valor

**Dica:** Use um código de TESTE e observe o vídeo ao vivo!

---

## 🖥️ 3. PARÂMETROS DE SOFTWARE (Boost)

Estes ajustam a imagem **DEPOIS** de capturada, por software.

---

### **⚡ BOOST** (Checkbox)

**O que faz:**
- Ativa o ganho digital (alpha/beta)
- Processamento **pós-captura**

**Quando ativar:**
- ✅ Câmera não tem controle de **ganho/brilho/contraste**
- ✅ Já ajustou tudo no hardware mas ainda está ruim
- ⚠️ Aumenta processamento (pode deixar mais lento)

---

### **📈 ALPHA (Ganho/Contraste Digital)**

**O que faz:**
- **Multiplica** os valores de pixel
- `novo_pixel = antigo_pixel × alpha`

**Como funciona:**
```python
cv2.convertScaleAbs(frame, alpha=valor, beta=0)
# 0.5 = escurece 50%
# 1.0 = sem mudança (padrão)
# 2.0 = dobra o brilho
```

**Valores:**
- **0.5-0.9**: Reduz brilho → Códigos em **papel muito branco**
- **1.0**: Neutro
- **1.1-1.5**: Aumenta contraste → Códigos **desbotados**
- **1.5-3.0**: Alto contraste → Último recurso

**Quando usar:**
- ✅ Imagem capturada está muito **pálida**
- ✅ Precisa **aumentar contraste** após captura
- ❌ Pode gerar **ruído** se exagerar

---

### **➕ BETA (Offset de Brilho)**

**O que faz:**
- **Adiciona** um valor fixo a todos os pixels
- `novo_pixel = antigo_pixel + beta`

**Como funciona:**
```python
cv2.convertScaleAbs(frame, alpha=1.0, beta=valor)
# -100 = escurece (remove branco)
# 0 = sem mudança (padrão)
# +100 = clareia (adiciona branco)
```

**Valores:**
- **-100 a -20**: Escurece → Códigos em fundo **muito claro**
- **0**: Neutro
- **+20 a +100**: Clareia → Códigos muito **escuros**

**Quando usar:**
- ✅ Toda imagem está um "tom" muito escura/clara
- ✅ Complementa o ALPHA (use juntos)

---

## 🎨 4. MODOS DE MINIATURA

Controlam **qual versão processada** aparece nas miniaturas.

---

### **🖤 BINARIZADA (Preto e Branco Puro)**

**Pipeline:**
```
Imagem Retificada → Escala de Cinza → Binarização Adaptativa → Morfologia
```

**Resultado:**
- Apenas **preto** (0) e **branco** (255)
- **Melhor** para códigos **1D** (barras)

**Quando ver:**
- ✅ Debugar detecção de **códigos 1D**
- ✅ Ver se binarização está **correta**
- ✅ Identificar **ruído** (pontos pretos indesejados)

---

### **🎨 Enhanced (CLAHE)**

**Pipeline:**
```
Imagem Retificada → CLAHE (equalização adaptativa) → Colorida
```

**Resultado:**
- Imagem **colorida** com contraste melhorado
- **Melhor** para códigos **2D** (QR, DataMatrix)

**Quando ver:**
- ✅ Visualização **natural** do código
- ✅ Debugar problemas de **iluminação**
- ✅ Ver resultado do **CLAHE**

---

### **⚪ Escala de Cinza (Sharpened)**

**Pipeline:**
```
Imagem Retificada → Enhanced → Escala de Cinza → Sharpening
```

**Resultado:**
- 256 tons de cinza **aguçados**
- **Melhor** para ver **detalhes finos**

**Quando ver:**
- ✅ Códigos **pequenos** ou **distantes**
- ✅ Debugar **foco** (se está nítido)
- ✅ Meio-termo entre binarizada e enhanced

---

## 💾 5. SALVAR/CARREGAR CONFIGURAÇÕES

### **💾 SALVAR CONFIG**

**O que faz:**
- Salva **TODOS** os parâmetros atuais em arquivo JSON
- Formato: `modelo1.json`, `modelo2.json`, etc.

**Quando usar:**
- ✅ Encontrou configuração **perfeita** para seu caso
- ✅ Tem **vários tipos** de códigos (crie múltiplos modelos)
- ✅ Quer **compartilhar** config com outro PC

**Conteúdo salvo:**
```json
{
  "auto_exposure": true,
  "exposure": -6,
  "gain": 30,
  "brightness": 128,
  "contrast": 50,
  "gamma": 100,
  "auto_focus": true,
  "focus": 0,
  "boost": false,
  "alpha": 1.2,
  "beta": 10
}
```

---

### **📂 CARREGAR CONFIG**

**O que faz:**
- Carrega o **último** arquivo `modeloX.json` salvo
- Aplica **todos** os parâmetros automaticamente

**Quando usar:**
- ✅ Trocar entre **configurações salvas**
- ✅ Resetar para configuração **conhecida**
- ✅ Importar config de **outro operador**

---

## 🎯 6. GUIA RÁPIDO DE TROUBLESHOOTING

### **❌ Não detecta NADA:**
1. Verificar se câmera está **aberta** (luz LED acesa)
2. Desativar **Modo Rápido**
3. Ativar **Auto Exposição** e **Auto Foco**
4. Aumentar **Contraste** (50-70)
5. Verificar distância (ideal: **10-30cm**)

---

### **❌ Detecta mas "perde" o código:**
1. Desativar **Modo Rápido** (precisa processar mais frames)
2. Aumentar **Contraste** (40-60)
3. Verificar se código está **nítido** (ajustar foco)

---

### **❌ Códigos 1D (barras) não detectam:**
1. Aumentar **Contraste** (60-80) ← **Crítico!**
2. Verificar se barras estão **nítidas** (foco)
3. Desativar **Auto Exposição**, testar exposição manual (-8 a -4)
4. Ver miniatura **Binarizada** (deve ter barras pretas puras)

---

### **❌ Códigos 2D (QR) não detectam:**
1. Ativar **Auto Foco** (essencial para QR)
2. Reduzir **Contraste** (30-40) ← QR é mais tolerante
3. Aumentar **Brilho** se QR estiver muito escuro
4. Ver miniatura **Enhanced** (deve ter boa iluminação)

---

### **❌ Sistema LENTO/TRAVANDO:**
1. Ativar **Modo Rápido** ← Reduz 66% processamento
2. Fechar outros programas
3. Reduzir **Códigos Esperados** (processar menos miniaturas)

---

### **❌ Miniaturas tortas/erradas:**
1. **Já corrigido!** (retificação de perspectiva implementada)
2. Se persistir: verificar se `rectified_binary/gray/enhanced` estão no dict

---

## 📋 7. WORKFLOW RECOMENDADO

### **SETUP INICIAL (1ª vez):**
```
1. Abrir câmera
2. Posicionar código de TESTE (20cm da câmera)
3. Deixar Auto Exposição ✅ e Auto Foco ✅ ATIVOS
4. Ajustar CONTRASTE até detectar bem
5. Salvar Config (modelo1.json)
```

### **USO DIÁRIO:**
```
1. Abrir câmera
2. Carregar Config (modelo1.json)
3. Aguardar 1s (autofoco estabilizar)
4. Iniciar Inspeção
```

### **CÓDIGOS 1D (EAN, CODE128):**
```
Contraste: 60-80 ← Essencial!
Auto Exposição: ✅
Modo Rápido: ❌ (desligado)
Miniatura: Binarizada (para debug)
```

### **CÓDIGOS 2D (QR, DataMatrix):**
```
Contraste: 30-50
Auto Foco: ✅ ← Essencial!
Modo Rápido: ✅ (pode usar)
Miniatura: Enhanced (visualização)
```

