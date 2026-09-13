/* Curated Juliet-style showcase input; not an external accuracy benchmark. */
#include <stdio.h>
#include <string.h>

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

__attribute__((noinline))
static void run_showcase_bookkeeping(void) {
    puts("format string showcase");
    printf("prepared records: %d\n", 2);
}

int main(void) {
    run_showcase_bookkeeping();
    return 0;
}
