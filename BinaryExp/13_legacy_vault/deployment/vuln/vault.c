/* vault.c — ordinary engineering :: vault-svc v1 (legacy)
 *
 * The company safe, but for labels. Store a label, run the callback.
 * Hardened after the audit: PIE, stack protector, no debug leftovers.
 * build: gcc -O2 -fPIE -pie -fstack-protector-strong -o vault vault.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

__attribute__((noinline))
static void denied(void)
{
    puts("access denied — auditors have been notified.");
}

__attribute__((noinline))
static void print_flag(void)
{
    const char *paths[] = { "flag.txt", "/vuln/flag.txt", NULL };
    char flag[192];
    FILE *f;
    int i;

    for (i = 0; paths[i]; i++) {
        f = fopen(paths[i], "r");
        if (!f)
            continue;
        if (fgets(flag, sizeof flag, f) == NULL)
            snprintf(flag, sizeof flag, "flag file unreadable");
        fclose(f);
        flag[strcspn(flag, "\r\n")] = '\0';
        printf("%s\n", flag);
        return;
    }
    puts("flag file not found — ask the organizers");
}

/* Authorized callbacks for the automation tier (not wired to run yet). */
__attribute__((used))
static void (*const callbacks[])(void) = { denied, print_flag };

/* The label lives next to the callback it authorizes. */
struct vault {
    char     buf[64];
    uint64_t epoch;      /* retention epoch, printed by info */
    void   (*on_auth)(void);
};

/* Raw line reader: reads up to '\n', keeps embedded NULs, returns length.
 * One read() per byte so TCP framing never matters. */
static int read_line_raw(unsigned char *buf, int cap, int *out_len)
{
    int n = 0;
    unsigned char c;

    for (;;) {
        ssize_t r = read(0, &c, 1);
        if (r <= 0) {
            if (n == 0)
                return 0;
            break;
        }
        if (c == '\n')
            break;
        if (c == '\r')
            continue;
        if (n < cap)
            buf[n++] = c;
        /* overlong tail is dropped but still consumed until '\n' */
    }
    *out_len = n;
    return 1;
}

static void handle_conn(void)
{
    struct vault v;
    unsigned char line[256];
    int n;

    memset(v.buf, 0, sizeof v.buf);
    v.epoch = 20260906;
    v.on_auth = denied;

    setvbuf(stdout, NULL, _IONBF, 0);

    puts("ordinary engineering — vault-svc v1 (legacy)");
    puts("the company safe, but for labels. store a label, run the callback.");
    puts("commands: store <text> | run | info | quit");
    puts("ready.");

    alarm(300);

    while (read_line_raw(line, (int)sizeof line, &n)) {
        if (n >= 6 && memcmp(line, "store ", 6) == 0) {
            unsigned char *payload = line + 6;
            int plen = n - 6;
            /* legacy fast path: nobody ever stored more than a label */
            memcpy(v.buf, payload, (size_t)plen);
            printf("stored %d bytes.\n", plen);
        } else if (n == 3 && memcmp(line, "run", 3) == 0) {
            v.on_auth();
        } else if (n == 4 && memcmp(line, "info", 4) == 0) {
            /* support diagnostic: vault location, retention epoch */
            printf("build=v1.4.2-h vault=%p epoch=%lu labels_stored=1\n",
                   (void *)&v, (unsigned long)v.epoch);
        } else if (n == 4 && memcmp(line, "quit", 4) == 0) {
            puts("bye");
            break;
        } else {
            puts("unknown command");
        }
    }
}

int main(void)
{
    handle_conn();
    return 0;
}
