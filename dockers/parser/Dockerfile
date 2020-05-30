FROM python:3
WORKDIR /usr/src/app
COPY ../requirements.txt ./
COPY ../MindReader/parsers ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python" , "-m", "run-parser"]