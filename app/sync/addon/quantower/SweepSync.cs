using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using TradingPlatform.BusinessLayer;
using TradingPlatform.PresentationLayer.Plugins;

// Sweep Sync — Quantower add-on of Sweep (app.makeitsweep.com): a panel (Plugin, not a Strategy: Topstep's free Quantower
// has no Strategy Manager). Sends every execution of every connected account to the trader's Sweep journal, with the
// trader's personal key (a Quantower key: Sweep > Settings > Data > Connections > Quantower).
// Read-only: it never places, changes or cancels an order. Besides the executions, only the accounts leave the computer: name,
// connection, currency and balance (so that Sweep's balance follows the platform). No password, no market data.
//  - the sync starts when the panel opens (Quantower reopens it with the workspace) and runs until Quantower closes;
//  - every new execution is queued (%LocalAppData%\SweepSync\Quantower\queue.txt, kept if Quantower closes);
//  - the queue is sent every 2 seconds (500 executions at most per request); a « hello » every 5 minutes says the add-on runs;
//  - at start and when a connection connects, the executions of the last 7 days are read again (Sweep never doubles them);
//  - times are sent in UTC (milliseconds): Quantower keeps the times of its connections in UTC;
//  - no connection: the executions wait and are sent later (waiting longer after each failure, 5 minutes at most).
namespace SweepSync
{
    /// <summary>The panel: the key, and what is happening. Opening it starts the sync.</summary>
    public class SweepSyncPanel : Plugin
    {
        private System.Threading.Timer refresh;
        private string[] L = Texts.En;
        private bool badKey;

        public static PluginInfo GetInfo()
        {
            return new PluginInfo()
            {
                Name = "SweepSync",
                Title = "Sweep Sync",
                Group = PluginGroup.Misc,
                ShortName = "SWP",
                TemplateName = "layout.html",
                WindowParameters = new NativeWindowParameters(NativeWindowParameters.Panel),
                CustomProperties = new Dictionary<string, object>()
                {
                    { PluginInfo.Const.ALLOW_MANUAL_CREATION, true }
                }
            };
        }

        public override Size DefaultSize => new Size(460, 340);

        public override void Initialize()
        {
            base.Initialize();
            string lang = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
            L = lang == "fr" ? Texts.Fr : lang == "es" ? Texts.Es : Texts.En;
            SweepSyncEngine.Start();
            if (this.Window != null && this.Window.Browser != null)
                this.Window.Browser.AddEventHandler("save", "onclick", OnSave);
            refresh = new System.Threading.Timer(_ => Refresh(), null, 500, 2000);
        }

        /// <summary>Called when the panel is created and each time a connection connects or disconnects.</summary>
        public override void Populate(PluginParameters args = null)
        {
            base.Populate(args);
            SweepSyncEngine.ReadHistory();
            Refresh();
        }

        public override void Dispose()
        {
            if (refresh != null) { refresh.Dispose(); refresh = null; }
            base.Dispose();   // the sync goes on until Quantower closes
        }

        private void OnSave(string elementId, object args)
        {
            try
            {
                object v = this.Window.Browser.GetHtmlValue("key", HtmlGetValueAction.GetProperty, "value").Result;
                badKey = !SweepSyncEngine.SetKey(v == null ? "" : v.ToString());
                if (!badKey) this.Window.Browser.UpdateHtml("key", HtmlAction.SetValueString, string.Empty);   // the key is never shown again
            }
            catch (Exception ex) { SweepSyncEngine.Log("save: " + ex.Message); }
            Refresh();
        }

        private void Refresh()
        {
            try
            {
                if (this.Window == null || this.Window.Browser == null) return;
                List<string> lines = new List<string>();
                string key = SweepSyncEngine.Key ?? "";
                if (badKey) lines.Add(L[10]);
                else if (key.Length == 0) lines.Add(L[3]);
                else if (SweepSyncEngine.LastError == "key") lines.Add(L[6]);
                else if (SweepSyncEngine.LastError == "network" || SweepSyncEngine.LastError == "server") lines.Add(L[7]);
                else if (SweepSyncEngine.LastOk != DateTime.MinValue) lines.Add(string.Format(L[4], SweepSyncEngine.LastOk.ToString("HH:mm:ss", CultureInfo.InvariantCulture)));
                else lines.Add(L[5]);
                if (key.Length > 4) lines.Add(string.Format(L[12], "····" + key.Substring(key.Length - 4)));
                int n = SweepSyncEngine.Pending;
                if (n > 0) lines.Add(string.Format(L[8], n));
                string[] acc = SweepSyncEngine.AccountNames();
                if (acc.Length > 0) lines.Add(string.Format(L[9], string.Join(", ", acc)));
                lines.Add(L[11]);
                string js = "sweep.paint(" + SweepSyncEngine.J(L[0]) + "," + SweepSyncEngine.J(L[1]) + "," + SweepSyncEngine.J(L[2]) + "," + SweepSyncEngine.J(string.Join("\n", lines)) + ")";
                this.Window.Browser.UpdateHtml(string.Empty, HtmlAction.InvokeJs, js);
            }
            catch { }
        }
    }

    /// <summary>The panel's texts, in the language of Windows.</summary>
    internal static class Texts
    {
        // intro, key label, save, no key, sent, waiting, key refused, no connection, waiting count, accounts, bad key format, keep the panel, key saved
        public static readonly string[] En = { "Sweep Sync sends the executions of all your accounts to your Sweep journal. Read-only: it never places, changes or cancels an order.", "Your Sweep key for Quantower (Sweep > Settings > Data > Connections)", "Save", "Paste your key to start.", "Connected · last sent at {0}", "Waiting to send…", "Key refused: create a new Quantower key in Sweep and paste it here.", "No connection to Sweep: the executions wait and will be sent.", "{0} execution(s) waiting", "Accounts followed: {0}", "This is not a Sweep key (it starts with swk_).", "Keep this panel in your workspace: the sync starts with it when Quantower opens.", "Key saved: {0}" };
        public static readonly string[] Fr = { "Sweep Sync envoie les exécutions de tous tes comptes à ton journal Sweep. Lecture seule : il ne passe, ne modifie et n’annule jamais d’ordre.", "Ta clé Sweep pour Quantower (Sweep > Réglages > Données > Connexions)", "Enregistrer", "Colle ta clé pour commencer.", "Connecté · dernier envoi à {0}", "Envoi en attente…", "Clé refusée : crée une nouvelle clé Quantower dans Sweep et colle-la ici.", "Pas de connexion à Sweep : les exécutions attendent et seront envoyées.", "{0} exécution(s) en attente", "Comptes suivis : {0}", "Ce n’est pas une clé Sweep (elle commence par swk_).", "Garde ce panneau dans ton espace de travail : la synchro démarre avec lui à l’ouverture de Quantower.", "Clé enregistrée : {0}" };
        public static readonly string[] Es = { "Sweep Sync envía las ejecuciones de todas tus cuentas a tu diario de Sweep. Solo lectura: nunca envía, modifica ni cancela una orden.", "Tu clave de Sweep para Quantower (Sweep > Ajustes > Datos > Conexiones)", "Guardar", "Pega tu clave para empezar.", "Conectado · último envío a las {0}", "Envío pendiente…", "Clave rechazada: crea una nueva clave de Quantower en Sweep y pégala aquí.", "Sin conexión con Sweep: las ejecuciones esperan y se enviarán.", "{0} ejecución(es) pendiente(s)", "Cuentas seguidas: {0}", "No es una clave de Sweep (empieza por swk_).", "Deja este panel en tu espacio de trabajo: la sincronización arranca con él al abrir Quantower.", "Clave guardada: {0}" };
    }

    /// <summary>The sync itself: one for the whole platform, started by the first panel, running until Quantower closes.</summary>
    public static class SweepSyncEngine
    {
        public const string Version = "1.1.0";
        private const string DefaultUrl = "https://app.makeitsweep.com/api/sync/push";
        private const int MaxPerPush = 500;
        private const int HistoryDays = 7;
        private static readonly object Gate = new object();
        private static readonly Dictionary<string, string> pending = new Dictionary<string, string>();   // « account|execution id » → JSON
        private static readonly HashSet<string> sent = new HashSet<string>();                           // « key|JSON » accepted by Sweep
        private static readonly HashSet<string> read = new HashSet<string>();                           // connections whose recent executions were read
        private static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        private static System.Threading.Timer timer;
        private static bool started;
        private static int busy;
        private static int failures;
        private static DateTime retryAt = DateTime.MinValue;
        private static DateTime nextHello = DateTime.MinValue;

        public static string Key = "";
        public static string Url = DefaultUrl;
        public static DateTime LastOk = DateTime.MinValue;
        public static string LastError = "";   // "", "key", "network", "server", "error"

        public static int Pending { get { lock (Gate) return pending.Count; } }

        private static string Folder
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SweepSync", "Quantower"); }
        }

        public static void Start()
        {
            lock (Gate)
            {
                if (started) return;
                started = true;
            }
            Load();
            Core.Instance.TradeAdded += OnTrade;
            ReadHistory();
            timer = new System.Threading.Timer(_ => Tick(), null, 2000, 2000);
        }

        /// <summary>A key pasted by the trader: kept, then the recent executions are read and sent again with it.</summary>
        public static bool SetKey(string key)
        {
            key = (key ?? "").Trim();
            if (!Regex.IsMatch(key, "^swk_[0-9a-f]{40}$")) return false;
            lock (Gate)
            {
                Key = key;
                LastError = "";
                failures = 0;
                retryAt = DateTime.MinValue;
                nextHello = DateTime.MinValue;
                sent.Clear();
                read.Clear();
            }
            SaveConfig();
            ReadHistory();
            return true;
        }

        private static void OnTrade(Trade t)
        {
            Add(t);
        }

        /// <summary>The executions of the last days, once per connected connection (again after a reconnection), in the background.</summary>
        public static void ReadHistory()
        {
            List<Connection> todo = new List<Connection>();
            try
            {
                List<Connection> on = new List<Connection>();
                foreach (Connection c in Core.Instance.Connections.Connected) if (c != null) on.Add(c);
                lock (Gate)
                {
                    read.RemoveWhere(id => !on.Any(c => c.Id == id));   // disconnected: read again when it comes back
                    foreach (Connection c in on) if (read.Add(c.Id)) todo.Add(c);
                }
            }
            catch (Exception ex) { Log("connections: " + ex.Message); }
            foreach (Connection c in todo)
            {
                Connection conn = c;
                Task.Run(() =>
                {
                    try
                    {
                        TradesHistoryRequestParameters p = new TradesHistoryRequestParameters
                        {
                            From = DateTime.UtcNow.AddDays(-HistoryDays),
                            To = DateTime.UtcNow.AddDays(1)
                        };
                        IList<Trade> list = Core.Instance.GetTrades(p, conn.Id);
                        if (list != null) foreach (Trade t in list) Add(t);
                    }
                    catch (Exception ex)
                    {
                        lock (Gate) read.Remove(conn.Id);   // tried again at the next connection change or key
                        Log("history: " + ex.Message);
                    }
                });
            }
        }

        private static void Add(Trade x)
        {
            try
            {
                if (x == null || x.Account == null || x.Symbol == null) return;
                string id = Convert.ToString(x.Id, CultureInfo.InvariantCulture), acct = x.Account.Name;
                if (string.IsNullOrEmpty(id) || string.IsNullOrEmpty(acct)) return;
                string json = "{\"id\":" + J(id)
                    + ",\"account\":" + J(acct)
                    + ",\"contract\":" + J(x.Symbol.Name)
                    + ",\"side\":\"" + (x.Side == Side.Buy ? "buy" : "sell") + "\""
                    + ",\"qty\":" + Qty(Math.Abs(x.Quantity))
                    + ",\"price\":" + N(x.Price)
                    + ",\"ts\":" + Utc(x.DateTime).ToString(CultureInfo.InvariantCulture)
                    + ",\"fee\":" + (x.Fee != null ? N(Math.Abs(x.Fee.Value)) : "null")
                    + ",\"point_value\":" + PointValue(x.Symbol, x.Price) + "}";
                string key = acct + "|" + id;
                lock (Gate)
                {
                    if (sent.Contains(key + "|" + json)) return;   // already accepted by Sweep, unchanged
                    string old;
                    if (pending.TryGetValue(key, out old) && old == json) return;
                    pending[key] = json;
                }
                SaveQueue();
            }
            catch (Exception ex) { Log("execution: " + ex.Message); }
        }

        /// <summary>An execution time → UTC milliseconds (Quantower's times are UTC; a local time is converted).</summary>
        private static long Utc(DateTime t)
        {
            DateTime u = t.Kind == DateTimeKind.Local ? t.ToUniversalTime() : DateTime.SpecifyKind(t, DateTimeKind.Utc);
            return (long)(u - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalMilliseconds;
        }

        /// <summary>$ per point of one contract: Quantower's tick cost ÷ tick size; unknown → null (Sweep uses its own table).</summary>
        private static string PointValue(Symbol s, double price)
        {
            try
            {
                double size = s.GetTickSize(price), cost = s.GetTickCost(price);
                if (size > 0 && cost > 0 && !double.IsNaN(size) && !double.IsNaN(cost) && !double.IsInfinity(cost / size)) return N(Math.Round(cost / size, 6));
            }
            catch { }
            return "null";
        }

        private static string Qty(double q)
        {
            double r = Math.Round(q);
            return Math.Abs(q - r) < 1e-9 ? ((long)r).ToString(CultureInfo.InvariantCulture) : N(q);
        }

        /// <summary>The accounts of the connected connections, by name, for the panel.</summary>
        public static string[] AccountNames()
        {
            try { return Core.Instance.Accounts.Where(a => a != null && !string.IsNullOrEmpty(a.Name)).Select(a => a.Name).Distinct().OrderBy(n => n).ToArray(); }
            catch { return new string[0]; }
        }

        private static void Tick()
        {
            if (Interlocked.Exchange(ref busy, 1) == 1) return;
            try
            {
                if (string.IsNullOrEmpty(Key) || DateTime.UtcNow < retryAt) return;
                List<KeyValuePair<string, string>> batch;
                bool hello;
                lock (Gate)
                {
                    batch = pending.Take(MaxPerPush).ToList();
                    hello = DateTime.UtcNow >= nextHello;
                }
                if (batch.Count == 0 && !hello) return;
                string body = "{\"client\":" + J("Sweep Quantower " + Version) + ",\"accounts\":[" + AccountsJson() + "],\"fills\":[" + string.Join(",", batch.Select(b => b.Value)) + "]}";
                int code = Post(body);
                lock (Gate)
                {
                    if (code == 200)
                    {
                        foreach (KeyValuePair<string, string> b in batch)
                        {
                            string now;
                            if (pending.TryGetValue(b.Key, out now) && now == b.Value) pending.Remove(b.Key);   // amended meanwhile: sent next time
                            sent.Add(b.Key + "|" + b.Value);
                        }
                        LastOk = DateTime.Now;
                        LastError = "";
                        failures = 0;
                        nextHello = DateTime.UtcNow.AddMinutes(5);
                    }
                    else if (code == 401)
                    {
                        LastError = "key";   // revoked, wrong key, or a NinjaTrader key: wait for a new one
                        retryAt = DateTime.UtcNow.AddMinutes(5);
                    }
                    else
                    {
                        failures++;
                        LastError = code == 0 ? "network" : "server";
                        retryAt = DateTime.UtcNow.AddSeconds(Math.Min(300, 5 * Math.Pow(2, Math.Min(failures, 6))));
                    }
                }
                if (code == 200) SaveQueue();
            }
            catch (Exception ex) { LastError = "error"; Log("send: " + ex.Message); }
            finally { Interlocked.Exchange(ref busy, 0); }
        }

        /// <summary>What Quantower says about the accounts (name, connection, provider, currency, balance) — never a password.</summary>
        private static string AccountsJson()
        {
            List<string> parts = new List<string>();
            try
            {
                Dictionary<string, Connection> conns = new Dictionary<string, Connection>();
                foreach (Connection c in Core.Instance.Connections.Connected) if (c != null && c.Id != null) conns[c.Id] = c;
                foreach (Account a in Core.Instance.Accounts.Take(50))
                {
                    try
                    {
                        if (a == null || string.IsNullOrEmpty(a.Name)) continue;
                        Connection c;
                        string conn = "", provider = "";
                        if (a.ConnectionId != null && conns.TryGetValue(a.ConnectionId, out c))
                        {
                            conn = c.Name ?? "";
                            provider = c.VendorName ?? "";
                        }
                        string cur = a.AccountCurrency != null ? a.AccountCurrency.Name ?? "" : "";
                        string cash = "";   // (1.1.0) the account's balance: Sweep's balance follows it
                        try { double v = a.Balance; if (!double.IsNaN(v) && !double.IsInfinity(v)) cash = ",\"cash\":" + v.ToString("0.##", CultureInfo.InvariantCulture); } catch { }
                        parts.Add("{\"name\":" + J(a.Name) + ",\"connection\":" + J(conn) + ",\"provider\":" + J(provider) + ",\"currency\":" + J(cur) + cash + "}");
                    }
                    catch { }
                }
            }
            catch (Exception ex) { Log("accounts: " + ex.Message); }
            return string.Join(",", parts);
        }

        private static int Post(string body)
        {
            try
            {
                using (HttpRequestMessage req = new HttpRequestMessage(HttpMethod.Post, Url))
                {
                    req.Headers.TryAddWithoutValidation("X-Sweep-Key", Key);
                    req.Headers.TryAddWithoutValidation("User-Agent", "SweepSync-Quantower/" + Version);
                    req.Content = new StringContent(body, Encoding.UTF8, "application/json");
                    using (HttpResponseMessage r = http.SendAsync(req).GetAwaiter().GetResult()) return (int)r.StatusCode;
                }
            }
            catch (Exception ex) { Log("network: " + ex.Message); return 0; }
        }

        /* ---------- files: the key and the executions waiting ---------- */

        private static void Load()
        {
            try
            {
                string cfg = Path.Combine(Folder, "config.txt");
                if (File.Exists(cfg))
                    foreach (string line in File.ReadAllLines(cfg))
                    {
                        if (line.StartsWith("key=")) Key = line.Substring(4).Trim();
                        else if (line.StartsWith("url=") && line.Length > 4) Url = line.Substring(4).Trim();   // tests only: another Sweep server
                    }
                string q = Path.Combine(Folder, "queue.txt");
                if (File.Exists(q))
                    lock (Gate)
                        foreach (string line in File.ReadAllLines(q))
                        {
                            int i = line.IndexOf('\t');
                            if (i > 0) pending[line.Substring(0, i)] = line.Substring(i + 1);
                        }
            }
            catch (Exception ex) { Log("load: " + ex.Message); }
        }

        private static void SaveConfig()
        {
            try
            {
                Directory.CreateDirectory(Folder);
                List<string> lines = new List<string> { "key=" + Key };
                if (Url != DefaultUrl) lines.Add("url=" + Url);
                WriteAll(Path.Combine(Folder, "config.txt"), lines);
            }
            catch (Exception ex) { Log("config: " + ex.Message); }
        }

        private static void SaveQueue()
        {
            try
            {
                List<string> lines;
                lock (Gate) lines = pending.Select(p => p.Key + "\t" + p.Value).ToList();
                Directory.CreateDirectory(Folder);
                WriteAll(Path.Combine(Folder, "queue.txt"), lines);
            }
            catch (Exception ex) { Log("queue: " + ex.Message); }
        }

        private static readonly object FileGate = new object();
        private static void WriteAll(string path, List<string> lines)
        {
            lock (FileGate)
            {
                string tmp = path + ".tmp";
                File.WriteAllLines(tmp, lines, new UTF8Encoding(false));
                File.Move(tmp, path, true);
            }
        }

        /* ---------- JSON ---------- */

        public static string J(string s)
        {
            StringBuilder b = new StringBuilder("\"");
            foreach (char c in s ?? "")
            {
                switch (c)
                {
                    case '"': b.Append("\\\""); break;
                    case '\\': b.Append("\\\\"); break;
                    case '\n': b.Append("\\n"); break;
                    case '\r': b.Append("\\r"); break;
                    case '\t': b.Append("\\t"); break;
                    default:
                        if (c < 0x20 || c == 0x2028 || c == 0x2029) b.Append("\\u").Append(((int)c).ToString("x4"));
                        else b.Append(c);
                        break;
                }
            }
            return b.Append('"').ToString();
        }

        private static string N(double v)
        {
            return double.IsNaN(v) || double.IsInfinity(v) ? "null" : v.ToString("R", CultureInfo.InvariantCulture);
        }

        public static void Log(string text)
        {
            try { Core.Instance.Loggers.Log("Sweep Sync: " + text); } catch { }
        }
    }
}
