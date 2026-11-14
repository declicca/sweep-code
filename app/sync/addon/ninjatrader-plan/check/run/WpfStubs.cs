// The live run (tests/ninjatrader_plan_test.py) runs on the Mac, where WPF does not exist: the few WPF types Sweep Plan names.
using System;
namespace System.Windows
{
    public struct Point { public double X, Y; }
    public interface IInputElement { }
    public class PresentationSource { }
}
namespace System.Windows.Threading { public class Dispatcher { public void InvokeAsync(Action a) { a(); } } }
namespace System.Windows.Input
{
    public class MouseButtonEventArgs : EventArgs { public bool Handled; public System.Windows.Point GetPosition(System.Windows.IInputElement e) { return new System.Windows.Point(); } }
    public delegate void MouseButtonEventHandler(object sender, MouseButtonEventArgs e);
}
namespace System.Windows.Controls
{
    public class UserControl : System.Windows.IInputElement
    {
        public System.Windows.Threading.Dispatcher Dispatcher = new System.Windows.Threading.Dispatcher();
        public event System.Windows.Input.MouseButtonEventHandler PreviewMouseLeftButtonDown;
        public void Click() { if (PreviewMouseLeftButtonDown != null) PreviewMouseLeftButtonDown(this, new System.Windows.Input.MouseButtonEventArgs()); }
    }
}
namespace System.Windows.Media
{
    public struct Color { public byte R, G, B; public static Color FromRgb(byte r, byte g, byte b) { Color c; c.R = r; c.G = g; c.B = b; return c; } }
    public static class Colors { public static Color White { get { return Color.FromRgb(255, 255, 255); } } }
    public class Brush { public void Freeze() { } }
    public class SolidColorBrush : Brush { public SolidColorBrush(Color c) { } }
}
