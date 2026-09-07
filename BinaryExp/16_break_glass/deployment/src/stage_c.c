/* Break Glass — runtime stage B.
 *
 * Contract: rdi points at a uint64_t state slot initialized to 0x11 and rsi
 * points at a uint64_t status slot. The intended path is 0x11 -> 0x59 ->
 * 0x7d -> 0xff. The shipped stage contains one wrong edge, so a live patch
 * is required before the dead-end state is consumed.
 */
typedef unsigned long u64;

#define BARRIER(x) __asm__ volatile("" : "+r"(x) : : "memory")

__attribute__((noinline, used, section(".text")))
void stage_c(u64 *state_slot, u64 *status_slot) {
    u64 state = *state_slot;
    u64 iterations = 0;

    while (iterations < 64) {
        BARRIER(state);
        switch (state) {
            case 0x11:
                state = 0x59;
                break;
            case 0x59:
                state = 0x7e; /* live-debug target: change to 0x7d */
                break;
            case 0x7d:
                state = 0xff;
                break;
            case 0x7e:
                *status_slot = 0;
                return;
            default:
                *status_slot = 0;
                return;
        }
        BARRIER(state);
        *state_slot = state;
        if (state == 0xff) {
            *status_slot = 1;
            return;
        }
        iterations++;
    }
    *status_slot = 0;
}
