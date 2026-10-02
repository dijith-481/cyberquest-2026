# Optimized Away — deployment image (slot 12)
# One nc port; the dispatcher runs both frozen builds in lockstep.
# Mirrors the 2025 BinaryExp shape: debian-slim + socat, non-root user.
FROM debian:trixie-slim

RUN useradd -m bob

RUN apt-get update && apt-get install -y socat \
    && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /vuln
COPY vuln /vuln/
COPY flag.txt /vuln/flag.txt
WORKDIR /vuln

EXPOSE 1337

USER bob

# dispatcher takes the directory holding both builds as its argument
CMD ["socat","TCP-LISTEN:1337,reuseaddr,fork","EXEC:/vuln/dispatcher /vuln"]
