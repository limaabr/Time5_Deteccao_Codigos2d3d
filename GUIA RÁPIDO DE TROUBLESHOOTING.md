## 🎯 GUIA RÁPIDO DE TROUBLESHOOTING

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
