# WebApp com Tunnel Cloudflare

Este projeto utiliza Docker e Cloudflare Tunnel para expor sua aplicação web de forma segura, sem necessidade de redirecionamento de portas no firewall.

## Pré-requisitos

- Docker e Docker Compose instalados
- Conta na [Cloudflare](https://dash.cloudflare.com/)
- Token de tunnel da Cloudflare

## Configuração

1. **Renomeie o arquivo `.env.example` para `.env`:**

```bash
mv .env.example .env
````

2. **Adicione seu token da Cloudflare no arquivo `.env`:**

```env
TUNNEL_TOKEN=seu_token_aqui
```

---

## Build da Aplicação

```bash
docker build -t webapp .
```

---

## Inicialização dos Contêineres

Para subir os contêineres no modo interativo (logs no terminal):

```bash
docker compose up
```

Para rodar os contêineres em segundo plano (modo daemon):

```bash
docker compose up -d
```

---
## Cloudflare

A configuração para o Cloudflare Tunnel funcionar com contêiner precisa ser fornecido o nome do serviço informado no docker-compose.yml:

```proxy_service
http://web:80
```

## Acesso

Após iniciar os contêineres, a aplicação estará disponível por meio do link gerado pelo Cloudflare Tunnel. Consulte os logs do container `cloudflared` para obter a URL pública:

```bash
docker logs -f cloudflared_tunnel
```