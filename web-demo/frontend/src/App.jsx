import { useEffect, useRef, useState } from 'react';
import Workflow from './components/Workflow';
import PredictionTable from './components/PredictionTable';
import CodeModal from './components/CodeModal';

const labels = ['Clean', 'Buffer Overflow', 'Format String', 'Integer Overflow'];
const API = import.meta.env.VITE_API_BASE ?? '';

function Card({ label, value, tone }) { return <article className={`metric ${tone ?? ''}`}><span>{label}</span><strong>{value}</strong></article>; }

export default function App() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [debugOpen, setDebugOpen] = useState(false);
  const input = useRef(null);

  useEffect(() => {
    if (!running) return undefined;
    const interval = window.setInterval(() => setProgress((value) => Math.min(value + 1, 6)), 1700);
    return () => window.clearInterval(interval);
  }, [running]);

  const choose = (candidate) => { if (candidate) { setFile(candidate); setError(null); setResult(null); } };
  const reset = () => { setFile(null); setResult(null); setError(null); setProgress(0); if (input.current) input.current.value = ''; };
  const analyze = async () => {
    if (!file || running) return;
    setRunning(true); setProgress(0); setResult(null); setError(null);
    const body = new FormData(); body.append('file', file);
    try {
      const response = await fetch(`${API}/api/analyze`, { method: 'POST', body });
      const payload = await response.json();
      if (!response.ok) throw payload;
      setProgress(7); setResult(payload);
    } catch (failure) {
      setError({ message: failure.message ?? 'Analysis request failed.', stdout: failure.stdout ?? '', stderr: failure.stderr ?? '', warnings: failure.warnings ?? [] });
    } finally { setRunning(false); }
  };
  const distribution = result?.class_distribution ?? {};
  const candidates = result?.top_suspicious_functions ?? [];

  return <main><header className="hero"><div className="hero-glow" /><nav><span className="brand">CODE<span>BERT</span> / PHASE 11</span><span className="status">LOCAL ACADEMIC DEMO</span></nav>
    <div className="hero-copy"><p className="eyebrow">Decompile · classify · inspect</p><h1>ELF Vulnerability<br /><em>Classification Demo</em></h1><p>Fine-tuned CodeBERT on Ghidra-decompiled pseudo-C functions.</p></div>
  </header>
  <div className="layout"><section className="card upload-card"><p className="eyebrow">Input binary</p><h2>Analyze a Linux ELF</h2>
    <div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); choose(event.dataTransfer.files[0]); }} onClick={() => input.current?.click()}>
      <input ref={input} type="file" onChange={(event) => choose(event.target.files[0])} />
      <div className="upload-icon">↑</div><strong>{file ? file.name : 'Drop an ELF binary here'}</strong><span>{file ? `${(file.size / 1024).toFixed(1)} KB selected` : 'or select a file from your computer'}</span>
    </div>
    <div className="actions"><button className="primary" disabled={!file || running} onClick={analyze}>{running ? 'Analyzing…' : 'Analyze binary'}</button><button className="secondary" disabled={running} onClick={reset}>Reset</button></div>
    {error && <div className="error"><strong>Analysis failed</strong><p>{error.message}</p>{error.warnings.map((warning) => <small key={warning}>{warning}</small>)}</div>}
  </section><Workflow active={progress} complete={Boolean(result)} /></div>
  {result && <section className="results"><div className="results-heading"><div><p className="eyebrow">Analysis complete</p><h2>{result.binary_name}</h2><span>Run ID: <code>{result.run_id}</code></span></div><div className="downloads"><a href={`${API}${result.output_paths.csv}`}>Download CSV</a><a href={`${API}${result.output_paths.json}`}>Download JSON</a><a href={`${API}${result.output_paths.summary}`} target="_blank" rel="noreferrer">View Markdown Summary</a></div></div>
    <div className="metrics"><Card label="Functions analyzed" value={result.total_functions} /><Card label="Clean" value={distribution.Clean ?? 0} tone="clean" /><Card label="Buffer Overflow" value={distribution['Buffer Overflow'] ?? 0} tone="high" /><Card label="Format String" value={distribution['Format String'] ?? 0} tone="high" /><Card label="Integer Overflow" value={distribution['Integer Overflow'] ?? 0} tone="medium" /></div>
    <section className="card candidates"><div className="section-heading"><div><p className="eyebrow">Model prediction</p><h2>Top vulnerability candidates</h2></div><span>Non-Clean only</span></div>{candidates.length ? <div className="candidate-grid">{candidates.map((candidate, index) => <article key={`${candidate.function_address}-${index}`} className="candidate"><span className="rank">0{index + 1}</span><span className={`badge ${candidate.predicted_label_name === 'Integer Overflow' ? 'medium' : 'high'}`}>Predicted candidate</span><h3>{candidate.function_name}</h3><p className="mono">{candidate.function_address}</p><strong>{candidate.predicted_label_name}</strong><p>Potential vulnerability class · {(candidate.confidence * 100).toFixed(2)}% confidence</p><p className="explanation-preview">{candidate.explanation}</p>{candidate.supporting_signals?.slice(0, 2).map((signal) => <p className="signal-preview" key={signal}>• {signal}</p>)}<button className="link-button" onClick={() => setSelected(candidate)}>Supporting code signals & pseudo-C</button></article>)}</div> : <p className="empty">No non-clean vulnerability candidates were predicted.</p>}</section>
    <PredictionTable predictions={result.predictions} onView={setSelected} />
    <details className="debug"><summary>Debug details</summary><pre>{result.stdout || 'No stdout captured.'}{result.stderr ? `\n\nSTDERR\n${result.stderr}` : ''}</pre></details>
    <aside className="limitation">These predictions classify vulnerability candidates in Ghidra-decompiled pseudo-C functions. They do not prove real-world exploitability.<br /><br />These explanations are heuristic indicators derived from decompiled pseudo-C text. They are intended to help interpret the model prediction and do not represent formal proof of exploitability or the internal reasoning of CodeBERT.</aside>
  </section>}
  <CodeModal prediction={selected} onClose={() => setSelected(null)} />
  </main>;
}
