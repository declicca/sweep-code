// Plan Sync on NinjaTrader 8, the add-on's own code against a Sweep test server (tests/ninjatrader_plan_test.py): the plan read
// with Sweep Sync's key, two charts (MNQ, NQ) → one engine, alerts once in NinjaTrader's Alerts window, the events sent to Sweep,
// another platform's key refused with Sweep's message. NinjaTrader's API is stubbed; the network, files and logic are real.
using System;
using System.IO;
using System.Threading;
using NinjaTrader.Cbi;
using NinjaTrader.NinjaScript.AddOns;
using SP = SweepPlanSync;

static class Program
{
    static int fails;
    static void Ok(bool c, string what) { if (!c) fails++; Console.WriteLine((c ? "ok   " : "FAIL ") + what); }
    static bool Wait(Func<bool> c, int seconds) { for (int i = 0; i < seconds * 10; i++) { if (c()) return true; Thread.Sleep(100); } return c(); }

    static int Main(string[] args)
    {
        string url = args[0], key = args[1], otherKey = args[2];
        string folder = Environment.GetEnvironmentVariable("SWEEP_PLAN_TEST_DIR");
        SweepSyncEngine.Key = key;
        SweepSyncEngine.Url = url.TrimEnd('/') + "/api/sync/push";
        Instrument mnq = new Instrument { FullName = "MNQ 12-26" }; mnq.MasterInstrument.Name = "MNQ";
        Instrument nq = new Instrument { FullName = "NQ 12-26" }; nq.MasterInstrument.Name = "NQ";
        string r1 = SP.Roots.Root(mnq.FullName, mnq.MasterInstrument.Name), r2 = SP.Roots.Root(nq.FullName, nq.MasterInstrument.Name);
        Ok(r1 == "NQ" && r2 == "NQ", "« MNQ 12-26 » and « NQ 12-26 » are the same instrument: NQ");
        SweepPlanHost.Register(r1, mnq, "chart MNQ 1m");
        SweepPlanHost.Register(r2, nq, "chart NQ 5m");
        Ok(Wait(() => { SP.Plan p = SweepPlanHost.Snapshot("NQ").Plan; return p != null && !p.Empty; }, 10), "the day's plan read with Sweep Sync's key, within seconds");
        SP.Plan plan = SweepPlanHost.Snapshot("NQ").Plan;
        Ok(plan != null && plan.Zones.Count == 1 && plan.Zones[0].Price == 21300 && plan.Lang == "fr", "the NQ level (21300), in the trader's language (fr)");
        Ok(File.Exists(Path.Combine(folder, "plan-NQ.json")), "the last plan kept on disk (plan-NQ.json): it stays if Sweep becomes unreachable");
        DateTime t = DateTime.UtcNow;
        foreach (double p in new double[] { 21250, 21295, 21296, 21300, 21301 })
        {
            SweepPlanHost.Price("NQ", p, t, 0.25);   // the MNQ chart
            SweepPlanHost.Price("NQ", p, t, 0.25);   // the NQ chart, same price
            t = t.AddSeconds(1);
        }
        Ok(NinjaTrader.NinjaScript.Alert.Calls == 2, "approach then touch: 2 alerts in NinjaTrader's Alerts window, not 4 for 2 charts (" + NinjaTrader.NinjaScript.Alert.Calls + ")");
        Ok(NinjaTrader.NinjaScript.Alert.Last.StartsWith("Sweep Plan · Le prix touche PDH"), "the alert's text: « Sweep Plan · Le prix touche PDH … » (" + NinjaTrader.NinjaScript.Alert.Last + ")");
        SweepPlanHost.View v = SweepPlanHost.Snapshot("NQ");
        Ok(v.BannerKind == "alert" && v.BannerKey.Length > 0 && v.Banner.StartsWith("Le prix touche PDH"), "the chart's banner shows the last alert, with « Réarmer »");
        string events = Path.Combine(folder, "events.txt");
        Ok(Wait(() => File.Exists(events) && File.ReadAllText(events).Trim().Length == 0, 10), "the 2 events sent to Sweep right away (events.txt emptied)");
        Ok(File.ReadAllText(Path.Combine(folder, "fired.txt")).Contains("|zone:" + plan.Zones[0].Id + ":enter"), "what alerted today is kept (fired.txt): a restart does not alert again");
        SweepPlanHost.Rearm("NQ", v.BannerKey);
        SweepPlanHost.Price("NQ", 21250, t.AddSeconds(1), 0.25);
        SweepPlanHost.Price("NQ", 21300, t.AddSeconds(2), 0.25);
        Ok(NinjaTrader.NinjaScript.Alert.Calls == 3, "« Réarmer »: the touch alerts once more, and once only (" + NinjaTrader.NinjaScript.Alert.Calls + ")");
        // a Quantower key pasted in Sweep Sync: Sweep's message, in the trader's language
        SweepSyncEngine.Key = otherKey;
        SweepPlanHost.Register("ES", new Instrument { FullName = "ES 12-26" }, "chart ES");
        Ok(Wait(() => SweepPlanHost.Snapshot("ES").Banner.StartsWith("Sweep Plan: "), 10), "another platform's key: the banner says so (" + SweepPlanHost.Snapshot("ES").Banner + ")");
        SweepSyncEngine.Key = "";
        SweepPlanHost.Register("GC", new Instrument { FullName = "GC 02-27" }, "chart GC");
        Ok(Wait(() => SweepPlanHost.Snapshot("GC").Banner.Contains("Control Center › New › Sweep Sync"), 20), "no key: where to paste it (" + SweepPlanHost.Snapshot("GC").Banner + ")");
        Console.WriteLine("folder " + folder);
        Console.WriteLine(fails == 0 ? "all passed" : fails + " failed");
        return fails == 0 ? 0 : 1;
    }
}
