#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static void safe_copy_example(const char *input) {
    char target[40];
    if (strlen(input) < sizeof(target)) snprintf(target, sizeof(target), "%s", input);
    puts(target);
}

static void safe_format_example(const char *input) { fprintf(stdout, "Status: %s\n", input); }

static unsigned int safe_integer_check_example(unsigned int left, unsigned int right) {
    if (left <= UINT_MAX - right) return left + right;
    return 0;
}

static void buffer_overflow_candidate_2(const char *input) {
    char local_message[20] = "prefix: ";
    strcat(local_message, input);
    puts(local_message);
}

static void format_string_candidate_2(const char *user_input, ...) {
    va_list arguments;
    va_start(arguments, user_input);
    vprintf(user_input, arguments);
    va_end(arguments);
}

static void integer_overflow_candidate_2(unsigned int count, unsigned int width) {
    unsigned int total = count + width;
    int *items = malloc((size_t)(total * sizeof(int)));
    if (items != NULL) { items[0] = 7; free(items); }
}

int main(void) {
    safe_copy_example("bounded"); safe_format_example("ready"); safe_integer_check_example(2, 3);
    buffer_overflow_candidate_2("ok"); format_string_candidate_2("controlled format text\n");
    integer_overflow_candidate_2(4U, 8U); return 0;
}
