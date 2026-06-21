#include <stdio.h>
#include <stdarg.h>

static void clean_output_helper(const char *input) { printf("Message: %s\n", input); }

static void format_string_candidate_printf(const char *user_input, ...) {
    va_list arguments;
    va_start(arguments, user_input);
    vprintf(user_input, arguments);
    va_end(arguments);
}

static void format_string_candidate_fprintf(const char *user_input, ...) {
    va_list arguments;
    va_start(arguments, user_input);
    vprintf(user_input, arguments);
    va_end(arguments);
}

int main(void) {
    clean_output_helper("safe output"); format_string_candidate_printf("controlled format text\n");
    format_string_candidate_fprintf("another controlled format text\n"); return 0;
}
