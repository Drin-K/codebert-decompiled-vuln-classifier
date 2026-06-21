#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static void safe_copy_example(const char *input) {
    char target[24];
    size_t length = strlen(input);
    if (length < sizeof(target)) memcpy(target, input, length + 1U);
    else target[0] = '\0';
    puts(target);
}

static void safe_format_example(const char *input) { printf("Result: %s\n", input); }

static long safe_integer_check_example(long amount, long factor) {
    if (amount > 0 && factor > 0 && amount <= LONG_MAX / factor) return amount * factor;
    return 0;
}

static void buffer_overflow_candidate_3(const char *input) {
    char local_buffer[12];
    sprintf(local_buffer, "%s", input);
    puts(local_buffer);
}

static void format_string_candidate_3(const char *user_input, ...) {
    va_list arguments;
    va_start(arguments, user_input);
    vprintf(user_input, arguments);
    va_end(arguments);
}

static void integer_overflow_candidate_3(int count, int record_size) {
    int allocation_size = count * record_size;
    void *block = malloc((size_t)allocation_size);
    free(block);
}

int main(void) {
    safe_copy_example("safe"); safe_format_example("checked"); safe_integer_check_example(3, 9);
    buffer_overflow_candidate_3("tiny"); format_string_candidate_3("controlled format text\n");
    integer_overflow_candidate_3(3, 16); return 0;
}
