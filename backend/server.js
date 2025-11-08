import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import bodyParser from "body-parser";
import mysql from "mysql2/promise";
import { GoogleGenAI, Type } from "@google/genai";


dotenv.config();
const app = express();
app.use(cors());
app.use(bodyParser.json());
const genAI = new GoogleGenAI({});

const db = await mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));


app.post("/generate-form", async (req, res) => {
    const { tableSchema } = req.body;
    

    const MAX_RETRIES = 5;
    let lastError = null;

    const formFieldSchema = {
        type: Type.ARRAY,
        description: "An array of form field objects corresponding to a database table schema.",
        items: {
            type: Type.OBJECT,
            properties: {
                name: { type: Type.STRING, description: "Unique, snake_case field name (e.g., 'user_name')." },
                label: { type: Type.STRING, description: "Human-readable label for the field (e.g., 'User Name')." },
                inputType: { 
                    type: Type.STRING, 
                    enum: ["text", "number", "email", "date", "password", "textarea", "checkbox", "radio", "select"], 
                    description: "The type of HTML input element."
                },
                required: { type: Type.BOOLEAN, description: "Whether this field is mandatory." },
                default: { 
                    type: Type.Any, // Handles string, number, or boolean defaults.
                    description: "Default value to prefill the form field."
                },
                options: {
                    type: Type.ARRAY,
                    description: "List of {value, label} objects used for 'radio', 'select', or 'checkbox' types.",
                    items: {
                        type: Type.OBJECT,
                        properties: {
                            value: { type: Type.Any, description: "The internal value submitted (string or number)." },
                            label: { type: Type.STRING, description: "The text displayed to the user." }
                        },
                        required: ["value", "label"]
                    }
                },
                validation: {
                    type: Type.OBJECT,
                    description: "Validation constraints for this input field.",
                    properties: {
                        min: { type: Type.NUMBER },
                        max: { type: Type.NUMBER },
                        minLength: { type: Type.NUMBER },
                        maxLength: { type: Type.NUMBER },
                        pattern: { type: Type.STRING, description: "Regex pattern string for input validation." }
                    }
                }
            },
            required: ["name", "label", "inputType", "required"]
        }
    };

    const prompt = `
You are an expert form generation engine.

***Behavioral rule***
1. If the input is empty, missing, or not a valid CREATE TABLE statement, do NOT generate a form. Instead respond with exactly:
"No table schema provided. Please provide a SQL CREATE TABLE statement to generate the form."
(That must be the whole response — no extra text.)

***Output format (MANDATORY)***
- ALWAYS output JSON only (no explanation, no markdown fences).
- Output must be a single JSON array where each element is an object with at least these properties:
 {
 "name": "<column_name>",
 "label": "<Human readable label>",
 "inputType": "<text|number|email|date|datetime-local|password|textarea|checkbox|radio|select>",
 "required": true|false,
 "validation": { "min": <number>|undefined, "max": <number>|undefined, "minLength": <number>|undefined, "maxLength": <number>|undefined, "pattern": "<regex>"|undefined },
 "options": [ { "value": "<val>", "label": "<label>" }, ... ] // optional, used for select/radio/checkbox groups
 }

***High-priority mapping rules (apply in this order)***
- Map every column in the CREATE TABLE to one object in the array (no column omissions).
- NULLABLE / NOT NULL → required = true if column is NOT NULL and does not have a DEFAULT; otherwise required = false.
- Primary key columns (INT, BIGINT with PRIMARY KEY) → inputType = "number", required = true.
- Foreign keys (column name ends with _id) → inputType = "number"; set required = false unless NOT NULL.
- VARCHAR(N):
 - If N <= 255 → inputType = "text" (or "email" if column name suggests email); set validation.maxLength = N.
 - If N > 255 → inputType = "textarea".
- TEXT / LONGTEXT / BLOB / CLOB → inputType = "textarea".
- DATE / DATETIME / TIMESTAMP → map to "date" or "datetime-local" appropriately.
- PASSWORD/TOKEN-like columns (name contains password|token|secret) → inputType = "password".
- BOOLEAN / TINYINT(1) columns:
 - Do NOT use a single checkbox for required boolean. Instead produce **radio** with exactly two options:
 [
 { "value": 1, "label": "Yes" },
 { "value": 0, "label": "No" }
 ]
 - Set inputType = "radio". If column is NOT NULL → required = true; else required = false.
- ENUM or explicit CHECK with small set of values (e.g., CHECK (status IN ('A','B'))):
 - Use inputType = "select" (or "radio" if <= 3 options) and populate options accordingly.
- CHECK ranges (e.g., CHECK (satisfaction_rating BETWEEN 1 AND 5) or CHECK (col >= a AND col <= b)):
 - Set validation.min = a and validation.max = b; set inputType appropriate (usually "number").
 - Also include pattern only if necessary, but prefer min/max for numeric ranges.
- If both a CHECK-range and a pattern exist, prefer numeric min/max for numeric fields.
- If a column has a DEFAULT value include it in the label or add a "default" property if your schema supports it (optional).

***Edge cases & sanitization***
- Normalize SQL types: treat INT, INTEGER, SMALLINT, BIGINT as numbers; treat VARCHAR, CHAR as text; treat DECIMAL/NUMERIC as number with possible step; treat BOOLEAN and TINYINT(1) as booleans.
- For any multi-value checkbox group, set inputType = "checkbox" and options = [{value,label}, ...] and initialize form value as an array.
- Ensure option values are primitive strings or numbers (no objects).

***Examples (strict JSON)***
- Boolean column example:
{
 "name":"is_active",
 "label":"Is active?",
 "inputType":"radio",
 "required": true,
 "options":[ {"value":1,"label":"Yes"}, {"value":0,"label":"No"} ]
}

- Range example (CHECK BETWEEN 1 AND 5):
{
 "name":"satisfaction_rating",
 "label":"Satisfaction Rating",
 "inputType":"number",
 "required": false,
 "validation": { "min": 1, "max": 5 }
}

- Long text example:
{
 "name":"feedback",
 "label":"Feedback",
 "inputType":"textarea",
 "required": false
}

### Input SQL Schema:
${tableSchema}
`;

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {

            const response = await genAI.models.generateContent({
                model: "gemini-2.5-flash",
                contents: prompt,
                config: {
                    responseMimeType: "application/json",
                    responseSchema: formFieldSchema,
                },
            });

            const jsonText = response.text;
            const json = JSON.parse(jsonText); 
            console.log(`Successfully generated form fields on attempt ${attempt}.`);
            console.log(json);
            return res.json(json);

        } catch (e) {
            if (e.status === 503 || e.code === 503) {
                lastError = e;

                if (attempt < MAX_RETRIES) {
                    const delay = Math.pow(2, attempt) * 1000;
                    console.warn(`Error generating form fields: 503 UNAVAILABLE. Retrying in ${delay / 1000} seconds...`);
                    await sleep(delay);
                } else {
                    console.error("Critical: Failed to generate form fields after multiple retries.", lastError);
                    return res.status(503).json({ 
                        error: "Service temporarily unavailable. Please try again later.",
                        detail: lastError.message 
                    });
                }
            } else {
                console.error("Error generating form fields (non-503):", e);
                return res.status(500).json({ error: "Form generation failed due to invalid input or internal error." });
            }
        }
    }
});

app.post("/nl-query", async (req, res) => {
  try {
    const { nlQuery } = req.body;
    if (!nlQuery || nlQuery.trim() === "") {
      return res.status(400).json({ message: "Natural language query is required." });
    }

    const [tables] = await db.query("SHOW TABLES");
    const tableNames = tables.map(obj => Object.values(obj)[0]);

    let schemaDescription = "";
    for (const table of tableNames) {
      const [cols] = await db.query(`SHOW COLUMNS FROM \`${table}\``);
      schemaDescription += `Table: ${table}\n`;
      cols.forEach(c => {
        schemaDescription += `- ${c.Field} (${c.Type})\n`;
      });
      schemaDescription += "\n";
    }

    const prompt = `

You are an expert SQL query generator for a MySQL database.



### RULES ###

1. Always use correct table and column names from the provided schema.

2. Only generate one SQL statement.

3. Support SELECT, INSERT, UPDATE, DELETE, drop, alter, create, describe.

4. Do NOT include markdown, backticks, or explanations — output raw SQL only.

5. Never hallucinate tables or columns not present in the schema.



### DATABASE SCHEMA ###

${schemaDescription}



### USER REQUEST ###

${nlQuery}

`;

    const response = await genAI.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
    });

    const sql = response.text.trim().replace(/```/g, "");
    console.log("Generated SQL:", sql);

    let result;
    let message = "";

    try {
      const [rows] = await db.query(sql);

      const command = sql.trim().split(" ")[0].toUpperCase();

      if (["INSERT", "UPDATE", "DELETE"].includes(command)) {
        message =
          command === "INSERT"
            ? `${rows.affectedRows} row(s) inserted successfully.`
            : command === "UPDATE"
            ? `${rows.affectedRows} row(s) updated successfully.`
            : `${rows.affectedRows} row(s) deleted successfully.`;
        result = [];
      } else {
        message = "Query executed successfully.";
        result = rows;
      }
    } catch (err) {
      console.error("SQL Execution Error:", err);
      return res.status(400).json({
        sql,
        message: "Generated SQL failed to execute. Please refine your query.",
        error: err.message,
      });
    }

    res.json({
      sql,
      result,
      message,
    });
  } catch (e) {
    console.error("Error in /nl-query:", e);
    res.status(500).json({
      message: "Internal server error",
      error: e.message,
    });
  }
});



app.post("/insert-data", async (req, res) => {
  try {
    const { tableName, formData, tableSchema } = req.body;

    if (!tableName || !/^[a-zA-Z0-9_]+$/.test(tableName)) {
      return res.status(400).json({ error: "Invalid or missing table name" });
    }

    const [rows] = await db.query(`SHOW TABLES LIKE '${tableName}'`);

    if (rows.length === 0) {
      if (!tableSchema) {
        return res.status(400).json({ error: "Table does not exist and no schema provided" });
      }

      let createTableSQL = tableSchema.trim();

      if ((createTableSQL.startsWith('"') && createTableSQL.endsWith('"')) ||
          (createTableSQL.startsWith("'") && createTableSQL.endsWith("'"))) {
        createTableSQL = createTableSQL.slice(1, -1);
      }

      await db.query(createTableSQL);
      console.log(`Table ${tableName} created successfully`);
    }

    const cols = Object.keys(formData);
    const vals = Object.values(formData);
    const placeholders = cols.map(() => "?").join(",");

    await db.execute(
      `INSERT INTO \`${tableName}\` (${cols.map(col => `\`${col}\``).join(",")}) VALUES (${placeholders})`,
      vals
    );

    res.json({ message: "inserted" });
  } catch (e) {
    console.error("Error inserting data:", e);
    res.status(500).json({ error: e.message });
  }
});




app.listen(5000, () => console.log("Backend on http://localhost:5000"));
