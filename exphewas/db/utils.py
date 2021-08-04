"""
Utilities for the SQLAlchemy ORM or for other database related matters.
"""


ANALYSIS_TYPES = [
    "PHECODES", "CONTINUOUS_VARIABLE", "SELF_REPORTED", "CV_ENDPOINTS"
]

ANALYSIS_SUBSETS = ["BOTH", "FEMALE_ONLY", "MALE_ONLY"]


def mod_to_dict(o):
    """Introspects a model to convert it to a regular Python dict."""
    keys = o.__table__.columns.keys()
    return {k: getattr(o, k) for k in keys}


def _get_table_name(analysis_subset, analysis_type):
    template = "results_{}_{}"
    analysis_subset = analysis_subset.split("_")[0].lower()
    analysis_type = analysis_type.lower()

    # I should've followed naming conventions better, but now I don't want
    # to rebuilt the whole database so I capture discrepancies manually.
    if analysis_type == "continuous_variable":
        analysis_type += "s"

    return "results_{}_{}".format(analysis_subset, analysis_type)


def _get_class_name(analysis_subset, analysis_type):
    def camel_word(s):
        return s.lower().capitalize()

    analysis_subset = camel_word(analysis_subset.split("_")[0])

    analysis_type_dict = {
        "CONTINUOUS_VARIABLE": "ContinuousResult",
        "PHECODES": "PhecodesResult",
        "SELF_REPORTED": "SelfReportedResult",
        "CV_ENDPOINTS": "CVEndpointsResult",
    }

    return "{}{}".format(analysis_subset, analysis_type_dict[analysis_type])
