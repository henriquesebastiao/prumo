# Instalação e atualização (self-host)

O Prumo roda em três containers: PostgreSQL (`db`), a API (`api`) e a web com nginx (`web`), que é o único a publicar uma porta. As imagens da API e da web são publicadas no GitHub Container Registry a cada versão (D37).

## Requisitos

- Um servidor Linux com Docker Engine 24+ e o plugin Compose (amd64 ou arm64).
- Um proxy reverso com HTTPS (Caddy, Traefik, nginx…) se o Prumo for acessado fora de `localhost`. O cookie de sessão da web só trafega por HTTPS (veja [Cookie seguro](#cookie-seguro)).
- Cerca de 1 GB de RAM livre e espaço para o banco, as capas e os backups.

## Instalação

1. Crie uma pasta e baixe os arquivos de uma versão (troque `0.1.0` pela versão desejada):

   ```bash
   mkdir prumo && cd prumo
   base=https://raw.githubusercontent.com/henriquesebastiao/prumo/0.1.0
   curl -fsSLO "$base/docker-compose.yml"
   curl -fsSL "$base/.env.example" -o .env
   mkdir deploy && curl -fsSL "$base/deploy/backup.sh" -o deploy/backup.sh \
     && curl -fsSL "$base/deploy/restore.sh" -o deploy/restore.sh && chmod +x deploy/*.sh
   ```

   Se preferir, clone o repositório na tag (`git clone --branch 0.1.0 …`): o resultado é o mesmo.

2. Edite o `.env`:
   - `POSTGRES_PASSWORD`: uma senha forte, só com letras, números, `-` e `_` (ela entra na URL de conexão da API).
   - `PRUMO_VERSION`: a versão das imagens. Fixe a versão (`0.1.0`) para atualizar só quando quiser; `latest` acompanha a última versão.
   - `PRUMO_PORT`: a porta da web no servidor (padrão `8080`).
   - `PRUMO_DEFAULT_TIMEZONE`, `PRUMO_DEFAULT_LOCALE` e `PRUMO_DEFAULT_CURRENCY`: os padrões dos usuários novos (cada pessoa pode mudar o fuso nas Configurações).
   - `PRUMO_COOKIE_SECURE`: mantenha `true` atrás de HTTPS.

3. Suba o Prumo e crie o primeiro usuário (não existe cadastro público):

   ```bash
   docker compose up -d
   docker compose exec api prumo users create --admin
   ```

   A API aplica as migrations sozinha a cada início. Acompanhe com `docker compose logs -f api`.

4. Aponte o proxy reverso para `http://<servidor>:<PRUMO_PORT>`. Exemplo com Caddy:

   ```
   prumo.exemplo.com {
       reverse_proxy 127.0.0.1:8080
   }
   ```

Pronto: acesse `https://prumo.exemplo.com`. A documentação interativa da API fica em `/api/docs`.

### Cookie seguro

Com `PRUMO_COOKIE_SECURE=true` (o padrão), o navegador só envia o cookie de sessão por HTTPS, então o login pela web não funciona por `http://` (exceto em `localhost`). Numa rede de confiança e sem proxy, dá para usar `PRUMO_COOKIE_SECURE=false`. O app Android usa token e não depende do cookie.

## Usuários

```bash
docker compose exec api prumo users create          # pergunta usuário, nome e senha
docker compose exec api prumo users create --admin  # administrador
docker compose exec api prumo users set-password     # redefine a senha de alguém
```

Cada pessoa troca a própria senha e encerra sessões em Configurações. Os dados de cada usuário são separados.

## Backup e restauração

```bash
deploy/backup.sh
```

Grava em `backups/` o dump do banco (`prumo-AAAAMMDD-HHMM.sql.gz`) e as capas (`…-uploads.tar.gz`). Agende o script (por exemplo, com cron, uma vez por dia) e copie a pasta `backups/` para fora do servidor.

```bash
deploy/restore.sh backups/prumo-20261117-1430.sql.gz
```

Para a API, substitui o banco (e as capas, se o `.tar.gz` correspondente estiver ao lado) e religa a API. Pede confirmação; `PRUMO_RESTORE_CONFIRM=yes` dispensa.

Cada pessoa também pode baixar os próprios dados em Configurações › Seus dados (JSON, CSV e capas).

## Atualização

1. Faça um backup (`deploy/backup.sh`).
2. Leia as notas da versão nova.
3. Ajuste `PRUMO_VERSION` no `.env` (ou mantenha `latest`) e, se a versão trouxer mudanças no `docker-compose.yml` ou no `.env.example`, baixe os arquivos novos como na instalação.
4. Atualize:

   ```bash
   docker compose pull
   docker compose up -d
   ```

   A API aplica as migrations da versão nova ao iniciar. Imagens antigas podem ser removidas com `docker image prune`.

Para voltar a uma versão anterior, restaure o backup feito antes da atualização e fixe a `PRUMO_VERSION` antiga: migrations não são desfeitas automaticamente.

## Construir as imagens a partir do código

Sem usar o GHCR, a partir de um clone do repositório:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

## Publicar uma versão (mantenedores)

1. Atualize a versão em `backend/pyproject.toml` e `frontend/package.json`, e as notas da versão.
2. Crie e envie uma tag sem prefixo: `git tag 0.1.0 && git push origin 0.1.0`.
3. O workflow `release.yml` publica `ghcr.io/henriquesebastiao/prumo-api` e `prumo-web` com as tags `0.1.0`, `0.1` e `latest`, para amd64 e arm64. Na primeira publicação, torne os pacotes públicos nas configurações do GitHub.
