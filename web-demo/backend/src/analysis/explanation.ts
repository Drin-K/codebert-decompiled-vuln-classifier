import { PredictionDto } from './dto/analysis-result.dto';

const matches = (code: string, expression: RegExp) => expression.test(code);

export function addHeuristicExplanation(prediction: PredictionDto): PredictionDto {
  const code = prediction.function_code ?? '';
  const signals: string[] = [];
  const confidence = `${(prediction.confidence * 100).toFixed(2)}%`;

  if (prediction.predicted_label_name === 'Buffer Overflow') {
    if (matches(code, /\b(strcpy|strcat|sprintf|vsprintf|gets)\s*\(/i)) signals.push('Detected a copy- or format-like call without an explicit bound in its name.');
    if (matches(code, /\b(memcpy|memmove)\s*\(/i)) signals.push('Detected a memory-copy call. Its size argument should be reviewed.');
    if (matches(code, /\b(?:char|byte|uint8_t|undefined1)\s+[A-Za-z_]\w*\s*\[/i)) signals.push('Detected a local buffer-like array in the decompiled pseudo-C.');
    if (matches(code, /\b(?:if|while|for)\s*\([^)]*(?:<|<=|>|>=)[^)]*\)/)) signals.push('Detected a conditional comparison that may act as a bounds check.');
  } else if (prediction.predicted_label_name === 'Format String') {
    if (matches(code, /\b(?:printf|fprintf|sprintf|snprintf|syslog|vprintf|vfprintf)\s*\(/i)) signals.push('Detected a printf-like function call.');
    if (matches(code, /\b(?:printf|vprintf|syslog)\s*\(\s*(?!["'])?[A-Za-z_]\w*/i) || matches(code, /\b(?:fprintf|sprintf|snprintf|vfprintf)\s*\([^,]+,\s*(?!["'])?[A-Za-z_]\w*/i)) signals.push('A variable appears to be used in a format-argument position.');
  } else if (prediction.predicted_label_name === 'Integer Overflow') {
    const arithmetic = matches(code, /\b[A-Za-z_]\w*\s*(?:\+|\*|-)\s*[A-Za-z_]\w*\b/);
    const sizeContext = matches(code, /\b(size|length|len|count|alloc|malloc|calloc|realloc|sizeof)\b/i);
    const integerType = matches(code, /\b(?:int|unsigned|long|short|size_t|uint\d*|undefined\d+)\b/i);
    if (arithmetic && sizeContext) signals.push('Detected arithmetic in a size, length, count, or allocation-related context.');
    else if (arithmetic) signals.push('Detected arithmetic involving decompiled variables.');
    if (arithmetic && integerType) signals.push('Detected integer-like declarations alongside an arithmetic operation.');
  }

  if (prediction.predicted_label === 0) return { ...prediction, explanation: 'The model predicted Clean. No high-risk heuristic indicators were highlighted in the decompiled text.', supporting_signals: ['No high-risk heuristic indicators were highlighted.'], risk_note: 'This is a model prediction, not a proof that the function is safe.' };
  if (signals.length === 0) return { ...prediction, explanation: `The model predicted ${prediction.predicted_label_name} with ${confidence} confidence, but no simple heuristic indicator was detected in the decompiled text.`, supporting_signals: [], risk_note: 'Manual review is recommended.' };
  const article = prediction.predicted_label_name === 'Integer Overflow' ? 'an' : 'a';
  return { ...prediction, explanation: `The model predicted ${article} ${prediction.predicted_label_name} candidate. The matched code patterns below may support this prediction.`, supporting_signals: signals, risk_note: 'These signals are heuristic indicators. Manual review is recommended.' };
}
