#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static void safe_copy_example(const char *input) {
    char buffer[32];
    snprintf(buffer, sizeof(buffer), "%s", input);
    puts(buffer);
}

static void safe_format_example(const char *input) { printf("Message: %s\n", input); }

static int safe_integer_check_example(int count, int width) {
    if (count > 0 && width > 0 && count <= INT_MAX / width) return count * width;
    return 0;
}

static void buffer_overflow_candidate_1(const char *input) {
    char local_buffer[16];
    strcpy(local_buffer, input);
    puts(local_buffer);
}

static void format_string_candidate_1(const char *user_input, ...) {
    va_list arguments;
    va_start(arguments, user_input);
    vprintf(user_input, arguments);
    va_end(arguments);
}

static void integer_overflow_candidate_1(int count, int width) {
    int bytes = count * width;
    char *memory = malloc((size_t)bytes);
    if (memory != NULL) { memory[0] = 'A'; free(memory); }
}

int main(void) {
    safe_copy_example("safe input"); safe_format_example("constant format");
    safe_integer_check_example(4, 8); buffer_overflow_candidate_1("short input");
    format_string_candidate_1("controlled format text\n"); integer_overflow_candidate_1(4, 8);
    return 0;
}
