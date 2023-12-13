const SHOWDOWN_TEAMBUILDER_URL = "https://play.pokemonshowdown.com";

chrome.sidePanel
	.setPanelBehavior({openPanelOnActionClick: true})
	.catch((error) => console.error(error));

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
	if (!tab.url) return;
	const url = new URL(tab.url);
	if (url.origin === SHOWDOWN_TEAMBUILDER_URL) {
		await chrome.sidePanel.setOptions({
			tabId,
			path: "sidepanel.html",
			enabled: true
		});
	} else {
		await chrome.sidePanel.setOptions({
			tabId,
			enabled: false
		});
	}
});
