"""Descarga del dataset Sleep-EDF Expanded desde PhysioNet.

MNE incluye un descargador oficial (``fetch_data``) que trae los archivos EDF
directamente desde PhysioNet, por lo que no hace falta manejar URLs a mano.
"""

from __future__ import annotations

from mne.datasets.sleep_physionet.age import fetch_data


def download_sleep_edf(subject: int = 0, recording: int = 1) -> tuple[str, str]:
    """Descarga el PSG y el hipnograma de un sujeto/noche del Sleep-EDF Expanded.

    Parameters
    ----------
    subject : int
        Índice del sujeto (0 a 82 disponibles).
    recording : int
        Número de noche (1 o 2).

    Returns
    -------
    (psg_path, hypnogram_path) : tuple[str, str]
        Rutas locales al archivo PSG (señales) y al hipnograma (anotaciones).
    """
    paths = fetch_data(subjects=[subject], recording=[recording], verbose=False)
    psg_path, hypnogram_path = paths[0]
    return psg_path, hypnogram_path
