const steps = [
  'Uploading ELF binary', 'Validating input', 'Running Ghidra/PyGhidra decompilation',
  'Extracting pseudo-C functions', 'Loading fine-tuned CodeBERT', 'Classifying functions',
  'Generating reports', 'Analysis complete',
];

export default function Workflow({ active, complete }) {
  return <section className="card workflow"><p className="eyebrow">Workflow</p><h2>Analysis pipeline</h2>
    <ol>{steps.map((step, index) => <li className={complete || index < active ? 'done' : index === active ? 'active' : ''} key={step}>
      <span>{complete || index < active ? '✓' : index + 1}</span>{step}
    </li>)}</ol>
  </section>;
}
