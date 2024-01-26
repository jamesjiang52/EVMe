document.body.querySelector("#update-pokepaste-btn").addEventListener("click", async () => {
	const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
	const resp = await chrome.tabs.sendMessage(tab.id, {
		name: "get-mon-data",
		data: null
	});
	if (resp === undefined) {
		document.body.querySelector("#pokepaste-text").innerText = "Please update set with a Pokémon, ability, and held item."
	} else {
		document.body.querySelector("#pokepaste-text").innerText = resp;
	}
});

function showSpreads(data) {
    var spreads_list = document.body.querySelector("#spreads-list");
    spreads_list.innerHTML = "";
    
    if (data === undefined) {
        document.body.querySelector("#spreads-text").innerText = "Something went wrong. Please check if input paste is valid and native application is correctly installed. If yes, send input and options to jamesjiang52@gmail.com.";
        return;
    }

    document.body.querySelector("#spreads-text").innerText = "";

    var spread_count = 0;
    for (spread of data.text) {
        entry_div = document.createElement("div");
        entry_div.className = "w3-input w3-border";

        var use_spread_btn = document.createElement("button");
        use_spread_btn.id = "use-spread-btn" + String(spread_count);
        use_spread_btn.className = "w3-button w3-blue-grey";
        use_spread_btn.innerHTML = "Use this spread";
        entry_div.appendChild(use_spread_btn);

        var spread_str = "";
        var EV_list = spread[2];
        spread_str += EV_list[0] + " HP / " + EV_list[1] + " Atk / " + EV_list[2] + " Def / " + EV_list[3] + " SpA / " + EV_list[4] + " SpD / " + EV_list[5] + " Spe<br>";
        spread_str += spread[1] + " Nature<br>";
        spread_str += spread[0] + " Remaining EVs";
        
        var spread_p = document.createElement("p");
        spread_p.id = "spread-p" + String(spread_count);
        spread_p.innerHTML = spread_str;
        entry_div.appendChild(spread_p);
        
        var calcs_list = document.createElement("ul");
        
        for (calc of spread[3]) {
            if (calc !== "N/A") {
                calc_li = document.createElement("li");
                calc_li.textContent = calc;
                calcs_list.appendChild(calc_li);
            }
        }
        calcs_list.className = "w3-ul";
        entry_div.appendChild(calcs_list);
        
        spreads_list.appendChild(entry_div);
        
        entry_break = document.createElement("br");
        spreads_list.appendChild(entry_break);
        
        spread_count += 1;
    }
}

document.body.querySelector("#submit-btn").addEventListener("click", async () => {
    var bias1 = null;
    var bias2 = null;
    
    if (document.querySelector('#HP').checked) {
        if (bias1 == null) bias1 = "HP";
        else if (bias2 == null) bias2 = "HP";
    }
    if (document.querySelector('#Atk').checked) {
        if (bias1 == null) bias1 = "Atk";
        else if (bias2 == null) bias2 = "Atk";
    }
    if (document.querySelector('#Def').checked) {
        if (bias1 == null) bias1 = "Def";
        else if (bias2 == null) bias2 = "Def";
    }
    if (document.querySelector('#SpA').checked) {
        if (bias1 == null) bias1 = "SpA";
        else if (bias2 == null) bias2 = "SpA";
    }
    if (document.querySelector('#SpD').checked) {
        if (bias1 == null) bias1 = "SpD";
        else if (bias2 == null) bias2 = "SpD";
    }
    if (document.querySelector('#Spe').checked) {
        if (bias1 == null) bias1 = "Spe";
        else if (bias2 == null) bias2 = "Spe";
    }
    
    const args = {
        "mon_data": document.body.querySelector("#pokepaste-text").innerText,
        "num_mons": document.body.querySelector("#num-meta-mons").value,
        "num_spreads": document.body.querySelector("#num-spreads").value,
        "bias1": bias1,
        "bias2": bias2
        //"moveset_url": "https://www.smogon.com/stats/2023-11/moveset/gen9vgc2023regulationebo3-1760.txt",
        //"chaos_url": "https://www.smogon.com/stats/2023-11/chaos/gen9vgc2023regulationebo3-1760.json"
        //"moveset_url": document.body.querySelector("#moveset-url").value,
        //"chaos_url": document.body.querySelector("#chaos-url").value
    }

    document.body.querySelector("#spreads-text").innerText = "Calculating spreads (this could take a few minutes)...";

    chrome.runtime.sendNativeMessage(
        "com.jamesjiang52.evme",
        {text: args},
        showSpreads
    );
});

document.body.querySelector("#spreads-list").addEventListener("click", async (event) => {
    const btn_regexp = /use-spread-btn(\d+)/g;
    const btn_match = [...event.target.id.matchAll(btn_regexp)];

    if (btn_match[0] !== undefined) {
        const spread_num = btn_match[0][1];
        const spread_regexp = /(\d+) HP \/ (\d+) Atk \/ (\d+) Def \/ (\d+) SpA \/ (\d+) SpD \/ (\d+) Spe<br>([A-Za-z]+) Nature/g;
        const spread_match = [...document.body.querySelector("#spread-p" + spread_num).innerHTML.matchAll(spread_regexp)][0];

        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        chrome.tabs.sendMessage(tab.id, {
            name: "update-evs",
            data: spread_match.slice(1)
        });
    }
});
