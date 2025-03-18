import pulp
import re
import tkinter
def solve():
    #requirements
    resultlabel.config(text="")
    M = 10000
    inittier2conpoints = 0
    inittier3conpoints = 0
    minorbis = 0
    minasteroidbase = 0
    mincoriolis = 0
    mincommercialoutpost = 0
    minindustrialoutpost = 0
    mincriminaloutpost = 0
    mincivilianoutpost = 0
    minscientificoutpost = 0
    minmilitaryoutpost = 0
    maxpiratebase = 0
    maxcriminaloutpost = 0
    maximize = maximizeinput.get()

    def convert_maybe(value, default=0):
        if value != "": return int(value)
        return default

    mininitialpopulationincrease = convert_maybe(minvars["initialpopulationincrease"].get())
    minmaxpopulationincrease = convert_maybe(minvars["maxpopulationincrease"].get())
    minsecurity = convert_maybe(minvars["security"].get())
    mintechlevel = convert_maybe(minvars["techlevel"].get())
    minwealth = convert_maybe(minvars["wealth"].get())
    minstandardofliving = convert_maybe(minvars["standardofliving"].get())
    mindevelopmentlevel = convert_maybe(minvars["developmentlevel"].get())

    maxinitialpopulationincrease = convert_maybe(maxvars["initialpopulationincrease"].get(), default=None)
    maxmaxpopulationincrease = convert_maybe(maxvars["maxpopulationincrease"].get(), default=None)
    maxsecurity = convert_maybe(maxvars["security"].get(), default=None)
    maxtechlevel = convert_maybe(maxvars["techlevel"].get(), default=None)
    maxwealth = convert_maybe(maxvars["wealth"].get(), default=None)
    maxstandardofliving = convert_maybe(maxvars["standardofliving"].get(), default=None)
    maxdevelopmentlevel = convert_maybe(maxvars["developmentlevel"].get(), default=None)

    orbitalfacilityslots = orbitalfacilityslotsinput.get()
    groundfacilityslots = groundfacilityslotsinput.get()
    asteroidslots = asteroidslotsinput.get()
    idk2 = criminalinput.get()
    if idk2:
        maxpiratebase = M
        maxcriminaloutpost = M
    idk = firststationinput.get()
    if idk == "orbis" or idk == "ocellus":
        minorbis = 1
        inittier3conpoints += 6
    elif idk == "asteroid base":
        minasteroidbase  = 1
        inittier2conpoints += 3
        if asteroidslots == 0:
            resultlabel.config(text="Error: your starting station is an asteroid base but there are no slots for asteroid bases to be built")
            return None
    elif idk == "coriolis":
        mincoriolis = 1
        inittier2conpoints += 3
    elif idk == "commercial outpost":
        mincommercialoutpost = 1
    elif idk == "industrial outpost":
        minindustrialoutpost = 1
    elif idk == "criminal outpost":
        mincriminaloutpost = 1
        if maxcriminaloutpost == 0:
            resultlabel.config(text="Error: your starting station is a criminal outpost but you do not want criminal outposts to be built")
            return None
    elif idk == "civilian outpost":
        mincivilianoutpost = 1
    elif idk == "scientific outpost":
        minscientificoutpost = 1
    elif idk == "military outpost":
        minmilitaryoutpost = 1
    else:
        resultlabel.config(text="Error: One or more inputs are blank")
        return None
    #create all the variables for each of the facilities
    #orbital facilities
    coriolis = pulp.LpVariable('Coriolis', lowBound = mincoriolis, cat='Integer')
    orbis = pulp.LpVariable('Orbis_or_Ocellus', lowBound = minorbis, cat='Integer')
    commercialoutpost = pulp.LpVariable('Commercial_Outpost', lowBound = mincommercialoutpost, cat='Integer')
    industrialoutpost = pulp.LpVariable('Industrial_Outpost', lowBound = minindustrialoutpost, cat='Integer')
    civilianoutpost = pulp.LpVariable('Civilian_Outpost', lowBound = mincivilianoutpost, cat='Integer')
    scientificoutpost = pulp.LpVariable('Scientific_Outpost', lowBound = minscientificoutpost, cat='Integer')
    militaryoutpost = pulp.LpVariable('Military_Outpost', lowBound = minmilitaryoutpost, cat='Integer')
    satellite = pulp.LpVariable('Satellite', lowBound = 0, cat='Integer')
    communicationstation = pulp.LpVariable('Communication_Station', lowBound = 0, cat='Integer')
    spacefarm = pulp.LpVariable('Spacefarm', lowBound = 0, cat='Integer')
    miningoutpost = pulp.LpVariable('Mining_Outpost', lowBound = 0, cat='Integer')
    relaystation = pulp.LpVariable('Relay_Station', lowBound = 0, cat='Integer')
    military = pulp.LpVariable('Military', lowBound = 0, cat='Integer')
    securitystation = pulp.LpVariable('Security Station', lowBound = 0, cat='Integer')
    government = pulp.LpVariable('Government', lowBound = 0, cat='Integer')
    medical = pulp.LpVariable('Medical', lowBound = 0, cat='Integer')
    researchstation = pulp.LpVariable('Research_Station', lowBound = 0, cat='Integer')
    tourist = pulp.LpVariable('Tourist', lowBound = 0, cat='Integer')
    bar = pulp.LpVariable('Bar', lowBound = 0, cat='Integer')
    asteroidbase = pulp.LpVariable('Asteroid_Base', lowBound = minasteroidbase, upBound = asteroidslots, cat='Integer')
    criminaloutpost = pulp.LpVariable('Criminal Outpost', lowBound = mincriminaloutpost, upBound = maxcriminaloutpost, cat='Integer')
    piratebase = pulp.LpVariable('Pirate_Base', lowBound = 0, upBound = maxpiratebase, cat='Integer')
    #ground facilities
    civilianplanetaryoutpost = pulp.LpVariable('Civilian_Planetary_Outpost', lowBound = 0, cat='Integer')
    industrialplanetaryoutpost = pulp.LpVariable('Industrial_Planetary_Outpost', lowBound = 0, cat='Integer')
    scientificplanetaryoutpost = pulp.LpVariable('Scientific_Planetary_Outpost', lowBound = 0, cat='Integer')
    planetaryport = pulp.LpVariable('Planetary_Port', lowBound = 0, cat='Integer')
    smallagriculturalsettlement = pulp.LpVariable('Small_Agricultural_Settlement', lowBound = 0, cat='Integer')
    mediumagriculturalsettlement = pulp.LpVariable('Medium_Agricultural_Settlement', lowBound = 0, cat='Integer')
    largeagriculturalsettlement = pulp.LpVariable('Large_Agricultural_Settlement', lowBound = 0, cat='Integer')
    smallextractionsettlement = pulp.LpVariable('Small_Extraction_Settlement', lowBound = 0, cat='Integer')
    mediumextractionsettlement = pulp.LpVariable('Medium_Extraction_Settlement', lowBound = 0, cat='Integer')
    largeextractionsettlement = pulp.LpVariable('Large_Extraction_Settlement', lowBound = 0, cat='Integer')
    smallindustrialsettlement = pulp.LpVariable('Small_Industrial_Settlement', lowBound = 0, cat='Integer')
    mediumindustrialsettlement = pulp.LpVariable('Medium_Industrial_Settlement', lowBound = 0, cat='Integer')
    largeindustrialsettlement = pulp.LpVariable('Large_Industrial_Settlement', lowBound = 0, cat='Integer')
    smallmilitarysettlement = pulp.LpVariable('Small_Military_Settlement', lowBound = 0, cat='Integer')
    mediummilitarysettlement = pulp.LpVariable('Medium_Military_Settlement', lowBound = 0, cat='Integer')
    largemilitarysettlement = pulp.LpVariable('Large_Military_Settlement', lowBound = 0, cat='Integer')
    smallscientificsettlement = pulp.LpVariable('Small_Scientific_Settlement', lowBound = 0, cat='Integer')
    mediumscientificsettlement = pulp.LpVariable('Medium_Scientific_Settlement', lowBound = 0, cat='Integer')
    largescientificsettlement = pulp.LpVariable('Large_Scientific_Settlement', lowBound = 0, cat='Integer')
    smalltourismsettlement = pulp.LpVariable('Small_Tourism_Settlement', lowBound = 0, cat='Integer')
    mediumtourismsettlement = pulp.LpVariable('Medium_Tourism_Settlement', lowBound = 0, cat='Integer')
    largetourismsettlement = pulp.LpVariable('Large_Tourism_Settlement', lowBound = 0, cat='Integer')
    extractionhub = pulp.LpVariable('Extraction_Hub', lowBound = 0, cat='Integer')
    civilianhub = pulp.LpVariable('Civilian_Hub', lowBound = 0, cat='Integer')
    explorationhub = pulp.LpVariable('Exploration_Hub', lowBound = 0, cat='Integer')
    outposthub = pulp.LpVariable('Outpost_Hub', lowBound = 0, cat='Integer')
    scientifichub = pulp.LpVariable('Scientific_Hub', lowBound = 0, cat='Integer')
    militaryhub = pulp.LpVariable('Military_Hub', lowBound = 0, cat='Integer')
    refineryhub = pulp.LpVariable('Refinery_Hub', lowBound = 0, cat='Integer')
    hightechhub = pulp.LpVariable('Hightech_Hub', lowBound = 0, cat='Integer')
    industrialhub = pulp.LpVariable('Industrial_Hub', lowBound = 0, cat='Integer')
    #problem
    prob = pulp.LpProblem("optimal_system_colonization_layout", pulp.LpMaximize)
    #objective function
    if maximize == "initial population increase":
        prob += (5 * orbis) + (coriolis) + (scientificoutpost) + (militaryoutpost) + (10 * planetaryport) + (2 * civilianplanetaryoutpost) + (industrialplanetaryoutpost) + (scientificplanetaryoutpost) + (asteroidbase), "initial population increase"
    elif maximize == "maximum population increase":
        prob += (orbis) + (10 * planetaryport) >= minmaxpopulationincrease, "maximum population increase"
    elif maximize == "security":
        prob += (8 * securitystation) + (6 * military) + (2 * militaryoutpost) + (2 * government) + (communicationstation) + (relaystation) + (-1 * commercialoutpost) + (-1 * civilianoutpost) + (-2 * coriolis) + (-2 * bar) + (-3 * orbis) + (-3 * tourist) + (10 * militaryhub) + (6 * largemilitarysettlement) + (4 * mediummilitarysettlement) + (2 * smallmilitarysettlement) + (-1 * industrialplanetaryoutpost) + (-1 * scientificplanetaryoutpost) + (-1 * smalltourismsettlement) + (-1 * mediumtourismsettlement) + (-1 * largetourismsettlement) + (-1 * refineryhub) + (-1 * explorationhub) + (-2 * civilianplanetaryoutpost) + (-2 * hightechhub) + (-2 * outposthub) + (-3 * planetaryport) + (-3 * civilianhub) + (-1 * asteroidbase) + (-4 * piratebase) + (-2 * criminaloutpost), "security"
    elif maximize == "tech level":
        prob += (8 * researchstation) + (6 * orbis) + (3 * communicationstation) + (3 * scientificoutpost) + (3 * industrialoutpost) + (3 * medical) + (coriolis) + (10 * hightechhub) + (10 * largescientificsettlement) + (10 * scientifichub) + (6 * explorationhub) + (6 * mediumscientificsettlement) + (5 * scientificplanetaryoutpost) + (5 * planetaryport) + (3 * refineryhub) + (3 * smallscientificsettlement) + (3 * industrialhub) + (largeextractionsettlement) + (3 * asteroidbase), "tech level"
    elif maximize == "wealth":
        prob += (7 * orbis) + (6 * tourist) + (3 * miningoutpost) + (2 * coriolis) + (2 * commercialoutpost) + (2 * bar) + (civilianoutpost) + (satellite) + (10 * extractionhub) + (7 * largeextractionsettlement) + (5 * planetaryport) + (5 * mediumextractionsettlement) + (5 * largetourismsettlement) + (5 * refineryhub) + (5 * industrialhub) + (2 * industrialplanetaryoutpost) + (2 * smallextractionsettlement) + (2 * largeindustrialsettlement) + (2 * mediumtourismsettlement) + (smalltourismsettlement) + (-2 * hightechhub) + (5 * asteroidbase) + (3 * piratebase) + (2 * criminaloutpost), "wealth"
    elif maximize == "standard of living":
        prob += (6 * government) + (5 * orbis) + (5 * medical) + (5 * commercialoutpost) + (5 * spacefarm) + (3 * coriolis) + (3 * securitystation) + (3 * bar) + (civilianoutpost) + (satellite) + (-2 * miningoutpost) + (10 * largeagriculturalsettlement) + (6 * planetaryport) + (6 * mediumagriculturalsettlement) + (3 * civilianplanetaryoutpost) + (3 * outposthub) + (3 * civilianhub) + (3 * smallagriculturalsettlement) + (-2 * refineryhub) + (-2 * largeextractionsettlement) + (-4 * industrialhub) + (-4 * extractionhub) + (-4 * asteroidbase), "standard of living"
    elif maximize == "development level":
        prob += (8 * orbis) + (2 * government) + (2 * coriolis) + (2 * securitystation) + (2 * researchstation) + (2 * industrialoutpost) + (2 * tourist) + (spacefarm) + (civilianoutpost) + (satellite) + (relaystation) + (10 * planetaryport) + (8 * largeindustrialsettlement) + (7 * refineryhub) + (5 * mediumindustrialsettlement) + (2 * outposthub) + (2 * civilianhub) + (2 * industrialhub) + (2 * extractionhub) + (2 * largescientificsettlement) + (2 * explorationhub) + (2 * largemilitarysettlement) + (2 * smallindustrialsettlement) + (mediumscientificsettlement) + (scientificplanetaryoutpost) + (smallscientificsettlement) + (7 * asteroidbase), "development level"
    else:
        resultlabel.config(text="Error: One or more inputs are blank")
        return None
    #minimum and maximum stats
    initialpopulationincrease = (5 * orbis) + (coriolis) + (scientificoutpost) + (militaryoutpost) + (10 * planetaryport) + (2 * civilianplanetaryoutpost) + (industrialplanetaryoutpost) + (scientificplanetaryoutpost) + (asteroidbase)
    prob += initialpopulationincrease >= mininitialpopulationincrease, "minimum initial population increase"
    if maxinitialpopulationincrease is not None:
        prob += initialpopulationincrease <= maxinitialpopulationincrease, "maximum initial population increase"

    maxpopulationincrease = (orbis) + (10 * planetaryport)
    prob += maxpopulationincrease  >= minmaxpopulationincrease, "minimum maximum population increase"
    if maxmaxpopulationincrease is not None:
        prob += maxpopulationincrease  <= maxmaxpopulationincrease, "maximum maximum population increase"

    security = (8 * securitystation) + (6 * military) + (2 * militaryoutpost) + (2 * government) + (communicationstation) + (relaystation) + (-1 * commercialoutpost) + (-1 * civilianoutpost) + (-2 * coriolis) + (-2 * bar) + (-3 * orbis) + (-3 * tourist) + (10 * militaryhub) + (6 * largemilitarysettlement) + (4 * mediummilitarysettlement) + (2 * smallmilitarysettlement) + (-1 * industrialplanetaryoutpost) + (-1 * scientificplanetaryoutpost) + (-1 * smalltourismsettlement) + (-1 * mediumtourismsettlement) + (-1 * largetourismsettlement) + (-1 * refineryhub) + (-1 * explorationhub) + (-2 * civilianplanetaryoutpost) + (-2 * hightechhub) + (-2 * outposthub) + (-3 * planetaryport) + (-3 * civilianhub) + (-1 * asteroidbase) + (-4 * piratebase) + (-2 * criminaloutpost)
    prob += security >= minsecurity, "minimum security"
    if maxsecurity is not None: prob += security <= maxsecurity, "maximum security"

    techlevel = (8 * researchstation) + (6 * orbis) + (3 * communicationstation) + (3 * scientificoutpost) + (3 * industrialoutpost) + (3 * medical) + (coriolis) + (10 * hightechhub) + (10 * largescientificsettlement) + (10 * scientifichub) + (6 * explorationhub) + (6 * mediumscientificsettlement) + (5 * scientificplanetaryoutpost) + (5 * planetaryport) + (3 * refineryhub) + (3 * smallscientificsettlement) + (3 * industrialhub) + (largeextractionsettlement) + (3 * asteroidbase)
    prob += techlevel >= mintechlevel, "minimum tech level"
    if maxtechlevel is not None:
        prob += techlevel <= maxtechlevel, "maximum tech level"

    wealth = (7 * orbis) + (6 * tourist) + (3 * miningoutpost) + (2 * coriolis) + (2 * commercialoutpost) + (2 * bar) + (civilianoutpost) + (satellite) + (10 * extractionhub) + (7 * largeextractionsettlement) + (5 * planetaryport) + (5 * mediumextractionsettlement) + (5 * largetourismsettlement) + (5 * refineryhub) + (5 * industrialhub) + (2 * industrialplanetaryoutpost) + (2 * smallextractionsettlement) + (2 * largeindustrialsettlement) + (2 * mediumtourismsettlement) + (smalltourismsettlement) + (-2 * hightechhub) + (5 * asteroidbase) + (3 * piratebase) + (2 * criminaloutpost)
    prob += wealth >= minwealth, "minimum wealth"
    if maxwealth is not None:
        prob += wealth <= maxwealth, "maximum wealth"

    standardofliving = (6 * government) + (5 * orbis) + (5 * medical) + (5 * commercialoutpost) + (5 * spacefarm) + (3 * coriolis) + (3 * securitystation) + (3 * bar) + (civilianoutpost) + (satellite) + (-2 * miningoutpost) + (10 * largeagriculturalsettlement) + (6 * planetaryport) + (6 * mediumagriculturalsettlement) + (3 * civilianplanetaryoutpost) + (3 * outposthub) + (3 * civilianhub) + (3 * smallagriculturalsettlement) + (-2 * refineryhub) + (-2 * largeextractionsettlement) + (-4 * industrialhub) + (-4 * extractionhub) + (-4 * asteroidbase)
    prob += standardofliving >= minstandardofliving, "minimum standard of living"
    if maxstandardofliving is not None:
        prob += standardofliving <= maxstandardofliving, "maximum standard of living"

    developmentlevel = (8 * orbis) + (2 * government) + (2 * coriolis) + (2 * securitystation) + (2 * researchstation) + (2 * industrialoutpost) + (2 * tourist) + (spacefarm) + (civilianoutpost) + (satellite) + (relaystation) + (10 * planetaryport) + (8 * largeindustrialsettlement) + (7 * refineryhub) + (5 * mediumindustrialsettlement) + (2 * outposthub) + (2 * civilianhub) + (2 * industrialhub) + (2 * extractionhub) + (2 * largescientificsettlement) + (2 * explorationhub) + (2 * largemilitarysettlement) + (2 * smallindustrialsettlement) + (mediumscientificsettlement) + (scientificplanetaryoutpost) + (smallscientificsettlement) + (7 * asteroidbase)
    prob += developmentlevel >= mindevelopmentlevel, "minimum development level"
    if maxdevelopmentlevel is not None:
        prob += developmentlevel <= maxdevelopmentlevel, "maximum development level"

    #number of slots
    prob += coriolis + orbis + commercialoutpost + industrialoutpost + civilianoutpost + scientificoutpost + militaryoutpost + satellite + communicationstation + spacefarm + miningoutpost + relaystation + military + securitystation + government + medical + researchstation + tourist + bar + asteroidbase + criminaloutpost + piratebase == orbitalfacilityslots + 1, "orbital facility slots"
    prob += civilianplanetaryoutpost + industrialplanetaryoutpost + scientificplanetaryoutpost + planetaryport + smallagriculturalsettlement + mediumagriculturalsettlement + largeagriculturalsettlement + smallextractionsettlement + mediumextractionsettlement + largeextractionsettlement + smallindustrialsettlement + mediumindustrialsettlement + largeindustrialsettlement + smallmilitarysettlement + mediummilitarysettlement + largemilitarysettlement + smallscientificsettlement + mediumscientificsettlement + largescientificsettlement + smalltourismsettlement + mediumtourismsettlement + largetourismsettlement + extractionhub + civilianhub + explorationhub + outposthub + scientifichub + militaryhub + refineryhub + hightechhub + industrialhub == groundfacilityslots, "ground facility slots"
    #construction points
    prob += (industrialoutpost) + (spacefarm) + (civilianoutpost) + (satellite) + (relaystation) + (commercialoutpost) + (miningoutpost) + (communicationstation) + (scientificoutpost) + (militaryoutpost) + (mediumindustrialsettlement) + (smallindustrialsettlement) + (scientificplanetaryoutpost) + (mediumagriculturalsettlement) + (civilianplanetaryoutpost) + (smallagriculturalsettlement) + (mediummilitarysettlement) + (smallmilitarysettlement) + (industrialplanetaryoutpost) + (mediumextractionsettlement) + (smallextractionsettlement) + (-3 * coriolis) + (-1 * government) + (-1 * securitystation) + (-1 * researchstation) + (-1 * tourist) + (-1 * medical) + (-1 * bar) + (-1 * military) + (-1 * largeindustrialsettlement) + (-1 * largescientificsettlement) + (-1 * largemilitarysettlement) + (-1 * largeagriculturalsettlement) + (-1 * largeextractionsettlement) + (-1 * largetourismsettlement) + (-1 * refineryhub) + (-1 * outposthub) + (-1 * civilianhub) + (-1 * industrialhub) + (-1 * extractionhub) + (-1 * explorationhub) + (-1 * mediumscientificsettlement) + (-1 * smallscientificsettlement) + (-1 * hightechhub) + (-1 * scientifichub) + (-1 * militaryhub) + (-1 * mediumtourismsettlement) + (-1 * smalltourismsettlement) + inittier2conpoints + piratebase + criminaloutpost + (-3 * asteroidbase) >= 0, "tier 2 construction points"
    prob += (coriolis) + (government) + (securitystation) + (researchstation) + (tourist) + (medical) + (bar) + (military) + (2 * largeindustrialsettlement) + (2 * largescientificsettlement) + (2 * largemilitarysettlement) + (2 * largeagriculturalsettlement) + (2 * largeextractionsettlement) + (2 * largetourismsettlement) + (refineryhub) + (outposthub) + (civilianhub) + (industrialhub) + (extractionhub) + (explorationhub) + (mediumscientificsettlement) + (smallscientificsettlement) + (hightechhub) + (scientifichub) + (militaryhub) + (mediumtourismsettlement) + (smalltourismsettlement) + (-6 * orbis) + (-6 * planetaryport) + inittier3conpoints + asteroidbase >= 0, "tier 3 construction points"
    #sort out dependencies for facilities
    b1 = pulp.LpVariable("b1", cat="Binary")
    b2 = pulp.LpVariable("b2", cat="Binary")
    b3 = pulp.LpVariable("b3", cat="Binary")
    prob += smalltourismsettlement <= M * b1
    prob += smalltourismsettlement >= b1
    prob += mediumtourismsettlement <= M * b2
    prob += mediumtourismsettlement >= b2
    prob += largetourismsettlement <= M * b3
    prob += largetourismsettlement >= b3
    any_positive1 = pulp.LpVariable("any_positive1", cat="Binary")
    prob += any_positive1 >= b1
    prob += any_positive1 >= b2
    prob += any_positive1 >= b3
    prob += any_positive1 <= M * (b1 + b2 + b3)
    prob += tourist <= M * any_positive1
    b4 = pulp.LpVariable("b4", cat="Binary")
    b5 = pulp.LpVariable("b5", cat="Binary")
    b6 = pulp.LpVariable("b6", cat="Binary")
    prob += smallscientificsettlement <= M * b4
    prob += smallscientificsettlement >= b4
    prob += mediumscientificsettlement <= M * b5
    prob += mediumscientificsettlement >= b5
    prob += largescientificsettlement <= M * b6
    prob += largescientificsettlement >= b6
    any_positive2 = pulp.LpVariable("any_positive2", cat="Binary")
    prob += any_positive2 >= b4
    prob += any_positive2 >= b5
    prob += any_positive2 >= b6
    prob += any_positive2 <= M * (b4 + b5 + b6)
    prob += researchstation <= M * any_positive2
    b7 = pulp.LpVariable("b7", cat="Binary")
    b8 = pulp.LpVariable("b8", cat="Binary")
    b9 = pulp.LpVariable("b9", cat="Binary")
    prob += smallmilitarysettlement <= M * b7
    prob += smallmilitarysettlement >= b7
    prob += mediummilitarysettlement <= M * b8
    prob += mediummilitarysettlement >= b8
    prob += largemilitarysettlement <= M * b9
    prob += largemilitarysettlement >= b9
    any_positive3 = pulp.LpVariable("any_positive3", cat="Binary")
    prob += any_positive3 >= b7
    prob += any_positive3 >= b8
    prob += any_positive3 >= b9
    prob += any_positive3 <= M * (b7 + b8 + b9)
    prob += military <= M * any_positive3
    b10 = pulp.LpVariable("b10", cat="Binary")
    prob += relaystation <= M * b10
    prob += relaystation >= b10
    prob += securitystation <= M * b10
    b11 = pulp.LpVariable("b11", cat="Binary")
    prob += spacefarm <= M * b11
    prob += spacefarm >= b11
    prob += outposthub <= M * b11
    b12 = pulp.LpVariable("b12", cat="Binary")
    b13 = pulp.LpVariable("b13", cat="Binary")
    b14 = pulp.LpVariable("b14", cat="Binary")
    prob += smallextractionsettlement <= M * b12
    prob += smallextractionsettlement >= b12
    prob += mediumextractionsettlement <= M * b13
    prob += mediumextractionsettlement >= b13
    prob += largeextractionsettlement <= M * b14
    prob += largeextractionsettlement >= b14
    any_positive4 = pulp.LpVariable("any_positive4", cat="Binary")
    prob += any_positive4 >= b12
    prob += any_positive4 >= b13
    prob += any_positive4 >= b14
    prob += any_positive4 <= M * (b12 + b13 + b14)
    prob += extractionhub <= M * any_positive4
    b15 = pulp.LpVariable("b15", cat="Binary")
    b16 = pulp.LpVariable("b16", cat="Binary")
    b17 = pulp.LpVariable("b17", cat="Binary")
    prob += smallagriculturalsettlement <= M * b15
    prob += smallagriculturalsettlement >= b15
    prob += mediumagriculturalsettlement <= M * b16
    prob += mediumagriculturalsettlement >= b16
    prob += largeagriculturalsettlement <= M * b17
    prob += largeagriculturalsettlement >= b17
    any_positive5 = pulp.LpVariable("any_positive5", cat="Binary")
    prob += any_positive5 >= b15
    prob += any_positive5 >= b16
    prob += any_positive5 >= b17
    prob += any_positive5 <= M * (b15 + b16 + b17)
    prob += civilianhub <= M * any_positive5
    b18 = pulp.LpVariable("b18", cat="Binary")
    prob += miningoutpost <= M * b18
    prob += miningoutpost >= b18
    prob += industrialhub <= M * b18
    b19 = pulp.LpVariable("b19", cat="Binary")
    prob += military <= M * b19
    prob += military >= b19
    prob += militaryhub <= M * b19
    b20 = pulp.LpVariable("b20", cat="Binary")
    prob += satellite <= M * b20
    prob += satellite >= b20
    prob += smalltourismsettlement <= M * b20
    prob += mediumtourismsettlement <= M * b20
    prob += largetourismsettlement <= M * b20
    b21 = pulp.LpVariable("b21", cat="Binary")
    prob += communicationstation <= M * b21
    prob += communicationstation >= b21
    prob += explorationhub <= M * b21
    #solve
    prob.solve()
    if pulp.LpStatus[prob.status] == "Infeasible":
        resultlabel.config(text="Error: There is no possible system arrangement that can fit the conditions you have specified")
        return None
    printresult("Here is what you need to build in the system (including the first station) to achieve these requirements: ")
    for v in prob.variables():
        if v.name != "__dummy":
            if v.varValue > 0 and not bool(re.fullmatch(r"b\d+", v.name)) and not bool(re.fullmatch(r"any_positive\d+", v.name)):
                if v.name == "orbis":
                    printresult("orbis/ocellus = " + str(int(v.varValue)))
                else:
                    printresult(v.name.replace("_", " ") + " = " + str(int(v.varValue)))

    resultvars["initialpopulationincrease"].set(pulp.value((5 * orbis) + (coriolis) + (scientificoutpost) + (militaryoutpost) + (10 * planetaryport) + (2 * civilianplanetaryoutpost) + (industrialplanetaryoutpost) + (scientificplanetaryoutpost) + (asteroidbase)))
    resultvars["maxpopulationincrease"].set(pulp.value((orbis) + (10 * planetaryport)))
    resultvars["security"].set(pulp.value((8 * securitystation) + (6 * military) + (2 * militaryoutpost) + (2 * government) + (communicationstation) + (relaystation) + (-1 * commercialoutpost) + (-1 * civilianoutpost) + (-2 * coriolis) + (-2 * bar) + (-3 * orbis) + (-3 * tourist) + (10 * militaryhub) + (6 * largemilitarysettlement) + (4 * mediummilitarysettlement) + (2 * smallmilitarysettlement) + (-1 * industrialplanetaryoutpost) + (-1 * scientificplanetaryoutpost) + (-1 * smalltourismsettlement) + (-1 * mediumtourismsettlement) + (-1 * largetourismsettlement) + (-1 * refineryhub) + (-1 * explorationhub) + (-2 * civilianplanetaryoutpost) + (-2 * hightechhub) + (-2 * outposthub) + (-3 * planetaryport) + (-3 * civilianhub) + (-1 * asteroidbase) + (-4 * piratebase) + (-2 * criminaloutpost)))
    resultvars["techlevel"].set(pulp.value((8 * researchstation) + (6 * orbis) + (3 * communicationstation) + (3 * scientificoutpost) + (3 * industrialoutpost) + (3 * medical) + (coriolis) + (10 * hightechhub) + (10 * largescientificsettlement) + (10 * scientifichub) + (6 * explorationhub) + (6 * mediumscientificsettlement) + (5 * scientificplanetaryoutpost) + (5 * planetaryport) + (3 * refineryhub) + (3 * smallscientificsettlement) + (3 * industrialhub) + (largeextractionsettlement) + (3 * asteroidbase)))
    resultvars["wealth"].set(pulp.value((7 * orbis) + (6 * tourist) + (3 * miningoutpost) + (2 * coriolis) + (2 * commercialoutpost) + (2 * bar) + (civilianoutpost) + (satellite) + (10 * extractionhub) + (7 * largeextractionsettlement) + (5 * planetaryport) + (5 * mediumextractionsettlement) + (5 * largetourismsettlement) + (5 * refineryhub) + (5 * industrialhub) + (2 * industrialplanetaryoutpost) + (2 * smallextractionsettlement) + (2 * largeindustrialsettlement) + (2 * mediumtourismsettlement) + (smalltourismsettlement) + (-2 * hightechhub) + (5 * asteroidbase) + (3 * piratebase) + (2 * criminaloutpost)))
    resultvars["standardofliving"].set(pulp.value((6 * government) + (5 * orbis) + (5 * medical) + (5 * commercialoutpost) + (5 * spacefarm) + (3 * coriolis) + (3 * securitystation) + (3 * bar) + (civilianoutpost) + (satellite) + (-2 * miningoutpost) + (10 * largeagriculturalsettlement) + (6 * planetaryport) + (6 * mediumagriculturalsettlement) + (3 * civilianplanetaryoutpost) + (3 * outposthub) + (3 * civilianhub) + (3 * smallagriculturalsettlement) + (-2 * refineryhub) + (-2 * largeextractionsettlement) + (-4 * industrialhub) + (-4 * extractionhub) + (-4 * asteroidbase)))
    resultvars["developmentlevel"].set(pulp.value((8 * orbis) + (2 * government) + (2 * coriolis) + (2 * securitystation) + (2 * researchstation) + (2 * industrialoutpost) + (2 * tourist) + (spacefarm) + (civilianoutpost) + (satellite) + (relaystation) + (10 * planetaryport) + (8 * largeindustrialsettlement) + (7 * refineryhub) + (5 * mediumindustrialsettlement) + (2 * outposthub) + (2 * civilianhub) + (2 * industrialhub) + (2 * extractionhub) + (2 * largescientificsettlement) + (2 * explorationhub) + (2 * largemilitarysettlement) + (2 * smallindustrialsettlement) + (mediumscientificsettlement) + (scientificplanetaryoutpost) + (smallscientificsettlement) + (7 * asteroidbase)))

def printresult(text):
    current_text = resultlabel.cget("text")
    new_text = current_text + "\n" + text
    resultlabel.config(text=new_text)
# tkinter setup
def validate_input(P):
    return P.isdigit() or P == ""

def on_focus_out(event, var):
    value = event.widget.get().lower()
    var.set(value)

root = tkinter.Tk()
vcmd = root.register(validate_input)
root.title("Elite Dangerous colonisation planner")
root.geometry("800x1000")
maximizeinput = tkinter.StringVar()
frame = tkinter.Frame(root)
frame.pack(pady=5)
label = tkinter.Label(frame, text="Select what you are trying to maximise:", font=("calibri", 12))
label.pack(side="left")
dropdown = tkinter.OptionMenu(frame, maximizeinput, "initial population increase", "maximum population increase", "security", "tech level", "wealth", "standard of living", "development level")
dropdown.pack(side="left")
listofminimum = ["initial population increase", "max population increase", "security", "tech level", "wealth", "standard of living", "development level"]

minframes = {}
minvars = {}
maxvars = {}
resultvars = {}

constraint_frame = tkinter.Frame(root)
constraint_frame.pack(padx=10, pady=5)
tkinter.Label(constraint_frame, text="System Scores",font=("calibri", 12)).grid(column=0, columnspan=3, row=0)
tkinter.Label(constraint_frame, text="min. value",font=("calibri", 12)).grid(column=1, row=1)
tkinter.Label(constraint_frame, text="max. value",font=("calibri", 12)).grid(column=2, row=1)
tkinter.Label(constraint_frame, text="solution value",font=("calibri", 12)).grid(column=3, row=1)
for i, name in enumerate(listofminimum):
    var_name = name.replace(" ", "")
    minvars[var_name] = tkinter.StringVar(value="")
    maxvars[var_name] = tkinter.StringVar(value="")
    resultvars[var_name] = tkinter.IntVar()

    label = tkinter.Label(constraint_frame, text=name,font=("calibri", 12))
    label.grid(column=0, row=2+i)
    entry_min = tkinter.Entry(constraint_frame, textvariable=minvars[var_name], validate="key", validatecommand=(vcmd, "%P"), width=10)
    entry_max = tkinter.Entry(constraint_frame, textvariable=maxvars[var_name], validate="key", validatecommand=(vcmd, "%P"), width=10)
    entry_min.grid(column=1, row=2+i)
    entry_max.grid(column=2, row=2+i)
    entry_min.bind("<FocusOut>", lambda event, var=minvars[var_name]: on_focus_out(event, var))
    entry_max.bind("<FocusOut>", lambda event, var=maxvars[var_name]: on_focus_out(event, var))

    result = tkinter.Entry(constraint_frame, textvariable=resultvars[var_name], width=10)
    result.grid(column=3, row=2+i, padx=5)
    result.config(state=tkinter.DISABLED)

orbitalfacilityslotsinput = tkinter.IntVar()
groundfacilityslotsinput = tkinter.IntVar()
asteroidslotsinput = tkinter.IntVar()
frame20 = tkinter.Frame(root)
frame20.pack(pady=5)
label = tkinter.Label(frame20, text="Enter the number of orbital facility slots your system has (excluding the first station):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame20, textvariable=orbitalfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=orbitalfacilityslotsinput: on_focus_out(event, var))
frame21 = tkinter.Frame(root)
frame21.pack(pady=5)
label = tkinter.Label(frame21, text="Enter the number of ground facility slots your system has:", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame21, textvariable=groundfacilityslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=groundfacilityslotsinput: on_focus_out(event, var))
frame22 = tkinter.Frame(root)
frame22.pack(pady=5)
label = tkinter.Label(frame22, text="Enter the number of slots your system has that can have asteroid bases (including the first station):", font=("calibri", 12))
label.pack(side="left")
entry = tkinter.Entry(frame22, textvariable=asteroidslotsinput, validate="key", validatecommand=(vcmd, "%P"),width=10)
entry.pack(side="left")
entry.bind("<FocusOut>", lambda event, var=asteroidslotsinput: on_focus_out(event, var))
criminalinput = tkinter.BooleanVar()
checkbox = tkinter.Checkbutton(root, text="Are you okay with contraband stations being built in your system? (pirate base, criminal outpost)", variable=criminalinput, font=("calibri", 12))
checkbox.pack(pady=5)
firststationinput = tkinter.StringVar()
frame23 = tkinter.Frame(root)
frame23.pack(pady=5)
label = tkinter.Label(frame23, text="Select your first station:", font=("calibri", 12))
label.pack(side="left")
dropdown = tkinter.OptionMenu(frame23, firststationinput, "orbis", "ocellus", "asteroid base", "coriolis", "commercial outpost", "industrial outpost", "criminal outpost", "civilian outpost", "scientific outpost", "military outpost")
dropdown.pack(side="left")
button = tkinter.Button(root, text="Solve for a system", command=lambda: solve())
button.pack(pady=7)
resultlabel = tkinter.Label(root, text="", font=("calibri", 12))
resultlabel.pack(pady=10)
root.mainloop()
