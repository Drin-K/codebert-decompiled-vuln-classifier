import { BadRequestException, Injectable, InternalServerErrorException, NotFoundException } from '@nestjs/common';
import { ChildProcessWithoutNullStreams, spawn } from 'child_process';
import { createReadStream, existsSync, mkdirSync, openSync, readFileSync, readSync, closeSync } from 'fs';
import { basename, isAbsolute, relative, resolve } from 'path';
import { randomUUID } from 'crypto';
import { AnalysisResultDto, PredictionDto } from './dto/analysis-result.dto';
import { addHeuristicExplanation } from './explanation';

interface ScriptOutput {
  metadata?: {
    binary?: string;
    total_functions_extracted?: number;
    total_functions_predicted?: number;
    class_distribution?: Record<string, number>;
  };
  predictions?: PredictionDto[];
}

interface ProcessResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  timedOut: boolean;
}

const runtimeOrLibraryFunctions = new Set([
  '_start', '_init', '_fini', '_dl_relocate_static_pie', 'deregister_tm_clones',
  'register_tm_clones', '__do_global_dtors_aux', 'frame_dummy', '__libc_start_main',
  '__cxa_finalize', '__stack_chk_fail', '__gmon_start__', '_global_offset_table_',
]);

const isHighlightCandidate = (prediction: PredictionDto) => {
  const name = prediction.function_name.trim().toLowerCase();
  const nonUserFunction = runtimeOrLibraryFunctions.has(name) || name.startsWith('__') ||
    name.startsWith('fun_') || name.startsWith('thunk_') || name.startsWith('plt_') ||
    name.startsWith('imp_') || name.endsWith('@plt');
  return prediction.predicted_label !== 0 && !nonUserFunction;
};

@Injectable()
export class AnalysisService {
  private readonly backendRoot = resolve(__dirname, '..', '..');
  private readonly repositoryRoot = resolve(this.backendRoot, '..', '..');
  private readonly uploadRoot = resolve(this.backendRoot, 'uploads');

  async analyze(file: Express.Multer.File): Promise<AnalysisResultDto> {
    this.assertElf(file.path);
    const runId = randomUUID();
    const config = this.configuration();
    this.assertConfiguration(config);
    const outputDir = resolve(config.outputRoot, runId);
    mkdirSync(outputDir, { recursive: true });

    const args = [
      config.scriptPath,
      '--binary', file.path,
      '--ghidra-home', config.ghidraHome,
      '--model-dir', config.modelDir,
      '--output-dir', outputDir,
      '--max-length', String(config.maxLength),
      '--batch-size', String(config.batchSize),
    ];
    const result = await this.runPython(config.pythonBin, args, config.timeoutMs);
    if (result.exitCode !== 0 || result.timedOut) {
      throw new InternalServerErrorException({
        message: result.timedOut ? 'Phase 11 analysis timed out.' : 'Phase 11 analysis failed.',
        run_id: runId,
        stdout: result.stdout,
        stderr: result.stderr,
        warnings: ['The existing Python pipeline did not complete. Review Debug details or Ghidra logs.'],
      });
    }

    const jsonPath = resolve(outputDir, 'elf_predictions.json');
    let output: ScriptOutput;
    try {
      if (!existsSync(jsonPath)) throw new Error('elf_predictions.json was not created');
      output = JSON.parse(readFileSync(jsonPath, 'utf8')) as ScriptOutput;
    } catch (error) {
      throw new InternalServerErrorException({
        message: 'Phase 11 completed without a readable predictions JSON file.',
        run_id: runId,
        stdout: result.stdout,
        stderr: result.stderr,
        warnings: [String(error)],
      });
    }
    if (!Array.isArray(output.predictions) || output.predictions.length === 0) {
      throw new InternalServerErrorException({
        message: 'Phase 11 produced no function predictions.', run_id: runId,
        stdout: result.stdout, stderr: result.stderr,
        warnings: ['Ghidra extraction may have failed before CodeBERT inference.'],
      });
    }

    const predictions = output.predictions.map(addHeuristicExplanation);
    const classDistribution = output.metadata?.class_distribution ?? {};
    const suspicious = predictions
      .filter(isHighlightCandidate)
      .sort((left, right) => right.confidence - left.confidence)
      .slice(0, 10);
    const warnings = result.stderr ? ['The pipeline produced stderr output; open Debug details to review it.'] : [];
    return {
      run_id: runId,
      binary_name: basename(output.metadata?.binary ?? file.originalname),
      total_functions: output.metadata?.total_functions_predicted ?? predictions.length,
      class_distribution: classDistribution,
      top_suspicious_functions: suspicious,
      predictions,
      output_paths: {
        csv: `/api/analyze/${runId}/download/csv`,
        json: `/api/analyze/${runId}/download/json`,
        summary: `/api/analyze/${runId}/summary`,
      },
      stdout: result.stdout,
      stderr: result.stderr,
      warnings,
    };
  }

  downloadPath(runId: string, filename: string): string {
    if (!/^[a-f0-9-]{36}$/i.test(runId)) throw new BadRequestException('Invalid analysis run id.');
    const path = resolve(this.configuration().outputRoot, runId, filename);
    if (!this.isInsideOutputRoot(path) || !existsSync(path)) throw new NotFoundException('Requested analysis output was not found.');
    return path;
  }

  stream(path: string) { return createReadStream(path); }

  private configuration() {
    const fromRoot = (value: string) => isAbsolute(value) ? value : resolve(this.repositoryRoot, value);
    return {
      pythonBin: fromRoot(process.env.PYTHON_BIN ?? '.venv/bin/python'),
      ghidraHome: fromRoot(process.env.GHIDRA_HOME ?? '/opt/ghidra'),
      modelDir: fromRoot(process.env.MODEL_DIR ?? 'models/codebert-final'),
      outputRoot: fromRoot(process.env.OUTPUT_ROOT ?? 'results/web_demo'),
      scriptPath: fromRoot(process.env.SCRIPT_PATH ?? 'scripts/predict_elf.py'),
      maxLength: Number(process.env.MAX_LENGTH ?? 512),
      batchSize: Number(process.env.BATCH_SIZE ?? 8),
      timeoutMs: Number(process.env.ANALYSIS_TIMEOUT_MS ?? 900000),
    };
  }

  private assertConfiguration(config: ReturnType<AnalysisService['configuration']>) {
    if (!existsSync(config.pythonBin)) throw new BadRequestException(`Python executable was not found: ${config.pythonBin}`);
    if (!existsSync(config.scriptPath)) throw new BadRequestException(`Phase 11 script was not found: ${config.scriptPath}`);
    if (!existsSync(config.modelDir)) throw new BadRequestException(`CodeBERT model directory was not found: ${config.modelDir}`);
    if (!existsSync(config.ghidraHome)) throw new BadRequestException(`Ghidra home directory was not found: ${config.ghidraHome}`);
    if (!Number.isInteger(config.maxLength) || config.maxLength <= 0) throw new BadRequestException('MAX_LENGTH must be a positive integer.');
    if (!Number.isInteger(config.batchSize) || config.batchSize <= 0) throw new BadRequestException('BATCH_SIZE must be a positive integer.');
  }

  private assertElf(filePath: string) {
    const descriptor = openSync(filePath, 'r');
    const bytes = Buffer.alloc(4);
    try { readSync(descriptor, bytes, 0, 4, 0); } finally { closeSync(descriptor); }
    if (!bytes.equals(Buffer.from([0x7f, 0x45, 0x4c, 0x46]))) {
      throw new BadRequestException('Uploaded file is not a Linux ELF binary.');
    }
  }

  private runPython(pythonBin: string, args: string[], timeoutMs: number): Promise<ProcessResult> {
    return new Promise((resolvePromise, reject) => {
      const child: ChildProcessWithoutNullStreams = spawn(pythonBin, args, {
        cwd: this.repositoryRoot, shell: false, windowsHide: true,
      });
      let stdout = ''; let stderr = ''; let timedOut = false;
      const timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); }, timeoutMs);
      child.stdout.on('data', (chunk: Buffer) => { stdout += chunk.toString(); });
      child.stderr.on('data', (chunk: Buffer) => { stderr += chunk.toString(); });
      child.on('error', (error) => { clearTimeout(timer); reject(new InternalServerErrorException({ message: `Could not start Phase 11: ${error.message}`, stdout, stderr })); });
      child.on('close', (exitCode) => { clearTimeout(timer); resolvePromise({ exitCode: exitCode ?? 1, stdout, stderr, timedOut }); });
    });
  }

  private isInsideOutputRoot(path: string) {
    return !relative(this.configuration().outputRoot, path).startsWith('..');
  }
}
