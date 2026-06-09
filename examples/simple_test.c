#include <stdio.h>
#include <string.h>

void safe_print(char *input) {
    printf("%s\n", input);
}

void demo_copy(char *input) {
    char buffer[64];
    strcpy(buffer, input);
    puts(buffer);
}

int main(int argc, char **argv) {
    if (argc > 1) {
        safe_print(argv[1]);
        demo_copy(argv[1]);
    }

    return 0;
}
