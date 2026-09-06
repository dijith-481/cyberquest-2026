/* valuesd — culture artifacts service (the crashed "culture app")
 *
 * Compile-only source kept in deployment/ for provenance. The handout is
 * the heap dump the binary writes at startup; the binary itself is NOT
 * shipped. The flag never exists as a contiguous string in memory — it is
 * ledger bytes, one per record, in sequence order.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>

#define FLAG "cyber_quest{v4lu3s_4rr1v3_0ut_0f_0rd3r_k33p_th3_s3q_b3f19}"

struct rec {                 /* the values ledger record, 16 bytes */
    char tag[4];             /* "LEDJ" live, "AUDT" audited */
    char pad0[4];
    uint32_t seq;            /* big-endian on disk; this is a memory dump */
    char value;              /* the value byte */
    char pad1[3];
};

static void put(char **arena, size_t *at, const char *s) {
    size_t n = strlen(s) + 1;
    memcpy(*arena + *at, s, n);
    *at += n;
}

int main(void) {
    /* everything the service "was thinking about" lives on the heap */
    char *arena = calloc(1, 16384);
    size_t at = 0;

    put(&arena, &at, "valuesd v0.4.1 — culture artifacts service");
    put(&arena, &at, "status: crashed during the quarterly values sync (job 8841)");
    put(&arena, &at,
        "crash report: the values ledger is an array of 16-byte records. "
        "bytes 0-3: record tag (LEDJ = live record, AUDT = audited/retired). "
        "bytes 8-11: sequence number (uint32, this is a memory dump so it is "
        "little-endian here). byte 12: the value byte. everything else is "
        "padding and always has been. records are stored in wall-clock order, "
        "which is not sequence order, because the writer did not believe in "
        "sorting things it did not write.");
    put(&arena, &at,
        "note (job 8841): the audit job writes the flag into the ledger one "
        "byte per LEDJ record, in sequence order, starting at 1. the ledger "
        "holds no flag string anywhere. this is by design and, mostly, by "
        "accident. AUDT records are retired values and are not part of any "
        "current message; LEDJ records with a sequence above 100 are writer "
        "scratches and also not part of it.");
    put(&arena, &at, "quarterly values deck (final, for the all-hands):");
    put(&arena, &at, "  1. pragmatic optimism, but only on Thursdays");
    put(&arena, &at, "  2. printer empathy (unofficial, load-bearing)");
    put(&arena, &at, "  3. the ledger does not lie, it merely misplaces");
    put(&arena, &at, "  4. every ticket has a home. some homes are haunted.");
    put(&arena, &at, "  5. ship it, unless it is the ledger, in which case still ship it");
    put(&arena, &at, "  6. kevin's desk plant is fake. this is not a value. leave it in.");
    put(&arena, &at, "  7. sequence numbers are a suggestion (DISPUTED, see job 8841)");

    /* the ledger itself: scratches + message + audited records */
    const char *FLAG_S = FLAG;
    size_t flen = strlen(FLAG_S);
    int nrec = 10 + (int)flen + 12;
    struct rec *ledger = calloc(nrec, sizeof(struct rec));

    int r = 0;
    /* writer scratches: live tag, junk values, sequence far out of range */
    for (int i = 0; i < 10; i++, r++) {
        memcpy(ledger[r].tag, "LEDJ", 4);
        ledger[r].seq = 900 + i * 7;
        ledger[r].value = "?!##..,,;;"[(i * 3) % 10];
    }
    /* the real message: LEDJ records, seq 1..len, one byte each */
    for (size_t i = 0; i < flen; i++, r++) {
        memcpy(ledger[r].tag, "LEDJ", 4);
        ledger[r].seq = (uint32_t)(i + 1);
        ledger[r].value = FLAG_S[i];
    }
    /* retired/audited records: plausible values, not part of the message */
    const char *AUDJ = "trust,honesty,printer,silence,toner,desk,audit,memo,";
    for (int i = 0; r < nrec; i++, r++) {
        memcpy(ledger[r].tag, "AUDT", 4);
        ledger[r].seq = 200 + i;
        ledger[r].value = AUDJ[i % (sizeof(AUDJ) - 1)];
    }

    /* wall-clock shuffle: reverse pairs so sequence order != memory order */
    for (int i = 0; i + 1 < nrec; i += 2) {
        struct rec t = ledger[i];
        ledger[i] = ledger[i + 1];
        ledger[i + 1] = t;
    }

    /* copy the ledger into the arena too so the dump holds one story */
    memcpy(arena + at, ledger, nrec * sizeof(struct rec));
    at += nrec * sizeof(struct rec);

    /* self-dump the heap: find [heap] in our own maps, read it back.
     * maps is read with raw syscalls into a STACK buffer on purpose —
     * a stdio buffer would be malloc'd, and the dump would end up
     * containing our own /proc/self/maps (and with it, the binary's
     * build path). */
    int mfd = open("/proc/self/maps", O_RDONLY);
    if (mfd < 0) { perror("open maps"); return 1; }
    char mbuf[16384];
    ssize_t mlen = read(mfd, mbuf, sizeof(mbuf) - 1);
    close(mfd);
    if (mlen <= 0) { fprintf(stderr, "read maps\n"); return 1; }
    mbuf[mlen] = '\0';

    unsigned long lo = 0, hi = 0;
    for (char *p = mbuf; (p = strstr(p, "[heap]")); p++) {
        char *ls = p;
        while (ls > mbuf && ls[-1] != '\n') ls--;
        sscanf(ls, "%lx-%lx", &lo, &hi);
        break;
    }
    if (!lo) { fprintf(stderr, "no [heap] mapping\n"); return 1; }

    FILE *out = fopen("valuesd_heap.raw", "wb");
    FILE *mem = fopen("/proc/self/mem", "rb");
    fseek(mem, lo, SEEK_SET);
    char *buf = malloc(hi - lo);
    if (fread(buf, 1, hi - lo, mem) != hi - lo) {
        fprintf(stderr, "short read of own heap\n");
        return 1;
    }
    fwrite(buf, 1, hi - lo, out);
    fclose(mem);
    fclose(out);
    fprintf(stderr, "dumped %lu bytes of heap to valuesd_heap.raw\n",
            (unsigned long)(hi - lo));
    return 0;
}
