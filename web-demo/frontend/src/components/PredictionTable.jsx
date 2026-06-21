const risk = (label) => label === 'Clean' ? 'low' : label === 'Integer Overflow' ? 'medium' : 'high';

function WhyPrediction({ prediction }) {
  return <details className="why"><summary>Why this prediction?</summary><p>{prediction.explanation}</p>
    {prediction.supporting_signals?.length > 0 && <><strong>Supporting signals</strong><ul>{prediction.supporting_signals.map((signal) => <li key={signal}>{signal}</li>)}</ul></>}
    <small>{prediction.risk_note}</small></details>;
}

export default function PredictionTable({ predictions, onView }) {
  return <section className="card table-card"><div className="section-heading"><div><p className="eyebrow">Complete results</p><h2>Function-level predictions</h2></div><span>{predictions.length} functions</span></div>
    <div className="table-wrap"><table><thead><tr><th>Function</th><th>Address</th><th>Prediction</th><th>Confidence</th><th>Risk</th><th>Interpretation</th><th /></tr></thead>
      <tbody>{predictions.map((prediction, index) => <tr key={`${prediction.function_address}-${index}`}><td>{prediction.function_name}</td><td className="mono">{prediction.function_address}</td><td>{prediction.predicted_label_name}</td><td>{(prediction.confidence * 100).toFixed(2)}%</td><td><span className={`badge ${risk(prediction.predicted_label_name)}`}>{risk(prediction.predicted_label_name)}</span></td><td><WhyPrediction prediction={prediction} /></td><td><button className="link-button" onClick={() => onView(prediction)}>View pseudo-C</button></td></tr>)}</tbody>
    </table></div>
  </section>;
}
