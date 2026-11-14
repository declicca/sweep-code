using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using SweepPlanSync;
using TradingPlatform.BusinessLayer;

// Sweep Plan — Plan Sync on Quantower (BRIEF_PLAN_SYNC, step 3, 13 Nov. 2026): an indicator the trader adds to a chart. It draws
// the day's plan made in Sweep (levels as lines, zones as light rectangles, behind the candles, with their names) and alerts with
// Quantower's own alerts when price reaches them or a rule of the plan happens (approach, enter, close above / below, sweep, a
// New York time). The triggers are evaluated here, on Quantower's prices (sync/addon/plan/PlanCore.cs, shared with NinjaTrader 8):
// no call to Sweep to evaluate, no market data sent to Sweep. It never places, changes or cancels an order.
//  - the same key as the Sweep Sync panel (read from %LocalAppData%\SweepSync\Quantower\config.txt), the same server;
//  - the plan is read when a chart of the instrument opens, then every 15 s while one is open (If-None-Match: almost always 304);
//  - each alert at most once per trading day, even with several charts of the instrument (one engine per instrument root: MNQ
//    reads NQ); kept across restarts (fired.txt); the chart's banner can re-arm the last one;
//  - what alerted is sent to Sweep (api/plan-sync/events) every 30 s or right away, kept in events.txt while Sweep is unreachable;
//  - Sweep unreachable: the last plan received (plan-<root>.json) stays drawn and its alerts go on.
[assembly: System.Runtime.Versioning.SupportedOSPlatform("windows")]   // Quantower runs on Windows (GDI+ drawing)

namespace SweepPlan
{
    public class SweepPlanIndicator : Indicator
    {
        private string root;
        private Rectangle rearmBox = Rectangle.Empty;
        private string rearmKey = "";

        public SweepPlanIndicator() : base()
        {
            Name = "Sweep Plan";
            Description = "Your Sweep plan on the chart: levels, zones and alerts. Reminders only: it never places an order.";
            SeparateWindow = false;
            OnBackGround = true;       // behind the candles
            AllowFitAuto = false;      // never changes the chart's price scale
            UpdateType = IndicatorUpdateType.OnTick;
        }

        protected override void OnInit()
        {
            Release();
            if (Symbol == null) return;
            root = Roots.Root(Symbol.Name, Symbol.Root);
            PlanHost.Register(root);
            if (CurrentChart != null) CurrentChart.MouseDown += OnMouseDown;
        }

        protected override void OnUpdate(UpdateArgs args)
        {
            if (root == null || Symbol == null || args.Reason == UpdateReason.HistoricalBar) return;
            double price = Symbol.Last;
            if (double.IsNaN(price) || price <= 0) price = Close(0);
            PlanHost.Price(root, price, DateTime.UtcNow, Tick());
        }

        private double Tick()
        {
            try { double t = Symbol.GetTickSize(Symbol.Last); if (t > 0 && !double.IsNaN(t)) return t; } catch (Exception) { }
            return 0.25;
        }

        public override void OnPaintChart(PaintChartEventArgs args)
        {
            base.OnPaintChart(args);
            if (root == null || CurrentChart == null) return;
            PlanHost.View v = PlanHost.Snapshot(root);
            try
            {
                Graphics g = args.Graphics;
                var w = CurrentChart.MainWindow;
                Rectangle r = w.ClientRectangle;
                using (Font font = new Font("Segoe UI", 8f, FontStyle.Regular))
                {
                    if (v.Plan != null)
                        foreach (Zone z in v.Plan.Zones) DrawZone(g, w, r, z, font);
                    DrawBanner(g, r, v, font);
                }
            }
            catch (Exception ex) { PlanHost.Log("paint: " + ex.Message); }
        }

        private static Color RoleColor(string role, int alpha)
        {
            // Sweep's colors: a gain blue, a loss gold, the rest neutral grey
            if (role == "target") return Color.FromArgb(alpha, 0x4C, 0x8D, 0xFF);
            if (role == "invalidation") return Color.FromArgb(alpha, 0xD4, 0xA2, 0x4C);
            return Color.FromArgb(alpha, 0x8E, 0x8E, 0x93);
        }

        private void DrawZone(Graphics g, TradingPlatform.BusinessLayer.Chart.IChartWindow w, Rectangle r, Zone z, Font font)
        {
            int yTop = (int)Math.Round(w.CoordinatesConverter.GetChartY(z.Top));
            int yBottom = (int)Math.Round(w.CoordinatesConverter.GetChartY(z.Bottom));
            if (Math.Max(yTop, yBottom) < r.Top - 2 || Math.Min(yTop, yBottom) > r.Bottom + 2) return;   // off screen
            Color line = RoleColor(z.Role, 150);
            using (Pen pen = new Pen(line, 1f))
            {
                if (z.IsZone)
                {
                    int top = Math.Min(yTop, yBottom), h = Math.Max(1, Math.Abs(yBottom - yTop));
                    using (SolidBrush fill = new SolidBrush(RoleColor(z.Role, 28))) g.FillRectangle(fill, r.Left, top, r.Width, h);
                    g.DrawLine(pen, r.Left, top, r.Right, top);
                    g.DrawLine(pen, r.Left, top + h, r.Right, top + h);
                }
                else
                {
                    pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
                    g.DrawLine(pen, r.Left, yTop, r.Right, yTop);
                }
            }
            string name = Texts.Name(z);
            SizeF sz = g.MeasureString(name, font);
            int y = Math.Min(yTop, yBottom) - (int)sz.Height - 1;
            if (y < r.Top) y = Math.Min(yTop, yBottom) + 2;
            using (SolidBrush text = new SolidBrush(RoleColor(z.Role, 220))) g.DrawString(name, font, text, r.Right - sz.Width - 8, y);
        }

        /// <summary>one line at the top of the chart: the last alert (with « Re-arm »), or what keeps the plan from showing</summary>
        private void DrawBanner(Graphics g, Rectangle r, PlanHost.View v, Font font)
        {
            rearmBox = Rectangle.Empty;
            rearmKey = "";
            string line = v.Banner;
            if (string.IsNullOrEmpty(line)) return;
            string rearm = v.BannerKey.Length > 0 ? "  ↺ " + Texts.Rearm(v.Lang) : "";
            SizeF s1 = g.MeasureString(line, font), s2 = rearm.Length > 0 ? g.MeasureString(rearm, font) : SizeF.Empty;
            int x = r.Left + 8, y = r.Top + 6, wd = (int)Math.Min(r.Width - 16, s1.Width + s2.Width + 14), ht = (int)s1.Height + 8;
            Color accent = v.BannerKind == "alert" ? Color.FromArgb(0x4C, 0x8D, 0xFF) : Color.FromArgb(0x8E, 0x8E, 0x93);
            using (SolidBrush bg = new SolidBrush(Color.FromArgb(215, 0x14, 0x14, 0x18))) g.FillRectangle(bg, x, y, wd, ht);
            using (SolidBrush bar = new SolidBrush(accent)) g.FillRectangle(bar, x, y, 3, ht);
            g.DrawString(line, font, Brushes.White, x + 9, y + 4);
            if (rearm.Length > 0)
            {
                using (SolidBrush blue = new SolidBrush(Color.FromArgb(0x4C, 0x8D, 0xFF))) g.DrawString(rearm, font, blue, x + 9 + s1.Width, y + 4);
                rearmBox = new Rectangle((int)(x + 9 + s1.Width), y, (int)s2.Width + 4, ht);
                rearmKey = v.BannerKey;
            }
        }

        private void OnMouseDown(object sender, TradingPlatform.BusinessLayer.Chart.ChartMouseNativeEventArgs e)
        {
            if (rearmBox.IsEmpty || root == null || !rearmBox.Contains(e.Location)) return;
            PlanHost.Rearm(root, rearmKey);
            e.Handled = true;
        }

        private void Release()
        {
            if (CurrentChart != null) CurrentChart.MouseDown -= OnMouseDown;
            if (root != null) PlanHost.Unregister(root);
            root = null;
        }

        public override void Dispose()
        {
            Release();
            base.Dispose();
        }
    }

    /// <summary>
    /// One for all the charts: an engine per instrument root, the polls, the alerts, the events for Sweep, the files. The network
    /// runs on its own timer, never on Quantower's drawing or price threads.
    /// </summary>
    public static class PlanHost
    {
        public const string Version = "1.0.0";
        private const string DefaultBase = "https://app.makeitsweep.com";
        private static readonly object Gate = new object();
        private static readonly HttpClient http = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
        private static readonly Dictionary<string, int> charts = new Dictionary<string, int>();        // root → open charts
        private static readonly Dictionary<string, Engine> engines = new Dictionary<string, Engine>();
        private static readonly Dictionary<string, DateTime> nextPoll = new Dictionary<string, DateTime>();
        private static readonly Dictionary<string, double> ticks = new Dictionary<string, double>();
        private static readonly Dictionary<string, string> noPlanSaid = new Dictionary<string, string>(); // root → day the « no plan » showed
        private static readonly HashSet<string> fired = new HashSet<string>();
        private static readonly List<string> events = new List<string>();
        private static System.Threading.Timer timer;
        private static int busy;
        private static bool flushNow;
        private static DateTime nextFlush = DateTime.MinValue, retryAt = DateTime.MinValue;
        private static int failures;
        private static string key = "", baseUrl = DefaultBase, status = "";   // status: "", "nokey", "key", "offline"
        private static string lang = Texts.Lang(CultureInfo.CurrentUICulture.TwoLetterISOLanguageName);   // Windows' until Sweep's comes with the plan
        private static string keyMessage = "";
        private static Alert lastAlert;
        private static DateTime lastAlertAt = DateTime.MinValue, statusShownUntil = DateTime.MinValue;

        public class View
        {
            public Plan Plan;
            public string Banner = "", BannerKey = "", BannerKind = "", Lang = "en";
        }

        private static string Folder
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SweepSync", "Quantower"); }
        }

        public static void Register(string root)
        {
            bool start = false;
            lock (Gate)
            {
                int n;
                charts[root] = charts.TryGetValue(root, out n) ? n + 1 : 1;
                if (!engines.ContainsKey(root))
                {
                    Engine e = new Engine(root, fired);
                    e.SetPlan(LoadPlan(root));   // the last plan received, until Sweep answers
                    engines[root] = e;
                }
                nextPoll[root] = DateTime.MinValue;   // read now
                if (timer == null) { start = true; }
            }
            if (start)
            {
                LoadFiles();
                lock (Gate) if (timer == null) timer = new System.Threading.Timer(_ => Tick(), null, 300, 1000);
            }
        }

        public static void Unregister(string root)
        {
            lock (Gate)
            {
                int n;
                if (!charts.TryGetValue(root, out n)) return;
                if (n <= 1) charts.Remove(root); else charts[root] = n - 1;   // no chart left: no more polls for it
            }
        }

        public static void Price(string root, double price, DateTime utc, double tick)
        {
            List<Alert> a;
            lock (Gate)
            {
                Engine e;
                if (!engines.TryGetValue(root, out e)) return;
                ticks[root] = tick;
                a = e.OnPrice(price, utc, tick);
            }
            Show(a);
        }

        public static void Rearm(string root, string k)
        {
            lock (Gate)
            {
                Engine e;
                if (engines.TryGetValue(root, out e)) e.Rearm(k);
                if (lastAlert != null && lastAlert.Key == k) lastAlert = null;
            }
            SaveFired();
        }

        public static View Snapshot(string root)
        {
            View v = new View();
            lock (Gate)
            {
                Engine e;
                if (engines.TryGetValue(root, out e)) v.Plan = e.Plan;
                v.Lang = lang;
                DateTime now = DateTime.UtcNow;
                if (status == "nokey") { v.Banner = Texts.NoKey(lang); v.BannerKind = "status"; }
                else if (status == "key") { v.Banner = keyMessage; v.BannerKind = "status"; }
                else if (lastAlert != null && lastAlert.Instrument == root && now - lastAlertAt < TimeSpan.FromMinutes(2))
                {
                    v.Banner = lastAlert.Text; v.BannerKey = lastAlert.Key; v.BannerKind = "alert";
                }
                else if (status == "offline" && now < statusShownUntil) { v.Banner = Texts.Offline(lang); v.BannerKind = "status"; }
                else if (v.Plan != null && v.Plan.Empty && now < statusShownUntil) { v.Banner = Texts.NoPlan(lang); v.BannerKind = "status"; }
            }
            return v;
        }

        /// <summary>each second: the clock for every engine; the polls (every 15 s, open charts only); the events</summary>
        private static void Tick()
        {
            if (Interlocked.Exchange(ref busy, 1) == 1) return;
            try
            {
                List<Alert> a = new List<Alert>();
                List<string> due = new List<string>();
                DateTime now = DateTime.UtcNow;
                lock (Gate)
                {
                    foreach (KeyValuePair<string, Engine> kv in engines)
                    {
                        double t;
                        a.AddRange(kv.Value.OnClock(now, ticks.TryGetValue(kv.Key, out t) ? t : 0.25));
                    }
                    foreach (string r in charts.Keys) { DateTime at; if (!nextPoll.TryGetValue(r, out at) || now >= at) due.Add(r); }
                }
                Show(a);
                if (now >= retryAt) foreach (string r in due) Poll(r);
                bool send;
                lock (Gate) send = events.Count > 0 && now >= retryAt && (flushNow || now >= nextFlush);
                if (send) Flush();
            }
            catch (Exception ex) { Log("tick: " + ex.Message); }
            finally { Interlocked.Exchange(ref busy, 0); }
        }

        private static void Poll(string root)
        {
            LoadConfig();
            string k, etag;
            lock (Gate)
            {
                nextPoll[root] = DateTime.UtcNow.AddSeconds(15);
                k = key;
                Engine e;
                etag = engines.TryGetValue(root, out e) && e.Plan != null && e.Plan.Version.Length > 0 ? e.Plan.Version : "";
            }
            if (k.Length == 0) { lock (Gate) status = "nokey"; return; }
            try
            {
                using (HttpRequestMessage req = new HttpRequestMessage(HttpMethod.Get, baseUrl + "/api/plan-sync/today?instrument=" + Uri.EscapeDataString(root)))
                {
                    Headers(req, k);
                    if (etag.Length > 0) req.Headers.TryAddWithoutValidation("If-None-Match", "\"" + etag + "\"");
                    using (HttpResponseMessage r = http.SendAsync(req).GetAwaiter().GetResult())
                    {
                        int code = (int)r.StatusCode;
                        string body = code == 304 ? "" : r.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                        lock (Gate)
                        {
                            if (code == 304) { Ok(); return; }
                            if (code == 200)
                            {
                                Plan p = Plan.Parse(body);
                                if (p == null) { Log("plan: unreadable answer"); return; }
                                Engine e;
                                if (engines.TryGetValue(root, out e)) e.SetPlan(p);
                                lang = p.Lang;
                                string said;
                                if (p.Empty && (!noPlanSaid.TryGetValue(root, out said) || said != p.Day)) { noPlanSaid[root] = p.Day; statusShownUntil = DateTime.UtcNow.AddSeconds(12); }   // said once a day
                                Ok();
                                SavePlan(root, body);
                                return;
                            }
                            if (code == 401) { KeyRefused(body); return; }
                            if (code == 429) { retryAt = DateTime.UtcNow.AddSeconds(60); return; }
                            Offline();
                        }
                    }
                }
            }
            catch (Exception ex) { Log("plan: " + ex.Message); lock (Gate) Offline(); }
        }

        private static void Ok()
        {
            if (status == "offline" || status == "key" || status == "nokey") status = "";
            failures = 0;
        }

        private static void Offline()
        {
            if (status != "offline") statusShownUntil = DateTime.UtcNow.AddSeconds(12);
            status = "offline";
            failures++;
            retryAt = DateTime.UtcNow.AddSeconds(Math.Min(300, 15 * Math.Pow(2, Math.Min(failures - 1, 5))));
        }

        /// <summary>a 401: the server's message in the trader's language (a revoked key, or a NinjaTrader key)</summary>
        private static void KeyRefused(string body)
        {
            status = "key";
            Dictionary<string, object> o = Json.Parse(body) as Dictionary<string, object>;
            Dictionary<string, object> m = Json.Get(o, "messages") as Dictionary<string, object>;
            string s = Json.Str(m, lang);
            keyMessage = "Sweep Plan: " + (s.Length > 0 ? s : Json.Str(o, "error"));
            retryAt = DateTime.UtcNow.AddMinutes(1);   // a new key pasted in the panel is read at the next poll
        }

        private static void Headers(HttpRequestMessage req, string k)
        {
            req.Headers.TryAddWithoutValidation("X-Sweep-Key", k);
            req.Headers.TryAddWithoutValidation("X-Sweep-Client", "Sweep Quantower Plan " + Version);   // « Sweep Quantower… »: a Quantower key only
            req.Headers.TryAddWithoutValidation("User-Agent", "SweepPlan-Quantower/" + Version);
        }

        /// <summary>the alerts: Quantower's own (window and sound, as the trader set Quantower's alerts), the chart's banner, the event</summary>
        private static void Show(List<Alert> a)
        {
            if (a == null || a.Count == 0) return;
            foreach (Alert x in a)
            {
                try { Core.Instance.Alert(x.Text, x.Instrument, "", null, "Sweep Plan"); }
                catch (Exception ex) { Log("alert: " + ex.Message); }
                lock (Gate)
                {
                    lastAlert = x;
                    lastAlertAt = DateTime.UtcNow;
                    events.Add(Events.Json(x));
                    flushNow = true;
                }
            }
            SaveFired();
            SaveEvents();
        }

        private static void Flush()
        {
            string k, body;
            int n;
            lock (Gate)
            {
                flushNow = false;
                nextFlush = DateTime.UtcNow.AddSeconds(30);
                k = key;
                n = Math.Min(100, events.Count);
                body = Events.Body(events, n);
            }
            if (k.Length == 0) return;
            int code = 0;
            try
            {
                using (HttpRequestMessage req = new HttpRequestMessage(HttpMethod.Post, baseUrl + "/api/plan-sync/events"))
                {
                    Headers(req, k);
                    req.Content = new StringContent(body, Encoding.UTF8, "application/json");
                    using (HttpResponseMessage r = http.SendAsync(req).GetAwaiter().GetResult()) code = (int)r.StatusCode;
                }
            }
            catch (Exception ex) { Log("events: " + ex.Message); }
            lock (Gate)
            {
                if (code == 200 || code == 400 || code == 413) events.RemoveRange(0, Math.Min(n, events.Count));   // sent, or never acceptable: not again
                else if (code == 401) status = "key";
                else if (code == 429) retryAt = DateTime.UtcNow.AddSeconds(60);
                else Offline();   // kept, sent again later
            }
            SaveEvents();
        }

        /* ---------- files (%LocalAppData%\SweepSync\Quantower, next to the panel's) ---------- */

        /// <summary>the panel's key and server (config.txt): read again at each poll, so a key pasted in the panel works at once</summary>
        private static void LoadConfig()
        {
            try
            {
                string cfg = Path.Combine(Folder, "config.txt"), k = "", b = DefaultBase;
                if (File.Exists(cfg))
                    foreach (string line in File.ReadAllLines(cfg))
                    {
                        if (line.StartsWith("key=")) k = line.Substring(4).Trim();
                        else if (line.StartsWith("url=") && line.Length > 4)   // tests only: another Sweep server (the panel's push address)
                        {
                            string u = line.Substring(4).Trim();
                            int i = u.IndexOf("/api/", StringComparison.Ordinal);
                            b = i > 0 ? u.Substring(0, i) : u.TrimEnd('/');
                        }
                    }
                lock (Gate)
                {
                    if (k != key && status == "key") { status = ""; retryAt = DateTime.MinValue; }
                    key = k; baseUrl = b;
                    if (k.Length > 0 && status == "nokey") status = "";
                }
            }
            catch (Exception ex) { Log("config: " + ex.Message); }
        }

        private static void LoadFiles()
        {
            LoadConfig();
            try
            {
                string f = Path.Combine(Folder, "fired.txt"), today = Engine.DayOf(DateTime.UtcNow);
                if (File.Exists(f))
                    lock (Gate)
                        foreach (string line in File.ReadAllLines(f))
                            if (line.StartsWith(today + "|", StringComparison.Ordinal)) fired.Add(line.Trim());   // only today's
                string q = Path.Combine(Folder, "events.txt");
                if (File.Exists(q))
                    lock (Gate)
                        foreach (string line in File.ReadAllLines(q)) if (line.StartsWith("{", StringComparison.Ordinal) && events.Count < 2000) events.Add(line);
            }
            catch (Exception ex) { Log("load: " + ex.Message); }
        }

        private static Plan LoadPlan(string root)
        {
            try
            {
                string f = Path.Combine(Folder, "plan-" + Safe(root) + ".json");
                if (!File.Exists(f)) return null;
                Plan p = Plan.Parse(File.ReadAllText(f, Encoding.UTF8));
                return p != null && p.Day == Engine.DayOf(DateTime.UtcNow) ? p : null;   // another day's plan is not today's
            }
            catch (Exception) { return null; }
        }

        private static void SavePlan(string root, string body)
        {
            Write(Path.Combine(Folder, "plan-" + Safe(root) + ".json"), new List<string> { body });
        }

        private static void SaveFired()
        {
            List<string> lines;
            lock (Gate) lines = fired.ToList();
            Write(Path.Combine(Folder, "fired.txt"), lines);
        }

        private static void SaveEvents()
        {
            List<string> lines;
            lock (Gate) lines = events.ToList();
            Write(Path.Combine(Folder, "events.txt"), lines);
        }

        private static string Safe(string s)
        {
            StringBuilder b = new StringBuilder();
            foreach (char c in s ?? "") if (char.IsLetterOrDigit(c)) b.Append(c);
            return b.Length > 0 ? b.ToString() : "X";
        }

        private static readonly object FileGate = new object();
        private static void Write(string path, List<string> lines)
        {
            try
            {
                lock (FileGate)
                {
                    Directory.CreateDirectory(Folder);
                    string tmp = path + ".tmp";
                    File.WriteAllLines(tmp, lines, new UTF8Encoding(false));
                    File.Move(tmp, path, true);
                }
            }
            catch (Exception ex) { Log("file: " + ex.Message); }
        }

        public static void Log(string text)
        {
            try { Core.Instance.Loggers.Log("Sweep Plan: " + text); } catch (Exception) { }
        }
    }
}
