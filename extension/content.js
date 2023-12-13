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
            paste = "Please input a Pokemon, its ability, and a held item.";
        }

		sendResponse(paste);
	}
});

chrome.runtime.onMessage.addListener(({name, data}) => {
    if (name === "update-evs") {
        console.log("received update EVs message");
        var [hp, atk, def, spa, spd, spe, nature] = data;
        console.log(hp, atk, def, spa, spd, spe, nature)
        
        var atk_mod = "";
        var def_mod = "";
        var spa_mod = "";
        var spd_mod = "";
        var spe_mod = "";
        
        if (["Lonely", "Adamant", "Naughty", "Brave"].includes(nature))
            atk_mod = "+";
        else if (["Bold", "Modest", "Calm", "Timid"].includes(nature))
            atk_mod = "-";
        
        if (["Bold", "Impish", "Lax", "Relaxed"].includes(nature))
            def_mod = "+";
        else if (["Lonely", "Mild", "Gentle", "Hasty"].includes(nature))
            def_mod = "-";
        
        if (["Modest", "Mild", "Rash", "Quiet"].includes(nature))
            spa_mod = "+";
        else if (["Adamant", "Impish", "Careful", "Jolly"].includes(nature))
            spa_mod = "-";
        
        if (["Calm", "Gentle", "Careful", "Sassy"].includes(nature))
            spd_mod = "+";
        else if (["Naughty", "Lax", "Rash", "Naive"].includes(nature))
            spd_mod = "-";
        
        if (["Timid", "Hasty", "Jolly", "Naive"].includes(nature))
            spe_mod = "+";
        else if (["Brave", "Relaxed", "Quiet", "Sassy"].includes(nature))
            spe_mod = "-";
        
        document.body.querySelector("[name=stat-hp]").value = hp;
        document.body.querySelector("[name=stat-atk]").value = atk + atk_mod;
        document.body.querySelector("[name=stat-def]").value = def + def_mod;
        document.body.querySelector("[name=stat-spa]").value = spa + spa_mod;
        document.body.querySelector("[name=stat-spd]").value = spd + spd_mod;
        document.body.querySelector("[name=stat-spe]").value = spe + spe_mod;
        
        document.body.querySelector("[name=evslider-hp]").value = hp;
        document.body.querySelector("[name=evslider-atk]").value = atk;
        document.body.querySelector("[name=evslider-def]").value = def;
        document.body.querySelector("[name=evslider-spa]").value = spa;
        document.body.querySelector("[name=evslider-spd]").value = spd;
        document.body.querySelector("[name=evslider-spe]").value = spe;
        
        document.body.querySelector("[name=nature]").value = nature;
    }
})
