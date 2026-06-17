from langdetect.detector_factory import DetectorFactory
import pkg_resources
import threading

# Load profiles only once, globally
_profile_path = pkg_resources.resource_filename('langdetect', 'profiles')
_factory = DetectorFactory()
_factory.load_profile(_profile_path)

# Lock to ensure thread-safety when creating detectors
_lock = threading.Lock()

def detect_language(text):
    with _lock:
        detector = _factory.create()
        detector.append(text)
        return detector.detect()
