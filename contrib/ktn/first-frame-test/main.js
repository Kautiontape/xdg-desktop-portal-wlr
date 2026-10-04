// Times desktopCapturer.getSources() the way Vesktop calls it on Wayland: it only
// resolves once Chromium has a thumbnail, i.e. once a frame actually reached it.
const { app, desktopCapturer } = require("electron");
const types = (process.env.FF_TYPES || "window").split(",");
app.whenReady().then(async () => {
    const t0 = Date.now();
    const timer = setTimeout(() => {
        console.log(JSON.stringify({ result: "TIMEOUT", ms: Date.now() - t0 }));
        app.exit(2);
    }, Number(process.env.FF_TIMEOUT_MS || 15000));
    try {
        const sources = await desktopCapturer.getSources({
            types,
            thumbnailSize: { width: 1920, height: 1080 },
        });
        clearTimeout(timer);
        console.log(JSON.stringify({
            result: "OK",
            ms: Date.now() - t0,
            sources: sources.length,
            thumbnailEmpty: sources.map(s => s.thumbnail.isEmpty()),
        }));
        app.exit(0);
    } catch (e) {
        console.log(JSON.stringify({ result: "ERROR", error: String(e) }));
        app.exit(1);
    }
});
