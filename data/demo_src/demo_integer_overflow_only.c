#include <stdlib.h>

static int clean_integer_helper(int value) {
    if (value > 0 && value < 100) return value + 1;
    return 0;
}

static void integer_overflow_candidate_multiply(int count, int element_size) {
    int allocation_size = count * element_size;
    char *memory = malloc((size_t)allocation_size);
    if (memory != NULL) { memory[0] = 'I'; free(memory); }
}

static void integer_overflow_candidate_add(int count, int extra) {
    int total_count = count + extra;
    int *items = malloc((size_t)(total_count * sizeof(int)));
    if (items != NULL) { items[0] = 1; free(items); }
}

int main(void) {
    clean_integer_helper(8); integer_overflow_candidate_multiply(4, 16);
    integer_overflow_candidate_add(4, 2); return 0;
}
