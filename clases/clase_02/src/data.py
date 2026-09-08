"""Descarga del dataset Sleep-EDF Expanded desde PhysioNet.

MNE incluye un descargador oficial (``fetch_data``) que trae los archivos EDF
directamente desde PhysioNet, por lo que no hace falta manejar URLs a mano.
"""

from __future__ import annotations

from pathlib import Path

from mne.datasets.sleep_physionet.age import fetch_data

from .config import DATA_RAW


def download_sleep_edf(
    subject: int = 0,
    recording: int = 1,
    path: str | Path = DATA_RAW,
) -> tuple[str, str]:
    """Descarga el PSG y el hipnograma de un sujeto/noche del Sleep-EDF Expanded.

    Parameters
    ----------
    subject : int
        Índice del sujeto (0 a 82 disponibles).
    recording : int
        Número de noche (1 o 2).
    path : str | Path
        Carpeta donde guardar los archivos (por defecto ``data/raw/``). MNE crea
        adentro un subdirectorio ``physionet-sleep-data/``. Si el archivo ya
        existe no se vuelve a descargar.

    Returns
    -------
    (psg_path, hypnogram_path) : tuple[str, str]
        Rutas locales al archivo PSG (señales) y al hipnograma (anotaciones).
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    paths = fetch_data(
        subjects=[subject], recording=[recording], path=str(path), verbose=False
    )
    psg_path, hypnogram_path = paths[0]
    return psg_path, hypnogram_path
