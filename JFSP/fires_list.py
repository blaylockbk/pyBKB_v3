from datetime import datetime


def get_fire(fire):

    fires = {
        "Lake Christine": {
            "name": "Lake Christine",
            "cause": "Human",
            "sDATE": datetime(2018, 7, 6),
            "event": datetime(2018, 7, 5, 21),
            "latitude": 39.3777,
            "longitude": -107.0427,
        },
        "Whitten": {
            "name": "Whitten",
            "cause": "Undetermined",
            "sDATE": datetime(2017, 7, 10),
            "latitude": 45.36389,
            "longitude": -106.6575,
        },
        "Coal Hollow": {
            "name": "Coal Hollow",
            "cause": "Lightning",
            "sDATE": datetime(2018, 8, 4),
            "latitude": 39.951,
            "longitude": -111.403,
        },
        "Dollar Ridge": {
            "name": "Dollar Ridge",
            "cause": "Human",
            "sDATE": datetime(2018, 7, 11),
            "latitude": 40.1,
            "longitude": -110.96,
        },
        "July Storm": {
            "name": "July Storm",
            "cause": "Human",
            "sDATE": datetime(2018, 7, 16),
            "event": datetime(2018, 7, 17, 6),
            "latitude": 40.77069,
            "longitude": -111.96503,
        },
        "Cougar Creek": {
            "name": "Cougar Creek",
            "cause": "Lightning",
            "sDATE": datetime(2018, 9, 7),
            "latitude": 47.851,
            "longitude": -120.549,
        },
        "Mallard": {
            "name": "Mallard",
            "cause": "Lightning",
            "sDATE": datetime(2018, 5, 14),
            "event": datetime(2018, 5, 15, 23),
            "latitude": 34.81,
            "longitude": -101.306,
        },
    }

    return fires[fire]
