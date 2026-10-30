#region Using declarations
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
#endregion

// Sweep Sync — NinjaTrader 8 add-on of Sweep (app.makeitsweep.com).
// Sends every execution of every connected account to the trader's Sweep journal, with the trader's personal key.
// Read-only: it never places, changes or cancels an order. Besides the executions, only the accounts leave the computer: name,
// connection, currency and balance (so that Sweep's balance follows the platform). No password, no market data.
//  - every new or amended execution is queued (Documents\NinjaTrader 8\SweepSync\queue.txt, kept if NinjaTrader closes);
//  - the queue is sent every 2 seconds (500 executions at most per request); a « hello » every 5 minutes says the add-on runs;
//  - at start and when an account connects, the executions of its current session are sent again (Sweep never doubles them);
//  - times are sent in UTC (milliseconds), converted from the time zone set in Tools > Options > General;
//  - no connection: the executions wait and are sent later (waiting longer after each failure, 5 minutes at most).
namespace NinjaTrader.NinjaScript.AddOns
{
	public class SweepSync : AddOnBase
	{
		private NTMenuItem menuItem;
		private NTMenuItem newMenu;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Name = "Sweep Sync";
				Description = "Sends your executions to your Sweep journal. Read-only: never places an order.";
			}
			else if (State == State.Active)
				SweepSyncEngine.Start(this);
			else if (State == State.Terminated)
				SweepSyncEngine.Stop(this);
		}

		protected override void OnWindowCreated(Window window)
		{
			ControlCenter cc = window as ControlCenter;
			if (cc == null) return;
			SweepSyncEngine.Start(this);   // also here, in case this NinjaTrader version does not pass through State.Active
			newMenu = cc.FindFirst("ControlCenterMenuItemNew") as NTMenuItem;
			if (newMenu == null) return;
			menuItem = new NTMenuItem { Header = "Sweep Sync", Style = Application.Current.TryFindResource("MainMenuItem") as Style };
			newMenu.Items.Add(menuItem);
			menuItem.Click += OnMenuItemClick;
		}

		protected override void OnWindowDestroyed(Window window)
		{
			if (menuItem == null || !(window is ControlCenter)) return;
			if (newMenu != null && newMenu.Items.Contains(menuItem)) newMenu.Items.Remove(menuItem);
			menuItem.Click -= OnMenuItemClick;
			menuItem = null;
			newMenu = null;
		}

		private void OnMenuItemClick(object sender, RoutedEventArgs e)
		{
			Core.Globals.RandomDispatcher.InvokeAsync(new Action(() => new SweepSyncWindow().Show()));
		}
	}

	/// <summary>The sync itself: one instance for the whole platform (a recompile ends it and starts it again).</summary>
	public static class SweepSyncEngine
	{
		public const string Version = "1.1.0";
		private const string DefaultUrl = "https://app.makeitsweep.com/api/sync/push";
		private const int MaxPerPush = 500;
		private static readonly object Gate = new object();
		private static readonly Dictionary<string, string> pending = new Dictionary<string, string>();   // « account|execution id » → JSON
		private static readonly HashSet<string> sent = new HashSet<string>();                           // « key|JSON » accepted by Sweep
		private static readonly HashSet<Account> watched = new HashSet<Account>();
		private static object owner;
		private static System.Threading.Timer timer;
		private static int busy;
		private static int failures;
		private static DateTime retryAt = DateTime.MinValue;
		private static DateTime nextHello = DateTime.MinValue;

		public static string Key = "";
		public static string Url = DefaultUrl;
		public static DateTime LastOk = DateTime.MinValue;
		public static string LastError = "";   // "", "key", "network", "server", "error"

		public static int Pending { get { lock (Gate) return pending.Count; } }
		public static string[] Accounts { get { lock (Gate) return watched.Select(a => a.Name).OrderBy(n => n).ToArray(); } }

		private static string Folder
		{
			get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "NinjaTrader 8", "SweepSync"); }
		}

		public static void Start(object who)
		{
			lock (Gate)
			{
				if (owner != null) return;
				owner = who;
			}
			Load();
			Account.AccountStatusUpdate += OnAccountStatus;
			List<Account> all = new List<Account>();
			lock (Account.All) foreach (Account a in Account.All) all.Add(a);
			foreach (Account a in all) Watch(a);
			timer = new System.Threading.Timer(_ => Tick(), null, 2000, 2000);
		}

		public static void Stop(object who)
		{
			lock (Gate)
			{
				if (owner != who) return;
				owner = null;
			}
			Account.AccountStatusUpdate -= OnAccountStatus;
			if (timer != null) { timer.Dispose(); timer = null; }
			lock (Gate)
			{
				foreach (Account a in watched) a.ExecutionUpdate -= OnExecution;
				watched.Clear();
			}
		}

		/// <summary>A key pasted by the trader: kept, then every execution of the session is sent again with it.</summary>
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
			}
			SaveConfig();
			List<Account> list;
			lock (Gate) list = watched.ToList();
			foreach (Account a in list) AddSession(a);
			return true;
		}

		private static void OnAccountStatus(object sender, AccountStatusEventArgs e)
		{
			if (e.Status == ConnectionStatus.Connected) Watch(e.Account);
		}

		private static void Watch(Account a)
		{
			if (a == null) return;
			lock (Gate) { if (!watched.Add(a)) return; }
			a.ExecutionUpdate += OnExecution;
			AddSession(a);
		}

		private static void AddSession(Account a)
		{
			try
			{
				List<Execution> list = new List<Execution>();
				lock (a.Executions) foreach (Execution x in a.Executions) list.Add(x);
				foreach (Execution x in list) Add(x);
			}
			catch (Exception ex) { Log("session: " + ex.Message); }
		}

		private static void OnExecution(object sender, ExecutionEventArgs e)
		{
			Add(e.Execution);
		}

		private static void Add(Execution x)
		{
			try
			{
				if (x == null || x.Account == null || x.Instrument == null || string.IsNullOrEmpty(x.ExecutionId)) return;
				string id = x.ExecutionId, acct = x.Account.Name;
				string json = "{\"id\":" + J(id)
					+ ",\"account\":" + J(acct)
					+ ",\"contract\":" + J(x.Instrument.FullName)
					+ ",\"side\":\"" + (x.MarketPosition == MarketPosition.Long ? "buy" : "sell") + "\""
					+ ",\"qty\":" + x.Quantity.ToString(CultureInfo.InvariantCulture)
					+ ",\"price\":" + N(x.Price)
					+ ",\"ts\":" + Utc(x.Time).ToString(CultureInfo.InvariantCulture)
					+ ",\"fee\":" + N(x.Commission)
					+ ",\"point_value\":" + N(x.Instrument.MasterInstrument.PointValue) + "}";
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

		/// <summary>An execution time (in the time zone of Tools > Options > General) → UTC milliseconds.</summary>
		private static long Utc(DateTime t)
		{
			DateTime u;
			try
			{
				u = t.Kind == DateTimeKind.Utc ? t : TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo);
			}
			catch { u = t.ToUniversalTime(); }
			return (long)(u - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalMilliseconds;
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
				string body = "{\"client\":" + J("Sweep NT8 " + Version) + ",\"accounts\":[" + AccountsJson() + "],\"fills\":[" + string.Join(",", batch.Select(b => b.Value)) + "]}";
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
						LastError = "key";   // revoked or wrong key: wait for a new one
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

		/// <summary>What NinjaTrader says about the accounts (name, connection, provider, currency, cash balance) — never a password.</summary>
		private static string AccountsJson()
		{
			List<Account> list;
			lock (Gate) list = watched.ToList();
			List<string> parts = new List<string>();
			foreach (Account a in list.Take(50))
			{
				try
				{
					string conn = "", provider = "";
					if (a.Connection != null && a.Connection.Options != null)
					{
						conn = a.Connection.Options.Name ?? "";
						provider = a.Connection.Options.Provider.ToString();
					}
					string cur = a.Denomination.ToString();
					cur = cur == "UsDollar" ? "USD" : cur == "Euro" ? "EUR" : cur;
					string cash = "";   // (1.1.0) the account's balance: Sweep's balance follows it
					try { double v = a.Get(AccountItem.CashValue, a.Denomination); if (!double.IsNaN(v) && !double.IsInfinity(v)) cash = ",\"cash\":" + v.ToString("0.##", CultureInfo.InvariantCulture); } catch { }
					parts.Add("{\"name\":" + J(a.Name) + ",\"connection\":" + J(conn) + ",\"provider\":" + J(provider) + ",\"currency\":" + J(cur) + cash + "}");
				}
				catch { }
			}
			return string.Join(",", parts);
		}

		private static int Post(string body)
		{
			try
			{
				ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
				HttpWebRequest req = (HttpWebRequest)WebRequest.Create(Url);
				req.Method = "POST";
				req.ContentType = "application/json";
				req.UserAgent = "SweepSync/" + Version;
				req.Timeout = 20000;
				req.ReadWriteTimeout = 20000;
				req.Headers["X-Sweep-Key"] = Key;
				byte[] data = Encoding.UTF8.GetBytes(body);
				req.ContentLength = data.Length;
				using (Stream s = req.GetRequestStream()) s.Write(data, 0, data.Length);
				using (HttpWebResponse r = (HttpWebResponse)req.GetResponse()) return (int)r.StatusCode;
			}
			catch (WebException we)
			{
				HttpWebResponse r = we.Response as HttpWebResponse;
				if (r == null) Log("network: " + we.Message);
				return r != null ? (int)r.StatusCode : 0;
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
				if (File.Exists(path)) File.Delete(path);
				File.Move(tmp, path);
			}
		}

		/* ---------- JSON ---------- */

		private static string J(string s)
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
						if (c < 0x20) b.Append("\\u").Append(((int)c).ToString("x4"));
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

		private static void Log(string text)
		{
			try { NinjaTrader.Code.Output.Process("Sweep Sync: " + text, PrintTo.OutputTab1); } catch { }
		}
	}

	/// <summary>The add-on's window (Control Center > New > Sweep Sync): the key, and what is happening.</summary>
	public class SweepSyncWindow : NTWindow
	{
		private readonly TextBox keyBox;
		private readonly TextBlock status;
		private readonly DispatcherTimer refresh;
		private readonly string[] L;
		private bool badKey;

		// intro, key label, save, no key, sent, waiting, key refused, no connection, waiting count, accounts, bad key format
		private static readonly string[] En = { "Sweep Sync sends the executions of all your accounts to your Sweep journal. Read-only: it never places, changes or cancels an order.", "Your Sweep key (Sweep > Settings > Data > Connections)", "Save", "Paste your key to start.", "Connected · last sent at {0}", "Waiting to send…", "Key refused: create a new one in Sweep and paste it here.", "No connection to Sweep: the executions wait and will be sent.", "{0} execution(s) waiting", "Accounts followed: {0}", "This is not a Sweep key (it starts with swk_)." };
		private static readonly string[] Fr = { "Sweep Sync envoie les exécutions de tous tes comptes à ton journal Sweep. Lecture seule : il ne passe, ne modifie et n’annule jamais d’ordre.", "Ta clé Sweep (Sweep > Réglages > Données > Connexions)", "Enregistrer", "Colle ta clé pour commencer.", "Connecté · dernier envoi à {0}", "Envoi en attente…", "Clé refusée : crée une nouvelle clé dans Sweep et colle-la ici.", "Pas de connexion à Sweep : les exécutions attendent et seront envoyées.", "{0} exécution(s) en attente", "Comptes suivis : {0}", "Ce n’est pas une clé Sweep (elle commence par swk_)." };
		private static readonly string[] Es = { "Sweep Sync envía las ejecuciones de todas tus cuentas a tu diario de Sweep. Solo lectura: nunca envía, modifica ni cancela una orden.", "Tu clave de Sweep (Sweep > Ajustes > Datos > Conexiones)", "Guardar", "Pega tu clave para empezar.", "Conectado · último envío a las {0}", "Envío pendiente…", "Clave rechazada: crea una nueva en Sweep y pégala aquí.", "Sin conexión con Sweep: las ejecuciones esperan y se enviarán.", "{0} ejecución(es) pendiente(s)", "Cuentas seguidas: {0}", "No es una clave de Sweep (empieza por swk_)." };

		public SweepSyncWindow()
		{
			string lang = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
			L = lang == "fr" ? Fr : lang == "es" ? Es : En;
			Caption = "Sweep Sync";
			Width = 480;
			Height = 320;
			Brush text = Application.Current.TryFindResource("FontControlBrush") as Brush;
			StackPanel panel = new StackPanel { Margin = new Thickness(18) };
			panel.Children.Add(MakeText(L[0], text, new Thickness(0, 0, 0, 14)));
			panel.Children.Add(MakeText(L[1], text, new Thickness(0, 0, 0, 4)));
			keyBox = new TextBox { Text = SweepSyncEngine.Key ?? "", Margin = new Thickness(0, 0, 0, 10), FontFamily = new FontFamily("Consolas") };
			panel.Children.Add(keyBox);
			Button save = new Button { Content = L[2], HorizontalAlignment = HorizontalAlignment.Left, Padding = new Thickness(16, 4, 16, 4) };
			save.Click += (o, e) => { badKey = !SweepSyncEngine.SetKey(keyBox.Text); Refresh(); };
			panel.Children.Add(save);
			status = MakeText("", text, new Thickness(0, 14, 0, 0));
			panel.Children.Add(status);
			Content = panel;
			refresh = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
			refresh.Tick += (o, e) => Refresh();
			refresh.Start();
			Closed += (o, e) => refresh.Stop();
			Refresh();
		}

		private static TextBlock MakeText(string s, Brush brush, Thickness margin)
		{
			TextBlock t = new TextBlock { Text = s, TextWrapping = TextWrapping.Wrap, Margin = margin };
			if (brush != null) t.Foreground = brush;
			return t;
		}

		private void Refresh()
		{
			List<string> lines = new List<string>();
			if (badKey) lines.Add(L[10]);
			else if (string.IsNullOrEmpty(SweepSyncEngine.Key)) lines.Add(L[3]);
			else if (SweepSyncEngine.LastError == "key") lines.Add(L[6]);
			else if (SweepSyncEngine.LastError == "network" || SweepSyncEngine.LastError == "server") lines.Add(L[7]);
			else if (SweepSyncEngine.LastOk != DateTime.MinValue) lines.Add(string.Format(L[4], SweepSyncEngine.LastOk.ToString("HH:mm:ss")));
			else lines.Add(L[5]);
			int n = SweepSyncEngine.Pending;
			if (n > 0) lines.Add(string.Format(L[8], n));
			string[] acc = SweepSyncEngine.Accounts;
			if (acc.Length > 0) lines.Add(string.Format(L[9], string.Join(", ", acc)));
			status.Text = string.Join("\n", lines);
		}
	}
}
