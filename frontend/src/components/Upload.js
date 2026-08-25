import styled from "styled-components";
import SearchButton from "./searchBtn";
import { useState, useEffect } from "react";
import { FaArrowLeft, FaSync } from "react-icons/fa";
import Loader from "./Loader";
import toast from "react-hot-toast";
import ChartView from "./ChartView";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

const Upload = ({mode}) => {
  const [btn, setBtn] = useState(0);
  const [formSchema, setFormSchema] = useState([]);
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  const [tableSchema, setTableSchema] = useState("");
  const [loading, setLoading] = useState(false);
  const [nlQuery, setNlQuery] = useState("");
  const [generatedSQL, setGeneratedSQL] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [vizSpec, setVizSpec] = useState(null);
  const [message, setMessage] = useState("");

  // Phase 12: Dynamic Forms state
  const [inputMode, setInputMode] = useState("table"); // "table" | "ddl"
  const [tableList, setTableList] = useState([]);
  const [selectedTable, setSelectedTable] = useState("");
  const [tableListLoading, setTableListLoading] = useState(false);

  // Fetch available tables from the Semantic Twin
  const fetchTables = async () => {
    setTableListLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/schema`);
      const data = await res.json();
      setTableList(data.postgresql_tables || []);
    } catch {
      setTableList([]);
    } finally {
      setTableListLoading(false);
    }
  };

  useEffect(() => {
    if (mode === 0 && inputMode === "table") {
      fetchTables();
    }
  }, [mode, inputMode]);

  const handleChange = (e, field) => {
    const { name, value, checked } = e.target;
    let newValue = value;

    if (field.inputType === "checkbox") {
      if (field.options && field.options.length > 0) {
        const prevValues = Array.isArray(formData[name]) ? formData[name] : [];
        newValue = checked
          ? [...prevValues, value]
          : prevValues.filter((v) => v !== value);
      } else {
        newValue = checked ? 1 : 0;
      }
    } else if (field.inputType === "radio") {
      newValue = value;
    } else if (field.inputType === "number") {
      newValue = value ? Number(value) : "";
    }

    setFormData((prev) => ({ ...prev, [name]: newValue }));

    let errorMsg = "";
    if (field.required) {
      if (field.inputType === "checkbox") {
        if (field.options?.length > 0 && (!newValue || newValue.length === 0)) {
          errorMsg = "Please select at least one option";
        } else if (!field.options && newValue !== 1) {
          errorMsg = "This field is required";
        }
      } else if (newValue === "" || newValue === null || newValue === undefined) {
        errorMsg = "This field is required";
      }
    }

    if (!errorMsg && field.validation?.maxLength && String(newValue).length > field.validation.maxLength) {
      errorMsg = `Max length is ${field.validation.maxLength}`;
    }

    if (!errorMsg && field.inputType === "number") {
      const { min, max } = field.validation || {};
      if (min !== undefined && newValue < min) errorMsg = `Value must be ≥ ${min}`;
      if (max !== undefined && newValue > max) errorMsg = `Value must be ≤ ${max}`;
    }

    if (!errorMsg && field.validation?.pattern) {
      const regex = new RegExp(`^${field.validation.pattern}$`);
      if (newValue && !regex.test(String(newValue))) errorMsg = "Invalid value";
    }

    if (!errorMsg && field.inputType === "email") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (newValue && !emailRegex.test(newValue)) errorMsg = "Invalid email address";
    }

    setErrors((prev) => ({ ...prev, [name]: errorMsg }));
  };

  const _initFormData = (fields) => {
    const initData = {};
    fields.forEach((field) => {
      if (field.default !== undefined && field.default !== null) {
        initData[field.name] = field.default;
      } else if (field.inputType === "checkbox") {
        initData[field.name] = field.options ? [] : 0;
      } else {
        initData[field.name] = "";
      }
    });
    return initData;
  };

  const handleGenerate = async () => {
    try {
      setLoading(true);
      let json;

      if (mode === 0 && inputMode === "table") {
        if (!selectedTable) {
          toast.error("Select a table first.");
          return;
        }
        const res = await fetch(`${BACKEND_URL}/api/generate-form-by-table`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tableName: selectedTable }),
        });
        if (!res.ok) {
          const err = await res.json();
          toast.error(err.detail || "Failed to generate form.");
          return;
        }
        json = await res.json();
      } else {
        if (!tableSchema.trim()) {
          toast.error("Please enter table schema first!");
          return;
        }
        const res = await fetch(`${BACKEND_URL}/api/generate-form`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tableSchema }),
        });
        json = await res.json();
      }

      if (!json || json.length === 0) {
        toast.error("No form fields generated. Check your input.");
        return;
      }

      setFormSchema(json);
      setFormData(_initFormData(json));
      setErrors({});
      setBtn(1);
    } catch (err) {
      console.error(err);
      toast.error("Failed to generate form.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const newErrors = {};
    formSchema.forEach((field) => {
      const val = formData[field.name];
      if (field.required && (!val || (Array.isArray(val) && val.length === 0))) {
        newErrors[field.name] = "This field is required";
      }
    });

    setErrors(newErrors);
    if (Object.values(newErrors).some((msg) => msg)) {
      toast.error("Please fix the highlighted errors before submitting.");
      return;
    }

    let tableName;
    let schemaForInsert = "";

    if (inputMode === "table") {
      tableName = selectedTable;
    } else {
      tableName = tableSchema.match(/CREATE TABLE (\w+)/i)?.[1];
      schemaForInsert = tableSchema;
      if (!tableName) {
        toast.error("Could not detect table name. Please use CREATE TABLE syntax.");
        return;
      }
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/insert-data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tableName, formData, tableSchema: schemaForInsert }),
      });

      const result = await res.json();
      if (result.message === "inserted") {
        toast.success("Data inserted successfully!");
        setFormData(_initFormData(formSchema));
        setErrors({});
      } else {
        toast.error("Insert failed: " + (result.error || result.detail || "Unknown error"));
      }
    } catch (err) {
      console.error("Insert error:", err);
      toast.error("Error inserting data. Check console for details.");
    }
  };

  const handleNaturalQuery = async () => {
    if (!nlQuery.trim()) {
      toast.error("Please enter a natural language query.");
      return;
    }

    setErrors({});
    setLoading(true);
    setGeneratedSQL("");
    setQueryResult(null);
    setVizSpec(null);
    setMessage("");

    try {
      const res = await fetch(`${BACKEND_URL}/api/nl-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nlQuery }),
      });

      const data = await res.json();

      if (res.ok) {
        setGeneratedSQL(data.sqlQuery || data.sql || "");
        setQueryResult(data.result || null);
        setVizSpec(data.viz_spec || null);
        setMessage(data.message || "");
      } else {
        setErrors({ api: data.error || "Something went wrong." });
        toast.error("Something went wrong.");
      }
    } catch (err) {
      console.error("Error:", err);
      setErrors({ api: "Failed to connect to backend." });
      toast.error("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <StyledWrapper>
      {btn === 0 && (
        <>
          {mode === 0 && (
            <div className="tab-bar">
              <button
                className={`tab-btn${inputMode === "table" ? " tab-active" : ""}`}
                onClick={() => setInputMode("table")}
              >
                Select Table
              </button>
              <button
                className={`tab-btn${inputMode === "ddl" ? " tab-active" : ""}`}
                onClick={() => setInputMode("ddl")}
              >
                Custom DDL
              </button>
            </div>
          )}

          {mode === 0 && inputMode === "table" ? (
            <div className="table-select-wrapper">
              <div className="table-select-row">
                <select
                  className="table-select"
                  value={selectedTable}
                  onChange={(e) => setSelectedTable(e.target.value)}
                  disabled={tableListLoading}
                >
                  <option value="">
                    {tableListLoading ? "Loading tables…" : "— choose a table —"}
                  </option>
                  {tableList.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                <button
                  className="refresh-btn"
                  title="Refresh table list"
                  onClick={fetchTables}
                  disabled={tableListLoading}
                >
                  <FaSync className={tableListLoading ? "spin" : ""} />
                </button>
              </div>
              {tableList.length === 0 && !tableListLoading && (
                <p className="twin-hint">
                  No tables found. Run <code>POST /api/schema/refresh</code> to build the Semantic Twin.
                </p>
              )}
            </div>
          ) : (
            <div className="form-control">
              <textarea
                className="input input-alt"
                placeholder={mode === 0 ? "Type SQL CREATE TABLE statement here" : "Type the query you want to execute"}
                rows={15}
                value={mode === 0 ? tableSchema : nlQuery}
                onChange={(e) => { mode === 0 ? setTableSchema(e.target.value) : setNlQuery(e.target.value); }}
              />
              <span className="input-border input-border-alt" />
            </div>
          )}

          <div className="button">
            <SearchButton btn={btn} setbtn={mode === 0 ? handleGenerate : handleNaturalQuery} mode={mode} />
          </div>
        </>
      )}

      {mode === 0 && !loading && btn === 1 && formSchema.length > 0 && (
        <div className="custom-form-wrapper">
          <div className="custom-form-back" onClick={() => setBtn(0)}>
            <FaArrowLeft /> Back
          </div>

          <form onSubmit={handleSubmit}>
            {formSchema.map((field) => (
              <div key={field.name} className="custom-form-control">
                <label>{field.label}</label>

                {field.inputType === "select" ? (
                  <select
                    name={field.name}
                    value={formData[field.name] || ""}
                    onChange={(e) => handleChange(e, field)}
                    className={errors[field.name] ? "custom-error-input" : ""}
                  >
                    <option value="">Select an option</option>
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : field.inputType === "radio" ? (
                  field.options?.map((opt) => (
                    <label key={opt.value} className="custom-radio-label">
                      <input
                        type="radio"
                        name={field.name}
                        value={opt.value}
                        checked={String(formData[field.name]) === String(opt.value)}
                        onChange={(e) => handleChange(e, field)}
                      />
                      {opt.label}
                    </label>
                  ))
                ) : field.inputType === "checkbox" && field.options ? (
                  field.options.map((opt) => (
                    <label key={opt.value} className="custom-checkbox-label">
                      <input
                        type="checkbox"
                        name={field.name}
                        value={opt.value}
                        checked={formData[field.name]?.includes(opt.value)}
                        onChange={(e) => handleChange(e, field)}
                      />
                      {opt.label}
                    </label>
                  ))
                ) : field.inputType === "checkbox" ? (
                  <input
                    type="checkbox"
                    name={field.name}
                    checked={!!formData[field.name]}
                    onChange={(e) => handleChange(e, field)}
                    className={errors[field.name] ? "custom-error-input" : ""}
                  />
                ) : field.inputType === "textarea" ? (
                  <textarea
                    name={field.name}
                    value={formData[field.name] || ""}
                    onChange={(e) => handleChange(e, field)}
                    required={field.required}
                    maxLength={field.validation?.maxLength}
                    className={errors[field.name] ? "custom-error-input" : ""}
                    rows={4}
                    placeholder={
                      field.default !== undefined
                        ? `Default: ${field.default}`
                        : `Enter ${field.label.toLowerCase()}...`
                    }
                  />
                ) : (
                  <input
                    type={field.inputType}
                    name={field.name}
                    value={formData[field.name] || ""}
                    onChange={(e) => handleChange(e, field)}
                    required={field.required}
                    maxLength={field.validation?.maxLength}
                    placeholder={
                      field.default !== undefined
                        ? `Default: ${field.default}`
                        : `Enter ${field.label.toLowerCase()}...`
                    }
                    className={errors[field.name] ? "custom-error-input" : ""}
                  />
                )}

                {errors[field.name] && (
                  <span className="custom-error">{errors[field.name]}</span>
                )}
              </div>
            ))}

            <button type="submit" className="custom-submit-btn">
              Submit
            </button>
          </form>
        </div>
      )}

      {mode === 1 && generatedSQL && (
        <div className="query-output-section">
          <h2>Generated SQL</h2>
          <pre className="query-sql-box">{generatedSQL}</pre>
        </div>
      )}

      {mode === 1 && vizSpec && queryResult && queryResult.length > 0 && (
        <ChartView vizSpec={vizSpec} data={queryResult} />
      )}

      {mode === 1 && queryResult && Array.isArray(queryResult) && queryResult.length > 0 && (
        <div className="query-output-section">
          <h2>Query Result</h2>
          <table className="query-result-table">
            <thead>
              <tr>
                {Object.keys(queryResult[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {queryResult.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => (
                    <td key={j}>{String(val)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mode === 1 && message && (
        <div className="query-output-section query-info-message">
          {message}
        </div>
      )}

      {loading && <Loader mode={mode} />}
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .input {
    color: #fff;
    font-size: 0.9rem;
    background-color: #212121;
    width: 100%;
    box-sizing: border-box;
    padding-inline: 0.5em;
    padding-block: 0.7em;
    border: none;
    border-bottom: var(--border-height) solid var(--border-before-color);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #b4b4b4 transparent;
  }

  .button {
    margin-left: 350px;
  }

  .input-border {
    position: absolute;
    background: var(--border-after-color);
    width: 0%;
    height: 2px;
    bottom: 0;
    left: 0;
    transition: width 0.3s cubic-bezier(0.6, -0.28, 0.735, 0.045);
  }

  .input:focus {
    outline: none;
  }

  .input:focus + .input-border {
    width: 100%;
  }

  .form-control {
    position: relative;
    width: 80vw;
    background-color: #212121;
    margin: auto;
    margin-bottom: 15px;
  }

  .input-alt {
    font-size: 1.2rem;
    padding-inline: 1em;
    padding-block: 0.8em;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .input-border-alt {
    height: 3px;
    background: linear-gradient(90deg, #FF6464 0%, #FFBF59 50%, #47C9FF 100%);
    transition: width 0.4s cubic-bezier(0.42, 0, 0.58, 1.00);
  }

  .input-alt:focus + .input-border-alt {
    width: 100%;
  }

  /* ── Phase 12: tab bar ── */
  .tab-bar {
    display: flex;
    gap: 8px;
    width: 80vw;
    margin: 0 auto 16px;
  }

  .tab-btn {
    padding: 8px 22px;
    border: 1px solid #444;
    border-radius: 6px;
    background: #1a1a1a;
    color: #aaa;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tab-btn:hover {
    border-color: #FFBF59;
    color: #fff;
  }

  .tab-active {
    background: linear-gradient(90deg, #FF6464 0%, #FFBF59 100%);
    color: #111;
    border-color: transparent;
    font-weight: 600;
  }

  /* ── Phase 12: table select ── */
  .table-select-wrapper {
    width: 80vw;
    margin: 0 auto 15px;
  }

  .table-select-row {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .table-select {
    flex: 1;
    background: #212121;
    color: #fff;
    font-size: 1.1rem;
    padding: 0.7em 1em;
    border: none;
    border-bottom: 3px solid #444;
    outline: none;
    cursor: pointer;
    appearance: none;
  }

  .table-select:focus {
    border-bottom-color: #FFBF59;
  }

  .refresh-btn {
    background: #212121;
    border: 1px solid #444;
    border-radius: 6px;
    color: #aaa;
    padding: 10px 12px;
    cursor: pointer;
    font-size: 1rem;
    transition: color 0.2s, border-color 0.2s;
  }

  .refresh-btn:hover {
    color: #FFBF59;
    border-color: #FFBF59;
  }

  .refresh-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }

  .twin-hint {
    margin-top: 10px;
    color: #888;
    font-size: 0.85rem;
  }

  .twin-hint code {
    color: #FFBF59;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .spin {
    animation: spin 0.8s linear infinite;
  }
`;

export default Upload;
