# ===============================================================
#                server.py (v22.5 - Final com Análise e CORS)
# ===============================================================
import subprocess
import os
import re
import sys
import json
import logging
import threading
from time import sleep
from flask import Flask, jsonify, request
from waitress import serve
from flask_cors import CORS # 1. IMPORTAÇÃO ADICIONADA PARA SEGURANÇA DE ORIGEM

# --- CONFIGURAÇÃO DE CAMINHOS E LOGS ---
APP_NAME = "pecztusb-api-server"
try:
    PROGRAMDATA_DIR = os.environ.get('ProgramData', 'C:\\ProgramData')
    LOG_DIR = os.path.join(PROGRAMDATA_DIR, APP_NAME)
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, "pecztusb_service.log")
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')
except Exception:
    LOG_FILE = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), f"{APP_NAME}.log")
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

# LÓGICA DE CAMINHO ABSOLUTO E INFALÍVEL
# Determina o diretório do executável (.exe) ou do script (.py)
if getattr(sys, 'frozen', False):
    # Se estiver rodando como um executável compilado (pyinstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como um script .py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos dos arquivos essenciais RELATIVOS ao diretório base
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CLOUDFLARED_EXE = os.path.join(BASE_DIR, "cloudflared.exe")

# O caminho para o FabulaTech permanece o mesmo, pois é uma instalação padrão
FABULA_CMD_EXE = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "FabulaTech", "USB Over Network (Server)", "usbsrvcmd.exe")

# --- GERENCIAMENTO DE ESTADO E FUNÇÕES AUXILIARES ---
cloudflared_proc = None
bound_devices = {}

def log(message):
    logging.info(str(message))

def run_fabula_command(args):
    command = [FABULA_CMD_EXE] + args
    log(f"Executando FabulaTech: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='cp850', errors='ignore')
        log(f"Saída FabulaTech: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        log(f"ERRO FabulaTech: {e}")
        return None

# --- LÓGICA DO SERVIÇO DE TÚNEL ---
def start_cloudflared_tunnel():
    global cloudflared_proc
    while True:
        log("Verificando token e iniciando túnel...")
        try:
            with open(CONFIG_FILE, 'r') as f:
                token = json.load(f).get("cloudflare_token")
            if not token or token == "SEU_TOKEN_CLOUDFLARE_AQUI":
                log("Token inválido. Esperando 60s.")
                sleep(60)
                continue
            
            command = [CLOUDFLARED_EXE, "tunnel", "--no-autoupdate", "run", "--token", token]
            cloudflared_proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log(f"Cloudflare iniciado. PID: {cloudflared_proc.pid}.")
            cloudflared_proc.wait()
            log(f"Cloudflare (PID: {cloudflared_proc.pid}) morreu. Reiniciando em 15s...")
        except Exception as e:
            log(f"ERRO NO LOOP DO TÚNEL: {e}. Reiniciando em 15s...")
        sleep(15)

# --- A API FLASK ---
app = Flask(__name__)
# --- INÍCIO DA SEÇÃO CORS CRÍTICA ---
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
) 
# --- FIM DA SEÇÃO CORS ---

@app.route('/status')
def status():
    is_running = cloudflared_proc is not None and cloudflared_proc.poll() is None
    get_devices_data() 
    return jsonify({
        "cloudflared_process_running": is_running,
        "shared_device_count": len(bound_devices),
        "shared_devices_ids": list(bound_devices.keys())
    })

def get_devices_data():
    """Função auxiliar para obter e analisar (parse) dados dos dispositivos."""
    output = run_fabula_command(['list'])
    if output is None:
        return None
    
    devices = []
    current_shared = set()
    lines = output.strip().split('\n')

    for line in lines[1:]:
        match = re.search(
            r'^\s*(\d+)\s+'           # Grupo 1: devID
            r'([\da-fA-F:]+)\s+'      # Grupo 2: VID:PID:REV
            r'([\d-]+)\s+'            # Grupo 3: Location
            r'(\w+)\s+'               # Grupo 4: Status (Shared/Unshared)
            r'(".*?"|\S+)\s+'         # Grupo 5: Serial
            r'(.*)$',                  # Grupo 6: Device Name (tudo até o final)
            line
        )
        if match:
            dev_id = match.group(1)
            status_text = match.group(4).lower()
            description = match.group(6).strip()
            
            # Padronizando o status para o frontend
            status_map = {
                'shared': 'shared',
                'unshared': 'unshared',
                'connected': 'connected' # Adicione outros mapeamentos se necessário
            }
            # O status 'connected' pode não vir diretamente do comando 'list',
            # mas mantemos a estrutura para consistência com o frontend.
            final_status = status_map.get(status_text, status_text)

            devices.append({"devID": dev_id, "description": description, "status": final_status})
            if 'shared' in status_text:
                current_shared.add(dev_id)
                
    bound_devices.clear()
    bound_devices.update({dev_id: True for dev_id in current_shared})
    return devices

@app.route('/devices')
def get_devices():
    """Endpoint para listar os dispositivos USB."""
    devices = get_devices_data()
    if devices is None:
        return jsonify({"error": "Falha ao listar dispositivos do servidor FabulaTech"}), 500
    return jsonify(devices)

@app.route('/share', methods=['POST'])
def share_device():
    dev_id = request.json.get('devID')
    if not dev_id: return jsonify({"error": "devID é obrigatório"}), 400
    output = run_fabula_command(['share', str(dev_id)])
    if output and "successfully" in output.lower():
        bound_devices[str(dev_id)] = True
        return jsonify({"status": "sucesso"})
    return jsonify({"error": "falha ao compartilhar", "details": output}), 500

@app.route('/unshare', methods=['POST'])
def unshare_device():
    dev_id = request.json.get('devID')
    if not dev_id: return jsonify({"error": "devID é obrigatório"}), 400
    output = run_fabula_command(['unshare', str(dev_id)])
    if output and "successfully" in output.lower():
        bound_devices.pop(str(dev_id), None)
        return jsonify({"status": "sucesso"})
    return jsonify({"error": "falha ao parar", "details": output}), 500

# --- INICIALIZAÇÃO (MODIFICADA) ---
if __name__ == '__main__':
    log(f"--- Serviço {APP_NAME} Iniciado --- Log em: {LOG_FILE}")
    threading.Thread(target=start_cloudflared_tunnel, daemon=True).start()

    # --- LÓGICA PARA LER PORTA DO CONFIG.JSON ---
    DEFAULT_API_PORT = 5001
    api_port = DEFAULT_API_PORT
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
            # Lê a porta, converte para inteiro, e usa o padrão se não encontrar
            api_port = int(config_data.get('api_port', DEFAULT_API_PORT))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError) as e:
        log(f"AVISO: Nao foi possivel ler a porta do config.json ou o valor e invalido. Usando a porta padrao {DEFAULT_API_PORT}. Erro: {e}")
        api_port = DEFAULT_API_PORT

    log(f"Iniciando servidor da API na porta {api_port}...")
    serve(app, host='127.0.0.1', port=api_port)    