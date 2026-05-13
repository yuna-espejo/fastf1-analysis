import fastf1
import os

os.makedirs('cache_f1', exist_ok=True)
fastf1.Cache.enable_cache('cache_f1')


def cargar_carrera (year, circuit):
    session = fastf1.get_session(year, circuit, "R")
    session.load()
    return session

def detectar_pits(session):
    pass

session = cargar_carrera(2024, "Mónaco")
detectar_pits(session)

