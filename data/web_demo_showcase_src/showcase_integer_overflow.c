/* Curated Juliet-style showcase input; not an external accuracy benchmark. */
#include <stdio.h>
#include <stdlib.h>

int staticReturnsTrue(void);
void printHexCharLine(char value);

#define URAND31() (((unsigned)rand() << 30) ^ ((unsigned)rand() << 15) ^ rand())
#define RAND32() ((int)(rand() & 1 ? URAND31() : -URAND31() - 1))

__attribute__((noinline, no_stack_protector))
void CWE190_Integer_Overflow__char_rand_add_08_bad(void) {
    char data = ' ';

    if (staticReturnsTrue()) {
        data = (char)RAND32();
    }
    if (staticReturnsTrue()) {
        char result = data + 1;
        printHexCharLine(result);
    }
}

__attribute__((noinline, no_stack_protector))
void CWE190_Integer_Overflow__char_rand_square_08_bad(void) {
    char data = ' ';

    if (staticReturnsTrue()) {
        data = (char)RAND32();
    }
    if (staticReturnsTrue()) {
        char result = data * data;
        printHexCharLine(result);
    }
}

__attribute__((noinline))
static void run_showcase_bookkeeping(void) {
    puts("integer overflow showcase");
    printf("prepared records: %d\n", 2);
}

int main(void) {
    run_showcase_bookkeeping();
    return 0;
}
