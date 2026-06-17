FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py backup.py ./
COPY templates/ templates/
RUN mkdir -p instance
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
RUN useradd -r -u 1000 app \
    && touch /flag && chown app:app /flag \
    && chown -R app /app
USER app
EXPOSE 5000
CMD ["/app/entrypoint.sh"]
