/* Break Glass — BinaryExp slot 16.
 *
 * The release does not keep the flag as plaintext. Two encrypted, position-
 * independent stages are materialized briefly in anonymous executable pages.
 * Their exact runtime outputs form the key that decodes the flag fragment.
 * A normal execution follows both deliberately broken paths and therefore
 * prints a fresh, plausible decoy token.
 */
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include "frag_arrays.h"
#include "stages.h"

typedef uint64_t u64;
typedef void (*stage_a_fn)(u64 *slot);
typedef void (*stage_c_fn)(u64 *state_slot, u64 *status_slot);

#define EXPECTED_A UINT64_C(0x442cb715d93c702d)
#define DONE_STATE UINT64_C(0xff)

struct stage_image {
    void *address;
    size_t mapping_size;
};

static _Noreturn void fail(const char *operation) {
    perror(operation);
    exit(EXIT_FAILURE);
}

static size_t page_round_up(size_t length) {
    long page = sysconf(_SC_PAGESIZE);
    if (page <= 0) {
        fail("sysconf");
    }

    size_t page_size = (size_t)page;
    size_t remainder = length % page_size;
    if (remainder != 0) {
        size_t padding = page_size - remainder;
        if (length > SIZE_MAX - padding) {
            fputs("stage is too large\n", stderr);
            exit(EXIT_FAILURE);
        }
        length += padding;
    }
    return length;
}

static struct stage_image load_stage(const unsigned char *encrypted,
                                     const unsigned char *key,
                                     size_t length) {
    if (length == 0) {
        fputs("empty stage\n", stderr);
        exit(EXIT_FAILURE);
    }

    size_t mapping_size = page_round_up(length);
    void *address = mmap(NULL, mapping_size, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (address == MAP_FAILED) {
        fail("mmap");
    }

    unsigned char *decoded = (unsigned char *)address;
    for (size_t i = 0; i < length; i++) {
        decoded[i] = encrypted[i] ^ key[i];
    }

    if (mprotect(address, mapping_size, PROT_READ | PROT_EXEC) != 0) {
        int saved_errno = errno;
        (void)munmap(address, mapping_size);
        errno = saved_errno;
        fail("mprotect");
    }

    struct stage_image image = {address, mapping_size};
    return image;
}

static void unload_stage(struct stage_image image) {
    if (munmap(image.address, image.mapping_size) != 0) {
        fail("munmap");
    }
}

/* POSIX makes a mapping executable; copy its address into the function
 * pointer representation without asking the compiler for a pedantic object-
 * pointer cast. Linux x86-64 uses the same representation for both. */
static stage_a_fn stage_a_entry(void *address) {
    _Static_assert(sizeof(stage_a_fn) == sizeof(void *),
                   "unexpected function pointer representation");
    stage_a_fn entry;
    memcpy(&entry, &address, sizeof(entry));
    return entry;
}

static stage_c_fn stage_c_entry(void *address) {
    _Static_assert(sizeof(stage_c_fn) == sizeof(void *),
                   "unexpected function pointer representation");
    stage_c_fn entry;
    memcpy(&entry, &address, sizeof(entry));
    return entry;
}

/* MurmurHash3 finalizer-style mixer, used as a tiny keystream generator. */
static u64 mix64(u64 value) {
    value ^= value >> 33;
    value *= UINT64_C(0xff51afd7ed558ccd);
    value ^= value >> 33;
    value *= UINT64_C(0xc4ceb9fe1a85ec53);
    value ^= value >> 33;
    return value;
}

static unsigned char keystream_byte(u64 master_key, size_t index) {
    u64 offset = (u64)index * UINT64_C(0x9E3779B97F4A7C15);
    return (unsigned char)(mix64(master_key + offset) & UINT64_C(0xff));
}

static void print_decoy(void) {
    static const char alphabet[] =
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
    unsigned seed = (unsigned)time(NULL) ^ (unsigned)getpid();
    srand(seed);
    putchar('c');
    fputs("yber_quest{", stdout);
    for (size_t i = 0; i < FRAG_LEN; i++) {
        putchar(alphabet[rand() % (sizeof(alphabet) - 1)]);
    }
    puts("}");
}

int main(void) {
    struct stage_image image_a =
        load_stage(enc_stage_a, key_stage_a, sizeof(enc_stage_a));
    u64 checksum = 0;
    stage_a_entry(image_a.address)(&checksum);
    unload_stage(image_a);

    struct stage_image image_c =
        load_stage(enc_stage_c, key_stage_c, sizeof(enc_stage_c));
    u64 state = UINT64_C(0x11);
    u64 status = 0;
    stage_c_entry(image_c.address)(&state, &status);
    unload_stage(image_c);
    (void)status; /* exact state, not this convenience status, is the gate */

    u64 master_key = checksum ^ (state << 32) ^ GATE_SALT;
    u64 target_key = EXPECTED_A ^ (DONE_STATE << 32) ^ GATE_SALT;

    if (master_key != target_key) {
        print_decoy();
        return EXIT_SUCCESS;
    }

    unsigned char fragment[FRAG_LEN + 1];
    for (size_t i = 0; i < FRAG_LEN; i++) {
        fragment[i] = frag_enc[i] ^ keystream_byte(master_key, i);
    }
    fragment[FRAG_LEN] = '\0';
    printf("cyber_quest{%s}\n", fragment);
    return EXIT_SUCCESS;
}
