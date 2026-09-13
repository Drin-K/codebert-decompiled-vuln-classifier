#include <stdio.h>

int staticReturnsTrue(void) {
    return 1;
}

void printHexCharLine(char value) {
    printf("%02x\n", (unsigned char)value);
}
