# Macintel Monitor 🎥

O **Macintel Monitor** é um visualizador leve, eficiente e multiplataforma de streams de vídeo RTSP (câmeras IP e DVRs), desenvolvido em **Python** e **PySide6 (Qt)**, integrado ao motor do **VLC (libVLC)** para decodificação acelerada por hardware (GPU).

Ele foi projetado especificamente para rodar continuamente (24/7) em portarias e centrais de monitoramento de condomínios, evitando travamentos e o lag acumulado comuns em softwares tradicionais como o Intelbras SIM Plus/SIM Next.

---

## ✨ Principais Recursos

- **Grade Dinâmica**: Escolha layouts de visualização rápida em grades de **2x2, 3x3, 4x4** e até **8x8 (visualização simultânea de 64 câmeras)**.
- **Menu Hamburger (☰)**: Oculte ou exiba a barra lateral de condomínios para otimizar e maximizar o espaço de tela para o mosaico de câmeras.
- **Zoom em Tela Cheia**: Clique duplo em qualquer câmera para ampliá-la instantaneamente. O clique duplo na tela cheia retorna ao mosaico.
- **Otimização de Recursos (Sub-Stream)**: O mosaico carrega apenas o fluxo secundário das câmeras (menor resolução/bitrate), economizando até 90% de uso de CPU e rede. O fluxo principal (alta resolução) é carregado somente ao abrir a câmera em tela cheia.
- **Gerenciador de Dispositivos Integrado**: Cadastre e gerencie condomínios, DVRs e canais de câmeras diretamente pela interface gráfica, sem precisar editar arquivos de configuração manualmente.
- **Reconexão Automática**: Sistema inteligente de buffering e reconexão automática caso o stream RTSP caia.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3
- **Interface Gráfica (GUI)**: PySide6 (Qt para Python)
- **Motor de Vídeo**: python-vlc (libVLC nativa)
- **Descoberta**: ONVIF (onvif-zeep)

---

## ⚙️ Instalação e Execução

### Pré-requisitos
1. **Python 3.10 ou superior** instalado.
2. **VLC Media Player** instalado no sistema operacional (necessário para fornecer as DLLs do libVLC para aceleração física por hardware).

### Passo a Passo

1. Clone o repositório ou navegue até a pasta do projeto:
   ```bash
   cd macintel-monitor
   ```

2. Crie e ative o ambiente virtual:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Inicie o aplicativo:
   ```bash
   python main.py
   ```
