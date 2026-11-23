MAIN_TEMPS_LIST = [
    "Drugbox",
    "Speciesbox",
    "Infobox anatomy",
    "Infobox birth control",
    "Infobox diagnostic",
    "Infobox drug (new)",
    "Infobox drug class",
    "Infobox drug mechanism",
    "Infobox drug",
    "Infobox medical condition (new)",
    "Infobox medical condition",
    "Infobox medical intervention",
    "Infobox nonhuman protein",
    "Infobox nutritional value",
    "Infobox organization",
    "Infobox project",
    "Infobox protein family",
    "Infobox sanitation technology",
    "Infobox vein",
]

main_temps_lower_list = [x.lower() for x in MAIN_TEMPS_LIST]

IMC_params = {
    "infobox medical condition": [
        "name",
        "synonym",
        "image",
        "image_size",
        "image_thumbtime",
        "alt",
        "caption",
        "pronounce",
        "field",
        "symptoms",
        "complications",
        "onset",
        "duration",
        "types",
        "causes",
        "risks",
        "diagnosis",
        "differential",
        "prevention",
        "treatment",
        "medication",
        "prognosis",
        "frequency",
        "deaths",
    ]
}
IMC_params["infobox medical condition (new)"] = IMC_params["infobox medical condition"]

dup_params = {
    "infobox medical condition": {
        "synonyms": "synonym",
        "speciality": "field",
        "specialty": "field",
    }
}

dup_params["infobox medical condition (new)"] = dup_params["infobox medical condition"]
