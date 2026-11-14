#region Using declarations
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.AddOns;
using SP = SweepPlanSync;
#endregion

// Sweep Plan — Plan Sync on NinjaTrader 8 (BRIEF_PLAN_SYNC, step 4, 14 Nov. 2026): an indicator the trader adds to a chart. It
// draws the day's plan made in Sweep (levels as dashed lines, zones as light rectangles, behind the bars, with their names) and
// alerts in NinjaTrader's Alerts window, with a sound, when price reaches them or a rule of the plan happens (approach, enter,
// close above / below, sweep, a New York time). The triggers are evaluated here, on NinjaTrader's prices, by the logic shared with
// Quantower (AddOns/SweepPlanCore.cs = sync/addon/plan/PlanCore.cs): no call to Sweep to evaluate, no market data sent to Sweep.
// It never places, changes or cancels an order.
//  - the same key and server as the Sweep Sync add-on (SweepSyncEngine, compiled in the same NinjaScript assembly);
//  - the plan is read when a chart of the instrument opens, then every 15 s while one is open (If-None-Match: almost always 304);
//  - each alert at most once per trading day, even with several charts of the instrument (one engine per instrument root: MNQ
//    reads NQ); kept across restarts (fired.txt); the chart's banner can re-arm the last one;
//  - what alerted is sent to Sweep (api/plan-sync/events) every 30 s or right away, kept in events.txt while Sweep is unreachable;
//  - Sweep unreachable: the last plan received (plan-<root>.json) stays drawn and its alerts go on.
// Files: Documents\NinjaTrader 8\SweepSync\plan\ (next to Sweep Sync's own).
namespace NinjaTrader.NinjaScript.Indicators
{
	public class SweepPlan : Indicator
	{
		private string root;
		private bool registered;
		private System.Threading.Timer repaint;
		private int seen = -1;
		private SharpDX.RectangleF rearmBox;
		private string rearmKey = "";

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Name = "Sweep Plan";
				Description = "Your Sweep plan on the chart: levels, zones and alerts. Reminders only: it never places an order.";
				Calculate = Calculate.OnEachTick;
				IsOverlay = true;
				DisplayInDataBox = false;
				DrawOnPricePanel = true;
				PaintPriceMarkers = false;
				IsAutoScale = false;                  // never changes the chart's price scale
				IsSuspendedWhileInactive = false;     // a chart in the background still alerts
			}
			else if (State == State.DataLoaded)
			{
				if (ChartControl == null || Instrument == null || Instrument.MasterInstrument == null) return;   // a chart only
				root = SP.Roots.Root(Instrument.FullName, Instrument.MasterInstrument.Name);
				SweepPlanHost.Register(root, Instrument, this);
				registered = true;
				ChartControl.Dispatcher.InvokeAsync(new Action(() => { if (ChartControl != null) ChartControl.PreviewMouseLeftButtonDown += OnMouseDown; }));
				// the chart is drawn again when the plan or the banner changes, even with no new price (a closed market)
				repaint = new System.Threading.Timer(_ => { int v = SweepPlanHost.Changes; if (v != seen) { seen = v; try { ForceRefresh(); } catch (Exception) { } } }, null, 1000, 1000);
			}
			else if (State == State.Historical)
				SetZOrder(-1);   // behind the bars
			else if (State == State.Terminated)
			{
				if (repaint != null) { repaint.Dispose(); repaint = null; }
				if (ChartControl != null) ChartControl.Dispatcher.InvokeAsync(new Action(() => { if (ChartControl != null) ChartControl.PreviewMouseLeftButtonDown -= OnMouseDown; }));
				if (registered) SweepPlanHost.Unregister(root, this);
				registered = false;
			}
		}

		protected override void OnBarUpdate()
		{
			if (!registered || State != State.Realtime || CurrentBar < 0) return;
			SweepPlanHost.Price(root, Close[0], DateTime.UtcNow, TickSize);
		}

		private static SharpDX.Color4 RoleColor(string role, float alpha)
		{
			// Sweep's colors: a gain blue, a loss gold, the rest neutral grey
			if (role == "target") return new SharpDX.Color4(0x4C / 255f, 0x8D / 255f, 0xFF / 255f, alpha);
			if (role == "invalidation") return new SharpDX.Color4(0xD4 / 255f, 0xA2 / 255f, 0x4C / 255f, alpha);
			return new SharpDX.Color4(0x8E / 255f, 0x8E / 255f, 0x93 / 255f, alpha);
		}

		protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
		{
			base.OnRender(chartControl, chartScale);
			rearmBox = new SharpDX.RectangleF();
			rearmKey = "";
			if (!registered || RenderTarget == null || ChartPanel == null) return;
			SweepPlanHost.View v = SweepPlanHost.Snapshot(root);
			try
			{
				using (SharpDX.DirectWrite.TextFormat font = new SharpDX.DirectWrite.TextFormat(NinjaTrader.Core.Globals.DirectWriteFactory, "Segoe UI", 11f))
				{
					if (v.Plan != null)
						foreach (SP.Zone z in v.Plan.Zones) DrawZone(chartScale, z, font);
					DrawBanner(v, font);
				}
			}
			catch (Exception ex) { SweepPlanHost.Log("render: " + ex.Message); }
		}

		private void DrawZone(ChartScale scale, SP.Zone z, SharpDX.DirectWrite.TextFormat font)
		{
			float left = ChartPanel.X, right = ChartPanel.X + ChartPanel.W, top = ChartPanel.Y, bottom = ChartPanel.Y + ChartPanel.H;
			float yTop = scale.GetYByValue(z.Top), yBottom = scale.GetYByValue(z.Bottom);
			if (Math.Max(yTop, yBottom) < top - 2 || Math.Min(yTop, yBottom) > bottom + 2) return;   // off screen
			float y0 = Math.Min(yTop, yBottom), h = Math.Max(1f, Math.Abs(yBottom - yTop));
			using (SharpDX.Direct2D1.SolidColorBrush line = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, RoleColor(z.Role, 0.6f)))
			{
				if (z.IsZone)
				{
					using (SharpDX.Direct2D1.SolidColorBrush fill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, RoleColor(z.Role, 0.11f)))
						RenderTarget.FillRectangle(new SharpDX.RectangleF(left, y0, right - left, h), fill);
					RenderTarget.DrawLine(new SharpDX.Vector2(left, y0), new SharpDX.Vector2(right, y0), line, 1f);
					RenderTarget.DrawLine(new SharpDX.Vector2(left, y0 + h), new SharpDX.Vector2(right, y0 + h), line, 1f);
				}
				else
				{
					SharpDX.Direct2D1.StrokeStyleProperties sp = new SharpDX.Direct2D1.StrokeStyleProperties();
					sp.DashStyle = SharpDX.Direct2D1.DashStyle.Dash;
					using (SharpDX.Direct2D1.StrokeStyle dash = new SharpDX.Direct2D1.StrokeStyle(RenderTarget.Factory, sp))
						RenderTarget.DrawLine(new SharpDX.Vector2(left, y0), new SharpDX.Vector2(right, y0), line, 1f, dash);
				}
			}
			string name = SP.Texts.Name(z);
			using (SharpDX.DirectWrite.TextLayout tl = new SharpDX.DirectWrite.TextLayout(NinjaTrader.Core.Globals.DirectWriteFactory, name, font, 400f, 30f))
			using (SharpDX.Direct2D1.SolidColorBrush text = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, RoleColor(z.Role, 0.86f)))
			{
				float w = tl.Metrics.Width, th = tl.Metrics.Height;
				float y = y0 - th - 1;
				if (y < top) y = y0 + h + 2;
				RenderTarget.DrawTextLayout(new SharpDX.Vector2(right - w - 8, y), tl, text, SharpDX.Direct2D1.DrawTextOptions.NoSnap);
			}
		}

		/// <summary>one line at the top of the chart: the last alert (with « Re-arm »), or what keeps the plan from showing</summary>
		private void DrawBanner(SweepPlanHost.View v, SharpDX.DirectWrite.TextFormat font)
		{
			if (string.IsNullOrEmpty(v.Banner)) return;
			string rearm = v.BannerKey.Length > 0 ? "  ↺ " + SP.Texts.Rearm(v.Lang) : "";
			float x = ChartPanel.X + 8, y = ChartPanel.Y + 6;
			using (SharpDX.DirectWrite.TextLayout t1 = new SharpDX.DirectWrite.TextLayout(NinjaTrader.Core.Globals.DirectWriteFactory, v.Banner, font, Math.Max(100f, ChartPanel.W - 40f), 40f))
			using (SharpDX.DirectWrite.TextLayout t2 = new SharpDX.DirectWrite.TextLayout(NinjaTrader.Core.Globals.DirectWriteFactory, rearm, font, 200f, 40f))
			using (SharpDX.Direct2D1.SolidColorBrush bg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0x14 / 255f, 0x14 / 255f, 0x18 / 255f, 0.84f)))
			using (SharpDX.Direct2D1.SolidColorBrush white = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(1f, 1f, 1f, 1f)))
			using (SharpDX.Direct2D1.SolidColorBrush blue = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0x4C / 255f, 0x8D / 255f, 0xFF / 255f, 1f)))
			using (SharpDX.Direct2D1.SolidColorBrush grey = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0x8E / 255f, 0x8E / 255f, 0x93 / 255f, 1f)))
			{
				float w1 = t1.Metrics.Width, w2 = rearm.Length > 0 ? t2.Metrics.Width : 0f, ht = t1.Metrics.Height + 8;
				float wd = Math.Min(ChartPanel.W - 16, w1 + w2 + 14);
				RenderTarget.FillRectangle(new SharpDX.RectangleF(x, y, wd, ht), bg);
				RenderTarget.FillRectangle(new SharpDX.RectangleF(x, y, 3, ht), v.BannerKind == "alert" ? blue : grey);
				RenderTarget.DrawTextLayout(new SharpDX.Vector2(x + 9, y + 4), t1, white, SharpDX.Direct2D1.DrawTextOptions.NoSnap);
				if (rearm.Length > 0)
				{
					RenderTarget.DrawTextLayout(new SharpDX.Vector2(x + 9 + w1, y + 4), t2, blue, SharpDX.Direct2D1.DrawTextOptions.NoSnap);
					rearmBox = new SharpDX.RectangleF(x + 9 + w1, y, w2 + 4, ht);
					rearmKey = v.BannerKey;
				}
			}
		}

		/// <summary>« Re-arm » touched on the banner: that alert can show again today</summary>
		private void OnMouseDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
		{
			if (rearmKey.Length == 0 || ChartControl == null || !registered) return;
			System.Windows.Point p = e.GetPosition(ChartControl as System.Windows.IInputElement);
			float x = ChartingExtensions.ConvertToHorizontalPixels(p.X, ChartControl.PresentationSource);
			float y = ChartingExtensions.ConvertToVerticalPixels(p.Y, ChartControl.PresentationSource);
			if (x < rearmBox.Left || x > rearmBox.Right || y < rearmBox.Top || y > rearmBox.Bottom) return;
			SweepPlanHost.Rearm(root, rearmKey);
			e.Handled = true;
			ForceRefresh();
		}
	}
}

namespace NinjaTrader.NinjaScript.AddOns
{
	/// <summary>
	/// One for all the charts: an engine per instrument root, the polls, the alerts, the events for Sweep, the files. The network
	/// runs on its own timer, never on NinjaTrader's drawing or price threads.
	/// </summary>
	public static class SweepPlanHost
	{
		public const string Version = "1.0.0";
		private const string DefaultBase = "https://app.makeitsweep.com";
		private static readonly object Gate = new object();
		private static readonly Dictionary<string, List<object>> charts = new Dictionary<string, List<object>>();   // root → its indicators
		private static readonly Dictionary<string, Instrument> instruments = new Dictionary<string, Instrument>();
		private static readonly Dictionary<string, SP.Engine> engines = new Dictionary<string, SP.Engine>();
		private static readonly Dictionary<string, DateTime> nextPoll = new Dictionary<string, DateTime>();
		private static readonly Dictionary<string, double> ticks = new Dictionary<string, double>();
		private static readonly Dictionary<string, string> noPlanSaid = new Dictionary<string, string>();   // root → day the « no plan » showed
		private static readonly HashSet<string> fired = new HashSet<string>();
		private static readonly List<string> events = new List<string>();
		private static System.Threading.Timer timer;
		private static int busy, changes;
		private static bool flushNow;
		private static DateTime nextFlush = DateTime.MinValue, retryAt = DateTime.MinValue;
		private static int failures;
		private static string key = "", baseUrl = DefaultBase, status = "";   // status: "", "nokey", "key", "offline"
		private static string lang = SP.Texts.Lang(CultureInfo.CurrentUICulture.TwoLetterISOLanguageName);   // Windows' until Sweep's comes with the plan
		private static string keyMessage = "";
		private static SP.Alert lastAlert;
		private static DateTime lastAlertAt = DateTime.MinValue, statusShownUntil = DateTime.MinValue;
		private static Brush alertBack, alertFore;

		public class View
		{
			public SP.Plan Plan;
			public string Banner = "", BannerKey = "", BannerKind = "", Lang = "en";
		}

		/// <summary>grows each time what the charts show changes (a plan, the banner): the charts draw again</summary>
		public static int Changes { get { return Interlocked.CompareExchange(ref changes, 0, 0); } }
		private static void Changed() { Interlocked.Increment(ref changes); }

		private static string Folder
		{
			get
			{
				string t = Environment.GetEnvironmentVariable("SWEEP_PLAN_TEST_DIR");   // tests only (tests/ninjatrader_plan_test.py)
				if (!string.IsNullOrEmpty(t)) return t;
				return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "NinjaTrader 8", "SweepSync", "plan");
			}
		}

		public static void Register(string root, Instrument instrument, object chart)
		{
			bool start = false;
			lock (Gate)
			{
				List<object> l;
				if (!charts.TryGetValue(root, out l)) { l = new List<object>(); charts[root] = l; }
				if (!l.Contains(chart)) l.Add(chart);
				if (!instruments.ContainsKey(root)) instruments[root] = instrument;
				if (!engines.ContainsKey(root))
				{
					SP.Engine e = new SP.Engine(root, fired);
					e.SetPlan(LoadPlan(root));   // the last plan received, until Sweep answers
					engines[root] = e;
				}
				nextPoll[root] = DateTime.MinValue;   // read now
				if (timer == null) start = true;
			}
			if (start)
			{
				LoadFiles();
				lock (Gate) if (timer == null) timer = new System.Threading.Timer(_ => Tick(), null, 300, 1000);
			}
			Changed();
		}

		public static void Unregister(string root, object chart)
		{
			lock (Gate)
			{
				List<object> l;
				if (root == null || !charts.TryGetValue(root, out l)) return;
				l.Remove(chart);
				if (l.Count == 0) charts.Remove(root);   // no chart left: no more polls for it (its engine and plan stay for the day)
			}
		}

		public static void Price(string root, double price, DateTime utc, double tick)
		{
			List<SP.Alert> a;
			lock (Gate)
			{
				SP.Engine e;
				if (root == null || !engines.TryGetValue(root, out e)) return;
				ticks[root] = tick;
				a = e.OnPrice(price, utc, tick);
			}
			Show(a);
		}

		public static void Rearm(string root, string k)
		{
			lock (Gate)
			{
				SP.Engine e;
				if (engines.TryGetValue(root, out e)) e.Rearm(k);
				if (lastAlert != null && lastAlert.Key == k) lastAlert = null;
			}
			SaveFired();
			Changed();
		}

		public static View Snapshot(string root)
		{
			View v = new View();
			lock (Gate)
			{
				SP.Engine e;
				if (root != null && engines.TryGetValue(root, out e)) v.Plan = e.Plan;
				v.Lang = lang;
				DateTime now = DateTime.UtcNow;
				if (status == "nokey") { v.Banner = SP.Texts.NoKeyNinja(lang); v.BannerKind = "status"; }
				else if (status == "key") { v.Banner = keyMessage; v.BannerKind = "status"; }
				else if (lastAlert != null && lastAlert.Instrument == root && now - lastAlertAt < TimeSpan.FromMinutes(2))
				{
					v.Banner = lastAlert.Text; v.BannerKey = lastAlert.Key; v.BannerKind = "alert";
				}
				else if (status == "offline" && now < statusShownUntil) { v.Banner = SP.Texts.Offline(lang); v.BannerKind = "status"; }
				else if (v.Plan != null && v.Plan.Empty && now < statusShownUntil) { v.Banner = SP.Texts.NoPlan(lang); v.BannerKind = "status"; }
			}
			return v;
		}

		/// <summary>each second: the clock for every engine; the polls (every 15 s, open charts only); the events</summary>
		private static void Tick()
		{
			if (Interlocked.Exchange(ref busy, 1) == 1) return;
			try
			{
				LoadConfig();   // Sweep Sync's key, read in memory each second: a key saved there works at once
				List<SP.Alert> a = new List<SP.Alert>();
				List<string> due = new List<string>();
				DateTime now = DateTime.UtcNow;
				bool banner;
				lock (Gate)
				{
					foreach (KeyValuePair<string, SP.Engine> kv in engines)
					{
						double t;
						a.AddRange(kv.Value.OnClock(now, ticks.TryGetValue(kv.Key, out t) ? t : 0.25));
					}
					foreach (string r in charts.Keys) { DateTime at; if (!nextPoll.TryGetValue(r, out at) || now >= at) due.Add(r); }
					// a banner that just expired: the charts draw again without it
					banner = (lastAlert != null && now - lastAlertAt >= TimeSpan.FromMinutes(2) && now - lastAlertAt < TimeSpan.FromMinutes(2) + TimeSpan.FromSeconds(1.5))
						|| (statusShownUntil != DateTime.MinValue && now >= statusShownUntil && now < statusShownUntil + TimeSpan.FromSeconds(1.5));
				}
				if (banner) Changed();
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
			string k, etag, b;
			lock (Gate)
			{
				nextPoll[root] = DateTime.UtcNow.AddSeconds(15);
				k = key; b = baseUrl;
				SP.Engine e;
				etag = engines.TryGetValue(root, out e) && e.Plan != null && e.Plan.Version.Length > 0 ? e.Plan.Version : "";
			}
			if (k.Length == 0) { lock (Gate) { if (status != "nokey") Changed(); status = "nokey"; } return; }
			string body;
			int code = Http("GET", b + "/api/plan-sync/today?instrument=" + Uri.EscapeDataString(root), k, null, etag, out body);
			lock (Gate)
			{
				if (code == 304) { Ok(); return; }
				if (code == 200)
				{
					SP.Plan p = SP.Plan.Parse(body);
					if (p == null) { Log("plan: unreadable answer"); return; }
					SP.Engine e;
					if (engines.TryGetValue(root, out e)) e.SetPlan(p);
					lang = p.Lang;
					string said;
					if (p.Empty && (!noPlanSaid.TryGetValue(root, out said) || said != p.Day)) { noPlanSaid[root] = p.Day; statusShownUntil = DateTime.UtcNow.AddSeconds(12); }   // said once a day
					Ok();
					SavePlan(root, body);
					Changed();
					return;
				}
				if (code == 401) { KeyRefused(body); return; }
				if (code == 429) { retryAt = DateTime.UtcNow.AddSeconds(60); return; }
				Offline();
			}
		}

		private static void Ok()
		{
			if (status == "offline" || status == "key" || status == "nokey") { status = ""; Changed(); }
			failures = 0;
		}

		private static void Offline()
		{
			if (status != "offline") statusShownUntil = DateTime.UtcNow.AddSeconds(12);
			status = "offline";
			failures++;
			retryAt = DateTime.UtcNow.AddSeconds(Math.Min(300, 15 * Math.Pow(2, Math.Min(failures - 1, 5))));
			Changed();
		}

		/// <summary>a 401: the server's message in the trader's language (a revoked key, or a Quantower key)</summary>
		private static void KeyRefused(string body)
		{
			status = "key";
			Dictionary<string, object> o = SP.Json.Parse(body) as Dictionary<string, object>;
			Dictionary<string, object> m = SP.Json.Get(o, "messages") as Dictionary<string, object>;
			string s = SP.Json.Str(m, lang);
			keyMessage = "Sweep Plan: " + (s.Length > 0 ? s : SP.Json.Str(o, "error"));
			retryAt = DateTime.UtcNow.AddMinutes(1);   // the same key again in a minute; a new key saved in Sweep Sync is tried at once
			Changed();
		}

		/// <summary>the alerts: NinjaTrader's Alerts window with a sound (once for all the charts), the chart's banner, the event</summary>
		private static void Show(List<SP.Alert> a)
		{
			if (a == null || a.Count == 0) return;
			foreach (SP.Alert x in a)
			{
				Instrument inst;
				object source = null;
				lock (Gate)
				{
					instruments.TryGetValue(x.Instrument, out inst);
					List<object> l;
					if (charts.TryGetValue(x.Instrument, out l) && l.Count > 0) source = l[0];
				}
				try
				{
					if (alertBack == null)
					{
						SolidColorBrush bk = new SolidColorBrush(Color.FromRgb(0x14, 0x2B, 0x52)); bk.Freeze();   // a dark Sweep blue
						SolidColorBrush fg = new SolidColorBrush(Colors.White); fg.Freeze();
						alertBack = bk; alertFore = fg;
					}
					NinjaTrader.NinjaScript.Alert.AlertCallback(inst, source ?? (object)"Sweep Plan", "SweepPlan." + x.Key, NinjaTrader.Core.Globals.Now, Priority.High,
						"Sweep Plan · " + x.Text, Path.Combine(NinjaTrader.Core.Globals.InstallDir, "sounds", "Alert2.wav"), alertBack, alertFore, 0);
				}
				catch (Exception ex) { Log("alert: " + ex.Message); }
				lock (Gate)
				{
					lastAlert = x;
					lastAlertAt = DateTime.UtcNow;
					events.Add(SP.Events.Json(x));
					flushNow = true;
				}
			}
			Changed();
			SaveFired();
			SaveEvents();
		}

		private static void Flush()
		{
			string k, body, b;
			int n;
			lock (Gate)
			{
				flushNow = false;
				nextFlush = DateTime.UtcNow.AddSeconds(30);
				k = key; b = baseUrl;
				n = Math.Min(100, events.Count);
				body = SP.Events.Body(events, n);
			}
			if (k.Length == 0) return;
			string answer;
			int code = Http("POST", b + "/api/plan-sync/events", k, body, "", out answer);
			lock (Gate)
			{
				if (code == 200 || code == 400 || code == 413) events.RemoveRange(0, Math.Min(n, events.Count));   // sent, or never acceptable: not again
				else if (code == 401) { status = "key"; Changed(); }
				else if (code == 429) retryAt = DateTime.UtcNow.AddSeconds(60);
				else Offline();   // kept, sent again later
			}
			SaveEvents();
		}

		/// <summary>one request to Sweep; the HTTP code (0: no answer) and the body</summary>
		private static int Http(string method, string url, string k, string json, string etag, out string body)
		{
			body = "";
			try
			{
				ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
				HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
				req.Method = method;
				req.UserAgent = "SweepPlan-NT8/" + Version;
				req.Timeout = 15000;
				req.ReadWriteTimeout = 15000;
				req.Headers["X-Sweep-Key"] = k;
				req.Headers["X-Sweep-Client"] = "Sweep NT8 Plan " + Version;   // « Sweep NT8… »: a NinjaTrader 8 key only
				if (etag.Length > 0) req.Headers["If-None-Match"] = "\"" + etag + "\"";
				if (json != null)
				{
					byte[] data = Encoding.UTF8.GetBytes(json);
					req.ContentType = "application/json";
					req.ContentLength = data.Length;
					using (Stream s = req.GetRequestStream()) s.Write(data, 0, data.Length);
				}
				using (HttpWebResponse r = (HttpWebResponse)req.GetResponse())
				{
					body = Read(r);
					return (int)r.StatusCode;
				}
			}
			catch (WebException we)
			{
				HttpWebResponse r = we.Response as HttpWebResponse;
				if (r == null) { Log("cannot reach Sweep: " + we.Status); return 0; }
				using (r)
				{
					int code = (int)r.StatusCode;
					if (code != 304) { try { body = Read(r); } catch (Exception) { } }
					return code;
				}
			}
			catch (Exception ex) { Log("request: " + ex.Message); return 0; }
		}

		private static string Read(HttpWebResponse r)
		{
			using (StreamReader rd = new StreamReader(r.GetResponseStream(), Encoding.UTF8)) return rd.ReadToEnd();
		}

		/* ---------- the key, and the files (Documents\NinjaTrader 8\SweepSync\plan) ---------- */

		/// <summary>Sweep Sync's key and server (its fields in memory: nothing read from disk)</summary>
		private static void LoadConfig()
		{
			string k = "", b = DefaultBase;
			try
			{
				k = SweepSyncEngine.Key ?? "";
				string u = SweepSyncEngine.Url ?? "";
				int i = u.IndexOf("/api/", StringComparison.Ordinal);
				if (i > 0) b = u.Substring(0, i);
			}
			catch (Exception ex) { Log("config: " + ex.Message); }
			lock (Gate)
			{
				if (k != key && status == "key") { status = ""; retryAt = DateTime.MinValue; Changed(); }
				key = k; baseUrl = b;
				if (k.Length > 0 && status == "nokey") { status = ""; Changed(); }
			}
		}

		private static void LoadFiles()
		{
			LoadConfig();
			try
			{
				string f = Path.Combine(Folder, "fired.txt"), today = SP.Engine.DayOf(DateTime.UtcNow);
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

		private static SP.Plan LoadPlan(string root)
		{
			try
			{
				string f = Path.Combine(Folder, "plan-" + Safe(root) + ".json");
				if (!File.Exists(f)) return null;
				SP.Plan p = SP.Plan.Parse(File.ReadAllText(f, Encoding.UTF8));
				return p != null && p.Day == SP.Engine.DayOf(DateTime.UtcNow) ? p : null;   // another day's plan is not today's
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
					if (File.Exists(path)) File.Delete(path);
					File.Move(tmp, path);
				}
			}
			catch (Exception ex) { Log("file: " + ex.Message); }
		}

		public static void Log(string text)
		{
			try { NinjaTrader.Code.Output.Process("Sweep Plan: " + text, PrintTo.OutputTab1); } catch (Exception) { }
		}
	}
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
	public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
	{
		private SweepPlan[] cacheSweepPlan;
		public SweepPlan SweepPlan()
		{
			return SweepPlan(Input);
		}

		public SweepPlan SweepPlan(ISeries<double> input)
		{
			if (cacheSweepPlan != null)
				for (int idx = 0; idx < cacheSweepPlan.Length; idx++)
					if (cacheSweepPlan[idx] != null &&  cacheSweepPlan[idx].EqualsInput(input))
						return cacheSweepPlan[idx];
			return CacheIndicator<SweepPlan>(new SweepPlan(), input, ref cacheSweepPlan);
		}
	}
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
	public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
	{
		public Indicators.SweepPlan SweepPlan()
		{
			return indicator.SweepPlan(Input);
		}

		public Indicators.SweepPlan SweepPlan(ISeries<double> input )
		{
			return indicator.SweepPlan(input);
		}
	}
}

namespace NinjaTrader.NinjaScript.Strategies
{
	public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
	{
		public Indicators.SweepPlan SweepPlan()
		{
			return indicator.SweepPlan(Input);
		}

		public Indicators.SweepPlan SweepPlan(ISeries<double> input )
		{
			return indicator.SweepPlan(input);
		}
	}
}

#endregion
