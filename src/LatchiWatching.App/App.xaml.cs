using System.IO;
using System.Windows;
namespace LatchiWatching.App;
public partial class App : Application
{
    public static string? TestFixture {get;private set;}
    public static string? TestOutput {get;private set;}
    public static bool IsTest => TestFixture is not null;
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        if(e.Args.Length==3 && e.Args[0]=="--self-test") {TestFixture=Path.GetFullPath(e.Args[1]);TestOutput=Path.GetFullPath(e.Args[2]);Directory.CreateDirectory(TestOutput);}
        DispatcherUnhandledException += (_,ev) => { Log(ev.Exception); if(IsTest) {ev.Handled=true;Shutdown(2);} };
        var main=new MainWindow();MainWindow=main;main.Show();
    }
    public static void Log(Exception ex)
    {
        try {var dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"LATCHI","WatchingWindows");Directory.CreateDirectory(dir);File.AppendAllText(Path.Combine(dir,"errors.log"),DateTime.UtcNow.ToString("O")+" "+ex+Environment.NewLine);}catch{}
    }
}
