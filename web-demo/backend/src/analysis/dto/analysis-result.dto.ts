export interface PredictionDto {
  binary_name: string;
  function_name: string;
  function_address: string;
  function_code: string;
  predicted_label: number;
  predicted_label_name: string;
  confidence: number;
  probabilities: Record<string, number>;
  explanation?: string;
  supporting_signals?: string[];
  risk_note?: string;
}

export interface AnalysisResultDto {
  run_id: string;
  binary_name: string;
  total_functions: number;
  class_distribution: Record<string, number>;
  top_suspicious_functions: PredictionDto[];
  predictions: PredictionDto[];
  output_paths: { csv: string; json: string; summary: string };
  stdout: string;
  stderr: string;
  warnings: string[];
}
