"""Carga de la señal EEG y segmentación en épocas por etapa de sueño."""

from __future__ import annotations

import mne

from .config import EEG_CHANNEL, EPOCH_DURATION, STAGE_IDS, STAGE_MAPPING


def load_recording(
    psg_path: str,
    hypnogram_path: str,
    channel: str = EEG_CHANNEL,
) -> mne.io.BaseRaw:
    """Carga el PSG, adjunta el hipnograma y se queda con un único canal EEG.

    Parameters
    ----------
    psg_path, hypnogram_path : str
        Rutas devueltas por :func:`src.data.download_sleep_edf`.
    channel : str
        Canal EEG a conservar (por defecto ``"EEG Fpz-Cz"``).

    Returns
    -------
    raw : mne.io.BaseRaw
        Registro con un solo canal y las anotaciones de etapas de sueño.
    """
    raw = mne.io.read_raw_edf(psg_path, preload=True, verbose=False)
    annotations = mne.read_annotations(hypnogram_path)
    raw.set_annotations(annotations, emit_warning=False)
    raw.pick([channel])
    return raw


def make_epochs(
    raw: mne.io.BaseRaw,
    epoch_duration: float = EPOCH_DURATION,
) -> mne.Epochs:
    """Segmenta el EEG en épocas de ``epoch_duration`` s etiquetadas por etapa.

    Sólo se incluyen las etapas realmente presentes en el hipnograma.

    Returns
    -------
    epochs : mne.Epochs
        Épocas con ``event_id`` mapeando el nombre de la etapa (W, N1, ...) a
        su id numérico.
    """
    present = set(raw.annotations.description)
    ann_to_id = {
        desc: STAGE_IDS[stage]
        for desc, stage in STAGE_MAPPING.items()
        if desc in present
    }

    events, _ = mne.events_from_annotations(
        raw, event_id=ann_to_id, chunk_duration=epoch_duration, verbose=False
    )

    id_to_stage = {v: k for k, v in STAGE_IDS.items()}
    event_id = {id_to_stage[code]: code for code in sorted(set(events[:, -1]))}

    sfreq = raw.info["sfreq"]
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=0.0,
        tmax=epoch_duration - 1.0 / sfreq,
        baseline=None,
        preload=True,
        verbose=False,
    )
    return epochs
