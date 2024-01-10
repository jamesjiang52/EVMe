chrome.runtime.onMessage.addListener(({name, data}, sender, sendResponse) => {
	if (name === "get-mon-data") {
		var name = document.body.querySelector("[name=pokemon]").value;
		var item = document.body.querySelector("[name=item]").value;
		var ability = document.body.querySelector("[name=ability]").value;
        
        var move1 = document.body.querySelector("[name=move1]").value;
        var move2 = document.body.querySelector("[name=move2]").value;
        var move3 = document.body.querySelector("[name=move3]").value;
        var move4 = document.body.querySelector("[name=move4]").value;
        
        var paste;
        
        if (name && item && ability) {
            paste = name + " @ " + item + "\nAbility: " + ability;
            if (move1) paste += "\n- " + move1;
            if (move2) paste += "\n- " + move2;
            if (move3) paste += "\n- " + move3;
            if (move4) paste += "\n- " + move4;
        } else {
            paste = "Please update set with a Pokémon, ability, and held item.";
        }

		sendResponse(paste);
    } else if (name === "update-evs") {
        document.dispatchEvent(new CustomEvent("updateEVsEvent", {detail: data}));
    }
});

/*
chrome.runtime.onMessage.addListener(({name, data}) => {
    if (name === "update-evs") {
        document.dispatchEvent(new CustomEvent("updateEVsEvent", {detail: data}));
    }
})
*/
