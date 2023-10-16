FROM python:3.11-slim
EXPOSE 3000

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        make \
        gcc 
RUN mkdir /code /data
COPY requirements.txt /code/
RUN pip install --no-cache-dir --compile -r /code/requirements.txt \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY *.py /code/
COPY run_app.sh /code/run_app.sh
WORKDIR /code
CMD ./run_app.sh
