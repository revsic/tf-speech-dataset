from typing import List, Tuple

import numpy as np

from .speechset import SpeechSet
from ..config import Config
from ..datasets.reader import DataReader
from ..utils.melstft import MelSTFT
from ..utils.normalizer import TextNormalizer


class AcousticDataset(SpeechSet):
    """Dataset for text to acoustic features.
    """
    VOCABS = len(TextNormalizer.GRAPHEMES) + 1

    def __init__(self, rawset: DataReader, config: Config):
        """Initializer.
        Args:
            rawset: file-format datum reader.
            config: configuration.
        """
        # cache dataset and preprocessor
        super().__init__(rawset)
        self.config = config
        self.melstft = MelSTFT(config)
        self.textnorm = TextNormalizer()

    def normalize(self, text: str, speech: np.ndarray) \
            -> Tuple[np.ndarray, np.ndarray]:
        """Normalize datum.
        Args:
            text: transcription.
            speech: [np.float32; [T]], speech in range (-1, 1).
        Returns:
            normalized datum.
                labels: [np.long; [S]], labeled text sequence.
                mel: [np.float32; [T // hop, mel]], mel spectrogram.
        """
        # [S]
        labels = np.array(self.textnorm.labeling(text), dtype=np.long)
        # [T // hop, mel]
        mel = self.melstft(speech)
        return labels, mel

    def collate(self, bunch: List[Tuple[np.ndarray, np.ndarray]]) \
            -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Collate bunch of datum to the batch data.
        Args:
            bunch: B x [...] list of normalized inputs.
                labels: [np.long; [Si]], labled text sequence.
                mel: [np.float32; [Ti, mel]], mel spectrogram.
        Returns:
            batch data.
                text: [np.long; [B, S]], labeled text sequence.
                mel: [np.float32; [B, T, mel]], mel spectrogram.
                textlen: [np.long; [B]], text lengths.
                mellen: [np.long; [B]], spectrogram lengths.
        """
        # [B], [B]
        textlen, mellen = np.array(
            [[len(labels), len(spec)] for labels, spec in bunch], dtype=np.long).T
        # [B, S]
        text = np.stack(
            [np.pad(labels, [0, len(labels) - textlen.max()]) for labels, _ in bunch])
        # [B, T, mel]
        mel = np.stack(
            [np.pad(spec, [[0, len(spec) - mellen.max()], [0, 0]]) for _, spec in bunch])
        return mel, text, textlen, mellen
