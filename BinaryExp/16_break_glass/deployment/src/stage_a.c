/* Break Glass — runtime stage A.
 *
 * This file is compiled as position-independent machine code and copied
 * from .text into an anonymous executable mapping. It deliberately computes
 * a value seven below the loader's expected checksum.
 *
 * Contract: rdi points at one uint64_t checksum slot.
 */
typedef unsigned long u64;

#define BARRIER(x) __asm__ volatile("" : "+r"(x) : : "memory")

__attribute__((noinline, used, section(".text")))
void stage_a(u64 *slot) {
    u64 value = 0x9E3779B97F4A7C15UL;
    BARRIER(value);
    value ^= 0x1234567890ABCDEFUL;
    BARRIER(value);
    value = (value << 13) | (value >> (64 - 13));
    BARRIER(value);
    value += 0xDEADBEEFCAFEBABEUL;
    BARRIER(value);
    value ^= (value >> 7);
    BARRIER(value);
    *slot = value;
}
