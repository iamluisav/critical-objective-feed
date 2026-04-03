import requests
import json
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# All BuildList companies not already in feed + retries from first pass
CANDIDATES = [
    # Retries from first pass that failed
    ("Figure", "https://figure.ai"),
    ("Clone Robotics", "https://clonerobotics.com"),
    ("Mark43", "https://www.mark43.com"),
    ("Cortical Labs", "https://www.corticallabs.com"),
    ("Antora Energy", "https://www.antoraenergy.com"),
    ("Anthro Energy", "https://www.anthroenergy.com"),
    ("Stoke Space", "https://www.stokespace.com"),
    ("Ark Electronics", "https://www.arkelectron.com"),
    ("Atomic Machines", "https://www.atomicmachines.com"),
    ("Asylon Robotics", "https://www.asylonrobotics.com"),
    ("Base Power", "https://www.basepowercompany.com"),
    ("Blumen Systems", "https://www.blumensystems.com"),
    ("Atom Limbs", "https://www.atomlimbs.com"),
    ("AstroForge", "https://www.astroforge.io"),
    ("Vast", "https://www.vastspace.com"),
    ("Cerebras Systems", "https://www.cerebras.net"),
    ("Roam Robotics", "https://www.roamrobotics.com"),
    ("CHAOS Industries", "https://www.chaosindustries.com"),
    ("Skysafe", "https://www.skysafe.io"),
    ("Bright Machines", "https://www.brightmachines.com"),
    ("Dawn Aerospace", "https://www.dawnaerospace.com"),
    ("Varda Space", "https://www.varda.com"),
    ("Durin", "https://www.durin.com"),
    ("Zeno Power", "https://www.zenopower.com"),
    ("Earth AI", "https://www.earth-ai.com"),
    ("EarthGrid", "https://www.earthgrid.io"),
    ("Corvus Robotics", "https://www.corvus-robotics.com"),
    ("Arc Boats", "https://www.arcboats.com"),
    ("Danti", "https://www.danti.ai"),
    ("Cognitive Space", "https://www.cognitivespace.com"),
    ("Formlogic", "https://www.formlogic.com"),
    ("Field AI", "https://www.fieldai.com"),
    ("Formic", "https://www.formic.co"),
    ("Decagon", "https://decagon.ai"),
    ("Atmo", "https://www.atmo.ai"),
    ("Cambridge Aerospace", "https://www.cambridgeaerospace.com"),
    ("Workrise", "https://www.workrise.com"),
    ("AtmoCooling", "https://www.atmocooling.com"),
    ("Flyby Robotics", "https://www.flybyrobotics.com"),
    ("Still Bright", "https://www.stillbright.co"),
    ("Deep Isolation", "https://www.deepisolation.com"),
    ("GenLogs", "https://www.genlogs.io"),
    ("Pila Energy", "https://www.pilaenergy.com"),
    ("Atopile", "https://www.atopile.io"),
    ("Blue Water Autonomy", "https://www.blw.ai"),

    # New from BuildList
    ("Outpost Space", "https://www.outpostspace.com"),
    ("Zettascale", "https://www.zettascale.com"),
    ("Zipline", "https://flyzipline.com"),
    ("Planted Solar", "https://plantedsolar.com"),
    ("Anduril Industries", "https://www.anduril.com"),
    ("Lumafield", "https://lumafield.com"),
    ("Aalo Atomics", "https://www.aaloatomics.com"),
    ("SpaceX", "https://www.spacex.com"),
    ("Rainmaker", "https://www.rainmaker.aero"),
    ("Valar Atomics", "https://valaratomics.com"),
    ("StarCloud", "https://starcloud.com"),
    ("Cuby", "https://www.cuby.homes"),
    ("H3X", "https://www.h3x.tech"),
    ("Neros", "https://neros.ai"),
    ("Atomic Industries", "https://www.atomicind.com"),
    ("Andrenam", "https://www.andrenam.com"),
    ("Rocket Lab", "https://www.rocketlabusa.com"),
    ("SendCutSend", "https://sendcutsend.com"),
    ("Standard Bots", "https://standardbots.com"),
    ("Radiant", "https://www.radiantnuclear.com"),
    ("Orbital Operations", "https://www.orbitaloperations.com"),
    ("CX2", "https://www.cx2technologies.com"),
    ("Diode Computers", "https://www.diode.computer"),
    ("Galadyne", "https://www.galadyne.com"),
    ("Boom Supersonic", "https://boomsupersonic.com"),
    ("Pryzm", "https://www.pryzm.ai"),
    ("xAI", "https://x.ai"),
    ("Anthropic", "https://www.anthropic.com"),
    ("Ouros", "https://www.ouros.energy"),
    ("Amidon Heavy Industries", "https://www.amidon.com"),
    ("Neuralink", "https://neuralink.com"),
    ("Sorcerer", "https://www.sorcerer.energy"),
    ("Reflect Orbital", "https://www.reflectorbital.com"),
    ("Extropic", "https://www.extropic.ai"),
    ("Heron Power", "https://www.heronpower.com"),
    ("Inversion", "https://inversionspace.com"),
    ("Aeon Industries", "https://www.aeonindustries.com"),
    ("Radical AI", "https://www.radical.ai"),
    ("Cover", "https://www.cover.build"),
    ("Turion Space", "https://turionspace.com"),
    ("Perplexity", "https://www.perplexity.ai"),
    ("Crusoe Energy", "https://www.crusoeenergy.com"),
    ("Physical Intelligence", "https://www.physicalintelligence.company"),
    ("Nominal", "https://www.nominal.so"),
    ("1x", "https://www.1x.tech"),
    ("Impulse Space", "https://www.impulsespace.com"),
    ("Allen Control Systems", "https://www.allencontrolsystems.com"),
    ("Flexport", "https://www.flexport.com"),
    ("Saronic", "https://www.saronic.com"),
    ("Flock Safety", "https://www.flocksafety.com"),
    ("Heliux", "https://www.heliux.com"),
    ("Vuecason", "https://www.vuecason.com"),
    ("Forterra", "https://www.forterra.com"),
    ("Starfish Space", "https://www.starfishspace.com"),
    ("Relativity Space", "https://www.relativityspace.com"),
    ("AMCA", "https://www.amca.aero"),
    ("Antares", "https://antares.energy"),
    ("Blue Origin", "https://www.blueorigin.com"),
    ("AMP Robotics", "https://amprobotics.com"),
    ("Pilgrim", "https://pilgrimbio.com"),
    ("The Boring Company", "https://www.boringcompany.com"),
    ("Vulcan Elements", "https://vulcanelements.com"),
    ("Commonwealth Fusion", "https://cfs.energy"),
    ("True Anomaly", "https://trueanomaly.space"),
    ("Impulse Labs", "https://www.impulselabs.com"),
    ("Castelion", "https://www.castelion.com"),
    ("Longshot Space", "https://longshotspace.com"),
    ("K2 Space", "https://www.k2space.com"),
    ("PsiQuantum", "https://www.psiquantum.com"),
    ("Terraform Industries", "https://terraformindustries.com"),
    ("Orchard Robotics", "https://www.orchard-robotics.com"),
    ("Skydio", "https://www.skydio.com"),
    ("Etched", "https://www.etched.com"),
    ("Galvanick", "https://www.galvanick.com"),
    ("Substrate", "https://www.substrate.ai"),
    ("Apptronik", "https://apptronik.com"),
    ("Waymo", "https://waymo.com"),
    ("Sila Nanotechnologies", "https://www.silanano.com"),
    ("Rangeview", "https://www.rangeview.com"),
    ("Firefly Aerospace", "https://fireflyspace.com"),
    ("Atom Computing", "https://www.atom-computing.com"),
    ("DeepNight", "https://www.deepnight.ai"),
    ("ElevenLabs", "https://elevenlabs.io"),
    ("AnySignal", "https://www.anysignal.com"),
    ("Quaise Energy", "https://www.quaise.energy"),
    ("Ramp", "https://ramp.com"),
    ("NewLimit", "https://www.newlimit.com"),
    ("RMFG", "https://www.rmfg.com"),
    ("Shinkei Systems", "https://shinkei.com"),
    ("Aalyria", "https://www.aalyria.com"),
    ("Redwood Materials", "https://www.redwoodmaterials.com"),
    ("Quindar", "https://www.quindar.space"),
    ("Replit", "https://replit.com"),
    ("Rune Technologies", "https://www.runetechnologies.com"),
    ("Argo Space", "https://www.argospace.com"),
    ("Saildrone", "https://www.saildrone.com"),
    ("Terranova", "https://www.terranova.build"),
    ("Gecko Robotics", "https://www.geckorobotics.com"),
    ("Framework Computer", "https://frame.work"),
    ("Armada", "https://www.armada.com"),
    ("Isar Aerospace", "https://www.isaraerospace.com"),
    ("Path Robotics", "https://www.path-robotics.com"),
    ("Kalshi", "https://www.kalshi.com"),
    ("Guardian RF", "https://www.guardianrf.com"),
    ("Fuse Energy", "https://www.f.energy"),
    ("Dyna Robotics", "https://www.dynarobotics.com"),
    ("Joby Aviation", "https://www.jobyaviation.com"),
    ("General Galactic", "https://www.generalgalactic.com"),
    ("Fervo Energy", "https://www.fervoenergy.com"),
    ("First Resonance", "https://www.firstresonance.io"),
    ("Electric Sheep", "https://www.electricsheep.co"),
    ("Epirus", "https://www.epirusinc.com"),
    ("Pixxel", "https://www.pixxel.space"),
    ("Proxima Fusion", "https://www.proximafusion.com"),
    ("Swarmbotics AI", "https://www.swarmbotics.ai"),
    ("DroneForge", "https://www.droneforge.com"),
    ("Thalassa Robotics", "https://www.thalassarobotics.com"),
    ("Traba", "https://www.traba.work"),
    ("Lunar Outpost", "https://www.lunaroutpost.com"),
    ("Nitricity", "https://www.nitricity.com"),
    ("Charge Robotics", "https://www.charge.robotics"),
    ("Charm Industrial", "https://charmindustrial.com"),
    ("Last Energy", "https://www.lastenergy.com"),
    ("Umbra", "https://umbra.space"),
    ("Shift5", "https://www.shift5.io"),
    ("Arbor Energy", "https://www.arbor.co"),
    ("Glimpse", "https://www.glimp.se"),
    ("Burro", "https://www.burro.ai"),
    ("Colossal Biosciences", "https://www.colossal.com"),
    ("Aon3D", "https://www.aon3d.com"),
    ("Groq", "https://groq.com"),
    ("Harmonic Bionics", "https://harmonicbionics.com"),
    ("Freeform", "https://www.freeform.com"),
    ("Glean", "https://www.glean.com"),
    ("Harvey", "https://www.harvey.ai"),
    ("Brex", "https://www.brex.com"),
    ("Oklo", "https://oklo.com"),
    ("Harmattan AI", "https://www.harmattanai.com"),
    ("Orbit Fab", "https://www.orbitfab.com"),
    ("KoBold Metals", "https://www.koboldmetals.com"),
    ("JetZero", "https://jetzero.aero"),
    ("Skild AI", "https://www.skild.ai"),
    ("Overland AI", "https://www.overland.ai"),
    ("Saronic", "https://www.saronic.com"),
    ("Sardine", "https://www.sardine.ai"),
    ("Sierra", "https://sierra.ai"),
    ("Ursa Major", "https://www.ursamajortech.com"),
    ("Tenstorrent", "https://tenstorrent.com"),
    ("Axiom Space", "https://www.axiomspace.com"),
    ("ICON", "https://www.iconbuild.com"),
    ("Avalanche Energy", "https://www.avalanche.energy"),
    ("Agility Robotics", "https://www.agilityrobotics.com"),
    ("Boston Metal", "https://www.bostonmetal.com"),
    ("Viam", "https://www.viam.com"),
    ("Aurora", "https://aurora.tech"),
    ("Ghost Robotics", "https://www.ghostrobotics.io"),
    ("Vannevar Labs", "https://www.vannevarlabs.com"),
    ("Second Front Systems", "https://www.secondfront.com"),
    ("Rapid Robotics", "https://www.rapidrobotics.com"),
    ("Seurat", "https://www.seurat.com"),
    ("LeoLabs", "https://leolabs.space"),
    ("Diligent Robotics", "https://www.diligentrobots.com"),
    ("Wisk Aero", "https://wisk.aero"),
    ("Spartan Radar", "https://spartanradar.com"),
    ("Parallel Systems", "https://www.parallel.systems"),
    ("WindBorne Systems", "https://windbornesystems.com"),
    ("Wyvern", "https://wyvern.space"),
    ("Kayhan Space", "https://kayhanspace.com"),
    ("HEO Robotics", "https://heorobotics.com"),
    ("Nuview", "https://nuview.space"),
    ("Muon Space", "https://muonspace.com"),
    ("Privateer", "https://www.privateerspace.com"),
    ("TerraDepth", "https://www.terradepth.com"),
    ("Dandelion Energy", "https://www.dandelionenergy.com"),
    ("Rondo Energy", "https://rondoenergy.com"),
    ("Samsara", "https://www.samsara.com"),
    ("Cohere", "https://cohere.com"),
    ("Rivian", "https://rivian.com"),
    ("Onebrief", "https://www.onebrief.com"),
    ("Mytra", "https://www.mytra.ai"),
    ("Form Energy", "https://formenergy.com"),
    ("Nominal", "https://www.nominal.so"),
    ("Saildrone", "https://www.saildrone.com"),
    ("Locus Robotics", "https://www.locusrobotics.com"),
    ("AMP Robotics", "https://amprobotics.com"),
    ("Firehawk Aerospace", "https://www.firehawkaerospace.com"),
    ("Lumen Energy", "https://www.lumen.energy"),
    ("Databricks", "https://www.databricks.com"),
    ("Chef Robotics", "https://www.chefrobotics.ai"),
    ("Dexterity", "https://www.dexterity.ai"),
    ("Joby Aviation", "https://www.jobyaviation.com"),
    ("Flock Safety", "https://www.flocksafety.com"),
    ("Gecko Robotics", "https://www.geckorobotics.com"),
    ("Redwood Materials", "https://www.redwoodmaterials.com"),
    ("Apptronik", "https://apptronik.com"),
    ("Crusoe Energy", "https://www.crusoeenergy.com"),
    ("Fervo Energy", "https://www.fervoenergy.com"),
    ("TurbineOne", "https://www.turbineone.com"),
    ("Dirac", "https://www.diracinc.com"),
    ("Ample", "https://www.ample.com"),
    ("Breen Energy", "https://www.breenenergy.com"),
    ("Texture Energy", "https://www.texturehq.com"),
    ("Campus", "https://www.campus.edu"),
    ("Electric Era", "https://electricera.tech"),
    ("Zap Energy", "https://www.zapenergy.com"),
    ("Pacific Fusion", "https://www.pacificfusion.com"),
    ("Fid Labs", "https://www.fidlabs.com"),
    ("Formation Bio", "https://www.formation.bio"),
    ("Phaidra", "https://www.phaidra.ai"),
    ("Helsing", "https://helsing.ai"),
    ("Heart Aerospace", "https://www.heartaerospace.com"),
    ("Hebbia", "https://www.hebbia.com"),
    ("Swan Technologies", "https://www.swan.tech"),
    ("Vatn Systems", "https://www.vatnsystems.com"),
    ("Orbital Sidekick", "https://www.orbitalsidekick.com"),
    ("Whisper Aero", "https://whisper.aero"),
    ("Urban Sky", "https://www.urbansky.com"),
    ("Unspun", "https://www.unspun.io"),
    ("Mitra Chem", "https://mitrachem.com"),
    ("Mangrove Lithium", "https://mangroveli.com"),
    ("Performance Drone Works", "https://www.performancedroneworks.com"),
    ("Vantage Robotics", "https://www.vantagerobotics.com"),
    ("Armada", "https://www.armadainfra.com"),
    ("Lilac Solutions", "https://www.lilacsolutions.com"),
    ("Molten Industries", "https://www.moltenindustries.com"),
    ("Radian Aerospace", "https://radianaerospace.com"),
    ("Pixxel", "https://www.pixxel.space"),
    ("KoBold Metals", "https://www.koboldmetals.com"),
    ("Peak Energy", "https://peakenergy.com"),
    ("Swift Solar", "https://www.swiftsolar.com"),
    ("Elroy Air", "https://elroyair.com"),
    ("Astrolab", "https://astrolab.space"),
    ("Venus Aerospace", "https://venusaero.com"),
    ("Aetherflux", "https://www.aetherflux.com"),
    ("Regent", "https://www.regentcraft.com"),
    ("Navier", "https://www.navier.ai"),
    ("Overland AI", "https://www.overland.ai"),
    ("Rcnow", "https://rcnow.com"),
    ("Xcimer Energy", "https://www.xcimerenergy.com"),
    ("ZeroMark", "https://zeromark.ai"),
    ("Havoc AI", "https://www.havoc.ai"),
    ("Eden Geopower", "https://www.edengeopower.com"),
    ("StratumAI", "https://www.stratumai.com"),
    ("Amperon", "https://www.amperon.co"),
    ("Remora", "https://www.remora.com"),
    ("CruxOCM", "https://www.cruxocm.com"),
    ("Kula Bio", "https://kulabio.com"),
    ("Dimensional Energy", "https://www.dimensionalenergy.com"),
    ("Pipedream", "https://pipedream.network"),
    ("Safire", "https://safiretech.com"),
    ("Limbinal", "https://www.liminal.ai"),
    ("Floodbase", "https://www.floodbase.com"),
    ("Equilibrium Energy", "https://www.equilibriumenergy.com"),
    ("Living Carbon", "https://www.livingcarbon.com"),
    ("Pivot Bio", "https://www.pivotbio.com"),
    ("Solugen", "https://www.solugen.com"),
    ("Wartsone", "https://wardstone.space"),
    ("Marathon Fusion", "https://marathonfusion.com"),
]

PATTERNS = {
    "lever": re.compile(r'jobs\.lever\.co/([a-zA-Z0-9_\-]+)', re.IGNORECASE),
    "ashby": re.compile(r'jobs\.ashbyhq\.com/([a-zA-Z0-9_\-\.]+)|app\.ashbyhq\.com/(?:api/xml-feed/job-postings/organization/)?([a-zA-Z0-9_\-\.]+)', re.IGNORECASE),
    "greenhouse": re.compile(r'boards(?:-api)?\.greenhouse\.io/(?:v\d/boards/)?([a-zA-Z0-9_\-]+)(?:/jobs)?', re.IGNORECASE),
}

def fetch(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        return r.text, r.url
    except Exception:
        return "", url

def scan_text(text):
    for ats, pattern in PATTERNS.items():
        m = pattern.search(text)
        if m:
            slug = next((g for g in m.groups() if g), None)
            return ats, slug, m.group(0)
    return None, None, None

def make_entry(company_name, company_url, ats, slug):
    if ats == "lever":
        return {"company_name": company_name, "company_url": company_url, "source_type": "lever",
                "feed_url": f"https://api.lever.co/v0/postings/{slug}"}
    elif ats == "ashby":
        return {"company_name": company_name, "company_url": company_url, "source_type": "ashby",
                "feed_url": f"https://app.ashbyhq.com/api/xml-feed/job-postings/organization/{slug}"}
    elif ats == "greenhouse":
        if slug in ("embed", "v1", "boards", ""):
            return None
        return {"company_name": company_name, "company_url": company_url, "source_type": "greenhouse",
                "feed_url": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"}
    return None

def detect_deep(company_name, company_url):
    base = company_url.rstrip("/")
    career_paths = [
        "", "/careers", "/jobs", "/about/careers", "/work-with-us",
        "/company/careers", "/join", "/join-us", "/open-roles",
        "/about/jobs", "/hiring", "/positions", "/team/jobs",
    ]

    all_text = ""
    visited_links = set()

    for path in career_paths:
        url = base + path
        text, final_url = fetch(url)
        if not text:
            continue
        all_text += text + url

        ats, slug, _ = scan_text(all_text)
        if ats and slug:
            entry = make_entry(company_name, company_url, ats, slug)
            if entry:
                return entry, ats

        # Follow career-looking links one level deep
        soup = BeautifulSoup(text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(final_url, href)
            link_text = (a.get_text() or "").lower()

            # Check if the link itself contains an ATS pattern
            ats, slug, _ = scan_text(full)
            if ats and slug:
                entry = make_entry(company_name, company_url, ats, slug)
                if entry:
                    return entry, ats

            is_career_link = any(w in link_text for w in ["career", "job", "hire", "work with", "join", "role", "position", "open"])
            is_external_ats = any(d in full for d in ["lever.co", "ashbyhq.com", "greenhouse.io"])

            if (is_career_link or is_external_ats) and full not in visited_links and len(visited_links) < 5:
                visited_links.add(full)
                sub_text, _ = fetch(full)
                if sub_text:
                    combined = sub_text + full
                    ats, slug, _ = scan_text(combined)
                    if ats and slug:
                        entry = make_entry(company_name, company_url, ats, slug)
                        if entry:
                            return entry, ats

        time.sleep(0.2)

    return None, None

def main():
    with open("companies.json") as f:
        existing = json.load(f)

    existing_names = {c["company_name"].lower() for c in existing}
    existing_feeds = {c["feed_url"] for c in existing}
    new_entries = []
    still_missing = []

    # Deduplicate candidates
    seen = set()
    candidates = []
    for name, url in CANDIDATES:
        if name.lower() not in existing_names and name not in seen:
            seen.add(name)
            candidates.append((name, url))

    print(f"Checking {len(candidates)} companies...\n")

    for company_name, company_url in candidates:
        print(f"Checking {company_name}...", end=" ", flush=True)
        entry, ats = detect_deep(company_name, company_url)

        if entry and entry["feed_url"] not in existing_feeds:
            print(f"Found {ats.upper()} → {entry['feed_url']}")
            new_entries.append(entry)
            existing_feeds.add(entry["feed_url"])
        elif entry:
            print(f"Duplicate feed URL")
        else:
            print("Not found")
            still_missing.append((company_name, company_url))

    if new_entries:
        existing.extend(new_entries)
        with open("companies.json", "w") as f:
            json.dump(existing, f, indent=2)
        print(f"\nAdded {len(new_entries)} companies → companies.json now has {len(existing)} total")

    if still_missing:
        print(f"\nNo ATS detected for {len(still_missing)} companies:")
        for name, url in still_missing:
            print(f"  - {name}: {url}")

if __name__ == "__main__":
    main()
