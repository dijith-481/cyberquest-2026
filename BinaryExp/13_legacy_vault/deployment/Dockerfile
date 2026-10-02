FROM debian:trixie-slim

RUN useradd -m bob

RUN apt-get update && apt-get install -y socat patchelf \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /vuln
COPY vuln /vuln/
WORKDIR /vuln

# The shipped binary was built on NixOS and embeds a /nix/store interpreter
# path that does not exist here. Rewrite it to the standard loader; this
# changes only the interpreter string, so code offsets are preserved and the
# documented solve (denied@0x300 / print_flag@0x1e0) still holds.
RUN patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2 /vuln/vault

RUN echo "cyber_quest{l3gacy_v4ult_0v3rwr1t3_8f3a21}" > /vuln/flag.txt

EXPOSE 1338

USER bob

CMD ["bash","/vuln/run.sh"]
