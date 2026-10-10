using LatchiWatching.Core;
using Xunit;
namespace LatchiWatching.Tests;
public class SourceTests
{
    [Fact] public void ExactlyEightOrderedSources(){Assert.Equal(new[]{"3isk","eseek","Krmzy","MyCimaProvider","Topcinema","TukTukcima","Tuniflix","Wecima"},Sources.All.Select(s=>s.Id));Assert.Equal(8,Sources.All.Select(s=>s.Id).Distinct().Count());}
    [Fact] public void EverySourceHasIndependentNamesImageAndHttpsWebsite(){foreach(var s in Sources.All){Assert.NotEmpty(s.Arabic);Assert.NotEmpty(s.English);Assert.StartsWith("assets/sources/",s.Image);Assert.True(Sources.IsSafeWebsite(s.Url));}}
    [Theory][InlineData("https://example.com")][InlineData("https://web8.topcinema.cam/path?q=1")][InlineData("https://qeseh.net/")]
    public void AcceptsOrdinaryPublicHttps(string url)=>Assert.True(Sources.IsSafeWebsite(url));
    [Theory][InlineData("javascript:alert(1)")][InlineData("file:///C:/Windows")][InlineData("http://example.com")][InlineData("https://localhost/")][InlineData("https://127.0.0.1/")][InlineData("https://[::1]/")][InlineData("https://example.local/")][InlineData("https://user:pass@example.com/")][InlineData("https://example.com:444/")][InlineData("https://example.test/")][InlineData("data:text/html,test")][InlineData("")]
    public void RejectsUnsafeNavigation(string url)=>Assert.False(Sources.IsSafeWebsite(url));
    [Fact] public void TrustedUiOriginCannotBeSpoofed(){Assert.True(Sources.IsAppOrigin("https://app.local/index.html"));Assert.False(Sources.IsAppOrigin("https://app.local.evil.example/index.html"));Assert.False(Sources.IsAppOrigin("http://app.local/index.html"));Assert.False(Sources.IsAppOrigin("https://app.local:444/index.html"));}
    [Fact] public void OverridesStayWithinKnownSourceIds(){var result=Sources.ValidateOverrides(new Dictionary<string,string>{{"3isk","https://example.com/"}});Assert.Equal("https://example.com/",result["3isk"]);Assert.Throws<ArgumentException>(()=>Sources.ValidateOverrides(new Dictionary<string,string>{{"unknown","https://example.com/"}}));Assert.Throws<ArgumentException>(()=>Sources.ValidateOverrides(new Dictionary<string,string>{{"3isk","file:///etc/passwd"}}));}
    [Fact] public void RegistryLookupIsExactAndDoesNotFallBackToAnotherProduct(){Assert.Null(Sources.Find("play"));Assert.Null(Sources.Find("3ISK"));Assert.NotNull(Sources.Find("3isk"));}
}
