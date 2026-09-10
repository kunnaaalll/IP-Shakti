"""
AYUSH Geographical Indications (GI) Strategic Registry and Radar Metric Definitions.

Provides statutory terroir intelligence, regional botanical hubs, and
5-dimensional IP risk vector metrics for the IP-SAKTI sovereign decision engine.
"""

from typing import Dict, Any, List

GI_HUBS: Dict[str, Dict[str, Any]] = {
    "kashmir": {
        "title": "Kashmir Valley Botanical Hub",
        "title_hi": "कश्मीर घाटी वानस्पतिक केंद्र",
        "state": "Jammu & Kashmir (Pampore / Kishtwar)",
        "reg_no": "GI Reg. #635 & #636",
        "items": [
            "Kashmiri Saffron (Crocus sativus)",
            "Kashmir Walnut",
            "Kashmiri Guchhi (Wild Morel)",
            "Bhaderwah Rajmash",
        ],
        "statute": "GI Act 1999 (§ 21 Exclusivity & § 23 Injunction against Infringement / False Indications).",
        "commercial": "Commands 45-70% global export price premium; mandatory GI QR/hologram seals protect against foreign adulteration.",
        "ayush": "Essential classical ingredient in Kumkumadi Tailam & Chyawanprash. Authentic GI certificate fulfills NBA/SBB Access and Benefit Sharing origin clearance under BD Act 2002.",
        "phytochem_marker": "Crocin (≥16%), Safranal (≥3%), Picrocrocin (HPLC Grade I ISO 3632)",
        "treatise_ref": "Charaka Samhita, Chikitsa Sthana (Kumkumadi Taila & Varnya Dashemani)",
        "export_premium": "+55% to +75% Export Price Realization",
        "fpo_association": "All Jammu & Kashmir Saffron Growers Cooperative Association (Pampore)",
    },
    "himalayas": {
        "title": "Western Himalayas & Kumaon Hub",
        "title_hi": "पश्चिमी हिमालय एवं कुमाऊं केंद्र",
        "state": "Himachal Pradesh & Uttarakhand",
        "reg_no": "GI Reg. #498, #521 & #438",
        "items": [
            "Uttarakhand Tejpatta (Bay Leaf)",
            "Kangra Tea (Camellia sinensis)",
            "Chamba Chukh (Chilli Paste)",
            "Munsyari White Rajma",
        ],
        "statute": "GI Act 1999 (§ 66 Protection of Authorized Users & BD Act 2002 SBB Notification).",
        "commercial": "EU Protected GI designation for Kangra; high therapeutic cinnamic aldehyde & polyphenol content.",
        "ayush": "Key classical ingredient in Trikatu & Sudarshan Churna; prevents biopiracy and certifies genuine wild-crafted Himalayan collection.",
        "phytochem_marker": "Cinnamic aldehyde (≥65%), Eugenol, Polyphenols (LC-MS certified)",
        "treatise_ref": "Sushruta Samhita, Sutra Sthana (Eladi Gana & Trikatu Formulation)",
        "export_premium": "+40% to +60% EU Protected GI Premium",
        "fpo_association": "Uttarakhand Organic Commodity Board & Kumaon FPO Collective",
    },
    "northeast": {
        "title": "Brahmaputra & Eastern Himalayan Hub",
        "title_hi": "ब्रह्मपुत्र एवं पूर्वी हिमालय केंद्र",
        "state": "Assam, Meghalaya & Arunachal Pradesh",
        "reg_no": "GI Reg. #435, #550 & #562",
        "items": [
            "Karbi Anglong Ginger",
            "Boka Chaul (Soft Mud Rice)",
            "Joha Aromatic Rice",
            "Assam Kaji Nemu (Medicinal Lemon)",
        ],
        "statute": "GI Act 1999 (§ 28 Exclusive Right to Trade Dress & ABS Benefit Sharing with local Karbi communities).",
        "commercial": "Exceptional gingerol oleoresin concentration (up to 35% higher than mainland plains ginger).",
        "ayush": "Optimal raw botanical for Sunthi preparations and Ayurvedic Aahar digestive tonics; verified indigenous sourcing.",
        "phytochem_marker": "6-Gingerol (≥1.8%), 6-Shogaol, Curcumin (HPLC peak separation)",
        "treatise_ref": "Ashtanga Hridaya, Sutra Sthana Ch. 6 (Sunthi deepana/pachana pharmacokinetics)",
        "export_premium": "+45% to +65% High Oleoresin Organic Premium",
        "fpo_association": "Karbi Anglong Ginger Producers Cooperative Society Ltd.",
    },
    "west": {
        "title": "Konkan Coast & Western Bio-Zone",
        "title_hi": "कोंकण तट एवं पश्चिमी जैव क्षेत्र",
        "state": "Maharashtra & Goa",
        "reg_no": "GI Reg. #243 & #170",
        "items": [
            "Konkan Kokum (Garcinia indica)",
            "Sindhudurg Mango (Alphonso)",
            "Goan Khaje (Ayurvedic Sweet)",
            "Vengurla Cashew",
        ],
        "statute": "GI Act 1999 (§ 20 Bar on Generic Trademark Claims).",
        "commercial": "Hydroxycitric acid (HCA) rich bio-fractions for metabolic formulations and lipid management nutraceuticals.",
        "ayush": "Documented Vrikshamla in Sushruta Samhita for Hridya (cardiac) and Deepana (digestive) tonics.",
        "phytochem_marker": "(-)-Hydroxycitric Acid / HCA (≥12%), Garcinol, Anthocyanins",
        "treatise_ref": "Sushruta Samhita & Bhavaprakasha Nighantu (Vrikshamla for Hridya action)",
        "export_premium": "+40% to +55% Nutraceutical Metabolic Premium",
        "fpo_association": "Sindhudurg District Fruit & Herbal Processing Society (Konkan)",
    },
    "karnataka": {
        "title": "Deccan & Mysore Plateau Hub",
        "title_hi": "दक्कन एवं मैसूर पठार केंद्र",
        "state": "Karnataka & Coorg",
        "reg_no": "GI Reg. #29, #109 & #112",
        "items": [
            "Mysore Sandalwood Oil (Santalum album)",
            "Coorg Green Cardamom",
            "Mysore Betel Leaf (Paan)",
            "Nanjanagud Banana",
        ],
        "statute": "GI Act 1999 (§ 67 Criminal Penalties for Falsification of GI Goods).",
        "commercial": "Highest santalol isomer concentration worldwide (>90% α and β santalol); top luxury cosmetic and pharma grade.",
        "ayush": "Classical Chandana taila preparations; strict Forest Department & SBB custody chain compliance protects formulation integrity.",
        "phytochem_marker": "α-Santalol (≥55%) & β-Santalol (≥35%) [Total Santalol ≥90% by GC-FID]",
        "treatise_ref": "Charaka Samhita, Sutra Sthana (Shvitrahara & Dahaprashamana Gana)",
        "export_premium": "+70% to +110% Luxury Pharma & Cosmetic Benchmark",
        "fpo_association": "Karnataka Soaps & Detergents Ltd (KSDL) / Mysore Artisans Guild",
    },
    "kerala": {
        "title": "Malabar & Western Ghats Biodiverse Hub",
        "title_hi": "मालाबार एवं पश्चिमी घाट जैव-विविधता केंद्र",
        "state": "Kerala (Alleppey, Wayanad, Palakkad)",
        "reg_no": "GI Reg. #67, #77, #79 & #80",
        "items": [
            "Alleppey Green Cardamom",
            "Malabar Pepper (Piper nigrum)",
            "Navara Rice (Shashtika Shali)",
            "Pokkali Saltwater Rice",
        ],
        "statute": "GI Act 1999 (§ 21) + Biological Diversity Act 2002 (Kerala SBB ABS Regulations).",
        "commercial": "Navara rice commands ₹500-900/kg in medical tourism spas and Panchakarma wellness resorts worldwide.",
        "ayush": "Integral to Navarakizhi rejuvenation therapy; Section 3(p) patent bar is bypassed by deploying certified GI collective licensing.",
        "phytochem_marker": "Piperine (≥4.5% HPLC), Oleoresin, Starch amylose ratio (medicinal grade)",
        "treatise_ref": "Sushruta Samhita, Chikitsa Sthana (Shashtika Shali Pinda Sweda for neuromuscular disorders)",
        "export_premium": "+50% to +80% Ayurvedic Export Premium",
        "fpo_association": "Navara Eco-Farm & Kerala Ayurveda Producers Consortium",
    },
}

SCENARIO_GI_MAP: Dict[str, Dict[str, Any]] = {
    "Classical": {
        "hub": "kerala",
        "badge": "PRIMARY IP MONOPOLY (§ 21)",
        "lead": "Classical IP Alternative (Bypassing Section 3p Bar):",
        "text": "Classical formulations are strictly barred from patenting under Section 3(p) as Traditional Knowledge. However, the Geographical Indications of Goods Act, 1999 (§ 21 & § 23) provides perpetual legal territorial monopolies, registered collective producer protection, and commands +45% to +75% export price premiums via authentic QR/hologram certification.",
    },
    "Phytopharmaceutical": {
        "hub": "kashmir",
        "badge": "STANDARDIZED BOTANICAL PROVENANCE (GSR 918E)",
        "lead": "Phytopharmaceutical Batch-to-Batch Reproducibility:",
        "text": "Under GSR 918(E) and New Drugs & Clinical Trials Rules 2019, phytopharmaceutical regulatory approval demands a minimum of 4 HPLC bioactive marker fingerprints and strict chemical stability. Sourcing from certified GI agro-climatic zones eliminates batch-to-batch variation (e.g. Saffron crocin >=16%, Tejpatta cinnamic aldehyde >=65%), satisfying CDSCO clinical reproducibility mandates and clearing Section 3(d) therapeutic efficacy hurdles.",
    },
    "Patent&Proprietary": {
        "hub": "karnataka",
        "badge": "SOVEREIGN BIO-RESOURCE TRACEABILITY (BDA § 6)",
        "lead": "Biodiversity Act Section 6 Compliance & Form 3 Clearance:",
        "text": "Patents utilizing Indian biological resources require mandatory prior approval from the National Biodiversity Authority (NBA Form 3) under Section 6 of the Biological Diversity Act, 2002. Sourcing certified GI botanicals establishes an unbroken State Biodiversity Board (SBB) origin trail, expediting Form 3 approval, satisfying Rule 18 ABS benefit-sharing requirements, and precluding patent revocation under Patents Act § 64(1)(p).",
    },
    "Aahar": {
        "hub": "northeast",
        "badge": "FSSAI REG. 5 AUTHENTICITY & TRADE DRESS",
        "lead": "Ayurvedic Aahar Functional Food Authenticity:",
        "text": "Under FSSAI (Ayurvedic Aahar) Regulations, 2022 (Regulations 5 & 8), functional food products cannot make medicinal disease-cure claims, making indigenous provenance their primary brand differentiator. Registered GI credentials provide statutory substantiation of classical nutritional heritage under Schedule A, shields the product from regulatory food adulteration inquiries, and creates enforceable collective trade dress protection under GI Act § 28 in the ₹30,000+ Cr market.",
    },
    "Ambiguous": {
        "hub": "west",
        "badge": "PRE-FILING BIOPIRACY & FTO DEFENSIVE AUDIT",
        "lead": "Pre-Filing Biopiracy Risk & Freedom-to-Operate Audit:",
        "text": "When formulation boundaries or extraction parameters are undefined, filing broad patent claims risks infringing indigenous community GI rights or triggering pre-grant oppositions from TKDL. Screening the formulation against the National GI Strategic Registry provides defensive Freedom-to-Operate (FTO) clearance, prevents criminal counterfeiting liability under GI Act § 67, and establishes clear scientific boundaries before submitting patent claims.",
    },
}

RADAR_PROFILES: Dict[str, List[Dict[str, Any]]] = {
    "Classical": [
        {"key": "tk", "label": "Traditional Knowledge (§ 3p)", "val": 0.95, "desc": "Critical Bar (Strictly Barred)"},
        {"key": "sec3d", "label": "Efficacy Hurdle (§ 3d)", "val": 0.15, "desc": "Not Applicable (Classical Path)"},
        {"key": "nba", "label": "Biodiversity Compliance (NBA)", "val": 0.45, "desc": "SBB Notice Required"},
        {"key": "fto", "label": "Regulatory Freedom (AYUSH API)", "val": 0.85, "desc": "Form 25D Standard Conformity"},
        {"key": "brand", "label": "Brand & GI Monopolizability", "val": 0.90, "desc": "High (GI & Collective TM Route)"},
    ],
    "Patent&Proprietary": [
        {"key": "tk", "label": "Traditional Knowledge (§ 3p)", "val": 0.15, "desc": "Low Risk (Novel Extraction)"},
        {"key": "sec3d", "label": "Efficacy Hurdle (§ 3d)", "val": 0.88, "desc": "High Hurdle (Proof of Enhanced Efficacy)"},
        {"key": "nba", "label": "Biodiversity Compliance (NBA)", "val": 0.92, "desc": "Form 3 Approval Mandatory"},
        {"key": "fto", "label": "Regulatory Freedom (P&P License)", "val": 0.70, "desc": "State AYUSH § 3(h) License"},
        {"key": "brand", "label": "Brand & GI Monopolizability", "val": 0.85, "desc": "High 20-Year Patentability"},
    ],
    "Phytopharmaceutical": [
        {"key": "tk", "label": "Traditional Knowledge (§ 3p)", "val": 0.20, "desc": "Low TK Risk (Standardized Fraction)"},
        {"key": "sec3d", "label": "Efficacy Hurdle (§ 3d)", "val": 0.85, "desc": "Clinical Superiority Proof Needed"},
        {"key": "nba", "label": "Biodiversity Compliance (NBA)", "val": 0.95, "desc": "Form 3 Approval Mandatory"},
        {"key": "fto", "label": "Regulatory Freedom (CDSCO Trial)", "val": 0.50, "desc": "New Drug Clearance (GSR 918E)"},
        {"key": "brand", "label": "Brand & GI Monopolizability", "val": 0.92, "desc": "High Global Market Asset"},
    ],
    "Aahar": [
        {"key": "tk", "label": "Traditional Knowledge (§ 3p)", "val": 0.10, "desc": "Exempt (Dietary Supplement)"},
        {"key": "sec3d", "label": "Efficacy Hurdle (§ 3d)", "val": 0.10, "desc": "No Drug Therapeutic Proof Required"},
        {"key": "nba", "label": "Biodiversity Compliance (NBA)", "val": 0.35, "desc": "SBB Commercial Intimation"},
        {"key": "fto", "label": "Regulatory Freedom (FSSAI Reg 5)", "val": 0.80, "desc": "Fast-Track FSSAI Schedule A"},
        {"key": "brand", "label": "Brand & GI Monopolizability", "val": 0.75, "desc": "Collective Trade Dress & TM"},
    ],
    "Ambiguous": [
        {"key": "tk", "label": "Traditional Knowledge (§ 3p)", "val": 0.55, "desc": "Undetermined Conflict Boundary"},
        {"key": "sec3d", "label": "Efficacy Hurdle (§ 3d)", "val": 0.60, "desc": "Bioactive Novelty Unclear"},
        {"key": "nba", "label": "Biodiversity Compliance (NBA)", "val": 0.65, "desc": "Verify Biological Origin"},
        {"key": "fto", "label": "Regulatory Freedom (Triage)", "val": 0.40, "desc": "Requires Human IP Clinic Review"},
        {"key": "brand", "label": "Brand & GI Monopolizability", "val": 0.45, "desc": "Comprehensive FTO Audit Required"},
    ],
}


def get_radar_metrics(classification: str) -> List[Dict[str, Any]]:
    """Returns the 5-axis sovereign IP risk profile for a given classification."""
    return RADAR_PROFILES.get(classification, RADAR_PROFILES["Ambiguous"])


def get_gi_strategy(classification: str) -> Dict[str, Any]:
    """Returns the tailored GI Strategic Registry recommendation for a classification."""
    strat = SCENARIO_GI_MAP.get(classification, SCENARIO_GI_MAP["Classical"])
    hub_key = strat.get("hub", "kerala")
    hub = GI_HUBS.get(hub_key, GI_HUBS["kerala"])
    return {
        "strategy": strat,
        "hub_key": hub_key,
        "hub": hub,
    }
