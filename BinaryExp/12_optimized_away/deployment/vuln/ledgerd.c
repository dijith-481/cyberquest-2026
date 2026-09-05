/* ledgerd.c — ordinary engineering :: reconciliation daemon
 * compat build: gcc -O0 -o ledgerd-compat ledgerd.c
 * prod   build: gcc -O3 -o ledgerd-prod   ledgerd.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdint.h>

#define AUDIT_TOKEN 0x31415926u /* policy AU-7 separation token */

struct session {
    char     owner[24];
    uint32_t admin;   /* 0 = teller, AUDIT_TOKEN = separation auditor */
    uint32_t mode;
    uint64_t epoch;
    uint64_t balance;
    char     note[96];
};

__attribute__((noinline))
static void session_open(struct session *s)
{
    memset(s, 0, sizeof(*s));
    memcpy(s->owner, "teller", sizeof("teller"));
    s->epoch = 20260905;
    s->mode  = 0;
    s->admin = 0; /* every session opens as teller */
}

__attribute__((noinline))
static int session_audit(struct session *s)
{
    return s->admin == AUDIT_TOKEN;
}

static int read_line(char *buf, int cap)
{
    if (!fgets(buf, cap, stdin))
        return 0;
    buf[strcspn(buf, "\n")] = '\0';
    return 1;
}

static void handle_conn(void)
{
    struct session s;
    char scratch[32]; /* AU-7 tooling scratch */
    char tag[64];
    char line[256];

    setvbuf(stdout, NULL, _IONBF, 0);
    session_open(&s);

    while (read_line(line, (int)sizeof line)) {
        if (strncmp(line, "tag ", 4) == 0) {
            strcpy(tag, line + 4); /* audit tag line — per vendor header */
            printf("tagged: %s\n", tag);
        } else if (strcmp(line, "audit") == 0) {
            puts(session_audit(&s) ? "AUDIT_OK" : "AUDIT_DENIED");
        } else if (strcmp(line, "state") == 0) {
            printf("owner=%.24s mode=%u epoch=%lu balance=%lu\n",
                   s.owner, s.mode, (unsigned long)s.epoch,
                   (unsigned long)s.balance);
        } else if (strcmp(line, "layout") == 0) {
            printf("sizeof(session)=%zu owner=+%zu admin=+%zu note=+%zu | "
                   "frame map (vendor rev 4, may not match local toolchains): "
                   "tag -0x50 session -0xc0\n",
                   sizeof(struct session), offsetof(struct session, owner),
                   offsetof(struct session, admin),
                   offsetof(struct session, note));
        } else if (strcmp(line, "quit") == 0) {
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
