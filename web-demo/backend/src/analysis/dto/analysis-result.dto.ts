export interface PredictionDto {
  binary_name: string;
  function_name: string;
  function_address: string;
  function_code: string;
  classification_status: 'classified' | 'excluded';
  exclusion_reason: string;
  predicted_label: number | null;
  predicted_label_name: string;
  confidence: number | null;
  probabilities: Record<string, number>;
  explanation?: string;
  supporting_signals?: string[];
  risk_note?: string;
}

export interface AnalysisResultDto {
  run_id: string;
  binary_name: string;
  total_functions: number;
  total_functions_extracted: number;
  total_functions_classified: number;
  total_functions_excluded: number;
  class_distribution: Record<string, number>;
  top_suspicious_functions: PredictionDto[];
  predictions: PredictionDto[];
  output_paths: { csv: string; json: string; summary: string };
  stdout: string;
  stderr: string;
  warnings: string[];
}
