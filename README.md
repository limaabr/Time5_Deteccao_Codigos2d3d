#Repositorio para desenvolvimento do desafio 5 - AutoLabel ajust

📋 Sobre o Projeto
Sistema desenvolvido para inspeção automática de produtos utilizando técnicas avançadas de Processamento Digital de Imagens (PDI) e Visão Computacional. Otimizado especialmente para a webcam Pcyes Raza Auto Focus FHD-03 1080P, oferecendo alta precisão na detecção de códigos em diferentes condições de iluminação e distância.
🎯 Aplicações

✅ Controle de qualidade em linhas de produção
✅ Inspeção automática de embalagens
✅ Rastreabilidade de produtos
✅ Automação industrial
✅ Logística e gestão de estoque


✨ Características
🚀 Funcionalidades Principais

Detecção Automática Multi-Formato

Códigos 1D: EAN-13, EAN-8, UPC-A, UPC-E, Code 39, Code 128, ITF, Codabar
Códigos 2D: QR Code, DataMatrix, PDF417, Aztec Code


Pipeline Avançado de PDI

Equalização adaptativa de histograma (CLAHE)
Binarização adaptativa com filtro Gaussiano
Remoção de ruído por operações morfológicas
Boost de software para ambientes de baixa luminosidade


Sistema de Inspeção Inteligente

Configuração de quantidade esperada de códigos (1-8)
Timeout personalizável (1-300 segundos)
Detecção de códigos faltantes ou excedentes
Aprovação/reprovação automática (OK/NG)
Reinício automático de ciclos de inspeção


Interface Gráfica Profissional

Visualização em tempo real com sobreposição de detecções
Histórico completo de códigos detectados
Miniaturas automáticas dos códigos capturados
Painel de controles avançados de câmera
Modo tela cheia (F11)


Otimizações para Pcyes FHD-03

Suporte completo a autofoco automático
Auto exposição otimizada para leitura de códigos
Resolução otimizada (720p para melhor performance)
Codec MJPEG para menor latência
Sharpness (nitidez) alto para melhor detecção
Distância mínima de operação: 10cm



⚙️ Parâmetros Ajustáveis de PDI

Exposição: Controle manual ou automático
Ganho: Amplificação de sinal (0-100)
Brilho: Ajuste de luminosidade (0-255)
Contraste: Diferenciação de tons (0-100)
Gamma: Correção de luminância (0-200)
Foco: Manual ou automático (recomendado)
Boost Software: Ganho digital (Alpha/Beta)

💾 Gerenciamento de Configurações

Salvamento automático em formato JSON sequencial (modelo1.json, modelo2.json, ...)
Carregamento do último modelo salvo
Preservação de todos os parâmetros de PDI
Compartilhamento fácil entre usuários/estações
