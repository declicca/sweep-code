using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using SweepPlanSync;

// Plan Sync — the shared logic's tests: simulated price series on NQ and MNQ, every V1 trigger alerts once, the texts, the events.
static class Program
{
    static int fails, oks;
    static void Ok(bool c, string what) { if (c) oks++; else fails++; Console.WriteLine((c ? "ok   " : "FAIL ") + what); }

    const string Day = "2026-11-16";   // a Monday
    static readonly DateTime T0 = new DateTime(2026, 11, 16, 14, 31, 0, DateTimeKind.Utc);   // 9:31 New York (EST)
    const double Tick = 0.25;

    static string PlanJson(string zones, string rules, string lang = "fr", string day = Day, string extra = "")
    {
        return "{\"day\":\"" + day + "\",\"instrument\":\"NQ\",\"lang\":\"" + lang + "\",\"empty\":false,\"zones\":[" + zones + "],\"rules\":[" + rules + "],"
            + "\"plan\":{\"bias\":\"bullish\",\"scenario\":\"Buy the dip\",\"rule\":\"Max 2 trades\",\"setups\":[\"ORB\"],\"checklist\":[\"Wait for the close\",\"Stop under the wick\"]},"
            + "\"limits\":{\"max_loss_c\":50000,\"max_trades\":3,\"losses_in_row\":2,\"stopped\":null,\"accounts\":[]},\"updated_at\":1,\"version\":\"abc123\"" + extra + "}";
    }
    const string Pdh = "{\"id\":\"z1\",\"instrument\":\"NQ\",\"type\":\"level\",\"price\":21300,\"label\":\"PDH\",\"role\":\"resistance\",\"bias\":\"short\",\"note\":\"Watch the reaction\",\"proximity_ticks\":40}";
    const string BuyZone = "{\"id\":\"z2\",\"instrument\":\"NQ\",\"type\":\"zone\",\"high\":21200,\"low\":21180,\"label\":\"Zone d’achat\",\"role\":\"support\",\"bias\":\"long\",\"note\":\"\",\"proximity_ticks\":null}";
    const string AsiaLow = "{\"id\":\"z3\",\"instrument\":\"NQ\",\"type\":\"level\",\"price\":21100,\"label\":\"Asia low\",\"role\":\"invalidation\",\"bias\":null,\"note\":\"\",\"proximity_ticks\":8}";

    static Engine New(string json, HashSet<string> fired = null)
    {
        Engine e = new Engine("NQ", fired ?? new HashSet<string>());
        e.SetPlan(Plan.Parse(json));
        return e;
    }

    /// <summary>prices one second apart from t; the clock ticks too; all alerts</summary>
    static List<Alert> Feed(Engine e, DateTime t, params double[] prices)
    {
        List<Alert> o = new List<Alert>();
        foreach (double p in prices)
        {
            o.AddRange(e.OnClock(t, Tick));
            o.AddRange(e.OnPrice(p, t, Tick));
            t = t.AddSeconds(1);
        }
        return o;
    }

    static int Count(List<Alert> a, string trigger, string zone = null) { return a.Count(x => x.Trigger == trigger && (zone == null || x.ZoneId == zone)); }

    static void Main()
    {
        // ---------- roots: MNQ reads NQ, the month is ignored, the platforms' long names ----------
        Ok(Roots.Of("NQZ6") == "NQ" && Roots.Of("MNQZ6") == "NQ" && Roots.Of("mnq h27") == "NQ" && Roots.Of("MESZ26") == "ES" && Roots.Of("ES") == "ES", "roots: NQZ6 → NQ, MNQZ6 → NQ, « mnq h27 » → NQ, MESZ26 → ES");
        Ok(Roots.Root("CON.F.US.MNQ.Z25", "") == "NQ" && Roots.Root("/MNQ:XCME", "") == "NQ" && Roots.Root("MNQZ5", "MNQ") == "NQ" && Roots.Root("NQZ5", "NQ") == "NQ" && Roots.Root("6EZ6", "") == "6E", "roots: ProjectX « CON.F.US.MNQ.Z25 », « /MNQ:XCME », the platform's own root (MNQ), 6EZ6");
        Ok(Roots.DefaultProx("NQ") == 40 && Roots.DefaultProx("ES") == 8 && Roots.DefaultProx("ZZ") == 20, "the default approach distance: NQ 40 ticks, ES 8, another root 20 (the app's table)");

        // ---------- the plan as api/plan-sync/today gives it ----------
        Plan p = Plan.Parse(PlanJson(Pdh + "," + BuyZone, "{\"id\":\"r1\",\"trigger\":\"sweep\",\"zone\":\"z1\",\"tf\":\"5m\",\"action\":\"plan\",\"message\":\"Attendre le retour\"},{\"id\":\"r9\",\"trigger\":\"teleport\",\"zone\":\"z1\",\"action\":\"alert\",\"message\":\"\"}"));
        Ok(p != null && p.Day == Day && p.Lang == "fr" && p.Zones.Count == 2 && p.Zones[1].IsZone && p.Zones[1].High == 21200 && p.Zones[1].Low == 21180 && p.Zones[1].ProximityTicks == 0, "plan: day, language, a level and a zone (no approach distance → the default)");
        Ok(p.Rules.Count == 1 && p.Rules[0].TfMinutes == 5 && p.Rules[0].Action == "plan", "plan: an unknown trigger (not V1) is left out");
        Ok(p.Limits != null && p.Limits.MaxLossC == 50000 && p.Limits.MaxTrades == 3 && p.Checklist.Count == 2 && p.DayBias == "bullish", "plan: the limits and the checklist Sweep already knows");
        Ok(Plan.Parse("not json") == null && Plan.Parse("{\"error\":\"x\"}") == null, "plan: anything else is not a plan");

        // ---------- a plan with just 2 levels and no rule: approach + enter, automatically, once ----------
        {
            Engine e = New(PlanJson(Pdh + "," + AsiaLow, ""));
            List<Alert> a = Feed(e, T0, 21250, 21280, 21291, 21292, 21295, 21300, 21290, 21300, 21310, 21300);
            Ok(Count(a, "approach", "z1") == 1 && Count(a, "enter", "z1") == 1 && a.Count == 2, "2 levels, no rule: « approaching PDH » once (within 40 ticks = 10 points), then « price on PDH » once");
            Ok(a[0].EventType == "zone_approached" && a[1].EventType == "zone_entered" && a[0].Title == "Tu approches de PDH" && a[1].Title == "Le prix touche PDH" && a[0].Body == "Watch the reaction", "the automatic alerts: zone_approached / zone_entered, in French, the zone's note");
            Ok(Feed(e, T0.AddMinutes(2), 21250, 21300, 21250, 21300).Count == 0, "back and forth on the level: nothing more today");
        }

        // ---------- approach and enter rules, on NQ and on MNQ (same engine: the MNQ chart reads the NQ levels) ----------
        foreach (string inst in new[] { "NQ", "MNQ" })
        {
            HashSet<string> fired = new HashSet<string>();
            Engine e = new Engine(Roots.Of(inst + "Z6"), fired);
            e.SetPlan(Plan.Parse(PlanJson(BuyZone, "{\"id\":\"ra\",\"trigger\":\"approach\",\"zone\":\"z2\",\"action\":\"alert\",\"message\":\"Prépare ton entrée\"},{\"id\":\"re\",\"trigger\":\"enter\",\"zone\":\"z2\",\"action\":\"plan\",\"message\":\"\"}")));
            List<Alert> a = Feed(e, T0, 21230, 21215, 21209, 21208, 21199, 21190, 21185, 21201, 21195);
            Ok(e.Root == "NQ" && a.Count == 2 && a[0].RuleId == "ra" && a[0].EventType == "rule_triggered" && a[1].RuleId == "re", inst + ": approach rule (within 40 ticks of the zone's high), then enter rule, once each");
            Ok(a[0].Text == "Tu approches de Zone d’achat — Prépare ton entrée", inst + ": the alert's text = short title + the trader's message (" + a[0].Text + ")");
            Ok(a[1].Body.Contains("Biais : long") && a[1].Body.Contains("Journée : haussière") && a[1].Body.Contains("Règle : Max 2 trades") && a[1].Body.Contains("Checklist : Wait for the close · Stop under the wick"), inst + ": « remind me of my plan » = the zone's bias, the day's bias, the rule, the checklist (" + a[1].Body + ")");
        }

        // ---------- a jump into the zone: enter, never a late approach; a fast move through a level counts as a touch ----------
        {
            Engine e = New(PlanJson(BuyZone + "," + AsiaLow, ""));
            List<Alert> a = Feed(e, T0, 21300, 21190, 21300);
            Ok(Count(a, "enter", "z2") == 1 && Count(a, "approach", "z2") == 0, "a jump straight into the zone: « price in » only, no late « approaching »");
            List<Alert> b = Feed(e, T0.AddMinutes(1), 21150, 21050);
            Ok(Count(b, "enter", "z3") == 1 && Count(b, "approach", "z3") == 0, "price moves through Asia low between two ticks: it counts as a touch");
        }

        // ---------- a gap: approach and enter are never retroactive; a close above is, on the first closed candle ----------
        {
            Engine e = New(PlanJson(Pdh, "{\"id\":\"rc\",\"trigger\":\"close_above\",\"zone\":\"z1\",\"tf\":\"5m\",\"action\":\"alert\",\"message\":\"Cassure\"}"));
            DateTime close = new DateTime(2026, 11, 13, 21, 59, 0, DateTimeKind.Utc);
            Feed(e, close, 21200);
            List<Alert> a = Feed(e, new DateTime(2026, 11, 16, 14, 30, 5, DateTimeKind.Utc), 21400, 21405);
            Ok(Count(a, "enter") == 0 && Count(a, "approach") == 0, "a gap over PDH (21 200 → 21 400 at the open): no « price on », no « approaching »");
            List<Alert> c = e.OnClock(new DateTime(2026, 11, 16, 14, 35, 0, DateTimeKind.Utc), Tick);
            Ok(c.Count == 1 && c[0].RuleId == "rc" && c[0].Title == "Bougie 5m fermée au-dessus de PDH", "…but the first closed 5m candle above PDH alerts (" + (c.Count > 0 ? c[0].Title : "-") + ")");
        }

        // ---------- close above / below: on the candle's close only, of the chosen time frame ----------
        {
            Engine e = New(PlanJson(Pdh, "{\"id\":\"rc\",\"trigger\":\"close_above\",\"zone\":\"z1\",\"tf\":\"1m\",\"action\":\"alert\",\"message\":\"\"},{\"id\":\"rd\",\"trigger\":\"close_below\",\"zone\":\"z1\",\"tf\":\"15m\",\"action\":\"alert\",\"message\":\"\"}"));
            DateTime t = new DateTime(2026, 11, 16, 14, 31, 0, DateTimeKind.Utc);
            List<Alert> a = Feed(e, t, 21290, 21305, 21298);                      // above during the minute, closes below
            a.AddRange(e.OnClock(t.AddMinutes(1), Tick));
            Ok(a.Count(x => x.RuleId == "rc") == 0, "close above 1m: above during the minute, closed below → nothing");
            a = Feed(e, t.AddMinutes(1).AddSeconds(5), 21302, 21310);
            a.AddRange(e.OnClock(t.AddMinutes(2), Tick));
            Ok(a.Count(x => x.RuleId == "rc") == 1, "close above 1m: the minute closes at 21 310 → alerts once");
            Ok(a.Count(x => x.RuleId == "rd") == 0, "close below 15m: still above, nothing");
            a = Feed(e, t.AddMinutes(3), 21290, 21280);
            a.AddRange(e.OnClock(new DateTime(2026, 11, 16, 14, 45, 0, DateTimeKind.Utc), Tick));
            Ok(a.Count(x => x.RuleId == "rd") == 1 && a.Count(x => x.RuleId == "rc") == 0, "close below 15m: the 9:30–9:45 candle closes at 21 280 → alerts once; close above does not again");
        }

        // ---------- sweep: 1 tick past, then a candle closes back on the other side ----------
        {
            string rule = "{\"id\":\"rs\",\"trigger\":\"sweep\",\"zone\":\"z3\",\"tf\":\"5m\",\"action\":\"alert\",\"message\":\"Attendre le retour au-dessus\"}";
            Engine e = New(PlanJson(AsiaLow, rule));
            DateTime t = new DateTime(2026, 11, 16, 14, 35, 0, DateTimeKind.Utc);
            List<Alert> a = Feed(e, t, 21110, 21101, 21099.75, 21104);           // 1 tick under 21 100, back above
            a.AddRange(e.OnClock(t.AddMinutes(5), Tick));
            Ok(a.Count(x => x.RuleId == "rs") == 1 && a.First(x => x.RuleId == "rs").Text == "Sweep de Asia low (5m) — Attendre le retour au-dessus", "sweep 5m: 1 tick under Asia low, the candle closes back above → alerts once");
            Ok(Feed(e, t.AddMinutes(5).AddSeconds(5), 21090, 21105).Count(x => x.RuleId == "rs") == 0 && e.OnClock(t.AddMinutes(10), Tick).Count == 0, "sweep: a second sweep the same day → nothing more");

            Engine b = New(PlanJson(AsiaLow, rule));
            List<Alert> c = Feed(b, t, 21110, 21099.875, 21104);                  // half a tick: not past
            c.AddRange(b.OnClock(t.AddMinutes(5), Tick));
            Ok(c.Count(x => x.RuleId == "rs") == 0, "sweep: less than 1 tick past is not a sweep");
            Engine d = New(PlanJson(AsiaLow, rule));
            List<Alert> f = Feed(d, t, 21110, 21095, 21090);                      // breaks down and closes below
            f.AddRange(d.OnClock(t.AddMinutes(5), Tick));
            Ok(f.Count(x => x.RuleId == "rs") == 0, "sweep: a breakdown (the candle closes below) is not a sweep");
            f = Feed(d, t.AddMinutes(5).AddSeconds(2), 21092, 21104);            // then back above: closes above, from below — not a sweep of the low
            f.AddRange(d.OnClock(t.AddMinutes(10), Tick));
            Ok(f.Count(x => x.RuleId == "rs") == 0, "sweep: the next candle back above a level it closed below is not a sweep of that low");

            Engine u = New(PlanJson(Pdh, "{\"id\":\"rh\",\"trigger\":\"sweep\",\"zone\":\"z1\",\"tf\":\"1m\",\"action\":\"alert\",\"message\":\"\"}"));
            List<Alert> g = Feed(u, t, 21290, 21300.25, 21296);
            g.AddRange(u.OnClock(t.AddMinutes(1), Tick));
            Ok(g.Count(x => x.RuleId == "rh") == 1, "sweep of a high (PDH) on 1m: 1 tick above, closes back under → alerts once");
        }

        // ---------- time: a New York time, once, never late; the same rule on two instruments alerts once ----------
        {
            HashSet<string> fired = new HashSet<string>();
            string rules = "{\"id\":\"rt\",\"trigger\":\"time\",\"time\":\"09:45\",\"action\":\"limit\",\"message\":\"Pause\"}";
            Engine nq = New(PlanJson(Pdh, rules), fired), es = new Engine("ES", fired);
            es.SetPlan(Plan.Parse(PlanJson("", rules)));
            DateTime t = new DateTime(2026, 11, 16, 14, 44, 58, DateTimeKind.Utc);
            List<Alert> a = new List<Alert>();
            for (int i = 0; i < 5; i++) { a.AddRange(nq.OnClock(t.AddSeconds(i), Tick)); a.AddRange(es.OnClock(t.AddSeconds(i), Tick)); }
            Ok(a.Count == 1 && a[0].RuleId == "rt" && a[0].Title == "Il est 09:45 à New York", "time 09:45 (New York): once, though NQ and ES both read it");
            Ok(a[0].Body == "Pause · Risque permis aujourd’hui : 500 $ · Trades max : 3 · Arrête après 2 pertes de suite", "« remind me of my limit » = the limits Sweep knows (" + a[0].Body + ")");
            Engine late = New(PlanJson(Pdh, rules));
            Ok(late.OnClock(t.AddMinutes(1), Tick).Count == 0 && late.OnClock(t.AddMinutes(2), Tick).Count == 0, "time: an add-on started after 09:45 does not alert late");
            Ok(Engine.NyInstant(Day, "09:30") == new DateTime(2026, 11, 16, 14, 30, 0, DateTimeKind.Utc) && Engine.NyInstant("2026-07-15", "09:30") == new DateTime(2026, 7, 15, 13, 30, 0, DateTimeKind.Utc), "time: 9:30 New York = 14:30 UTC in November, 13:30 UTC in July");
            Ok(Engine.NyInstant(Day, "20:00") == new DateTime(2026, 11, 16, 1, 0, 0, DateTimeKind.Utc), "time: 20:00 of Monday's trading day is Sunday evening (New York)");
            Ok(Engine.DayOf(new DateTime(2026, 11, 13, 23, 30, 0, DateTimeKind.Utc)) == "2026-11-16" && Engine.DayOf(new DateTime(2026, 11, 16, 21, 59, 0, DateTimeKind.Utc)) == "2026-11-16" && Engine.DayOf(new DateTime(2026, 11, 16, 23, 0, 0, DateTimeKind.Utc)) == "2026-11-17", "the trading day: Friday 18:30 → Monday; Monday 16:59 → Monday; Monday 18:00 → Tuesday");
        }

        // ---------- two charts of one instrument (1m and 5m, NQ and MNQ): one engine, one alert ----------
        {
            Engine e = New(PlanJson(Pdh, ""));
            List<Alert> a = new List<Alert>();
            DateTime t = T0;
            foreach (double px in new[] { 21280.0, 21295, 21300 }) { a.AddRange(e.OnPrice(px, t, Tick)); a.AddRange(e.OnPrice(px, t, Tick)); t = t.AddSeconds(1); }
            Ok(Count(a, "approach") == 1 && Count(a, "enter") == 1, "two charts feeding the same prices: one « approaching », one « price on »");
        }

        // ---------- the plan changes during the session; a new day; re-arm ----------
        {
            HashSet<string> fired = new HashSet<string>();
            Engine e = New(PlanJson(Pdh, ""), fired);
            Feed(e, T0, 21295, 21300);
            e.SetPlan(Plan.Parse(PlanJson(Pdh.Replace("Watch the reaction", "New note") + "," + AsiaLow, "")));
            Ok(Feed(e, T0.AddMinutes(1), 21295, 21300).Count == 0, "the plan changed during the session: what already alerted stays done");
            string key = e.KeyOf(Day, "zone:z1:enter");
            e.Rearm(key);
            List<Alert> r = Feed(e, T0.AddMinutes(2), 21310, 21300);
            Ok(r.Count == 1 && r[0].Key == key, "re-arm « price on PDH »: it alerts again, once");
            e.SetPlan(Plan.Parse(PlanJson(Pdh, "", "fr", "2026-11-17")));
            List<Alert> n = Feed(e, new DateTime(2026, 11, 17, 14, 31, 0, DateTimeKind.Utc), 21250, 21296, 21300);
            Ok(Count(n, "approach") == 1 && Count(n, "enter") == 1 && n.All(x => x.Day == "2026-11-17"), "a new trading day: its plan alerts afresh");
        }

        // ---------- English and Spanish ----------
        {
            Engine en = New(PlanJson(BuyZone, "{\"id\":\"rs\",\"trigger\":\"sweep\",\"zone\":\"z2\",\"tf\":\"15m\",\"action\":\"limit\",\"message\":\"\"}", "en"));
            Engine es = New(PlanJson(BuyZone, "", "es"));
            List<Alert> a = Feed(es, T0, 21250, 21205, 21190);
            Ok(a.Count == 2 && a[0].Title == "Te acercas a Zone d’achat" && a[1].Title == "El precio entra en Zone d’achat", "Spanish: « Te acercas a … », « El precio entra en … »");
            Ok(Texts.Title("en", "close_below", Plan.Parse(PlanJson(Pdh, "")).Zones[0], 5, "") == "5m candle closed below PDH" && Texts.NoPlan("en") == "No plan for today in Sweep." && Texts.NoPlan("fr") == "Pas de plan pour aujourd’hui dans Sweep." && Texts.NoPlan("es") == "No hay plan para hoy en Sweep.", "English texts, and « no plan today » in the 3 languages");
            Plan none = Plan.Parse("{\"day\":\"" + Day + "\",\"lang\":\"en\",\"empty\":true,\"zones\":[],\"rules\":[],\"plan\":null,\"limits\":null,\"version\":\"v\"}");
            Ok(none.Empty && none.Limits == null && Texts.Body(none, new Rule { Action = "limit" }, null) == "No limit set in Sweep for today.", "no plan, no limits: the limit reminder says so");
            // (step 4) NinjaTrader 8: no key yet → where to paste it, in the 3 languages
            Ok(new[] { "en", "fr", "es" }.All(l => Texts.NoKeyNinja(l).Contains("Control Center › New › Sweep Sync") && Texts.NoKeyNinja(l).Contains("NinjaTrader 8")) && Texts.NoKeyNinja("fr").StartsWith("Sweep Plan : dans NinjaTrader") && Texts.NoKeyNinja("es").StartsWith("Sweep Plan: en NinjaTrader") && Texts.NoKeyNinja("de") == Texts.NoKeyNinja("en"), "NinjaTrader 8, no key: « Control Center › New › Sweep Sync » in EN, FR and ES");
        }

        // ---------- (step 4) NinjaTrader 8's names: « NQ 12-26 » and its MasterInstrument « NQ »; MNQ reads NQ ----------
        {
            Ok(Roots.Root("NQ 12-26", "NQ") == "NQ" && Roots.Root("MNQ 12-26", "MNQ") == "NQ" && Roots.Root("ES 03-27", "ES") == "ES" && Roots.Root("MES 03-27", "MES") == "ES" && Roots.Root("GC 02-27", "GC") == "GC" && Roots.Root("MGC 02-27", "MGC") == "GC", "NinjaTrader 8 names (« NQ 12-26 », « MNQ 12-26 »…) → NQ, NQ, ES, ES, GC, GC");
        }

        // ---------- the events Sweep receives (api/plan-sync/events) ----------
        {
            Engine e = New(PlanJson(Pdh, "{\"id\":\"r1\",\"trigger\":\"enter\",\"zone\":\"z1\",\"action\":\"alert\",\"message\":\"x\"}"));
            List<Alert> a = Feed(e, T0, 21290, 21300);
            string j1 = Events.Json(a[0]), j2 = Events.Json(a[1]);
            Ok(Regex.IsMatch(Events.Id(a[0]), "^[A-Za-z0-9_.:-]{8,64}$") && Events.Id(a[0]) == "ps.20261116.zz1.a" && Events.Id(a[1]) == "ps.20261116.rr1", "event ids: what the server accepts, the same alert of the day always the same id (" + Events.Id(a[0]) + ", " + Events.Id(a[1]) + ")");
            Ok(j1 == "{\"id\":\"ps.20261116.zz1.a\",\"type\":\"zone_approached\",\"at\":\"2026-11-16T14:31:00.000Z\",\"instrument\":\"NQ\",\"price\":21290,\"zone\":\"z1\"}", "event JSON: id, type, at (UTC), instrument, price, zone (" + j1 + ")");
            Ok(j2.Contains("\"type\":\"rule_triggered\"") && j2.Contains("\"rule\":\"r1\"") && Regex.IsMatch(j2, "\"at\":\"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z\""), "a rule's event: rule_triggered with its rule");
            Ok(Events.Body(new List<string> { j1, j2 }, 1) == "{\"events\":[" + j1 + "]}", "a request takes at most N events");
            Dictionary<string, object> back = Json.Parse(Events.Body(new List<string> { j1, j2 }, 100)) as Dictionary<string, object>;
            Ok(back != null && Json.List(back, "events").Count == 2, "the request is valid JSON");
        }

        Console.WriteLine();
        Console.WriteLine(oks + " ok, " + fails + " failed");
        Environment.Exit(fails == 0 ? 0 : 1);
    }
}
