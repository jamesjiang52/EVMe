document.addEventListener("updateEVsEvent", function (e) {
    var [hp, atk, def, spa, spd, spe, nature] = e.detail;
    
    var set = window.room.curSet;
    set.nature = nature;
    set.evs["hp"] = parseInt(hp);
    set.evs["atk"] = parseInt(atk);
    set.evs["def"] = parseInt(def);
    set.evs["spa"] = parseInt(spa);
    set.evs["spd"] = parseInt(spd);
    set.evs["spe"] = parseInt(spe);
    window.room.updateStatForm();
});
