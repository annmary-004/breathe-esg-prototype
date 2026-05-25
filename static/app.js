const {useEffect, useMemo, useState} = React;

function api(path, options = {}) {
  return fetch(path, {
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  }).then(async response => {
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed");
    return data;
  });
}

function App() {
  const [tenant, setTenant] = useState(null);
  const [summary, setSummary] = useState({});
  const [rows, setRows] = useState([]);
  const [audit, setAudit] = useState([]);
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState("all");
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const selectedRow = useMemo(() => rows.find(row => row.id === selected) || rows[0], [rows, selected]);

  async function refresh() {
    const query = new URLSearchParams({status, source}).toString();
    const [summaryData, rowsData, auditData] = await Promise.all([
      api("/api/summary/"),
      api(`/api/activities/?${query}`),
      api("/api/audit/"),
    ]);
    setSummary(summaryData);
    setRows(rowsData.results);
    setAudit(auditData.results);
  }

  useEffect(() => {
    api("/api/bootstrap/").then(data => setTenant(data.tenant));
  }, []);

  useEffect(() => {
    refresh().catch(err => setError(err.message));
  }, [status, source]);

  async function ingestSamples() {
    setBusy(true); setError("");
    try {
      await api("/api/ingest/sample/", {method: "POST", body: "{}"});
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile(evt, sourceType) {
    const file = evt.target.files[0];
    if (!file) return;
    setBusy(true); setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(`/api/ingest/${sourceType}/`, {method: "POST", body});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Upload failed");
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      evt.target.value = "";
    }
  }

  async function act(row, action) {
    setBusy(true); setError("");
    try {
      await api(`/api/activities/${row.id}/${action}/`, {
        method: "POST",
        body: JSON.stringify({actor: "analyst@demo", lock: true, note: "Reviewed in prototype dashboard"}),
      });
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    React.createElement("div", {className: "shell"},
      React.createElement("header", {className: "topbar"},
        React.createElement("div", {className: "brand"},
          React.createElement("strong", null, "Breathe ESG Review Console"),
          React.createElement("span", null, tenant ? `${tenant.name} · normalized activity review` : "loading tenant")
        ),
        React.createElement("div", {className: "actions"},
          error && React.createElement("span", {className: "small", style: {color: "#b3261e"}}, error),
          React.createElement("button", {className: "btn primary", onClick: ingestSamples, disabled: busy}, busy ? "Working..." : "Load sample data")
        )
      ),
      React.createElement("div", {className: "layout"},
        React.createElement("aside", {className: "sidebar"},
          React.createElement("div", {className: "kpis"},
            React.createElement(Kpi, {label: "Rows", value: summary.total_rows || 0}),
            React.createElement(Kpi, {label: "Failed", value: summary.failed_rows || 0}),
            React.createElement(Kpi, {label: "Pending", value: summary.pending_rows || 0}),
            React.createElement(Kpi, {label: "Approved", value: summary.approved_rows || 0})
          ),
          React.createElement("div", {className: "filters"},
            React.createElement("label", null, "Status", React.createElement("select", {value: status, onChange: e => setStatus(e.target.value)},
              ["all", "pending", "failed", "locked", "rejected"].map(v => React.createElement("option", {key: v, value: v}, v))
            )),
            React.createElement("label", null, "Source", React.createElement("select", {value: source, onChange: e => setSource(e.target.value)},
              ["all", "sap", "utility", "travel"].map(v => React.createElement("option", {key: v, value: v}, v))
            )),
            React.createElement("label", null, "Upload SAP CSV", React.createElement("input", {type: "file", accept: ".csv", onChange: e => uploadFile(e, "sap")})),
            React.createElement("label", null, "Upload utility CSV", React.createElement("input", {type: "file", accept: ".csv", onChange: e => uploadFile(e, "utility")})),
            React.createElement("label", null, "Upload travel CSV", React.createElement("input", {type: "file", accept: ".csv", onChange: e => uploadFile(e, "travel")}))
          )
        ),
        React.createElement("section", {className: "content"},
          React.createElement("div", {className: "toolbar"},
            React.createElement("div", null,
              React.createElement("h1", null, "Analyst queue"),
              React.createElement("div", {className: "small"}, "Failed rows cannot be approved; pending rows lock into the audit trail.")
            ),
            React.createElement("div", {className: "small"}, scopeText(summary.by_scope || {}))
          ),
          React.createElement(ActivityTable, {rows, selected: selectedRow?.id, onSelect: setSelected}),
          selectedRow && React.createElement(DetailDrawer, {row: selectedRow, audit, busy, onApprove: () => act(selectedRow, "approve"), onReject: () => act(selectedRow, "reject")})
        )
      )
    )
  );
}

function Kpi({label, value}) {
  return React.createElement("div", {className: "kpi"}, React.createElement("span", {className: "small"}, label), React.createElement("b", null, value));
}

function scopeText(scopes) {
  return Object.entries(scopes).map(([scope, value]) => `${scope}: ${Number(value).toFixed(1)} kgCO2e`).join(" · ") || "No emissions yet";
}

function ActivityTable({rows, selected, onSelect}) {
  return React.createElement("div", {className: "table-wrap"},
    React.createElement("table", null,
      React.createElement("thead", null, React.createElement("tr", null,
        ["Source", "Record", "Facility", "Category", "Scope", "Activity", "CO2e", "Status", "Flags"].map(h => React.createElement("th", {key: h}, h))
      )),
      React.createElement("tbody", null,
        rows.length === 0 && React.createElement("tr", null, React.createElement("td", {colSpan: 9}, "No rows yet. Load samples or upload a CSV.")),
        rows.map(row => React.createElement("tr", {key: row.id, className: row.id === selected ? "selected" : "", onClick: () => onSelect(row.id)},
          React.createElement("td", null, row.source_type),
          React.createElement("td", null, row.source_record_id),
          React.createElement("td", null, row.facility),
          React.createElement("td", null, row.category),
          React.createElement("td", {className: "scope"}, row.scope),
          React.createElement("td", null, `${row.quantity ?? "-"} ${row.unit}`),
          React.createElement("td", null, row.co2e_kg == null ? "-" : Number(row.co2e_kg).toFixed(1)),
          React.createElement("td", null, React.createElement("span", {className: `pill ${row.status}`}, row.status)),
          React.createElement("td", null, React.createElement("div", {className: "flags"}, (row.flags || []).map(flag => React.createElement("span", {className: "flag", key: flag}, flag))))
        ))
      )
    )
  );
}

function DetailDrawer({row, audit, busy, onApprove, onReject}) {
  const rowAudit = audit.filter(event => event.activity_id === row.id);
  return React.createElement("div", {className: "drawer"},
    React.createElement("h2", null, `${row.source_type.toUpperCase()} ${row.source_record_id}`),
    React.createElement("div", {className: "grid"},
      React.createElement(Field, {label: "Period", value: `${row.activity_start || "-"} to ${row.activity_end || "-"}`}),
      React.createElement(Field, {label: "Emission factor", value: row.emission_factor}),
      React.createElement(Field, {label: "Supplier", value: row.supplier || "-"})
    ),
    React.createElement("div", {className: "actions"},
      React.createElement("button", {className: "btn primary", disabled: busy || row.status === "failed" || row.status === "locked", onClick: onApprove}, "Approve and lock"),
      React.createElement("button", {className: "btn danger", disabled: busy || row.status === "locked", onClick: onReject}, "Reject")
    ),
    React.createElement("h2", null, "Raw source payload"),
    React.createElement("pre", null, JSON.stringify(row.raw_payload, null, 2)),
    React.createElement("h2", null, "Audit trail"),
    React.createElement("div", {className: "audit"}, rowAudit.length ? rowAudit.map(event =>
      React.createElement("div", {className: "audit-row", key: event.id}, `${new Date(event.created_at).toLocaleString()} · ${event.actor} · ${event.action}`)
    ) : React.createElement("span", {className: "small"}, "No audit events loaded"))
  );
}

function Field({label, value}) {
  return React.createElement("div", {className: "field"}, React.createElement("span", null, label), React.createElement("strong", null, value ?? "-"));
}

ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App));
