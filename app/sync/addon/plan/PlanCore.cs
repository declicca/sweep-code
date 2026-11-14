using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

// Sweep — Plan Sync (BRIEF_PLAN_SYNC, step 3, 13 Nov. 2026): the logic both chart add-ons share (Quantower now, NinjaTrader 8 at
// step 4), with no platform library: the day's plan read from api/plan-sync/today, the triggers evaluated on the platform's own
// prices (never a call to Sweep to evaluate), each alert once per trading day, the texts in EN / FR / ES, the events for Sweep.
// Written in plain C# 5 (no newer syntax, no System.Text.Json): NinjaTrader 8 compiles it on .NET Framework.
// Reminder, never execution: nothing here can reach an order.
namespace SweepPlanSync
{
    public class Zone
    {
        public string Id = "", Instrument = "", Type = "level", Label = "", Role = "neutral", Bias = "", Note = "";
        public double Price, High, Low;
        public int ProximityTicks;   // 0: the instrument's default (Roots.DefaultProx)
        public bool IsZone { get { return Type == "zone"; } }
        /// <summary>the top and the bottom (a level: both its price)</summary>
        public double Top { get { return IsZone ? High : Price; } }
        public double Bottom { get { return IsZone ? Low : Price; } }
    }

    public class Rule
    {
        public string Id = "", Trigger = "", ZoneId = "", Time = "", Action = "alert", Message = "";
        public int TfMinutes = 5;
    }

    public class Limits
    {
        public long MaxLossC;          // cents, 0 = not set
        public int MaxTrades, LossesInRow;
        public string Stopped = "";    // set when Sweep says the day is over
    }

    public class Plan
    {
        public string Day = "", Instrument = "", Lang = "en", Version = "";
        public bool Empty = true;
        public List<Zone> Zones = new List<Zone>();
        public List<Rule> Rules = new List<Rule>();
        public string DayBias = "", Scenario = "", DayRule = "";
        public List<string> Checklist = new List<string>();
        public Limits Limits;          // null: unknown

        public Zone ZoneById(string id)
        {
            foreach (Zone z in Zones) if (z.Id == id) return z;
            return null;
        }

        /// <summary>api/plan-sync/today's answer → a plan; null when it is not one</summary>
        public static Plan Parse(string json)
        {
            Dictionary<string, object> o = Json.Parse(json) as Dictionary<string, object>;
            if (o == null || !(o.ContainsKey("day"))) return null;
            Plan p = new Plan();
            p.Day = Json.Str(o, "day");
            p.Instrument = Json.Str(o, "instrument");
            p.Lang = Texts.Lang(Json.Str(o, "lang"));
            p.Version = Json.Str(o, "version");
            p.Empty = Json.Bool(o, "empty");
            foreach (object x in Json.List(o, "zones"))
            {
                Dictionary<string, object> d = x as Dictionary<string, object>;
                if (d == null) continue;
                Zone z = new Zone();
                z.Id = Json.Str(d, "id"); z.Instrument = Json.Str(d, "instrument"); z.Type = Json.Str(d, "type") == "zone" ? "zone" : "level";
                z.Price = Json.Num(d, "price"); z.High = Json.Num(d, "high"); z.Low = Json.Num(d, "low");
                z.Label = Json.Str(d, "label"); z.Role = Json.Str(d, "role"); z.Bias = Json.Str(d, "bias"); z.Note = Json.Str(d, "note");
                z.ProximityTicks = (int)Json.Num(d, "proximity_ticks");
                if (z.Id.Length == 0 || (z.IsZone ? (z.High <= 0 || z.Low <= 0) : z.Price <= 0)) continue;
                if (z.IsZone && z.High < z.Low) { double t = z.High; z.High = z.Low; z.Low = t; }
                p.Zones.Add(z);
            }
            foreach (object x in Json.List(o, "rules"))
            {
                Dictionary<string, object> d = x as Dictionary<string, object>;
                if (d == null) continue;
                Rule r = new Rule();
                r.Id = Json.Str(d, "id"); r.Trigger = Json.Str(d, "trigger"); r.ZoneId = Json.Str(d, "zone"); r.Time = Json.Str(d, "time");
                r.Action = Json.Str(d, "action"); r.Message = Json.Str(d, "message");
                string tf = Json.Str(d, "tf");
                r.TfMinutes = tf == "1m" ? 1 : tf == "15m" ? 15 : 5;
                if (r.Action != "plan" && r.Action != "limit") r.Action = "alert";
                if (r.Id.Length == 0 || Array.IndexOf(Engine.Triggers, r.Trigger) < 0) continue;
                if (r.Trigger == "time" ? !Engine.IsTime(r.Time) : p.ZoneById(r.ZoneId) == null) continue;
                p.Rules.Add(r);
            }
            Dictionary<string, object> pl = Json.Get(o, "plan") as Dictionary<string, object>;
            if (pl != null)
            {
                p.DayBias = Json.Str(pl, "bias"); p.Scenario = Json.Str(pl, "scenario"); p.DayRule = Json.Str(pl, "rule");
                foreach (object c in Json.List(pl, "checklist")) { string s = c as string; if (!string.IsNullOrEmpty(s)) p.Checklist.Add(s); }
            }
            Dictionary<string, object> li = Json.Get(o, "limits") as Dictionary<string, object>;
            if (li != null)
            {
                p.Limits = new Limits();
                p.Limits.MaxLossC = (long)Json.Num(li, "max_loss_c");
                p.Limits.MaxTrades = (int)Json.Num(li, "max_trades");
                p.Limits.LossesInRow = (int)Json.Num(li, "losses_in_row");
                p.Limits.Stopped = Json.Str(li, "stopped");
            }
            return p;
        }
    }

    /// <summary>instrument roots, as Sweep reads them (game/chart-plan.php ChartPlan::root, src/game.js PC_ROOTS)</summary>
    public static class Roots
    {
        private static readonly Dictionary<string, string> Micro = new Dictionary<string, string>
        {
            { "MNQ", "NQ" }, { "MES", "ES" }, { "MYM", "YM" }, { "M2K", "RTY" }, { "MCL", "CL" }, { "MGC", "GC" }, { "SIL", "SI" }, { "M6E", "6E" }
        };
        // the default approach distance in ticks, the app's one table (src/game.js PC_ROOTS); 20 for any other root
        private static readonly Dictionary<string, int> Prox = new Dictionary<string, int>
        {
            { "NQ", 40 }, { "ES", 8 }, { "YM", 20 }, { "RTY", 20 }, { "CL", 10 }, { "GC", 20 }, { "SI", 10 }, { "6E", 20 },
            { "NG", 10 }, { "HG", 20 }, { "ZN", 8 }, { "ZB", 8 }, { "MBT", 20 }, { "MET", 20 }
        };

        public static int DefaultProx(string root)
        {
            int n;
            return Prox.TryGetValue(root ?? "", out n) ? n : 20;
        }

        /// <summary>one name → its root: NQZ6 → NQ, MNQ → NQ, « mnq h27 » → NQ</summary>
        public static string Of(string s)
        {
            StringBuilder b = new StringBuilder();
            foreach (char c in (s ?? "").ToUpperInvariant()) if ((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) b.Append(c);
            string r = b.ToString();
            if (r.Length > 3)
            {
                int i = r.Length - 1, digits = 0;
                while (i >= 0 && char.IsDigit(r[i]) && digits < 2) { i--; digits++; }
                if (digits >= 1 && i >= 1 && "FGHJKMNQUVXZ".IndexOf(r[i]) >= 0) r = r.Substring(0, i);
            }
            if (r.Length > 8) r = r.Substring(0, 8);
            string m;
            return Micro.TryGetValue(r, out m) ? m : r;
        }

        /// <summary>a platform's symbol → its root: the platform's own root when it gives one, else from the name; names made of
        /// parts (ProjectX « CON.F.US.MNQ.Z25 », « /MNQ:XCME ») use the part Sweep knows</summary>
        public static string Root(string name, string platformRoot)
        {
            string r = Of(platformRoot);
            if (r.Length > 0 && (Prox.ContainsKey(r) || Micro.ContainsKey(r))) return r;
            foreach (string part in (name ?? "").Split(new char[] { '.', ':', '/', ' ', '-', '_' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string x = Of(part);
                if (Prox.ContainsKey(x)) return x;
            }
            string whole = Of(name);
            return whole.Length > 0 ? whole : r;
        }
    }

    /// <summary>an alert the platform shows (and the event Sweep receives)</summary>
    public class Alert
    {
        public string Key = "", Trigger = "", EventType = "", ZoneId = "", RuleId = "", Title = "", Body = "", Day = "", Instrument = "";
        public double Price;
        public DateTime AtUtc;
        public string Text { get { return Body.Length > 0 ? Title + " — " + Body : Title; } }
    }

    /// <summary>
    /// The triggers of one instrument root. Fed with the platform's prices (each tick) and the clock (each second); returns the
    /// alerts to show. Candles of 1, 5 and 15 minutes are built here from the ticks, on the clock (a chart of any time frame
    /// gives the same candles). Each alert at most once per trading day: its key goes into Fired, shared by every root (a time
    /// rule read by two instruments alerts once) and kept by the host across restarts.
    /// </summary>
    public class Engine
    {
        public static readonly string[] Triggers = { "approach", "enter", "close_above", "close_below", "sweep", "time" };
        public static readonly TimeSpan Gap = TimeSpan.FromMinutes(20);   // no price for longer (session break, reconnection): a gap

        private class Bar { public long Slot = long.MinValue; public double Close = double.NaN; public bool Open; }
        private class SweepState { public int SideHigh, SideLow; public bool PiercedUp, PiercedDown; }   // side: -1 below, 1 above, 0 unknown

        public readonly string Root;
        public Plan Plan;
        public readonly HashSet<string> Fired;
        private double last = double.NaN;
        private DateTime lastAt = DateTime.MinValue;
        private DateTime clock = DateTime.MinValue;
        private readonly Dictionary<int, Bar> bars = new Dictionary<int, Bar>();
        private readonly Dictionary<string, SweepState> sweeps = new Dictionary<string, SweepState>();

        public Engine(string root, HashSet<string> fired)
        {
            Root = root;
            Fired = fired ?? new HashSet<string>();
        }

        public double Last { get { return last; } }

        /// <summary>a new plan (each poll that changed): what already alerted today stays done; a new day starts afresh</summary>
        public void SetPlan(Plan p)
        {
            if (p != null && Plan != null && p.Day != Plan.Day) sweeps.Clear();
            Plan = p;
        }

        public static bool IsTime(string t)
        {
            int h, m;
            return t != null && t.Length == 5 && t[2] == ':' && int.TryParse(t.Substring(0, 2), out h) && int.TryParse(t.Substring(3), out m) && h >= 0 && h < 24 && m >= 0 && m < 60;
        }

        public string KeyOf(string day, string what) { return day + "|" + what; }

        /// <summary>the alert can show again (the banner's « Re-arm »)</summary>
        public void Rearm(string key) { Fired.Remove(key); }

        /// <summary>one price of the platform</summary>
        public List<Alert> OnPrice(double price, DateTime utc, double tick)
        {
            List<Alert> o = new List<Alert>();
            if (double.IsNaN(price) || double.IsInfinity(price) || price <= 0) return o;
            if (tick <= 0 || double.IsNaN(tick)) tick = 0.25;
            bool continuous = !double.IsNaN(last) && utc - lastAt <= Gap && utc >= lastAt;
            double prev = last;
            // candles that ended before this price close first, at their last price
            CloseBars(utc, o, tick);
            if (Plan != null && !Plan.Empty)
            {
                foreach (Zone z in Plan.Zones)
                {
                    double d = Dist(z, price, tick);
                    bool inside = d <= 0;
                    bool crossed = continuous && Crossed(z, prev, price);
                    double prox = (z.ProximityTicks > 0 ? z.ProximityTicks : Roots.DefaultProx(Root)) * tick;
                    if (inside || crossed)
                    {
                        Fire(o, z, "enter", price, utc);
                        Consume(z, "approach");   // reached without an approach first (a jump): no late « approaching »
                    }
                    else if (d <= prox + tick * 1e-6) Fire(o, z, "approach", price, utc);
                    Pierce(z, price, tick);
                }
            }
            last = price;
            lastAt = utc;
            foreach (int tf in Tfs())
            {
                Bar b;
                if (!bars.TryGetValue(tf, out b)) { b = new Bar(); bars[tf] = b; }
                long slot = Slot(utc, tf);
                if (b.Slot != slot) { b.Slot = slot; b.Open = true; }
                b.Close = price;
            }
            return o;
        }

        /// <summary>the clock (each second): time rules, and candles that ended with no new price</summary>
        public List<Alert> OnClock(DateTime utc, double tick)
        {
            List<Alert> o = new List<Alert>();
            if (tick <= 0 || double.IsNaN(tick)) tick = 0.25;
            CloseBars(utc, o, tick);
            if (clock == DateTime.MinValue) { clock = utc; return o; }   // started now: an hour already past never alerts late
            if (utc <= clock) return o;
            if (Plan != null)
                foreach (Rule r in Plan.Rules)
                {
                    if (r.Trigger != "time") continue;
                    DateTime at = NyInstant(Plan.Day, r.Time);
                    if (at > clock && at <= utc) FireRule(o, r, null, double.NaN, utc);
                }
            clock = utc;
            return o;
        }

        private List<int> Tfs()
        {
            List<int> o = new List<int>();
            if (Plan == null) return o;
            foreach (Rule r in Plan.Rules)
                if ((r.Trigger == "close_above" || r.Trigger == "close_below" || r.Trigger == "sweep") && !o.Contains(r.TfMinutes)) o.Add(r.TfMinutes);
            return o;
        }

        private static long Slot(DateTime utc, int tf) { return utc.Ticks / TimeSpan.FromMinutes(tf).Ticks; }

        private void CloseBars(DateTime utc, List<Alert> o, double tick)
        {
            foreach (KeyValuePair<int, Bar> kv in bars)
            {
                Bar b = kv.Value;
                if (!b.Open || Slot(utc, kv.Key) == b.Slot || double.IsNaN(b.Close)) continue;
                b.Open = false;
                OnClose(kv.Key, b.Close, utc, o, tick);
            }
        }

        /// <summary>a candle of tf minutes closed at close</summary>
        private void OnClose(int tf, double close, DateTime utc, List<Alert> o, double tick)
        {
            if (Plan == null) return;
            foreach (Rule r in Plan.Rules)
            {
                if (r.TfMinutes != tf) continue;
                Zone z = Plan.ZoneById(r.ZoneId);
                if (z == null) continue;
                if (r.Trigger == "close_above" && close > z.Top) FireRule(o, r, z, close, utc);
                else if (r.Trigger == "close_below" && close < z.Bottom) FireRule(o, r, z, close, utc);
                else if (r.Trigger == "sweep")
                {
                    SweepState s = State(r, z, close);
                    if (s.PiercedUp && close < z.Top) FireRule(o, r, z, close, utc);
                    else if (s.PiercedDown && close > z.Bottom) FireRule(o, r, z, close, utc);
                    s.PiercedUp = false; s.PiercedDown = false;
                    s.SideHigh = close < z.Top ? -1 : 1;
                    s.SideLow = close > z.Bottom ? 1 : -1;
                }
            }
        }

        private SweepState State(Rule r, Zone z, double price)
        {
            SweepState s;
            if (!sweeps.TryGetValue(r.Id, out s))
            {
                s = new SweepState();
                s.SideHigh = price < z.Top ? -1 : 1;
                s.SideLow = price > z.Bottom ? 1 : -1;
                sweeps[r.Id] = s;
            }
            return s;
        }

        /// <summary>a sweep starts when price goes at least 1 tick past the level from the side it closed on</summary>
        private void Pierce(Zone z, double price, double tick)
        {
            foreach (Rule r in Plan.Rules)
            {
                if (r.Trigger != "sweep" || r.ZoneId != z.Id) continue;
                SweepState s = State(r, z, price);
                if (s.SideHigh < 0 && price >= z.Top + tick - tick * 1e-6) s.PiercedUp = true;
                if (s.SideLow > 0 && price <= z.Bottom - tick + tick * 1e-6) s.PiercedDown = true;
            }
        }

        /// <summary>how far price is from the level or the zone (0 inside; a level is touched within half a tick)</summary>
        public static double Dist(Zone z, double p, double tick)
        {
            if (!z.IsZone) { double d = Math.Abs(p - z.Price); return d < tick / 2 ? 0 : d; }
            if (p >= z.Low && p <= z.High) return 0;
            return p > z.High ? p - z.High : z.Low - p;
        }

        /// <summary>price went through the level or the zone between two prices (a fast move between ticks)</summary>
        private static bool Crossed(Zone z, double a, double b)
        {
            if (double.IsNaN(a)) return false;
            double lo = Math.Min(a, b), hi = Math.Max(a, b);
            return lo <= z.Top && hi >= z.Bottom;
        }

        /// <summary>a zone's own approach / enter: the trader's rule on that zone and trigger if there is one, else the automatic one</summary>
        private void Fire(List<Alert> o, Zone z, string trigger, double price, DateTime utc)
        {
            bool ruled = false;
            foreach (Rule r in Plan.Rules)
                if (r.ZoneId == z.Id && r.Trigger == trigger) { ruled = true; FireRule(o, r, z, price, utc); }
            if (ruled) return;
            string key = KeyOf(Plan.Day, "zone:" + z.Id + ":" + trigger);
            if (Fired.Contains(key)) return;
            Fired.Add(key);
            Alert a = Make(key, trigger, z, null, price, utc);
            a.EventType = trigger == "approach" ? "zone_approached" : "zone_entered";
            a.Title = Texts.Title(Plan.Lang, trigger, z, 0, "");
            a.Body = z.Note;
            o.Add(a);
        }

        /// <summary>the approach did not alert before the enter: it never will today</summary>
        private void Consume(Zone z, string trigger)
        {
            bool ruled = false;
            foreach (Rule r in Plan.Rules)
                if (r.ZoneId == z.Id && r.Trigger == trigger) { ruled = true; Fired.Add(KeyOf(Plan.Day, "rule:" + r.Id)); }
            if (!ruled) Fired.Add(KeyOf(Plan.Day, "zone:" + z.Id + ":" + trigger));
        }

        private void FireRule(List<Alert> o, Rule r, Zone z, double price, DateTime utc)
        {
            string key = KeyOf(Plan.Day, "rule:" + r.Id);
            if (Fired.Contains(key)) return;
            Fired.Add(key);
            Alert a = Make(key, r.Trigger, z, r, price, utc);
            a.EventType = "rule_triggered";
            a.Title = Texts.Title(Plan.Lang, r.Trigger, z, r.TfMinutes, r.Time);
            a.Body = Texts.Body(Plan, r, z);
            o.Add(a);
        }

        private Alert Make(string key, string trigger, Zone z, Rule r, double price, DateTime utc)
        {
            Alert a = new Alert();
            a.Key = key; a.Trigger = trigger; a.Day = Plan.Day; a.Instrument = Root;
            a.ZoneId = z != null ? z.Id : ""; a.RuleId = r != null ? r.Id : "";
            a.Price = price; a.AtUtc = utc;
            return a;
        }

        /* ---------- New York time ---------- */

        private static TimeZoneInfo ny;
        public static TimeZoneInfo NewYork
        {
            get
            {
                if (ny != null) return ny;
                foreach (string id in new string[] { "America/New_York", "Eastern Standard Time" })
                {
                    try { ny = TimeZoneInfo.FindSystemTimeZoneById(id); return ny; } catch (Exception) { }
                }
                ny = TimeZoneInfo.CreateCustomTimeZone("NY", TimeSpan.FromHours(-5), "New York", "New York");   // no time zone data: EST
                return ny;
            }
        }

        /// <summary>a New York time of the trading day → its instant (UTC): from 18:00 on, it is the evening before the day</summary>
        public static DateTime NyInstant(string day, string hhmm)
        {
            DateTime d;
            if (!DateTime.TryParseExact(day, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d) || !IsTime(hhmm)) return DateTime.MinValue;
            int h = int.Parse(hhmm.Substring(0, 2), CultureInfo.InvariantCulture), m = int.Parse(hhmm.Substring(3), CultureInfo.InvariantCulture);
            DateTime local = d.Date.AddHours(h).AddMinutes(m);
            if (h >= 18) local = local.AddDays(-1);   // the evening before (Monday's opens on Sunday)
            try { return TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(local, DateTimeKind.Unspecified), NewYork); }
            catch (Exception) { return DateTime.SpecifyKind(local.AddHours(5), DateTimeKind.Utc); }
        }

        /// <summary>the trading day of an instant, as Sweep (Fiche::dayOf): from 18:00 New York the next day; a weekend is Monday</summary>
        public static string DayOf(DateTime utc)
        {
            DateTime l = TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(utc, DateTimeKind.Utc), NewYork);
            DateTime d = l.Hour >= 18 ? l.Date.AddDays(1) : l.Date;
            if (d.DayOfWeek == DayOfWeek.Saturday) d = d.AddDays(2);
            else if (d.DayOfWeek == DayOfWeek.Sunday) d = d.AddDays(1);
            return d.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        }
    }

    /// <summary>the events sent to Sweep (api/plan-sync/events): one line of JSON each, the id made here (a resend is ignored)</summary>
    public static class Events
    {
        public static string Json(Alert a)
        {
            StringBuilder b = new StringBuilder("{");
            b.Append("\"id\":").Append(SweepPlanSync.Json.Quote(Id(a)));
            b.Append(",\"type\":").Append(SweepPlanSync.Json.Quote(a.EventType));
            b.Append(",\"at\":").Append(SweepPlanSync.Json.Quote(a.AtUtc.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'", CultureInfo.InvariantCulture)));
            b.Append(",\"instrument\":").Append(SweepPlanSync.Json.Quote(a.Instrument));
            b.Append(",\"price\":").Append(double.IsNaN(a.Price) ? "null" : a.Price.ToString("R", CultureInfo.InvariantCulture));
            if (a.ZoneId.Length > 0) b.Append(",\"zone\":").Append(SweepPlanSync.Json.Quote(a.ZoneId));
            if (a.RuleId.Length > 0) b.Append(",\"rule\":").Append(SweepPlanSync.Json.Quote(a.RuleId));
            return b.Append('}').ToString();
        }

        /// <summary>the same alert of the same day always has the same id: sent twice (a restart, a lost answer), Sweep keeps one</summary>
        public static string Id(Alert a)
        {
            string what = a.RuleId.Length > 0 ? "r" + a.RuleId : "z" + a.ZoneId + "." + (a.EventType == "zone_approached" ? "a" : "e");
            string id = "ps." + a.Day.Replace("-", "") + "." + what;
            return id.Length > 64 ? id.Substring(0, 64) : id;
        }

        /// <summary>the body of one request: up to max lines</summary>
        public static string Body(IList<string> lines, int max)
        {
            StringBuilder b = new StringBuilder("{\"events\":[");
            for (int i = 0; i < lines.Count && i < max; i++) { if (i > 0) b.Append(','); b.Append(lines[i]); }
            return b.Append("]}").ToString();
        }
    }

    /// <summary>the add-on's texts, in the trader's Sweep language (the plan's lang)</summary>
    public static class Texts
    {
        public static string Lang(string l) { return l == "fr" || l == "es" ? l : "en"; }

        private static string Pick(string lang, string en, string fr, string es) { return lang == "fr" ? fr : lang == "es" ? es : en; }

        public static string Name(Zone z)
        {
            if (z == null) return "";
            if (z.Label.Length > 0) return z.Label;
            return z.IsZone ? Num(z.Low) + "–" + Num(z.High) : Num(z.Price);
        }

        public static string Num(double v) { return v.ToString("0.#####", CultureInfo.InvariantCulture); }

        public static string Title(string lang, string trigger, Zone z, int tf, string time)
        {
            string n = Name(z), t = tf + "m";
            switch (trigger)
            {
                case "approach": return string.Format(Pick(lang, "Approaching {0}", "Tu approches de {0}", "Te acercas a {0}"), n);
                case "enter": return string.Format(z != null && z.IsZone ? Pick(lang, "Price in {0}", "Le prix entre dans {0}", "El precio entra en {0}") : Pick(lang, "Price on {0}", "Le prix touche {0}", "El precio toca {0}"), n);
                case "close_above": return string.Format(Pick(lang, "{1} candle closed above {0}", "Bougie {1} fermée au-dessus de {0}", "Vela de {1} cerrada por encima de {0}"), n, t);
                case "close_below": return string.Format(Pick(lang, "{1} candle closed below {0}", "Bougie {1} fermée au-dessous de {0}", "Vela de {1} cerrada por debajo de {0}"), n, t);
                case "sweep": return string.Format(Pick(lang, "{0} swept ({1})", "Sweep de {0} ({1})", "Sweep de {0} ({1})"), n, t);
                case "time": return string.Format(Pick(lang, "It is {0} in New York", "Il est {0} à New York", "Son las {0} en Nueva York"), time);
            }
            return "Sweep";
        }

        /// <summary>what the alert says: the trader's message, then what the rule's action reminds</summary>
        public static string Body(Plan p, Rule r, Zone z)
        {
            string l = p.Lang;
            List<string> parts = new List<string>();
            if (r.Message.Length > 0) parts.Add(r.Message);
            if (r.Action == "plan")
            {
                if (z != null && z.Bias == "long") parts.Add(Pick(l, "Bias: long", "Biais : long", "Sesgo: largo"));
                else if (z != null && z.Bias == "short") parts.Add(Pick(l, "Bias: short", "Biais : short", "Sesgo: corto"));
                if (z != null && z.Note.Length > 0) parts.Add(z.Note);
                string db = DayBias(l, p.DayBias);
                if (db.Length > 0) parts.Add(db);
                if (p.DayRule.Length > 0) parts.Add(Pick(l, "Rule: ", "Règle : ", "Regla: ") + p.DayRule);
                if (p.Checklist.Count > 0) parts.Add(Pick(l, "Checklist: ", "Checklist : ", "Checklist: ") + string.Join(" · ", p.Checklist.ToArray()));
                if (parts.Count == 0) parts.Add(Pick(l, "Your plan has no details yet in Sweep.", "Ton plan n’a pas encore de détails dans Sweep.", "Tu plan aún no tiene detalles en Sweep."));
            }
            else if (r.Action == "limit")
            {
                Limits m = p.Limits;
                int before = parts.Count;
                if (m != null)
                {
                    if (m.Stopped.Length > 0) parts.Add(Pick(l, "Sweep says your day is done: protect your account.", "Sweep dit que ta journée est finie : protège ton compte.", "Sweep dice que tu día terminó: protege tu cuenta."));
                    if (m.MaxLossC > 0) parts.Add(string.Format(Pick(l, "Risk allowed today: ${0}", "Risque permis aujourd’hui : {0} $", "Riesgo permitido hoy: {0} $"), Money(m.MaxLossC)));
                    if (m.MaxTrades > 0) parts.Add(string.Format(Pick(l, "Max trades: {0}", "Trades max : {0}", "Máximo de trades: {0}"), m.MaxTrades));
                    if (m.LossesInRow > 0) parts.Add(string.Format(Pick(l, "Stop after {0} losses in a row", "Arrête après {0} pertes de suite", "Para tras {0} pérdidas seguidas"), m.LossesInRow));
                }
                if (parts.Count == before) parts.Add(Pick(l, "No limit set in Sweep for today.", "Aucune limite dans Sweep pour aujourd’hui.", "Ningún límite en Sweep para hoy."));
            }
            else if (parts.Count == 0 && z != null && z.Note.Length > 0) parts.Add(z.Note);
            return string.Join(" · ", parts.ToArray());
        }

        private static string DayBias(string l, string b)
        {
            switch (b)
            {
                case "bullish": return Pick(l, "Day: bullish", "Journée : haussière", "Día: alcista");
                case "bearish": return Pick(l, "Day: bearish", "Journée : baissière", "Día: bajista");
                case "neutral": return Pick(l, "Day: neutral", "Journée : neutre", "Día: neutral");
                case "no_trade": return Pick(l, "Day: no trade", "Journée : pas de trade", "Día: sin operar");
            }
            return "";
        }

        private static string Money(long cents)
        {
            double v = cents / 100.0;
            return v == Math.Floor(v) ? ((long)v).ToString(CultureInfo.InvariantCulture) : v.ToString("0.00", CultureInfo.InvariantCulture);
        }

        // the add-on's own lines (the chart's banner)
        public static string NoPlan(string l) { return Pick(l, "No plan for today in Sweep.", "Pas de plan pour aujourd’hui dans Sweep.", "No hay plan para hoy en Sweep."); }
        public static string NoKey(string l) { return Pick(l, "Sweep Plan: open the Sweep Sync panel and paste your Quantower key.", "Sweep Plan : ouvre le panneau Sweep Sync et colle ta clé Quantower.", "Sweep Plan: abre el panel Sweep Sync y pega tu clave de Quantower."); }
        public static string NoKeyNinja(string l) { return Pick(l, "Sweep Plan: in NinjaTrader, open Control Center › New › Sweep Sync and paste your NinjaTrader 8 key.", "Sweep Plan : dans NinjaTrader, ouvre Control Center › New › Sweep Sync et colle ta clé NinjaTrader 8.", "Sweep Plan: en NinjaTrader, abre Control Center › New › Sweep Sync y pega tu clave de NinjaTrader 8."); }
        public static string Offline(string l) { return Pick(l, "Sweep unreachable: your last plan stays on the chart and its alerts still work.", "Sweep injoignable : ton dernier plan reste sur le chart et ses alertes fonctionnent.", "Sweep no responde: tu último plan sigue en el gráfico y sus alertas funcionan."); }
        public static string Rearm(string l) { return Pick(l, "Re-arm", "Réarmer", "Rearmar"); }
    }

    /// <summary>a small JSON reader and writer (objects → Dictionary, arrays → List, numbers → double)</summary>
    public static class Json
    {
        public static object Parse(string s)
        {
            try
            {
                int i = 0;
                object v = Value(s ?? "", ref i);
                Ws(s, ref i);
                return i == s.Length ? v : null;
            }
            catch (Exception) { return null; }
        }

        public static object Get(Dictionary<string, object> o, string k) { object v; return o != null && o.TryGetValue(k, out v) ? v : null; }
        public static string Str(Dictionary<string, object> o, string k) { string s = Get(o, k) as string; return s ?? ""; }
        public static double Num(Dictionary<string, object> o, string k) { object v = Get(o, k); return v is double ? (double)v : 0; }
        public static bool Bool(Dictionary<string, object> o, string k) { object v = Get(o, k); return v is bool && (bool)v; }
        public static List<object> List(Dictionary<string, object> o, string k) { List<object> l = Get(o, k) as List<object>; return l ?? new List<object>(); }

        private static void Ws(string s, ref int i) { while (i < s.Length && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) i++; }

        private static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            char c = s[i];
            if (c == '{')
            {
                Dictionary<string, object> o = new Dictionary<string, object>();
                i++; Ws(s, ref i);
                if (s[i] == '}') { i++; return o; }
                while (true)
                {
                    Ws(s, ref i);
                    string k = Text(s, ref i);
                    Ws(s, ref i);
                    if (s[i] != ':') throw new FormatException();
                    i++;
                    o[k] = Value(s, ref i);
                    Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == '}') { i++; return o; }
                    throw new FormatException();
                }
            }
            if (c == '[')
            {
                List<object> l = new List<object>();
                i++; Ws(s, ref i);
                if (s[i] == ']') { i++; return l; }
                while (true)
                {
                    l.Add(Value(s, ref i));
                    Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == ']') { i++; return l; }
                    throw new FormatException();
                }
            }
            if (c == '"') return Text(s, ref i);
            if (s.Length - i >= 4 && s.Substring(i, 4) == "true") { i += 4; return true; }
            if (s.Length - i >= 5 && s.Substring(i, 5) == "false") { i += 5; return false; }
            if (s.Length - i >= 4 && s.Substring(i, 4) == "null") { i += 4; return null; }
            int st = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            if (i == st) throw new FormatException();
            return double.Parse(s.Substring(st, i - st), NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        private static string Text(string s, ref int i)
        {
            if (s[i] != '"') throw new FormatException();
            i++;
            StringBuilder b = new StringBuilder();
            while (s[i] != '"')
            {
                char c = s[i++];
                if (c != '\\') { b.Append(c); continue; }
                char e = s[i++];
                switch (e)
                {
                    case 'n': b.Append('\n'); break;
                    case 't': b.Append('\t'); break;
                    case 'r': b.Append('\r'); break;
                    case 'b': b.Append('\b'); break;
                    case 'f': b.Append('\f'); break;
                    case 'u': b.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture)); i += 4; break;
                    default: b.Append(e); break;
                }
            }
            i++;
            return b.ToString();
        }

        public static string Quote(string s)
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
    }
}
