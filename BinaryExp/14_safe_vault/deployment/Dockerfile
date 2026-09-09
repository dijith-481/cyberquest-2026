FROM debian:trixie-slim

RUN useradd -m bob

RUN apt-get update && apt-get install -y socat \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /vuln
COPY vuln /vuln/
WORKDIR /vuln
RUN echo "cyber_quest{saf3_vault_unsafe_b0undary_4d2e90}" > /vuln/flag.txt

EXPOSE 1339

USER bob

CMD ["bash","/vuln/run.sh"]
