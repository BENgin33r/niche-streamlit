FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && apt-get clean

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY main.py ./

EXPOSE 8501

RUN rm -rf ~/.cache/pip

CMD ["streamlit", "run", "main.py"]