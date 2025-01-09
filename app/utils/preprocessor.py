import os
import torch
from io import BytesIO
from pydub import AudioSegment
from pyannote.audio.pipelines import VoiceActivityDetection
from importlib import import_module

class LocalModelLoader:
    @classmethod
    def load_local_model(cls, checkpoint_path: str, map_location=None):
        # Check if the checkpoint path is local
        if os.path.isfile(checkpoint_path):
            path_for_pl = checkpoint_path
        else:
            raise ValueError("Local path expected for checkpoint, but got a remote path.")

        # Load the checkpoint using torch.load
        if map_location is None:
            map_location = lambda storage, loc: storage
        loaded_checkpoint = torch.load(path_for_pl, map_location=map_location)

        # Obtain architecture details from the checkpoint metadata
        module_name = loaded_checkpoint["pyannote.audio"]["architecture"]["module"]
        class_name = loaded_checkpoint["pyannote.audio"]["architecture"]["class"]

        # Dynamically import the module and get the model class
        module = import_module(module_name)
        Klass = getattr(module, class_name)

        # Instantiate the model from the local checkpoint
        model = Klass.load_from_checkpoint(
            path_for_pl,
            map_location=map_location,
            strict=True
        )

        return model

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'audio_classifier_model/pytorch_model.bin')
local_model = LocalModelLoader.load_local_model(model_path)

# Set up the Voice Activity Detection pipeline with the loaded model
vad_pipeline = VoiceActivityDetection(segmentation=local_model)

# Define parameters for the pipeline
HYPER_PARAMETERS = {
    "onset": 0.8104268538848918,
    "offset": 0.4806866463041527,
    "min_duration_on": 0.05537587440407595,
    "min_duration_off": 0.09791355693027545
}

# Instantiate the pipeline with the parameters
vad_pipeline.instantiate(HYPER_PARAMETERS)

def run_voice_activity_detector(audio_file: BytesIO) -> bool:
    audio = AudioSegment.from_file(audio_file)
    wav_io = BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)

    output = vad_pipeline({"audio": wav_io, "uri": "audio_clip"})
    has_speech = any(segment for segment in output.get_timeline().support())
    return has_speech
