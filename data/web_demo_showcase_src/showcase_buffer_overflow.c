/* Curated Juliet-style showcase input; not an external accuracy benchmark. */
#include <alloca.h>
#include <stdio.h>
#include <string.h>

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
static void run_showcase_bookkeeping(void) {
    puts("buffer showcase");
    printf("prepared records: %d\n", 2);
}

int main(void) {
    run_showcase_bookkeeping();
    return 0;
}
