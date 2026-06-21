import { BadRequestException, Controller, Get, Param, Post, Res, UploadedFile, UseInterceptors } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { mkdirSync } from 'fs';
import { extname, resolve } from 'path';
import { randomUUID } from 'crypto';
import type { Response } from 'express';
import { AnalysisService } from './analysis.service';

const uploadRoot = resolve(process.cwd(), 'uploads');

@Controller('api/analyze')
export class AnalysisController {
  constructor(private readonly analysis: AnalysisService) {}

  @Post()
  @UseInterceptors(FileInterceptor('file', {
    storage: diskStorage({
      destination: (_request, _file, callback) => { mkdirSync(uploadRoot, { recursive: true }); callback(null, uploadRoot); },
      filename: (_request, file, callback) => callback(null, `${randomUUID()}${extname(file.originalname).slice(0, 12)}`),
    }),
    limits: { fileSize: 25 * 1024 * 1024 },
  }))
  async analyzeFile(@UploadedFile() file?: Express.Multer.File) {
    if (!file) throw new BadRequestException('Upload one ELF file in the "file" form field.');
    return this.analysis.analyze(file);
  }

  @Get(':runId/download/csv')
  downloadCsv(@Param('runId') runId: string, @Res() response: Response) {
    const path = this.analysis.downloadPath(runId, 'elf_predictions.csv');
    response.download(path, 'elf_predictions.csv');
  }

  @Get(':runId/download/json')
  downloadJson(@Param('runId') runId: string, @Res() response: Response) {
    const path = this.analysis.downloadPath(runId, 'elf_predictions.json');
    response.download(path, 'elf_predictions.json');
  }

  @Get(':runId/summary')
  summary(@Param('runId') runId: string, @Res() response: Response) {
    const path = this.analysis.downloadPath(runId, 'summary.md');
    response.type('text/markdown').sendFile(path);
  }
}
