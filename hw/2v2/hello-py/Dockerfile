FROM python:3.10

EXPOSE 8000
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .

ENTRYPOINT ["python", "app.py"]
