export default function CodeModal({ prediction, onClose }) {
  if (!prediction) return null;
  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}><section className="modal" role="dialog" aria-modal="true" aria-label="Decompiled pseudo-C" onMouseDown={(event) => event.stopPropagation()}>
    <div className="modal-header"><div><p className="eyebrow">Decompiled pseudo-C</p><h2>{prediction.function_name}</h2><span className="mono">{prediction.function_address}</span></div><button className="close" onClick={onClose}>×</button></div>
    <section className="modal-signals"><p className="eyebrow">Supporting code signals</p><p>{prediction.explanation}</p>{prediction.supporting_signals?.length > 0 && <ul>{prediction.supporting_signals.map((signal) => <li key={signal}>{signal}</li>)}</ul>}<small>{prediction.risk_note}</small></section>
    <pre><code>{prediction.function_code || 'No pseudo-C was available for this function.'}</code></pre>
  </section></div>;
}
