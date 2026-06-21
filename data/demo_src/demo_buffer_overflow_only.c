#include <stdio.h>
#include <string.h>

static int clean_length_helper(const char *input) {
    size_t length = strlen(input);
    return length < 64U ? (int)length : -1;
}

static void buffer_overflow_candidate_copy(const char *input) {
    char local_buffer[16];
    strcpy(local_buffer, input);
    puts(local_buffer);
}

static void buffer_overflow_candidate_concat(const char *input) {
    char local_message[20] = "note: ";
    strcat(local_message, input);
    puts(local_message);
}

int main(void) {
    clean_length_helper("short"); buffer_overflow_candidate_copy("safe");
    buffer_overflow_candidate_concat("text"); return 0;
}
