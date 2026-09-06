FROM debian:trixie-slim

RUN useradd -m bob

RUN apt-get update && apt-get install -y socat \
    && apt clean && rm -rf /var/lib/apt/lists/*
    
RUN mkdir /vuln
COPY vuln /vuln/
WORKDIR /vuln
RUN echo "cyber_quest{1gn0r3d_ch4r5_4r3_n0t_c0mm3nt5_5f3a20}" > /vuln/flag.txt

EXPOSE 1340

USER bob

CMD ["bash","/vuln/run.sh"]
