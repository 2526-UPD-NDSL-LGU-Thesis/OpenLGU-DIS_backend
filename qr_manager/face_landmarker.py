""" 
Landmarker based on [MediaPipe Face Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python#handle_and_display_results) \
and [google-ai-edge/mediapipe-samples](https://github.com/google-ai-edge/mediapipe-samples/blob/main/examples/face_landmarker/python/%5BMediaPipe_Python_Tasks%5D_Face_Landmarker.ipynb).
"""


from typing import Optional, Any
from dataclasses import dataclass
from django.conf import settings
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# pylint: disable=trailing-whitespace


@dataclass
class MediaPipeFaceLandMarker:
    """MediaPipe Face Landmarker for image cropping."""
    _detector : Optional[Any] = None
    _initialized : bool = False

    def get_detector(self):
        if self._initialized:
            if self._detector:
                return self._detector
            else:
                raise RuntimeError("Failed to initialize MediaPipe Landmarkers.")
        
        try:
            base_options = python.BaseOptions(model_asset_path=settings.LANDMARKER_MODEL)
            options = vision.FaceLandmarkerOptions(base_options=base_options,
                                                output_face_blendshapes=True,
                                                output_facial_transformation_matrixes=True,
                                                num_faces=1)
            self._detector = vision.FaceLandmarker.create_from_options(options)
        except Exception as err:
            print("Failed to initialize MediaPipe Landmarkers: ", err)
            self._detector = None
        self._initialized = True

        return self._detector
