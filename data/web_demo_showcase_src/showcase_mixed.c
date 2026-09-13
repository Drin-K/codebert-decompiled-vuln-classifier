/* Curated Juliet-style mixed showcase; not an external accuracy benchmark. */
#include <alloca.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int staticReturnsTrue(void);
void printHexCharLine(char value);

#define URAND31() (((unsigned)rand() << 30) ^ ((unsigned)rand() << 15) ^ rand())
#define RAND32() ((int)(rand() & 1 ? URAND31() : -URAND31() - 1))

__attribute__((noinline))
void CWE121_Stack_Based_Buffer_Overflow__CWE131_memmove_16_bad(void) {
    int *data = (int *)alloca(10);
    int source[10] = {0};
    int i;

    for (i = 0; i < 10; i++) {
        source[i] = i;
    }

    memmove(data, source, 10 * sizeof(int));
    printf("%d\n", data[0]);
}

__attribute__((noinline))
void CWE121_Stack_Based_Buffer_Overflow__CWE131_memcpy_16_bad(void) {
    int *data = (int *)alloca(10);
    int source[10] = {1, 2, 3};
    int i;

    for (i = 3; i < 10; i++) {
        source[i] = i * 2;
    }

    memcpy(data, source, 10 * sizeof(int));
    printf("%d\n", data[1]);
}

__attribute__((noinline))
void CWE134_Uncontrolled_Format_String__char_console_snprintf_01_bad(void) {
    char data[100] = "";
    char destination[100] = "";

    if (fgets(data, sizeof(data), stdin) != NULL) {
        data[strcspn(data, "\n")] = '\0';
        snprintf(destination, sizeof(destination) - 1, data);
        puts(destination);
    }
}

__attribute__((noinline))
void CWE134_Uncontrolled_Format_String__char_console_printf_01_bad(void) {
    char data[100] = "";

    if (fgets(data, sizeof(data), stdin) != NULL) {
        data[strcspn(data, "\n")] = '\0';
        printf(data);
        putchar('\n');
    }
}

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
    puts("mixed showcase");
    printf("prepared records: %d\n", 6);
}

int main(void) {
    run_showcase_bookkeeping();
    return 0;
}
