FROM debian:trixie-slim

RUN useradd -m bob

RUN apt-get update && apt-get install -y socat \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /vuln
COPY vuln /vuln/
WORKDIR /vuln
RUN echo "cyber_quest{l3gacy_v4ult_0v3rwr1t3_8f3a21}" > /vuln/flag.txt

EXPOSE 1338

USER bob

CMD ["bash","/vuln/run.sh"]
