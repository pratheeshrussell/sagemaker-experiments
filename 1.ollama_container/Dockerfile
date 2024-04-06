FROM ollama/ollama

RUN apt update -y && \
    apt install --no-install-recommends curl wget bash python3.10 python3-pip ca-certificates -y \
    && apt clean && rm -rf /var/lib/apt/lists/*
# python env vars
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ollama is only required locally
ENV OLLAMA_HOST="localhost"
# setup the executable path
ENV PATH="/opt/:${PATH}"

# copy the code and requirements
COPY main.py /opt/
COPY requirements.txt /opt/
COPY run_server.sh /opt/serve

WORKDIR /opt
# install required python stuff
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /opt/serve

EXPOSE 8080

ENTRYPOINT ["/opt/serve"]