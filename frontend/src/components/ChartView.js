import styled from "styled-components";
import {
  BarChart, Bar,
  LineChart, Line,
  ScatterChart, Scatter,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#FF6464", "#FFBF59", "#47C9FF", "#8884d8", "#82ca9d", "#ff7300"];

const ChartView = ({ vizSpec, data }) => {
  if (!vizSpec || !data || data.length === 0) return null;

  const { chart_type, x_field, y_fields, title } = vizSpec;

  const renderChart = () => {
    switch (chart_type) {
      case "bar":
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={x_field} stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <YAxis stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #444", color: "#fff" }} />
            <Legend />
            {y_fields.map((f, i) => (
              <Bar key={f} dataKey={f} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        );

      case "line":
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={x_field} stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <YAxis stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #444", color: "#fff" }} />
            <Legend />
            {y_fields.map((f, i) => (
              <Line
                key={f}
                type="monotone"
                dataKey={f}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={data.length <= 30}
              />
            ))}
          </LineChart>
        );

      case "scatter": {
        const xKey = x_field;
        const yKey = y_fields[0];
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={xKey} name={xKey} stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <YAxis dataKey={yKey} name={yKey} stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{ background: "#1a1a1a", border: "1px solid #444", color: "#fff" }}
            />
            <Scatter data={data} fill={COLORS[0]} />
          </ScatterChart>
        );
      }

      case "pie": {
        const valueKey = y_fields[0];
        return (
          <PieChart>
            <Pie
              data={data}
              dataKey={valueKey}
              nameKey={x_field}
              cx="50%"
              cy="50%"
              outerRadius={140}
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              labelLine={false}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #444", color: "#fff" }} />
            <Legend />
          </PieChart>
        );
      }

      case "histogram": {
        const valKey = y_fields[0] || x_field;
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={x_field} stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <YAxis stroke="#aaa" tick={{ fill: "#aaa", fontSize: 12 }} />
            <Tooltip contentStyle={{ background: "#1a1a1a", border: "1px solid #444", color: "#fff" }} />
            <Bar dataKey={valKey} fill={COLORS[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        );
      }

      default:
        return null;
    }
  };

  return (
    <Wrapper>
      <h2 className="chart-title">{title}</h2>
      <ResponsiveContainer width="100%" height={360}>
        {renderChart()}
      </ResponsiveContainer>
    </Wrapper>
  );
};

const Wrapper = styled.div`
  width: 80vw;
  margin: 0 auto 24px;
  background: #1a1a1a;
  border-radius: 10px;
  padding: 24px 16px 16px;
  border: 1px solid #2a2a2a;

  .chart-title {
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 16px 8px;
    letter-spacing: 0.02em;
  }
`;

export default ChartView;
