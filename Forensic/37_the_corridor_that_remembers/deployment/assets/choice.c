#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *clue  = "look_under_the_floor";
    const char *truth = "The answer was never north or south.";

    if (argc > 1 && strcmp(argv[1], "--remember") == 0)
        puts(clue);
    else if (argc > 1 && strcmp(argv[1], "--north") == 0)
        puts(truth);
    else
        puts("You chose too quickly.");

    return 0;
}
