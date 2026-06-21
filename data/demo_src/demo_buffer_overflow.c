#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char buffer[16];

    if (argc < 2) {
        puts("Usage: demo_buffer_overflow <input>");
        return 1;
    }

    /* Intentionally unsafe for Phase 11 vulnerability-classification demo. */
    strcpy(buffer, argv[1]);
    printf("Input: %s\n", buffer);
    return 0;
}
