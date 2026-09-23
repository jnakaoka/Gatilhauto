# Publicação do Gatilhauto

## Variáveis obrigatórias

Copie os nomes de `.env.example` para o ambiente do serviço. Nunca envie o
ficheiro `.env` nem senhas para o Git.

- Gere uma nova `DJANGO_SECRET_KEY` antes da próxima publicação.
- Use `DJANGO_DEBUG=False` em produção.
- No Gmail, crie uma senha de aplicação exclusiva para o site e guarde-a em
  `EMAIL_HOST_PASSWORD`.

## Atualização

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy
```

Execute a aplicação através de Gunicorn e mantenha o Nginx responsável por
HTTPS, ficheiros estáticos e ficheiros de media.

Exemplo:

```bash
.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

Antes de atualizar a produção, faça backup de `db.sqlite3` e da pasta
`media/`. Depois da publicação, altere as senhas de todos os administradores,
pois o banco já esteve versionado num repositório público.
