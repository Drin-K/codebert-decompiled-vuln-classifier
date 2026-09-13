/* Curated Juliet-style showcase input; not an external accuracy benchmark. */
#include <stdio.h>

__attribute__((noinline))
static void print_clean_banner(void) {
    puts("clean showcase");
}

__attribute__((noinline))
static void print_clean_status(void) {
    printf("prepared records: %d\n", 3);
}

__attribute__((noinline))
static void print_clean_footer(void) {
    puts("no unsafe copy, no unchecked arithmetic, no uncontrolled format");
}

__attribute__((noinline))
static void run_showcase_bookkeeping(void) {
    print_clean_banner();
    print_clean_status();
    print_clean_footer();
}

int main(void) {
    run_showcase_bookkeeping();
    puts("System ready");
    return 0;
}
