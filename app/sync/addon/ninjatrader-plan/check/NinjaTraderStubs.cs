// Compile check only (tests/ninjatrader_plan_test.py): the few parts of NinjaTrader 8's API that Sweep Plan uses, with their
// documented shapes (help guide: NinjaScript, OnRender, SetZOrder, AlertCallback, ChartingExtensions). Never shipped.
using System;
namespace NinjaTrader.Cbi
{
    public class MasterInstrument { public string Name = ""; public double TickSize = 0.25; }
    public class Instrument { public string FullName = ""; public MasterInstrument MasterInstrument = new MasterInstrument(); }
}
namespace NinjaTrader.Data { public class Bars { } }
namespace NinjaTrader.Gui { public class Stroke { } }
namespace NinjaTrader.Gui.Tools { public class SimpleFont { } }
namespace NinjaTrader.Core
{
    public static class Globals
    {
        public static SharpDX.DirectWrite.Factory DirectWriteFactory;
        public static DateTime Now { get { return DateTime.Now; } }
        public static string InstallDir = "";
    }
}
namespace NinjaTrader.Code { public static class Output { public static void Process(string text, NinjaTrader.NinjaScript.PrintTo to) { } } }
namespace NinjaTrader.Gui.Chart
{
    public class ChartControl : System.Windows.Controls.UserControl { public System.Windows.PresentationSource PresentationSource { get { return null; } } }
    public class ChartScale { public int GetYByValue(double value) { return 0; } }
    public class ChartPanel { public int X, Y, W, H; }
    public static class ChartingExtensions
    {
        public static int ConvertToHorizontalPixels(this double x, System.Windows.PresentationSource target) { return 0; }
        public static int ConvertToVerticalPixels(this double y, System.Windows.PresentationSource target) { return 0; }
    }
}
namespace NinjaTrader.NinjaScript
{
    public enum State { SetDefaults, Configure, Active, DataLoaded, Historical, Transition, Realtime, Terminated, Finalized }
    public enum Calculate { OnBarClose, OnEachTick, OnPriceChange }
    public enum Priority { High, Low, Medium }
    public enum PrintTo { OutputTab1, OutputTab2 }
    public interface ISeries<T> { T this[int barsAgo] { get; } }
    public class Alert
    {
        public static int Calls; public static string Last = "";   // what the live run (run/) counts
        public static void AlertCallback(NinjaTrader.Cbi.Instrument instrument, object source, string id, DateTime time, Priority priority, string message, string soundLocation, System.Windows.Media.Brush backBrush, System.Windows.Media.Brush foreBrush, int rearmSeconds)
        {
            if (id == null) throw new ArgumentNullException("id");
            System.Threading.Interlocked.Increment(ref Calls); Last = message;
        }
    }
    public abstract class NinjaScriptBase
    {
        public string Name, Description;
        public State State;
        public Calculate Calculate;
        public bool IsOverlay, DisplayInDataBox, DrawOnPricePanel, PaintPriceMarkers, IsAutoScale, IsSuspendedWhileInactive;
        public NinjaTrader.Cbi.Instrument Instrument;
        public double TickSize;
        public int CurrentBar;
        public ISeries<double> Close, Input;
        protected virtual void OnStateChange() { }
        protected virtual void OnBarUpdate() { }
        public bool EqualsInput(object input) { return false; }
        protected T CacheIndicator<T>(T indicator, ISeries<double> input, ref T[] cache) { return indicator; }
    }
    public class MarketAnalyzerColumnBase { protected NinjaTrader.NinjaScript.Indicators.Indicator indicator; public ISeries<double> Input; }
}
namespace NinjaTrader.Gui.NinjaScript
{
    public class IndicatorRenderBase : NinjaTrader.NinjaScript.NinjaScriptBase
    {
        public NinjaTrader.Gui.Chart.ChartControl ChartControl;
        public NinjaTrader.Gui.Chart.ChartPanel ChartPanel;
        public SharpDX.Direct2D1.RenderTarget RenderTarget;
        protected virtual void OnRender(NinjaTrader.Gui.Chart.ChartControl chartControl, NinjaTrader.Gui.Chart.ChartScale chartScale) { }
        public void SetZOrder(int z) { }
        public void ForceRefresh() { }
    }
    public class StrategyRenderBase { protected NinjaTrader.NinjaScript.Indicators.Indicator indicator; public NinjaTrader.NinjaScript.ISeries<double> Input; }
}
namespace NinjaTrader.NinjaScript.Indicators { public partial class Indicator { } }
namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns { public partial class MarketAnalyzerColumn { } }
namespace NinjaTrader.NinjaScript.Strategies { public partial class Strategy { } }
// Sweep Sync (AddOns/SweepSync.cs, compiled in the same assembly in NinjaTrader): only what Sweep Plan reads
namespace NinjaTrader.NinjaScript.AddOns { public static class SweepSyncEngine { public static string Key = ""; public static string Url = "https://app.makeitsweep.com/api/sync/push"; } }
