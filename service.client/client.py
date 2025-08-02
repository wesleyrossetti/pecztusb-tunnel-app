# client.py (v4 - Final Alinhado com a API FabulaTech)
import requests
import argparse
import json
import sys

def do_request(method, url, data=None):
    try:
        if method.lower() == 'get':
            response = requests.get(url, timeout=15)
        else:
            response = requests.post(url, json=data, timeout=15)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\nERRO: Falha na comunicação com o servidor: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Cliente de controle remoto para o pecztusb-api.")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Comandos disponíveis')

    parser_status = subparsers.add_parser('status', help='Verifica o status do servidor.')
    parser_status.add_argument("--url", required=True, help="URL da API do servidor (ex: https://api.pecsolucoes.com).")

    parser_devices = subparsers.add_parser('devices', help='Lista os dispositivos USB no servidor.')
    parser_devices.add_argument("--url", required=True, help="URL da API do servidor.")

    parser_share = subparsers.add_parser('share', help='Compartilha um dispositivo USB.')
    parser_share.add_argument("--url", required=True, help="URL da API do servidor.")
    # # <<< CORREÇÃO: Pede 'devID' em vez de 'id' >>>
    parser_share.add_argument("--devID", required=True, help="O 'devID' numérico do dispositivo a ser compartilhado (obtido com o comando 'devices').")

    parser_unshare = subparsers.add_parser('unshare', help='Para o compartilhamento de um dispositivo USB.')
    parser_unshare.add_argument("--url", required=True, help="URL da API do servidor.")
    # # <<< CORREÇÃO: Pede 'devID' em vez de 'id' >>>
    parser_unshare.add_argument("--devID", required=True, help="O 'devID' numérico do dispositivo a ser parado.")

    args = parser.parse_args()

    # Monta a URL base da API
    api_base_url = args.url.rstrip('/')

    if args.command == 'status':
        response_data = do_request('get', f"{api_base_url}/status")
    elif args.command == 'devices':
        response_data = do_request('get', f"{api_base_url}/devices")
    elif args.command == 'share':
        # # <<< CORREÇÃO: Envia o JSON com a chave 'devID' >>>
        response_data = do_request('post', f"{api_base_url}/share", data={'devID': args.devID})
    elif args.command == 'unshare':
        # # <<< CORREÇÃO: Envia o JSON com a chave 'devID' >>>
        response_data = do_request('post', f"{api_base_url}/unshare", data={'devID': args.devID})
    
    print(json.dumps(response_data, indent=2))

if __name__ == "__main__":
    main()