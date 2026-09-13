# Curated Web Demo Showcase Verification

- Model: `models/codebert-group-aware/`
- Threshold: 0.70
- ELF files completed: 5/5
- Eligible functions: 25
- Expected raw classes: 25/25 correct
- Accepted decisions: 25/25
- Human-review decisions: 0
- Unexpected eligible functions: 0

| ELF | Function | Expected | Predicted | Confidence | Decision |
|---|---|---|---|---:|---|
| `showcase_buffer_overflow` | `CWE121_Stack_Based_Buffer_Overflow__CWE131_memmove_16_bad` | Buffer Overflow | Buffer Overflow | 78.77% | Accepted |
| `showcase_buffer_overflow` | `CWE121_Stack_Based_Buffer_Overflow__CWE131_memcpy_16_bad` | Buffer Overflow | Buffer Overflow | 76.58% | Accepted |
| `showcase_buffer_overflow` | `run_showcase_bookkeeping` | Clean | Clean | 90.34% | Accepted |
| `showcase_buffer_overflow` | `main` | Clean | Clean | 88.76% | Accepted |
| `showcase_format_string` | `CWE134_Uncontrolled_Format_String__char_console_snprintf_01_bad` | Format String | Format String | 98.28% | Accepted |
| `showcase_format_string` | `CWE134_Uncontrolled_Format_String__char_console_printf_01_bad` | Format String | Format String | 98.06% | Accepted |
| `showcase_format_string` | `run_showcase_bookkeeping` | Clean | Clean | 90.36% | Accepted |
| `showcase_format_string` | `main` | Clean | Clean | 88.76% | Accepted |
| `showcase_integer_overflow` | `CWE190_Integer_Overflow__char_rand_add_08_bad` | Integer Overflow | Integer Overflow | 97.91% | Accepted |
| `showcase_integer_overflow` | `CWE190_Integer_Overflow__char_rand_square_08_bad` | Integer Overflow | Integer Overflow | 97.97% | Accepted |
| `showcase_integer_overflow` | `run_showcase_bookkeeping` | Clean | Clean | 90.24% | Accepted |
| `showcase_integer_overflow` | `main` | Clean | Clean | 88.76% | Accepted |
| `showcase_clean` | `print_clean_banner` | Clean | Clean | 90.41% | Accepted |
| `showcase_clean` | `print_clean_status` | Clean | Clean | 89.95% | Accepted |
| `showcase_clean` | `print_clean_footer` | Clean | Clean | 90.21% | Accepted |
| `showcase_clean` | `run_showcase_bookkeeping` | Clean | Clean | 90.93% | Accepted |
| `showcase_clean` | `main` | Clean | Clean | 87.76% | Accepted |
| `showcase_mixed` | `CWE121_Stack_Based_Buffer_Overflow__CWE131_memmove_16_bad` | Buffer Overflow | Buffer Overflow | 78.24% | Accepted |
| `showcase_mixed` | `CWE121_Stack_Based_Buffer_Overflow__CWE131_memcpy_16_bad` | Buffer Overflow | Buffer Overflow | 76.06% | Accepted |
| `showcase_mixed` | `CWE134_Uncontrolled_Format_String__char_console_snprintf_01_bad` | Format String | Format String | 98.28% | Accepted |
| `showcase_mixed` | `CWE134_Uncontrolled_Format_String__char_console_printf_01_bad` | Format String | Format String | 98.06% | Accepted |
| `showcase_mixed` | `CWE190_Integer_Overflow__char_rand_add_08_bad` | Integer Overflow | Integer Overflow | 97.91% | Accepted |
| `showcase_mixed` | `CWE190_Integer_Overflow__char_rand_square_08_bad` | Integer Overflow | Integer Overflow | 97.97% | Accepted |
| `showcase_mixed` | `run_showcase_bookkeeping` | Clean | Clean | 90.28% | Accepted |
| `showcase_mixed` | `main` | Clean | Clean | 88.76% | Accepted |

## Interpretation

This is a curated best-case capability showcase, not an external accuracy estimate. The unstripped symbols and code patterns are intentionally aligned with the Juliet-style training domain. Generalization claims must use the separately retained seven-demo and stripped-binary evaluations.
