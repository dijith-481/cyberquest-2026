/* dispatcher.c — ordinary engineering :: ledgerd reconciliation mirror
 *
 * Runs the two ledgerd builds (prod + compat) in lockstep for one
 * connection: every line the client sends is executed on both builds and
 * the dispatcher prints the consensus. The reconciliation report opens
 * only when BOTH builds pass the AU-7 audit.
 *
 * usage: dispatcher [dir]     (dir holds ledgerd-prod / ledgerd-compat)
 */
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static pid_t pid_prod, pid_compat;
static FILE *to_prod, *from_prod, *to_compat, *from_compat;

static void die(const char *which)
{
    fprintf(stderr, "mirror fault: %s build exited\n", which);
    exit(1);
}

static void spawn(const char *dir, const char *bin, pid_t *pid, FILE **to,
                  FILE **from)
{
    int in[2], out[2];
    pid_t p;

    if (pipe(in) != 0 || pipe(out) != 0) {
        perror("pipe");
        exit(1);
    }
    p = fork();
    if (p == 0) {
        dup2(in[0], 0);
        dup2(out[1], 1);
        close(in[0]); close(in[1]);
        close(out[0]); close(out[1]);
        if (chdir(dir) != 0) {
            perror("chdir");
            _exit(127);
        }
        execl(bin, bin, (char *)NULL);
        perror("exec");
        _exit(127);
    }
    close(in[0]);
    close(out[1]);
    *to = fdopen(in[1], "w");
    *from = fdopen(out[0], "r");
    if (!*to || !*from) {
        perror("fdopen");
        exit(1);
    }
    *pid = p;
}

static void read_child(FILE *f, char *buf, size_t cap, const char *which)
{
    if (!fgets(buf, (int)cap, f))
        die(which);
    buf[strcspn(buf, "\r\n")] = '\0';
}

static void print_flag(void)
{
    const char *paths[] = { "/opt/ledger/flag.txt", "flag.txt", NULL };
    char flag[160];
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
    printf("flag file not found — ask the organizers\n");
}

int main(int argc, char **argv)
{
    const char *dir = argc > 1 ? argv[1] : ".";
    char line[256], rp[512], rc[512];

    setvbuf(stdout, NULL, _IONBF, 0);

    spawn(dir, "./ledgerd-prod", &pid_prod, &to_prod, &from_prod);
    spawn(dir, "./ledgerd-compat", &pid_compat, &to_compat, &from_compat);

    /* Banner deliberately does NOT name the build optimization levels
     * ("prod (-O3) / compat (-O0)"). That line handed the player the whole
     * premise of the exploit: same source, two builds, different stack
     * frames. The fact that both builds run in lockstep is stated in
     * handout/README.txt instead -- the player should have to work out
     * WHY the two builds disagree. Do not re-add it here. */
    puts("ordinary engineering — ledgerd 2.4.1 (reconciliation mirror)");
    puts("commands: tag <text> | audit | state | layout | quit");
    puts("ready.");

    alarm(600); /* one reconciliation window per connection */

    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = '\0';
        fprintf(to_prod, "%s\n", line);
        fflush(to_prod);
        fprintf(to_compat, "%s\n", line);
        fflush(to_compat);

        read_child(from_prod, rp, sizeof rp, "prod");
        read_child(from_compat, rc, sizeof rc, "compat");

        if (strcmp(line, "audit") == 0 &&
            strcmp(rp, "AUDIT_OK") == 0 && strcmp(rc, "AUDIT_OK") == 0) {
            printf("prod: %s — compat: %s\nreconciliation complete across both builds — ",
                   rp, rc);
            print_flag();
            break;
        }
        printf("prod: %s — compat: %s\n", rp, rc);
    }

    kill(pid_prod, SIGTERM);
    kill(pid_compat, SIGTERM);
    waitpid(pid_prod, NULL, 0);
    waitpid(pid_compat, NULL, 0);
    return 0;
}
