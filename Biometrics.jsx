import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import './Biometrics.css';

export default function Biometrics({ data }) {
  const mousePlotRef = useRef(null);
  const keystrokePlotRef = useRef(null);

  useEffect(() => {
    if (!data || !data.mouse || !data.keyboard) return;

    // Mouse Movement Visualization
    if (mousePlotRef.current) {
      const mouseTrace = {
        x: data.mouse.movements.map(m => m.x),
        y: data.mouse.movements.map(m => -m.y), // Invert Y for more natural view
        mode: 'lines+markers',
        type: 'scatter',
        name: 'Mouse Path',
        marker: { size: 4 }
      };

      const layout = {
        title: 'Mouse Movement Pattern',
        xaxis: { title: 'X Position' },
        yaxis: { title: 'Y Position' },
        showlegend: true
      };

      Plotly.newPlot(mousePlotRef.current, [mouseTrace], layout);
    }

    // Keystroke Dynamics Visualization
    if (keystrokePlotRef.current && data.keyboard.keystrokes.length > 0) {
      const keys = data.keyboard.keystrokes.map(k => k.key);
      const dwellTimes = data.keyboard.keystrokes.map(k => k.dwellTime);
      
      const keystrokeTrace = {
        x: keys,
        y: dwellTimes,
        type: 'bar',
        name: 'Dwell Time (ms)'
      };

      const layout = {
        title: 'Keystroke Dynamics',
        xaxis: { title: 'Key Pressed' },
        yaxis: { title: 'Duration (ms)' }
      };

      Plotly.newPlot(keystrokePlotRef.current, [keystrokeTrace], layout);
    }

    return () => {
      // Cleanup Plotly instances
      if (mousePlotRef.current) {
        Plotly.purge(mousePlotRef.current);
      }
      if (keystrokePlotRef.current) {
        Plotly.purge(keystrokePlotRef.current);
      }
    };
  }, [data]);

  if (!data) {
    return <div className="loading">Loading biometric data...</div>;
  }

  return (
    <div className="biometrics-container">
      <div className="biometrics-header">
        <h2>Behavioral Biometrics</h2>
        <div className="metrics-summary">
          <div className="metric">
            <span>Mouse Velocity:</span>
            <strong>{data.mouse.avgVelocity.toFixed(2)} px/s</strong>
          </div>
          <div className="metric">
            <span>Avg Dwell Time:</span>
            <strong>{data.keyboard.avgDwellTime.toFixed(2)} ms</strong>
          </div>
        </div>
      </div>

      <div className="biometrics-plots">
        <div ref={mousePlotRef} className="plot-container"></div>
        <div ref={keystrokePlotRef} className="plot-container"></div>
      </div>

      <div className="biometrics-data">
        <h3>Raw Data Sample</h3>
        <div className="data-sample">
          <pre>{JSON.stringify({
            mouse: data.mouse.movements.slice(0, 5),
            keyboard: data.keyboard.keystrokes.slice(0, 5)
          }, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
}