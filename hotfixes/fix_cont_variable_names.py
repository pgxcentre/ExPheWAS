#!/usr/bin/env python

"""
Fixes the cryptic name of some continuous variables.

Some continous variables had names that were taken as is from reports and this
script updates the database with more eloquent descriptions.

Even though it is part of the package, this script is meant to be used as a
stand-alone utility.

"""


from exphewas.db.engine import Session
from exphewas.db.models import Outcome


updates = [
    # variable_id, label
    ("cont_v1", "Intima-media thickness"),
    ("cont_v2", "Waist-to-hip ratio (baseline)"),
    ("cont_v3", "Body fat percentage (baseline)"),
    ("cont_v4", "Forced expiratory volume in 1 second (FEV1)"),
    ("cont_v5", "Body mass index (baseline)"),
    ("cont_v6", "Hip circumference (baseline)"),
    ("cont_v7", "Basal metabolic rate (baseline)"),
    ("cont_v8", "Waist circumference"),
    ("cont_v9", "Pulse rate (baseline)"),
    ("cont_v10", "Diastolic blood pressure (baseline)"),
    ("cont_v11", "Forced vital capacity (FVC)"),
    ("cont_v12", "Systolic blood pressure (baseline)"),
]


def main():
    session = Session()

    print("Renaming continuous variables to nicer labels.")
    for id_, new_label in updates:
        # Get object from db.
        o = session.query(Outcome).filter_by(id=id_).one()
        o.label = new_label

    session.commit()
    print("Done!")


if __name__ == "__main__":
    main()
