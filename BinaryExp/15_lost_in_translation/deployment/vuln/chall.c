#define _GNU_SOURCE
/* chall.c -- build farm intake, internal build 0.9.7
 *
 * All inbound translation units pass through here before they reach the
 * farm. Vendors connect over the internal wire, paste one unit, and
 * intake decides whether it ships. Most units are turned away without
 * explanation. The intake team considers this load-bearing.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <ctype.h>
#include <sys/random.h>

#define KEYLEN   16
#define KEYADD   17

#define TAPELEN  32768
#define MAXUNIT  65536
#define MAXOPS   MAXUNIT
#define MAXSTEPS 5000000L
#define MAXOUT   16384
#define MAXUNITS 8

static const char BANNER[] =
    "\n"
    "== intake 0.9.7 -- build farm intake ==\n"
    "\n"
    "  every translation unit bound for the farm passes through intake.\n"
    "  paste one unit and terminate it with a line that reads __END__\n"
    "\n"
    "  units without a main function are turned away\n"
    "\n";

static const char PROMPT[] = "intake> awaiting translation unit\n";

/* intake reads units the way intake reads units */
static const char *MARKS = "+-<>[].,";

static char  unit[MAXUNIT + 1];
static int   ulen;
static char  clean[MAXUNIT + 1];
static int   clen;
static char  ops[MAXOPS];
static int   nops;
static char  out[MAXOUT];
static int   outlen;

static unsigned char key[KEYLEN];
static unsigned char want[KEYLEN];

/* the flag travels next to the binary, not in the caller's cwd:
   resolve it against /proc/self/exe so any launcher, wrapper, unit
   file, or working directory serves it identically */
static FILE *open_flag(void)
{
    char self[4096], path[4096];
    ssize_t n = readlink("/proc/self/exe", self, sizeof(self) - 1);
    if (n > 0 && n < (ssize_t)sizeof(self)) {
        char *slash;
        size_t dlen;
        self[n] = 0;
        slash = strrchr(self, '/');
        if (slash != NULL) {
            FILE *fp;
            dlen = (size_t)(slash - self);
            if (dlen < sizeof(path) - 10) {
                memcpy(path, self, dlen);
                strcpy(path + dlen, "/flag.txt");
                fp = fopen(path, "r");
                if (fp != NULL)
                    return fp;
            }
        }
    }
    return fopen("flag.txt", "r");   /* legacy: working directory */
}

static void alarm_handler(int sig)
{
    (void)sig;
    printf("intake: unit rejected\n");
    fflush(stdout);
    _exit(0);
}

/* read one unit; returns 0 on __END__, -1 on wire close */
static int read_unit(void)
{
    char line[512];
    int  llen = 0;
    int  c;
    int  done = 0;

    ulen = 0;
    while (!done && (c = getchar()) != EOF) {
        if (c == '\r')
            continue;               /* vendor terminals */
        if (c != '\n') {
            if (llen < (int)sizeof(line) - 1)
                line[llen++] = (char)c;
            continue;
        }
        line[llen] = 0;
        if (strcmp(line, "__END__") == 0) {
            done = 1;
            break;
        }
        if (ulen + llen <= MAXUNIT) {
            memcpy(unit + ulen, line, (size_t)llen);
            ulen += llen;
        }
        llen = 0;
        if (ulen < MAXUNIT)
            unit[ulen++] = '\n';
    }
    unit[ulen] = 0;
    return 0;
}

/* comments and quoted text are not code: strip them before intake
   reads anything. unterminated anything strips to end of unit --
   garbage in, nothing out */
static void strip(void)
{
    int i = 0, o = 0;

    clen = 0;
    while (i < ulen) {
        char c = unit[i];
        if (c == '/' && i + 1 < ulen && unit[i + 1] == '*') {
            i += 2;
            while (i + 1 < ulen && !(unit[i] == '*' && unit[i + 1] == '/'))
                i++;
            i += 2;
            if (i > ulen)
                i = ulen;
            continue;
        }
        if (c == '/' && i + 1 < ulen && unit[i + 1] == '/') {
            while (i < ulen && unit[i] != '\n')
                i++;
            continue;
        }
        if (c == '"' || c == '\'') {
            char q = c;
            i++;
            while (i < ulen && unit[i] != q) {
                if (unit[i] == '\\' && i + 1 < ulen)
                    i += 2;
                else
                    i++;
            }
            if (i < ulen)
                i++;
            continue;
        }
        clean[o++] = c;
        i++;
    }
    clean[o] = 0;
    clen = o;
}

/* no directives, period: # outside strings/comments can only start
   one, and directive-free code is the whole game here */
static int nodirectives(void)
{
    int i;
    for (i = 0; i < clen; i++) {
        if (clean[i] == '#')
            return 0;
    }
    return 1;
}

/* every kept mark must touch real code: at least one side of it
   (skipping whitespace) is a word character. ++ and -- glue first,
   the way the compiler munches them, so i++ reads as one unit while
   bare +++ soup falls apart */
static int bound_ok(void)
{
    static int pair_at[MAXUNIT + 1];
    int i, j;

    for (i = 0; i < clen; i++)
        pair_at[i] = 0;
    i = 0;
    while (i + 1 < clen) {
        if ((clean[i] == '+' || clean[i] == '-') && clean[i + 1] == clean[i]) {
            pair_at[i] = 1;
            i += 2;
        } else {
            i++;
        }
    }
    for (i = 0; i < clen; i++) {
        unsigned char c = (unsigned char)clean[i];
        int l, r;
        if (!strchr(MARKS, (char)c))
            continue;
        if ((c == '+' || c == '-') && i > 0 && pair_at[i - 1])
            continue;               /* judged with its partner */
        if (pair_at[i])
            j = i + 1;              /* check outer sides of the pair */
        else
            j = i;
        l = i - 1;
        while (l >= 0 && isspace((unsigned char)clean[l]))
            l--;
        r = j + 1;
        while (r < clen && isspace((unsigned char)clean[r]))
            r++;
        if (!((l >= 0 && (isalnum((unsigned char)clean[l]) || clean[l] == '_')) ||
              (r < clen && (isalnum((unsigned char)clean[r]) || clean[r] == '_'))))
            return 0;
    }
    return 1;
}


/* keep what intake keeps; returns 0 or -1 */
static int extract(void)
{
    int  p;
    int  depth = 0;

    nops = 0;
    for (p = 0; p < clen; p++) {
        char c = clean[p];
        if (!strchr(MARKS, c))
            continue;
        if (nops >= MAXOPS)
            break;
        if (c == '[')
            depth++;
        else if (c == ']') {
            depth--;
            if (depth < 0)
                return -1;
        }
        ops[nops++] = c;
    }
    if (depth != 0)
        return -1;
    return 0;
}

static int run(void)
{
    static unsigned char store[TAPELEN];
    long pc = 0, steps = 0;
    int  head = 0, o = 0;

    memset(store, 0, sizeof(store));
    memcpy(store, key, sizeof(key));

    outlen = 0;
    while (pc < nops) {
        if (++steps > MAXSTEPS)
            return -1;
        switch (ops[pc]) {
        case '+': store[head] = (unsigned char)(store[head] + 1); break;
        case '-': store[head] = (unsigned char)(store[head] - 1); break;
        case '>': head = (head + 1) % TAPELEN;                  break;
        case '<': head = (head + TAPELEN - 1) % TAPELEN;        break;
        case '.':
            if (o < MAXOUT)
                out[o++] = (char)store[head];
            break;
        case ',': store[head] = 0;   break;
        case '[': if (!store[head]) { long d = 1;
                    while (d && pc < nops - 1) { pc++;
                        if (ops[pc] == '[') d++;
                        else if (ops[pc] == ']') d--; } }
                  break;
        case ']': if (store[head])  { long d = 1;
                    while (d && pc > 0) { pc--;
                        if (ops[pc] == ']') d++;
                        else if (ops[pc] == '[') d--; } }
                  break;
        }
        pc++;
    }
    outlen = o;
    return 0;
}

static void reject(void)
{
    printf("intake: unit rejected\n");
}

int main(void)
{
    int served = 0;
    int i;

    setbuf(stdout, NULL);
    signal(SIGALRM, alarm_handler);
    alarm(240);

    /* a fresh stamp for every connection */
    if (getrandom(key, sizeof(key), 0) != (ssize_t)sizeof(key)) {
        srand((unsigned)(time(0) ^ (unsigned long)getpid()));
        for (i = 0; i < KEYLEN; i++)
            key[i] = (unsigned char)(rand() & 0xFF);
    }
    for (i = 0; i < KEYLEN; i++)
        key[i] = (unsigned char)(1 + key[i] % 255);   /* never blank */
    want[0] = (unsigned char)(key[0] + KEYADD);
    for (i = 1; i < KEYLEN; i++)                      /* chained: every
        byte carries the previous answer forward */
        want[i] = (unsigned char)(key[i] + KEYADD + want[i - 1]);

    fputs(BANNER, stdout);

    while (served < MAXUNITS) {
        fputs(PROMPT, stdout);
        if (read_unit() != 0)
            break;
        if (ulen == 0)
            break;

        served++;
        if (!strstr(unit, "int main")) {
            printf("intake: unit rejected -- no main function found\n");
            continue;
        }
        strip();
        if (!nodirectives() || !bound_ok() || extract() != 0 || nops == 0) {
            reject();
            continue;
        }
        if (run() != 0) {
            reject();
            continue;
        }

        if (outlen == KEYLEN && memcmp(out, want, KEYLEN) == 0) {
            FILE *fp;
            printf("unit accepted\n");
            fp = open_flag();
            if (fp != NULL) {
                char line[256];
                while (fgets(line, sizeof(line), fp) != NULL)
                    printf("%s", line);
                fclose(fp);
            } else {
                /* deployer-visible only: socat wires child stderr to
                   the server log, never to the player socket */
                fprintf(stderr, "intake: unit accepted but flag.txt "
                        "missing from working directory\n");
            }
            break;
        }
        reject();
    }

    fputs("intake: closing -- file units in triplicate\n", stdout);
    return 0;
}
