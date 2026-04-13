/* app.js — QueryCraft Alpine.js application logic */

function app() {
  return {
    theme: localStorage.getItem('qc-theme') || 'dark',
    sidebarOpen: window.innerWidth > 768,
    schema: [],
    messages: [],
    history: [],
    question: '',
    loading: false,
    hasApiKey: true,
    highlightedTable: '',

    exampleQuestions: [
      'Top 10 customers by total spend',
      'Most popular genre',
      'Monthly revenue trend',
      'Which artists have the most albums?',
      'Average invoice by country',
    ],

    init() {
      document.documentElement.setAttribute('data-theme', this.theme);
      this.fetchSchema();
    },

    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', this.theme);
      localStorage.setItem('qc-theme', this.theme);
    },

    async fetchSchema() {
      try {
        const res = await fetch('/api/schema');
        if (!res.ok) throw new Error('Failed to load schema');
        const data = await res.json();
        this.schema = data.map(t => ({ ...t, _open: false }));
      } catch (e) {
        console.error('Schema load failed:', e);
      }
    },

    async submitQuestion(q) {
      q = q.trim();
      if (!q || this.loading) return;

      this.messages.push({ role: 'user', content: q });
      this.history.push(q);
      this.question = '';
      this.loading = true;
      this.scrollToBottom();

      try {
        const res = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q }),
        });

        const data = await res.json();

        if (!res.ok) {
          if (data.detail && data.detail.includes('API key')) {
            this.hasApiKey = false;
            this.messages.push({
              role: 'assistant',
              error: 'llm',
              detail: data.detail,
            });
          } else if (data.error_type === 'sql') {
            this.messages.push({
              role: 'assistant',
              error: 'sql',
              sql: data.sql || '',
              _showSql: false,
            });
          } else {
            this.messages.push({
              role: 'assistant',
              error: 'llm',
              detail: data.detail || 'Unknown error',
            });
          }
        } else {
          const msg = {
            role: 'assistant',
            summary: data.summary,
            sql: data.sql,
            columns: data.columns,
            rows: data.rows,
            _showSql: false,
            _sortCol: null,
            _sortAsc: true,
            _displayRows: (data.rows || []).slice(0, 50),
          };
          this.messages.push(msg);
          this.highlightTable(data.sql);
        }
      } catch (e) {
        this.messages.push({
          role: 'assistant',
          error: 'llm',
          detail: 'Network error — could not reach the server.',
        });
      }

      this.loading = false;
      this.scrollToBottom();
    },

    replayQuestion(q) {
      this.question = q;
      this.submitQuestion(q);
    },

    sortColumn(msg, colIdx) {
      if (msg._sortCol === colIdx) {
        msg._sortAsc = !msg._sortAsc;
      } else {
        msg._sortCol = colIdx;
        msg._sortAsc = true;
      }

      const sorted = [...msg.rows].sort((a, b) => {
        const va = a[colIdx];
        const vb = b[colIdx];
        if (va == null) return 1;
        if (vb == null) return -1;
        if (typeof va === 'number' && typeof vb === 'number') {
          return msg._sortAsc ? va - vb : vb - va;
        }
        const sa = String(va).toLowerCase();
        const sb = String(vb).toLowerCase();
        if (sa < sb) return msg._sortAsc ? -1 : 1;
        if (sa > sb) return msg._sortAsc ? 1 : -1;
        return 0;
      });

      msg._displayRows = sorted.slice(0, 50);
    },

    exportCsv(msg) {
      const escape = (val) => {
        const s = String(val == null ? '' : val);
        return s.includes(',') || s.includes('"') || s.includes('\n')
          ? '"' + s.replace(/"/g, '""') + '"'
          : s;
      };

      const header = msg.columns.map(escape).join(',');
      const rows = msg.rows.map(r => r.map(escape).join(','));
      const csv = [header, ...rows].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query-results.csv';
      a.click();
      URL.revokeObjectURL(url);
    },

    highlightTable(sql) {
      if (!sql) return;
      const upper = sql.toUpperCase();
      for (const table of this.schema) {
        if (upper.includes(table.name.toUpperCase())) {
          this.highlightedTable = table.name;
          return;
        }
      }
      this.highlightedTable = '';
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatThread;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
  };
}
